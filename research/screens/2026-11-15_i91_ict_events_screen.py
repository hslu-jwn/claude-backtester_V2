"""I-91 / I-92 / I-93 screen: ICT event rules with timed exits, pooled over 8 cheap FTMO symbols (knowledge/ideas.md ›
I-91; rules fixed in commit 4fba88c before any data).

New York time; trading day = 17:00 -> 17:00 NY (labelled by its end date); development only (before 2021-09-14).
ATR = mean (high - low) of the previous 14 trading days. "M5 close" = close of a bar whose open minute % 5 == 4.
I-91 PDH / PDL raid: 03:00-15:55, trade-through >= 0.1 ATR, M5 close back inside within 30 minutes -> fade to 15:55.
I-92 power of three: >= 0.3 ATR away from the 00:00 open before 08:30, M5 close back across it 08:30-10:00 -> trade
toward the reclaim to 15:55; first per day. I-93 CRT: H4 blocks 01-05, 05-09, 09-13, 13-17 NY; candle n (05-09 or
09-13) trades beyond candle n-1's low (high) and closes back inside -> long (short) at n's close, exit 16:55 (two
candles later is past 16:55 for both). Assumption fixed before data: a candle that trades beyond both extremes of
n-1 is skipped. Cost = engine spread at the entry time + 2 x slippage, bp. No hold over 17:00 NY.
Kills each: net <= 0; t < 3.0; halves not both > 0; doubled costs <= 0; without the 2 best days <= 0.
`--power`: signal-free line (event counts, sd of event-to-exit returns).
Run: .venv/Scripts/python.exe research/screens/2026-11-15_i91_ict_events_screen.py [--power]
"""
import sys
from datetime import UTC, date, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.costs import CostConfig, fill_spread_time
from backtester.tools.entry_screen import load_m1

NY = ZoneInfo("America/New_York")
SYMBOLS = ("US30", "GER40", "NAS100", "US500", "UK100", "EURUSD", "USDJPY", "XAUUSD")
START, END = date(2015, 1, 1), date(2021, 9, 13)
cfg = CostConfig()


def frame(sym):
    d = load_m1(sym, DEFAULT_SOURCES, START, END)
    t = pd.to_datetime(d.open_s, unit="s", utc=True).tz_convert(NY)
    df = pd.DataFrame({"open": d.open, "high": d.high, "low": d.low, "close": d.close}, index=t)
    df["td"] = (df.index + pd.Timedelta(hours=7)).date  # 17:00 NY starts the next trading day
    df["mins"] = df.index.hour * 60 + df.index.minute
    rng = df.groupby("td").agg(h=("high", "max"), l=("low", "min"))
    rng["atr"] = (rng.h - rng.l).rolling(14, min_periods=14).mean().shift(1)
    rng["pdh"], rng["pdl"] = rng.h.shift(1), rng.l.shift(1)
    return df, rng


def cost_bp(sym, ts, price):
    return (cfg.spread(sym, fill_spread_time(ts.astimezone(UTC).to_pydatetime()), price) + 2 * cfg.slippage(sym, price)) / price * 1e4


def at(day_df, minute):
    """Close of the bar opening at `minute` (minutes after midnight NY), or NaN."""
    r = day_df[day_df.mins == minute]
    return (r.close.iloc[0], r.index[0]) if len(r) else (np.nan, None)


def i91(sym, df, rng, control=False):
    rows = []
    for td, g in df.groupby("td"):
        if td not in rng.index or np.isnan(rng.loc[td, "atr"]) or np.isnan(rng.loc[td, "pdh"]):
            continue
        a, pdh, pdl = rng.loc[td, ["atr", "pdh", "pdl"]]
        w = g[(g.mins >= 180) & (g.mins <= 15 * 60 + 54)]
        ex, _ = at(g, 15 * 60 + 54)
        if np.isnan(ex) or w.empty:
            continue
        for side, lvl in (("short", pdh), ("long", pdl)):
            brk = w[w.high >= lvl + 0.1 * a] if side == "short" else w[w.low <= lvl - 0.1 * a]
            if brk.empty:
                continue
            tb = brk.index[0]
            win = w[(w.index > tb) & (w.index <= tb + pd.Timedelta(minutes=30)) & (w.mins % 5 == 4)]
            back = win[win.close < lvl] if side == "short" else win[win.close > lvl]
            if control:
                if not back.empty:
                    continue
                late = w[(w.index >= tb + pd.Timedelta(minutes=30)) & (w.mins % 5 == 4)]
                if late.empty:
                    continue
                e, et = late.close.iloc[0], late.index[0]
            else:
                if back.empty:
                    continue
                e, et = back.close.iloc[0], back.index[0]
            if et.hour * 60 + et.minute >= 15 * 60 + 54:
                continue
            dr = -1 if side == "short" else 1
            rows.append({"day": td, "sym": sym, "gross": dr * (ex / e - 1) * 1e4, "cost": cost_bp(sym, et, e)})
    return rows


