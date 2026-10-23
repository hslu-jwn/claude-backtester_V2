"""Read candles from the local M1 cache, resampled to any supported timeframe.

Spec: ARCHITECTURE.md › Data sources › histdata.com, ROADMAP.md › 0.2.

Each requested UTC day is read from `{cache_dir}/{SYMBOL}/{YYYY}/{YYYY-MM-DD}.parquet`
(written by `data/histdata.py`, see `data/cache.py`), flat zero-volume minutes are dropped and the rest is
resampled (`data/resample.py`). Every intraday timeframe divides a day, so no candle spans
two days. D and W candles (trading days, `DayBoundary`) and New York-aligned 4h candles
(`H4Alignment`) can span several UTC days: the cached days around the range are read too,
a candle belongs to the range when it CLOSES in it, and a candle is only returned when
every UTC day it covers is cached (no half candles at the edges of the cache).

A day that was never imported raises `MissingCacheError`, so gaps in the cache are never
silent. A day cached as empty (the source had no data) simply has no candles. Only past days
are ever cached, so every candle returned is closed.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from backtester.core.models import Candle, Timeframe
from backtester.data.adapters.base import DataAdapter
from backtester.data.cache import DEFAULT_CACHE_DIR, cache_path, read_cached_days
from backtester.data.resample import (
    CANDLE_COLUMNS,
    DEFAULT_BOUNDARY,
    DayBoundary,
    H4Alignment,
    drop_flat_minutes,
    resample,
    spans_utc_days,
    supported,
)


class MissingCacheError(LookupError):
    """Requested days are not in the cache. Import them first (`data.histdata`)."""


class CacheAdapter(DataAdapter):
    def __init__(self, cache_dir: str | Path = DEFAULT_CACHE_DIR):
        self.cache_dir = Path(cache_dir)

    def _path(self, symbol: str, day: date) -> Path:
        """The day file of `symbol` (a subclass may read some days from another folder)."""
        return cache_path(self.cache_dir, symbol, day)

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
        on_read: Callable[[int, int], None] | None = None,
    ) -> pd.DataFrame:
        """Same candles as `fetch`, as a DataFrame with columns
        ts, open, high, low, close, volume, spread. `boundary`: the day of D / W candles,
        `h4`: the alignment of 4h candles. `on_read(files_done, files_total)` is called while
        the day files are read (`cache.read_cached_days`)."""
        if not supported(timeframe):
            raise ValueError(f"{timeframe.name} is not supported by the cache")
        start, end = _utc(start), _utc(end)
        if end <= start:
            raise ValueError(f"end {end} must be after start {start}")

        days = _days(start, end)
        paths = [self._path(symbol, d) for d in days]
        missing = [d for d, p in zip(days, paths) if not p.exists()]
        if missing:
            raise MissingCacheError(
                f"{symbol}: {len(missing)} day(s) not in {self.cache_dir}: {day_ranges(missing)}. "
                f"Import the histdata.com files: python -m backtester.data.histdata "
                f"data/raw/histdata/ (first missing day: {missing[0]})"
            )

        if spans_utc_days(timeframe, h4):
            return self._spanning(symbol, timeframe, start, end, days, boundary, h4, on_read)
        m1 = read_cached_days(paths, on_read)
        candles = resample(drop_flat_minutes(m1), timeframe)
        in_range = (candles["ts"] >= start) & (candles["ts"] < end)
        return candles[in_range].reset_index(drop=True)

    def _spanning(
        self, symbol, timeframe, start, end, days, boundary, h4, on_read=None
    ) -> pd.DataFrame:
        """Candles closing in (start, end] whose UTC days are all cached (D, W, NY 4h)."""
        span = timeframe.duration + timedelta(days=1)  # a DST day is up to 25 hours
        around = _days(start - span, end + span)
        loaded = [d for d in around if self._path(symbol, d).exists()]
        m1 = read_cached_days([self._path(symbol, d) for d in loaded], on_read)
        if m1.empty:
            return resample(pd.DataFrame(), timeframe)
        candles = resample(drop_flat_minutes(m1), timeframe, boundary, h4)
        close = candles["ts"] + timeframe.duration
        cached = set(loaded)
        complete = [all(d in cached for d in _days(c - timeframe.duration, c)) for c in close]
        keep = (close > start) & (close <= end) & pd.Series(complete, index=candles.index)
        return candles[keep].reset_index(drop=True)


class PreferredCacheAdapter(CacheAdapter):
    """Reads a day from `preferred_dir` when that day file exists there, else from `cache_dir`,
    else from `last_dir` (the live bot's folder, ROADMAP 7.8). Either extra folder may be None.
    A day file is read from exactly one folder, so days are never duplicated or overlapped;
    D / W / 4h candles spanning a seam are built from all feeds."""

    def __init__(
        self,
        cache_dir: str | Path,
        preferred_dir: str | Path | None = None,
        last_dir: str | Path | None = None,
    ):
        super().__init__(cache_dir)
        self.preferred_dir = None if preferred_dir is None else Path(preferred_dir)
        self.last_dir = None if last_dir is None else Path(last_dir)

    def _path(self, symbol: str, day: date) -> Path:
        if self.preferred_dir is not None:
            preferred = cache_path(self.preferred_dir, symbol, day)
            if preferred.exists():
                return preferred
        main = super()._path(symbol, day)
        if main.exists() or self.last_dir is None:
            return main
        last = cache_path(self.last_dir, symbol, day)
        return last if last.exists() else main


def candles_from_frame(frame: pd.DataFrame) -> list[Candle]:
    """Rows of a `fetch_frame` result as `Candle`s.

    Spec: ARCHITECTURE.md, data sources; docs/review/speed.md step 3.
    Standard UTC cache frames are validated together before any construction.
    Other layouts/dtypes and invalid batches use the original constructor path,
    preserving its first error, including timestamp and OHLC validation order.
    """
    if len(frame) == 0:
        return []
    if _valid_candle_frame(frame):
        # The same OHLC and timestamp checks as Candle.__post_init__ have passed
        # for every row. Keep the bypass private to this validated loading path.
        new, set_field = object.__new__, object.__setattr__
        candles = []
        for row in frame.itertuples(index=False):
            candle = new(Candle)
            set_field(candle, "ts", row.ts.to_pydatetime())
            set_field(candle, "open", row.open)
            set_field(candle, "high", row.high)
            set_field(candle, "low", row.low)
            set_field(candle, "close", row.close)
            set_field(candle, "volume", row.volume)
            set_field(candle, "spread", row.spread)
            candles.append(candle)
        return candles
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


def _valid_candle_frame(frame: pd.DataFrame) -> bool:
    """Vectorized Candle checks for the canonical float64, aware-UTC cache schema.

    Restrict the fast path to native float64 prices to avoid coercing object,
    nullable or mixed integer/float columns and changing their validation.
    Candle accepts other aware zones, too; those retain the constructor path.
    Volume and spread are deliberately not validated, just as in Candle.
    """
    if list(frame.columns) != CANDLE_COLUMNS:
        return False
    ts = frame["ts"]
    if not isinstance(ts.dtype, pd.DatetimeTZDtype):
        return False
    tz = ts.dt.tz
    is_utc = tz == UTC or (isinstance(tz, ZoneInfo) and tz.key == "UTC")
    if not is_utc or ts.isna().any():
        return False
    prices = frame[["open", "high", "low", "close"]]
    if not all(dtype == np.dtype("float64") for dtype in prices.dtypes):
        return False
    values = prices.to_numpy(copy=False)
    o, h, lo, c = values.T
    return bool(
        np.isfinite(values).all()
        and ((h >= lo) & (h >= o) & (h >= c) & (lo <= o) & (lo <= c)).all()
    )


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


_DAY_LISTS: dict[tuple[str, str], tuple[tuple, tuple[date, ...]]] = {}


def _signature(symbol_dir: Path) -> tuple:
    """Every year folder's name and modification time, plus the newest year's file count:
    Windows does not always update a folder's time at once when a day file is added, and new days
    (the live bot's, "Update data") land in the newest year."""
    try:
        with os.scandir(symbol_dir) as entries:
            years = sorted((e.name, e.stat().st_mtime_ns) for e in entries if e.is_dir())
        if not years:
            return ()
        with os.scandir(symbol_dir / years[-1][0]) as files:
            newest = sum(1 for _ in files)
    except OSError:
        return ()
    return (*years, newest)


def _scan_days(symbol_dir: Path) -> tuple[tuple, tuple[date, ...]]:
    signature = _signature(symbol_dir)  # taken first: a day added meanwhile triggers a rescan
    days = []
    for year, _ in signature[:-1]:
        with os.scandir(symbol_dir / year) as files:  # scandir: much faster than glob
            days += [date.fromisoformat(f.name[:-8]) for f in files if f.name.endswith(".parquet")]
    return signature, tuple(sorted(days))


def cached_days(symbol: str, cache_dir: str | Path = DEFAULT_CACHE_DIR) -> list[date]:
    """Days cached for `symbol`, oldest first. Days cached as empty count as cached.
    Listing years of day files takes ~0.1 s and the chart asks on every callback, so the list is
    kept in memory and read again only when a year folder changed (a day was added)."""
    symbol_dir = Path(cache_dir) / symbol
    key = (str(symbol_dir), symbol)
    kept = _DAY_LISTS.get(key)
    if kept is not None and _signature(symbol_dir) == kept[0]:
        return list(kept[1])
    _DAY_LISTS[key] = found = _scan_days(symbol_dir)
    return list(found[1])


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
