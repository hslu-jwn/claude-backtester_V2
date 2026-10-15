"""Download FTMO's M1 history from the running MT5 terminal into its own day cache.

    python -m backtester.tools.mt5_download                          # all five symbols, all history
    python -m backtester.tools.mt5_download NAS100 US500 --start 2021-09-15 --end 2022-12-31

(the command line, which opens the terminal session, is `tools/mt5_download.py`; the data
layer does not import `live/`).

Spec: ROADMAP.md > 11.5, ARCHITECTURE.md > MetaTrader 5.

Writes `data/cache/mt5/{SYMBOL}/{YYYY}/{YYYY-MM-DD}.parquet` (git-ignored), the layout and
columns of `data/cache.py`, so `SymbolSources` / `CacheAdapter` read it like histdata's:
`bid_*` = the MT5 bar, `ask_*` = bid + the bar's spread in price units, volumes = tick volume.
A bar with spread 0 (not recorded) has no ask (NaN, like histdata's missing asks), never
"ask = bid". The engine prices fills from `CostConfig`, not from the bars, so the ask only
feeds `Candle.spread`.

- Needs the terminal running and logged in (`live/connection.py`); no login is read or printed.
  The terminal's "Max bars in chart" must be Unlimited for the full depth.
- Bar times are server time; `ServerClock` (default `America/New_York + 7 h`, or the clock
  saved by `tools.mt5_info`) converts them to UTC. The rule was measured on 2020-2026 only:
  check earlier years first (`tools/mt5_clock_check.py`).
- Days are cut on the UTC day and written chunk by chunk (`chunk_days`). Nothing is claimed
  before the first real intraday day (`min_day_bars` bars) of the requested range; that day is
  skipped as partial (so with a `--start` inside the history the first day is not written);
  after it, days without bars are cached as empty. The end defaults to yesterday (UTC), so
  no forming bar is ever stored.
- Our symbol NAS100 is `US100.cash` on FTMO (`DEFAULT_NAMES`, overridden by the saved names).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd

from backtester.core.models import Timeframe
from backtester.data.adapters.mt5_adapter import Mt5Adapter, Mt5Error, ServerClock
from backtester.data.cache import (
    COLUMNS,
    MT5_CACHE_DIR,
    cache_path,
    empty_cache_frame,
    write_atomic,
)

DEFAULT_NAMES = {
    "NAS100": "US100.cash", "US500": "US500.cash",
    **{s: f"{s}.cash" for s in ("US30", "US2000", "GER40", "UK100", "JP225", "EU50", "USOIL", "UKOIL", "NATGAS", "DXY")},
}  # fmt: skip  # our name -> FTMO's (ROADMAP 11.8); other symbols have the same name
DEFAULT_CLOCK = ServerClock("America/New_York", 7)
DEFAULT_SYMBOLS = ("XAUUSD", "GBPUSD", "GBPJPY", "NAS100", "US500")
FIRST_DAY = date(2010, 1, 1)  # earlier than any FTMO history; empty chunks are skipped
CHUNK_DAYS = 31
# FTMO's index history before 2021-09 is one bar per day (also on "M1"); real intraday bars
# start later. The first day with at least this many bars is where the cache starts.
MIN_DAY_BARS = 100


@dataclass(frozen=True)
class DownloadResult:
    symbol: str
    bars: int
    days_written: int
    days_empty: int
    first_day: date | None  # first / last day written (None: nothing)
    last_day: date | None


def cache_frame(bars: pd.DataFrame) -> pd.DataFrame:
    """`bars` (ts UTC, open, high, low, close, volume, spread in price units) -> cache columns."""
    out = pd.DataFrame({"ts": bars["ts"].to_numpy()})
    spread = bars["spread"].to_numpy(dtype=float)
    known = spread > 0  # 0 = not recorded
    for field in ("open", "high", "low", "close"):
        bid = bars[field].to_numpy(dtype=float)
        out[f"bid_{field}"] = bid
        out[f"ask_{field}"] = pd.Series(bid + spread).where(known)
    volume = bars["volume"].to_numpy(dtype=float)
    out["bid_volume"] = volume
    out["ask_volume"] = volume
    out["ts"] = pd.DatetimeIndex(bars["ts"]).tz_convert("UTC")
    return out[COLUMNS]


def utc_bars(adapter: Mt5Adapter, symbol: str, first: date, last: date) -> pd.DataFrame:
    """M1 bars with UTC `ts` whose server window covers UTC days `first`..`last` (inclusive)."""
    start = datetime(first.year, first.month, first.day, tzinfo=UTC)
    end = datetime(last.year, last.month, last.day, tzinfo=UTC) + timedelta(days=1)
    raw = adapter.raw_frame(
        symbol, Timeframe.M1, adapter.clock.to_server(start), adapter.clock.to_server(end)
    )
    bars = raw.drop(columns="time")
    bars.insert(0, "ts", adapter.clock.to_utc(raw["time"].to_numpy()))
    return bars.drop_duplicates("ts").sort_values("ts").reset_index(drop=True)


def download_symbol(
    adapter: Mt5Adapter,
    symbol: str,
    start: date | None,
    end: date | None,
    cache_dir: Path = MT5_CACHE_DIR,
    chunk_days: int = CHUNK_DAYS,
    min_day_bars: int = MIN_DAY_BARS,
    log=lambda text: None,
) -> DownloadResult:
    """Write the day files of `symbol` for UTC days `start`..`end` (inclusive; defaults: all
    history, up to yesterday). Existing day files are overwritten."""
    start = start or FIRST_DAY
    end = end or adapter.now().astimezone(UTC).date() - timedelta(days=1)
    first_bar: date | None = None
    bars_n = written = empty = 0
    first_day = last_day = None
    day = start
    while day <= end:
        stop = min(day + timedelta(days=chunk_days - 1), end)
        try:
            # one padded day each side: a UTC day sits in two server days
            bars = utc_bars(adapter, symbol, day - timedelta(days=1), stop + timedelta(days=1))
        except Mt5Error:
            if first_bar is not None:
                raise
            bars = None  # before the terminal's history: not an error, nothing to write
        by_day = {} if bars is None else dict(tuple(bars.groupby(bars["ts"].dt.date)))
        if first_bar is None:
            dense = [d for d, part in by_day.items() if len(part) >= min_day_bars]
            first_bar = min(dense, default=None)
        if first_bar is not None:
            for d in (day + timedelta(days=i) for i in range((stop - day).days + 1)):
                if d <= first_bar:  # the first day with real bars is partial
                    continue
                part = by_day.get(d)
                frame = empty_cache_frame() if part is None else cache_frame(part)
                write_atomic(frame, cache_path(cache_dir, symbol, d))
                bars_n += len(frame)
                written += 1
                empty += part is None
                first_day, last_day = first_day or d, d
            log(f"{symbol} {stop}: {bars_n:,} bars, {written} days")
        day = stop + timedelta(days=1)
    return DownloadResult(symbol, bars_n, written, empty, first_day, last_day)