def i92(sym, df, rng, control=False):
    rows = []
    for td, g in df.groupby("td"):
        if td not in rng.index or np.isnan(rng.loc[td, "atr"]):
            continue
        a = rng.loc[td, "atr"]
        o = g[g.mins == 0]
        ex, _ = at(g, 15 * 60 + 54)
        if o.empty or np.isnan(ex):
            continue
        op = o.open.iloc[0]
        pre = g[(g.mins >= 0) & (g.mins < 8 * 60 + 30)]
        win = g[(g.mins >= 8 * 60 + 30) & (g.mins < 10 * 60) & (g.mins % 5 == 4)]
        cands = []
        if pre.low.min() <= op - 0.3 * a:
            hit = win[win.close > op]
            cands.append((1, hit))
        if pre.high.max() >= op + 0.3 * a:
            hit = win[win.close < op]
            cands.append((-1, hit))
        if control:
            for dr, hit in cands:
                if hit.empty:
                    e, et = at(g, 9 * 60 + 59)
                    if not np.isnan(e):
                        rows.append({"day": td, "sym": sym, "gross": dr * (ex / e - 1) * 1e4, "cost": cost_bp(sym, et, e)})
            continue
        hits = [(hit.index[0], dr, hit.close.iloc[0]) for dr, hit in cands if not hit.empty]
        if hits:
            et, dr, e = min(hits)
            rows.append({"day": td, "sym": sym, "gross": dr * (ex / e - 1) * 1e4, "cost": cost_bp(sym, et, e)})
    return rows


def i93(sym, df, rng, control=False):
    rows = []
    blocks = [(60, 300), (300, 540), (540, 780), (780, 1020)]
    for td, g in df.groupby("td"):
        ex, _ = at(g, 16 * 60 + 54)
        if np.isnan(ex):
            continue
        cs = []
        for lo, hi in blocks:
            b = g[(g.mins >= lo) & (g.mins < hi)]
            cs.append(None if b.empty else (b.high.max(), b.low.min(), b.close.iloc[-1], b.index[-1]))
        for n in (1, 2):  # candles 05-09 and 09-13; n-1 = the block before
            if cs[n] is None or cs[n - 1] is None:
                continue
            h, low, c, ct = cs[n]
            ph, pl = cs[n - 1][0], cs[n - 1][1]
            down, up = low < pl, h > ph
            if control:
                if down or up:
                    continue
                dr = 1 if c > (ph + pl) / 2 else -1  # no sweep: side of the prior candle's midpoint
            else:
                if down == up:
                    continue  # no sweep, or both extremes taken (skipped)
                if down and pl < c < ph:
                    dr = 1
                elif up and pl < c < ph:
                    dr = -1
                else:
                    continue
            rows.append({"day": td, "sym": sym, "gross": dr * (ex / c - 1) * 1e4, "cost": cost_bp(sym, ct + timedelta(minutes=1), c)})
    return rows


def tstat(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def report(name, rows, gate=True):
    t = pd.DataFrame(rows)
    if t.empty:
        print(f"{name}: no trades")
        return
    net_d = (t.gross - t.cost).groupby(t.day).mean()
    net2 = (t.gross - 2 * t.cost).groupby(t.day).mean()
    half = net_d.index < date(2018, 5, 1)
    tt = tstat(net_d)
    print(f"{name}: {len(t)} trades / {len(net_d)} days; net {net_d.mean():+.2f} bp, t {tt:.2f}; gross {t.gross.mean():+.2f}, "
          f"cost {t.cost.mean():.2f}; halves {net_d[half].mean():+.2f} / {net_d[~half].mean():+.2f}; 2x cost {net2.mean():+.2f}; "
          f"without 2 best {net_d.drop(net_d.nlargest(2).index).mean():+.2f}")
    if gate:
        kills = {"net <= 0": net_d.mean() <= 0, "t < 3": not tt >= 3.0,
                 "halves": not (net_d[half].mean() > 0 and net_d[~half].mean() > 0), "2x cost <= 0": net2.mean() <= 0,
                 "without 2 best <= 0": net_d.drop(net_d.nlargest(2).index).mean() <= 0}
        print("  kills:", {a: bool(b) for a, b in kills.items()}, "->", "KILLED" if any(kills.values()) else "PASSED")
        per = t.assign(net=t.gross - t.cost).groupby("sym").net.agg(["count", "mean"]).round(2)
        print("  per symbol:", per.to_dict("index"))


def main(argv):
    data = {s: frame(s) for s in SYMBOLS}
    rules = (("I-91 PDH / PDL raid", i91), ("I-92 power of three", i92), ("I-93 candle range theory H4", i93))
    if "--power" in argv:
        for name, fn in rules:
            rows = [r for s in SYMBOLS for r in fn(s, *data[s])]
            t = pd.DataFrame(rows)
            days = t.day.nunique()
            sd = t.gross.groupby(t.day).mean().std()
            print(f"POWER {name}: {len(t)} events on {days} days; sd of the per-day mean event return {sd:.0f} bp -> t 3 needs "
                  f"~{3 * sd / np.sqrt(days):.1f} bp net")
        return 0
    for name, fn in rules:
        report(name, [r for s in SYMBOLS for r in fn(s, *data[s])])
        report(f"  control for {name}", [r for s in SYMBOLS for r in fn(s, *data[s], control=True)], gate=False)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
