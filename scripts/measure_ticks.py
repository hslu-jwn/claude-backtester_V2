"""Measure V2.4d item 9 on seven 2023 golden setups, without changing defaults.

    .venv/Scripts/python.exe scripts/measure_ticks.py > results/measure_ticks.log 2>&1

Sequential runs, one worker; checkpoint CSV/Markdown after each off/on variant.
Current strategy/cost/intrabar defaults; no research trial or default selection.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from pathlib import Path
from time import perf_counter

from backtester.analytics.metrics import BREAK_EVEN_TOL
from backtester.data.sources import DEFAULT_SOURCES
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.registry import default_config
from backtester.tools.golden import GoldenConfig

METRICS = ("trades", "wins", "net_r", "avg_r")
COLUMNS = (
    "strategy",
    "round_to_tick",
    *METRICS,
    "orders_moved",
    "levels_moved",
    "mean_move_ticks",
    "rejected",
    *(f"delta_{key}" for key in METRICS),
)


def measurement(result) -> dict:
    n = len(result.trades)
    net = sum(t.r_net for t in result.trades)
    ticks = result.summary()["combined"]["tick_rounding"]
    return {
        "trades": n,
        "wins": sum(t.r_net > BREAK_EVEN_TOL for t in result.trades),
        "net_r": net,
        "avg_r": net / n if n else 0.0,
        **{k: ticks[k] for k in ("orders_moved", "levels_moved", "mean_move_ticks", "rejected")},
    }


def write_reports(output: Path, rows: list[dict], config: GoldenConfig, notes: list[str]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_suffix(".csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Tick rounding measurement (V2.4d item 9)",
        "",
        f"Golden setups: {config.start} through {config.end}, current defaults, one worker.",
        f"Completed: {len(rows)}/{2 * len(config.strategies)} variants. Default remains False.",
        "",
        "Deltas compare each strategy with rounding off. Moved orders include rejected attempts;",
        "mean move = total absolute move in ticks / moved levels, including computed BE.",
        "Warm-up attempts excluded. FTMO ticks use cache digits (no trade_tick_size in the",
        "recorded trading.json); Binance ticks remain None. Sources: risk-management.md > Costs.",
        "Intrabar=m1, TP penetration=0.5, short TP on ask=True. No default change or trial log.",
        "",
        "| Strategy | Rounding | Trades | Wins | Net R | Avg R | Moved | Mean ticks | Rejected | Change R |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['strategy']} | {'on' if r['round_to_tick'] else 'off'} | "
            f"{r['trades']} | {r['wins']} | {r['net_r']:.3f} | {r['avg_r']:.4f} | "
            f"{r['orders_moved']} | {r['mean_move_ticks']:.4f} | {r['rejected']} | "
            f"{r['delta_net_r']:+.3f} |"
        )
    if notes:
        lines.extend(["", "Run notes:", "", *(f"- {n}" for n in notes)])
    output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None, *, config: GoldenConfig | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/ticks"))
    args = parser.parse_args(argv)
    config = config or GoldenConfig()
    rows, notes = [], []
    for name, symbols in config.strategies:
        baseline = None
        for enabled in (False, True):
            started = perf_counter()
            print(f"{name}: round_to_tick={enabled}: running", flush=True)
            settings = RunSettings(strategy=default_config(name))
            settings = replace(
                settings,
                engine=replace(
                    settings.engine, costs=replace(settings.engine.costs, round_to_tick=enabled)
                ),
            )
            result = run_backtests(
                symbols, config.start, config.end, settings, DEFAULT_SOURCES, workers=1
            )
            metrics = measurement(result)
            if baseline is None:
                baseline = metrics
            row = {
                "strategy": name,
                "round_to_tick": enabled,
                **metrics,
                **{f"delta_{key}": metrics[key] - baseline[key] for key in METRICS},
            }
            rows.append(row)
            for note in (*result.notes, *(n for run in result.runs.values() for n in run.notes)):
                entry = f"{name} rounding={enabled}: {note}"
                if entry not in notes:
                    notes.append(entry)
            write_reports(args.output, rows, config, notes)
            print(
                f"{name}: {metrics['trades']} trades, net={metrics['net_r']:.3f}R, "
                f"moved={metrics['orders_moved']}, rejected={metrics['rejected']}, "
                f"delta={row['delta_net_r']:+.3f}R ({perf_counter() - started:.1f}s)",
                flush=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
