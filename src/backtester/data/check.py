"""Data check report for the Dukascopy M1 cache.

    python -m backtester.data.check XAUUSD GBPUSD GBPJPY
    python -m backtester.data.check XAUUSD --start 2024-01-01 --spot 2026-09-02T13:30

Spec: ROADMAP.md › 0.3, ARCHITECTURE.md › Data sources › Dukascopy.

Per symbol it prints:

1. Coverage: first/last traded minute, cached days, days cached empty, days missing from
   the cache between the first and last cached day.
2. Gaps between traded minutes (after dropping flat zero-volume filler, exactly like the
   resampler). Gaps are classified by the 17:00 New York daily close they contain, so the
   rules hold in summer and winter without a holiday calendar:
   - daily break: contains one close, short (gold: 17:00-18:00 NY)
   - weekend: contains a Friday close (Fri 17:00 -> Sun 17:00/18:00 NY)
   - weekend + holiday: same, but longer than a normal weekend
   - holiday, shortened day: contains a close, longer than a break, shorter than a day
     (early close / late open, e.g. US holidays)
   - holiday, closed: contains a close and lasts a day or more, no Friday close
   - not downloaded: touches a day missing from the cache (not a market gap)
   - unexpected: no close inside and at least `min_unexpected_gap_min` long
   - short: no close inside, shorter than that (only counted; quiet minutes happen)
3. Duplicates, minutes off the whole minute, rows in the wrong day file, non-empty files
   without 1440 rows.
4. Broken candles: high < low, open/close outside high-low, prices <= 0, minutes with
   only bid or only ask, ask < bid. Plus outliers for information: spread far above its
   median, and jumps between consecutive minutes far above the median minute range.
5. Lowest and highest bid per year (catches a wrong point factor over the whole history).
6. Spot check: a few candles in UTC, New York and MT5 server time, to compare by hand
   with TradingView or MT5.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from enum import Enum
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from backtester.core.models import Timeframe
from backtester.data.adapters.cache_adapter import CacheAdapter, day_ranges
from backtester.data.dukascopy import DEFAULT_CACHE_DIR, POINT_FACTORS, read_cached_day
from backtester.data.resample import drop_flat_minutes

NEW_YORK = ZoneInfo("America/New_York")
MINUTE = timedelta(minutes=1)
_SIDES = ("bid", "ask")
_FIELDS = ("open", "high", "low", "close")


@dataclass(frozen=True, slots=True)
class DataCheckConfig:
    daily_close_ny: time = time(17, 0)  # FX/metals trading day ends 17:00 New York
    daily_break_max_min: int = 90  # longer gap around the close = shortened day
    weekend_max_min: int = 50 * 60  # gold Fri 17:00 -> Sun 18:00 NY is 49 h
    min_unexpected_gap_min: int = 5  # shorter gaps without a close are only counted
    spread_outlier_factor: float = 10.0  # x median spread
    jump_outlier_factor: float = 20.0  # x median minute range (high - low)
    examples: int = 5  # rows listed per finding
    # Many MT5 brokers (FTMO too, verify in the terminal) run server time so that
    # 17:00 New York is 00:00 server time, i.e. UTC+2 in winter / UTC+3 in summer.
    mt5_hours_after_new_york: int = 7
    spot_timeframe: Timeframe = Timeframe.M5
    spot_times_utc: tuple[time, ...] = (time(1, 0), time(8, 0), time(13, 30))


DEFAULT_CONFIG = DataCheckConfig()


class GapKind(Enum):
    DAILY_BREAK = "daily break"
    WEEKEND = "weekend"
    WEEKEND_HOLIDAY = "weekend + holiday"
    SHORTENED_DAY = "holiday, shortened day"
    CLOSED_DAY = "holiday, closed"
    NOT_DOWNLOADED = "not downloaded"
    UNEXPECTED = "unexpected"
    SHORT = "short"


@dataclass(frozen=True, slots=True)
class Gap:
    start: datetime  # first missing minute (UTC)
    end: datetime  # first traded minute after the gap (UTC)
    kind: GapKind

    @property
    def minutes(self) -> int:
        return int((self.end - self.start) / MINUTE)


@dataclass
class Finding:
    """A named check with how many rows failed it and the first few of them."""

    name: str
    count: int
    examples: list[str] = field(default_factory=list)


@dataclass
class SymbolReport:
    symbol: str
    cached_days: list[date]
    empty_days: list[date]
    missing_days: list[date]  # between first and last cached day
    first_traded: datetime | None
    last_traded: datetime | None
    traded_minutes: int
    gaps: list[Gap]
    integrity: list[Finding]  # must be zero
    outliers: list[Finding]  # for information
    price_range: pd.DataFrame  # per year: low, high
    spot: pd.DataFrame


def daily_closes(start: datetime, end: datetime, config: DataCheckConfig) -> list[datetime]:
    """UTC times of the New York daily close in [start, end)."""
    first = start.astimezone(NEW_YORK).date() - timedelta(days=1)
    last = end.astimezone(NEW_YORK).date() + timedelta(days=1)
    out = []
    for i in range((last - first).days + 1):
        close = datetime.combine(first + timedelta(days=i), config.daily_close_ny, NEW_YORK)
        if start <= close.astimezone(UTC) < end:
            out.append(close)
    return out


def classify_gap(
    start: datetime, end: datetime, missing_days: set[date], config: DataCheckConfig
) -> GapKind:
    """Spec: ROADMAP.md › 0.3 (expected gaps: weekends, holidays, daily break)."""
    last_missing = end - MINUTE
    days = {
        start.date() + timedelta(days=i)
        for i in range((last_missing.date() - start.date()).days + 1)
    }
    if days & missing_days:
        return GapKind.NOT_DOWNLOADED
    minutes = (end - start) / MINUTE
    closes = daily_closes(start, end, config)
    if not closes:
        return GapKind.UNEXPECTED if minutes >= config.min_unexpected_gap_min else GapKind.SHORT
    if any(c.weekday() == 4 for c in closes):
        return GapKind.WEEKEND if minutes <= config.weekend_max_min else GapKind.WEEKEND_HOLIDAY
    if minutes <= config.daily_break_max_min:
        return GapKind.DAILY_BREAK
    return GapKind.SHORTENED_DAY if minutes < 24 * 60 else GapKind.CLOSED_DAY


def find_gaps(traded_ts: pd.Series, missing_days: set[date], config: DataCheckConfig) -> list[Gap]:
    ts = traded_ts.sort_values(ignore_index=True)
    step = ts.diff()
    gaps = []
    for i in step.index[step > MINUTE]:
        start = (ts[i - 1] + MINUTE).to_pydatetime()
        end = ts[i].to_pydatetime()
        gaps.append(Gap(start, end, classify_gap(start, end, missing_days, config)))
    return gaps


def integrity_findings(
    raw: pd.DataFrame, file_day: pd.Series, config: DataCheckConfig
) -> list[Finding]:
    """Checks every cached row must pass. `file_day` = the day of the file each row came from."""
    n = config.examples

    def finding(name: str, mask: pd.Series) -> Finding:
        rows = raw.loc[mask, "ts"].head(n)
        return Finding(name, int(mask.sum()), [_fmt_ts(t) for t in rows])

    ts = raw["ts"]
    out = [
        finding("duplicate timestamps", ts.duplicated(keep=False)),
        finding("not on a whole minute", ts != ts.dt.floor("min")),
        finding("row in the wrong day file", ts.dt.date != file_day),
        finding(
            "bid without ask or ask without bid", raw["bid_close"].isna() != raw["ask_close"].isna()
        ),
    ]
    for side in _SIDES:
        o, h, lo, c = (raw[f"{side}_{f}"] for f in _FIELDS)
        present = c.notna()
        out += [
            finding(f"{side}: high < low", present & (h < lo)),
            finding(
                f"{side}: open/close outside high-low",
                present & ((o > h) | (c > h) | (o < lo) | (c < lo)),
            ),
            finding(f"{side}: price <= 0", present & ((o <= 0) | (h <= 0) | (lo <= 0) | (c <= 0))),
        ]
    traded = raw.index.isin(drop_flat_minutes(raw).index)
    out.append(
        finding("ask < bid (negative spread)", traded & (raw["ask_close"] < raw["bid_close"]))
    )
    return out


def outlier_findings(traded: pd.DataFrame, config: DataCheckConfig) -> list[Finding]:
    """Unusual but possibly real minutes (news, rollover). Listed largest first."""
    n = config.examples
    traded = traded.sort_values("ts", ignore_index=True)
    spread = traded["ask_close"] - traded["bid_close"]
    rng = traded["bid_high"] - traded["bid_low"]
    consecutive = traded["ts"].diff() == MINUTE
    jump = (traded["bid_open"] - traded["bid_close"].shift()).abs().where(consecutive)

    def finding(name: str, values: pd.Series, limit: float) -> Finding:
        hits = values[values > limit].sort_values(ascending=False)
        examples = [f"{_fmt_ts(traded['ts'][i])}  {values[i]:.5g}" for i in hits.index[:n]]
        return Finding(f"{name} (> {limit:.5g})", len(hits), examples)

    return [
        finding(
            f"spread > {config.spread_outlier_factor:g} x median",
            spread,
            config.spread_outlier_factor * spread.median(),
        ),
        finding(
            f"jump between minutes > {config.jump_outlier_factor:g} x median range",
            jump,
            config.jump_outlier_factor * rng[rng > 0].median(),
        ),
    ]


def price_range(traded: pd.DataFrame) -> pd.DataFrame:
    year = traded["ts"].dt.year.rename("year")
    return traded.groupby(year).agg(low=("bid_low", "min"), high=("bid_high", "max"))


def spot_check(
    adapter: CacheAdapter, symbol: str, times: list[datetime], config: DataCheckConfig
) -> pd.DataFrame:
    """The candles containing each time, with UTC, New York and MT5 server open times."""
    tf = config.spot_timeframe
    rows = []
    for t in times:
        open_ts = pd.Timestamp(t).floor(f"{tf.value}min")
        frame = adapter.fetch_frame(
            symbol, tf, open_ts.to_pydatetime(), (open_ts + tf.duration).to_pydatetime()
        )
        ny = open_ts.tz_convert(NEW_YORK)
        mt5 = ny.tz_localize(None) + timedelta(hours=config.mt5_hours_after_new_york)
        row = {
            "UTC": open_ts.strftime("%Y-%m-%d %H:%M"),
            "New York": ny.strftime("%a %H:%M"),
            "MT5 server": mt5.strftime("%Y-%m-%d %H:%M"),
        }
        if frame.empty:
            row.update(open="no candle")
        else:
            c = frame.iloc[0]
            row.update(open=c.open, high=c.high, low=c.low, close=c.close, spread=c.spread)
        rows.append(row)
    return pd.DataFrame(rows)


def default_spot_times(
    report_days: list[date], traded_days: set[date], config: DataCheckConfig
) -> list[datetime]:
    """The configured times on the latest cached Tue/Wed/Thu that has trading."""
    for day in reversed(report_days):
        if day.weekday() in (1, 2, 3) and day in traded_days:
            return [datetime.combine(day, t, UTC) for t in config.spot_times_utc]
    return []


def check_symbol(
    cache_dir: Path,
    symbol: str,
    start: date | None = None,
    end: date | None = None,
    spot: list[datetime] | None = None,
    config: DataCheckConfig = DEFAULT_CONFIG,
) -> SymbolReport:
    """Build the report for days start <= day < end that are in the cache."""
    paths = {}
    for path in (Path(cache_dir) / symbol).glob("*/*.parquet"):
        day = date.fromisoformat(path.stem)
        if (start is None or day >= start) and (end is None or day < end):
            paths[day] = path
    days = sorted(paths)
    raw, file_day, empty = _read_days(paths)
    missing = []
    if days:
        span = [days[0] + timedelta(days=i) for i in range((days[-1] - days[0]).days + 1)]
        missing = [d for d in span if d not in paths]
    report = SymbolReport(
        symbol=symbol,
        cached_days=days,
        empty_days=empty,
        missing_days=missing,
        first_traded=None,
        last_traded=None,
        traded_minutes=0,
        gaps=[],
        integrity=[],
        outliers=[],
        price_range=pd.DataFrame(),
        spot=pd.DataFrame(),
    )
    if raw.empty:
        return report

    rows_per_file = Counter(file_day)
    short_files = [str(d) for d, k in rows_per_file.items() if k != 24 * 60]
    report.integrity = [
        *integrity_findings(raw, file_day, config),
        Finding(
            "non-empty file without 1440 rows", len(short_files), short_files[: config.examples]
        ),
    ]
    traded = drop_flat_minutes(raw).sort_values("ts", ignore_index=True)
    if traded.empty:
        return report

    report.first_traded = traded["ts"].iloc[0].to_pydatetime()
    report.last_traded = traded["ts"].iloc[-1].to_pydatetime()
    report.traded_minutes = len(traded)
    report.gaps = find_gaps(traded["ts"], set(missing), config)
    report.outliers = outlier_findings(traded, config)
    report.price_range = price_range(traded)
    spot_times = spot or default_spot_times(days, set(traded["ts"].dt.date), config)
    if spot_times:
        report.spot = spot_check(CacheAdapter(cache_dir), symbol, spot_times, config)
    return report


def _read_days(paths: dict[date, Path]) -> tuple[pd.DataFrame, pd.Series, list[date]]:
    """All non-empty cached days concatenated, the file day of each row, and the empty days."""
    frames, file_days, empty = [], [], []
    for day, path in sorted(paths.items()):
        frame = read_cached_day(path)
        if frame.empty:
            empty.append(day)
        else:
            frames.append(frame)
            file_days.append(pd.Series(day, index=range(len(frame))))
    if not frames:
        return pd.DataFrame(), pd.Series(dtype=object), empty
    return pd.concat(frames, ignore_index=True), pd.concat(file_days, ignore_index=True), empty


def format_report(r: SymbolReport, config: DataCheckConfig = DEFAULT_CONFIG) -> str:
    n = config.examples
    lines = [f"===== {r.symbol} =====", ""]
    if not r.cached_days:
        return "\n".join([*lines, "No cached days. Download first."])

    lines += [
        "Coverage",
        f"  cached days      {len(r.cached_days)}  ({r.cached_days[0]} .. {r.cached_days[-1]})",
        f"  first traded     {_fmt_ts(r.first_traded)} UTC",
        f"  last traded      {_fmt_ts(r.last_traded)} UTC",
        f"  traded minutes   {r.traded_minutes}",
        f"  cached as empty  {len(r.empty_days)}"
        + (f"  ({day_ranges(r.empty_days)})" if r.empty_days else ""),
        f"  NOT DOWNLOADED   {len(r.missing_days)}"
        + (f"  ({day_ranges(r.missing_days)})" if r.missing_days else ""),
        "",
        "Gaps between traded minutes (New York close = 17:00 NY)",
    ]
    by_kind: dict[GapKind, list[Gap]] = {k: [] for k in GapKind}
    for g in r.gaps:
        by_kind[g.kind].append(g)
    for kind, gaps in by_kind.items():
        if not gaps:
            continue
        mins = sorted({g.minutes for g in gaps})
        typical = Counter(g.minutes for g in gaps).most_common(1)[0][0]
        lines.append(
            f"  {kind.value:<24}{len(gaps):>6}   minutes: typical {typical}, min {mins[0]}, max {mins[-1]}"
        )
        if kind in (GapKind.SHORT, GapKind.DAILY_BREAK, GapKind.WEEKEND):
            continue
        shown = gaps if kind is not GapKind.UNEXPECTED else sorted(gaps, key=lambda g: -g.minutes)
        for g in shown[: 3 * n]:
            lines.append(f"      {_fmt_gap(g)}")
        if len(shown) > 3 * n:
            lines.append(f"      ... {len(shown) - 3 * n} more")

    lines += ["", "Integrity (all must be 0)"]
    for f in r.integrity:
        lines.append(_fmt_finding(f, n, flag=f.count > 0))
    lines += ["", "Outliers (for information; can be real: news, rollover)"]
    for f in r.outliers:
        lines.append(_fmt_finding(f, n, flag=False))

    lines += ["", "Bid price range per year (wrong point factor = off by x10 / x100)"]
    for year, row in r.price_range.iterrows():
        lines.append(f"  {year}  low {row.low:<12.6g} high {row.high:.6g}")

    if not r.spot.empty:
        lines += [
            "",
            (
                f"Spot check: compare with TradingView / MT5 ({config.spot_timeframe.name}, bid; "
                f"MT5 server time assumed = New York + {config.mt5_hours_after_new_york} h)"
            ),
        ]
        table = r.spot.to_string(
            index=False, float_format=lambda x: f"{x:.5f}".rstrip("0").rstrip(".")
        )
        lines += ["  " + line for line in table.splitlines()]
    return "\n".join(lines)


def _fmt_ts(t) -> str:
    return pd.Timestamp(t).strftime("%Y-%m-%d %H:%M")


def _fmt_gap(g: Gap) -> str:
    ny = pd.Timestamp(g.start).tz_convert(NEW_YORK)
    hours = g.minutes / 60
    return (
        f"{_fmt_ts(g.start)} -> {_fmt_ts(g.end)} UTC  ({g.minutes} min = {hours:.1f} h, "
        f"starts {ny:%a %H:%M} NY)"
    )


def _fmt_finding(f: Finding, n: int, flag: bool) -> str:
    mark = "  !! " if flag else "     "
    line = f"{mark}{f.name:<58}{f.count:>8}"
    if f.examples:
        line += "   e.g. " + ", ".join(f.examples[:n])
    return line


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("symbols", nargs="+", choices=sorted(POINT_FACTORS))
    p.add_argument("--start", type=date.fromisoformat, help="first day, YYYY-MM-DD (UTC)")
    p.add_argument("--end", type=date.fromisoformat, help="end day, exclusive (UTC)")
    p.add_argument(
        "--spot",
        type=lambda s: datetime.fromisoformat(s).replace(tzinfo=UTC),
        action="append",
        help="UTC time of a candle to print for comparison (repeatable), e.g. 2026-09-02T13:30",
    )
    p.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    args = p.parse_args(argv)

    problems = False
    for symbol in args.symbols:
        report = check_symbol(args.cache_dir, symbol, args.start, args.end, args.spot)
        print(format_report(report), end="\n\n", flush=True)
        problems |= any(f.count for f in report.integrity) or bool(report.missing_days)
        problems |= any(g.kind is GapKind.UNEXPECTED for g in report.gaps)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
