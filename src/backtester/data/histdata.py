"""Import histdata.com M1 files (MetaTrader format) into the Parquet cache.

    python -m backtester.data.histdata data/raw/histdata/
    python -m backtester.data.histdata data/raw/histdata/NAS100/
    python -m backtester.data.histdata data/raw/histdata/DAT_MT_GBPUSD_M1_202609.csv

Spec: ARCHITECTURE.md › Data sources › histdata.com.

A folder is searched with its subfolders (`data/raw/histdata/<SYMBOL>/`, one per pair).
histdata's index names are cached under ours (`SYMBOL_NAMES`: NSXUSD -> NAS100,
SPXUSD -> US500); the indices use the same clock as forex and gold (their daily break
moves with gold's in the US-only summer time weeks).

One file per symbol and month, `DAT_MT_{SYMBOL}_M1_{YYYYMM}.csv`, or per symbol and year
for full past years, `DAT_MT_{SYMBOL}_M1_{YYYY}.csv`; either may come inside a zip file
(histdata.com's download, e.g. `HISTDATA_COM_MT_XAUUSD_M1_2023.zip`), which is read without
unpacking. One minute per line:

    2026.09.01,00:00,1.354050,1.354070,1.354020,1.354060,0
    date,      time,  open,    high,    low,     close,   volume

- Times are the minute's open on **New York's standard time (UTC-5), moved one hour
  forward while Europe is on summer time** (UTC-4 then), so every row is converted to UTC
  (`histdata_to_utc`). HistData's FAQ says "EST without daylight saving", but comparing
  candles with TradingView showed otherwise: the clock follows summer time, and on the
  **European** dates. In the weeks where only the US is on summer time (March and late
  October / early November) New York time with US daylight saving put every candle one
  hour early (user, 2026-10-09: TradingView's XAUUSD 5m candle of 2026-03-18 14:00 UTC is
  the one that was cached at 13:00). Europe changes on a Sunday at 01:00 UTC, when FX is
  closed, so the skipped and the repeated hour should have no minutes; if one does, the
  import stops (`HistdataError`) instead of guessing its UTC time.
  Exception proven in V2.6b: local dates 2015–2018 follow America/New_York US DST.
  See ARCHITECTURE.md > Data sources and results/clock_check_histdata.md for evidence.
- Prices are **bid** only and already decimal (no point factor). The `ask_*` columns are
  left empty (NaN), so candles get `spread` = NaN (unknown).
- Volume is always 0 in these files, i.e. unknown: it is stored as NaN, not 0. Minutes
  without trading are **missing** rather than flat filler, so `drop_flat_minutes` (which
  only drops flat minutes with volume exactly 0) never removes a histdata minute, not even
  a real quiet minute with O = H = L = C.

The cache layout and columns are in `data/cache.py` (`data/cache/histdata/` by default).
A month file covers UTC from midnight of the 1st on that clock (04:00 UTC in European
summer time, 05:00 otherwise) to midnight of the next month's 1st (a year file: 1 January to the next
1 January, 05:00 UTC), so only UTC days fully inside the imported periods are written
(the first day is only complete if the period before is imported too: e.g. 1 January
00:00-05:00 UTC is in the previous year's file). Periods must not overlap (a year file and
a month file of the same year). Days in range without minutes (weekends) are cached as
empty. Days already cached are overwritten (re-importing refreshes them).
"""

from __future__ import annotations

import argparse
import io
import re
import zipfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from itertools import pairwise
from pathlib import Path
from types import MappingProxyType
from zoneinfo import ZoneInfo

import pandas as pd

from backtester.data.cache import (
    COLUMNS,
    DEFAULT_CACHE_DIR,
    cache_path,
    empty_cache_frame,
    write_atomic,
)

# histdata's clock: New York's standard offset, + Europe's summer time (module docstring)
NEW_YORK = ZoneInfo("America/New_York")
EUROPE = ZoneInfo("Europe/London")  # the EU's summer time dates (all switch at 01:00 UTC)
_HOUR = pd.Timedelta(hours=1)
_FILE_NAME = re.compile(r"^DAT_MT_(?P<symbol>[A-Z0-9]+)_M1_(?P<period>\d{6}|\d{4})\.csv$")
_RAW_COLUMNS = ["date", "time", "open", "high", "low", "close", "volume"]
# histdata's symbol in the file name -> ours (the name used by the cache, chart, costs)
SYMBOL_NAMES = MappingProxyType(
    {
        "NSXUSD": "NAS100",
        "SPXUSD": "US500",
        "GRXEUR": "GER40",
        "UKXGBP": "UK100",
        "JPXJPY": "JP225",
        "ETXEUR": "EU50",
        "WTIUSD": "USOIL",
        "BCOUSD": "UKOIL",
        "UDXUSD": "DXY",
        "AUXAUD": "AUS200",  # V2.6 step 9 (user, 2026-10-27)
        "HKXHKD": "HK50",
    }
)


