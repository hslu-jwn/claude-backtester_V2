"""I-72 screen: price drift around Binance funding settlements (knowledge/ideas.md › I-72).

Rule and kills pre-registered in the card (commit 1559dbf) before this script ran.
Signal: rate settled at t - 8 h; s = +1 if > 0.0001, -1 if < 0, skip otherwise.
PRE: -s from close of the bar ending t-60 to close of the bar ending t-1.
POST: +s from close of the bar ending t+1 to close of the bar ending t+60.
Net = gross bp - 10 bp (taker 0.05 % per side, engine/costs.py). Development 2020-01-01 .. 2021-09-13.
Kills (each cell): net <= 0; t < 3.0; BTC vs ETH opposite gross signs; 2020 vs 2021 opposite gross signs.
t is taken on the per-settlement mean of the two symbols (BTC and ETH events at one time are not independent).
Diagnostic: the same windows at 04 / 12 / 20 UTC with the same signal; net at 12 bp.
Run: .venv/Scripts/python.exe research/screens/2026-11-13_i72_funding_settlement_screen.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path("data/cache")
START, END = pd.Timestamp("2020-01-01", tz="UTC"), pd.Timestamp("2021-09-14", tz="UTC")
COST = 10.0
M = pd.Timedelta(minutes=1)


def closes(sym):
    files = sorted(f for f in (CACHE / "binance" / sym).glob("*/*.parquet") if "2020-01-01" <= f.stem < "2021-09-15")
    d = pd.concat(pd.read_parquet(f, columns=["ts", "bid_close"]) for f in files)
    return d.set_index("ts")["bid_close"]  # index = bar open time


def funding(sym):
    f = pd.read_csv(CACHE / "binance_funding" / f"{sym}.csv", parse_dates=["calc_time"])
    return f.set_index(f.calc_time.dt.tz_localize("UTC").dt.floor("min"))["last_funding_rate"]


def events(sym, shift_h):
    """Rows per settlement t (+ shift_h for the diagnostic): signal and PRE / POST gross bp."""
    px, fr = closes(sym), funding(sym)
    rows = []
    for t, prev in zip(fr.index[1:], fr.values[:-1]):
        s = 1 if prev > 0.0001 else -1 if prev < 0 else 0
        t = t + pd.Timedelta(hours=shift_h)
        if not s or not START <= t < END:
            continue
        # close of the bar ending at x = bar opening at x - 1 min
        get = lambda x: px.get(x - M)  # noqa: E731
        a, b, c, d = get(t - 60 * M), get(t - M), get(t + M), get(t + 60 * M)
        pre = -s * (b / a - 1) * 1e4 if a and b else np.nan
        post = s * (d / c - 1) * 1e4 if c and d else np.nan
        rows.append((t, sym, s, pre, post))
    return pd.DataFrame(rows, columns=["t", "sym", "s", "PRE", "POST"])


def report(df, label):
    print(f"\n== {label}: {len(df)} symbol-events, s=+1 share {np.mean(df.s > 0):.2f}")
    for cell in ("PRE", "POST"):
        g = df.dropna(subset=[cell])
        per_t = g.groupby("t")[cell].mean() - COST
        t_stat = per_t.mean() / per_t.std(ddof=1) * np.sqrt(len(per_t))
        naive = (g[cell] - COST).mean() / (g[cell] - COST).std(ddof=1) * np.sqrt(len(g))
        by_sym = g.groupby("sym")[cell].mean().round(2).to_dict()
        by_year = g.groupby(g.t.dt.year)[cell].mean().round(2).to_dict()
        print(f"{cell}: n {len(g)} ({len(per_t)} times)  gross {g[cell].mean():+.2f} bp  net {g[cell].mean() - COST:+.2f}"
              f"  net@12 {g[cell].mean() - 12:+.2f}  t(clustered) {t_stat:+.2f}  t(naive) {naive:+.2f}"
              f"  sd {g[cell].std():.0f}  win {np.mean(g[cell] > COST):.2f}")
        print(f"      gross by symbol {by_sym}  by year {by_year}  by s {g.groupby('s')[cell].mean().round(2).to_dict()}")


if __name__ == "__main__":
    report(pd.concat(events(s, 0) for s in ("BTCUSDT", "ETHUSDT")), "settlements 00/08/16 UTC")
    report(pd.concat(events(s, 4) for s in ("BTCUSDT", "ETHUSDT")), "diagnostic 04/12/20 UTC (no settlement)")
