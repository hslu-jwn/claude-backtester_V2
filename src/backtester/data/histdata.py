"""Import histdata.com M1 files (MetaTrader format) into the Parquet cache.

    python -m backtester.data.histdata data/raw/histdata/
    python -m backtester.data.histdata data/raw/histdata/DAT_MT_GBPUSD_M1_202609.csv

Spec: ARCHITECTURE.md › Data sources › histdata.com.

One file per symbol and month, named `DAT_MT_{SYMBOL}_M1_{YYYYMM}.csv`, one minute per line:

    2026.09.01,00:00,1.354050,1.354070,1.354020,1.354060,0
    date,      time,  open,    high,    low,     close,   volume

- Times are the minute's open in **New York local time with daylight saving**
  (`America/New_York`: UTC−4 in summer, UTC−5 in winter), so every row is converted to UTC.
  HistData's FAQ says "EST without daylight saving", but comparing candles with
  TradingView showed otherwise (ARCHITECTURE.md › Data sources › histdata.com).
  US clocks change on a Sunday at 02:00, when FX is closed, so the skipped and the
  repeated local hour should have no minutes; if one does, the import stops
  (`HistdataError`) instead of guessing its UTC time.
- Prices are **bid** only and already decimal (no point factor). The `ask_*` columns are
  left empty (NaN), so candles get `spread` = NaN (unknown).
- Volume is always 0 in these files, i.e. unknown: it is stored as NaN, not 0. Minutes
  without trading are **missing** rather than flat filler, so `drop_flat_minutes` (which
  only drops flat minutes with volume exactly 0) never removes a histdata minute, not even
  a real quiet minute with O = H = L = C.

The cache has the same layout and columns as the Dukascopy one (`data/dukascopy.py`), but
lives in its own folder (`data/cache/histdata/` by default) so the two sources never mix.
A month file covers UTC from New York midnight of the 1st (04:00 UTC in summer, 05:00 in
winter) to New York midnight of the next month's 1st, so only
UTC days fully inside the imported months are written (the 1st of the first month is only
complete if the month before is imported too). Days in range without minutes (weekends)
are cached as empty. Days already cached are overwritten (re-importing refreshes them).
"""

from __future__ import annotations

import argparse
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from backtester.data.dukascopy import _COLUMNS, _empty_cache_frame, _write_atomic, cache_path

DEFAULT_HISTDATA_CACHE_DIR = Path("data/cache/histdata")
HISTDATA_TZ = ZoneInfo("America/New_York")  # with DST, verified against TradingView
_FILE_NAME = re.compile(r"^DAT_MT_(?P<symbol>[A-Z0-9]+)_M1_(?P<month>\d{6})\.csv$")
_RAW_COLUMNS = ["date", "time", "open", "high", "low", "close", "volume"]


class HistdataError(ValueError):
    """A file that doesn't look like a histdata MT M1 file; nothing is cached from it."""


@dataclass(frozen=True, slots=True)
class MonthFile:
    path: Path
    symbol: str
    month: date  # first day of the month (New York time)

    @property
    def utc_start(self) -> datetime:
        """First minute this file can contain, in UTC."""
        return _local_midnight(self.month)

    @property
    def utc_end(self) -> datetime:
        """End (exclusive) of what this file covers, in UTC."""
        nxt = (self.month.replace(day=28) + timedelta(days=4)).replace(day=1)
        return _local_midnight(nxt)


@dataclass(frozen=True, slots=True)
class ImportResult:
    symbol: str
    days_written: list[date]
    days_empty: list[date]  # written as empty (no minutes, e.g. Saturday)
    days_partial: list[date]  # touched by the files but not complete: not written
    minutes: int
    merged_minutes: int = 0  # minutes that appeared more than once in the files


def month_file(path: Path) -> MonthFile:
    m = _FILE_NAME.match(path.name)
    if not m:
        raise HistdataError(f"{path.name}: expected a name like DAT_MT_GBPUSD_M1_202609.csv")
    month = date(int(m["month"][:4]), int(m["month"][4:]), 1)
    return MonthFile(path, m["symbol"], month)


def parse_histdata_mt(text_or_path, month_file_: MonthFile | None = None) -> pd.DataFrame:
    """Rows of one file as cache columns (`ts` UTC, bid OHLC, bid_volume NaN, ask NaN).

    Fails loudly on broken rows (OHLC inconsistent, rows outside the file's month) instead
    of caching something plausible-looking. Duplicate minutes are merged
    (`merge_duplicate_minutes`); `frame.attrs["merged_minutes"]` says how many.
    """
    raw = pd.read_csv(
        text_or_path,
        header=None,
        names=_RAW_COLUMNS,
        dtype={"date": str, "time": str},
    )
    if raw.empty:
        return _empty_cache_frame()
    local = pd.to_datetime(raw["date"] + " " + raw["time"], format="%Y.%m.%d %H:%M")
    try:
        ts = local.dt.tz_localize(HISTDATA_TZ, ambiguous="raise", nonexistent="raise")
    except ValueError as e:  # repeated (ambiguous) or skipped (nonexistent) local time
        raise HistdataError(
            f"local time that doesn't map to one UTC time (DST change night): {e}"
        ) from e
    ts = ts.dt.tz_convert(UTC)
    o, h, lo, c = (raw[f].astype("float64") for f in ("open", "high", "low", "close"))
    bad = (h < lo) | (o > h) | (o < lo) | (c > h) | (c < lo) | (lo <= 0)
    if bad.any():
        raise HistdataError(f"{bad.sum()} broken rows, first: {raw[bad].iloc[0].tolist()}")
    if month_file_ is not None:
        outside = (ts < month_file_.utc_start) | (ts >= month_file_.utc_end)
        if outside.any():
            raise HistdataError(
                f"{month_file_.path.name}: {outside.sum()} rows outside "
                f"{month_file_.month:%Y-%m} (New York time), first: {raw[outside].iloc[0].tolist()}"
            )
    nan = float("nan")
    frame = pd.DataFrame(
        {
            "ts": ts,
            "bid_open": o,
            "bid_high": h,
            "bid_low": lo,
            "bid_close": c,
            "bid_volume": nan,  # file says 0 = unknown, see module docstring
            **{f"ask_{f}": nan for f in ("open", "high", "low", "close", "volume")},
        }
    )
    return merge_duplicate_minutes(frame)


