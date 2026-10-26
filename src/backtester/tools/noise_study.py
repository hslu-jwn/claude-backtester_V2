"""Noise study: how noisy is each symbol on each timeframe, per year and per half, and does
noise explain strategy 4's split halves? Research only, it changes no setting.

    python -m backtester.tools.noise_study
    python -m backtester.tools.noise_study --symbols XAUUSD NAS100 --timeframes H1 H4 D1
    python -m backtester.tools.noise_study --split-csv results/trend_grid/split.csv --join-n 20

The efficiency ratio ER(n) = |close - close n bars ago| / sum of the n bar-to-bar moves
(0 = pure noise, 1 = a straight line; Kaufman p.10-14) is computed at every closed bar from
the bars up to it, then averaged per year and per half (2020-22 / 2023-26, as
`tools/trend_grid`). Written to `<out>/noise.csv` (symbol x timeframe x n x year / half /
all: bars, mean, median) and, with a `trend_grid` `split.csv`, `<out>/vs_strategy4.csv`: per
symbol x timeframe x half the mean ER next to strategy 4's average GROSS R per trade over
that timeframe's variants (gross: costs and swap do not belong to the signal's noise), plus
the rank correlation of the levels and of the changes between the halves.

Spec: ROADMAP.md › 11.1; knowledge/ideas.md I-01.
"""

from __future__ import annotations

import argparse
import csv
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from backtester.analytics.noise import (
    efficiency_ratio,
    median,
    random_walk_er,
    rank_correlation,
    values_by,
)
from backtester.analytics.robustness import RobustnessConfig
from backtester.core.models import Timeframe
from backtester.data.sources import DEFAULT_SOURCES
from backtester.paths import RESULTS_DIR
from backtester.strategy.trend_following.config import TIMEFRAMES
from backtester.tools.research_helpers import HALVES, SYMBOLS, write_csv

NS = (10, 20, 60)  # ER windows in bars
DEFAULT_JOIN_N = 20  # Kaufman's 20-bar noise
MIN_TRADES = 30  # a symbol x timeframe x half cell needs this many strategy 4 trades
FIRST_HALF_END_YEAR = RobustnessConfig().first_half_end_year
LEVEL = "level: mean ER vs avg gross R per trade"
CHANGE = "change: ER 2023-26 minus 2020-22 vs change in avg gross R"


def half_of(year: int) -> str:
    return HALVES[0] if year <= FIRST_HALF_END_YEAR else HALVES[1]


def noise_rows(
    symbol: str,
    timeframe: str,
    times: Sequence[datetime],
    closes: Sequence[float],
    ns: Sequence[int] = NS,
) -> list[dict]:
    """Rows kind = year / half / all for each n: bars with a ratio, mean and median ER."""
    rows = []
    for n in ns:
        er = efficiency_ratio(closes, n)
        groupings = (
            ("year", [f"{t.year}" for t in times]),
            ("half", [half_of(t.year) for t in times]),
            ("all", ["all"] * len(times)),
        )
        for kind, keys in groupings:
            for period, values in sorted(values_by(keys, er).items()):
                rows.append(
                    {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "n": n,
                        "kind": kind,
                        "period": period,
                        "bars": len(values),
                        "mean_er": sum(values) / len(values),
                        "median_er": median(values),
                    }
                )
    return rows


def compare_with_strategy4(
    noise: Sequence[dict],
    split: Sequence[dict],
    n: int = DEFAULT_JOIN_N,
    min_trades: int = MIN_TRADES,
) -> tuple[list[dict], list[dict]]:
    """(cells, stats). A cell is (symbol, timeframe, half) with the mean ER (window `n`) and
    strategy 4's gross R per trade over all variants of that timeframe in `split` (the
    `trend_grid` split.csv rows; the ALL group is left out). Cells with fewer than
    `min_trades` trades or without a noise value are skipped. `stats`: Spearman's rho, n and
    t of the levels over all cells and of the change between the halves over the symbol x
    timeframe pairs that have both (a measure without enough pairs is not listed)."""
    er = {
        (r["symbol"], r["timeframe"], r["period"]): float(r["mean_er"])
        for r in noise
        if r["kind"] == "half" and int(r["n"]) == n
    }
    sums: dict[tuple[str, str, str], list[float]] = {}
    for r in split:
        if r["symbol"] == "ALL":
            continue
        key = (r["symbol"], r["variant"].split()[0], r["half"])
        acc = sums.setdefault(key, [0.0, 0.0])
        acc[0] += int(float(r["trades"]))
        acc[1] += float(r["sum_r_gross"])
    cells = []
    for (symbol, tf, half), (trades, gross) in sums.items():
        if trades < min_trades or (symbol, tf, half) not in er:
            continue
        cells.append(
            {
                "symbol": symbol,
                "timeframe": tf,
                "half": half,
                "n": n,
                "trades": int(trades),
                "mean_er": er[symbol, tf, half],
                "avg_gross_r": gross / trades,
            }
        )
    stats = []
    level = rank_correlation([c["mean_er"] for c in cells], [c["avg_gross_r"] for c in cells])
    if level:
        stats.append({"measure": LEVEL, **level})
    by_pair: dict[tuple[str, str], dict[str, dict]] = {}
    for c in cells:
        by_pair.setdefault((c["symbol"], c["timeframe"]), {})[c["half"]] = c
    pairs = [h for h in by_pair.values() if HALVES[0] in h and HALVES[1] in h]
    change = rank_correlation(
        [h[HALVES[1]]["mean_er"] - h[HALVES[0]]["mean_er"] for h in pairs],
        [h[HALVES[1]]["avg_gross_r"] - h[HALVES[0]]["avg_gross_r"] for h in pairs],
    )
    if change:
        stats.append({"measure": CHANGE, **change})
    return cells, stats


