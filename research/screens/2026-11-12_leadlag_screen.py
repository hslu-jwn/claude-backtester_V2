"""Pre-build screen of the four remaining lead-lag primaries (L15-L18), development data only.

Screen rule (fixed before the run, 2026-11-12): timed hold without the stop, one position at a time,
signed gross bp per trade minus the round-trip cost (spread + 2 x slippage + commission, cost table)
minus swap for the rollovers crossed. A spec SURVIVES only if mean net bp > 0 AND the signal beats its
direction-weighted all-days control (signal dates removed) by more than 0 bp. Otherwise it stays a card.
"""
import math
from datetime import UTC, date, datetime, time, timedelta

import numpy as np

from backtester.core.models import Direction
from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.costs import CostConfig, rollover_nights
from backtester.tools.entry_screen import load_m1

DEV_END = date(2021, 9, 13)
CFG = CostConfig()


def closes(symbol, start):
    d = load_m1(symbol, DEFAULT_SOURCES, start, DEV_END)
    return dict(zip((d.open_s + 60).tolist(), d.close.tolist()))  # keyed by candle close time


def px(series, ts, forward=False, limit=3 * 86400):
    """Close at ts; forward=True takes the first close at or after ts (weekend exits)."""
    if not forward:
        return series.get(ts)
    for k in range(0, limit, 60):
        if ts + k in series:
            return series[ts + k], ts + k
    return None


def trade_bp(series, symbol, ts, sign, hold):
    entry = series.get(ts)
    got = px(series, ts + hold * 60, forward=True)
    if entry is None or got is None:
        return None
    exit_price, exit_ts = got
    costs = CFG.for_symbol(symbol)
    rt = CFG.spread(symbol, price=entry) + 2 * CFG.slippage(symbol, entry) + CFG.commission_price(symbol, entry)
    t0, t1 = datetime.fromtimestamp(ts, UTC), datetime.fromtimestamp(exit_ts, UTC)
    nights = rollover_nights(t0, t1, costs.swap_triple_weekday)
    swap_bp = 1e4 * CFG.swap_r_nights(symbol, Direction.BULLISH if sign > 0 else Direction.BEARISH, entry, nights, entry)
    gross = 1e4 * sign * (exit_price / entry - 1)
    return gross, 1e4 * rt / entry - swap_bp, exit_ts


def run(name, target, marks, signal, hold):
    """marks: candidate timestamps (sorted); signal(ts) -> +1 / -1 / 0 / None (None = not eligible)."""
    trades, ctrl = [], {1: {}, -1: {}}
    busy_until = 0
    for ts in marks:
        s = signal(ts)
        if s is None:
            continue
        for d in (1, -1):
            r = trade_bp(target_px, target, ts, d, hold)
            if r:
                ctrl[d][ts] = r[0] - r[1]
        if s and ts >= busy_until:
            r = trade_bp(target_px, target, ts, s, hold)
            if r:
                trades.append((ts, s, r[0], r[1]))
                busy_until = r[2]
    if not trades:
        print(name, "no trades"); return
    g = np.array([t[2] for t in trades]); c = np.array([t[3] for t in trades]); n = g - c
    days = {datetime.fromtimestamp(t[0], UTC).date() for t in trades}
    cm = {d: np.mean([v for k, v in ctrl[d].items() if datetime.fromtimestamp(k, UTC).date() not in days]) for d in (1, -1)}
    nl = sum(t[1] == 1 for t in trades); ns = len(trades) - nl
    control = (nl * cm[1] + ns * cm[-1]) / len(trades)
    t = n.mean() / (n.std(ddof=1) / math.sqrt(len(n))) if len(n) > 1 else float("nan")
    verdict = "SURVIVES" if n.mean() > 0 and n.mean() - control > 0 else "card"
    print(f"{name}: {len(trades)} trades (long {nl}, short {ns}); gross {g.mean():+.2f} bp, cost {c.mean():.2f} bp, "
          f"net {n.mean():+.2f} bp (t {t:+.2f}); control net {control:+.2f} bp -> diff {n.mean() - control:+.2f} bp; {verdict}")


def daily_marks(start):
    out, d = [], start
    while d <= DEV_END:
        if d.weekday() < 5:
            out.append(int(datetime.combine(d, time(21), UTC).timestamp()))
        d += timedelta(days=1)
    return out


def prev_daily(ts):
    d = datetime.fromtimestamp(ts, UTC) - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return int(d.timestamp())


def ret(series, ts, back, log=False):
    a, b = series.get(ts), series.get(back)
    if a is None or b is None or a <= 0 or b <= 0:
        return None
    return 100 * (math.log(a / b) if log else a / b - 1)


start = date(2015, 1, 2)
# L15 oil -> USDCAD, primary 2.0 % / 1440 min; short USDCAD on an oil rise
target_px, oil = closes("USDCAD", start), closes("USOIL", start)
def l15(ts):
    r = ret(oil, ts, prev_daily(ts))
    return None if r is None or ts not in target_px else (-1 if r >= 2 else 1 if r <= -2 else 0)
run("L15 oil->USDCAD", "USDCAD", daily_marks(start), l15, 1440)

# L16 USD breadth -> USDCAD, primary 0.20 % / 4 votes / 1440 min
refs = {s: closes(s, start) for s in ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF")}
def l16(ts):
    back = prev_daily(ts)
    rs = []
    for s, ser in refs.items():
        r = ret(ser, ts, back, log=True)
        if r is None:
            return None
        rs.append(r if s.startswith("USD") else -r)
    if ts not in target_px:
        return None
    m, up, dn = sum(rs) / 6, sum(r > 0 for r in rs), sum(r < 0 for r in rs)
    return 1 if up >= 4 and m >= 0.2 else -1 if dn >= 4 and m <= -0.2 else 0
run("L16 USD breadth->USDCAD", "USDCAD", daily_marks(start), l16, 1440)

# L17 gold -> silver, H1 closes 12:00-19:00 UTC, primary 0.50 % / 120 min
target_px, gold = closes("XAGUSD", start), closes("XAUUSD", start)
marks = [int(datetime.combine(start + timedelta(days=i), time(h), UTC).timestamp())
         for i in range((DEV_END - start).days + 1) for h in range(12, 20)
         if (start + timedelta(days=i)).weekday() < 5]
def l17(ts):
    r = ret(gold, ts, ts - 3600, log=True)
    return None if r is None or ts not in target_px else (1 if r >= .5 else -1 if r <= -.5 else 0)
run("L17 gold->silver", "XAGUSD", marks, l17, 120)

# L18 BTC -> ETH, every H1 close, primary 2.0 % / 240 min
cstart = date(2018, 1, 10)
target_px, btc = closes("ETHUSD", cstart), closes("BTCUSD", cstart)
marks = [int(datetime.combine(cstart, time(0), UTC).timestamp()) + 3600 * k
         for k in range(((DEV_END - cstart).days + 1) * 24)]
def l18(ts):
    r = ret(btc, ts, ts - 3600)
    return None if r is None or ts not in target_px else (1 if r >= 2 else -1 if r <= -2 else 0)
run("L18 BTC->ETH", "ETHUSD", marks, l18, 240)
