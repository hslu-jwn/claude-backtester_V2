"""I-78 / I-79 / I-80 screen: weekly cross-sectional sorts on every Binance USDT perp (knowledge/ideas.md › I-78).

Rules and kills pre-registered in the card (commit 709a87c) before any data was read. Crypto split: development
2020-01-01 .. 2023-12-31 only (no bar after 2023-12-31 is read). Every Monday: eligible = >= 60 daily bars before
the Monday, median daily quote volume >= 5 M USDT over the last 30 days, a Monday bar; a week needs >= 20 eligible.
Signals from the 7 bars before the Monday: flow = sum(2 x taker buy - volume) / sum(volume); max = largest daily
close-to-close return; vshock = 7-day quote volume / (7 x mean daily quote volume of the 60 days before).
Quintile legs (n = floor(eligible / 5), ascending sort, ties by name); entry at the Monday open, exit at the close of
the next Sunday bar (or the last close in the week). Gross = top - bottom price return - funding of the top leg +
funding of the bottom leg (settlements strictly inside the hold); net in direction d = d x gross - 20 bp, d = sign
of the development mean. Kills: |t| < 3.0; net <= 0; halves not both > 0; net <= 0 at 40 bp; net <= 0 without the
2 best weeks.
`--test`: the one-time test pre-registered in the card (eba2631): flow only, long top, weeks from 2024-01-01.
`--power`: signal-free line (eligible per week, weekly sd of random quintile legs).
Run: .venv/Scripts/python.exe research/screens/2026-11-14_i78_crypto_wide_factors_screen.py [--power]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("data/cache/binance_wide")
TEST_ROOT = Path("data/cache/binance_wide_test")
TEST_START = pd.Timestamp("2024-01-01")
END = pd.Timestamp("2023-12-31")  # last development day (crypto split)
COST_BP, MIN_ELIG, MIN_BARS, MIN_QVOL = 20.0, 20, 60, 5e6
FACTORS = ("flow", "max", "vshock")


def read_klines(name, roots):
    parts = [pd.read_csv(r / "klines_1d" / name, usecols=["open_time", "open", "close", "volume", "quote_volume",
                                                         "taker_buy_volume"])
             for r in roots if (r / "klines_1d" / name).exists()]
    return pd.concat(parts, ignore_index=True)


def read_funding(name, roots):
    parts = [pd.read_csv(r / "funding" / name, usecols=["calc_time", "last_funding_rate"])
             for r in roots if (r / "funding" / name).exists()]
    return pd.concat(parts, ignore_index=True) if parts else None


def load(roots=(ROOT,)):
    k, fund = {}, {}
    names = sorted({p.name for r in roots for p in (r / "klines_1d").glob("*.csv")})
    for name in names:
        p = Path(name)
        d = read_klines(name, roots)
        d.index = pd.to_datetime(d.open_time, unit="ms").dt.normalize()
        d = d[~d.index.duplicated()].sort_index()
        d = d[d.index <= END]
        if len(d):
            k[p.stem] = d
        g = read_funding(name, roots)
        if g is not None:
            fund[p.stem] = pd.Series(g.last_funding_rate.to_numpy(),
                                     index=pd.to_datetime(g.calc_time, unit="ms").dt.floor("min")).sort_index()
    return k, fund


def week_rows(k, fund, monday):
    sunday_prev, sunday_next = monday - pd.Timedelta(days=1), monday + pd.Timedelta(days=6)
    rows = []
    for s, d in k.items():
        if monday not in d.index or (d.index < monday).sum() < MIN_BARS:
            continue
        past = d[d.index < monday]
        if past.quote_volume.iloc[-30:].median() < MIN_QVOL:
            continue
        last7 = past[past.index > sunday_prev - pd.Timedelta(days=7)]
        if len(last7) < 7:
            continue
        before = past[(past.index <= sunday_prev - pd.Timedelta(days=7))].iloc[-60:]
        rets = past.close.pct_change().loc[last7.index]
        held = d[(d.index >= monday) & (d.index <= sunday_next)]
        fr = fund.get(s, pd.Series(dtype=float, index=pd.DatetimeIndex([])))  # a perp without a funding file
        f = fr[(fr.index > monday) & (fr.index < sunday_next + pd.Timedelta(days=1))].sum() * 1e4
        rows.append({
            "sym": s,
            "flow": (2 * last7.taker_buy_volume - last7.volume).sum() / last7.volume.sum(),
            "max": rets.max(),
            "vshock": last7.quote_volume.sum() / (7 * before.quote_volume.mean()) if len(before) >= 30 else np.nan,
            "ret": (held.close.iloc[-1] / held.open.iloc[0] - 1) * 1e4,
            "fund": f,
        })
    return pd.DataFrame(rows)


def mondays(k):
    first = min(d.index[0] for d in k.values())
    m = first + pd.Timedelta(days=(7 - first.weekday()) % 7)
    out = []
    while m + pd.Timedelta(days=6) <= END:
        out.append(m)
        m += pd.Timedelta(days=7)
    return out


def spread(w, col):
    w = w.dropna(subset=[col]).sort_values([col, "sym"], kind="mergesort")
    n = len(w) // 5
    lo, hi = w.iloc[:n], w.iloc[-n:]
    gross = (hi.ret.mean() - lo.ret.mean()) - hi.fund.mean() + lo.fund.mean()
    return gross, hi.ret.mean() - lo.ret.mean(), n


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def test(argv):
    """One-time test (card I-78, pre-registered in eba2631): flow only, long top, weeks from 2024-01-01."""
    global END
    END = pd.Timestamp("2026-10-31")
    k, fund = load((ROOT, TEST_ROOT))
    weeks = {m: week_rows(k, fund, m) for m in mondays(k)}
    weeks = {m: w for m, w in weeks.items() if len(w) >= MIN_ELIG}
    dev = pd.Series({m: spread(w, "flow")[0] for m, w in weeks.items() if m < TEST_START}) - COST_BP
    net = pd.Series({m: spread(w, "flow")[0] for m, w in weeks.items() if m >= TEST_START}) - COST_BP
    g2 = net - COST_BP
    h = len(net) // 2
    both = pd.concat([dev, net])
    print(f"dev re-run: {len(dev)} weeks, net {dev.mean():+.1f}, t {tstat(dev):.2f} (must be +145.0, 3.24)")
    print(f"TEST: {len(net)} weeks ({net.index[0].date()} .. {net.index[-1].date()}), eligible median "
          f"{int(np.median([len(weeks[m]) for m in net.index]))}; net {net.mean():+.1f} bp/week, t {tstat(net):.2f}, "
          f"positive {100 * (net > 0).mean():.0f} %, worst {net.min():+.0f}")
    gates = {"(1) net > 0": net.mean() > 0, "(2) t >= 2": tstat(net) >= 2.0, "(3) pooled t >= 3": tstat(both) >= 3.0,
             "(4) halves > 0": net.iloc[:h].mean() > 0 and net.iloc[h:].mean() > 0,
             "(5) without 2 best > 0": net.drop(net.nlargest(2).index).mean() > 0, "(6) 40 bp > 0": g2.mean() > 0}
    print(f"  halves {net.iloc[:h].mean():+.1f} / {net.iloc[h:].mean():+.1f}; pooled t {tstat(both):.2f}; "
          f"without 2 best {net.drop(net.nlargest(2).index).mean():+.1f}; at 40 bp {g2.mean():+.1f}")
    print("  gates:", {a: bool(b) for a, b in gates.items()}, "->", "PASSED" if all(gates.values()) else "FAILED")
    return 0


def main(argv):
    if "--test" in argv:
        return test(argv)
    k, fund = load()
    weeks = {m: week_rows(k, fund, m) for m in mondays(k)}
    weeks = {m: w for m, w in weeks.items() if len(w) >= MIN_ELIG}
    print(f"symbols {len(k)}, weeks {len(weeks)} ({min(weeks).date()} .. {max(weeks).date()}), eligible per week "
          f"min {min(len(w) for w in weeks.values())} median {int(np.median([len(w) for w in weeks.values()]))} "
          f"max {max(len(w) for w in weeks.values())}")
    if "--power" in argv:
        rng = np.random.default_rng(1)
        sds = []
        for _ in range(200):
            sp = []
            for w in weeks.values():
                n = len(w) // 5
                r = rng.permutation(w.ret.to_numpy())
                sp.append(r[-n:].mean() - r[:n].mean())
            sds.append(np.std(sp, ddof=1))
        sd = float(np.mean(sds))
        print(f"POWER: random-leg weekly sd {sd:.0f} bp -> se {sd / np.sqrt(len(weeks)):.1f} bp; |t| 3 needs "
              f"{3 * sd / np.sqrt(len(weeks)):.0f} bp a week net")
        return 0
    idx = sorted(weeks)
    res = {}
    for col in FACTORS:
        g, p, n = zip(*(spread(weeks[m], col) for m in idx), strict=True)
        g = pd.Series(g, index=idx)
        d = 1.0 if g.mean() > 0 else -1.0
        net = d * g - COST_BP
        half = net[net.index < pd.Timestamp("2022-01-01")], net[net.index >= pd.Timestamp("2022-01-01")]
        t = tstat(net)
        kills = {"|t| < 3": not abs(t) >= 3.0, "net <= 0": net.mean() <= 0,
                 "halves": not (half[0].mean() > 0 and half[1].mean() > 0),
                 "40 bp <= 0": (d * g - 2 * COST_BP).mean() <= 0,
                 "without 2 best <= 0": net.drop(net.nlargest(2).index).mean() <= 0}
        res[col] = d * g
        print(f"\n{col}: direction {'long top' if d > 0 else 'long bottom'}; net {net.mean():+.1f} bp/week, t {t:.2f}, "
              f"price {d * np.mean(p):+.1f}, funding part {d * g.mean() - d * np.mean(p):+.1f}, legs {min(n)}-{max(n)}, "
              f"positive {100 * (net > 0).mean():.0f} %, worst {net.min():+.0f}")
        print(f"  halves {half[0].mean():+.1f} / {half[1].mean():+.1f}; at 40 bp {(d * g - 2 * COST_BP).mean():+.1f}; "
              f"without 2 best {net.drop(net.nlargest(2).index).mean():+.1f}")
        print("  kills:", {a: bool(b) for a, b in kills.items()}, "->", "KILLED" if any(kills.values()) else "PASSED")
    past = []
    for m in idx:  # diagnostic: 1-week past-return sort (I-75's closed signal), long top
        w = weeks[m].copy()
        prev = []
        for s in w.sym:
            d_ = k[s]
            c = d_.close[d_.index < m]
            prev.append(c.iloc[-1] / c.iloc[-8] - 1 if len(c) >= 8 else np.nan)
        w["past"] = prev
        past.append(spread(w, "past")[0])
    past = pd.Series(past, index=idx)
    print("\nDIAG correlations of weekly gross spreads (in tested direction):")
    corr = pd.DataFrame({**res, "past_1w": past}).corr()
    print(corr.round(2).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
