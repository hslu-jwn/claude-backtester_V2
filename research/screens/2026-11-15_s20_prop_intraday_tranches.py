"""Strategy 20 top-100 at HyroTrader: intraday worst-case marks and weekday tranches (Fable call 3 items 2-3).

Diagnostic on the spent test period 2024-01..2026-10, frozen FB-017 book (CryptoFlowConfig(top_volume=100)).
Calendar-daily book series per weekday anchor k (klines / funding relabelled k days earlier, as FB-022): close mark
and a worst-case intraday mark (every long at its daily low, every short at its daily high, at once; an upper bound
on the intraday drawdown). Costs 10 bp on entry day and 10 bp on exit day (as the prop-fit script), funding by day.
Accounts: "monolithic" = Monday anchor only; "tranches" = 1/7 of the notional on each weekday anchor.
Monte Carlo: 7-day calendar blocks of (daily increment, intraday worst) bootstrapped from the test period, weekly mean
shifted to the fair +92 bp (spec › Execution). HyroTrader Two-Step: +10 % then +5 %, 5 % daily loss vs start-of-day
equity (on the intraday worst when marked so), 10 % static max loss, 40 % best-day rule. 2,000 attempts per cell.
Marks: argv daily_hl (bound, default) | hourly_close (book marked each hour on 1 h closes, data/cache/binance_1h) |
hourly_hl (1 h lows for longs / highs for shorts). Run: .venv/Scripts/python.exe research/screens/2026-11-15_s20_prop_intraday_tranches.py [mark]
"""
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.data import binance_wide
from backtester.tools import crypto_flow as cf

FAIR, START, END = 92.0, date(2024, 1, 1), date(2026, 10, 31)
H1 = Path("data/cache/binance_1h")
MARK = "daily_hl"  # "daily_hl" (bound) | "hourly_close" | "hourly_hl"; set by argv


def hourly(sym):
    files = sorted(H1.glob(f"{sym}-1h-*.zip"))
    if not files:
        return None
    cols = ["open_time", "open", "high", "low", "close", "volume", "close_time", "qv", "n", "tb", "tbq", "ignore"]
    parts = []
    for f in files:
        d = pd.read_csv(f, header=None, names=cols)
        if not str(d.iloc[0, 0]).isdigit():  # newer archives carry a header row
            d = d.iloc[1:]
        parts.append(d[["open_time", "high", "low", "close"]].astype(float))
    d = pd.concat(parts)
    d.index = pd.to_datetime(d.open_time.astype("int64"), unit="ms", utc=True)
    return d[~d.index.duplicated()].sort_index()


def hl(sym):
    parts = [pd.read_csv(r / "klines_1d" / f"{sym}.csv", usecols=["open_time", "high", "low"])
             for r in binance_wide.ROOTS if (r / "klines_1d" / f"{sym}.csv").exists()]
    d = pd.concat(parts)
    d.index = pd.to_datetime(d.open_time, unit="ms", utc=True).dt.normalize()
    return d[~d.index.duplicated()].sort_index()


