"""I-67 screen: month-end rebalancing with a conditional sign (knowledge/ideas.md › I-67, review D2).

Fixed before the run (2026-11-12), development data only (US500, 2015-01-02 to 2021-09-13):
- Daily close = the last US500 M1 candle closing in (09:30, 16:00] New York on that day (early closes kept).
  Trading days = days with such a close. T = the month's last trading day; T-k = k trading days earlier.
- Past = close(T-9) -> close(T-4) (days T-8..T-4); trade = close(T-4) -> close(T-1) (days T-3..T-1).
- Signed = -sign(past) x trade return (funds sell after a strong window, buy after a weak one).
- Kill (card): signed mean < 15 bp, t < 2, or opposite signs in the two halves. Settlement shift declared:
  the window is NOT shifted for T+2 (2017-09-05); the halves split at 2017-09-05, so the kill on halves
  also covers the shift. Net = signed minus round trip (cost table) minus swap for the nights held.
"""
import math
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

import numpy as np

from backtester.core.models import Direction
from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.costs import CostConfig, rollover_nights
from backtester.tools.entry_screen import load_m1

NY = ZoneInfo("America/New_York")
START, END, SPLIT = date(2015, 1, 2), date(2021, 9, 13), date(2017, 9, 5)

d = load_m1("US500", DEFAULT_SOURCES, START, END)
closes = {}
for open_s, c in zip(d.open_s.tolist(), d.close.tolist()):
    t = datetime.fromtimestamp(open_s + 60, UTC).astimezone(NY)
    if time(9, 30) < t.time() <= time(16, 0) and t.weekday() < 5:
        closes[t.date()] = (c, open_s + 60)  # later candles overwrite: last close <= 16:00
days = sorted(closes)
by_month = {}
for day in days:
    by_month.setdefault((day.year, day.month), []).append(day)

cfg = CostConfig()
rows = []
for (y, m), ds in sorted(by_month.items()):
    if len(ds) < 10 or (y, m) == (END.year, END.month):  # incomplete first / last month
        continue
    t9, t4, t1 = ds[-10], ds[-5], ds[-2]
    past = closes[t4][0] / closes[t9][0] - 1
    if past == 0:
        continue
    sign = -1 if past > 0 else 1
    entry, exit_ = closes[t4][0], closes[t1][0]
    signed = 1e4 * sign * (exit_ / entry - 1)
    rt = cfg.spread("US500", price=entry) + 2 * cfg.slippage("US500", entry) + cfg.commission_price("US500", entry)
    t0, t1s = (datetime.fromtimestamp(closes[x][1], UTC) for x in (t4, t1))
    nights = rollover_nights(t0, t1s, cfg.for_symbol("US500").swap_triple_weekday)
    swap = 1e4 * cfg.swap_r_nights("US500", Direction.BULLISH if sign > 0 else Direction.BEARISH, entry, nights, entry)
    rows.append((t4, sign, signed, signed - 1e4 * rt / entry + swap))


def stats(xs):
    xs = np.array(xs)
    return len(xs), xs.mean(), xs.mean() / (xs.std(ddof=1) / math.sqrt(len(xs)))


n, mean, t = stats([r[2] for r in rows])
h1 = stats([r[2] for r in rows if r[0] < SPLIT])
h2 = stats([r[2] for r in rows if r[0] >= SPLIT])
nn, nmean, nt = stats([r[3] for r in rows])
print(f"months {n} (long {sum(r[1] > 0 for r in rows)}, short {sum(r[1] < 0 for r in rows)})")
print(f"signed gross {mean:+.1f} bp (t {t:+.2f}); halves {h1[1]:+.1f} bp (n {h1[0]}, t {h1[2]:+.2f}) / "
      f"{h2[1]:+.1f} bp (n {h2[0]}, t {h2[2]:+.2f}); net {nmean:+.1f} bp (t {nt:+.2f})")
kills = [k for k, bad in (("mean < 15 bp", mean < 15), ("t < 2", t < 2),
                          ("opposite halves", np.sign(h1[1]) != np.sign(h2[1]))) if bad]
print("KILLED: " + ", ".join(kills) if kills else "SURVIVES the screen")
