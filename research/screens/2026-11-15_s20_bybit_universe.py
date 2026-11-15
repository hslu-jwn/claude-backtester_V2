"""Diagnostic (not a look at a new rule): frozen Strategy 20 on the spent test period, restricted to perps listed on Bybit.

Bybit list: public v5 instruments-info (linear), fetched 2026-11-15 into data/cache/bybit (current listings only, so
coins Bybit delisted are missing). A Binance perp counts from its Bybit launch day. Prices and funding stay Binance.
Run: .venv/Scripts/python.exe research/screens/2026-11-15_s20_bybit_universe.py
"""

import json
import re
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.tools import crypto_flow as cf

by = json.loads(Path("data/cache/bybit/linear_instruments_2026-11-15.json").read_text(encoding="utf-8"))


def base(s):
    s = re.sub(r"USDT$", "", s)
    return re.sub(r"^(1000000|100000|10000|1000|1M)|1000$", "", s)


launch = {}
for x in by:
    if x["type"] == "LinearPerpetual" and x["symbol"].endswith("USDT"):
        b = base(x["symbol"])
        launch[b] = min(launch.get(b, 1e18), x["launch"])
k, f = cf.load()
kb, fb, miss = {}, {}, 0
for s, d in k.items():
    b = base(s)
    if b not in launch:
        miss += 1
        continue
    t0 = pd.Timestamp(launch[b], unit="ms", tz="UTC").normalize()
    dd = d[d.index >= t0]
    if len(dd):
        kb[s], fb[s] = dd, f[s]
print(f"Binance perps {len(k)}, on Bybit now {len(kb)}, not on Bybit (or delisted there) {miss}")
legs_all = None
for name, (kk, ff) in {"all Binance": (k, f), "Bybit-listed": (kb, fb)}.items():
    tr, legs = cf.compute_weeks(kk, ff, date(2024, 1, 1), date(2026, 10, 31))
    legs_all = legs if legs_all is None else legs_all
    n = np.array([t["net_bp"] for t in tr])
    print(
        f"{name}: weeks {len(n)}, net {n.mean():+.1f} bp/week, t {n.mean() / n.std(ddof=1) * np.sqrt(len(n)):.2f}, "
        f"eligible/week {np.mean([t['n_eligible'] for t in tr]):.0f}"
    )
full = pd.DataFrame(legs_all)
cov = full.symbol.map(lambda s: base(s) in launch)
print(f"legs of the full-universe book whose coin is on Bybit now: {100 * cov.mean():.0f} %")
