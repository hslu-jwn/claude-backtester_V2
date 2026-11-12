"""I-70 screen: long US500 in the option-expiration week (knowledge/ideas.md › I-70).

Rule and kills pre-registered in the card and ledger (commit d3c8161) before this script ran:
cash close (last M1 close <= 16:00 New York) of the Friday before the third Friday -> cash close of the
expiry week's last trading day (the third Friday, or the last cash close before it in that week).
Pre-sample 2010-2014 (histdata_presample) pooled with development 2015-01 to 2021-08.
Kills: net mean per week <= 0; t < 3.0; opposite halves (pre-sample vs development).
"""
import math
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from backtester.core.models import Direction
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.engine.costs import CostConfig, rollover_nights
from backtester.tools.entry_screen import load_m1

NY = ZoneInfo("America/New_York")
cfg = CostConfig()


def cash_closes(sources, start, end):
    d = load_m1("US500", sources, start, end)
    out = {}
    for open_s, c in zip(d.open_s.tolist(), d.close.tolist()):
        t = datetime.fromtimestamp(open_s + 60, UTC).astimezone(NY)
        if time(9, 30) < t.time() <= time(16, 0) and t.weekday() < 5:
            out[t.date()] = (c, open_s + 60)
    return out


closes = cash_closes(SymbolSources.single("data/cache/histdata_presample", ["US500"]), date(2010, 1, 1), date(2014, 12, 31))
closes |= cash_closes(DEFAULT_SOURCES, date(2015, 1, 1), date(2021, 8, 31))


def last_before_or_on(day):
    for k in range(5):
        if day - timedelta(days=k) in closes:
            return day - timedelta(days=k)
    return None


def trade(friday):
    """Friday-before close -> close on (or the last trading day before) `friday`."""
    a, b = last_before_or_on(friday - timedelta(days=7)), last_before_or_on(friday)
    if not a or not b or a >= b:
        return None
    (p0, t0), (p1, t1) = closes[a], closes[b]
    rt = cfg.spread("US500", price=p0) + 2 * cfg.slippage("US500", p0) + cfg.commission_price("US500", p0)
    t0d, t1d = datetime.fromtimestamp(t0, UTC), datetime.fromtimestamp(t1, UTC)
    nights = rollover_nights(t0d, t1d, cfg.for_symbol("US500").swap_triple_weekday)
    swap = cfg.swap_r_nights("US500", Direction.BULLISH, p0, nights, p0)
    gross = 1e4 * (p1 / p0 - 1)
    return friday, gross, gross - 1e4 * rt / p0 + 1e4 * swap


opex, other = [], []
f = date(2010, 1, 8)
while f <= date(2021, 8, 31):
    r = trade(f)
    if r:
        (opex if 15 <= f.day <= 21 else other).append(r)
    f += timedelta(days=7)


def stats(xs):
    xs = np.array(xs)
    return len(xs), xs.mean(), xs.mean() / (xs.std(ddof=1) / math.sqrt(len(xs)))


n, g, _ = stats([x[1] for x in opex])
_, net, t = stats([x[2] for x in opex])
pre = [x[2] for x in opex if x[0].year < 2015]
dev = [x[2] for x in opex if x[0].year >= 2015]
_, og, _ = stats([x[1] for x in other])
_, onet, _ = stats([x[2] for x in other])
print(f"opex weeks {n}: gross {g:+.1f} bp, net {net:+.1f} bp (t {t:+.2f}), positive {np.mean([x[1] > 0 for x in opex]):.0%}; "
      f"pre-sample {np.mean(pre):+.1f} bp (n {len(pre)}) / development {np.mean(dev):+.1f} bp (n {len(dev)})")
print(f"diagnostic, other weeks {len(other)}: gross {og:+.1f} bp, net {onet:+.1f} bp")
kills = [k for k, bad in (("net <= 0", net <= 0), ("t < 3.0", t < 3.0),
                          ("opposite halves", np.sign(np.mean(pre)) != np.sign(np.mean(dev)))) if bad]
print("KILLED: " + ", ".join(kills) if kills else "SURVIVES the screen")