class HistdataError(ValueError):
    """A file that doesn't look like a histdata MT M1 file; nothing is cached from it."""


@dataclass(frozen=True, slots=True)
class ImportConfig:
    """Spec: ARCHITECTURE.md > Data sources; V2.6b data validation settings."""

    max_day_close_jump: float = 0.25
    # A weekend alone is not an explanation for a different instrument's price.
    explained_jumps: tuple[tuple[str, date, str], ...] = (
        ("UKOIL", date(2020, 3, 9), "2020 oil price war crash (Brent 45.5 -> 33.4)"),
        ("USOIL", date(2020, 4, 19), "April 2020 WTI negative-price week / contract roll"),
        ("USOIL", date(2020, 4, 21), "day after WTI settled negative (2020-04-20), -34 %"),
        ("USOIL", date(2020, 4, 27), "WTI collapse continues after the negative settle, -26 %"),
    )

    def __post_init__(self):
        if self.max_day_close_jump <= 0:
            raise ValueError("max_day_close_jump must be positive")
        if any(not reason.strip() for _, _, reason in self.explained_jumps):
            raise ValueError("every continuity exemption needs an explanation")


IMPORT_CONFIG = ImportConfig()
# Periods in which histdata's files hold a different instrument than the symbol's name:
# symbol -> ((first invalid UTC day or None, first valid-again UTC day or None, reason), ...).
# Rows of those UTC days are dropped on import and removed from an existing cache.
INVALID_PERIODS: Mapping[str, tuple[tuple[date | None, date | None, str], ...]] = MappingProxyType(
    {
        "GER40": ((date(2020, 6, 15), None, "GRXEUR files switch instrument"),),
        "DXY": ((None, date(2018, 12, 16), "UDXUSD files are the Dow Jones until 2018-12-14"),),
        "EU50": ((date(2018, 12, 15), None, "ETXEUR files are the IBEX 35 from 2018-12-17"),),
    }
)


def is_invalid_day(symbol: str, day: date) -> bool:
    """True when `day` (UTC) lies in one of the symbol's INVALID_PERIODS."""
    return any(
        (start is None or day >= start) and (end is None or day < end)
        for start, end, _ in INVALID_PERIODS.get(symbol, ())
    )


@dataclass(frozen=True, slots=True)
class MonthFile:
    """One histdata file: a month or (`yearly`) a whole year, on histdata's clock."""

    path: Path
    symbol: str
    month: date  # first day of the period (New York time)
    yearly: bool = False
    member: str | None = None  # the csv inside `path` when `path` is a zip file

    @property
    def end(self) -> date:
        """First day after the period (New York time)."""
        if self.yearly:
            return date(self.month.year + 1, 1, 1)
        return (self.month.replace(day=28) + timedelta(days=4)).replace(day=1)

    @property
    def label(self) -> str:
        return f"{self.month:%Y}" if self.yearly else f"{self.month:%Y-%m}"

    @property
    def name(self) -> str:
        return self.member or self.path.name

    @property
    def utc_start(self) -> datetime:
        """First minute this file can contain, in UTC."""
        return _local_midnight(self.month)

    @property
    def utc_end(self) -> datetime:
        """End (exclusive) of what this file covers, in UTC."""
        return _local_midnight(self.end)

    def open(self):
        """The csv text (from the zip file when there is one)."""
        if self.member is None:
            return self.path
        with zipfile.ZipFile(self.path) as z:
            return io.StringIO(z.read(self.member).decode("utf-8"))


@dataclass(frozen=True, slots=True)
class ImportResult:
    symbol: str
    days_written: list[date]
    days_empty: list[date]  # written as empty (no minutes, e.g. Saturday)
    days_partial: list[date]  # touched by the files but not complete: not written
    minutes: int
    merged_minutes: int = 0  # minutes that appeared more than once in the files


def month_file(path: Path, member: str | None = None) -> MonthFile:
    """The period of a file from its name (`member`: the csv's name inside a zip)."""
    name = member.rsplit("/", 1)[-1] if member else path.name
    m = _FILE_NAME.match(name)
    if not m:
        raise HistdataError(
            f"{name}: expected a name like DAT_MT_GBPUSD_M1_202609.csv (month) "
            "or DAT_MT_GBPUSD_M1_2023.csv (year)"
        )
    period, symbol = m["period"], SYMBOL_NAMES.get(m["symbol"], m["symbol"])
    if len(period) == 4:
        return MonthFile(path, symbol, date(int(period), 1, 1), True, member)
    return MonthFile(path, symbol, date(int(period[:4]), int(period[4:]), 1), False, member)


