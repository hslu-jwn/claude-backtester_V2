"""Pre-build screen of the pair drafts P01 (USOIL / UKOIL) and P02 (XAUUSD / XAGUSD), primary cells.

Fixed before the run (2026-11-12, ledger P01 / P02): development data only (to 2021-09-13). Daily close =
last M1 close <= 21:00 UTC on weekdays where both legs have one. s = ln(A) - ln(B); z over the 120 prior
aligned closes; entry when z crosses outside +-2.0 (short the rich leg, long the cheap one, equal notional
50 / 50); exit at the first close where s crosses the frozen entry mean, or after 20 closes; one pair at a
time; the 1.5-ATR leg stops are NOT simulated (optimistic for gross). Pair return per unit gross notional
= 0.5 * (long leg return - short leg return). Cost = both legs' round trip (cost table) + both legs' swap
for the nights held (credits off), per unit notional.
Kills: net mean per trade <= 0; t of the net < 3.0 (family `pairs`); opposite signs in the two halves.
"""
import math
from datetime import UTC, date, datetime, time

import numpy as np

from backtester.core.models import Direction
from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.costs import CostConfig, rollover_nights
from backtester.tools.entry_screen import load_m1

END = date(2021, 9, 13)
cfg = CostConfig()


def daily(symbol):
    d = load_m1(symbol, DEFAULT_SOURCES, date(2015, 1, 1), END)
    out = {}
    for open_s, c in zip(d.open_s.tolist(), d.close.tolist()):
        t = datetime.fromtimestamp(open_s + 60, UTC)
        if t.weekday() < 5 and t.time() <= time(21, 0) and c > 0:
            out[t.date()] = (c, t)
    return out


def leg_cost(symbol, price, direction, t0, t1):
    rt = cfg.spread(symbol, price=price) + 2 * cfg.slippage(symbol, price) + cfg.commission_price(symbol, price)
    nights = rollover_nights(t0, t1, cfg.for_symbol(symbol).swap_triple_weekday)
    swap = cfg.swap_r_nights(symbol, direction, price, nights, price)  # fraction of notional, <= 0
    return rt / price - swap


def screen(a, b):
    da, db = daily(a), daily(b)
    days = sorted(set(da) & set(db))
    s = np.array([math.log(da[d][0]) - math.log(db[d][0]) for d in days])
    trades, i = [], 120
    while i < len(days):
        hist = s[i - 120:i]
        m, sd = hist.mean(), hist.std(ddof=1)
        z, zp = (s[i] - m) / sd, (s[i - 1] - m) / sd
        side = -1 if (z > 2 and zp <= 2) else 1 if (z < -2 and zp >= -2) else 0  # -1: short A / long B
        if not side:
            i += 1
            continue
        j = i + 1
        while j < len(days) and j - i < 20 and np.sign(s[j] - m) == np.sign(s[i] - m):
            j += 1
        j = min(j, len(days) - 1)
        e0, e1 = days[i], days[j]
        ra = da[e1][0] / da[e0][0] - 1
        rb = db[e1][0] / db[e0][0] - 1
        gross = 0.5 * side * (ra - rb)
        da_dir = Direction.BULLISH if side > 0 else Direction.BEARISH
        db_dir = Direction.BEARISH if side > 0 else Direction.BULLISH
        cost = 0.5 * leg_cost(a, da[e0][0], da_dir, da[e0][1], da[e1][1]) + 0.5 * leg_cost(b, db[e0][0], db_dir, db[e0][1], db[e1][1])
        trades.append((e0, 1e4 * gross, 1e4 * (gross - cost), j - i))
        i = j + 1
    g = np.array([t[1] for t in trades]); n = np.array([t[2] for t in trades])
    t = n.mean() / (n.std(ddof=1) / math.sqrt(len(n))) if len(n) > 1 else float("nan")
    h = len(n) // 2
    print(f"{a}/{b}: {len(n)} trades, hold {np.mean([x[3] for x in trades]):.1f} d; gross {g.mean():+.1f} bp, "
          f"net {n.mean():+.1f} bp (t {t:+.2f}); halves {n[:h].mean():+.1f} / {n[h:].mean():+.1f} bp")
    kills = [k for k, bad in (("net <= 0", n.mean() <= 0), ("t < 3.0", t < 3.0),
                              ("opposite halves", np.sign(n[:h].mean()) != np.sign(n[h:].mean()))) if bad]
    print("  KILLED: " + ", ".join(kills) if kills else "  SURVIVES the screen")


screen("USOIL", "UKOIL")
screen("XAUUSD", "XAGUSD")
