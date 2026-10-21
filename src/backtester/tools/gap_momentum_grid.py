"""Run strategy 7 (gap momentum) over its sweep and compare the results, plus the gap-bucket study.

    python -m backtester.tools.gap_momentum_grid --mode index        # 36 variants, fixed spread
    python -m backtester.tools.gap_momentum_grid --mode fx --spread-table /path/ftmo_spread_median.json
    python -m backtester.tools.gap_momentum_grid --no-sweep --start 2020-01-01 --end 2020-03-31

Variants = `entry_z` (0, 0.1, 0.25, 0.5) x `stop_atr` (0.5, 1, 2) x `exit_time` (index 11:00, 12:00,
15:59; fx 08:00, 11:00, 16:59) = 36 per mode; the spec default is one of them. `--no-sweep` runs
only the spec default. Symbols: index NAS100 and US500, fx GBPUSD, EURUSD and XAUUSD. The period
is the development period 2015-01-01 to 2021-09-13 (histdata); an end after 2021-09-13 (the data
split cut-off, the untouched test period) is refused unless `--allow-test-period`. Written to
`<out>/summary.csv` (variant x symbol group), `<out>/split.csv` and `<out>/robustness.csv` (halves at
the middle of the period), `<out>/grid.csv` (share of profitable variants, plateau variant over
`entry_z` per stop x exit family and over all variants, via `analytics/robustness.py`) and
`<out>/gap_buckets.csv` (the study: open-to-close move per gap bucket in sd units, beyond / inside
the prior range, up / down, momentum against fade on the same days; `--no-study` skips it). Default
`<out>` is results/gap_momentum/<mode>/fixed, or .../table with `--spread-table`. Every variant adds
one line to the trial log (family gap_momentum_index / gap_momentum_fx). Net R includes the swap.
`--cache-dir` reads every symbol from another cache folder (read only). Research only: it changes
no setting. Spec: strategy-gap-momentum.md > Backtest options (ROADMAP 11.12).
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

from backtester.analytics.gap_buckets import GapDay, bucket_rows, gap_days
from backtester.analytics.metrics import summarize
from backtester.analytics.robustness import RobustnessConfig, welch_t
from backtester.analytics.trial_log import append, make_record
from backtester.analytics.verdict import middle_date
from backtester.core.models import Timeframe
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.engine.spread_table import SpreadTable
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.gap_momentum.config import GapMomentumConfig
from backtester.tools.archive.trend_grid import (
    grid_rows,
    load_shocks,
    print_grid,
    robustness_row,
    sum_ex_swap,
    summary_net,
    summary_row,
    swap_rates_note,
    write_csv,
)

STRATEGY = "gap_momentum"  # registry name; trial-log families are gap_momentum_<mode>
SYMBOLS = {"index": ("NAS100", "US500"), "fx": ("GBPUSD", "EURUSD", "XAUUSD")}
START = date(2015, 1, 1)
DEV_END = date(2021, 9, 13)  # the day before the data split cut-off 2021-09-14
ENTRY_ZS = (0.0, 0.1, 0.25, 0.5)
STOP_ATRS = (0.5, 1.0, 2.0)
EXIT_TIMES = {
    "index": (time(11, 0), time(12, 0), time(15, 59)),
    "fx": (time(8, 0), time(11, 0), time(16, 59)),
}
HALF_LABELS = ("first", "second")
MINUTES_PER_HOUR = 60
WORKERS = 1


def variants(
    mode: str = "index",
    sweep: bool = True,
    entry_zs: Sequence[float] = ENTRY_ZS,
    stop_atrs: Sequence[float] = STOP_ATRS,
    exit_times: Sequence[time] | None = None,
) -> list[GapMomentumConfig]:
    """One config per entry_z x stop_atr x exit time (the spec default only without sweep)."""
    if not sweep:
        return [GapMomentumConfig(mode=mode)]
    return [
        GapMomentumConfig(mode=mode, entry_z=z, stop_atr=stop, exit_time=t)
        for stop in stop_atrs
        for t in (exit_times or EXIT_TIMES[mode])
        for z in entry_zs
    ]


def variant_name(config: GapMomentumConfig) -> str:
    return f"z {config.entry_z:g} stop {config.stop_atr:g} exit {config.exit_time_resolved:%H:%M}"


def family_key(config: GapMomentumConfig) -> tuple[str, float]:
    """(family, order): variants differing only in `entry_z`, ordered by it."""
    return (
        f"stop {config.stop_atr:g} exit {config.exit_time_resolved:%H:%M}",
        config.entry_z,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--mode", choices=tuple(SYMBOLS), default="index")
    p.add_argument("--start", type=date.fromisoformat, default=START)
    p.add_argument("--end", type=date.fromisoformat, default=DEV_END,
                   help=f"default {DEV_END} (development period)")  # fmt: skip
    p.add_argument("--allow-test-period", action="store_true",
                   help=f"allow an end after {DEV_END} (the untouched test period)")  # fmt: skip
    p.add_argument("--symbols", nargs="+", default=None, help="default: the symbols of the mode")
    p.add_argument("--no-sweep", action="store_true", help="only the spec's default parameters")
    p.add_argument("--entry-z", nargs="+", type=float, default=list(ENTRY_ZS))
    p.add_argument("--stop-atr", nargs="+", type=float, default=list(STOP_ATRS))
    p.add_argument("--exit-times", nargs="+", type=time.fromisoformat, default=None,
                   help="New York time HH:MM (default: the mode's three)")  # fmt: skip
    p.add_argument("--spread-table", type=Path, default=None,
                   help="spread by year and hour JSON; without the flag: fixed spread")  # fmt: skip
    p.add_argument("--cache-dir", type=Path, default=None,
                   help="read every symbol from this cache folder (default: the app's sources)")  # fmt: skip
    p.add_argument("--no-shocks", action="store_true",
                   help="do not read the daily bars for the shock days")  # fmt: skip
    p.add_argument("--no-study", action="store_true", help="skip the gap-bucket study")
    p.add_argument("--workers", type=int, default=WORKERS,
                   help="processes per backtest (one per symbol; 1 = in this process)")  # fmt: skip
    p.add_argument("--family", default=None,
                   help="trial-log family (default gap_momentum_<mode>)")  # fmt: skip
    p.add_argument("--out", type=Path, default=None)
    return p.parse_args(argv)


def symbols_for(args: argparse.Namespace) -> list[str]:
    return [s.upper() for s in (args.symbols or SYMBOLS[args.mode])]


def data_start(symbols: Sequence[str], sources: SymbolSources, start: date) -> date:
    """`start`, or the first cached day when the data begins later (halves are cut there)."""
    firsts = [min(days) for s in symbols if (days := sources.cached_days(s))]
    return max(start, min(firsts)) if firsts else start


# --- halves at the middle of the period -----------------------------------------------------------


def split_trades(trades: Sequence, middle: date) -> tuple[list, list]:
    """Trades entered up to / after the middle date (the middle date is in the first half)."""
    first = [t for t in trades if t.entry_time.date() <= middle]
    second = [t for t in trades if t.entry_time.date() > middle]
    return first, second


def half_rows(variant: str, group: str, trades: Sequence, middle: date) -> list[dict]:
    rows = []
    for half, part in zip(HALF_LABELS, split_trades(trades, middle), strict=True):
        s = summarize(part)
        rows.append(
            {
                "variant": variant, "symbol": group, "half": half, "trades": s["trades"],
                "sum_r_gross": s["net_r_gross"], "sum_r_net": s["net_r_net"],
                "sum_r_ex_swap": sum_ex_swap(part),
            }
        )  # fmt: skip
    return rows


def robustness_row_mid(variant, group, trades, shocks, rcfg, middle: date) -> dict:
    """The robustness row with the halves cut at `middle` instead of at a year."""
    row = robustness_row(variant, group, trades, shocks, rcfg)
    first, second = split_trades(trades, middle)
    welch = welch_t([t.r_net for t in first], [t.r_net for t in second], rcfg)
    row.update(
        half_first_trades=len(first), half_second_trades=len(second),
        half_first_net_r=sum(t.r_net for t in first),
        half_second_net_r=sum(t.r_net for t in second),
        welch_t=welch["t"] if welch else None, welch_df=welch["df"] if welch else None,
        welch_significant=bool(welch and welch["significant"]),
    )  # fmt: skip
    return row


# --- the gap-bucket study --------------------------------------------------------------------------


def load_session_bars(
    symbol: str, cache_dir: Path, start: date, end: date, config: GapMomentumConfig
) -> list[tuple[datetime, float, float, float]]:
    """(close time UTC, high, low, close) of the cached 1m candles closing within the session
    [open, close] of `config` in New York time, for the cached days of [start, end]."""
    sources = SymbolSources.single(cache_dir, [symbol])
    cached = sorted(d for d in sources.cached_days(symbol) if start <= d <= end)
    if not cached:
        raise ValueError(f"{symbol}: no cached days between {start} and {end}")
    first = datetime(cached[0].year, cached[0].month, cached[0].day, tzinfo=UTC)
    last = cached[-1] + timedelta(days=1)
    frame = sources.adapter(symbol).fetch_frame(
        symbol, Timeframe.M1, first, datetime(last.year, last.month, last.day, tzinfo=UTC)
    )
    close_time = frame["ts"] + Timeframe.M1.duration
    local = close_time.dt.tz_convert(config.zone)
    minute = local.dt.hour * MINUTES_PER_HOUR + local.dt.minute
    lo = config.session_open.hour * MINUTES_PER_HOUR + config.session_open.minute
    hi = config.session_close.hour * MINUTES_PER_HOUR + config.session_close.minute
    keep = (minute >= lo) & (minute <= hi)
    return [
        (ts.to_pydatetime(), float(h), float(low), float(c))
        for ts, h, low, c in zip(
            close_time[keep], frame["high"][keep], frame["low"][keep], frame["close"][keep],
            strict=True,
        )
    ]  # fmt: skip


def study_rows(
    symbols: Sequence[str], sources: SymbolSources, start: date, end: date, mode: str,
    middle: date,
) -> list[dict]:  # fmt: skip
    """Gap-bucket rows per symbol and pooled over the symbols (`ALL`), for days from `start`."""
    config = GapMomentumConfig(mode=mode)
    warm = timedelta(days=int(config.vol_days * 1.5) + 14)  # history for the sd and the ATR
    rows: list[dict] = []
    pooled: list[GapDay] = []
    for symbol in symbols:
        bars = load_session_bars(symbol, sources.cache_dir(symbol), start - warm, end, config)
        days = [g for g in gap_days(bars, config) if g.day >= start]
        pooled += days
        rows += bucket_rows(days, symbol, middle)
    if len(symbols) > 1:
        rows += bucket_rows(pooled, "ALL", middle)
    return rows


# --- main ---------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.end > DEV_END and not args.allow_test_period:
        raise SystemExit(
            f"end {args.end} is after {DEV_END}: that is the untouched test period "
            "(use --allow-test-period for the one test run with the variants fixed in advance)"
        )
    configs = variants(args.mode, not args.no_sweep, args.entry_z, args.stop_atr, args.exit_times)
    symbols = symbols_for(args)
    sources = (
        DEFAULT_SOURCES if args.cache_dir is None else SymbolSources.single(args.cache_dir, symbols)
    )
    first_day = data_start(symbols, sources, args.start)
    middle = middle_date(first_day, args.end)
    engine = RunSettings().engine
    if args.spread_table is not None:
        table = SpreadTable.from_dict(json.loads(args.spread_table.read_text(encoding="utf-8")))
        engine = replace(engine, costs=replace(engine.costs, spread_table=table))
        print(f"spread table: {table.stat} by year and New York hour, {table.note}")
    cost_mode = "fixed" if args.spread_table is None else "table"
    out = args.out or RESULTS_DIR / "gap_momentum" / args.mode / cost_mode
    out.mkdir(parents=True, exist_ok=True)
    print(f"{args.mode} {symbols} {first_day}..{args.end}, halves split at {middle}", flush=True)
    rcfg = RobustnessConfig()
    shocks, shock_note = (
        ({}, "") if args.no_shocks else load_shocks(symbols, args.start, args.end, rcfg, sources)
    )
    family = args.family or f"{STRATEGY}_{args.mode}"
    summary, split, robust, entries = [], [], [], []
    for config in configs:
        name = variant_name(config)
        result = run_backtests(
            symbols,
            args.start,
            args.end,
            replace(RunSettings(), strategy=config, engine=engine),
            sources=sources,
            workers=args.workers,
        )
        print(f"{name}: {len(result.trades)} trades", flush=True)
        append(make_record(
            family, STRATEGY, config, symbols, args.start, args.end, "histdata",
            result.trades,
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
                    "gross_r_per_trade": row["avg_r_gross"],
                    "swap_r": sum(t.swap_r for t in trades),
                }
            )
            split += half_rows(name, group, trades, middle)
            robust.append(robustness_row_mid(name, group, trades, shocks, rcfg, middle))
        fam, order = family_key(config)
        entries.append((fam, order, name, summary_net(summary, name)))
        write_csv(out / "summary.csv", summary)
        write_csv(out / "split.csv", split)
        write_csv(out / "robustness.csv", robust)
    grid = grid_rows(entries, rcfg)
    write_csv(out / "grid.csv", grid)
    print(f"\n{'variant':30}{'trades':>7}{'gross':>9}{'net':>9}{'net/tr':>8}")
    for r in summary:
        if r["symbol"] == "ALL":
            per = "-" if r["net_r_per_trade"] is None else f"{r['net_r_per_trade']:+.3f}"
            print(
                f"{r['variant']:30}{r['trades']:>7}{r['sum_r_gross']:>+9.1f}"
                f"{r['sum_r_net']:>+9.1f}{per:>8}"
            )
    print_grid(grid)
    if not args.no_study:
        write_csv(out / "gap_buckets.csv",
                  study_rows(symbols, sources, first_day, args.end, args.mode, middle))  # fmt: skip
    print(f"halves: first (to {middle}) / second in split.csv")
    print(swap_rates_note(engine.costs, symbols))
    if shock_note:
        print(shock_note)
    print(f"written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
