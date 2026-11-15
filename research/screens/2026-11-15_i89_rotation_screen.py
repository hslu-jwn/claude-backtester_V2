"""I-89 / I-90 screen: intraday index rotation NAS100 vs US500 (knowledge/ideas.md › I-89; rules fixed in commit
c1187ea before any data).

New York time, development only (before 2021-09-14). Spread s = r(NAS100) - beta x r(US500), beta = OLS slope of the
daily 09:30 -> 15:55 returns over the previous 60 days (>= 40). I-89: m = spread 09:30 open -> 10:30 close; hold
sign(m) x spread 10:30 -> 15:55 every day. I-90: m = spread 09:30 -> 11:00; |z| > 2 vs the previous 60 days' m (>= 40):
hold -sign(m) x spread 11:00 -> 15:55. Cost = NAS100 round trip + beta x US500 round trip at the entry time.
Kills per cell: net <= 0; t < 3.0; halves not both > 0; doubled costs <= 0; without the 2 best days <= 0.
`--power`: signal-free line. Run: .venv/Scripts/python.exe research/screens/2026-11-15_i89_rotation_screen.py [--power]
"""
import sys
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.costs import CostConfig, fill_spread_time
from backtester.tools.entry_screen import load_m1

NY = ZoneInfo("America/New_York")
START, END = date(2015, 1, 1), date(2021, 9, 13)
cfg = CostConfig()


def table(sym):
    d = load_m1(sym, DEFAULT_SOURCES, START, END)
    t = pd.to_datetime(d.open_s, unit="s", utc=True).tz_convert(NY)
    df = pd.DataFrame({"open": d.open, "close": d.close, "day": t.date, "hm": t.strftime("%H:%M")})
    o = df[df.hm == "09:30"].set_index("day").open.rename("o0930")
    c = df[df.hm.isin(["10:29", "10:59", "15:54"])].pivot_table(index="day", columns="hm", values="close", aggfunc="first")
    return c.join(o, how="inner").rename(columns={"10:29": "c1030", "10:59": "c1100", "15:54": "c1555"})


def cost_bp(sym, day, hm, price):
    et = datetime.combine(day, datetime.strptime(hm, "%H:%M").time(), NY).astimezone(UTC)
    return (cfg.spread(sym, fill_spread_time(et), price) + 2 * cfg.slippage(sym, price)) / price * 1e4


def build(a, b):
    ta, tb = table(a), table(b)
    j = ta.join(tb, how="inner", lsuffix="_a", rsuffix="_b").dropna()
    ra, rb = j.c1555_a / j.o0930_a - 1, j.c1555_b / j.o0930_b - 1
    cov = ra.rolling(60, min_periods=40).cov(rb).shift(1)
    var = rb.rolling(60, min_periods=40).var().shift(1)
    j["beta"] = cov / var
    j["m1"] = (j.c1030_a / j.o0930_a - 1) - j.beta * (j.c1030_b / j.o0930_b - 1)
    j["h1"] = (j.c1555_a / j.c1030_a - 1) - j.beta * (j.c1555_b / j.c1030_b - 1)
    j["m2"] = (j.c1100_a / j.o0930_a - 1) - j.beta * (j.c1100_b / j.o0930_b - 1)
    j["h2"] = (j.c1555_a / j.c1100_a - 1) - j.beta * (j.c1555_b / j.c1100_b - 1)
    j["z2"] = j.m2 / j.m2.rolling(60, min_periods=40).std().shift(1)
    return j.dropna(subset=["beta"]), (a, b)


def cells(j, pair):
    a, b = pair
    out = {}
    c1 = np.array([cost_bp(a, d, "10:30", r.c1030_a) + abs(r.beta) * cost_bp(b, d, "10:30", r.c1030_b) for d, r in j.iterrows()])
    out["I-89 follow morning (10:30 -> 15:55)"] = pd.DataFrame(
        {"gross": np.sign(j.m1) * j.h1 * 1e4, "cost": c1, "long_a": j.m1 > 0}, index=j.index)
    k = j[j.z2.abs() > 2]
    c2 = np.array([cost_bp(a, d, "11:00", r.c1100_a) + abs(r.beta) * cost_bp(b, d, "11:00", r.c1100_b) for d, r in k.iterrows()])
    out["I-90 fade extreme morning (11:00 -> 15:55)"] = pd.DataFrame(
        {"gross": -np.sign(k.m2) * k.h2 * 1e4, "cost": c2, "long_a": k.m2 < 0}, index=k.index)
    return out


def tstat(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def report(name, t, gate=True):
    net, net2 = t.gross - t.cost, t.gross - 2 * t.cost
    half = np.array([d < date(2018, 5, 1) for d in t.index])
    tt = tstat(net)
    print(f"{name}: {len(t)} days; net {net.mean():+.2f} bp, t {tt:.2f}; gross {t.gross.mean():+.2f}, cost {t.cost.mean():.2f}; "
          f"halves {net[half].mean():+.2f} / {net[~half].mean():+.2f}; 2x cost {net2.mean():+.2f}; without 2 best "
          f"{net.drop(net.nlargest(2).index).mean():+.2f}; long-A days {net[t.long_a].mean():+.2f}, short-A {net[~t.long_a].mean():+.2f}")
    if gate:
        kills = {"net <= 0": net.mean() <= 0, "t < 3": not tt >= 3.0,
                 "halves": not (net[half].mean() > 0 and net[~half].mean() > 0), "2x cost <= 0": net2.mean() <= 0,
                 "without 2 best <= 0": net.drop(net.nlargest(2).index).mean() <= 0}
        print("  kills:", {a: bool(b) for a, b in kills.items()}, "->", "KILLED" if any(kills.values()) else "PASSED")


def main(argv):
    j, pair = build("NAS100", "US500")
    if "--power" in argv:
        print(f"POWER: {len(j)} days; sd of the 10:30 -> 15:55 spread {j.h1.std() * 1e4:.0f} bp -> t 3 needs "
              f"~{3 * j.h1.std() * 1e4 / np.sqrt(len(j)):.1f} bp; days with |z| > 2: {(j.z2.abs() > 2).sum()}, sd of the "
              f"11:00 -> 15:55 spread {j.h2.std() * 1e4:.0f} bp -> t 3 needs "
              f"~{3 * j.h2.std() * 1e4 / np.sqrt(max((j.z2.abs() > 2).sum(), 1)):.1f} bp")
        return 0
    for name, t in cells(j, pair).items():
        report(name, t)
    print("\nDiagnostic (no gate): NAS100 vs US30 (US30 from 2019-02)")
    j3, pair3 = build("NAS100", "US30")
    for name, t in cells(j3, pair3).items():
        report("  " + name, t, gate=False)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
