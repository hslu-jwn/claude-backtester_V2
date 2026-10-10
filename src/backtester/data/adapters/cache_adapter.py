"""Read candles from the local Dukascopy M1 cache, resampled to any supported timeframe.

Spec: ARCHITECTURE.md › Data sources › Dukascopy, ROADMAP.md › 0.2.

Each requested UTC day is read from `{cache_dir}/{SYMBOL}/{YYYY}/{YYYY-MM-DD}.parquet`
(written by `data/dukascopy.py`), flat zero-volume minutes are dropped and the rest is
resampled (`data/resample.py`). Every intraday timeframe divides a day, so no candle spans
two days. D and W candles (trading days, `DayBoundary`) and New York-aligned 4h candles
(`H4Alignment`) can span several UTC days: the cached days around the range are read too,
a candle belongs to the range when it CLOSES in it, and a candle is only returned when
every UTC day it covers is cached (no half candles at the edges of the cache).

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
from backtester.data.dukascopy import DEFAULT_CACHE_DIR, cache_path, read_cached_days
from backtester.data.resample import (
    DEFAULT_BOUNDARY,
    DayBoundary,
    H4Alignment,
    drop_flat_minutes,
    resample,
    spans_utc_days,
    supported,
)


class MissingCacheError(LookupError):
    """Requested days are not in the cache. Download them first."""


class CacheAdapter(DataAdapter):
    def __init__(self, cache_dir: str | Path = DEFAULT_CACHE_DIR):
        self.cache_dir = Path(cache_dir)

    def fetch(
        self, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> list[Candle]:
        return candles_from_frame(self.fetch_frame(symbol, timeframe, start, end))

    def fetch_frame(
        self,
        symbol: str,
        timeframe: Timeframe,
        start: datetime,
        end: datetime,
        boundary: DayBoundary = DEFAULT_BOUNDARY,
        h4: H4Alignment = H4Alignment.UTC,
    ) -> pd.DataFrame:
        """Same candles as `fetch`, as a DataFrame with columns
        ts, open, high, low, close, volume, spread. `boundary`: the day of D / W candles,
        `h4`: the alignment of 4h candles."""
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
                f"{symbol}: {len(missing)} day(s) not in {self.cache_dir}: {day_ranges(missing)}. "
                f"Run: python -m backtester.data.download {symbol} {missing[0]} "
                f"{missing[-1] + timedelta(days=1)}"
            )

        if spans_utc_days(timeframe, h4):
            return self._spanning(symbol, timeframe, start, end, days, boundary, h4)
        m1 = read_cached_days(paths)
        candles = resample(drop_flat_minutes(m1), timeframe)
        in_range = (candles["ts"] >= start) & (candles["ts"] < end)
        return candles[in_range].reset_index(drop=True)

    def _spanning(self, symbol, timeframe, start, end, days, boundary, h4) -> pd.DataFrame:
        """Candles closing in (start, end] whose UTC days are all cached (D, W, NY 4h)."""
        span = timeframe.duration + timedelta(days=1)  # a DST day is up to 25 hours
        around = _days(start - span, end + span)
        loaded = [d for d in around if cache_path(self.cache_dir, symbol, d).exists()]
        m1 = read_cached_days([cache_path(self.cache_dir, symbol, d) for d in loaded])
        if m1.empty:
            return resample(pd.DataFrame(), timeframe)
        candles = resample(drop_flat_minutes(m1), timeframe, boundary, h4)
        close = candles["ts"] + timeframe.duration
        cached = set(loaded)
        complete = [all(d in cached for d in _days(c - timeframe.duration, c)) for c in close]
        keep = (close > start) & (close <= end) & pd.Series(complete, index=candles.index)
        return candles[keep].reset_index(drop=True)


def candles_from_frame(frame: pd.DataFrame) -> list[Candle]:
    """Rows of a `fetch_frame` result as `Candle`s."""
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
        for row in frame.itertuples(index=False)
    ]


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def _days(start: datetime, end: datetime) -> list[date]:
    """UTC days touched by [start, end)."""
    first, last = start.date(), (end - timedelta(microseconds=1)).date()
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def day_ranges(days: list[date]) -> str:
    """Compact list of consecutive day runs: '2026-01-01..2026-01-03, 2026-02-10'."""
    runs: list[list[date]] = []
    for d in days:
        if runs and d - runs[-1][-1] == timedelta(days=1):
            runs[-1].append(d)
        else:
            runs.append([d])
    return ", ".join(f"{r[0]}..{r[-1]}" if len(r) > 1 else str(r[0]) for r in runs)


def available_symbols(cache_dir: str | Path = DEFAULT_CACHE_DIR) -> list[str]:
    """Symbols with at least one cached day, sorted. Folders without cache files are ignored."""
    root = Path(cache_dir)
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir() and any(p.glob("*/*.parquet")))


def cached_days(symbol: str, cache_dir: str | Path = DEFAULT_CACHE_DIR) -> list[date]:
    """Days cached for `symbol`, oldest first. Days cached as empty count as cached."""
    return sorted(
        date.fromisoformat(p.stem) for p in (Path(cache_dir) / symbol).glob("*/*.parquet")
    )


def latest_run(days: list[date]) -> tuple[date, date] | None:
    """First and last day of the newest run of consecutive days, or None if there are none."""
    if not days:
        return None
    first = days[-1]
    for d in reversed(days[:-1]):
        if first - d != timedelta(days=1):
            break
        first = d
    return first, days[-1]
