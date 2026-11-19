"""I-132 Treasury month-end x indexation era (rule fixed in knowledge/ideas.md › I-132, commit 5116e42).

Reuses the I-109 statistic (last 3 trade dates, excess over the month's other dates, DGS10 par-bond duration) on the
unseen 1962-1989 years. No trading gate: a causal reading for I-109's mechanism.
Run: .venv/Scripts/python.exe research/screens/2026-11-19_i132_month_end_eras.py power | run
"""

import importlib.util
import sys

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("i109", "research/screens/2026-11-17_i109_treasury_month_end_screen.py")
i109 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i109)

ERAS = {"E0 1962-72": ("1962-01-01", "1972-12-31"), "E1 1973-89": ("1973-01-01", "1989-12-31"),
        "E2 1990-2021": (i109.START, i109.END)}


def mid_month(r, days=3):
    """Per month: 3 returns centred on the first trade date on or after the 15th; excess as in i109.months."""
    rows = {}
    for m, g in r.groupby(r.index.to_period("M")):
        k = int(np.searchsorted(g.index.day, 15))
        if k < 1 or k + 2 > len(g) - 3:  # needs a neighbour each side and no overlap with the month-end window
            continue
        w = g.iloc[k - 1 : k + 2]
        rows[m] = w.sum() - days * g.drop(w.index).mean()
    return pd.Series(rows)


def power():
    for name, (a, b) in ERAS.items():
        r = i109.returns("DGS10", a, b)
        sd = pd.concat([i109.months(r, k).excess for k in (5, 8, 11, 14)], axis=1).std().mean()
        n = len(i109.months(r))
        print(f"{name}: months {n}, signal-free excess sd {sd:.1f} bp, se {sd / np.sqrt(n):.1f}")


def shuffled(r, draws=200, seed=7):
    """Random 3-date window per month (not touching the last 3 dates): share of draws with t >= 2.0."""
    rng = np.random.default_rng(seed)
    groups = [g for _, g in r.groupby(r.index.to_period("M")) if len(g) >= 10]
    hits = 0
    for _ in range(draws):
        x = []
        for g in groups:
            k = rng.integers(0, len(g) - 6)
            w = g.iloc[k : k + 3]
            x.append(w.sum() - 3 * g.drop(w.index).mean())
        hits += i109.tstat(x) >= 2.0
    return hits / draws


def run():
    res = {}
    for name, (a, b) in ERAS.items():
        r = i109.returns("DGS10", a, b)
        e, mm = i109.months(r).excess, mid_month(r)
        res[name] = e
        print(f"{name}: month-end excess {e.mean():+.1f} bp (t {i109.tstat(e):.2f}, n {len(e)}); "
              f"mid-month {mm.mean():+.1f} (t {i109.tstat(mm):.2f})")
    e0, e2 = res["E0 1962-72"], res["E2 1990-2021"]
    se0 = e0.std(ddof=1) / np.sqrt(len(e0))
    diff_t = (e2.mean() - e0.mean()) / np.sqrt(se0**2 + e2.var(ddof=1) / len(e2))
    if abs(e0.mean()) <= 2 * se0 and diff_t >= 2.0:
        verdict = "SUPPORTED (index mechanism)"
    elif e0.mean() >= 10 and i109.tstat(e0) >= 2.0:
        verdict = "NOT SUPPORTED (month-end excess without indexing)"
    else:
        verdict = "UNCLEAR"
    print(f"E2 - E0 {e2.mean() - e0.mean():+.1f} bp, t {diff_t:.2f} -> {verdict}")
    allpre = pd.concat([res["E0 1962-72"], res["E1 1973-89"]])
    print("reported: by decade", allpre.groupby((allpre.index.year // 10) * 10).agg(["mean", "count"]).round(1).to_dict("index"))
    print(f"shuffled-label control 1962-1989: {shuffled(i109.returns('DGS10', '1962-01-01', '1989-12-31')):.1%} of 200 random "
          "windows reach t >= 2.0")


if __name__ == "__main__":
    {"power": power, "run": run}[sys.argv[1]]()
