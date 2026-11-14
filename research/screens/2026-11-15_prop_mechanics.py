"""Prop mechanics (Fable directions rows 2 and 13, 2026-11-15): FTMO 2-Step pass chance by sizing policy and by the
number of concurrent weak streams. Synthetic trades (-1 R or +1.5 R, p set for the edge), played by the house
simulator (`risk.monte_carlo.ftmo_by_risk`); no market data, no rule.

A. Sizing: fixed risk vs the house adaptive risk (`risk.adaptive.AdaptiveRisk` defaults: risk x room to the max-loss
   line / full room, floor 25 %, daily budget 3 %), 1 trade a day.
B. Streams: K streams, each one trade a day with the same edge, all open together during the day (K entries, then K
   exits), outcome correlation rho through a Gaussian copula; fixed risk per trade.
Run: .venv/Scripts/python.exe research/screens/2026-11-15_prop_mechanics.py [--runs 150]
"""
import sys
from statistics import NormalDist

import numpy as np

from backtester.risk.adaptive import AdaptiveRisk
from backtester.risk.monte_carlo import Day, MonteCarloConfig, ftmo_by_risk

B = 1.5
PHI = NormalDist().cdf


def days(rng, edge, k, n_days, rho=0.0):
    p = (1.0 + edge) / (1.0 + B)
    z = np.sqrt(rho) * rng.standard_normal((n_days, 1)) + np.sqrt(1 - rho) * rng.standard_normal((n_days, k))
    u = np.vectorize(PHI)(z) if rho else rng.random((n_days, k))
    r = np.where(u < p, B, -1.0)
    out = []
    for row in r:
        ev = tuple((True, float(x)) for x in row) + tuple((False, float(x)) for x in row)
        ids = tuple(range(k)) * 2
        out.append(Day(r=row, events=ev, ids=ids))
    return out


def run(edge, k, risks, runs, n_days, seed, rho=0.0, adaptive=None):
    cfg = MonteCarloConfig(runs=1, risk_levels=risks, seed=seed, adaptive=adaptive)
    rng = np.random.default_rng(seed)
    tot = {r: [0, 0, 0, [], 0] for r in risks}  # attempts, passes, daily fails, days to pass, unfinished
    for _ in range(runs):
        res = ftmo_by_risk(days(rng, edge, k, n_days, rho), [np.arange(n_days)], cfg)
        for r, s in res.items():
            t = tot[r]
            t[0] += s["attempts"]
            t[1] += s["passes"]
            t[2] += s["fail_daily"]
            t[4] += s["unfinished_attempts"]
            if s["average_days_to_pass"] is not None:
                t[3] += [s["average_days_to_pass"]] * s["passes"]
    # pass % over all attempts incl. unfinished ones (counted as not passed): a policy that slows failures
    # down must not look better by leaving attempts open
    return {r: (100 * t[1] / max(t[0] + t[4], 1), 100 * t[2] / max(t[0] + t[4], 1),
                float(np.mean(t[3])) if t[3] else float("nan"), 100 * t[4] / max(t[0] + t[4], 1))
            for r, t in tot.items()}


def main(argv):
    runs = int(argv[argv.index("--runs") + 1]) if "--runs" in argv else 150
    risks = (0.0025, 0.005, 0.01, 0.02)
    print("A. sizing policy, 1 trade a day: pass % (unfinished attempts count as not passed) / mean trading days to "
          "pass (both phases) / share of attempts still open at the end of a 4,000-day history")
    print("| edge R | policy | " + " | ".join(f"{r:.2%}" for r in risks) + " |")
    print("|---|---|" + "---|" * len(risks))
    seed = 500
    for edge in (-0.02, 0.0, 0.02, 0.05):
        for name, ad in (("fixed", None), ("adaptive", AdaptiveRisk())):
            seed += 1
            res = run(edge, 1, risks, runs, 4000, seed, adaptive=ad)
            print(f"| {edge:+.2f} | {name} | " + " | ".join(f"{p:.0f} % / {d:.0f} d / {u:.0f} % open" for p, _, d, u in res.values()) + " |",
                  flush=True)
    print("\nB. K concurrent streams (one trade a day each), fixed risk per trade: pass % / months to pass (21 days)"
          " / daily-loss fails %")
    print("| edge per stream | rho | K | 0.25 % | 0.5 % | 1 % |")
    print("|---|---|---|---|---|---|")
    for edge in (0.02, 0.03, 0.05):
        for rho in (0.0, 0.3):
            for k in (1, 2, 3, 5):
                seed += 1
                res = run(edge, k, (0.0025, 0.005, 0.01), runs, 3000, seed, rho=rho)
                print(f"| {edge:+.2f} | {rho} | {k} | " + " | ".join(
                    f"{p:.0f} % / {d / 21:.1f} m / {f:.0f} %" for p, f, d, _ in res.values()) + " |", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
