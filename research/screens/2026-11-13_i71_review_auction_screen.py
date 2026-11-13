"""I-71 screen: short UK100 into the closing auction on index-review days (knowledge/ideas.md › I-71).

Rule and kills pre-registered in the card and ledger (commit 2365c6d) before this script ran:
short at the close of the 15:29 London M1 bar, cover at the close of the 16:35 bar; event days = third
Friday of Mar / Jun / Sep / Dec and the last weekday of Feb / May / Aug / Nov (a day without both bars is
skipped). Pre-sample 2010-2014 (histdata_presample) pooled with development 2015-01 to 2021-09-13.
Net = gross bp - (spread at the entry via fill_spread_time + 2 x slippage) in bp. No commission, no swap.
Kills: net mean <= 0; t < 3.0; opposite signs pre-sample vs development.
Diagnostic (not a gate): the same window on every other weekday.
Run: PYTHONPATH=src .venv/Scripts/python.exe research/screens/2026-11-13_i71_review_auction_screen.py
"""
import math
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.engine.costs import CostConfig, fill_spread_time
from backtester.tools.entry_screen import load_m1

LONDON = ZoneInfo("Europe/London")
SYMBOL = "UK100"
ENTRY, EXIT = (15, 29), (16, 35)  # London M1 bars whose closes are used
cfg = CostConfig()


def window_closes(sources, start, end):
    """{London date: {bar (h, m): (close, close time UTC)}} for the two bars."""
    d = load_m1(SYMBOL, sources, start, end)
    out = {}
    for open_s, c in zip(d.open_s.tolist(), d.close.tolist()):
        t = datetime.fromtimestamp(open_s, UTC).astimezone(LONDON)
        if (t.hour, t.minute) in (ENTRY, EXIT) and t.weekday() < 5:
            out.setdefault(t.date(), {})[(t.hour, t.minute)] = (c, datetime.fromtimestamp(open_s + 60, UTC))
    return out


bars = window_closes(SymbolSources.single("data/cache/histdata_presample", [SYMBOL]), date(2010, 1, 1), date(2014, 12, 31))
bars |= window_closes(DEFAULT_SOURCES, date(2015, 1, 1), date(2021, 9, 13))


def third_friday(y, m):
    d = date(y, m, 15)
    return d + timedelta(days=(4 - d.weekday()) % 7)


def last_weekday(y, m):
    d = date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)
    while d.weekday() > 4:
        d -= timedelta(days=1)
    return d


events = set()
for y in range(2010, 2022):
    events |= {third_friday(y, m) for m in (3, 6, 9, 12)} | {last_weekday(y, m) for m in (2, 5, 8, 11)}


def short(day):
    b = bars.get(day, {})
    if ENTRY not in b or EXIT not in b:
        return None
    (p0, t0), (p1, _) = b[ENTRY], b[EXIT]
    rt = cfg.spread(SYMBOL, fill_spread_time(t0), p0) + 2 * cfg.slippage(SYMBOL, p0)
    gross = -1e4 * (p1 / p0 - 1)
    return day, gross, gross - 1e4 * rt / p0


def stats(xs):
    xs = np.array(xs)
    return len(xs), xs.mean(), xs.mean() / (xs.std(ddof=1) / math.sqrt(len(xs)))


ev = [r for d in sorted(events) if (r := short(d))]
other = [r for d in sorted(bars) if d not in events and (r := short(d))]
missing = sorted(d for d in events if date(2010, 1, 1) <= d <= date(2021, 9, 13) and not short(d))
n, g, _ = stats([x[1] for x in ev])
_, net, t = stats([x[2] for x in ev])
pre = [x[2] for x in ev if x[0].year < 2015]
dev = [x[2] for x in ev if x[0].year >= 2015]
print(f"event days {n} (missing {len(missing)}): gross {g:+.2f} bp, net {net:+.2f} bp (t {t:+.2f}), "
      f"positive {np.mean([x[1] > 0 for x in ev]):.0%}; pre-sample {np.mean(pre):+.2f} bp (n {len(pre)}) / "
      f"development {np.mean(dev):+.2f} bp (n {len(dev)})")
qe = [x[2] for x in ev if x[0].month in (3, 6, 9, 12)]
ms = [x[2] for x in ev if x[0].month in (2, 5, 8, 11)]
print(f"by source: FTSE/STOXX third Fridays {np.mean(qe):+.2f} bp (n {len(qe)}), MSCI month ends {np.mean(ms):+.2f} bp (n {len(ms)})")
on, og, _ = stats([x[1] for x in other])
_, onet, ot = stats([x[2] for x in other])
print(f"diagnostic, other weekdays {on}: gross {og:+.2f} bp, net {onet:+.2f} bp (t {ot:+.2f})")
by_year = {}
for d, _, x in ev:
    by_year.setdefault(d.year, []).append(x)
print("net by year:", {y: round(float(np.mean(v)), 1) for y, v in sorted(by_year.items())})
kills = [k for k, hit in (("net <= 0", net <= 0), ("t < 3.0", t < 3.0),
                          ("opposite halves", np.sign(np.mean(pre)) != np.sign(np.mean(dev)))) if hit]
print("VERDICT:", "KILLED (" + "; ".join(kills) + ")" if kills else "SURVIVES the screen")
