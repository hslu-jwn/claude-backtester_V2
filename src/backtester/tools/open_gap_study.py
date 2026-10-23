"""Open / gap / trend-day study on the index CFDs. Research only, it changes no setting.

    python -m backtester.tools.open_gap_study
    python -m backtester.tools.open_gap_study --symbols NAS100 --start 2023-01-01

For each symbol the M1 bars of the cash session (09:30-16:00 New York) are grouped into days;
holidays, half days and data holes are classified and counted (`exclusions.csv`), the regular
days become one record each (`days.csv`) and are summarized per half (2020-22 / 2023-26):

- `gap_fill.csv`: gap = cash open - previous cash close in daily ATR; share filled the same day
  and by day 3, against the "extend" baseline (the same-size move the other way), which level
  is touched first (previous close = "fill" or the mirror level = "extend", i.e. a 1:1 fade
  before costs) and the claims 48 % / 76 % (Hougaard);
- `first30.csv`: continuation of the first 30 minutes (previous close -> 10:00) over the rest
  of the day;
- `trend_days.csv`: share of trend days (open and close at the opposite ends of the range),
  by weekday / month part and by the features known at 11:00 (claim: about 20 %);
- `extremes.csv`: share of days whose high / low printed in the first 90 minutes, first hour,
  last hour, against uniform and random-walk shares (claim: 90 % in the first 90 minutes);
- `last_hour.csv`: close position and move after a new high / low in the last hour.

Spec: ROADMAP.md › 11.2; knowledge/ideas.md I-09, I-39. The CFD trades through the night,
so the "gap" is the move from the cash close to the cash open; effects found here are
frequencies against baselines, not net profit (no costs, no rule).
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from backtester.analytics.open_gap import (
    Bar,
    OpenGapConfig,
    cash_days,
    day_records,
    missing_weekdays,
    summarize_extremes,
    summarize_first30,
    summarize_gaps,
    summarize_last_hour,
    summarize_trend,
)
from backtester.core.models import Timeframe
from backtester.data.sources import DEFAULT_SOURCES
from backtester.paths import RESULTS_DIR
from backtester.tools.research_helpers import write_csv

SYMBOLS = ("NAS100", "US500")
CLAIM_SAME_DAY, CLAIM_DAY3 = 0.48, 0.76  # Hougaard, DAX, unsourced
CLAIM_TREND_DAYS, CLAIM_FIRST90 = 0.20, 0.90
TABLES = ("days", "exclusions", "gap_fill", "first30", "trend_days", "extremes", "last_hour")


def load_m1(symbol: str, start: date, end: date, cfg: OpenGapConfig | None = None) -> list[Bar]:
    """The cached M1 bars of [start, end] that fall in the cash session, as `Bar`s."""
    cfg = cfg or OpenGapConfig()
    cached = sorted(d for d in DEFAULT_SOURCES.cached_days(symbol) if start <= d <= end)
    if not cached:
        raise ValueError(f"{symbol}: no cached days between {start} and {end}")
    first = datetime(cached[0].year, cached[0].month, cached[0].day, tzinfo=UTC)
    last = cached[-1] + timedelta(days=1)
    frame = DEFAULT_SOURCES.adapter(symbol).fetch_frame(
        symbol, Timeframe.M1, first, datetime(last.year, last.month, last.day, tzinfo=UTC)
    )
    local = frame["ts"].dt.tz_convert(cfg.zone)
    open_minute = cfg.cash_open.hour * 60 + cfg.cash_open.minute
    minute = local.dt.hour * 60 + local.dt.minute - open_minute
    cash = frame[(minute >= 0) & (minute < cfg.session_minutes)]
    return [
        Bar(ts.to_pydatetime(), float(o), float(h), float(low), float(c))
        for ts, o, h, low, c in zip(
            cash["ts"], cash["open"], cash["high"], cash["low"], cash["close"], strict=True
        )
    ]


def _fmt(value, spec: str = ".0%") -> str:
    return "-" if value is None else format(value, spec)


def _find(rows: list[dict], **match) -> dict | None:
    return next((r for r in rows if all(r.get(k) == v for k, v in match.items())), None)


def print_symbol(symbol: str, results: dict[str, list[dict]], cfg: OpenGapConfig) -> None:
    halves = (*cfg.half_labels, "all")
    print(f"\n=== {symbol} ===")
    print(
        f"gap fill, all directions (claims: same day {CLAIM_SAME_DAY:.0%}, by day 3 {CLAIM_DAY3:.0%})"
    )
    print(
        f"{'bucket':10}{'half':9}{'days':>6}{'same day':>10}{'by day 3':>10}{'extend':>8}"
        f"{'fill 1st':>10}{'ext 1st':>9}{'same bar':>10}"
    )
    for bucket in (*cfg.bucket_labels(), "all"):
        for half in halves:
            r = _find(results["gap_fill"], direction="both", bucket=bucket, half=half)
            if r:
                print(
                    f"{bucket:10}{half:9}{r['n']:>6}{_fmt(r['same_day_fill']):>10}"
                    f"{_fmt(r['by_day3_fill']):>10}{_fmt(r['extend_same_day']):>8}"
                    f"{_fmt(r['fill_first']):>10}{_fmt(r['extend_first']):>9}{_fmt(r['same_bar']):>10}"
                )
    print("\nfirst 30 minutes (previous close -> 10:00) vs the rest of the day")
    for half in halves:
        r = _find(results["first30"], half=half, bucket="all")
        if r:
            print(
                f"  {half:9} days {r['n']:>5}  continuation {_fmt(r['continuation_share'])}"
                f"  rest in that direction {_fmt(r['mean_rest_signed_atr'], '+.3f')} ATR"
                f" (t {_fmt(r['t'], '+.1f')})"
            )
    print(f"\ntrend days (claim about {CLAIM_TREND_DAYS:.0%}): share [95% interval], lift")
    for half in halves:
        for r in results["trend_days"]:
            if r["half"] == half and r["group"] in ("all", "weekday 5 Fri"):
                print(
                    f"  {half:9} {r['group']:14}{r['feature']:25} n {r['n']:>5}  "
                    f"{_fmt(r['share'])} [{_fmt(r['ci_low'])}-{_fmt(r['ci_high'])}]"
                    f"  lift {_fmt(r['lift'], '.2f')}"
                )
    print(f"\nday high / low in the window (claim: {CLAIM_FIRST90:.0%} in the first 90 minutes)")
    for r in results["extremes"]:
        print(
            f"  {r['half']:9} {r['window']:13} high {_fmt(r['high_share'])} low {_fmt(r['low_share'])}"
            f" either {_fmt(r['either_share'])}   uniform {_fmt(r['uniform_share'])}"
            f" random walk {_fmt(r['random_walk_share'])}"
        )
    print("\nlast hour: a new high / low against everything before 15:00")
    for r in results["last_hour"]:
        print(
            f"  {r['half']:9} {r['event']:9} days {r['n']:>5}"
            f"  close position {_fmt(r['mean_close_pos'], '.2f')}"
            f"  move {_fmt(r['mean_move_atr'], '+.2f')} ATR"
        )


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, default=date(2020, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date(2026, 9, 30))
    p.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    p.add_argument("--atr-period", type=int, default=OpenGapConfig().atr_period)
    p.add_argument("--out", type=Path, default=RESULTS_DIR / "open_gap_study")
    args = p.parse_args(argv)
    cfg = OpenGapConfig(atr_period=args.atr_period)
    args.out.mkdir(parents=True, exist_ok=True)

    tables: dict[str, list[dict]] = {name: [] for name in TABLES}
    for symbol in (s.upper() for s in args.symbols):
        try:
            bars = load_m1(symbol, args.start, args.end, cfg)
        except Exception as e:  # noqa: BLE001 - research tool: say what is missing, go on
            print(f"{symbol}: skipped ({type(e).__name__}: {e})", flush=True)
            continue
        days = cash_days(bars, cfg)
        records, excluded = day_records(days, cfg)
        counts = Counter((cfg.half(e["date"].year), e["reason"]) for e in excluded)
        counts.update((cfg.half(d.year), "no_bars") for d in missing_weekdays(days))
        print(
            f"{symbol}: {len(bars)} bars, {len(days)} cash days, {len(records)} regular days used",
            flush=True,
        )
        results = {
            "gap_fill": summarize_gaps(records, cfg),
            "first30": summarize_first30(records, cfg),
            "trend_days": summarize_trend(records, cfg),
            "extremes": summarize_extremes(records, cfg),
            "last_hour": summarize_last_hour(records, cfg),
        }
        tables["days"] += [{"symbol": symbol, **r} for r in records]
        tables["exclusions"] += [
            {"symbol": symbol, "half": h, "reason": reason, "days": n}
            for (h, reason), n in sorted(counts.items())
        ]
        for name, rows in results.items():
            tables[name] += [{"symbol": symbol, **r} for r in rows]
        print_symbol(symbol, results, cfg)
        left = ", ".join(f"{h} {reason} {n}" for (h, reason), n in sorted(counts.items()))
        print(f"\nleft out ({symbol}): {left or 'nothing'}")
    for name, rows in tables.items():
        write_csv(args.out / f"{name}.csv", rows)
    print(f"\nwritten to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
