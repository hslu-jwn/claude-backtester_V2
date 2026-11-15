"""FB-254 sequential forward boundaries for the forward paper logs (method, 2026-11-15; no data look).

Group-sequential test of H0: weekly net mean <= 0, one-sided alpha 2.5 %, looks every 13 weeks up to 104 weeks
(8 looks), O'Brien-Fleming efficacy boundary z_k >= c / sqrt(k / 8) with c calibrated by simulation; early kill when
z_k <= -2 at any look (the specs' 52-week kills stay). z = mean / (sd / sqrt(n)) with the sample sd of the logged
weeks. Prints boundaries (net mean needed at each look) and power at each log's fair expectation; `--check` reads the
forward CSVs in research/forward/ and prints each log's status at its latest completed look.
Run: .venv/Scripts/python.exe research/screens/2026-11-15_fb254_forward_boundaries.py [--check]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LOOK, K, ALPHA, KILL_Z = 13, 8, 0.025, -2.0
# log: (file, fair expectation bp a week, planning sd bp a week, source)
LOGS = {
    "Strategy 20": ("crypto_flow.csv", 74.0, 474.0, "spec › Execution: ~+74 after rebalance-day and taker checks; test sd"),
    "Strategy 20 top 100": ("crypto_flow_top100.csv", 74.0, 658.0, "same expectation (assumed); test sd of the variant"),
    "Strategy 19": ("crypto_carry.csv", 63.0, 624.0, "replication +63 (I73R); test sd"),
}


def calibrate(sims=200_000, seed=1):
    """c such that P(any z_k >= c / sqrt(k/K) | mean 0) = ALPHA (normal weekly nets, known sd)."""
    rng = np.random.default_rng(seed)
    z = np.cumsum(rng.standard_normal((sims, K)), axis=1) / np.sqrt(np.arange(1, K + 1))
    frac = np.sqrt(np.arange(1, K + 1) / K)
    lo, hi = 1.5, 3.5
    for _ in range(40):
        c = (lo + hi) / 2
        lo, hi = (lo, c) if ((z * frac >= c).any(axis=1)).mean() < ALPHA else (c, hi)
    return (lo + hi) / 2


def power(mu, sd, c, sims=100_000, seed=2):
    rng = np.random.default_rng(seed)
    drift = mu / sd * np.sqrt(LOOK)
    z = np.cumsum(rng.standard_normal((sims, K)) + drift, axis=1) / np.sqrt(np.arange(1, K + 1))
    frac = np.sqrt(np.arange(1, K + 1) / K)
    win, lose = z * frac >= c, z <= KILL_Z
    first_win = np.where(win.any(axis=1), win.argmax(axis=1), K)
    first_lose = np.where(lose.any(axis=1), lose.argmax(axis=1), K)
    return (first_win < first_lose).mean(), (first_lose < first_win).mean()


def main(argv):
    c = calibrate()
    print(f"O'Brien-Fleming c = {c:.3f} (8 looks, one-sided {ALPHA}); z boundary by look: "
          + ", ".join(f"{(k + 1) * LOOK}w {c / np.sqrt((k + 1) / K):.2f}" for k in range(K)))
    for name, (fname, mu, sd, src) in LOGS.items():
        need = [c / np.sqrt((k + 1) / K) * sd / np.sqrt((k + 1) * LOOK) for k in range(K)]
        win, lose = power(mu, sd, c)
        print(f"{name} (expect {mu:+.0f}, sd {sd:.0f}; {src}): confirm needs mean >= "
              + ", ".join(f"{(k + 1) * LOOK}w {n:.0f}" for k, n in enumerate(need))
              + f" bp; P(confirm by 104 w) {100 * win:.0f} %, P(early kill) {100 * lose:.0f} %; at mean 0: "
              f"P(kill) {100 * power(0.0, sd, c)[1]:.0f} %")
        if "--check" in argv:
            p = Path("research/forward") / fname
            if not p.exists():
                print("  check: no forward log yet")
                continue
            x = pd.read_csv(p).net_bp.to_numpy(float)
            k = len(x) // LOOK
            if k == 0:
                print(f"  check: {len(x)} weeks logged, first look at {LOOK}")
                continue
            y = x[: k * LOOK]
            z = y.mean() / (y.std(ddof=1) / np.sqrt(len(y)))
            state = ("CONFIRMED" if z >= c / np.sqrt(min(k, K) / K) else "KILL (z <= -2)" if z <= KILL_Z else "continue")
            print(f"  check: look {k} ({len(y)} weeks): mean {y.mean():+.1f} bp, z {z:.2f} -> {state}")


if __name__ == "__main__":
    main(sys.argv[1:])
