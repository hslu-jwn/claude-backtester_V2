"""V2.4d(4): golden-setup permutation vs bootstrap, and Masters bounds.

Run from the repository root, redirecting stdout/stderr to results/measure_bootstrap.log:
    python scripts/measure_bootstrap.py
No strategy/risk defaults or golden references are changed. Backtests run sequentially.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, replace
from pathlib import Path
from time import perf_counter

from backtester.analytics.daily import daily_net_r, daily_net_r_mtm, weekdays
from backtester.data.sources import DEFAULT_SOURCES
from backtester.risk.drawdown_bounds import DrawdownBoundsConfig
from backtester.risk.monte_carlo import MonteCarloConfig, run_monte_carlo
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.registry import default_config
from backtester.tools import drawdown_report
from backtester.tools.golden import GoldenConfig
from backtester.tools.monte_carlo import jsonable

STRATEGIES = ("trend_following", "opening_range", "gap_momentum")


def metrics(strategy, outputs) -> list[dict]:
    rows = []
    for sampling, result in outputs.items():
        for risk, output in result["risks"].items():
            st, ftmo = output["stats"], output["ftmo"]
            finished = ftmo["attempts"]
            rows.append(
                {
                    "strategy": strategy,
                    "sampling": sampling,
                    "risk": risk,
                    "dd_median_pct": st["max_dd_pct"]["median"],
                    "dd_p95_pct": st["max_dd_pct"]["p95"],
                    "p_dd_over_alert": st["p_dd_over_alert"],
                    "pass_probability": ftmo["pass_probability"],
                    "breach_probability": (ftmo["fail_daily"] + ftmo["fail_max"]) / finished
                    if finished
                    else None,
                    "unfinished_share": ftmo["unfinished_share"],
                }
            )
    return rows


def comparison_table(rows) -> list[str]:
    lines = [
        (
            "| Strategy | Sampling | Risk | Median DD % | P95 DD % | P(DD > alert) | "
            "FTMO pass | FTMO breach | Unfinished |"
        ),
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        probabilities = [
            "n/a" if r[k] is None else f"{r[k]:.1%}"
            for k in (
                "p_dd_over_alert",
                "pass_probability",
                "breach_probability",
                "unfinished_share",
            )
        ]
        lines.append(
            f"| {r['strategy']} | {r['sampling']} | {r['risk'] * 100:g}% | "
            f"{r['dd_median_pct']:.3f} | {r['dd_p95_pct']:.3f} | "
            + " | ".join(probabilities)
            + " |"
        )
    return lines


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--block-days", type=float, default=5)
    parser.add_argument("--outer", type=int, default=200)
    parser.add_argument("--inner", type=int, default=1000)
    parser.add_argument("--horizon-days", type=int, default=126)
    parser.add_argument("--out", type=Path, default=Path("results/bootstrap_compare.md"))
    args = parser.parse_args(argv)
    golden = GoldenConfig()
    config = MonteCarloConfig(runs=args.runs, seed=args.seed, block_days=args.block_days)
    bounds_cfg = DrawdownBoundsConfig(
        outer=args.outer,
        inner=args.inner,
        horizon_days=args.horizon_days,
        seed=args.seed,
        block_days=args.block_days,
        risk_levels=config.risk_levels,
    )
    output_folder = args.out.with_suffix("")
    output_folder.mkdir(parents=True, exist_ok=True)
    rows, bounds_by_strategy = [], {}
    for strategy in STRATEGIES:
        symbols = dict(golden.strategies)[strategy]
        print(f"{strategy}: {symbols}, {golden.start}..{golden.end}, golden defaults", flush=True)
        result = run_backtests(
            symbols,
            golden.start,
            golden.end,
            RunSettings(strategy=default_config(strategy)),
            DEFAULT_SOURCES,
            workers=1,
        )
        print(
            f"  {len(result.trades)} trades, net {sum(t.r_net for t in result.trades):+.3f} R",
            flush=True,
        )
        for note in (*result.notes, *(n for run in result.runs.values() for n in run.notes)):
            print(f"  note: {note}", flush=True)
        outputs = {}
        for sampling in ("permutation", "block_bootstrap"):
            started = perf_counter()
            outputs[sampling] = run_monte_carlo(
                result.trades, golden.start, golden.end, replace(config, sampling=sampling)
            )
            print(f"  {sampling}: {perf_counter() - started:.3f}s", flush=True)
        rows.extend(metrics(strategy, outputs))
        target = output_folder / strategy
        target.mkdir(exist_ok=True)
        # Preserve the V2.4d MTM series for audit; strategy 4 holds positions overnight.
        booked = daily_net_r(result.trades, golden.start, golden.end)
        mtm, position = daily_net_r_mtm(result.trades, golden.start, golden.end, DEFAULT_SOURCES)
        with (target / "daily.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(("date", "net_r_exit_booked", "net_r_mtm", "position"))
            writer.writerows(
                zip(weekdays(golden.start, golden.end), booked, mtm, position, strict=True)
            )
        started = perf_counter()
        bounds = drawdown_report.calculate(
            result.trades, golden.start, golden.end, target, bounds_cfg
        )
        elapsed = perf_counter() - started
        print(
            f"  double bootstrap {args.outer} x {args.inner} x {args.horizon_days}: {elapsed:.3f}s",
            flush=True,
        )
        bounds_by_strategy[strategy] = {**bounds, "elapsed_seconds": elapsed}
        drawdown_report.write(bounds, target)
        (target / "monte_carlo.json").write_text(
            json.dumps(jsonable(outputs), indent=1, allow_nan=False), encoding="utf-8"
        )
    lines = [
        "# Bootstrap comparison (V2.4d item 4)",
        "",
        (
            f"Golden setup, {golden.start}..{golden.end}, seed={config.seed}, runs={config.runs}, "
            f"block_days={config.block_days:g}, DD alert={config.dd_alert:.0%}. "
            "Whole-day account replay compounds risk; bounds use additive daily MTM R."
        ),
        "",
        (
            "FTMO pass/breach probabilities condition on finished attempts (both phases). "
            "Unfinished share is shown separately, as in the existing report. "
            "This comparison changes no further defaults. Bootstrap need not increase every statistic."
        ),
        "",
        *comparison_table(rows),
    ]
    for strategy, bounds in bounds_by_strategy.items():
        lines += drawdown_report.markdown(bounds, strategy)
        lines += ["", f"Bounds runtime: {bounds['elapsed_seconds']:.3f}s."]
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    args.out.with_suffix(".json").write_text(
        json.dumps(
            {
                "config": asdict(config),
                "rows": rows,
                "bounds": bounds_by_strategy,
            },
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )
    print(f"Written {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
