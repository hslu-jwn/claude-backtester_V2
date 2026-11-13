"""I-73 screen: cross-sectional funding carry on 17 Binance perps (knowledge/ideas.md › I-73).

Rule and kills pre-registered in the card (commit b586776) before the new data was read.
Monday 00:00 UTC: rank eligible symbols (>= 30 days of funding) by the mean of their last 21 settled
rates; short the top 4, long the bottom 4; enter at the close of the bar ending 00:01, exit at the
close of the bar ending Sunday 23:59. Weekly net (per 1 unit each side) = mean long return - mean short
return + funding received - funding paid - 20 bp. Development only (Sunday exit before 2021-09-14).
Kills: net <= 0; t < 3.0; halves opposite signs; net <= 0 without the 2 best weeks; price part < -20 bp.
`--power`: signal-free weekly sd of random 4-vs-4 portfolios (recorded in the card before the screen).
`--test`: the one-time test pre-registered in the card (commit 30c10b1): weeks from Monday 2021-09-20 to the
last Sunday exit <= 2026-10-25; signal = funding accrued in (Monday - 7 d, Monday] (same ranking as the mean of
21 rates for 8 h symbols; keeps 7 days for XTZUSDT's 4 h / 1 h funding from 2025-07-20).
Run: .venv/Scripts/python.exe research/screens/2026-11-13_i73_crypto_carry_xs_screen.py [--power | --test]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path("data/cache")
SYMBOLS = "BTC ETH BCH XRP EOS LTC TRX ETC LINK XLM ADA BNB XTZ XMR NEO DASH ATOM".split()
SYMBOLS = [s + "USDT" for s in SYMBOLS]
END = pd.Timestamp("2021-09-14", tz="UTC")
TEST_START, TEST_END = pd.Timestamp("2021-09-20", tz="UTC"), pd.Timestamp("2026-10-26", tz="UTC")
N_LEG, LOOKBACK, COST_BP = 4, 21, 20.0


def funding(sym):
    f = pd.read_csv(CACHE / "binance_funding" / f"{sym}.csv", parse_dates=["calc_time"])
    return f.set_index(f.calc_time.dt.tz_localize("UTC").dt.floor("min"))["last_funding_rate"].sort_index()


def close_at(sym, bar_open):
    """Close of the M1 bar that opens at `bar_open` (None if the bar is missing)."""
    p = CACHE / "binance" / sym / f"{bar_open.year}" / f"{bar_open.date()}.parquet"
    if not p.exists():
        return None
    d = pd.read_parquet(p, columns=["ts", "bid_close"]).set_index("ts")["bid_close"]
    return d.get(bar_open)


def weeks(start=None, end=END):
    """Per Monday: {symbol: (signal, price return bp, funding bp paid by a long)} of the eligible symbols."""
    fr = {s: funding(s) for s in SYMBOLS}
    first = min(f.index[0] for f in fr.values()).normalize()
    monday = first + pd.Timedelta(days=(7 - first.weekday()) % 7)
    monday = max(monday, start) if start is not None else monday
    out = {}
    while monday + pd.Timedelta(days=7) <= end:
        entry, exit_ = monday + pd.Timedelta(minutes=1), monday + pd.Timedelta(days=7, minutes=-1)
        rows = {}
        for s, f in fr.items():
            if f.index[0] > monday - pd.Timedelta(days=30):
                continue
            past = f[f.index <= monday]
            if len(past) < LOOKBACK:
                continue
            a, b = close_at(s, monday), close_at(s, exit_ - pd.Timedelta(minutes=1))
            held = f[(f.index > entry) & (f.index <= exit_)]
            accrued = past[past.index > monday - pd.Timedelta(days=7)].sum()
            rows[s] = (accrued, (b / a - 1) * 1e4 if a and b else np.nan, held.sum() * 1e4)
        if len(rows) >= 2 * N_LEG:
            out[monday] = rows
        monday += pd.Timedelta(days=7)
    return out


def leg_parts(rows, longs, shorts):
    """(price part bp, funding part bp) of one week for the given legs; NaN symbols dropped per leg."""
    lg = [rows[s] for s in longs if not np.isnan(rows[s][1])]
    sh = [rows[s] for s in shorts if not np.isnan(rows[s][1])]
    price = np.mean([r[1] for r in lg]) - np.mean([r[1] for r in sh])
    fund = np.mean([r[2] for r in sh]) - np.mean([r[2] for r in lg])  # shorts receive, longs pay
    return price, fund


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x))


def power(ws):
    rng = np.random.default_rng(73)
    sds = []
    for _ in range(200):
        net = []
        for rows in ws.values():
            pick = list(rng.permutation(sorted(rows)))
            p, f = leg_parts(rows, pick[:N_LEG], pick[N_LEG : 2 * N_LEG])
            net.append(p + f - COST_BP)
        sds.append(np.std(net, ddof=1))
    sd = float(np.median(sds))
    print(f"weeks {len(ws)}, symbols per week {min(map(len, ws.values()))}-{max(map(len, ws.values()))}")
    print(f"random 4v4 weekly sd {sd:.0f} bp -> standard error {sd / np.sqrt(len(ws)):.0f} bp; "
          f"t 3 needs a net mean of {3 * sd / np.sqrt(len(ws)):.0f} bp a week")


def screen(ws, quiet=False):
    rec = []
    for monday, rows in ws.items():
        ranked = sorted(rows, key=lambda s: rows[s][0])
        longs, shorts = ranked[:N_LEG], ranked[-N_LEG:]
        p, f = leg_parts(rows, longs, shorts)
        no_majors = {s: r for s, r in rows.items() if s not in ("BTCUSDT", "ETHUSDT")}
        rk = sorted(no_majors, key=lambda s: no_majors[s][0])
        p2, f2 = leg_parts(no_majors, rk[:N_LEG], rk[-N_LEG:]) if len(rk) >= 2 * N_LEG else (np.nan, np.nan)
        rec.append((monday, p, f, p + f - COST_BP, p2 + f2 - COST_BP, " ".join(s[:-4] for s in shorts)))
    d = pd.DataFrame(rec, columns=["monday", "price", "fund", "net", "net_ex_majors", "shorts"]).set_index("monday")
    if quiet:
        return d
    half = len(d) // 2
    drop2 = d.net.drop(d.net.nlargest(2).index)
    print(f"weeks {len(d)} ({d.index[0].date()} .. {d.index[-1].date()})")
    print(f"net {d.net.mean():+.1f} bp/week  t {tstat(d.net):+.2f}  price {d.price.mean():+.1f}  funding {d.fund.mean():+.1f}"
          f"  win {np.mean(d.net > 0):.2f}  sd {d.net.std():.0f}")
    print(f"halves {d.net.iloc[:half].mean():+.1f} / {d.net.iloc[half:].mean():+.1f}  without 2 best {drop2.mean():+.1f}"
          f"  net@30 {d.net.mean() - 10:+.1f}  worst week {d.net.min():+.0f}  ex BTC/ETH {d.net_ex_majors.mean():+.1f}")
    kills = {
        "net <= 0": d.net.mean() <= 0,
        "t < 3.0": tstat(d.net) < 3.0,
        "halves opposite": np.sign(d.net.iloc[:half].mean()) != np.sign(d.net.iloc[half:].mean()),
        "without 2 best <= 0": drop2.mean() <= 0,
        "price part < -20 bp": d.price.mean() < -20,
    }
    print("kills:", {k: bool(v) for k, v in kills.items()}, "->", "KILLED" if any(kills.values()) else "PASSES the screen")
    print(d.groupby(d.index.year).net.agg(["mean", "count"]).round(1).to_string())
    return d


def test():
    dev = screen(weeks(), quiet=True)
    print(f"development re-run: net {dev.net.mean():+.1f}, t {tstat(dev.net):+.2f} (must be +138.0 / +1.30)")
    d = screen(weeks(TEST_START, TEST_END + pd.Timedelta(days=6)), quiet=True)
    half, drop2 = len(d) // 2, d.net.drop(d.net.nlargest(2).index)
    pooled = pd.concat([dev.net, d.net])
    losing = (d.net < 0).astype(int).groupby((d.net >= 0).cumsum()).sum().max()
    print(f"TEST weeks {len(d)} ({d.index[0].date()} .. {d.index[-1].date()})")
    print(f"net {d.net.mean():+.1f} bp/week  t {tstat(d.net):+.2f}  price {d.price.mean():+.1f}  funding {d.fund.mean():+.1f}"
          f"  win {np.mean(d.net > 0):.2f}  sd {d.net.std():.0f}  worst {d.net.min():+.0f}  longest losing run {losing}")
    print(f"halves {d.net.iloc[:half].mean():+.1f} / {d.net.iloc[half:].mean():+.1f}  without 2 best {drop2.mean():+.1f}"
          f"  net@30 {d.net.mean() - 10:+.1f}  ex BTC/ETH {d.net_ex_majors.mean():+.1f}  pooled t {tstat(pooled):+.2f} (n {len(pooled)})")
    gates = {
        "1 test net > 0": d.net.mean() > 0,
        "2 test t >= 2.0": tstat(d.net) >= 2.0,
        "3 pooled t >= 3.0": tstat(pooled) >= 3.0,
        "4 both halves > 0": d.net.iloc[:half].mean() > 0 and d.net.iloc[half:].mean() > 0,
        "5 without 2 best > 0": drop2.mean() > 0,
    }
    print("gates:", {k: bool(v) for k, v in gates.items()}, "->", "PASSED" if all(gates.values()) else "FAILED")
    print(d.groupby(d.index.year)[["net", "price", "fund"]].mean().round(1).assign(weeks=d.groupby(d.index.year).size()).to_string())


if __name__ == "__main__":
    if "--test" in sys.argv:
        test()
    else:
        ws = weeks()
        power(ws) if "--power" in sys.argv else screen(ws)
