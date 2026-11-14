"""I-81 screen: new-listing drift on Binance USDT perps (knowledge/ideas.md › I-81).

Rule and kills pre-registered in the card (commit 6886954) before any data was read. Crypto split: development only
(no bar after 2023-12-31). Events: perps whose first daily bar is in 2020-03-01 .. 2023-11-30. Short at the close of
bar 2, cover at the close of bar 30 (or the last close); long BTCUSDT over the same two closes. Net = -coin return +
BTC return + coin funding received - BTC funding paid (settlements strictly between the closes) - 20 bp.
t over monthly cluster means (month of entry). Kills: net <= 0; t < 3.0; halves not both > 0; 40 bp <= 0; without
the 2 best months <= 0.
`--power`: signal-free line (event / month counts; sd of 28-day BTC-hedged returns of established perps at random
dates, scaled to month means).
Run: .venv/Scripts/python.exe research/screens/2026-11-15_i81_listing_drift_screen.py [--power]
"""
import sys

import numpy as np
import pandas as pd

from backtester.data import binance_wide

ROOT = binance_wide.ROOTS[0]
END = pd.Timestamp("2023-12-31", tz="UTC")
FIRST, LAST = pd.Timestamp("2020-03-01", tz="UTC"), pd.Timestamp("2023-11-30", tz="UTC")
COST_BP, ENTRY_BAR, EXIT_BAR = 20.0, 1, 29  # 0-based: close of bar 2, close of bar 30


def load():
    k, f = {}, {}
    for s in binance_wide.symbols((ROOT,)):
        d = binance_wide.read_klines(s, (ROOT,))
        d = d[d.index <= END]
        if len(d):
            k[s] = d
            f[s] = binance_wide.read_funding(s, (ROOT,))
    return k, f


def funding_between(series, t0, t1):
    """Settlements strictly between the close of the entry day and the close of the exit day."""
    # a daily bar closes just before the next 00:00: the 00:00 print after the entry close counts, the one after
    # the exit close does not
    a, b = t0 + pd.Timedelta(days=1), t1 + pd.Timedelta(days=1)
    return series[(series.index >= a) & (series.index < b)].sum() * 1e4


def hedged(k, f, sym, i0, i1):
    d, btc = k[sym], k["BTCUSDT"]
    t0, t1 = d.index[i0], d.index[i1]
    if t0 not in btc.index or t1 not in btc.index:
        return None
    coin = (d.close.iloc[i1] / d.close.iloc[i0] - 1) * 1e4
    b = (btc.close.loc[t1] / btc.close.loc[t0] - 1) * 1e4
    fund = funding_between(f[sym], t0, t1) - funding_between(f["BTCUSDT"], t0, t1)
    return {"sym": sym, "entry": t0, "coin": coin, "btc": b, "fund": fund, "early_stop": i1 < EXIT_BAR,
            "gross": -coin + b + fund}


def events(k, f):
    out = []
    for s, d in k.items():
        if s == "BTCUSDT" or not (FIRST <= d.index[0] <= LAST) or len(d) <= ENTRY_BAR + 1:
            continue
        r = hedged(k, f, s, ENTRY_BAR, min(EXIT_BAR, len(d) - 1))
        if r:
            out.append(r)
    return pd.DataFrame(out)


def month_means(e, cost):
    e = e.assign(net=e.gross - cost, month=e.entry.dt.strftime("%Y-%m"))
    return e.groupby("month").net.mean()


def tstat(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def main(argv):
    k, f = load()
    e = events(k, f)
    m = month_means(e, COST_BP)
    print(f"events {len(e)}, months {len(m)}, events per year {e.entry.dt.year.value_counts().sort_index().to_dict()}")
    if "--power" in argv:
        rng = np.random.default_rng(1)
        est = [s for s, d in k.items() if s != "BTCUSDT" and len(d) > 220]
        r = []
        for _ in range(3000):
            s = est[rng.integers(len(est))]
            d = k[s]
            i0 = int(rng.integers(180, len(d) - 30))
            x = hedged(k, f, s, i0, i0 + 28)
            if x:
                r.append(x["gross"])
        sd = float(np.std(r, ddof=1))
        per_month = len(e) / len(m)
        sd_m = sd / np.sqrt(per_month)  # ignores within-month correlation (optimistic)
        print(f"POWER: 28-day hedged sd {sd:.0f} bp (established perps, random dates); {per_month:.1f} events a "
              f"month -> month-mean sd ~{sd_m:.0f} bp, se {sd_m / np.sqrt(len(m)):.0f} bp; t 3 needs "
              f"~{3 * sd_m / np.sqrt(len(m)):.0f} bp net per event (optimistic: ignores within-month correlation)")
        return 0
    t = tstat(m)
    y = pd.Series(m.index.str[:4].astype(int), index=m.index)
    h1, h2 = m[y <= 2021].mean(), m[y >= 2022].mean()
    m40 = month_means(e, 2 * COST_BP)
    best = m.drop(m.nlargest(2).index)
    print(f"PRIMARY: net {m.mean():+.1f} bp (mean of month means), t {t:.2f}; event mean {(e.gross - COST_BP).mean():+.1f}, "
          f"median {(e.gross - COST_BP).median():+.1f}; coin {e.coin.mean():+.1f}, BTC {e.btc.mean():+.1f}, "
          f"funding {e.fund.mean():+.1f}; stopped early {100 * e.early_stop.mean():.0f} %")
    print(f"  halves {h1:+.1f} / {h2:+.1f}; at 40 bp {m40.mean():+.1f}; without 2 best months {best.mean():+.1f}")
    kills = {"net <= 0": m.mean() <= 0, "t < 3": not t >= 3.0, "halves": not (h1 > 0 and h2 > 0),
             "40 bp <= 0": m40.mean() <= 0, "without 2 best <= 0": best.mean() <= 0}
    print("  kills:", {a: bool(b) for a, b in kills.items()}, "->", "KILLED" if any(kills.values()) else "PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
