"""I-108 insider open-market purchases on US mid-caps, ranks 1,001-2,000 (rule fixed in knowledge/ideas.md, 0972ed9).

I-106's code unchanged (imported), only the universe file and the cost differ. Development only.
Steps: universe (signal-free), power (signal-free: Abdi-Ranaldo spread check + event count), run.
Run: .venv/Scripts/python.exe research/screens/2026-11-17_i108_midcap_insider_screen.py universe | power | run
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
MID = Path("data/cache/alpaca_meta/universe_1001_2000.csv")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"2026-11-17_{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ar_half_spread():
    """Median Abdi-Ranaldo (2017) half-spread (bp) over universe name-months 2016-04 .. 2021-08."""
    u = pd.read_csv(MID)
    u = u[(u.month >= "2016-04") & (u.month <= "2021-08")]
    keep = set(zip(u.symbol, u.month, strict=True))
    out = []
    for s in sorted(u.symbol.unique()):
        d = pd.read_csv(f"data/cache/alpaca_1d/{s}.csv", usecols=["ts", "high", "low", "close"])
        d.index = pd.to_datetime(d.ts, utc=True).dt.tz_convert("America/New_York").dt.strftime("%Y-%m")
        eta = (np.log(d.high) + np.log(d.low)) / 2
        c = np.log(d.close)
        s2 = 4 * (c - eta) * (c - eta.shift(-1))
        m = s2.groupby(level=0).mean().clip(lower=0) ** 0.5
        out += [v for k, v in m.items() if (s, k) in keep]
    out = np.asarray(out, float)  # NaN: name-months without a valid two-day pair
    return float(np.nanmedian(out)) / 2 * 1e4, int(np.isfinite(out).sum())


def cost():
    half, n = ar_half_spread()
    fill = max(10.0, half + 3.0)
    print(f"Abdi-Ranaldo half-spread median {half:.1f} bp over {n} name-months -> stock fill {fill:.1f} bp")
    return 2 * fill + 2.0


if __name__ == "__main__":
    step = sys.argv[1]
    if step == "universe":
        _load("card2_share_universe").universe(1001, 2000, MID.name)
    else:
        i106 = _load("i106_insider_buys_screen")
        i106.UNIVERSE, i106.COST = MID, cost()
        print(f"cost per event {i106.COST:.1f} bp, doubled {2 * i106.COST:.1f}")
        r = i106.event_returns(i106.filings("P", i106.MIN_VALUE))
        if step == "power":
            i106.power(r)
        else:
            i106.run(r, i106.event_returns(i106.filings("S", 1e6), sign=-1.0))
