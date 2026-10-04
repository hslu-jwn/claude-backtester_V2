"""Read candles from the local Dukascopy M1 cache, resampled to any supported timeframe.

Spec: ARCHITECTURE.md › Data sources › Dukascopy, ROADMAP.md › 0.2.

Each requested UTC day is read from `{cache_dir}/{SYMBOL}/{YYYY}/{YYYY-MM-DD}.parquet`
(written by `data/dukascopy.py`), flat zero-volume minutes are dropped and the rest is
resampled (`data/resample.py`). Every supported timeframe divides a day, so no candle spans
two days and each day can be resampled on its own.

A day that was never downloaded raises `MissingCacheError`, so gaps in the cache are never
silent. A day cached as empty (Dukascopy had no data) simply has no candles. Only past days
are ever cached, so every candle returned is closed.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd

from backtester.core.models import Candle, Timeframe
from backtester.data.adapters.base import DataAdapter
from backtester.data.dukascopy import DEFAULT_CACHE_DIR, cache_path, read_cached_day
from backtester.data.resample import drop_flat_minutes, resample, supported


class MissingCacheError(LookupError):
    """Requested days are not in the cache. Download them first."""


class CacheAdapter(DataAdapter):
    def __init__(self, cache_dir: str | Path = DEFAULT_CACHE_DIR):
        self.cache_dir = Path(cache_dir)

    def fetch(
        self, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> list[Candle]:
        return [
            Candle(
                ts=row.ts.to_pydatetime(),
                open=row.open,
                high=row.high,
                low=row.low,
                close=row.close,
                volume=row.volume,
                spread=row.spread,
            )
            for row in self.fetch_frame(symbol, timeframe, start, end).itertuples(index=False)
        ]

    def fetch_frame(
        self, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> pd.DataFrame:
        """Same candles as `fetch`, as a DataFrame with columns
        ts, open, high, low, close, volume, spread."""
        if not supported(timeframe):
            raise ValueError(f"{timeframe.name} is not supported by the cache")
        start, end = _utc(start), _utc(end)
        if end <= start:
            raise ValueError(f"end {end} must be after start {start}")

        days = _days(start, end)
        paths = [cache_path(self.cache_dir, symbol, d) for d in days]
        missing = [d for d, p in zip(days, paths) if not p.exists()]
        if missing:
            raise MissingCacheError(
                f"{symbol}: {len(missing)} day(s) not in {self.cache_dir}: {_ranges(missing)}. "
                f"Run: python -m backtester.data.download {symbol} {missing[0]} "
                f"{missing[-1] + timedelta(days=1)}"
            )

        frames = [f for f in map(read_cached_day, paths) if not f.empty]
        m1 = pd.concat(frames, ignore_index=True) if frames else read_cached_day(paths[0])
        candles = resample(drop_flat_minutes(m1), timeframe)
        in_range = (candles["ts"] >= start) & (candles["ts"] < end)
        return candles[in_range].reset_index(drop=True)


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def _days(start: datetime, end: datetime) -> list[date]:
    """UTC days touched by [start, end)."""
    first, last = start.date(), (end - timedelta(microseconds=1)).date()
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def _ranges(days: list[date]) -> str:
    """Compact list of consecutive day runs: '2026-01-01..2026-01-03, 2026-02-10'."""
    runs: list[list[date]] = []
    for d in days:
        if runs and d - runs[-1][-1] == timedelta(days=1):
            runs[-1].append(d)
        else:
            runs.append([d])
    return ", ".join(f"{r[0]}..{r[-1]}" if len(r) > 1 else str(r[0]) for r in runs)
