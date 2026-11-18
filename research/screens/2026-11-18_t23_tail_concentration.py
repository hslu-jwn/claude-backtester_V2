"""T-23 tail concentration audit (knowledge/ideas.md T-23; Taleb, Fat Tails p.16-17, 54-55, 148-150).

Diagnostic on spent data, no new look and no verdict change. Streams, as registered:
- Strategy 20 (crypto taker-flow sort, full universe, crypto_flow default config): weekly net bp, development
  2020..2023 and test 2024-01 .. 2026-10 (spec: 186 / 147 weeks, +145.0 / +147.2).
- I-109 (Treasury month-end, DGS10 excess statistic, cost 2 bp): monthly net bp, development 1990-01 .. 2021-08 and
  test 2021-10 .. 2026-10 (card: 380 / 61 months, +18.4 / +24.9).
Per series: share of the single largest observation in sum |r|^p (p = 1, 2, 4; Gaussian n = 10,000 gives ~0.008 at
p = 4), and mean / t after removing the k largest gains or the k largest losses (k = 1, 2, 5), sensitivity only.
Flag (fixed before the run): FRAGILE if removing the 5 largest gains leaves mean <= 0; CONCENTRATED if one observation
holds > 25 % of sum r^4. Run: .venv/Scripts/python.exe research/screens/2026-11-18_t23_tail_concentration.py
"""

import importlib.util
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.tools import crypto_flow as cf

spec = importlib.util.spec_from_file_location(
    "i109", Path(__file__).parent / "2026-11-17_i109_treasury_month_end_screen.py"
)
i109 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i109)


def tstat(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def audit(name, x):
    x = pd.Series(x, dtype=float).dropna().reset_index(drop=True)
    a = x.abs()
    shares = {p: (a**p).max() / (a**p).sum() for p in (1, 2, 4)}
    big = x.loc[(a**4).idxmax()]
    print(
        f"{name}: n {len(x)}, mean {x.mean():+.1f}, t {tstat(x):.2f}, sd {x.std():.0f}; largest {big:+.0f} "
        f"({'gain' if big > 0 else 'loss'}); max share p1 {shares[1]:.3f}  p2 {shares[2]:.3f}  p4 {shares[4]:.3f}"
    )
    rows = []
    for k in (1, 2, 5):
        g = x.drop(x.nlargest(k).index)
        lo = x.drop(x.nsmallest(k).index)
        rows.append(
            f"k={k}: w/o top gains {g.mean():+.1f} (t {tstat(g):.2f}) | w/o top losses {lo.mean():+.1f} (t {tstat(lo):.2f})"
        )
    print("   " + "\n   ".join(rows))
    no5 = x.drop(x.nlargest(5).index).mean()
    flags = [f for f, hit in (("FRAGILE", no5 <= 0), ("CONCENTRATED", shares[4] > 0.25)) if hit]
    print("   flags:", ", ".join(flags) or "none")


def main():
    k0, f0 = cf.load()
    for name, a, b in (
        ("S20 development", date(2020, 1, 1), date(2023, 12, 31)),
        ("S20 test", date(2024, 1, 1), date(2026, 10, 25)),
    ):
        trades, _ = cf.compute_weeks(k0, f0, a, b)
        audit(name, [t["net_bp"] for t in trades])
    for name, start, end, first, last in (
        ("I-109 development", "1990-01-01", "2021-09-13", "1990-01", "2021-08"),
        ("I-109 test", "2021-09-14", "2026-10-31", "2021-10", "2026-10"),
    ):
        m = i109.months(i109.returns("DGS10", start, end)).loc[first:last]
        audit(name, m.excess - 2.0)


if __name__ == "__main__":
    main()
