"""I-96 screen: overnight -> intraday reversal sort on FTMO's US share CFDs (knowledge/ideas.md › I-96; rule fixed in
commit 05e69f9 before any data).

Yahoo daily OHLC (split-adjusted, data/cache/yahoo_daily, downloaded only to 2021-09-13), dividends added back on
ex-days. Each day with >= 15 names (>= 20 prior bars): long the 5 lowest overnight returns, short the 5 highest (ties
by name), open -> close. Cost per name and fill = today's FTMO median spread / 2 (open 09:35-09:40, close 15:50-15:55,
research/share_spreads_2026-11-15.csv) + 1 bp slippage. Kills: net <= 0; t < 3.0; halves (2010-2015 / 2016-2021) not
both > 0; doubled costs <= 0; without the 2 best days <= 0.
Run: .venv/Scripts/python.exe research/screens/2026-11-15_i96_overnight_reversal_screen.py
"""
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

NY = ZoneInfo("America/New_York")
ROOT = Path("data/cache/yahoo_daily")
START, END, HALF = pd.Timestamp("2010-01-01"), pd.Timestamp("2021-09-13"), pd.Timestamp("2016-01-01")
N_LEG, MIN_NAMES, MIN_BARS, SLIP = 5, 15, 20, 1.0
SPREAD = pd.read_csv("research/share_spreads_2026-11-15.csv").set_index("symbol")


def load(sym):
    d = json.loads((ROOT / f"{sym}.json").read_text(encoding="utf-8"))["chart"]["result"][0]
    q = d["indicators"]["quote"][0]
    idx = pd.to_datetime(d["timestamp"], unit="s", utc=True).tz_convert(NY).normalize().tz_localize(None)
    f = pd.DataFrame({"open": q["open"], "close": q["close"]}, index=idx).dropna()
    f = f[~f.index.duplicated()]
    div = pd.Series(0.0, index=f.index)
    for ev in (d.get("events", {}).get("dividends") or {}).values():
        day = pd.Timestamp(ev["date"], unit="s", tz="UTC").tz_convert(NY).normalize().tz_localize(None)
        if day in div.index:
            div[day] += ev["amount"]
    f["r_on"] = (f.open + div) / f.close.shift(1) - 1
    f["r_id"] = f.close / f.open - 1
    f["bars"] = np.arange(len(f))
    return f[(f.index >= START) & (f.index <= END) & (f.bars >= MIN_BARS)]


def tstat(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def main():
    syms = [p.stem for p in sorted(ROOT.glob("*.json"))]
    panel = pd.concat({s: load(s) for s in syms}, names=["sym", "day"]).reset_index()
    panel = panel.dropna(subset=["r_on", "r_id"])
    cost_name = (SPREAD.open_bp / 2 + SPREAD.close_bp / 2 + 2 * SLIP).to_dict()
    rows, dec = [], []
    for day, g in panel.groupby("day"):
        if len(g) < MIN_NAMES:
            continue
        g = g.sort_values(["r_on", "sym"], kind="mergesort")
        lo, hi = g.iloc[:N_LEG], g.iloc[-N_LEG:]
        gross = (lo.r_id.mean() - hi.r_id.mean()) * 1e4
        cost = np.mean([cost_name[s] for s in lo.sym]) + np.mean([cost_name[s] for s in hi.sym])
        rows.append((day, gross, cost))
        q = pd.qcut(g.r_on.rank(method="first"), 10, labels=False)
        dec.append((g.r_id * 1e4).groupby(q.to_numpy()).mean())
    r = pd.DataFrame(rows, columns=["day", "gross", "cost"]).set_index("day")
    net = r.gross - r.cost
    h = net[net.index < HALF].mean(), net[net.index >= HALF].mean()
    t = tstat(net)
    kills = {"net <= 0": net.mean() <= 0, "t < 3": t < 3.0, "halves": not (h[0] > 0 and h[1] > 0),
             "doubled costs <= 0": (r.gross - 2 * r.cost).mean() <= 0,
             "without 2 best <= 0": net.drop(net.nlargest(2).index).mean() <= 0}
    print(f"I-96: {len(r)} days, gross {r.gross.mean():+.2f} bp, cost {r.cost.mean():.2f}, net {net.mean():+.2f} bp/day, "
          f"t {t:.2f} (gross t {tstat(r.gross):.2f}); halves {h[0]:+.2f} / {h[1]:+.2f}; doubled costs "
          f"{(r.gross - 2 * r.cost).mean():+.2f}; without 2 best {net.drop(net.nlargest(2).index).mean():+.2f}; "
          f"sd {net.std():.0f} bp")
    print("kills:", {k: bool(v) for k, v in kills.items()}, "->", "KILLED" if any(kills.values()) else "PASSED")
    print("DIAG deciles of r_on (mean intraday bp, low -> high):", pd.concat(dec, axis=1).mean(axis=1).round(1).to_dict())
    print("DIAG gross by year:", r.gross.groupby(r.index.year).mean().round(1).to_dict())


if __name__ == "__main__":
    main()
