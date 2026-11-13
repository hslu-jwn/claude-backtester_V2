"""Read-only check of the NY-hour-18 spread (research-log 2026-11-13, rollover hour).

Live fill probe buys at XX:00 New York (fills.csv of 2026-11-09): spread paid at the fill vs the
default table at the fill time ("now") and one second earlier ("prev", the hour of the bar that
just closed). Writes nothing. Run: PYTHONPATH=src .venv/Scripts/python.exe scripts/rollover_spread_check.py
"""
from datetime import timedelta

import numpy as np
import pandas as pd

from backtester.engine.costs import default_spread_table

tab = default_spread_table()
f = pd.read_csv("results/fill_report_2026-11-09/fills.csv")
f = f[(f.kind == "entry") & (f.side == "buy") & f.symbol.isin(list(tab.values))].copy()
t = pd.to_datetime(f.time_utc, utc=True)
f["now"] = [tab.spread_at(s, x.to_pydatetime()) for s, x in zip(f.symbol, t)]
f["prev"] = [tab.spread_at(s, x.to_pydatetime() - timedelta(seconds=1)) for s, x in zip(f.symbol, t)]
ny = t.dt.tz_convert("America/New_York"); f["h"] = ny.dt.hour; f["m"] = ny.dt.minute
f = f[(f.m == 0) & (f.slip_raw > 0)]
for name, g in (("all :00", f), (":00 without 18", f[f.h != 18]), ("18:00", f[f.h == 18])):
    for col in ("now", "prev"):
        r = g.slip_raw / g[col]
        print(f"{name:16s} {col:5s} n={len(g):3d} paid/model mean {r.mean():6.2f} median {r.median():5.2f} |log| {np.abs(np.log(r)).median():.2f}")
print(f[f.h==18].groupby("symbol").apply(lambda g: pd.Series({"n":len(g),"paid":g.slip_raw.mean(),"h18":g.now.mean(),"h17":g.prev.mean()})))
