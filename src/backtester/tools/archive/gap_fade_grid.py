"""Run strategy 5 (gap fade) over its sweep and compare the results.

    python -m backtester.tools.archive.gap_fade_grid                 # 36 variants, fixed spread
    python -m backtester.tools.archive.gap_fade_grid --spread-table  # with data/spreads/ftmo_spread_median.json
    python -m backtester.tools.archive.gap_fade_grid --source mt5 --start 2021-09-15  # FTMO's candles
    python -m backtester.tools.archive.gap_fade_grid --no-sweep --start 2026-08-01 --end 2026-08-31

Variants = gap bucket (min_gap_atr-max_gap_atr: 0.1-0.25, 0.25-0.5, 0.5-1, 0.1-1) x
`stop_gap_mult` (0.75, 1, 1.5) x `exit_time` (11:00, 12:00, 16:00) = 36; the spec default is
one of them. `--no-sweep` runs only the spec defaults. Everything else is the spec default.
Default symbols NAS100 and US500, from 2020-01-01 to the last cached day. Written to
`<out>/summary.csv` (variant x symbol group), `<out>/split.csv` (2020-22 against 2023-26),
`<out>/robustness.csv` (net without the best trade, costs x 1.5, halves, shock days) and
`<out>/grid.csv` (share of profitable variants, plateau variant per bucket x stop family,
ordered by exit time, and over all variants) via `analytics/robustness.py`. Default `<out>` is
results/gap_fade/fixed, or results/gap_fade/table with `--spread-table` (`gap_fade_mt5/` with
`--source mt5`). Net R includes the swap.
Research only: it changes no setting. Spec: strategy-gap-fade.md > Backtest options
(ROADMAP 11.4).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from datetime import date, time
from pathlib import Path

from backtester.analytics.robustness import RobustnessConfig
from backtester.analytics.trial_log import append, make_record
from backtester.data.cache import MT5_CACHE_DIR
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.engine.spread_table import SpreadTable
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.gap_fade.config import GapFadeConfig
from backtester.tools.archive.trend_grid import (
    HALVES,
    grid_rows,
    half_rows,
    load_shocks,
    print_grid,
    robustness_row,
    summary_net,
    summary_row,
    swap_rates_note,
    write_csv,
)

SYMBOLS = ("NAS100", "US500")
STRATEGY = "gap_fade"  # registry name; the default trial-log family
START = date(2020, 1, 1)
BUCKETS = ((0.1, 0.25), (0.25, 0.5), (0.5, 1.0), (0.1, 1.0))
STOP_MULTS = (0.75, 1.0, 1.5)
EXIT_TIMES = (time(11, 0), time(12, 0), time(16, 0))
DEFAULT_SPREAD_TABLE = Path("data") / "spreads" / "ftmo_spread_median.json"
MINUTES_PER_HOUR = 60
WORKERS = 1  # the process pool stalled on the long 1-minute runs; in-process is reliable


def variants(
    sweep: bool = True,
    buckets=BUCKETS,
    stop_mults=STOP_MULTS,
    exit_times=EXIT_TIMES,
) -> list[GapFadeConfig]:
    """One config per bucket x stop multiple x exit time (the spec default only without sweep)."""
    if not sweep:
        return [GapFadeConfig()]
    return [
        GapFadeConfig(min_gap_atr=lo, max_gap_atr=hi, stop_gap_mult=stop, exit_time=t)
        for lo, hi in buckets
        for stop in stop_mults
        for t in exit_times
    ]


def _family(config: GapFadeConfig) -> str:
    return f"gap {config.min_gap_atr:g}-{config.max_gap_atr:g} stop {config.stop_gap_mult:g}"


def variant_name(config: GapFadeConfig) -> str:
    return f"{_family(config)} exit {config.exit_time:%H:%M}"


def family_key(config: GapFadeConfig) -> tuple[str, float]:
    """(family, order): variants differing only in the exit time, ordered by it."""
    t = config.exit_time
    return _family(config), t.hour * MINUTES_PER_HOUR + t.minute


def _bucket(text: str) -> tuple[float, float]:
    lo, hi = text.split("-")
    return float(lo), float(hi)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, default=START)
    p.add_argument("--end", type=date.fromisoformat, default=None,
                   help="default: the last cached day")  # fmt: skip
    p.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    p.add_argument("--no-sweep", action="store_true", help="only the spec's default parameters")
    p.add_argument("--buckets", nargs="+", type=_bucket, default=list(BUCKETS),
                   help="gap buckets in ATR, e.g. 0.1-0.25")  # fmt: skip
    p.add_argument("--stop-mults", nargs="+", type=float, default=list(STOP_MULTS))
    p.add_argument("--exit-times", nargs="+", type=time.fromisoformat, default=list(EXIT_TIMES),
                   help="New York time HH:MM")  # fmt: skip
    p.add_argument("--spread-table", nargs="?", type=Path, const=DEFAULT_SPREAD_TABLE, default=None,
                   help=f"spread by year and hour JSON (default file {DEFAULT_SPREAD_TABLE}); "
                   "without the flag: fixed spread")  # fmt: skip
    p.add_argument("--no-shocks", action="store_true",
                   help="do not read the daily bars for the shock days")  # fmt: skip
    p.add_argument("--source", choices=("histdata", "mt5"), default="histdata",
                   help="candle cache: histdata (default) or FTMO's data/cache/mt5 "
                   "(python -m backtester.tools.mt5_download)")  # fmt: skip
    p.add_argument("--workers", type=int, default=WORKERS,
                   help="processes per backtest (1 = in this process)")  # fmt: skip
    p.add_argument("--family", default=None,
                   help="trial-log family (default gap_fade)")  # fmt: skip
    p.add_argument("--out", type=Path, default=None)
    return p.parse_args(argv)


def last_cached_day(symbols: list[str], sources: SymbolSources = DEFAULT_SOURCES) -> date:
    return max(max(sources.cached_days(s)) for s in symbols)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configs = variants(not args.no_sweep, args.buckets, args.stop_mults, args.exit_times)
    symbols = [s.upper() for s in args.symbols]
    sources = (
        DEFAULT_SOURCES
        if args.source == "histdata"
        else SymbolSources.single(MT5_CACHE_DIR, symbols)
    )
    end = args.end or last_cached_day(symbols, sources)
    engine = RunSettings().engine
    if args.spread_table is not None:
        table = SpreadTable.from_dict(json.loads(args.spread_table.read_text(encoding="utf-8")))
        engine = replace(engine, costs=replace(engine.costs, spread_table=table))
        print(f"spread table: {table.stat} by year and New York hour, {table.note}")
    mode = "fixed" if args.spread_table is None else "table"
    folder = "gap_fade" if args.source == "histdata" else f"gap_fade_{args.source}"
    out = args.out or RESULTS_DIR / folder / mode
    out.mkdir(parents=True, exist_ok=True)
    rcfg = RobustnessConfig()
    shocks, shock_note = (
        ({}, "") if args.no_shocks else load_shocks(symbols, args.start, end, rcfg, sources)
    )
    summary, split, robust, entries = [], [], [], []
    for config in configs:
        name = variant_name(config)
        result = run_backtests(
            symbols,
            args.start,
            end,
            replace(RunSettings(), strategy=config, engine=engine),
            sources=sources,
            workers=args.workers,
        )
        print(f"{name}: {len(result.trades)} trades", flush=True)
        append(make_record(
            args.family or STRATEGY, STRATEGY, config, symbols, args.start, end, args.source,
            [t.r_net for t in result.trades],
        ))  # fmt: skip
        sets = {"ALL": result.trades, **{s: r.trades for s, r in result.runs.items()}}
        for group, trades in sets.items():
            row = summary_row(name, group, trades)
            summary.append(
                {
                    "variant": name,
                    "symbol": group,
                    "trades": row["trades"],
                    "win_rate": row["win_rate"],
                    "sum_r_gross": row["sum_r_gross"],
                    "sum_r_net": row["sum_r_net"],
                    "net_r_per_trade": row["avg_r_net"],
                    "swap_r": sum(t.swap_r for t in trades),
                }
            )
            split += half_rows(name, group, trades)
            robust.append(robustness_row(name, group, trades, shocks, rcfg))
        family, order = family_key(config)
        entries.append((family, order, name, summary_net(summary, name)))
        write_csv(out / "summary.csv", summary)
        write_csv(out / "split.csv", split)
        write_csv(out / "robustness.csv", robust)
    grid = grid_rows(entries, rcfg)
    write_csv(out / "grid.csv", grid)
    print(f"\n{'variant':40}{'trades':>7}{'gross':>9}{'net':>9}{'net/tr':>8}")
    for r in summary:
        if r["symbol"] == "ALL":
            per = "-" if r["net_r_per_trade"] is None else f"{r['net_r_per_trade']:+.3f}"
            print(
                f"{r['variant']:40}{r['trades']:>7}{r['sum_r_gross']:>+9.1f}"
                f"{r['sum_r_net']:>+9.1f}{per:>8}"
            )
    print_grid(grid)
    print(f"halves: {HALVES[0]} / {HALVES[1]} in split.csv")
    print(swap_rates_note(engine.costs, symbols))
    if shock_note:
        print(shock_note)
    print(f"written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
