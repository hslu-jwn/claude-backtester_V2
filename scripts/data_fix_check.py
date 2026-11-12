"""Read-only evidence for the user's check of data fixes 13.12-13.15 (docs/data-fix-check.md).

Reads the cache only (data/cache/{histdata,mt5}/<SYM>/<year>/<date>.parquet); writes nothing.
Run: .venv/Scripts/python.exe scripts/data_fix_check.py
"""

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(__file__).resolve().parents[1] / "data" / "cache"


def day(source, sym, d):
    f = CACHE / source / sym / str(d.year) / f"{d}.parquet"
    return pd.read_parquet(f, columns=["ts", "bid_close"]) if f.exists() else None


def nth_sunday(y, m, n):
    d = date(y, m, 1) + timedelta(days=(6 - date(y, m, 1).weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def last_sunday(y, m):
    d = date(y, m + 1, 1) - timedelta(days=1)
    return d - timedelta(days=(d.weekday() + 1) % 7)


def best_lag(sym, d, lags=range(-90, 91)):
    """Minute lag (histdata vs MT5) with the highest return correlation; None if a source is missing."""
    a, b = day("histdata", sym, d), day("mt5", sym, d)
    if a is None or b is None or len(a) < 300 or len(b) < 300:
        return None
    ra = a.set_index("ts")["bid_close"].pipe(np.log).diff()
    rb = b.set_index("ts")["bid_close"].pipe(np.log).diff()
    scores = {}
    for lag in lags:
        j = pd.concat([ra, rb.shift(freq=pd.Timedelta(minutes=lag))], axis=1, join="inner").dropna()
        if len(j) > 200:
            scores[lag] = j.iloc[:, 0].corr(j.iloc[:, 1])
    return max(scores, key=scores.get) if scores else None


def clock_check():
    print("## 13.12 / 13.14 clocks: best lag histdata vs MT5 (0 = aligned)")
    for sym in ("EURUSD", "GBPUSD", "XAUUSD"):
        for y in (2015, 2016, 2017, 2018, 2019, 2020):
            gap = [nth_sunday(y, 3, 2) + timedelta(days=k) for k in (1, 2, 3, 8, 9, 10)]  # US-only DST
            gap += [last_sunday(y, 10) + timedelta(days=k) for k in (1, 2, 3)]
            normal = [date(y, 6, 13) + timedelta(days=k) for k in range(5)]
            res = {}
            for label, days in (("dst_gap", gap), ("normal", normal)):
                lags = [x for x in (best_lag(sym, d) for d in days if d.weekday() < 5) if x is not None]
                res[label] = f"{len(lags)} days, lags {sorted(set(lags))}" if lags else "no overlap"
            print(f"{sym} {y}: DST-gap weeks {res['dst_gap']}; June {res['normal']}")


def span(source, sym):
    days = sorted(p.stem for p in (CACHE / source / sym).glob("*/*.parquet"))
    return (days[0], days[-1]) if days else (None, None)


def instrument_check():
    print("\n## 13.13 wrong instruments dropped")
    for sym in ("GER40", "EU50", "DXY"):
        first, last = span("histdata", sym)
        print(f"histdata {sym}: {first} .. {last}")
    closes = []
    for f in sorted((CACHE / "histdata" / "GER40").glob("202*/*.parquet")):
        d = pd.read_parquet(f, columns=["bid_close"])
        if len(d):
            closes.append(d["bid_close"])
    s = pd.concat(closes)
    print(f"histdata GER40 2020-21 close range {s.min():.0f} .. {s.max():.0f} (Euro Stoxx level would be ~3,100)")


def mt5_days():
    print("\n## 13.14 MT5 cache: non-empty days per year (2010-2014 have no clock reference)")
    for sym in ("EURUSD", "XAUUSD", "US30", "GBPUSD"):
        row = []
        for y in range(2010, 2022):
            files = list((CACHE / "mt5" / sym / str(y)).glob("*.parquet"))
            full = sum(len(pd.read_parquet(f, columns=["ts"])) > 0 for f in files)
            row.append(f"{y}:{full}")
        print(sym, " ".join(row))


def new_year():
    print("\n## 13.15 1 January holes: bars on 31 Dec / 1 Jan / 2 Jan (histdata)")
    cases = [("XAUUSD", 2020), ("GBPUSD", 2020), ("GBPJPY", 2020), ("NAS100", 2018), ("US500", 2018),
             ("EURUSD", 2021), ("USDJPY", 2021), ("UK100", 2021)]
    for sym, y in cases:
        counts = []
        for d in (date(y - 1, 12, 31), date(y, 1, 1), date(y, 1, 2)):
            x = day("histdata", sym, d)
            counts.append("missing" if x is None else str(len(x)))
        print(f"{sym} {y - 1}-12-31 / {y}-01-01 / {y}-01-02: {' / '.join(counts)}")


def cross_check(threshold_pips=2.0):
    """MT5 GBPUSD / EURUSD vs MT5's own JPY cross, per day (median abs difference, pips)."""
    print(f"\n## MT5 FX vs its own JPY cross: days off by more than {threshold_pips} pips")

    def series(sym, d):
        x = day("mt5", sym, d)
        return None if x is None or len(x) < 300 else x.set_index("ts")["bid_close"]

    for target, a, b in (("GBPUSD", "GBPJPY", "USDJPY"), ("EURUSD", "EURJPY", "USDJPY")):
        bad, ok, d = [], 0, date(2015, 1, 1)
        while d <= date(2021, 9, 13):
            g, j, u = series(target, d), series(a, d), series(b, d)
            if all(x is not None for x in (g, j, u)):
                jn = pd.concat([g, j / u], axis=1, join="inner").dropna()
                if len(jn) > 300:
                    err = (jn.iloc[:, 0] - jn.iloc[:, 1]).abs().median() * 1e4
                    if err > threshold_pips:
                        bad.append(d)
                    else:
                        ok += 1
            d += timedelta(days=1)
        months = pd.Series([x.strftime("%Y-%m") for x in bad]).value_counts().sort_index()
        print(f"{target}: {ok} days ok, {len(bad)} off; by month {dict(months)}")


if __name__ == "__main__":
    cross_check()
    clock_check()
    instrument_check()
    mt5_days()
    new_year()
