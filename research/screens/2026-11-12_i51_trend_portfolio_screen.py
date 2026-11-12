"""I-51 screen: diversified daily trend portfolio (knowledge/ideas.md › I-51, review D3).

Fixed before the run (2026-11-12), development data only (every cached day before 2021-09-14; MT5 days
preferred, histdata otherwise, as DEFAULT_SOURCES reads them):
- Universe: every symbol with a cost-table entry and >= 13 month-ends of data (crypto included).
- Daily close = last M1 close of the UTC weekday. Month-end close = last daily close of the month.
- At each month-end m: sign of the 12-month return close(m) / close(m-12) - 1; volatility = std of the
  last 63 daily log returns x sqrt(252); weight = (0.10 / vol) / N_active (one portfolio, equal risk).
- Held for month m+1 (return close(m+1) / close(m) - 1); a month whose end is after 2021-09-13 is not used.
- Costs per unit notional: half the round trip (spread + 2 x slippage + commission, cost table) on every
  change of the signed weight; swap for every rollover night held, credits OFF (CostConfig default, B5).
- Kills (card): net annualised Sharpe < 0.4; the 3 best symbols bring more than half the net profit;
  the result needs swap credits (credits are off here, so a pass never relies on them).
"""
import math
import sys
from datetime import UTC, date, datetime
from itertools import pairwise

import numpy as np
import pandas as pd

from backtester.core.models import Direction
from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.costs import CostConfig, rollover_nights
from backtester.tools.entry_screen import load_m1

END = date(2021, 9, 13)
cfg = CostConfig()
symbols = [s for s in DEFAULT_SOURCES.symbols if s in cfg.symbols]

monthly = {}
for s in symbols:
    days = [d for d in DEFAULT_SOURCES.cached_days(s) if d <= END]
    if len(days) < 300:
        continue
    d = load_m1(s, DEFAULT_SOURCES, days[0], END)
    ts = pd.to_datetime(d.open_s + 60, unit="s", utc=True)
    daily = pd.Series(d.close, index=ts).groupby(ts.date).last()
    daily.index = pd.to_datetime(daily.index)
    daily = daily[daily.index.weekday < 5]
    lr = np.log(daily).diff()
    me = daily.groupby(daily.index.to_period("M")).tail(1)
    vol = lr.rolling(63).std().reindex(me.index) * math.sqrt(252)
    monthly[s] = pd.DataFrame({"close": me.values, "vol": vol.values},
                              index=me.index.to_period("M"))
    print(s, days[0], len(me), "month-ends", file=sys.stderr)

months = sorted(set().union(*[set(f.index) for f in monthly.values()]))
last_full = pd.Period(END, "M") - 1  # August 2021: its end is the last month-end before the split
months = [m for m in months if m <= last_full]
port, contrib, prev_w = [], {s: 0.0 for s in monthly}, {s: 0.0 for s in monthly}
parts = {"gross": 0.0, "swap": 0.0, "spread": 0.0}
gross_m = []
for m, nxt in pairwise(months):
    active = {}
    for s, f in monthly.items():
        if m in f.index and nxt in f.index and (m - 12) in f.index and f.loc[m, "vol"] > 0:
            sign = 1.0 if f.loc[m, "close"] > f.loc[m - 12, "close"] else -1.0
            active[s] = sign * 0.10 / f.loc[m, "vol"]
    if not active:
        continue
    total = 0.0
    g_month = 0.0
    for s, f in monthly.items():
        w = active.get(s, 0.0) / len(active)
        pnl = 0.0
        if w:
            p0, p1 = f.loc[m, "close"], f.loc[nxt, "close"]
            t0 = datetime(m.year, m.month, 1, tzinfo=UTC) + pd.offsets.MonthEnd(0)
            t1 = datetime(nxt.year, nxt.month, 1, tzinfo=UTC) + pd.offsets.MonthEnd(0)
            nights = rollover_nights(t0.to_pydatetime(), t1.to_pydatetime(), cfg.for_symbol(s).swap_triple_weekday)
            direction = Direction.BULLISH if w > 0 else Direction.BEARISH
            swap = cfg.swap_r_nights(s, direction, p0, nights, p0)  # fraction of notional, credits off
            pnl = w * (p1 / p0 - 1) + abs(w) * swap
            parts["gross"] += w * (p1 / p0 - 1); parts["swap"] += abs(w) * swap; g_month += w * (p1 / p0 - 1)
        price = f.loc[m, "close"] if m in f.index else None
        if price and (w or prev_w[s]):
            rt = cfg.spread(s, price=price) + 2 * cfg.slippage(s, price) + cfg.commission_price(s, price)
            pnl -= abs(w - prev_w[s]) * rt / 2 / price
            parts["spread"] -= abs(w - prev_w[s]) * rt / 2 / price
        prev_w[s] = w
        contrib[s] += pnl
        total += pnl
    port.append((str(nxt), total, len(active)))
    gross_m.append(g_month)

r = np.array([p[1] for p in port])
sharpe = r.mean() / r.std(ddof=1) * math.sqrt(12)
half = len(r) // 2
top = sorted(contrib.items(), key=lambda kv: kv[1], reverse=True)
net = sum(contrib.values())
top3 = sum(v for _, v in top[:3])
print(f"symbols {len(monthly)}; months {len(r)} ({port[0][0]}..{port[-1][0]}); active {min(p[2] for p in port)}-{max(p[2] for p in port)}")
print(f"net mean {1e4 * r.mean():+.1f} bp / month, ann. vol {r.std(ddof=1) * math.sqrt(12):.1%}, Sharpe {sharpe:+.2f}; "
      f"halves Sharpe {r[:half].mean() / r[:half].std(ddof=1) * math.sqrt(12):+.2f} / {r[half:].mean() / r[half:].std(ddof=1) * math.sqrt(12):+.2f}")
print("top 3:", [(s, f"{1e4 * v:+.0f} bp") for s, v in top[:3]], f"= {top3 / net:.0%} of net" if net > 0 else "(net <= 0)")
g = np.array(gross_m)
print(f"diagnostic (not a gate): gross Sharpe {g.mean() / g.std(ddof=1) * math.sqrt(12):+.2f}; totals bp gross {1e4 * parts['gross']:+.0f}, swap {1e4 * parts['swap']:+.0f}, spread {1e4 * parts['spread']:+.0f}")
print("bottom 3:", [(s, f"{1e4 * v:+.0f} bp") for s, v in top[-3:]])
kills = [k for k, bad in (("Sharpe < 0.4", sharpe < 0.4), ("3 symbols > half the profit", net <= 0 or top3 > net / 2)) if bad]
print("KILLED: " + ", ".join(kills) if kills else "SURVIVES the screen")
