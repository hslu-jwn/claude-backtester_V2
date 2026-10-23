"""Shared CSV and cached-piece helpers for research and standalone studies.

Spec: research-runner.md > Standalone gap-bucket study and sweep grids.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.runner import run_backtests
from backtester.tools.research import segments

SYMBOLS = ("XAUUSD", "GBPUSD", "GBPJPY", "NAS100", "US500")
HALVES = ("2020-22", "2023-26")


def write_csv(path: Path, rows: list[dict]) -> None:
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def last_cached_day(symbols: list[str], sources: SymbolSources = DEFAULT_SOURCES) -> date:
    return max(max(sources.cached_days(s)) for s in symbols)


def run_variant(symbols, start, end, settings, sources, workers) -> SimpleNamespace:
    """`run_backtests` over each cached segment of each symbol; trades merged per symbol."""
    groups: dict[tuple[date, date], list[str]] = {}
    for symbol in symbols:
        for seg in segments(symbol, start, end, sources):
            groups.setdefault(seg, []).append(symbol)
    per_symbol: dict[str, list] = {}
    for (a, b), names in sorted(groups.items()):
        result = run_backtests(names, a, b, settings, sources=sources, workers=workers)
        for name, run in result.runs.items():
            per_symbol.setdefault(name, []).extend(run.trades)
    runs = {s: SimpleNamespace(trades=tuple(per_symbol[s])) for s in symbols if s in per_symbol}
    trades = sorted((t for r in runs.values() for t in r.trades), key=lambda t: t.entry_time)
    return SimpleNamespace(trades=tuple(trades), runs=runs)
