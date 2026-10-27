"""Run a backtest of any strategy and print its summary. Spec: ROADMAP.md › 3.4.

    python -m backtester.run XAUUSD GBPUSD --start 2026-09-01 --end 2026-09-30

Settings: the spec defaults, or a saved preset with `--preset NAME` (results/presets/, any strategy;
ROADMAP 4.2); results go to `results/<run-id>/` (see runner.py for the files).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

from backtester.analytics.metrics import by_period, by_year
from backtester.analytics.trial_log import append, make_record
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.presets import DEFAULT, PRESETS_DIR, PresetError, is_default, load_preset
from backtester.runner import RESULTS_DIR, run_backtests, write_results
from backtester.strategy.base import UnsupportedSymbolError
from backtester.strategy.registry import REGISTRY, strategy_name


def format_periods(trades) -> str:
    """Per year (ROADMAP 6.3): trades, win rate, net R and max drawdown in R, all symbols
    and each."""
    periods = by_period(trades, by_year)
    if not periods:
        return ""
    groups = list(next(iter(periods.values())))
    header = "  ".join(f"{g:>31}" for g in groups)
    columns = "  ".join(f"{'trades':>7}{'win':>7}{'net R':>9}{'max DD':>8}" for _ in groups)
    lines = [f"year  {header}", f"      {columns}"]

    def cells(s):
        win = "-" if s["win_rate"] is None else f"{s['win_rate']:.0%}"
        return f"{s['trades']:>7}{win:>7}{s['net_r_net']:>+9.1f}{s['max_drawdown_r_net']:>8.1f}"

    for period, row in periods.items():
        lines.append(f"{period:<6}" + "  ".join(cells(row[g]) for g in groups))
    return "\n".join(lines)


def format_summary(summary: dict) -> str:
    """The summary as a table: one row per symbol, then the combined row."""
    header = ("", "trades", "win rate", "net R gross", "net R net", "avg R:R", "max DD R net")
    rows = [*summary["per_symbol"].items(), ("combined", summary["combined"])]

    def cell(value, fmt):
        return "-" if value is None else format(value, fmt)

    lines = [header] + [
        (
            name,
            str(s["trades"]),
            cell(s["win_rate"], ".1%"),
            cell(s["net_r_gross"], "+.2f"),
            cell(s["net_r_net"], "+.2f"),
            cell(s["avg_rr"], ".2f"),
            cell(s["max_drawdown_r_net"], ".2f"),
        )
        for name, s in rows
    ]
    widths = [max(len(line[i]) for line in lines) for i in range(len(header))]
    return "\n".join(
        "  ".join(
            v.ljust(w) if i == 0 else v.rjust(w) for i, (v, w) in enumerate(zip(line, widths))
        )
        for line in lines
    )


class _Bar:
    """Progress on one terminal line."""

    def __init__(self) -> None:
        self._last = -1

    def __call__(self, done: int, total: int) -> None:
        pct = 100 * done // total if total else 100
        if pct != self._last:
            self._last = pct
            print(f"\r{pct:3d}% ({done}/{total} base candles)", end="", file=sys.stderr, flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m backtester.run", description=__doc__)
    parser.add_argument("symbols", nargs="+", help="e.g. XAUUSD GBPUSD GBPJPY")
    parser.add_argument("--start", type=date.fromisoformat, required=True, help="first UTC day")
    parser.add_argument("--end", type=date.fromisoformat, required=True, help="last UTC day")
    parser.add_argument("--warmup-days", type=int, default=None, help="default: the preset's")
    parser.add_argument("--workers", type=int, default=None, help="parallel processes")
    parser.add_argument("--out", type=Path, default=RESULTS_DIR, help="results folder")
    parser.add_argument("--cache-dir", type=Path, default=None, help="read every symbol here")
    parser.add_argument("--preset", default=DEFAULT, help="settings preset (results/presets/)")
    parser.add_argument(
        "--strategy",
        choices=tuple(REGISTRY),
        default=None,
        help="the strategy to run (default: the preset's strategy, strategy 1 for Default); "
        "a preset of another strategy is refused",
    )
    parser.add_argument(
        "--family",
        default=None,
        help="trial-log family: the variants this run was picked from (default: the strategy)",
    )
    parser.add_argument("--presets-dir", type=Path, default=PRESETS_DIR, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    symbols = [s.upper() for s in args.symbols]
    sources = SymbolSources.single(args.cache_dir, symbols) if args.cache_dir else DEFAULT_SOURCES
    try:  # same rules as the app (settings_panel): a preset belongs to one strategy
        if args.strategy is None and not is_default(args.preset):
            args.strategy = strategy_name(load_preset(args.preset, args.presets_dir).strategy)
        args.strategy = args.strategy or "session_zone_sweep"
        preset = load_preset(args.preset, args.presets_dir, args.strategy)
    except PresetError as e:
        parser.error(str(e))
    warmup = args.warmup_days if args.warmup_days is not None else preset.warmup_days
    settings = replace(preset, warmup_days=warmup)
    try:
        result = run_backtests(
            symbols, args.start, args.end, settings, sources, _Bar(), args.workers
        )
    except UnsupportedSymbolError as e:  # no symbol has rules (others are left out with a note)
        parser.error(str(e))
    print(file=sys.stderr)
    name = args.preset if settings == preset else f"{args.preset} (modified)"
    folder = write_results(result, args.out, preset=name)
    for note in (*result.notes, *(n for run in result.runs.values() for n in run.notes)):
        print(f"note: {note}")
    print(format_summary(result.summary()))
    print()
    print(format_periods(result.trades))
    print(f"\nresults: {folder}")
    source = "histdata" if args.cache_dir is None else str(args.cache_dir)
    append(make_record(
        args.family or args.strategy, args.strategy, settings.strategy, symbols, args.start,
        args.end, source, result.trades,
    ))  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
