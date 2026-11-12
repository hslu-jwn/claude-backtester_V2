"""I-69 screen: long BTCUSD in the CME futures expiration week (knowledge/ideas.md › I-69).

Rule and kills pre-registered in the card and ledger (commit c487e2b) before this script ran:
long from Monday 00:00 UTC to Friday 15:00 UTC in each week whose Friday is the month's last Friday,
CME expiries 2018-01 to 2021-08 (development only). Net = gross - cost table round trip - swap.
Kills: net mean <= 0; t < 3.0; opposite halves (by count). Diagnostic: the same window in other weeks.
"""
import calendar
import math
from datetime import UTC, date, datetime, timedelta

import numpy as np

from backtester.core.models import Direction
from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.costs import CostConfig, rollover_nights
from backtester.tools.entry_screen import load_m1

END = date(2021, 9, 13)
d = load_m1("BTCUSD", DEFAULT_SOURCES, date(2017, 12, 1), END)
close_at = dict(zip((d.open_s + 60).tolist(), d.close.tolist()))
stamps = np.array(sorted(close_at))
cfg = CostConfig()


def last_close(at: datetime):
    """Last close at or before `at` within 3 days (weekend gaps in 2018-2020)."""
    t = int(at.timestamp())
    i = np.searchsorted(stamps, t, side="right") - 1
    return close_at[int(stamps[i])] if i >= 0 and t - stamps[i] <= 3 * 86400 else None


def week(friday: date):
    t0 = datetime.combine(friday - timedelta(days=4), datetime.min.time(), UTC)
    t1 = datetime.combine(friday, datetime.min.time(), UTC) + timedelta(hours=15)
    p0, p1 = last_close(t0), last_close(t1)
    if not p0 or not p1:
        return None
    rt = cfg.spread("BTCUSD", price=p0) + 2 * cfg.slippage("BTCUSD", p0) + cfg.commission_price("BTCUSD", p0)
    nights = rollover_nights(t0, t1, cfg.for_symbol("BTCUSD").swap_triple_weekday)
    swap = cfg.swap_r_nights("BTCUSD", Direction.BULLISH, p0, nights, p0)
    gross = 1e4 * (p1 / p0 - 1)
    return gross, gross - 1e4 * rt / p0 + 1e4 * swap


expiry, other = [], []
f = date(2018, 1, 5)
while f <= END - timedelta(days=0):
    last = max(w[calendar.FRIDAY] for w in calendar.monthcalendar(f.year, f.month) if w[calendar.FRIDAY])
    r = week(f)
    if r and f <= date(2021, 8, 31):
        (expiry if f.day == last else other).append(r)
    f += timedelta(days=7)


def stats(xs):
    xs = np.array(xs)
    return len(xs), xs.mean(), xs.mean() / (xs.std(ddof=1) / math.sqrt(len(xs)))


n, g, _ = stats([x[0] for x in expiry])
_, net, t = stats([x[1] for x in expiry])
h = len(expiry) // 2
a, b = np.mean([x[1] for x in expiry[:h]]), np.mean([x[1] for x in expiry[h:]])
_, og, _ = stats([x[0] for x in other])
_, onet, _ = stats([x[1] for x in other])
print(f"expiry weeks {n}: gross {g:+.0f} bp, net {net:+.0f} bp (t {t:+.2f}), positive {np.mean([x[0] > 0 for x in expiry]):.0%}; "
      f"halves net {a:+.0f} / {b:+.0f} bp")
print(f"diagnostic, other weeks {len(other)}: gross {og:+.0f} bp, net {onet:+.0f} bp")
kills = [k for k, bad in (("net <= 0", net <= 0), ("t < 3.0", t < 3.0), ("opposite halves", np.sign(a) != np.sign(b))) if bad]
print("KILLED: " + ", ".join(kills) if kills else "SURVIVES the screen")
