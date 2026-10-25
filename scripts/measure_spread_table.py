"""Measure the spread table (V2.4c, audit 2026-10-23) on the seven 2023 golden setups.

    .venv/Scripts/python.exe scripts/measure_spread_table.py > results/measure_spread_table.log 2>&1

Fixed spread (the default) against FTMO's measured median and 90th-percentile spread by year and
hour (`data/spreads/ftmo_spread_*.json`, built by `tools/spread_table.py`). Strategies 2, 5, 6, 7
trade at the index cash open, where the measured spread is wider than the fixed one. Current
defaults otherwise; no default change, no trial-log line. Writes results/spread_table.md / .csv.
"""

from __future__ import annotations

import csv
import json
from dataclasses import replace
from pathlib import Path
from time import perf_counter

from backtester.analytics.metrics import BREAK_EVEN_TOL
from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.spread_table import SpreadTable
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.registry import default_config
from backtester.tools.golden import GoldenConfig

TABLES = {
    "fixed": None,
    "median": Path("data/spreads/ftmo_spread_median.json"),
    "p90": Path("data/spreads/ftmo_spread_p90.json"),
}
OUTPUT = Path("results/spread_table")


def main() -> int:
    config = GoldenConfig()
    tables = {
        k: None if p is None else SpreadTable.from_dict(json.loads(p.read_text("utf-8")))
        for k, p in TABLES.items()
    }
    rows = []
    for name, symbols in config.strategies:
        base = None
        for label, table in tables.items():
            started = perf_counter()
            settings = RunSettings(strategy=default_config(name))
            costs = replace(settings.engine.costs, spread_table=table)
            settings = replace(settings, engine=replace(settings.engine, costs=costs))
            result = run_backtests(
                symbols, config.start, config.end, settings, DEFAULT_SOURCES, workers=1
            )
            n = len(result.trades)
            net = sum(t.r_net for t in result.trades)
            spread = sum(t.spread_r for t in result.trades)
            base = net if base is None else base
            rows.append(
                {
                    "strategy": name, "spread": label, "trades": n,
                    "wins": sum(t.r_net > BREAK_EVEN_TOL for t in result.trades),
                    "net_r": net, "avg_r": net / n if n else 0.0,
                    "spread_r_per_trade": spread / n if n else 0.0, "delta_net_r": net - base,
                }
            )  # fmt: skip
            print(f"{name} {label}: {n} trades, net {net:.2f} R ({perf_counter() - started:.0f}s)",
                  flush=True)  # fmt: skip
            write(rows)
    return 0


def write(rows: list[dict]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.with_suffix(".csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Spread table measurement (V2.4c)",
        "",
        "Golden setups 2023, current defaults; fixed spread (default) vs FTMO's measured spread by",
        "year and hour (median, 90th percentile). Change = net R against the fixed spread.",
        "",
        "| Strategy | Spread | Trades | Wins | Net R | Avg R | Spread R / trade | Change R |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
        *(
            f"| {r['strategy']} | {r['spread']} | {r['trades']} | {r['wins']} | {r['net_r']:.2f} "
            f"| {r['avg_r']:.4f} | {r['spread_r_per_trade']:.4f} | {r['delta_net_r']:+.2f} |"
            for r in rows
        ),
    ]
    OUTPUT.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
