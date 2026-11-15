"""I-85 / I-86 screen: noise-band intraday momentum on US500, NAS100, US30, unconditional and on negative-gamma days
(knowledge/ideas.md › I-85; rules fixed in commit 544ac31 before any data).

New York time. open = 09:30 bar open; prev close = previous day's 15:59 bar close; sigma(t) = mean over the previous
14 trading days of |close(t) / open - 1| at checkpoint t (bar closes at 10:00, 10:30, ..., 15:30); upper = max(open,
prev close) x (1 + sigma), lower = min(open, prev close) x (1 - sigma). Flat: close > upper -> long, < lower -> short;
in a position: exit when the checkpoint close is back inside its band side, else at the 15:55 close; re-entry allowed.
Cost per round trip = engine spread at the entry (fill_spread_time) + 2 x slippage, bp of the entry price.
Development only (before 2021-09-14). GEX: previous date's value from data/cache/squeezemetrics/DIX.csv.
Kills per cell: net <= 0; t < 3.0; halves not both > 0; doubled costs <= 0; without the 2 best days <= 0.
`--power`: signal-free line (sd of the 10:00 -> 15:55 return per symbol-day, day counts).
Run: .venv/Scripts/python.exe research/screens/2026-11-15_i85_noise_band_screen.py [--power]
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
SYMBOLS = ("US500", "NAS100", "US30")
START, END = date(2015, 1, 1), date(2021, 9, 13)
CHECK = [f"{h:02d}:{m:02d}" for h in range(9, 16) for m in (29, 59)][1:-1]  # bar opens 09:59 .. 15:29 -> closes 10:00 .. 15:30
cfg = CostConfig()


def day_table(sym):
    d = load_m1(sym, DEFAULT_SOURCES, START, END)
    t = pd.to_datetime(d.open_s, unit="s", utc=True).tz_convert(NY)
    df = pd.DataFrame({"open": d.open, "close": d.close}, index=t)
    df["day"] = df.index.date
    df["hm"] = df.index.strftime("%H:%M")
    keep = df[df.hm.isin(["09:30", "15:54", "15:59", *CHECK])]
    o = keep[keep.hm == "09:30"].set_index("day").open.rename("open")
    c = keep.pivot_table(index="day", columns="hm", values="close", aggfunc="first")
    tab = c.join(o, how="inner")
    tab["prev_close"] = tab["15:59"].shift(1)
    moves = pd.DataFrame({h: (tab[h] / tab.open - 1).abs() for h in CHECK})
    sig = moves.rolling(14, min_periods=14).mean().shift(1)
    return tab, sig


def simulate(sym, tab, sig):
    rows = []
    for day, r in tab.iterrows():
        if np.isnan(r.prev_close) or np.isnan(r["15:54"]) or sig.loc[day].isna().any():
            continue
        pos, entry, entry_t = 0, None, None
        trades = []
        for h in CHECK:
            px = r[h]
            if np.isnan(px):
                continue
            up = max(r.open, r.prev_close) * (1 + sig.loc[day, h])
            lo = min(r.open, r.prev_close) * (1 - sig.loc[day, h])
            if pos == 1 and px < up or pos == -1 and px > lo:
                trades.append((pos, entry, px, entry_t))
                pos = 0
            if pos == 0 and (px > up or px < lo):
                pos, entry = (1 if px > up else -1), px
                entry_t = datetime.combine(day, datetime.strptime(h, "%H:%M").time(), NY).astimezone(UTC)
        if pos:
            trades.append((pos, entry, r["15:54"], entry_t))
        for p, e, x, et in trades:
            cost = (cfg.spread(sym, fill_spread_time(et), e) + 2 * cfg.slippage(sym, e)) / e * 1e4
            rows.append({"day": day, "sym": sym, "dir": p, "gross": p * (x / e - 1) * 1e4, "cost": cost})
    return pd.DataFrame(rows)


def gex_prev():
    g = pd.read_csv("data/cache/squeezemetrics/DIX.csv", parse_dates=["date"]).set_index("date").gex
    return lambda day: g[g.index < pd.Timestamp(day)].iloc[-1] if (g.index < pd.Timestamp(day)).any() else np.nan


def tstat(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def cell(name, trades, days, mult=1.0):
    """Per date: mean over the symbols that traded of each symbol's summed net; eligible days without a trade = 0."""
    net = (trades.gross - mult * trades.cost).groupby([trades.day, trades.sym]).sum()
    return net.groupby(level=0).mean().reindex(days, fill_value=0.0)


def report(name, trades, days):
    if trades.empty:
        print(f"\n{name}: no trades")
        return
    d = cell(name, trades, days)
    d2 = cell(name, trades, days, 2.0)
    half = d.index < date(2018, 5, 1)
    t = tstat(d)
    best = d.drop(d.nlargest(2).index)
    kills = {"net <= 0": d.mean() <= 0, "t < 3": not t >= 3.0, "halves": not (d[half].mean() > 0 and d[~half].mean() > 0),
             "2x cost <= 0": d2.mean() <= 0, "without 2 best <= 0": best.mean() <= 0}
    print(f"\n{name}: {len(d)} days, {len(trades)} trades; net {d.mean():+.2f} bp/day (mean over traded symbols), t {t:.2f}; "
          f"per trade gross {trades.gross.mean():+.2f}, cost {trades.cost.mean():.2f}; halves {d[half].mean():+.2f} / "
          f"{d[~half].mean():+.2f}; 2x cost {d2.mean():+.2f}; without 2 best {best.mean():+.2f}")
    print("  kills:", {a: bool(b) for a, b in kills.items()}, "->", "KILLED" if any(kills.values()) else "PASSED")
    for s, g in trades.groupby("sym"):
        print(f"  DIAG {s}: {len(g)} trades, gross {g.gross.mean():+.2f}, cost {g.cost.mean():.2f}, net {(g.gross - g.cost).mean():+.2f}")
    for side, g in trades.groupby("dir"):
        print(f"  DIAG {'long' if side > 0 else 'short'}: {len(g)} trades, net {(g.gross - g.cost).mean():+.2f}")


def main(argv):
    tabs = {s: day_table(s) for s in SYMBOLS}
    if "--power" in argv:
        for s, (tab, _) in tabs.items():
            r = (tab["15:54"] / tab["09:59"] - 1) * 1e4
            print(f"POWER {s}: {r.notna().sum()} days, sd of 10:00 -> 15:55 return {r.std():.0f} bp")
        return 0
    trades = pd.concat([simulate(s, *tabs[s]) for s in SYMBOLS], ignore_index=True)
    days = sorted(set().union(*[set(t.index) for t, _ in tabs.values()]))
    gp = gex_prev()
    neg = {dd for dd in days if gp(dd) < 0}
    report("I-85 noise-band momentum (all days)", trades, days)
    report("I-86 negative-gamma days only", trades[trades.day.isin(neg)], sorted(neg))
    pos = trades[~trades.day.isin(neg)]
    print(f"\nDIAG positive-GEX days (FB-200 mirror): {len(pos)} trades, net per trade {(pos.gross - pos.cost).mean():+.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
