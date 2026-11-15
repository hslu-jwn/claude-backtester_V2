"""Strategy 20 at a crypto prop firm (2026-11-15; Fable FB-261): challenge pass chance of the weekly book marked to
market every day, against 2-Step rules (HyroTrader / Crypto Fund Trader type: +10 % then +5 %, daily loss limit on
end-of-day equity vs the previous day's end, 10 % static max loss, no time limit; rules UNVERIFIED, see
knowledge/research/reports/2026-11-15_prop_firm_rules.md). Diagnostic on the spent test weeks; no rule change.

Daily path of one week: each member's close / entry (Monday open) per day, held flat after its last bar; long leg -
short leg, both legs equal weight; cost 10 bp on Monday and 10 bp on Sunday (per unit on each side); funding of each
day's settlements (Monday 00:00 excluded, as tested). Account: notional per side = f x initial balance (fixed, no
compounding). Weeks are drawn with replacement (block = one week) to build attempts; intraday swings are not seen
(end-of-day marks only: optimistic for the daily limit).
Run: .venv/Scripts/python.exe research/screens/2026-11-15_s20_prop_fit.py
"""
import importlib.util

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("i78", "research/screens/2026-11-14_i78_crypto_wide_factors_screen.py")
i78 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i78)


def week_path(k, fund, w, monday):
    """Seven end-of-day book returns (bp of one side's notional) for one week, incl. costs and funding."""
    w = w.dropna(subset=["flow"]).sort_values(["flow", "sym"], kind="mergesort")
    n = len(w) // 5
    days = pd.date_range(monday, periods=7, freq="D")
    paths = {}
    for side, members in (("long", w.iloc[-n:].sym), ("short", w.iloc[:n].sym)):
        rel = []
        for s in members:
            d = k[s]
            held = d[(d.index >= monday) & (d.index <= days[-1])]
            entry = held.open.iloc[0]
            closes = held.close.reindex(days).ffill()
            fr = fund.get(s, pd.Series(dtype=float, index=pd.DatetimeIndex([])))
            # settlements inside the hold: (Monday 00:00, next Monday 00:00); day dd takes [dd, dd + 1 day)
            daily_f = pd.Series([fr[((fr.index > dd) if dd == monday else (fr.index >= dd))
                                    & (fr.index < dd + pd.Timedelta(days=1))].sum() for dd in days], index=days).cumsum()
            rel.append((closes / entry - 1) - daily_f)  # a long pays a positive rate
        paths[side] = pd.concat(rel, axis=1).mean(axis=1)
    book = (paths["long"] - paths["short"]) * 1e4  # short leg: price falls and funding received both add
    book.iloc[:] -= 10.0
    book.iloc[-1] -= 10.0
    return book.to_numpy()  # cumulative within the week


def attempt(weeks, rng, f, daily_lim, max_lim=0.10, targets=(0.10, 0.05), max_weeks=520):
    """Return (passed, days). Equity per phase starts at 1; P/L = f x book bp / 1e4."""
    total_days = 0
    for target in targets:
        eq, prev = 1.0, 1.0
        for _ in range(max_weeks):
            path = weeks[rng.integers(len(weeks))]
            start = eq
            for cum in path:
                eq_d = start + f * cum / 1e4
                total_days += 1
                if prev - eq_d >= daily_lim or 1.0 - eq_d >= max_lim:
                    return False, total_days
                prev = eq_d
            eq = eq_d
            if eq >= 1.0 + target:
                break
        else:
            return False, total_days
    return True, total_days


def main():
    i78.END = pd.Timestamp("2026-10-31")
    k, fund = i78.load((i78.ROOT, i78.TEST_ROOT))
    paths = {"dev": [], "test": []}
    for m in i78.mondays(k):
        w = i78.week_rows(k, fund, m)
        if len(w) < i78.MIN_ELIG:
            continue
        paths["test" if m >= i78.TEST_START else "dev"].append(week_path(k, fund, w, m))
    for name, weeks in paths.items():
        end = np.array([p[-1] for p in weeks])
        worst_day = min(np.min(np.diff(np.r_[0.0, p])) for p in weeks)
        print(f"{name}: {len(weeks)} weeks, mean week {end.mean():+.1f} bp (check: screen net), worst single day "
              f"{worst_day:+.0f} bp of one side")
    rng = np.random.default_rng(3)
    print("\nPass chance (2-Step 10 % + 5 %, 10 % static max loss), test weeks bootstrapped, 2,000 attempts:")
    print("| notional per side | daily limit 5 % | days (median) | daily limit 4 % | days (median) |")
    print("|---|---|---|---|---|")
    for f in (0.25, 0.5, 0.75, 1.0):
        cells = []
        for lim in (0.05, 0.04):
            res = [attempt(paths["test"], rng, f, lim) for _ in range(2000)]
            ok = [d for p, d in res if p]
            cells += [f"{100 * len(ok) / len(res):.0f} %", f"{np.median(ok):.0f}" if ok else "-"]
        print(f"| {f:.0%} | " + " | ".join(cells) + " |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
