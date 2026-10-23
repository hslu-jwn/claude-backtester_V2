"""Measure V2.4d item 3 on all seven 2023 golden setups, without changing defaults.

    .venv/Scripts/python.exe scripts/measure_tp_penetration.py

Runs sequentially (one worker), using spec-default strategies, symbols, sources and
dates from tools/golden.py. CSV and Markdown are checkpointed after every completed
variant; the log identifies progress if a run fails. TP exits count trades whose final
exit is TP; tp_fills also counts partial TP exits. This is a sensitivity measurement,
not a parameter selection or a new trial on the held-out research period.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from pathlib import Path
from time import perf_counter

from backtester.analytics.metrics import BREAK_EVEN_TOL
from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.trade import ExitReason
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.registry import default_config
from backtester.tools.golden import GoldenConfig

VARIANTS = ((0.0, False), (0.5, False), (1.0, False), (2.0, False), (0.0, True))
METRICS = ("trades", "wins", "net_r", "avg_r", "tp_exits", "touched_not_filled_share")
COLUMNS = (
    "strategy",
    "tp_penetration",
    "short_tp_on_ask",
    *METRICS,
    "tp_fills",
    "tp_levels_touched",
    "tp_levels_touched_not_filled",
    *(f"delta_{key}" for key in METRICS),
)


def measurement(trades) -> dict:
    count = len(trades)
    net = sum(t.r_net for t in trades)
    touched = sum(t.tp_levels_touched for t in trades)
    missed = sum(t.tp_levels_touched_not_filled for t in trades)
    return {
        "trades": count,
        "wins": sum(t.r_net > BREAK_EVEN_TOL for t in trades),
        "net_r": net,
        "avg_r": net / count if count else 0.0,
        "tp_exits": sum(t.exit_reason is ExitReason.TAKE_PROFIT for t in trades),
        "tp_fills": sum(p.reason is ExitReason.TAKE_PROFIT for t in trades for p in t.parts),
        "tp_levels_touched": touched,
        "tp_levels_touched_not_filled": missed,
        "touched_not_filled_share": missed / touched if touched else 0.0,
    }


def write_reports(output: Path, rows: list[dict], config: GoldenConfig, notes: list[str]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_suffix(".csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    expected = len(config.strategies) * len(VARIANTS)
    lines = [
        "# TP penetration measurement (V2.4d item 3)",
        "",
        f"Golden setups: {config.start} through {config.end}, spec defaults, one worker.",
        f"Completed: {len(rows)}/{expected} variants. Defaults remain 0 / False.",
        "",
        "TP exits = trades ending at TP; TP fills in CSV include partial exits. Miss share =",
        "unique levels touched but failing the price threshold / unique levels touched.",
        "Each level counts once, including if it fills later. SL-first precedence and",
        "MAE/MFE are unchanged. Deltas compare each row with that strategy's 0 / False run.",
        "This measures the settings; it does not select a default or log research trials.",
        "",
        (
            "| Strategy | Penetration | Ask | Trades (delta) | Wins (delta) | Net R (delta) | "
            "Avg R (delta) | TP exits (delta) | Miss share (delta pp) |"
        ),
        "|---|---:|:---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['strategy']} | {r['tp_penetration']:g} | "
            f"{'on' if r['short_tp_on_ask'] else 'off'} | "
            f"{r['trades']} ({r['delta_trades']:+d}) | {r['wins']} ({r['delta_wins']:+d}) | "
            f"{r['net_r']:.3f} ({r['delta_net_r']:+.3f}) | "
            f"{r['avg_r']:.4f} ({r['delta_avg_r']:+.4f}) | "
            f"{r['tp_exits']} ({r['delta_tp_exits']:+d}) | "
            f"{r['touched_not_filled_share']:.2%} "
            f"({100 * r['delta_touched_not_filled_share']:+.2f}) |"
        )
    if notes:
        lines.extend(["", "Data notes:", "", *(f"- {note}" for note in notes)])
    output.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None, *, config: GoldenConfig | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/tp_penetration"),
        help="output stem (.csv and .md)",
    )
    args = parser.parse_args(argv)
    config = config or GoldenConfig()
    rows, notes = [], []
    for name, symbols in config.strategies:
        baseline = None
        for penetration, ask in VARIANTS:
            started = perf_counter()
            print(f"{name}: penetration={penetration:g}, ask={ask}: running", flush=True)
            settings = RunSettings(strategy=default_config(name))
            settings = replace(
                settings,
                engine=replace(
                    settings.engine,
                    costs=replace(
                        settings.engine.costs, tp_penetration=penetration, short_tp_on_ask=ask
                    ),
                ),
            )
            result = run_backtests(
                symbols, config.start, config.end, settings, DEFAULT_SOURCES, workers=1
            )
            metrics = measurement(result.trades)
            if baseline is None:
                baseline = metrics
            row = {
                "strategy": name,
                "tp_penetration": penetration,
                "short_tp_on_ask": ask,
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
    print(f"Wrote {args.output.with_suffix('.csv')} and .md ({len(rows)} variants)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
