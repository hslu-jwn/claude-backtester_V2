"""I-76 screen: liquidation-cascade reversal on 37 Binance perps (knowledge/ideas.md › I-76).

Rule and kills pre-registered in the card (commit 1e5953e) before any data was read. Per symbol, at the close of
M1 bar t: r5 = log(close_t / close_t-5); sd5 = sd of the M1 log returns of the 1,440 bars before the window
(>= 1,000 present) x sqrt(5); v5 = volume of bars t-4..t; vmed = median M1 volume of those 1,440 bars.
Bearish event: r5 <= -4 sd5, sell share >= 0.65, v5 >= 25 vmed -> long; bullish mirrored -> short. Enter at
the close of bar t+1, exit at the close of bar t+61; no new event on a symbol until its exit. Net = price return
- funding paid at settlements inside the hold - 10 bp. Clusters: entries within 60 min of a cluster's first.
Kills: net <= 0; t < 3.0; a calendar half <= 0; net <= 0 at 20 bp; net <= 0 without the 2 best clusters.
`--power`: signal-free line (cluster count of the event rule, sd of the 60-min return after move-only events).
Run: .venv/Scripts/python.exe research/screens/2026-11-14_i76_liquidation_reversal_screen.py [--power]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path("data/cache")
START, END = pd.Timestamp("2020-01-01", tz="UTC"), pd.Timestamp("2021-09-14", tz="UTC")
K_SD, SHARE, VOL_X, HOLD, COST_BP = 4.0, 0.65, 25.0, 60, 10.0


def symbols():
    return sorted(p.name for p in (CACHE / "binance").iterdir() if p.is_dir())


def load(sym):
    frames = []
    for d in pd.date_range(START, END - pd.Timedelta(days=1), freq="D"):
        k = CACHE / "binance" / sym / f"{d.year}" / f"{d.date()}.parquet"
        f = CACHE / "binance_flow" / sym / f"{d.year}" / f"{d.date()}.parquet"
        if k.exists() and f.exists():
            a = pd.read_parquet(k, columns=["ts", "bid_close"]).set_index("ts")
            b = pd.read_parquet(f, columns=["ts", "volume", "buy_volume", "sell_volume"]).set_index("ts")
            frames.append(a.join(b, how="inner"))
    if not frames:
        return None
    x = pd.concat(frames)
    x = x[~x.index.duplicated()].sort_index()
    return x.reindex(pd.date_range(x.index[0], x.index[-1], freq="min"))  # gaps -> NaN, t-5 is 5 minutes


def funding(sym):
    f = pd.read_csv(CACHE / "binance_funding" / f"{sym}.csv", parse_dates=["calc_time"])
    return f.set_index(f.calc_time.dt.tz_localize("UTC").dt.floor("min"))["last_funding_rate"].sort_index()


def signals(x):
    c = x.bid_close
    lr = np.log(c).diff()
    sd5 = lr.shift(5).rolling(1440, min_periods=1000).std() * np.sqrt(5)
    r5 = np.log(c / c.shift(5))
    v5 = x.volume.rolling(5, min_periods=5).sum()
    vmed = x.volume.shift(5).rolling(1440, min_periods=1000).median()
    sell = x.sell_volume.rolling(5, min_periods=5).sum() / v5
    buy = x.buy_volume.rolling(5, min_periods=5).sum() / v5
    big = v5 >= VOL_X * vmed
    move_dn, move_up = r5 <= -K_SD * sd5, r5 >= K_SD * sd5
    event = pd.Series(0, index=x.index)
    event[move_dn & (sell >= SHARE) & big] = 1  # long after a bearish cascade
    event[move_up & (buy >= SHARE) & big] = -1
    control = pd.Series(0, index=x.index)
    control[move_dn] = 1
    control[move_up] = -1
    return event, control


def trades(sym, x, fr, sig, hold=HOLD):
    c = x.bid_close.to_numpy()
    idx = x.index
    s = sig.to_numpy()
    out, free = [], 0
    for t in np.flatnonzero(s):
        if t < free or t + 1 + hold >= len(c):
            continue
        e, q = c[t + 1], c[t + 1 + hold]
        if np.isnan(e) or np.isnan(q):
            continue
        free = t + 1 + hold
        d = int(s[t])
        held = fr[(fr.index > idx[t + 1]) & (fr.index <= idx[t + 1 + hold])].sum() * 1e4
        price = d * (q / e - 1) * 1e4
        out.append((idx[t + 1], sym, d, price, -d * held))
    return out


def clusters(df, cost):
    df = df.sort_values("entry").reset_index(drop=True)
    df["net"] = df.price + df.fund - cost
    cid, first, k = [], None, -1
    for t in df.entry:
        if first is None or t - first > pd.Timedelta(minutes=60):
            first, k = t, k + 1
        cid.append(k)
    df["cid"] = cid
    g = df.groupby("cid").agg(entry=("entry", "first"), net=("net", "mean"))
    return g


def stats(g):
    n, m, sd = len(g), g.net.mean(), g.net.std()
    return n, m, m / (sd / np.sqrt(n)) if n > 1 and sd > 0 else float("nan")


def main(argv):
    power = "--power" in argv
    rows, ctrl = [], []
    hold_rows = {15: [], 30: []}
    for sym in symbols():
        x = load(sym)
        if x is None:
            continue
        fr = funding(sym)
        ev, co = signals(x)
        rows += trades(sym, x, fr, ev)
        ctrl += trades(sym, x, fr, co)
        if not power:
            for h in (15, 30):
                hold_rows[h] += trades(sym, x, fr, ev, h)
        print(sym, int((ev != 0).sum()), int((co != 0).sum()), flush=True)
    cols = ["entry", "sym", "dir", "price", "fund"]
    df, cdf = pd.DataFrame(rows, columns=cols), pd.DataFrame(ctrl, columns=cols)
    g = clusters(df, COST_BP)
    if power:
        sd = cdf.price.std()
        print(f"POWER: event trades {len(df)}, clusters {len(g)}, symbols {df.sym.nunique()}; control trades "
              f"{len(cdf)}, 60-min return sd after move-only events {sd:.1f} bp -> se {sd / np.sqrt(len(g)):.1f} bp, "
              f"t 3 needs {3 * sd / np.sqrt(len(g)):.1f} bp net per cluster (ignores within-cluster averaging)")
        return 0
    n, m, t = stats(g)
    h20 = clusters(df, 2 * COST_BP)
    y = g.entry.dt.year
    best2 = g.drop(g.net.nlargest(2).index)
    print(f"\nPRIMARY: trades {len(df)}, clusters {n}, net {m:+.2f} bp/cluster, t {t:.2f}, "
          f"gross price {df.price.mean():+.2f}, funding {df.fund.mean():+.3f}, positive {100 * (g.net > 0).mean():.0f} %")
    print(f"  2020 {g.net[y == 2020].mean():+.2f} ({(y == 2020).sum()}), 2021 {g.net[y == 2021].mean():+.2f} "
          f"({(y == 2021).sum()}); at 20 bp {h20.net.mean():+.2f}; without 2 best {best2.net.mean():+.2f}")
    kills = {"net <= 0": m <= 0, "t < 3": not t >= 3.0, "half <= 0": min(g.net[y == 2020].mean(), g.net[y == 2021].mean()) <= 0,
             "20 bp <= 0": h20.net.mean() <= 0, "without 2 best <= 0": best2.net.mean() <= 0}
    print("  kills:", {k: bool(v) for k, v in kills.items()}, "->", "KILLED" if any(kills.values()) else "PASSED")
    gc = clusters(cdf, COST_BP)
    print(f"DIAG control (move only): trades {len(cdf)}, clusters {len(gc)}, net {stats(gc)[1]:+.2f}, t {stats(gc)[2]:.2f}, "
          f"gross {cdf.price.mean():+.2f}")
    for d, name in ((1, "long after bearish"), (-1, "short after bullish")):
        s = df[df.dir == d]
        print(f"DIAG {name}: trades {len(s)}, gross {s.price.mean():+.2f}, net/trade {(s.price + s.fund - COST_BP).mean():+.2f}")
    be = df[df.sym.isin(["BTCUSDT", "ETHUSDT"])]
    if len(be):
        gb = clusters(be, COST_BP)
        print(f"DIAG BTC+ETH: trades {len(be)}, net {stats(gb)[1]:+.2f}, t {stats(gb)[2]:.2f}")
    for h, r in hold_rows.items():
        gh = clusters(pd.DataFrame(r, columns=cols), COST_BP)
        print(f"DIAG hold {h} min: clusters {len(gh)}, net {stats(gh)[1]:+.2f}, t {stats(gh)[2]:.2f}")
    print("DIAG trades per symbol:", df.sym.value_counts().to_dict())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
