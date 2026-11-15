"""I-98 screen: spot-hedged funding carry on Binance (knowledge/ideas.md › I-98; rule fixed in commit 2ec4526).

Development 2020-01..2023-12. Each Monday: Strategy 20's eligibility (I-78 week_rows) + spot bars (Monday and the 7
before); rank by funding settled in the 7 days before the Monday; hold the 10 highest with a positive sum. Per name:
spot return - perp return (Monday open -> Sunday close) + funding inside the hold (week_rows' `fund`, a short receives
it). Cost 25 bp per name entering and 25 per name leaving (per unit notional). Kills: net <= 0; t < 3.0; halves
2020-21 / 2022-23 not both > 0; doubled costs <= 0; without the 2 best weeks <= 0.
Run: .venv/Scripts/python.exe research/screens/2026-11-15_i98_basis_carry_screen.py
"""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("i78", "research/screens/2026-11-14_i78_crypto_wide_factors_screen.py")
i78 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i78)
SPOT = Path("data/cache/binance_wide_spot/klines_1d")
N, COST, HALF = 10, 25.0, pd.Timestamp("2022-01-01")


def spot(sym):
    d = pd.read_csv(SPOT / f"{sym}.csv", usecols=["open_time", "open", "close"])
    d.index = pd.to_datetime(d.open_time, unit="ms").dt.normalize()
    return d[~d.index.duplicated()].sort_index()


def tstat(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def main():
    k, fund = i78.load()
    sp = {p.stem: spot(p.stem) for p in SPOT.glob("*.csv")}
    rows, held = [], set()
    for m in i78.mondays(k):
        w = i78.week_rows(k, fund, m)
        if len(w) < i78.MIN_ELIG:
            continue
        cand = []
        for s in w.sym:
            d = sp.get(s)
            if d is None or m not in d.index or len(d[(d.index < m) & (d.index >= m - pd.Timedelta(days=7))]) < 7:
                continue
            f = fund.get(s)
            if f is None:
                continue
            past = f[(f.index > m - pd.Timedelta(days=7)) & (f.index <= m)].sum()  # settled before the entry (incl. Monday 00:00)
            if past > 0:
                cand.append((past, s))
        pick = [s for _, s in sorted(cand, key=lambda x: (-x[0], x[1]))[:N]]
        new = set(pick)
        turnover = len(new - held) + len(held - new)
        n = max(len(new), 1)
        if not pick:
            rows.append((m, 0.0, 0.0, 0.0, turnover * COST / max(len(held), 1), 0))
            held = new
            continue
        wi = w.set_index("sym")
        basis, carry = [], []
        for s in pick:
            d = sp[s]
            hs = d[(d.index >= m) & (d.index <= m + pd.Timedelta(days=6))]
            r_spot = (hs.close.iloc[-1] / hs.open.iloc[0] - 1) * 1e4
            basis.append(r_spot - wi.loc[s, "ret"])
            carry.append(wi.loc[s, "fund"])  # funding a long pays = what the short perp receives
        cost = turnover * COST / n
        rows.append((m, np.mean(basis), np.mean(carry), np.mean(basis) + np.mean(carry), cost, len(pick)))
        held = new
    r = pd.DataFrame(rows, columns=["monday", "basis", "carry", "gross", "cost", "n"]).set_index("monday")
    net = r.gross - r.cost
    h = net[net.index < HALF].mean(), net[net.index >= HALF].mean()
    t = tstat(net)
    best2 = net.drop(net.nlargest(2).index).mean()
    kills = {"net <= 0": net.mean() <= 0, "t < 3": t < 3.0, "halves": not (h[0] > 0 and h[1] > 0),
             "doubled costs <= 0": (r.gross - 2 * r.cost).mean() <= 0, "without 2 best <= 0": best2 <= 0}
    print(f"I-98: {len(r)} weeks ({(r.n == 0).sum()} flat), names/week {r.n[r.n > 0].mean():.1f}; gross {r.gross.mean():+.1f} "
          f"(funding {r.carry.mean():+.1f}, basis {r.basis.mean():+.1f}), cost {r.cost.mean():.1f}, net {net.mean():+.1f} bp/week, "
          f"t {t:.2f}, worst {net.min():+.0f}; halves {h[0]:+.1f} / {h[1]:+.1f}; doubled costs {(r.gross - 2 * r.cost).mean():+.1f}; "
          f"without 2 best {best2:+.1f}; sd {net.std():.0f}")
    print("kills:", {a: bool(b) for a, b in kills.items()}, "->", "KILLED" if any(kills.values()) else "PASSED")
    print("DIAG net by year:", net.groupby(net.index.year).mean().round(1).to_dict())


if __name__ == "__main__":
    main()
