"""I-109 IEF 16:00 exit diagnostic (R5; pre-registered in knowledge/ideas.md › I-109 implementation notes, 2026-11-26).

On each month's last Treasury trade date: IEF return from the close of the 14:59 ET 1-minute bar to the close of the
15:59 ET bar (Alpaca SIP, data/cache/alpaca/IEF), months 2016-01 .. 2021-08. Placebo: the same slice on the 10th trade
date before each month's end. Gate: mean >= +3 bp and t >= 2.0 -> register a paper variant "exit at 16:00"; else
keep 15:00. One look.
Run: .venv/Scripts/python.exe research/screens/2026-11-26_i109_ief_4pm_diagnostic.py
"""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "cal", "research/screens/2026-11-19_i109_order_calendar.py"
)
cal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cal)


def bars():
    d = pd.concat(pd.read_csv(f) for f in sorted(Path("data/cache/alpaca/IEF").glob("*.csv")))
    d.index = pd.to_datetime(d.ts, utc=True).dt.tz_convert("America/New_York")
    return d.close.sort_index()


def at(c, day, hhmm):
    """Close of the last bar opening at or before day hh:mm ET (bars of that day only)."""
    x = c[(c.index.normalize() == day) & (c.index <= day + pd.Timedelta(hhmm))]
    return x.iloc[-1] if len(x) else np.nan


def slices(c, offset):
    out = {}
    for m in pd.period_range("2016-01", "2021-08", freq="M"):
        d = cal.trade_dates(m.start_time, m.end_time)
        day = d[-1 - offset].tz_localize("America/New_York")
        out[str(m)] = (at(c, day, "15:59:00") / at(c, day, "14:59:00") - 1) * 1e4
    return pd.Series(out).dropna()


def t(x):
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def main():
    c = bars()
    s, pl = slices(c, 0), slices(c, 10)
    ok = s.mean() >= 3 and t(s) >= 2.0
    print(
        f"last trade date 15:00 -> 16:00: {len(s)} months, mean {s.mean():+.2f} bp, t {t(s):.2f} -> "
        f"{'PASS: register exit-16:00 paper variant' if ok else 'FAIL: keep 15:00'}"
    )
    print(f"placebo (10th trade date before): mean {pl.mean():+.2f}, t {t(pl):.2f}")
    h1, h2 = s[s.index < "2019-01"], s[s.index >= "2019-01"]
    print(f"halves: 2016-2018 {h1.mean():+.2f} ({len(h1)}), 2019-2021 {h2.mean():+.2f} ({len(h2)})")


if __name__ == "__main__":
    main()
