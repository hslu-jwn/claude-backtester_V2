"""I-109 diagnostic on 10-year Treasury futures prices (venue check for HANDOFF Open 1; not a new look, the test is spent).

Yahoo continuous front contract ZN=F daily closes (2000-09+) -> data/cache/yahoo_futures/ZN.csv. Same window and excess
statistic as I-109 (last 3 trade dates of each month), compared with the registered DGS10 statistic month by month.
Run: .venv/Scripts/python.exe research/screens/2026-11-18_i109_zn_futures_check.py download | run
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "i109", Path(__file__).parent / "2026-11-17_i109_treasury_month_end_screen.py"
)
i109 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i109)

ROOT = Path("data/cache/yahoo_futures")
URL = "https://query1.finance.yahoo.com/v8/finance/chart/ZN%3DF?period1=946684800&period2={b}&interval=1d"
JUMP = 150.0  # bp: a daily move this large is flagged as a possible contract roll in the continuous series


def download():
    ROOT.mkdir(parents=True, exist_ok=True)
    b = int(pd.Timestamp.now().timestamp())
    raw = subprocess.run(
        ["curl", "-s", "-f", "-A", "Mozilla/5.0", URL.format(b=b)],
        capture_output=True,
        check=True,
        timeout=120,
    )
    res = json.loads(raw.stdout)["chart"]["result"][0]
    day = (
        pd.to_datetime(res["timestamp"], unit="s")
        .tz_localize("UTC")
        .tz_convert("America/New_York")
        .normalize()
    )
    c = pd.DataFrame(
        {"day": day.tz_localize(None), "close": res["indicators"]["quote"][0]["close"]}
    ).dropna()
    c.drop_duplicates("day", keep="last").to_csv(ROOT / "ZN.csv", index=False)
    print(len(c), c.day.min().date(), c.day.max().date())


def zn(start, end):
    c = pd.read_csv(ROOT / "ZN.csv", parse_dates=["day"]).set_index("day")["close"].loc[start:end]
    return (np.log(c).diff() * 1e4).dropna(), c


def period(name, start, end, first, last):
    r, close = zn(start, end)
    jumps = r[r.abs() > JUMP]
    z = i109.months(r).loc[first:last]
    d = i109.months(i109.returns("DGS10", start, end)).loc[first:last]
    both = z.add_suffix("_zn").join(d.add_suffix("_dgs"), how="inner")
    hit = {
        m
        for m in z.index
        for j in jumps.index
        if j.to_period("M") == m and j >= r[r.index.to_period("M") == m].index[-3]
    }
    clean = both.drop([m for m in hit if m in both.index])
    usd = (
        both.excess_zn.mean() * close.mean() * 0.1
    )  # 1 bp of price on one ZN contract ($1,000 a point) = price * $0.10
    print(
        f"{name}: {len(both)} months; ZN raw {both.raw_zn.mean():+.1f} bp (t {i109.tstat(both.raw_zn):.2f}), "
        f"excess {both.excess_zn.mean():+.1f} (t {i109.tstat(both.excess_zn):.2f}), net of 2 bp {both.excess_zn.mean() - 2:+.1f}; "
        f"DGS10 excess {both.excess_dgs.mean():+.1f} (t {i109.tstat(both.excess_dgs):.2f}); "
        f"corr excess {both.excess_zn.corr(both.excess_dgs):.2f}; ratio ZN/DGS10 {both.excess_zn.mean() / both.excess_dgs.mean():.2f}"
    )
    print(
        f"  daily moves > {JUMP:.0f} bp: {len(jumps)}; months with one inside the window: {len(hit)}; "
        f"without them excess {clean.excess_zn.mean():+.1f} (t {i109.tstat(clean.excess_zn):.2f}); "
        f"~${usd:,.0f} gross per contract per month-end"
    )
    return both


def run():
    dev = period("development 2000-10 .. 2021-08", "2000-09-21", "2021-09-13", "2000-10", "2021-08")
    test = period("test 2021-10 .. 2026-10", "2021-09-14", "2026-10-31", "2021-10", "2026-10")
    allm = pd.concat([dev, test])
    print(
        f"all {len(allm)} months: ZN excess {allm.excess_zn.mean():+.1f} bp (t {i109.tstat(allm.excess_zn):.2f}); "
        f"by quarter-month (roll months Feb/May/Aug/Nov vs others): "
        f"{allm[allm.index.month.isin([2, 5, 8, 11])].excess_zn.mean():+.1f} / {allm[~allm.index.month.isin([2, 5, 8, 11])].excess_zn.mean():+.1f}"
    )


if __name__ == "__main__":
    {"download": download, "run": run}[sys.argv[1]]()
