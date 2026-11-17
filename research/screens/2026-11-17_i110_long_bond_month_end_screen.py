"""I-110 Treasury month-end on 20-year bonds (rule fixed in knowledge/ideas.md, 1bb20f0). I-109's functions, DGS20.

Steps: power (signal-free), run (development 1993-10 .. 2021-08), test (2021-10 .. 2026-10, rule fixed in the card).
Data: data/cache/fred/DGS20.csv (curl's own user agent; see I-109), Alpaca TLT closes.
Run: .venv/Scripts/python.exe research/screens/2026-11-17_i110_long_bond_month_end_screen.py power | run | test
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location(
    "i109", Path(__file__).parent / "2026-11-17_i109_treasury_month_end_screen.py"
)
i109 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i109)
i109.SERIES["DGS20"] = 20
COST = 3.0


def dev():
    return i109.months(i109.returns("DGS20", "1993-10-01", "2021-08-31"))


def power():
    r = i109.returns("DGS20", "1993-10-01", "2021-08-31")
    sd = np.mean([i109.months(r, k).excess.std() for k in (5, 8, 11, 14)])
    n = len(i109.months(r))
    se = sd / np.sqrt(n)
    print(
        f"DGS20 {r.index[0].date()} .. {r.index[-1].date()}, months {n}; signal-free excess sd {sd:.1f} bp, se {se:.1f}: "
        f"t 3 needs {3 * se:.1f} bp net ({3 * se + COST:.1f} gross)"
    )


def run():
    r = i109.returns("DGS20", "1993-10-01", "2021-08-31")
    e = i109.months(r)
    net = e.excess - COST
    t = i109.tstat(net)
    h1, h2 = net[net.index.year <= 2007].mean(), net[net.index.year >= 2008].mean()
    n2 = (e.excess - 2 * COST).mean()
    nb = net.drop(net.nlargest(2).index).mean()
    kills = {
        "net <= 0": net.mean() <= 0,
        "t < 3.0": t < 3.0,
        "halves": not (h1 > 0 and h2 > 0),
        "doubled cost <= 0": n2 <= 0,
        "without 2 best <= 0": nb <= 0,
    }
    hit = [k for k, v in kills.items() if v]
    print(
        f"months {len(e)} ({e.index[0]} .. {e.index[-1]}): excess gross {e.excess.mean():+.1f}, net {net.mean():+.1f}, "
        f"t {t:.2f}; halves {h1:+.1f} / {h2:+.1f}; doubled {n2:+.1f}; without 2 best {nb:+.1f} -> "
        f"{'KILLED ' + str(hit) if hit else 'PASSED (development)'}"
    )
    pl = i109.months(r, 10).excess
    ten = i109.months(i109.returns("DGS10", "1993-10-01", "2021-08-31")).excess
    print(
        f"reported: raw {e.raw.mean():+.1f} (t {i109.tstat(e.raw):.2f}); last 2 days {i109.months(r, days=2).excess.mean():+.1f}; "
        f"placebo {pl.mean():+.1f} (t {i109.tstat(pl):.2f}); excess / event sd: 20y {e.excess.mean() / e.excess.std():.3f} vs "
        f"10y {ten.mean() / ten.std():.3f} (same months); ratio of means 20y / 10y {e.excess.mean() / ten.mean():.2f}"
    )


def test():
    start, end = "2021-09-14", "2026-10-31"
    e = i109.months(i109.returns("DGS20", start, end)).loc["2021-10":"2026-10"]
    net = e.excess - COST
    t = i109.tstat(net)
    n2 = (e.excess - 2 * COST).mean()
    tlt = i109.months(i109.etf("TLT", start, end)).loc["2021-10":"2026-10"]
    g = {"net > 0": net.mean() > 0, "t >= 1.5": t >= 1.5, "doubled > 0": n2 > 0, "TLT raw > 0": tlt.raw.mean() > 0}
    verdict = "PASSED" if all(g.values()) else ("FALSIFIED" if net.mean() <= 0 else "NOT CONFIRMED")
    print(
        f"test months {len(e)} ({e.index[0]} .. {e.index[-1]}): excess gross {e.excess.mean():+.1f}, net {net.mean():+.1f}, "
        f"t {t:.2f}; doubled {n2:+.1f}; TLT raw {tlt.raw.mean():+.1f} (t {i109.tstat(tlt.raw):.2f}, {len(tlt)} months)"
    )
    print("gates:", g, "->", verdict)
    print(f"reported: by year {net.groupby(net.index.year).mean().round(1).to_dict()}")


if __name__ == "__main__":
    {"power": power, "run": run, "test": test}[sys.argv[1]]()
