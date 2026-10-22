"""Run strategy 2 with different liquidity sweep rules and compare the results.

    python -m backtester.tools.archive.strategy2_sweep_grid --start 2023-01-01 --end 2026-09-30
    python -m backtester.tools.archive.strategy2_sweep_grid --only base "tol 0.5" --out results/grid_a

Every variant is a full strategy-2 backtest (NAS100 and US500, spec defaults except the
sweep rule) with the same data and costs. Written to `<out>/summary.csv` (variant x
symbol), `<out>/by_year.csv` and printed as a table. Variants run one after the other; the
two symbols of one variant run in parallel. Research only: it changes no setting.
Spec: strategy-ny-indices.md › Sweep; confluences.md › Liquidity sweep.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import date
from pathlib import Path

from backtester.analytics.metrics import by_period, by_year, summarize
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
from backtester.tools.grid_common import write_csv
from backtester.tools.strategy2_explore import VARIANTS

SYMBOLS = ("NAS100", "US500")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, default=date(2023, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date(2026, 9, 30))
    p.add_argument("--only", nargs="+", choices=list(VARIANTS), help="default: all variants")
    p.add_argument("--out", type=Path, default=RESULTS_DIR / "strategy2_sweep_grid")
    args = p.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    summary, years = [], []
    for name in args.only or VARIANTS:
        config = replace(NyIndexSweepConfig(), **VARIANTS[name])
        result = run_backtests(
            SYMBOLS, args.start, args.end, replace(RunSettings(), strategy=config)
        )
        print(f"{name}: {len(result.trades)} trades", flush=True)
        sets = {"ALL": result.trades, **{s: r.trades for s, r in result.runs.items()}}
        for group, trades in sets.items():
            s = summarize(trades)
            summary.append(
                {
                    "variant": name,
                    "symbol": group,
                    "trades": s["trades"],
                    "win_rate": s["win_rate"],
                    "net_r_gross": s["net_r_gross"],
                    "net_r_net": s["net_r_net"],
                    "avg_rr": s["avg_rr"],
                    "max_dd_r_net": s["max_drawdown_r_net"],
                }
            )
        for year, row in by_period(result.trades, by_year).items():
            for group, s in row.items():
                years.append(
                    {
                        "variant": name,
                        "year": year,
                        "symbol": group,
                        "trades": s["trades"],
                        "net_r_net": s["net_r_net"],
                    }
                )
        write_csv(args.out / "summary.csv", summary)
        write_csv(args.out / "by_year.csv", years)
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