def anchor_series(k0, f0, shift):
    dt = pd.Timedelta(days=shift)
    kk = {s: d.set_axis(d.index - dt) for s, d in k0.items()}
    ff = {s: (f.set_axis(f.index - dt) if f is not None else None) for s, f in f0.items()}
    _, legs = cf.compute_weeks(kk, ff, START - pd.Timedelta(days=7).to_pytimedelta(), END, cf.LIQUID)
    lg = pd.DataFrame(legs)
    close_inc, worst = {}, {}
    cache, hcache = {}, {}
    for wk, g in lg.groupby("week"):
        days = pd.date_range(wk, periods=7, freq="D")
        cum_c, cum_w = [], []
        for side, sign in (("long", 1), ("short", -1)):
            cc, ww = [], []
            for s in g[g.side == side].symbol:
                d = kk[s]
                held = d[(d.index >= days[0]) & (d.index <= days[-1])]
                entry = held.open.iloc[0]
                if s not in cache:
                    h0 = hl(s)
                    cache[s] = h0.set_axis(h0.index - dt)
                h = cache[s].reindex(days)
                c = held.close.reindex(days).ffill()
                fr = ff.get(s)
                fd = (pd.Series([fr[(fr.index > dd if dd == days[0] else fr.index >= dd) & (fr.index < dd + pd.Timedelta(days=1))].sum()
                                 for dd in days], index=days).cumsum() if fr is not None else pd.Series(0.0, index=days))
                cc.append(sign * (c / entry - 1) - sign * fd)
                if MARK == "daily_hl":
                    bad = (h.low if sign > 0 else h.high).fillna(c)
                    ww.append(sign * (bad / entry - 1) - sign * fd)
                else:
                    if s not in hcache:
                        h1 = hourly(s)
                        hcache[s] = None if h1 is None else h1.set_axis(h1.index - dt)
                    h1 = hcache[s]
                    hrs = pd.date_range(days[0], periods=7 * 24, freq="h")
                    if h1 is None:
                        hv = pd.Series(np.repeat(c.to_numpy(), 24), index=hrs)
                    else:
                        col = "close" if MARK == "hourly_close" else ("low" if sign > 0 else "high")
                        hv = h1[col].reindex(hrs).ffill().fillna(entry)
                    fh = pd.Series(np.repeat(fd.to_numpy(), 24), index=hrs)
                    ww.append(sign * (hv / entry - 1) - sign * fh)
            cum_c.append(pd.concat(cc, axis=1).mean(axis=1))
            cum_w.append(pd.concat(ww, axis=1).mean(axis=1))
        bc = (cum_c[0] + cum_c[1]) * 1e4
        bw = (cum_w[0] + cum_w[1]) * 1e4
        if MARK != "daily_hl":  # worst hourly mark of the whole book within each day
            bw = bw.groupby(bw.index.floor("D")).min().reindex(days).fillna(bc)
        bc.iloc[:] -= 10.0
        bw.iloc[:] -= 10.0
        bc.iloc[-1] -= 10.0
        bw.iloc[-1] -= 10.0
        prev = np.r_[0.0, bc.to_numpy()[:-1]]
        for i, day in enumerate(days + dt):  # back to the calendar
            close_inc[day] = bc.iloc[i] - prev[i]
            worst[day] = min(bw.iloc[i] - prev[i], close_inc[day])
    s = pd.DataFrame({"inc": close_inc, "worst": worst}).sort_index()
    return s[(s.index >= pd.Timestamp(START, tz="UTC")) & (s.index <= pd.Timestamp(END, tz="UTC"))]


def attempt(inc, worst, rng, f, use_worst, targets=(0.10, 0.05), daily_lim=0.05, max_lim=0.10, max_days=3650):
    n_blocks = len(inc) // 7
    days = 0
    for target in targets:
        eq, counted = 1.0, 0.0
        while days < max_days:
            b = rng.integers(n_blocks) * 7
            for i in range(b, b + 7):
                days += 1
                low = eq + f * (worst[i] if use_worst else inc[i]) / 1e4
                if eq - low >= daily_lim or 1.0 - low >= max_lim:
                    return False, days
                gain = f * inc[i] / 1e4
                counted += min(gain, 0.4 * target)
                eq += gain
            if counted >= target and eq >= 1.0 + target:
                break
        else:
            return False, days
    return True, days


def main():
    global MARK
    MARK = sys.argv[1] if len(sys.argv) > 1 else "daily_hl"
    print("marks:", MARK)
    k0, f0 = cf.load()
    series = {sh: anchor_series(k0, f0, sh) for sh in range(7)}
    idx = series[0].index
    mono = series[0]
    tr = sum(series[sh].reindex(idx).fillna(0.0) for sh in range(7)) / 7
    rng = np.random.default_rng(5)
    print("| account | weekly mean (raw) | weekly sd | worst day (close / intraday) | f per side | pass, close marks | "
          "pass, intraday worst | days (median, intraday) |")
    print("|---|---|---|---|---|---|---|---|")
    for name, s in (("monolithic (Monday)", mono), ("7 weekday tranches", tr)):
        wk = s.inc.groupby(np.arange(len(s)) // 7).sum()
        adj = (wk.mean() - FAIR) / 7
        inc, worst = (s.inc - adj).to_numpy(), (s.worst - adj).to_numpy()
        for f in (0.25, 0.5):
            a = [attempt(inc, worst, rng, f, False) for _ in range(2000)]
            b = [attempt(inc, worst, rng, f, True) for _ in range(2000)]
            ok = [d for p, d in b if p]
            print(f"| {name} | {wk.mean():+.0f} | {wk.std():.0f} | {s.inc.min():+.0f} / {s.worst.min():+.0f} | {f:.0%} | "
                  f"{100 * np.mean([p for p, _ in a]):.0f} % | {100 * len(ok) / 2000:.0f} % | {np.median(ok) if ok else float('nan'):.0f} |")


if __name__ == "__main__":
    main()
