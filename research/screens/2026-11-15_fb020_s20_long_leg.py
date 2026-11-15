"""FB-020 diagnostic: Strategy 20's long leg alone, hedged with BTCUSDT (beta 1), from the frozen book's legs.

Per week: mean long-leg price return + its funding - BTCUSDT's Monday open -> Sunday close return (+ BTC funding a
short receives) - 12 bp (long-leg round trip + BTC hedge round trip, the card's cell). Spent periods: diagnostic.
Run: .venv/Scripts/python.exe research/screens/2026-11-15_fb020_s20_long_leg.py
"""
from datetime import date

import numpy as np
import pandas as pd

from backtester.tools import crypto_flow as cf

COST = 12.0


def main():
    k, f = cf.load()
    btc, bf = k["BTCUSDT"], f["BTCUSDT"]
    for name, a, b in (("development", date(2020, 1, 1), date(2023, 12, 31)), ("test", date(2024, 1, 1), date(2026, 10, 31))):
        _, legs = cf.compute_weeks(k, f, a, b)
        lg = pd.DataFrame(legs)
        out = []
        for wk, g in lg.groupby("week"):
            lo, sh = g[g.side == "long"], g[g.side == "short"]
            held = btc[(btc.index >= wk) & (btc.index < wk + pd.Timedelta(days=7))]
            r_btc = (held.close.iloc[-1] / held.open.iloc[0] - 1) * 1e4
            f_btc = bf[(bf.index > wk) & (bf.index < wk + pd.Timedelta(days=7))].sum() * 1e4
            out.append((lo.price_bp.mean() + lo.funding_bp.mean() - r_btc + f_btc - COST,
                        -sh.price_bp.mean() + sh.funding_bp.mean() + r_btc - f_btc - COST))
        o = np.array(out)
        for j, leg in enumerate(("long leg - BTC", "BTC - short leg")):
            x = o[:, j]
            print(f"{name} {leg}: {len(x)} weeks, net {x.mean():+.1f} bp/week, t {x.mean() / x.std(ddof=1) * np.sqrt(len(x)):.2f}, "
                  f"worst {x.min():+.0f}")


if __name__ == "__main__":
    main()
