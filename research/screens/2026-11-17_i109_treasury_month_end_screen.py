"""I-109 Treasury month-end duration extension (rule fixed in knowledge/ideas.md, 585b997). Development only.

FRED H.15 constant-maturity yields (public CSV) -> data/cache/fred/<ID>.csv. Steps: download, power (signal-free), run.
Run: .venv/Scripts/python.exe research/screens/2026-11-17_i109_treasury_month_end_screen.py download | power | run
"""

import io
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

FRED = Path("data/cache/fred")
SERIES = {"DGS10": 10, "DGS5": 5, "DGS2": 2}
START, END = "1990-01-01", "2021-09-13"
COST, DAYS = 2.0, 3


def download():  # curl's own user agent: FRED hangs on unknown ones (2026-11-17)
    FRED.mkdir(parents=True, exist_ok=True)
    for s in SERIES:
        body = subprocess.run(
            ["curl", "-s", "-f", f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}"],
            check=True,
            capture_output=True,
            timeout=120,
        ).stdout
        (FRED / f"{s}.csv").write_bytes(body)
        print(s, len(body))


def returns(series, start=START, end=END):
    """Daily price return (bp) of a par bond: -D(prev yield) * dy; trade dates = dates with a value."""
    d = pd.read_csv(io.StringIO((FRED / f"{series}.csv").read_text()), na_values=".")
    d.columns = ["day", "y"]
    y = d.assign(day=pd.to_datetime(d.day)).dropna().set_index("day").y.loc[start:end] / 100
    n = SERIES[series]
    dur = (1 - (1 + y / 2) ** (-2 * n)) / y  # modified duration of a par bond, semiannual coupons
    return (-dur.shift(1) * y.diff() * 1e4).dropna()


def months(r, offset=0, days=DAYS):
    """Per month: window return (the `days` returns ending `offset` trade dates before the month's last) and the
    excess over `days` x the mean of the month's other daily returns."""
    rows = {}
    for m, g in r.groupby(r.index.to_period("M")):
        end = len(g) - offset
        if end - days < 1:
            continue
        w = g.iloc[end - days : end]
        other = g.drop(w.index)
        rows[m] = (w.sum(), w.sum() - days * other.mean())
    return pd.DataFrame(rows, index=["raw", "excess"]).T


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def power():
    r = returns("DGS10")
    ctrl = pd.concat([months(r, k).excess for k in (5, 8, 11, 14)], axis=1)  # windows away from month-end
    sd = ctrl.std().mean()
    n = len(months(r))
    se = sd / np.sqrt(n)
    print(
        f"DGS10 {r.index[0].date()} .. {r.index[-1].date()}, months {n}; signal-free excess sd {sd:.1f} bp "
        f"(windows 5-14 trade dates before month-end), se {se:.1f}: t 3 needs {3 * se:.1f} bp net ({3 * se + COST:.1f} gross)"
    )


def run():
    r = returns("DGS10")
    e = months(r)
    net = e.excess - COST
    t = tstat(net)
    h1, h2 = net[net.index.year <= 2005].mean(), net[net.index.year >= 2006].mean()
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
        f"months {len(e)}: excess gross {e.excess.mean():+.1f} bp, net {net.mean():+.1f}, t {t:.2f}; halves {h1:+.1f} / "
        f"{h2:+.1f}; doubled {n2:+.1f}; without 2 best {nb:+.1f} -> {'KILLED ' + str(hit) if hit else 'PASSED (development)'}"
    )
    print(f"reported: raw {e.raw.mean():+.1f} (t {tstat(e.raw):.2f}); last 2 days excess {months(r, days=2).excess.mean():+.1f}; "
          f"placebo (10 earlier) excess {months(r, 10).excess.mean():+.1f} (t {tstat(months(r, 10).excess):.2f})")
    for s in ("DGS5", "DGS2"):
        x = months(returns(s)).excess
        print(f"reported: {s} excess {x.mean():+.1f} bp, t {tstat(x):.2f}")
    dec = net.groupby((net.index.year // 10) * 10).agg(["mean", "count"]).round(1)
    print("reported: net by decade", dec.to_dict("index"))


def etf(symbol, start, end):
    """Daily log return (bp) of Alpaca split-adjusted closes (ex-dividend days fall outside the window)."""
    d = pd.read_csv(f"data/cache/alpaca_1d/{symbol}.csv", usecols=["ts", "close"])
    day = pd.to_datetime(d.ts, utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None).dt.normalize()
    c = pd.Series(d.close.to_numpy(float), index=day).loc[start:end]
    return (np.log(c).diff() * 1e4).dropna()


def test():
    """One-time test (rule in knowledge/ideas.md, 29e5f32): months 2021-10 .. 2026-10."""
    start, end = "2021-09-14", "2026-10-31"
    e = months(returns("DGS10", start, end)).loc["2021-10":"2026-10"]
    net = e.excess - COST
    t = tstat(net)
    n2 = (e.excess - 2 * COST).mean()
    ief = months(etf("IEF", start, end)).loc["2021-10":"2026-10"]
    gates = {"net > 0": net.mean() > 0, "t >= 1.5": t >= 1.5, "doubled > 0": n2 > 0, "IEF raw > 0": ief.raw.mean() > 0}
    verdict = "PASSED" if all(gates.values()) else ("FALSIFIED" if net.mean() <= 0 else "NOT CONFIRMED")
    print(
        f"test months {len(e)} ({e.index[0]} .. {e.index[-1]}): excess gross {e.excess.mean():+.1f}, net {net.mean():+.1f}, "
        f"t {t:.2f}; doubled {n2:+.1f}; IEF raw {ief.raw.mean():+.1f} (t {tstat(ief.raw):.2f}, {len(ief)} months)"
    )
    print("gates:", gates, "->", verdict)
    print(f"reported: raw {e.raw.mean():+.1f}; by year {net.groupby(net.index.year).mean().round(1).to_dict()}")


if __name__ == "__main__":
    {"download": download, "power": power, "run": run, "test": test}[sys.argv[1]]()
