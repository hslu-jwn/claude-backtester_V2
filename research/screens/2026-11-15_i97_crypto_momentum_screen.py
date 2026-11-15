"""I-97 screen: cross-sectional 3-week momentum on all Binance USDT perps (knowledge/ideas.md › I-97; rule fixed in
the commit before this script).

Reuses the Wave 1 tool (I-78 eligibility, legs, funding, 20 bp; canary must reproduce I-78 first). Signal mom3 = last
close before the Monday / close 21 bars earlier - 1 (>= 22 bars). Direction pre-registered: long winners.
Development 2020-01..2023-12 only. Kills: net <= 0; t < 3.0; halves not both > 0; net <= 0 at 40 bp; without the
2 best weeks <= 0. Run: .venv/Scripts/python.exe research/screens/2026-11-15_i97_crypto_momentum_screen.py
"""
import importlib.util

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("w1", "research/screens/2026-11-15_wave1_xs_crypto_screen.py")
w1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w1)
i78, COST, HALF = w1.i78, w1.COST, w1.HALF


def main():
    k, fund = i78.load()
    wk = w1.weekly(k, fund, {})
    canary = pd.Series([w1.legs_gross(w, "flow") for w in wk.values()]) - COST
    assert len(canary) == 186 and abs(canary.mean() - 145.0) < 0.05, "canary failed"
    print(f"CANARY I-78 ok: {len(canary)} weeks, net {canary.mean():+.1f}")
    for m, w in wk.items():
        mom = []
        for s in w.sym:
            c = k[s].close[k[s].index < m]
            mom.append(c.iloc[-1] / c.iloc[-22] - 1 if len(c) >= 22 else np.nan)
        w["mom3"] = mom
    idx = sorted(wk)
    g = pd.Series([w1.legs_gross(wk[m], "mom3") for m in idx], index=idx).dropna()
    net = g - COST
    h = net[net.index < HALF].mean(), net[net.index >= HALF].mean()
    t = w1.tstat(net)
    best2 = net.drop(net.nlargest(2).index).mean()
    kills = {"net <= 0": net.mean() <= 0, "t < 3": t < 3.0, "halves": not (h[0] > 0 and h[1] > 0),
             "40 bp <= 0": (g - 2 * COST).mean() <= 0, "without 2 best <= 0": best2 <= 0}
    print(f"I-97 3-week momentum (long winners): {len(net)} weeks, gross {g.mean():+.1f}, net {net.mean():+.1f} bp/week, "
          f"t {t:.2f}, positive {100 * (net > 0).mean():.0f} %, worst {net.min():+.0f}; halves {h[0]:+.1f} / {h[1]:+.1f}; "
          f"at 40 bp {(g - 2 * COST).mean():+.1f}; without 2 best {best2:+.1f}")
    print("kills:", {a: bool(b) for a, b in kills.items()}, "->", "KILLED" if any(kills.values()) else "PASSED")
    rng = np.random.default_rng(7)
    pt = [w1.tstat(pd.Series([w1.legs_gross(wk[m], "mom3", rng) for m in idx]).dropna()) for _ in range(20)]
    print(f"DIAG placebo gross t (20 draws): mean {np.mean(pt):+.2f}, |t| >= 3 in {sum(abs(x) >= 3 for x in pt)}")
    print(f"DIAG deciles (low -> high mom3): {w1.deciles(wk, 'mom3')}")
    s20 = pd.Series({m: w1.legs_gross(w, "flow") for m, w in wk.items()})
    print(f"DIAG weekly correlation with Strategy 20: {pd.concat([g, s20], axis=1).dropna().corr().iloc[0, 1]:+.2f}")


if __name__ == "__main__":
    main()
