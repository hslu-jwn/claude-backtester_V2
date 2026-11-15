"""I-94: level-touch null model for ICT levels, fair value gaps and equal highs / lows (knowledge/ideas.md › I-94;
rules fixed in commit ff93b2b before any data). Descriptive: one look for family `ict_levels`, never a pass.

M15 bars from M1 inside the trading day (17:00 -> 17:00 New York), 8 symbols, development only (before 2021-09-14).
ATR = mean daily range of the previous 14 trading days. FVG: bullish at bar i if low[i] > high[i-2] by >= 0.05 ATR;
first touch of low[i] within 32 later bars of the same day; held = no low below high[i-2] in the next 4 bars; forward
= close 4 bars after the touch vs low[i] (reversal direction), bp. Null: the zone shifted by u x gap, u ~ U(1, 3),
random sign (seed 11). Equal highs: swing high (2 bars each side), within 0.05 ATR of a swing high of the previous
32 bars with no bar between above both; exceeded within 16 bars; null: single swing highs, by distance bucket.
Run: .venv/Scripts/python.exe research/screens/2026-11-15_i94_level_null_model.py
"""
import importlib.util
import sys

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("ict", "research/screens/2026-11-15_i91_ict_events_screen.py")
ict = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ict)
rng = np.random.default_rng(11)


def m15(df):
    g = df.groupby(["td", df.index.floor("15min")])
    b = g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
    return b.reset_index(level=1).rename(columns={"level_1": "t"})


def fvg_events(sym, df, rng_d):
    out = []
    bars = m15(df)
    for td, b in bars.groupby(level=0):
        if td not in rng_d.index or np.isnan(rng_d.loc[td, "atr"]):
            continue
        a = rng_d.loc[td, "atr"]
        h, lo, c = b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy()
        n = len(b)
        for i in range(2, n - 1):
            for side in (1, -1):
                if side == 1:
                    gap = lo[i] - h[i - 2]
                    top, bot = lo[i], h[i - 2]
                else:
                    gap = lo[i - 2] - h[i]
                    top, bot = h[i], lo[i - 2]  # bearish: zone [h[i], lo[i-2]]; touch = high reaches h[i]
                if gap < 0.05 * a:
                    continue
                shift_null = rng.uniform(1, 3) * gap * rng.choice([-1, 1])
                # the null zone must sit on the real zone's side of the formation close (else an instant "touch")
                if side == 1 and top + shift_null >= c[i]:
                    shift_null = -abs(shift_null)
                if side == -1 and top + shift_null <= c[i]:
                    shift_null = abs(shift_null)
                for kind, shift in (("real", 0.0), ("null", shift_null)):
                    t_lvl, b_lvl = top + shift, bot + shift
                    rest = range(i + 1, min(n, i + 33))
                    touch = next((j for j in rest if (lo[j] <= t_lvl if side == 1 else h[j] >= t_lvl)), None)
                    rec = {"day": td, "sym": sym, "side": side, "kind": kind, "touched": touch is not None}
                    if touch is not None and touch + 4 < n:
                        nxt = slice(touch + 1, touch + 5)
                        rec["held"] = bool(lo[nxt].min() > b_lvl) if side == 1 else bool(h[nxt].max() < b_lvl)
                        rec["fwd"] = side * (c[touch + 4] / t_lvl - 1) * 1e4
                    out.append(rec)
    return out


def equal_events(sym, df, rng_d):
    out = []
    bars = m15(df)
    for td, b in bars.groupby(level=0):
        if td not in rng_d.index or np.isnan(rng_d.loc[td, "atr"]):
            continue
        a = rng_d.loc[td, "atr"]
        h, lo, c = b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy()
        n = len(b)
        for side, x in ((1, h), (-1, -lo)):  # lows mirrored as negative highs
            swings = [j for j in range(2, n - 2) if x[j] > max(x[j - 2], x[j - 1], x[j + 1], x[j + 2])]
            for k, j in enumerate(swings):
                conf = j + 2
                partner = None
                for p in reversed(swings[:k]):
                    if j - p > 32:
                        break
                    if abs(x[p] - x[j]) <= 0.05 * a and x[p + 1:j].max(initial=-np.inf) < min(x[p], x[j]):
                        partner = p
                        break
                level = max(x[j], x[partner]) if partner is not None else x[j]
                fut = x[conf + 1:min(n, conf + 17)]
                if len(fut) == 0:
                    continue
                dist = (level - (c[conf] if side == 1 else -c[conf])) / a
                out.append({"day": td, "sym": sym, "equal": partner is not None, "exceeded": bool(fut.max() > level),
                            "dist": dist})
    return out


def clustered_t(diff_by_day):
    x = diff_by_day.dropna()
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x))), len(x)


def main(argv):
    data = {s: ict.frame(s) for s in ict.SYMBOLS}
    f = pd.DataFrame([r for s in ict.SYMBOLS for r in fvg_events(s, *data[s])])
    print("FVG (M15, gap >= 0.05 ATR): real vs null (shifted zone)")
    for kind, g in f.groupby("kind"):
        t = g[g.touched]
        print(f"  {kind}: zones {len(g)}, touched within 32 bars {100 * g.touched.mean():.1f} %, held 4 bars "
              f"{100 * t.held.mean():.1f} %, forward 60 min {t.fwd.mean():+.2f} bp (n {t.fwd.notna().sum()})")
    real = f[(f.kind == "real") & f.fwd.notna()].groupby("day").fwd.mean()
    null = f[(f.kind == "null") & f.fwd.notna()].groupby("day").fwd.mean()
    tt, n = clustered_t(real - null)
    d = (real - null).mean()
    print(f"  difference real - null (per day): {d:+.2f} bp, t {tt:.2f} over {n} days -> "
          f"{'ABOVE NULL (flag)' if d > 2 and tt >= 3 else 'not above null'}")
    for s, g in f[f.fwd.notna()].groupby("sym"):
        r, nl = g[g.kind == "real"].fwd.mean(), g[g.kind == "null"].fwd.mean()
        print(f"    {s}: real {r:+.2f}, null {nl:+.2f}")
    e = pd.DataFrame([r for s in ict.SYMBOLS for r in equal_events(s, *data[s])])
    print("\nEqual highs / lows (M15 swings): exceeded within 16 bars, equal vs single, by distance from the close")
    diffs = []
    for lo_b, hi_b in ((0, 0.1), (0.1, 0.2), (0.2, 0.4)):
        g = e[(e.dist >= lo_b) & (e.dist < hi_b)]
        eq, si = g[g.equal], g[~g.equal]
        print(f"  distance {lo_b}-{hi_b} ATR: equal {100 * eq.exceeded.mean():.1f} % (n {len(eq)}), single "
              f"{100 * si.exceeded.mean():.1f} % (n {len(si)})")
        dd = (eq.groupby("day").exceeded.mean() - si.groupby("day").exceeded.mean()) * 100
        diffs.append(dd)
    dd = pd.concat(diffs).groupby(level=0).mean()
    tt, n = clustered_t(dd)
    print(f"  difference equal - single (per day, buckets pooled): {dd.mean():+.1f} points, t {tt:.2f} over {n} days -> "
          f"{'ABOVE NULL (flag)' if dd.mean() > 5 and tt >= 3 else 'not above null'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
