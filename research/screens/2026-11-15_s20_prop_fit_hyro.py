"""Strategy 20 at HyroTrader with the published rules applied (2026-11-15; diagnostic on spent test weeks).

Extends research/screens/2026-11-15_s20_prop_fit.py (same daily-marked weekly paths, same 2-Step 10 % + 5 %, 5 %
static daily loss from start-of-day equity, 10 % max loss) with two rules read on hyrotrader.com 2026-11-15:
(1) low-cap cap: <= 5 % of initial balance across coins under 100 M USD market cap or 0.5-5 M USD daily volume; proxy
here = the FB-017 universe (top 100 by 30-bar median quote volume, all >= 5 M), with the full universe for contrast;
(2) profit distribution: a day's profit counts toward the target only up to 40 % of the target (the excess still
stays in equity). Max-loss type (static vs trailing) is not stated by Hyro: run static (as CFT states for 2-Phase).
Also runs each universe with every week shifted down to the fair forward expectation (+74 bp a week).
Run: .venv/Scripts/python.exe research/screens/2026-11-15_s20_prop_fit_hyro.py
"""
import importlib.util

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("pf", "research/screens/2026-11-15_s20_prop_fit.py")
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)
i78 = pf.i78


def top100(k, w, monday):
    vol = {s: k[s].loc[k[s].index < monday].quote_volume.iloc[-30:].median() for s in w.sym}
    keep = sorted(vol, key=lambda s: (-vol[s], s))[:100]
    return w[w.sym.isin(keep)]


def attempt(weeks, rng, f, daily_lim=0.05, max_lim=0.10, targets=(0.10, 0.05), max_weeks=520):
    total_days = 0
    for target in targets:
        eq, prev, counted = 1.0, 1.0, 0.0
        for _ in range(max_weeks):
            path = weeks[rng.integers(len(weeks))]
            start = eq
            for cum in path:
                eq_d = start + f * cum / 1e4
                total_days += 1
                if prev - eq_d >= daily_lim or 1.0 - eq_d >= max_lim:
                    return False, total_days
                counted += min(eq_d - prev, 0.4 * target)  # losses count in full, gains capped at 40 % of target
                prev = eq_d
            eq = eq_d
            if counted >= target and eq >= 1.0 + target:
                break
        else:
            return False, total_days
    return True, total_days


def main():
    i78.END = pd.Timestamp("2026-10-31")
    k, fund = i78.load((i78.ROOT, i78.TEST_ROOT))
    paths = {"full": [], "top100": []}
    for m in i78.mondays(k):
        if m < i78.TEST_START:
            continue
        w = i78.week_rows(k, fund, m)
        if len(w) < i78.MIN_ELIG:
            continue
        paths["full"].append(pf.week_path(k, fund, w, m))
        t = top100(k, w, m)
        if len(t) >= i78.MIN_ELIG:
            paths["top100"].append(pf.week_path(k, fund, t, m))
    for name in list(paths):  # fair-expectation scenario: every week shifted so the mean is +74 bp (spec › Execution)
        shift = np.mean([p[-1] for p in paths[name]]) - 74.0
        paths[f"{name} at +74"] = [p - shift * np.arange(1, 8) / 7 for p in paths[name]]
    rng = np.random.default_rng(3)
    print("| universe | weeks | mean week bp | notional per side | pass, Hyro rules | days (median) | pass, no 40 % rule |")
    print("|---|---|---|---|---|---|---|")
    for name, weeks in paths.items():
        mean = np.mean([p[-1] for p in weeks])
        for f in (0.25, 0.5):
            res = [attempt(weeks, rng, f) for _ in range(2000)]
            base = [pf.attempt(weeks, rng, f, 0.05) for _ in range(2000)]
            ok = [d for p, d in res if p]
            print(f"| {name} | {len(weeks)} | {mean:+.0f} | {f:.0%} | {100 * len(ok) / len(res):.0f} % | "
                  f"{np.median(ok):.0f} | {100 * np.mean([p for p, _ in base]):.0f} % |")


if __name__ == "__main__":
    main()
