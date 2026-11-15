"""FB-022 rebalance-day robustness of Strategy 20 (diagnostic on spent periods; criteria fixed before the run).

The frozen book (`docs/strategy-crypto_flow.md` › Rule) anchored on each weekday: klines and funding are relabelled
k days earlier, so the tool's "Monday" is the original weekday k (k = 0 is the real book). Development 2020-2023 and
test 2024-01..2026-10. Flag a concern if any anchor's net <= 0 in either period, or if the mean of the six non-Monday
anchors is below half of the Monday anchor's net in either period.
Run: .venv/Scripts/python.exe research/screens/2026-11-15_fb022_s20_rebalance_day.py
"""
from datetime import date

import numpy as np
import pandas as pd

from backtester.tools import crypto_flow as cf

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
PERIODS = {"development": (date(2020, 1, 1), date(2023, 12, 31)), "test": (date(2024, 1, 1), date(2026, 10, 31))}


def shifted(k, klines, funding):
    dt = pd.Timedelta(days=k)
    return ({s: d.set_axis(d.index - dt) for s, d in klines.items()},
            {s: (f.set_axis(f.index - dt) if f is not None else None) for s, f in funding.items()})


def main():
    k0, f0 = cf.load()
    res = {}
    for k, day in enumerate(DAYS):
        kk, ff = shifted(k, k0, f0)
        for name, (a, b) in PERIODS.items():
            tr, _ = cf.compute_weeks(kk, ff, a, b)
            n = np.array([t["net_bp"] for t in tr])
            res[(day, name)] = (n.mean(), n.mean() / n.std(ddof=1) * np.sqrt(len(n)), len(n))
            print(f"{day} anchor, {name}: {len(n)} weeks, net {n.mean():+.1f} bp/week, t {res[(day, name)][1]:.2f}")
    for name in PERIODS:
        mon = res[("Mon", name)][0]
        other = np.mean([res[(d, name)][0] for d in DAYS[1:]])
        bad = [d for d in DAYS if res[(d, name)][0] <= 0]
        flag = bool(bad) or other < mon / 2
        print(f"{name}: Monday {mon:+.1f}, other six mean {other:+.1f}; anchors <= 0: {bad or 'none'} -> "
              f"{'CONCERN' if flag else 'robust'}")


if __name__ == "__main__":
    main()