def merge_duplicate_minutes(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per minute, sorted by time; `attrs["merged_minutes"]` = minutes merged.

    histdata files sometimes repeat a minute out of order, always as single-tick rows
    around a real one, e.g. 10:57, 10:58 (one tick), 10:57 (one tick), 10:58. The rows of
    one minute are merged in file order: open of the first, max high, min low, close of
    the last. So no tick is lost and the merged minute is still a valid candle.
    """
    dup = frame["ts"].duplicated(keep=False)
    merged = int(frame.loc[dup, "ts"].nunique())
    if merged:
        frame = (
            frame.groupby("ts", sort=False)
            .agg(
                {
                    "bid_open": "first",
                    "bid_high": "max",
                    "bid_low": "min",
                    "bid_close": "last",
                    **{c: "first" for c in _COLUMNS if c.startswith("ask_") or c == "bid_volume"},
                }
            )
            .reset_index()
        )
    out = frame.sort_values("ts", ignore_index=True)[_COLUMNS]
    out.attrs["merged_minutes"] = merged
    return out


def import_files(paths: Iterable[Path], cache_dir: Path = DEFAULT_HISTDATA_CACHE_DIR):
    """Import month files (any symbols) and return one ImportResult per symbol."""
    by_symbol: dict[str, list[MonthFile]] = {}
    for path in paths:
        mf = month_file(Path(path))
        by_symbol.setdefault(mf.symbol, []).append(mf)
    return [import_symbol(sym, files, cache_dir) for sym, files in sorted(by_symbol.items())]


def import_symbol(symbol: str, files: list[MonthFile], cache_dir: Path) -> ImportResult:
    files = sorted(files, key=lambda f: f.month)
    if len({f.month for f in files}) != len(files):
        raise HistdataError(f"{symbol}: the same month given twice")
    parts = [parse_histdata_mt(f.path, f) for f in files]
    merged = sum(p.attrs.get("merged_minutes", 0) for p in parts)
    frame = pd.concat(parts, ignore_index=True)
    covered = _covered_intervals(files)
    days = sorted({d for f in files for d in _days_touched(f.utc_start, f.utc_end)})
    written, empty, partial = [], [], []
    day_of = frame["ts"].dt.date
    for day in days:
        start = datetime.combine(day, datetime.min.time(), UTC)
        if not any(a <= start and start + timedelta(days=1) <= b for a, b in covered):
            partial.append(day)
            continue
        rows = frame[day_of == day].reset_index(drop=True)
        _write_atomic(
            rows if not rows.empty else _empty_cache_frame(), cache_path(cache_dir, symbol, day)
        )
        (empty if rows.empty else written).append(day)
    minutes = int(frame["ts"].dt.date.isin(set(written)).sum())
    return ImportResult(symbol, written, empty, partial, minutes, merged)


def _covered_intervals(files: list[MonthFile]) -> list[tuple[datetime, datetime]]:
    """UTC intervals covered by the month files, consecutive months merged."""
    out: list[list[datetime]] = []
    for f in files:
        if out and out[-1][1] == f.utc_start:
            out[-1][1] = f.utc_end
        else:
            out.append([f.utc_start, f.utc_end])
    return [(a, b) for a, b in out]


def _days_touched(start: datetime, end: datetime) -> list[date]:
    first, last = start.date(), (end - timedelta(microseconds=1)).date()
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def _local_midnight(d: date) -> datetime:
    return datetime.combine(d, datetime.min.time(), HISTDATA_TZ).astimezone(UTC)


def main(argv: list[str] | None = None) -> int:
    from backtester.data.adapters.cache_adapter import day_ranges

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("paths", nargs="+", type=Path, help="DAT_MT_*_M1_*.csv files or folders")
    p.add_argument("--cache-dir", type=Path, default=DEFAULT_HISTDATA_CACHE_DIR)
    args = p.parse_args(argv)
    files = [
        f
        for p_ in args.paths
        for f in (sorted(p_.glob("DAT_MT_*_M1_*.csv")) if p_.is_dir() else [p_])
    ]
    if not files:
        p.error("no DAT_MT_*_M1_*.csv files found")
    for r in import_files(files, args.cache_dir):
        print(f"{r.symbol}: {len(r.days_written)} days, {r.minutes:,} minutes -> {args.cache_dir}")
        if r.merged_minutes:
            print(f"  merged {r.merged_minutes} minutes that appeared twice (feed glitch)")
        if r.days_empty:
            print(f"  cached as empty (no minutes): {day_ranges(r.days_empty)}")
        if r.days_partial:
            print(
                f"  NOT written, only partly in the files (a New York month starts at 04:00 or 05:00 UTC): "
                f"{day_ranges(r.days_partial)}; import the neighbouring month to complete them"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
