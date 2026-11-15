"""FB-273 maker-fill model for Strategy 20's Monday rebalance (knowledge/ideas.md › FB-273; rule fixed before data).

Binance daily aggTrades (Sunday + Monday files) in data/cache/binance_aggtrades, 13 Mondays 2023-10-02..2023-12-25,
XEMUSDT / BELUSDT / CRVUSDT / SOLUSDT, one buy and one sell order each. P0 = last trade before Monday 00:00 UTC.
Taker now = first matching-aggressor trade after 00:00 + 5 bp. Maker first = limit at P0, filled when a later trade
prints strictly through it within 60 min (+ 2 bp), else taker at the first matching trade after 01:00 (+ 5 bp).
Cost = side x (fill - P0) / P0 x 1e4 + fee; saving = taker - maker. Adopt maker-first if mean saving >= 1 bp a fill
with t >= 2 clustered by Monday.
Run: .venv/Scripts/python.exe research/screens/2026-11-15_fb273_maker_fill.py
"""
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("data/cache/binance_aggtrades")
SYMS = ("XEMUSDT", "BELUSDT", "CRVUSDT", "SOLUSDT")
TAKER, MAKER, WAIT_MS = 5.0, 2.0, 60 * 60 * 1000


def trades(sym, day):
    d = pd.read_csv(ROOT / f"{sym}-aggTrades-{day}.zip", usecols=["price", "transact_time", "is_buyer_maker"])
    return d.sort_values("transact_time", kind="mergesort")


def first_taker(t, side, after):
    # buy order = buyer is the aggressor = is_buyer_maker False
    m = t[(t.transact_time >= after) & (t.is_buyer_maker == (side < 0))]
    return float(m.price.iloc[0]) if len(m) else np.nan


def order(sun, mon, side, t0):
    before = sun[sun.transact_time < t0]
    p0 = float(before.price.iloc[-1]) if len(before) else float(mon.price.iloc[0])
    taker = side * (first_taker(mon, side, t0) - p0) / p0 * 1e4 + TAKER
    win = mon[(mon.transact_time >= t0) & (mon.transact_time < t0 + WAIT_MS)]
    through = (win.price < p0) if side > 0 else (win.price > p0)
    if through.any():
        maker, filled = MAKER, True
    else:
        maker, filled = side * (first_taker(mon, side, t0 + WAIT_MS) - p0) / p0 * 1e4 + TAKER, False
    return taker, maker, filled


def main():
    rows = []
    m = date(2023, 10, 2)
    while m <= date(2023, 12, 25):
        t0 = int(pd.Timestamp(m, tz="UTC").timestamp() * 1000)
        for s in SYMS:
            sun, mon = trades(s, m - timedelta(days=1)), trades(s, m)
            for side in (1, -1):
                tk, mk, f = order(sun, mon, side, t0)
                rows.append({"monday": m, "sym": s, "side": side, "taker": tk, "maker": mk, "filled": f})
        m += timedelta(days=7)
    r = pd.DataFrame(rows)
    r["saving"] = r.taker - r.maker
    by_monday = r.groupby("monday").saving.mean()
    t = by_monday.mean() / by_monday.std(ddof=1) * np.sqrt(len(by_monday))
    print(r.groupby("sym")[["taker", "maker", "saving", "filled"]].mean().round(2))
    print(f"all {len(r)} orders: taker {r.taker.mean():.2f} bp, maker-first {r.maker.mean():.2f} bp, saving "
          f"{r.saving.mean():+.2f} bp a fill (t {t:.2f} over {len(by_monday)} Mondays), fill rate {100 * r.filled.mean():.0f} %;"
          f" unfilled orders cost {r[~r.filled].maker.mean():.1f} bp")
    print("decision:", "ADOPT maker-first" if r.saving.mean() >= 1 and t >= 2 else "keep taker")


if __name__ == "__main__":
    main()