def files_in(path: Path) -> list[MonthFile]:
    """The histdata files a path stands for: a csv, a zip (its DAT_MT_ csv files) or a
    folder (both kinds in it and in its subfolders)."""
    path = Path(path)
    if path.is_dir():
        return [
            f
            for p in sorted(path.iterdir())
            if p.is_dir()
            or (
                p.suffix.lower() in (".csv", ".zip")
                and p.name.upper().startswith(("DAT_MT_", "HISTDATA"))
            )
            for f in files_in(p)
        ]
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            members = [n for n in z.namelist() if _FILE_NAME.match(n.rsplit("/", 1)[-1])]
        if not members:
            raise HistdataError(f"{path.name}: no DAT_MT_..._M1_... csv inside")
        return [month_file(path, n) for n in members]
    return [month_file(path)]


def parse_histdata_mt(text_or_path, month_file_: MonthFile | None = None) -> pd.DataFrame:
    """Rows of one file as cache columns (`ts` UTC, bid OHLC, bid_volume NaN, ask NaN).

    Fails loudly on broken rows (OHLC inconsistent, rows outside the file's month) instead
    of caching something plausible-looking. Duplicate minutes are merged
    (`merge_duplicate_minutes`); `frame.attrs["merged_minutes"]` says how many.
    """
    if isinstance(text_or_path, MonthFile):
        month_file_, text_or_path = text_or_path, text_or_path.open()
    raw = pd.read_csv(
        text_or_path,
        header=None,
        names=_RAW_COLUMNS,
        dtype={"date": str, "time": str},
    )
    if raw.empty:
        return empty_cache_frame()
    local = pd.to_datetime(raw["date"] + " " + raw["time"], format="%Y.%m.%d %H:%M")
    ts = histdata_to_utc(local)
    o, h, lo, c = (raw[f].astype("float64") for f in ("open", "high", "low", "close"))
    bad = (h < lo) | (o > h) | (o < lo) | (c > h) | (c < lo) | (lo <= 0)
    if bad.any():
        raise HistdataError(f"{bad.sum()} broken rows, first: {raw[bad].iloc[0].tolist()}")
    if month_file_ is not None:
        outside = (ts < month_file_.utc_start) | (ts >= month_file_.utc_end)
        if outside.any():
            raise HistdataError(
                f"{month_file_.name}: {outside.sum()} rows outside "
                f"{month_file_.label} (New York time), first: {raw[outside].iloc[0].tolist()}"
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
                    **{c: "first" for c in COLUMNS if c.startswith("ask_") or c == "bid_volume"},
                }
            )
            .reset_index()
        )
    out = frame.sort_values("ts", ignore_index=True)[COLUMNS]
    out.attrs["merged_minutes"] = merged
    return out


def import_files(
    paths: Iterable[Path],
    cache_dir: Path = DEFAULT_CACHE_DIR,
    config: ImportConfig = IMPORT_CONFIG,
):
    """Import month / year files, csv or zip (any symbols); one ImportResult per symbol."""
    by_symbol: dict[str, list[MonthFile]] = {}
    for path in paths:
        for mf in files_in(Path(path)):
            by_symbol.setdefault(mf.symbol, []).append(mf)
    return [
        import_symbol(sym, files, cache_dir, config) for sym, files in sorted(by_symbol.items())
    ]


def import_symbol(
    symbol: str,
    files: list[MonthFile],
    cache_dir: Path,
    config: ImportConfig = IMPORT_CONFIG,
) -> ImportResult:
    files = sorted(files, key=lambda f: f.month)
    for a, b in pairwise(files):
        if b.month < a.end:
            raise HistdataError(f"{symbol}: {a.name} and {b.name} overlap (the same period twice)")
    parts = [parse_histdata_mt(f) for f in files]
    previous_close = None
    for index, (mf, part) in enumerate(zip(files, parts)):
        if index and files[index - 1].end != mf.month:
            previous_close = None  # absent periods cannot establish daily continuity
        if symbol in INVALID_PERIODS:
            keep = ~part["ts"].dt.date.map(lambda d: is_invalid_day(symbol, d))
            part = part.loc[keep].copy()
            parts[index] = part
        closes = part.groupby(part["ts"].dt.date)["bid_close"].last()
        for day, close in closes.items():
            explained = any(s == symbol and d == day for s, d, _ in config.explained_jumps)
            if (
                previous_close is not None
                and not explained
                and abs(close / previous_close - 1) > config.max_day_close_jump
            ):
                raise HistdataError(
                    f"{mf.name}: {day}: day-close price jump from {previous_close:g} to {close:g} "
                    f"exceeds {config.max_day_close_jump:.0%}; import stopped; "
                    "requires an explicit documented weekend/holiday explanation"
                )
            previous_close = close
    merged = sum(p.attrs.get("merged_minutes", 0) for p in parts)
    frame = pd.concat(parts, ignore_index=True)
    covered = _covered_intervals(files)
    days = sorted({d for f in files for d in _days_touched(f.utc_start, f.utc_end)})
    written, empty, partial = [], [], []
    by_day = {day: rows for day, rows in frame.groupby(frame["ts"].dt.date, sort=False)}
    minutes = 0
    if symbol in INVALID_PERIODS:
        # Performed only by the requested re-import job, never at module import.
        for path in (Path(cache_dir) / symbol).glob("*/*.parquet"):
            if is_invalid_day(symbol, date.fromisoformat(path.stem)):
                path.unlink()
    for day in days:
        if is_invalid_day(symbol, day):
            continue
        start = datetime.combine(day, datetime.min.time(), UTC)
        if not any(a <= start and start + timedelta(days=1) <= b for a, b in covered):
            partial.append(day)
            continue
        rows = by_day.get(day)
        if rows is None or rows.empty:
            write_atomic(empty_cache_frame(), cache_path(cache_dir, symbol, day))
            empty.append(day)
            continue
        write_atomic(rows.reset_index(drop=True), cache_path(cache_dir, symbol, day))
        written.append(day)
        minutes += len(rows)
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


