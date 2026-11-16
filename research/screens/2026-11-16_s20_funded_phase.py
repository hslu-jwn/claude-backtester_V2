"""Strategy 20 funded phase at HyroTrader (Fable backlog FB-265; 2026-11-16; diagnostic on the spent test period).

After the challenge: no target; the account is breached (and ends) at a 5 % daily loss vs start-of-day equity or at
equity <= 90 % of the initial balance (static). Every 4 weeks profits above the initial balance are paid out (equity
reset to 1.0). Policy = fixed notional per side f on the tranched top-100 book (7 weekday anchors, as the decision
package). Series from research/screens/2026-11-15_s20_prop_intraday_tranches.py (cached in data/cache, ignored),
weekly mean shifted to the fair +92 bp, 7-day blocks bootstrapped; 52 weeks; 4,000 accounts per cell.
Reports P(breach within a year) and the payout (percent of the initial balance, before the firm's split).
Marks: hourly_close (closest to Bybit's mark price) and hourly_hl (wick bound).
Run: .venv/Scripts/python.exe research/screens/2026-11-16_s20_funded_phase.py
"""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("it", "research/screens/2026-11-15_s20_prop_intraday_tranches.py")
it = importlib.util.module_from_spec(spec)
spec.loader.exec_module(it)
CACHE = Path("data/cache/s20_prop")
FAIR, WEEKS, N = 92.0, 52, 4000


def tranche_series(mark):
    p = CACHE / f"tranches_{mark}.csv"
    if p.exists():
        return pd.read_csv(p, index_col=0)
    it.MARK = mark
    k0, f0 = it.cf.load()
    series = {sh: it.anchor_series(k0, f0, sh) for sh in range(7)}
    idx = series[0].index
    tr = sum(series[sh].reindex(idx).fillna(0.0) for sh in range(7)) / 7
    CACHE.mkdir(parents=True, exist_ok=True)
    tr.to_csv(p)
    return tr


def year(inc, worst, rng, f, daily_lim=0.05, max_lim=0.10):
    eq, paid = 1.0, 0.0
    n_blocks = len(inc) // 7
    for w in range(WEEKS):
        b = rng.integers(n_blocks) * 7
        for i in range(b, b + 7):
            low = eq + f * worst[i] / 1e4
            if eq - low >= daily_lim or 1.0 - low >= max_lim:
                return paid, True
            eq += f * inc[i] / 1e4
        if (w + 1) % 4 == 0 and eq > 1.0:
            paid += eq - 1.0
            eq = 1.0
    return paid + max(eq - 1.0, 0.0), False


def main():
    rng = np.random.default_rng(11)
    print("| marks | notional per side | P(breach in 1 year) | mean payout % a year | median payout % |")
    print("|---|---|---|---|---|")
    for mark in ("hourly_close", "hourly_hl"):
        s = tranche_series(mark)
        wk = s.inc.groupby(np.arange(len(s)) // 7).sum()
        adj = (wk.mean() - FAIR) / 7
        inc, worst = (s.inc - adj).to_numpy(), (s.worst - adj).to_numpy()
        for f in (0.10, 0.15, 0.20, 0.25, 0.35):
            res = [year(inc, worst, rng, f) for _ in range(N)]
            pay = np.array([p for p, _ in res]) * 100
            print(f"| {mark} | {f:.0%} | {100 * np.mean([b for _, b in res]):.0f} % | {pay.mean():.1f} | {np.median(pay):.1f} |")


if __name__ == "__main__":
    main()