def load_closes(
    symbol: str, timeframe: Timeframe, start: date, end: date
) -> tuple[list[datetime], list[float]]:
    """(bar open times, closes) of the cached days between `start` and `end`."""
    cached = sorted(d for d in DEFAULT_SOURCES.cached_days(symbol) if start <= d <= end)
    if not cached:
        raise ValueError(f"{symbol}: no cached days between {start} and {end}")
    first = datetime(cached[0].year, cached[0].month, cached[0].day, tzinfo=UTC)
    last = cached[-1] + timedelta(days=1)
    frame = DEFAULT_SOURCES.adapter(symbol).fetch_frame(
        symbol, timeframe, first, datetime(last.year, last.month, last.day, tzinfo=UTC)
    )
    return list(frame["ts"].dt.to_pydatetime()), [float(c) for c in frame["close"]]


def read_split(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _print_table(rows: list[dict], n: int, symbols: Sequence[str], timeframes: Sequence[str]):
    half = {(r["symbol"], r["timeframe"], r["period"]): r["mean_er"] for r in rows
            if r["kind"] == "half" and r["n"] == n}  # fmt: skip
    print(f"\nmean ER({n}) first half -> second half (low = noisy; {HALVES[0]} -> {HALVES[1]})")
    print(f"{'':8}" + "".join(f"{tf:>14}" for tf in timeframes))
    for s in symbols:
        cells = []
        for tf in timeframes:
            a, b = half.get((s, tf, HALVES[0])), half.get((s, tf, HALVES[1]))
            cells.append("-" if a is None or b is None else f"{a:.3f}->{b:.3f}")
        print(f"{s:8}" + "".join(f"{c:>14}" for c in cells))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, default=date(2020, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date(2026, 9, 30))
    p.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    p.add_argument("--timeframes", nargs="+", choices=[t.name for t in TIMEFRAMES],
                   default=[t.name for t in TIMEFRAMES])  # fmt: skip
    p.add_argument("--ns", nargs="+", type=int, default=list(NS), help="ER windows in bars")
    p.add_argument("--join-n", type=int, default=DEFAULT_JOIN_N,
                   help="ER window used in the comparison with strategy 4")  # fmt: skip
    p.add_argument("--split-csv", type=Path, default=RESULTS_DIR / "trend_grid" / "split.csv",
                   help="trend_grid split.csv (variant, symbol, half, trades, sum_r_gross)")  # fmt: skip
    p.add_argument("--min-trades", type=int, default=MIN_TRADES)
    p.add_argument("--no-compare", action="store_true", help="only the noise, no strategy 4")
    p.add_argument("--out", type=Path, default=RESULTS_DIR / "noise_study")
    args = p.parse_args(argv)

    symbols = [s.upper() for s in args.symbols]
    ns = sorted({*args.ns, args.join_n})
    args.out.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for symbol in symbols:
        for tf_name in args.timeframes:
            try:
                times, closes = load_closes(symbol, Timeframe[tf_name], args.start, args.end)
            except Exception as e:  # noqa: BLE001 - research tool: say what is missing, go on
                print(f"{symbol} {tf_name}: skipped ({type(e).__name__}: {e})", flush=True)
                continue
            rows += noise_rows(symbol, tf_name, times, closes, ns)
            print(f"{symbol} {tf_name}: {len(closes)} bars", flush=True)
    reference = {n: random_walk_er(n) for n in ns}
    rows += [
        {"symbol": "RANDOM WALK", "timeframe": "-", "n": n, "kind": "all", "period": "all",
         "bars": 100_000, "mean_er": er, "median_er": None}
        for n, er in reference.items()
    ]  # fmt: skip
    write_csv(args.out / "noise.csv", rows)
    _print_table(rows, args.join_n, symbols, args.timeframes)
    print("random walk reference ER: " + ", ".join(f"n={n}: {v:.3f}" for n, v in reference.items()))

    if not args.no_compare and args.split_csv.is_file():
        cells, stats = compare_with_strategy4(
            rows, read_split(args.split_csv), args.join_n, args.min_trades
        )
        write_csv(args.out / "vs_strategy4.csv", cells)
        write_csv(args.out / "vs_strategy4_stats.csv", stats)
        print(
            f"\nstrategy 4 ({args.split_csv.name}), {len(cells)} symbol x timeframe x half cells:"
        )
        for s in stats:
            print(f"  {s['measure']}: rho {s['rho']:+.2f}, n {s['n']}, t {s['t']:+.1f}")
        if not stats:
            print("  not enough cells for a correlation")
        print("  (cells share trades and are few: |t| >= 2 is a hint, not a proof)")
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
