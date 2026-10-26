"""Measure T-03 on seven 2023 golden setups; preserve current execution defaults.

    .venv/Scripts/python.exe scripts/measure_intrabar.py > results/measure_intrabar.log 2>&1

Sequential runs with one worker. Checkpoint CSV/Markdown after each variant.
This execution sensitivity measurement does not select a default or log research trials.
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
    "intrabar",
    *METRICS,
    "ambiguous",
    "tp_first",
    "sl_first",
    "tp_first_share",
    "fallbacks",
    *(f"delta_{key}" for key in METRICS),
)


def measurement(result) -> dict:
    n = len(result.trades)
    net = sum(t.r_net for t in result.trades)
    summary = result.summary()["combined"]
    resolved = summary["intrabar_tp_first"] + summary["intrabar_sl_first"]
    return {
        "trades": n,
        "wins": sum(t.r_net > BREAK_EVEN_TOL for t in result.trades),
        "net_r": net,
        "avg_r": net / n if n else 0.0,
        "ambiguous": summary["intrabar_ambiguous"],
        "tp_first": summary["intrabar_tp_first"],
        "sl_first": summary["intrabar_sl_first"],
        "tp_first_share": summary["intrabar_tp_first"] / resolved if resolved else 0.0,
        "fallbacks": summary["intrabar_fallbacks"],
    }


def write_reports(output: Path, rows: list[dict], config: GoldenConfig, notes: list[str]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_suffix(".csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Intrabar M1 measurement (V2.4c T-03)",
        "",
        f"Golden setups: {config.start} through {config.end}, current defaults, one worker.",
        f"Completed: {len(rows)}/{2 * len(config.strategies)} variants. Default remains sl_first.",
        "",
        "Ambiguous counts trade/candle assessments, excluding warm-up entries. TP-first share",
        "= TP-first / (TP-first + SL-first), excluding fallbacks and limit replays with no exit.",
        "BE counts as a stop; partial TP then stop counts as TP-first. Deltas compare each",
        "row with its strategy's sl_first run. Missing minutes cause conservative fallback.",
        "",
        "| Strategy | Mode | Trades (delta) | Wins (delta) | Net R (delta) | Avg R (delta) | Ambiguous | TP-first share | Fallbacks |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['strategy']} | {r['intrabar']} | {r['trades']} ({r['delta_trades']:+d}) | "
            f"{r['wins']} ({r['delta_wins']:+d}) | {r['net_r']:.3f} ({r['delta_net_r']:+.3f}) | "
            f"{r['avg_r']:.4f} ({r['delta_avg_r']:+.4f}) | {r['ambiguous']} | "
            f"{r['tp_first_share']:.2%} | {r['fallbacks']} |"
        )
    if notes:
        lines.extend(["", "Data notes:", "", *(f"- {note}" for note in notes)])
    output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None, *, config: GoldenConfig | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/intrabar"))
    args = parser.parse_args(argv)
    config = config or GoldenConfig()
    rows, notes = [], []
    for name, symbols in config.strategies:
        baseline = None
        for mode in ("sl_first", "m1"):
            started = perf_counter()
            print(f"{name}: intrabar={mode}: running", flush=True)
            settings = RunSettings(strategy=default_config(name))
            settings = replace(settings, engine=replace(settings.engine, intrabar=mode))
            result = run_backtests(
                symbols, config.start, config.end, settings, DEFAULT_SOURCES, workers=1
            )
            metrics = measurement(result)
            if baseline is None:
                baseline = metrics
            row = {
                "strategy": name,
                "intrabar": mode,
                **metrics,
                **{f"delta_{k}": metrics[k] - baseline[k] for k in METRICS},
            }
            rows.append(row)
            for note in (*result.notes, *(n for run in result.runs.values() for n in run.notes)):
                entry = f"{name}: {note}"
                if entry not in notes:
                    notes.append(entry)
            write_reports(args.output, rows, config, notes)
            print(
                f"{name}: {metrics['trades']} trades, net={metrics['net_r']:.3f}R, "
                f"delta={row['delta_net_r']:+.3f}R ({perf_counter() - started:.1f}s)",
                flush=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
