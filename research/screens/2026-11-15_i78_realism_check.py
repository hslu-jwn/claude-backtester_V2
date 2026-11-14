"""Strategy 20 / I-78 realism check (2026-11-15): how much of the tested edge survives real execution.

Diagnostics on the spent development and test periods; no gate, no rule change (a changed rule would be a new,
counted hypothesis with forward data only). Uses the frozen screen's functions.
1. Break-even extra cost: extra slippage per side per member that brings the weekly net to 0 (each member pays it
   on entry and exit: 4 fills per unit pair a week -> extra bp a week = 4 x s).
2. Liquidity tiers: each member's 30-day median quote volume at entry; net when the weakest-liquidity tier pays
   tiered extra slippage (< 20 M USDT: 25 bp a side, 20-100 M: 10 bp, > 100 M: 3 bp), and the book restricted to the
   most liquid half of the eligible symbols (a new variant: diagnostic only).
3. Capacity: member notional as a share of its daily quote volume at a given account size.
Run: .venv/Scripts/python.exe research/screens/2026-11-15_i78_realism_check.py
"""
import importlib.util

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("s", "research/screens/2026-11-14_i78_crypto_wide_factors_screen.py")
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
s.END = pd.Timestamp("2026-10-31")
TIERS = ((20e6, 25.0), (100e6, 10.0), (np.inf, 3.0))  # (upper median quote volume, extra bp per side)


def tstat(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def main():
    k, fund = s.load((s.ROOT, s.TEST_ROOT))
    rows = []
    for mon in s.mondays(k):
        w = s.week_rows(k, fund, mon)
        if len(w) < s.MIN_ELIG:
            continue
        w["qvol"] = [k[x].quote_volume[k[x].index < mon].iloc[-30:].median() for x in w.sym]
        rows.append(w.assign(week=mon))
    d = pd.concat(rows, ignore_index=True)

    def book(part, liquid_half=False):
        out = {}
        for mon, w in part.groupby("week"):
            if liquid_half:
                w = w[w.qvol >= w.qvol.median()]
            w = w.dropna(subset=["flow"]).sort_values(["flow", "sym"], kind="mergesort")
            n = len(w) // 5
            if n == 0:
                continue
            lo, hi = w.iloc[:n], w.iloc[-n:]
            extra = lambda m: m.qvol.map(lambda q: next(c for u, c in TIERS if q < u)).mean()
            out[mon] = {"gross": hi.ret.mean() - lo.ret.mean() - hi.fund.mean() + lo.fund.mean(),
                        "tier_cost": 2 * extra(hi) + 2 * extra(lo), "n": n,
                        "qvol_med": pd.concat([lo, hi]).qvol.median(),
                        "share_small": (pd.concat([lo, hi]).qvol < 20e6).mean()}
        return pd.DataFrame(out).T

    for name, part in (("development", d[d.week < s.TEST_START]), ("test", d[d.week >= s.TEST_START])):
        b = book(part)
        net = b.gross - s.COST_BP
        print(f"\n{name}: {len(b)} weeks, net {net.mean():+.1f} bp/week (t {tstat(net):.2f})")
        print(f"  break-even extra slippage: {net.mean() / 4:.1f} bp per side per member (4 fills a week)")
        tiered = b.gross - s.COST_BP - b.tier_cost
        print(f"  tiered slippage (<20M 25 bp, 20-100M 10 bp, >100M 3 bp a side): extra {b.tier_cost.mean():.1f} "
              f"bp/week -> net {tiered.mean():+.1f} (t {tstat(tiered):.2f}); members < 20 M: {100 * b.share_small.mean():.0f} %, "
              f"median member volume {b.qvol_med.median() / 1e6:.0f} M USDT")
        h = book(part, liquid_half=True)
        hn = h.gross - s.COST_BP
        ht = h.gross - s.COST_BP - h.tier_cost
        print(f"  most liquid half only (variant): legs {int(h.n.min())}-{int(h.n.max())}, net {hn.mean():+.1f} "
              f"(t {tstat(hn):.2f}), with tiered slippage {ht.mean():+.1f} (t {tstat(ht):.2f})")
    # capacity at the test period's legs: notional per member vs its median daily quote volume
    t = d[d.week >= s.TEST_START]
    legs = book(t)
    for equity, risk in ((100_000, 0.01), (1_000_000, 0.01)):
        side = equity * risk / 0.06  # 1 R = 600 bp of one side's notional
        per = side / legs.n.median()
        print(f"\ncapacity: equity {equity:,} at {risk:.0%} risk per R -> {side:,.0f} per side, ~{per:,.0f} per member; "
              f"vs the 5 M floor {100 * per / 5e6:.3f} % of a day's volume")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
