"""FB-017 liquid-only Strategy 20 (knowledge/ideas.md › FB-017; rule frozen in commit before this script).

Diagnostic on spent periods (development 2020-2023, test 2024-01..2026-10), never a test: Strategy 20's frozen book
with the eligible set cut each Monday to the 100 symbols with the highest 30-bar median daily quote volume before the
Monday (ties by name). Prints weekly net, t, halves, and the top-100 share of the full book's legs.
Run: .venv/Scripts/python.exe research/screens/2026-11-15_fb017_liquid_s20.py
"""
from datetime import date

import numpy as np
import pandas as pd

from backtester.strategy.crypto_flow.book import DEFAULT, eligible_signals, pick_legs, week_result
from backtester.tools import crypto_flow as cf

TOP = 100


def top_cut(klines, monday, signals):
    vol = {s: klines[s].loc[klines[s].index < monday].quote_volume.iloc[-DEFAULT.volume_window:].median()
           for s in signals}
    keep = sorted(vol, key=lambda s: (-vol[s], s))[:TOP]
    return {s: signals[s] for s in keep}


def weeks(klines, funding, start, end, cut):
    monday = pd.Timestamp(start, tz="UTC")
    monday += pd.Timedelta(days=(-monday.weekday()) % 7)
    last = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
    out = []
    while monday + pd.Timedelta(days=7, minutes=-1) <= last:
        sig = eligible_signals(klines, monday)
        if cut:
            sig = top_cut(klines, monday, sig)
        picked = pick_legs(sig)
        if picked is not None:
            out.append((monday, week_result(monday, *picked, klines, funding).trade["net_bp"]))
        monday += pd.Timedelta(days=7)
    return pd.Series(dict(out))


def report(name, n, half):
    t = n.mean() / n.std(ddof=1) * np.sqrt(len(n))
    print(f"{name}: {len(n)} weeks, net {n.mean():+.1f} bp/week, t {t:.2f}, halves {n[n.index < half].mean():+.1f} / "
          f"{n[n.index >= half].mean():+.1f}, worst {n.min():+.0f}")


if __name__ == "__main__":
    k, f = cf.load()
    for label, a, b, half in (("development", date(2020, 1, 1), date(2023, 12, 31), pd.Timestamp("2022-01-01", tz="UTC")),
                              ("test (spent)", date(2024, 1, 1), date(2026, 10, 31), pd.Timestamp("2025-06-01", tz="UTC"))):
        report(f"{label} full universe", weeks(k, f, a, b, False), half)
        report(f"{label} top {TOP}", weeks(k, f, a, b, True), half)
