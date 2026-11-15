"""Wave 1 shared crypto breadth screen (I-82 / I-83 / I-84, knowledge/ideas.md; rules fixed in commit ff2c2c2).

Crypto split: development 2020-01-01 .. 2023-12-31 only. Weekly sorts reuse the frozen I-78 screen functions
(`research/screens/2026-11-14_i78_crypto_wide_factors_screen.py`), so eligibility, legs, funding and costs are
identical; the daily sort (I-82) uses the same rules on a date x symbol panel.
Tool features (Fable FB-287 / 246 / 252): a canary that must reproduce I-78's development result (+145.0 bp, t 3.24)
before any look, signal deciles (dose-response), a shuffled-signal placebo (signal permuted across symbols within
each period, 20 draws) and the weekly correlation with Strategy 20 (I-78).
Run: .venv/Scripts/python.exe research/screens/2026-11-15_wave1_xs_crypto_screen.py [--power] [i82] [i83] [i84]
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("i78", "research/screens/2026-11-14_i78_crypto_wide_factors_screen.py")
i78 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i78)
SPOT_ROOT = Path("data/cache/binance_wide_spot")
COST = i78.COST_BP
HALF = pd.Timestamp("2022-01-01")


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def legs_gross(w, col, rng=None):
    w = w.dropna(subset=[col])
    if rng is not None:  # placebo: the signal permuted across symbols
        w = w.assign(**{col: rng.permutation(w[col].to_numpy())})
    w = w.sort_values([col, "sym"], kind="mergesort")
    n = len(w) // 5
    if n == 0:
        return np.nan
    lo, hi = w.iloc[:n], w.iloc[-n:]
    return (hi.ret.mean() - lo.ret.mean()) - hi.fund.mean() + lo.fund.mean()


def deciles(periods, col):
    out = []
    for w in periods.values():
        w = w.dropna(subset=[col])
        if len(w) >= 20:
            q = pd.qcut(w[col].rank(method="first"), 10, labels=False)
            out.append(w.groupby(q).ret.mean())
    return pd.concat(out, axis=1).mean(axis=1).round(0).to_dict()


def report(name, periods, col, s20=None, unit="week"):
    idx = sorted(periods)
    g = pd.Series([legs_gross(periods[m], col) for m in idx], index=idx).dropna()
    d = 1.0 if g.mean() > 0 else -1.0
    net = d * g - COST
    h = net[net.index < HALF].mean(), net[net.index >= HALF].mean()
    t = tstat(net)
    kills = {"|t| < 3": not abs(t) >= 3.0, "net <= 0": net.mean() <= 0, "halves": not (h[0] > 0 and h[1] > 0),
             "40 bp <= 0": (d * g - 2 * COST).mean() <= 0,
             "without 2 best <= 0": net.drop(net.nlargest(2).index).mean() <= 0}
    print(f"\n{name}: {len(net)} {unit}s, direction {'long top' if d > 0 else 'long bottom'}; net {net.mean():+.1f} bp/"
          f"{unit}, t {t:.2f}, positive {100 * (net > 0).mean():.0f} %, worst {net.min():+.0f}; halves {h[0]:+.1f} / "
          f"{h[1]:+.1f}; at 40 bp {(d * g - 2 * COST).mean():+.1f}; without 2 best {net.drop(net.nlargest(2).index).mean():+.1f}")
    print("  kills:", {a: bool(b) for a, b in kills.items()}, "->", "KILLED" if any(kills.values()) else "PASSED")
    rng = np.random.default_rng(7)
    pt = []
    for _ in range(20):
        pg = pd.Series([legs_gross(periods[m], col, rng) for m in idx], index=idx).dropna()
        pt.append(tstat(d * pg - COST))
    print(f"  DIAG placebo (signal shuffled, 20 draws): mean t {np.mean(pt):+.2f}, |t| >= 3 in {sum(abs(x) >= 3 for x in pt)}")
    print(f"  DIAG deciles (mean member return bp, low -> high signal): {deciles(periods, col)}")
    if s20 is not None:
        wk = (d * g).groupby(g.index - pd.to_timedelta(g.index.weekday, unit="D")).sum() if unit == "day" else d * g
        j = pd.concat({"x": wk, "s20": s20}, axis=1, sort=True).dropna()
        print(f"  DIAG weekly correlation with Strategy 20: {j.corr().iloc[0, 1]:+.2f} ({len(j)} weeks)")
    return kills


def weekly(k, fund, spot):
    out = {}
    for m in i78.mondays(k):
        w = i78.week_rows(k, fund, m)
        if len(w) < i78.MIN_ELIG:
            continue
        r7, sf = [], []
        for s in w.sym:
            c = k[s].close[k[s].index < m]
            r7.append(c.iloc[-1] / c.iloc[-8] - 1 if len(c) >= 8 else np.nan)
            sp = spot.get(s)
            if sp is None:
                sf.append(np.nan)
                continue
            last = sp[(sp.index < m) & (sp.index >= m - pd.Timedelta(days=7))]
            sf.append((2 * last.taker_buy_volume - last.volume).sum() / last.volume.sum()
                      if len(last) == 7 and last.volume.sum() > 0 else np.nan)
        w["ret7"], w["spot_flow"] = r7, sf
        ok = w.dropna(subset=["flow", "ret7"])
        if len(ok) >= 3:
            b = np.polyfit(ok.ret7, ok.flow, 1)
            w["absorb"] = w.flow - (b[0] * w.ret7 + b[1])
        else:
            w["absorb"] = np.nan
        w["spot_minus_perp"] = w.spot_flow - w.flow
        out[m] = w
    return out


def daily(k, fund):
    """I-82 panel: eligibility as I-78 with the day's bar; signal = yesterday's bar flow; hold the day."""
    out = {}
    feats = {}
    for s, d in k.items():
        d = d.copy()
        d["bars_before"] = np.arange(len(d))
        d["qmed"] = d.quote_volume.rolling(30).median().shift(1)
        prev_ok = d.index.to_series().diff().dt.days.eq(1)
        flow = (2 * d.taker_buy_volume - d.volume) / d.volume.replace(0, np.nan)
        d["sig"] = flow.shift(1).where(prev_ok)
        d["ret"] = (d.close / d.open - 1) * 1e4
        fr = fund.get(s, pd.Series(dtype=float, index=pd.DatetimeIndex([])))
        day = fr.index.normalize()
        inside = fr[(fr.index > day) & (fr.index < day + pd.Timedelta(days=1))]  # strictly inside the day
        d["fund"] = inside.groupby(inside.index.normalize()).sum().reindex(d.index).fillna(0.0) * 1e4
        feats[s] = d[(d.bars_before >= i78.MIN_BARS) & (d.qmed >= i78.MIN_QVOL)]
    panel = pd.concat({s: f[["sig", "ret", "fund"]] for s, f in feats.items()}, names=["sym", "day"]).reset_index()
    panel = panel[panel.day >= pd.Timestamp("2020-01-01")]
    for day, w in panel.groupby("day"):
        if len(w) >= i78.MIN_ELIG and w.sig.notna().sum():
            out[day] = w.rename(columns={"sig": "flow1"})
    return out


def main(argv):
    k, fund = i78.load()
    spot = {}
    if SPOT_ROOT.exists():
        for p in (SPOT_ROOT / "klines_1d").glob("*.csv"):
            d = pd.read_csv(p, usecols=["open_time", "volume", "taker_buy_volume"])
            d.index = pd.to_datetime(d.open_time, unit="ms").dt.normalize()
            spot[p.stem] = d[~d.index.duplicated()].sort_index().loc[:i78.END]
    wk = weekly(k, fund, spot)
    canary = pd.Series([legs_gross(w, "flow") for w in wk.values()]) - COST
    print(f"CANARY I-78: {len(canary)} weeks, net {canary.mean():+.1f}, t {tstat(canary):.2f} (must be 186, +145.0, 3.24)")
    assert len(canary) == 186 and abs(canary.mean() - 145.0) < 0.05 and abs(tstat(canary) - 3.24) < 0.005, "canary failed"
    s20 = pd.Series({m: legs_gross(w, "flow") for m, w in wk.items()})
    if "--power" in argv:
        rng = np.random.default_rng(1)
        for name, periods, col in (("weekly (I-83 / I-84)", wk, "flow"),
                                   ("daily (I-82)", daily(k, fund) if "i82" in argv else {}, "flow1")):
            if not periods:
                continue
            sds = []
            for _ in range(50):
                sp = []
                for w in periods.values():
                    w = w.dropna(subset=[col])
                    n = len(w) // 5
                    r = rng.permutation(w.ret.to_numpy())
                    sp.append(r[-n:].mean() - r[:n].mean())
                sds.append(np.std(sp, ddof=1))
            sd = float(np.mean(sds))
            print(f"POWER {name}: {len(periods)} periods, random-leg sd {sd:.0f} bp -> |t| 3 needs "
                  f"{3 * sd / np.sqrt(len(periods)):.1f} bp net per period")
        n_spot = sum(1 for w in wk.values() if w.spot_flow.notna().sum() >= i78.MIN_ELIG)
        print(f"POWER I-84: weeks with >= 20 symbols with spot data: {n_spot}")
        return 0
    if "i82" in argv:
        report("I-82 daily taker flow", daily(k, fund), "flow1", s20, unit="day")
    if "i83" in argv:
        report("I-83 absorption", wk, "absorb", s20)
    if "i84" in argv:
        report("I-84 spot minus perp flow", {m: w for m, w in wk.items() if w.spot_flow.notna().sum() >= i78.MIN_ELIG},
               "spot_minus_perp", s20)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
