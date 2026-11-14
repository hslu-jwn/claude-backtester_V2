"""Challenge pass map (Fable directions row 1, 2026-11-14): FTMO 2-Step pass chance by net edge,
risk per trade and trades per day, on synthetic iid R streams, played by the house simulator
(`risk.monte_carlo.ftmo_by_risk`: static 10 % max loss, 5 % daily loss on the worst point, 4 days).

Each trade is -1 R (stop) or +B R (target) with p set so the mean is the net edge. Trades of a
day are sequential (one open at a time). No time limit (FTMO 2-Step has none, ftmo.com
2026-11-14), so each history is long and attempts are chained; unfinished attempts are reported.

Run: python research/screens/2026-11-14_challenge_pass_map.py [--runs 200] [--trades 12000]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from backtester.risk.monte_carlo import Day, MonteCarloConfig, ftmo_by_risk

EDGES = (-0.05, -0.02, 0.0, 0.02, 0.05, 0.10)
RISKS = (0.0025, 0.005, 0.01, 0.02)
PER_DAY = (1, 4)
B = 1.5  # target in R; sd of a trade ~1.22 R


def history(rng, edge: float, per_day: int, n_days: int, b: float = B) -> list[Day]:
    p = (1.0 + edge) / (1.0 + b)  # p*b - (1-p) = edge
    wins = rng.random((n_days, per_day)) < p
    r = np.where(wins, b, -1.0)
    days = []
    for row in r:
        events = tuple(e for x in row for e in ((True, float(x)), (False, float(x))))
        days.append(Day(r=row, events=events))
    return days


def cell(edge, per_day, runs, n_days, seed) -> dict:
    config = MonteCarloConfig(runs=1, risk_levels=RISKS, seed=seed)
    rng = np.random.default_rng(seed)
    tot = {r: {"attempts": 0, "passes": 0, "daily": 0, "unfinished": 0, "days": []} for r in RISKS}
    order = [np.arange(n_days)]
    for _ in range(runs):
        res = ftmo_by_risk(history(rng, edge, per_day, n_days), order, config)
        for risk, s in res.items():
            t = tot[risk]
            t["attempts"] += s["attempts"]
            t["passes"] += s["passes"]
            t["daily"] += s["fail_daily"]
            t["unfinished"] += s["unfinished_attempts"]
            if s["average_days_to_pass"] is not None:
                t["days"] += [s["average_days_to_pass"]] * s["passes"]
    return tot


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=200)
    ap.add_argument("--trades", type=int, default=12000)  # per history
    ap.add_argument("--out", type=Path, default=Path("results/challenge_pass_map.md"))
    a = ap.parse_args(argv)

    # self-check: zero edge at small risk is two fair barrier games, 0.5 * 10/15 = 1/3
    chk = cell(0.0, 1, 40, a.trades, 7)[0.0025]
    share = chk["passes"] / max(chk["attempts"], 1)
    assert 0.2 < share < 0.47, f"zero-edge self-check off: {share:.3f}"

    lines = [
        ("| edge R | trades/day | risk | attempts | pass % | daily-loss fails % | mean trading days to pass "
        "(both phases) | trades to pass | unfinished |"),
        "|---|---|---|---|---|---|---|---|---|",
    ]
    seed = 100
    for per_day in PER_DAY:
        for edge in EDGES:
            seed += 1
            for risk, t in cell(edge, per_day, a.runs, a.trades // per_day, seed).items():
                n = max(t["attempts"], 1)
                d = float(np.mean(t["days"])) if t["days"] else float("nan")
                lines.append(
                    f"| {edge:+.2f} | {per_day} | {risk:.2%} | {t['attempts']} | "
                    f"{100 * t['passes'] / n:.1f} | {100 * t['daily'] / n:.1f} | {d:.0f} | "
                    f"{d * per_day:.0f} | {t['unfinished']} |"
                )
            print(lines[-1], flush=True)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"self-check zero edge, 0.25 %: {share:.3f}; written {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
