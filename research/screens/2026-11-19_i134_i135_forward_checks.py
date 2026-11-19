"""I-134 and I-135 forward checks (rules fixed in knowledge/ideas.md › I-134, I-135, 2026-11-19; forward only).

I-134: I-105's forward days (research/forward/shelf_i105.csv) split by the previous VIX close vs its trailing 252-day
median; at each I-105 look (every 65 forward days) net(high) - net(low), Welch t; placebo = the split on the VIX
close 20 trading days later. Report only: I-105's FB-254 boundary stays its only gate.
I-135: monthly cross-asset book = mean of (S20 top-100 net / 600, S19 net / 1000, I-109 net / 87), crypto weeks
summed into their exit month; a month counts only when all three streams have it. Look every 6 months, up to 48.
Run: .venv/Scripts/python.exe research/screens/2026-11-19_i134_i135_forward_checks.py download | check | selfcheck
"""

import io
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

FORWARD = Path("research/forward")
VIX = Path("data/cache/vix_fwd/VIX.csv")
VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
LOOK_I105, LOOK_MONTHS = 65, 6
R = {"crypto_flow_top100.csv": 600.0, "crypto_carry.csv": 1000.0, "shelf_i109.csv": 87.0}


def download():
    body = subprocess.run(["curl", "-s", "-f", "-L", VIX_URL], check=True, capture_output=True, timeout=120).stdout
    d = pd.read_csv(io.BytesIO(body))
    out = pd.DataFrame({"day": pd.to_datetime(d.DATE, format="%m/%d/%Y").dt.date, "vix": d.CLOSE})
    VIX.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(VIX, index=False)
    print(f"VIX {out.day.iloc[0]} .. {out.day.iloc[-1]}, {len(out)} days")


def welch(a, b):
    return (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))


def vix_split(days, vix, shift=0):
    """days: net_bp by trade date; high = VIX close of the previous trade date (shift: that many dates later) above
    its trailing 252-day median (known at that close)."""
    high = (vix > vix.rolling(252).median()).shift(1 - shift)
    h = high.reindex(days.index)
    return days[h == True], days[h == False]  # NaN days drop out


def i134(vix):
    p = FORWARD / "shelf_i105.csv"
    if not p.exists():
        print("I-134: no forward I-105 days yet")
        return
    d = pd.read_csv(p)
    days = pd.Series(d.net_bp.to_numpy(float), index=pd.to_datetime(d.period)).sort_index()
    k = len(days) // LOOK_I105
    if k == 0:
        print(f"I-134: {len(days)} forward days, first look at {LOOK_I105}")
        return
    days = days.iloc[: k * LOOK_I105]
    hi, lo = vix_split(days, vix)
    ph, pl = vix_split(days, vix, shift=20)
    print(f"I-134 look {k} ({len(days)} days): high-VIX {hi.mean():+.1f} bp (n {len(hi)}), low {lo.mean():+.1f} "
          f"(n {len(lo)}), Welch t {welch(hi, lo):.2f} -> {'SUPPORTED' if welch(hi, lo) >= 2.0 else 'not supported'}; "
          f"placebo (VIX 20 dates later) t {welch(ph, pl):.2f}")


def monthly(name):
    d = pd.read_csv(FORWARD / name)
    if "exit_time" in d:  # crypto weekly rows -> exit month
        month = pd.to_datetime(d.exit_time, utc=True).dt.tz_localize(None).dt.to_period("M")
    else:  # shelf rows: period = month
        month = pd.PeriodIndex(d.period, freq="M")
    return pd.Series(d.net_bp.to_numpy(float) / R[name], index=month).groupby(level=0).sum()


def book(series):
    return pd.concat(series, axis=1, join="inner").mean(axis=1).sort_index()


def i135():
    missing = [n for n in R if not (FORWARD / n).exists()]
    if missing:
        print(f"I-135: forward logs missing {missing}")
        return
    b = book([monthly(n) for n in R])
    k = len(b) // LOOK_MONTHS
    if k == 0:
        print(f"I-135: {len(b)} paired months, first look at {LOOK_MONTHS}")
        return
    x = b.iloc[: k * LOOK_MONTHS]
    z = x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
    need = 2.071 / np.sqrt(k / 8)  # FB-254 c over 8 looks
    verdict = "CONFIRMED" if z >= need else ("KILLED early" if z <= -2 else "continue")
    print(f"I-135 look {k} ({len(x)} months): mean {x.mean():+.3f} R a month, z {z:.2f} (needs {need:.2f}) -> {verdict}")


def selfcheck():
    idx = pd.bdate_range("2025-01-01", periods=300)
    vix = pd.Series(np.r_[np.full(260, 10.0), np.full(40, 30.0)], index=idx)
    days = pd.Series(1.0, index=idx[-30:])
    hi, lo = vix_split(days, vix)
    assert len(hi) == 30 and len(lo) == 0  # the step is known from the first 30-close onward
    a = pd.Series([600.0, -300.0], index=pd.PeriodIndex(["2026-12", "2027-01"], freq="M"))
    b = pd.Series([1000.0], index=pd.PeriodIndex(["2026-12"], freq="M"))
    x = book([a / 600, b / 1000])
    assert len(x) == 1 and abs(x.iloc[0] - 1.0) < 1e-12
    print("selfcheck OK")


def check():
    vix = None
    if VIX.exists():
        v = pd.read_csv(VIX)
        vix = pd.Series(v.vix.to_numpy(float), index=pd.to_datetime(v.day))
    if vix is None:
        print("I-134: run `download` first (VIX history)")
    else:
        i134(vix)
    i135()


if __name__ == "__main__":
    {"download": download, "check": check, "selfcheck": selfcheck}[sys.argv[1]]()
