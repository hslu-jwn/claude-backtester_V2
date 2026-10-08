"""Run a strategy 1 backtest and print its summary. Spec: ROADMAP.md › 3.4.

    python -m backtester.run XAUUSD GBPUSD --start 2026-09-01 --end 2026-09-30

Default settings (every config dataclass at its spec default); results go to
`results/<run-id>/` (see runner.py for the files).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.runner import RESULTS_DIR, RunSettings, run_backtests, write_results


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
            print(f"\r{pct:3d}% ({done}/{total} 5m candles)", end="", file=sys.stderr, flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m backtester.run", description=__doc__)
    parser.add_argument("symbols", nargs="+", help="e.g. XAUUSD GBPUSD GBPJPY")
    parser.add_argument("--start", type=date.fromisoformat, required=True, help="first UTC day")
    parser.add_argument("--end", type=date.fromisoformat, required=True, help="last UTC day")
    parser.add_argument("--warmup-days", type=int, default=RunSettings().warmup_days)
    parser.add_argument("--workers", type=int, default=None, help="parallel processes")
    parser.add_argument("--out", type=Path, default=RESULTS_DIR, help="results folder")
    parser.add_argument("--cache-dir", type=Path, default=None, help="read every symbol here")
    args = parser.parse_args(argv)

    symbols = [s.upper() for s in args.symbols]
    sources = SymbolSources.single(args.cache_dir, symbols) if args.cache_dir else DEFAULT_SOURCES
    settings = replace(RunSettings(), warmup_days=args.warmup_days)
    result = run_backtests(symbols, args.start, args.end, settings, sources, _Bar(), args.workers)
    print(file=sys.stderr)
    folder = write_results(result, args.out)
    for run in result.runs.values():
        for note in run.notes:
            print(f"note: {note}")
    print(format_summary(result.summary()))
    print(f"\nresults: {folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