def _standard_offset(zone: ZoneInfo) -> timedelta:
    """The zone's offset without summer time (from mid-January)."""
    january = datetime(2000, 1, 15, tzinfo=zone)
    return january.utcoffset() - january.dst()


def _summer_time(utc: pd.Series) -> pd.Series:
    """Europe's summer time at each UTC time (1 h or 0)."""
    local = utc.dt.tz_convert(EUROPE).dt.tz_localize(None)
    return local - utc.dt.tz_localize(None) - _standard_offset(EUROPE)


def histdata_to_utc(local: pd.Series) -> pd.Series:
    """Naive file clock -> UTC: US DST in 2015–2018, European dates otherwise.

    Spec: ARCHITECTURE.md > Data sources > histdata.com. Ambiguous/nonexistent
    transition minutes have no single answer and raise `HistdataError`.
    """
    # Proven 2015–2018 US dates: results/clock_check_histdata.md. Other years retain
    # the previously measured European dates. Spec: ARCHITECTURE.md > Data sources.
    us = local.dt.year.between(2015, 2018)
    if us.any():
        try:
            converted = local[us].dt.tz_localize(NEW_YORK, ambiguous="raise", nonexistent="raise")
        except ValueError as exc:
            raise HistdataError(f"histdata US summer time transition: {exc}") from exc
        out = pd.Series(index=local.index, dtype="datetime64[ns, UTC]")
        out.loc[us] = converted.dt.tz_convert(UTC)
        if (~us).any():
            out.loc[~us] = histdata_to_utc(local[~us])
        return out
    winter = (local - _standard_offset(NEW_YORK)).dt.tz_localize(UTC)  # if no summer time
    summer = winter - _HOUR  # if summer time
    is_winter = _summer_time(winter) == pd.Timedelta(0)
    is_summer = _summer_time(summer) == _HOUR
    unclear = is_winter == is_summer  # both (repeated hour) or neither (skipped hour)
    if unclear.any():
        raise HistdataError(
            f"{unclear.sum()} local times in the hour Europe's summer time change skips or "
            f"repeats, first: {local[unclear].iloc[0]}"
        )
    return winter.where(is_winter, summer)


def _local_midnight(d: date) -> datetime:
    """Midnight of `d` on histdata's clock, in UTC."""
    local = pd.Series([pd.Timestamp(d)])
    return histdata_to_utc(local).iloc[0].to_pydatetime()


def main(argv: list[str] | None = None) -> int:
    from backtester.data.adapters.cache_adapter import day_ranges

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("paths", nargs="+", type=Path, help="DAT_MT_*_M1_*.csv / .zip files or folders")
    p.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    p.add_argument("--max-day-close-jump", type=float, default=ImportConfig().max_day_close_jump)
    args = p.parse_args(argv)
    if not any(files_in(p_) for p_ in args.paths):
        p.error("no DAT_MT_*_M1_* files found")
    try:
        results = import_files(args.paths, args.cache_dir, ImportConfig(args.max_day_close_jump))
    except (HistdataError, ValueError) as exc:
        p.exit(1, f"histdata: {exc}\n")
    for r in results:
        print(f"{r.symbol}: {len(r.days_written)} days, {r.minutes:,} minutes -> {args.cache_dir}")
        if r.merged_minutes:
            print(f"  merged {r.merged_minutes} minutes that appeared twice (feed glitch)")
        if r.days_empty:
            print(f"  cached as empty (no minutes): {day_ranges(r.days_empty)}")
        if r.days_partial:
            print(
                f"  NOT written, only partly in the files (a New York month / year starts at 04:00 "
                f"or 05:00 UTC): {day_ranges(r.days_partial)}; import the neighbouring period "
                "to complete them"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
