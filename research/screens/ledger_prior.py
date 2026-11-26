"""Empirical-Bayes prior per family type from the ledger's est / se (lead review A change 8; file 10 › C).

No data look: only rows already recorded in research/ledger.csv. Model per type f: t_i = est / se (right sign
positive), t | delta ~ N(delta, 1), delta ~ (1 - pi) * 0 + pi * HalfNormal(sigma). Marginal (skew-normal slab):
L(t) = (1 - pi) phi(t) + pi * 2 phi(t; 0, sqrt(1 + s^2)) Phi(s t / sqrt(1 + s^2)). (pi, sigma) by maximum likelihood
on a grid, per type with a Beta hyperprior on pi whose mean is the all-type pi (partial pooling, JKP one level).
Rows used: est_basis gross, est_sample not "expected" (looked-at rows only; power closures are missing not at random,
so pi reads "among looked-at rows"), one row per dup_group. Net rows are counted, not fitted (cost drag).
Run: .venv/Scripts/python.exe research/screens/ledger_prior.py
"""

import csv
import math
import sys
from pathlib import Path

import numpy as np

LEDGER = Path("research/ledger.csv")
PI_GRID = np.linspace(0, 1, 201)
S_GRID = np.linspace(0.05, 6, 120)
STRENGTH = 10.0  # Beta hyperprior a + b (assumption, Opus 2026-11-27): about 10 rows' worth of pull to the pooled pi
TYPES = {
    "a": "forced / dated flow",
    "b": "published premium",
    "c": "crypto breadth",
    "d": "share anomaly",
    "e": "practitioner / pattern",
    "f": "original",
}

_erf = np.vectorize(math.erf)


def phi(x, sd=1.0):
    return np.exp(-0.5 * (x / sd) ** 2) / (sd * math.sqrt(2 * math.pi))


def Phi(x):
    return 0.5 * (1 + _erf(np.asarray(x, dtype=float) / math.sqrt(2)))


def slab(t, s):
    v = math.sqrt(1 + s * s)
    return 2 * phi(t, v) * Phi(s * t / v)


def marginal(t, pi, s):
    t = np.asarray(t, dtype=float)
    return (1 - pi) * phi(t) + pi * slab(t, s)


def fit(t, prior_mean=None, strength=STRENGTH):
    """(pi, sigma) maximising the log-likelihood (+ log Beta(pi) when prior_mean is given)."""
    t = np.asarray(t, dtype=float)
    null = phi(t)
    slabs = np.array([slab(t, s) for s in S_GRID])  # (S, n)
    pi = PI_GRID[:, None, None]
    ll = np.log((1 - pi) * null + pi * slabs[None] + 1e-300).sum(axis=2)  # (P, S)
    if prior_mean is not None:
        a, b = prior_mean * strength, (1 - prior_mean) * strength
        p = np.clip(PI_GRID, 1e-9, 1 - 1e-9)
        ll = ll + ((a - 1) * np.log(p) + (b - 1) * np.log(1 - p))[:, None]
    i, j = np.unravel_index(np.argmax(ll), ll.shape)
    return float(PI_GRID[i]), float(S_GRID[j])


def posterior_positive(t, pi, s):
    t = np.asarray(t, dtype=float)
    return pi * slab(t, s) / marginal(t, pi, s)


def observations(rows):
    """type -> [(id, t)] for gross, looked-at rows, first row per dup_group."""
    out, seen = {}, set()
    for r in rows:
        if (
            not r["est"].strip()
            or r["est_basis"] != "gross"
            or r["est_sample"] == "expected"
            or not r["type"]
        ):
            continue
        if r["dup_group"]:
            if r["dup_group"] in seen:
                continue
            seen.add(r["dup_group"])
        out.setdefault(r["type"], []).append((r["id"], float(r["est"]) / float(r["se"])))
    return out


def main():
    with open(LEDGER, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    obs = observations(rows)
    net = sum(1 for r in rows if r["est"].strip() and r["est_basis"] == "net")
    allt = [t for v in obs.values() for _, t in v]
    if len(allt) < 5:
        sys.exit(f"only {len(allt)} usable gross rows: backfill first")
    pi0, s0 = fit(allt)
    print(
        f"all types: n {len(allt)}, pi {pi0:.2f}, sigma {s0:.2f}, prior odds {1 - pi0:.2f}:{pi0:.2f}  (net rows not fitted: {net})"
    )
    print(
        f"{'type':26} {'n':>3} {'mean t':>7} {'pi free':>8} {'pi pooled':>9} {'sigma':>6} {'odds 1:x':>8}"
    )
    for k, name in TYPES.items():
        t = np.array([x for _, x in obs.get(k, [])])
        if not len(t):
            print(f"{k} {name:24} {0:>3}")
            continue
        free = fit(t)[0]
        pi, s = fit(t, prior_mean=pi0)
        odds = (1 - pi) / pi if pi > 0 else float("inf")
        print(
            f"{k} {name:24} {len(t):>3} {t.mean():>7.2f} {free:>8.2f} {pi:>9.2f} {s:>6.2f} {odds:>8.1f}"
        )


if __name__ == "__main__":
    main()
