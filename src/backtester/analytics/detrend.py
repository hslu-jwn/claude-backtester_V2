"""Post-run trend diagnostics. Spec: research-runner.md > Skill vs trend, and bounds."""

import itertools
from datetime import UTC, datetime, time, timedelta
from math import isfinite

from backtester.analytics.daily import _field, _midnight, weekdays
from backtester.core.models import Direction, Timeframe


def _intervals(t):
    if (
        t.entry_time.utcoffset() is None
        or t.exit_time.utcoffset() is None
        or t.exit_time < t.entry_time
    ):
        raise ValueError("invalid trade times")
    if t.direction not in (Direction.BULLISH, Direction.BEARISH, "long", "short"):
        raise ValueError("invalid direction")
    sign = 1 if t.direction in (Direction.BULLISH, "long") else -1
    parts = []
    for p in getattr(t, "parts", ()):
        at = _field(p, "time")
        at = datetime.fromisoformat(at) if isinstance(at, str) else at
        share = _field(p, "share")
        if (
            at.utcoffset() is None
            or not t.entry_time <= at <= t.exit_time
            or not isfinite(share)
            or share <= 0
        ):
            raise ValueError("invalid partial exit")
        parts.append((at, share))
    if sum(s for _, s in parts) > 1 + 1e-9:
        raise ValueError("partial shares exceed one")
    remaining, at = 1.0, t.entry_time
    for until, share in sorted(parts) + [(t.exit_time, 0)]:
        yield at, until, sign * max(0, remaining)
        at, remaining = until, remaining - share


def detrend(trades, drifts):
    """Pure per-symbol and total R summaries given price drift per elapsed second."""
    groups = {}
    per_trade = []
    for t in trades:
        risk = abs(t.entry - t.initial_stop)
        weight = getattr(t, "risk_weight", 1.0)
        if (
            not all(isfinite(v) for v in (t.entry, t.initial_stop, risk, t.r_net, weight))
            or risk <= 0
            or weight <= 0
        ):
            raise ValueError("invalid trade price, stop distance or R")
        exposure = sum((b - a).total_seconds() * size for a, b, size in _intervals(t))
        drift = drifts.get(t.symbol)
        if drift is not None and not isfinite(drift):
            raise ValueError("nonfinite drift")
        row = groups.setdefault(t.symbol, {"trades": 0, "net_r": 0.0, "trend_r": 0.0})
        row["trades"] += 1
        row["net_r"] += t.r_net
        if drift is None:
            row["trend_r"] = None
        elif row["trend_r"] is not None:
            row["trend_r"] += drift * exposure / risk * weight
        trend_r = drift * exposure / risk * weight if drift is not None else None
        per_trade.append(
            {
                "symbol": t.symbol,
                "net_r": t.r_net,
                "trend_r": trend_r,
                "detrended_r": t.r_net - trend_r if trend_r is not None else None,
            }
        )
    total = {
        "trades": sum(r["trades"] for r in groups.values()),
        "net_r": sum(r["net_r"] for r in groups.values()),
        "trend_r": sum(r["trend_r"] for r in groups.values())
        if all(r["trend_r"] is not None for r in groups.values())
        else None,
    }
    for row in [*groups.values(), total]:
        row["avg_r"] = row["net_r"] / row["trades"] if row["trades"] else None
        row["detrended_net_r"] = (
            row["net_r"] - row["trend_r"] if row["trend_r"] is not None else None
        )
        row["detrended_avg_r"] = (
            row["detrended_net_r"] / row["trades"]
            if row["trades"] and row["trend_r"] is not None
            else None
        )
    return {"symbols": groups, "total": total, "trades": per_trade}


def position_bias(trades, start, end, symbols=()):
    """Time-integrated clipped net remaining share, per symbol, Prague weekdays."""
    events = {s: {} for s in symbols}
    for t in trades:
        changes = events.setdefault(t.symbol, {})
        for a, b, size in _intervals(t):
            changes[a] = changes.get(a, 0) + size
            changes[b] = changes.get(b, 0) - size
    days = weekdays(start, end)
    denominator = sum(
        (_midnight(d + timedelta(days=1)) - _midnight(d)).total_seconds() for d in days
    )
    out = {}
    for symbol, changes in events.items():
        long = short = 0.0
        for d in days:
            left, right = _midnight(d), _midnight(d + timedelta(days=1))
            cuts = [left, *sorted(at for at in changes if left < at < right), right]
            size = sum(v for at, v in changes.items() if at <= left)
            for a, b in itertools.pairwise(cuts):
                span = (b - a).total_seconds()
                long += min(1, max(0, size)) * span
                short += min(1, max(0, -size)) * span
                size += changes.get(b, 0)
        out[symbol] = (
            {
                "long": long / denominator,
                "short": short / denominator,
                "flat": max(0, 1 - (long + short) / denominator),
            }
            if denominator
            else {"long": None, "short": None, "flat": None}
        )
    total = {
        k: sum(r[k] for r in out.values()) / len(out) if out and denominator else None
        for k in ("long", "short", "flat")
    }
    return {"symbols": out, "total": total}


def load_drifts(symbols, start, end, sources):
    """One cached M1 read per symbol/consecutive-day block; sort endpoint closes."""
    result = {}
    for symbol in symbols:
        blocks = []
        for day in sorted({d for d in sources.cached_days(symbol) if start <= d <= end}):
            if blocks and day == blocks[-1][1] + timedelta(days=1):
                blocks[-1][1] = day
            else:
                blocks.append([day, day])
        first = last = None
        adapter = sources.adapter(symbol)
        for a, b in blocks:
            frame = adapter.fetch_frame(
                symbol,
                Timeframe.M1,
                datetime.combine(a, time(), UTC),
                datetime.combine(b + timedelta(days=1), time(), UTC),
            )
            if frame.empty:
                continue
            frame = frame.sort_values("ts")
            for i in (0, -1):
                at, price = frame["ts"].iloc[i], float(frame["close"].iloc[i])
                if not isfinite(price):
                    raise ValueError("nonfinite cached close")
                if first is None or at < first[0]:
                    first = (at, price)
                if last is None or at > last[0]:
                    last = (at, price)
        result[symbol] = (
            (last[1] - first[1]) / (last[0] - first[0]).total_seconds()
            if first and last[0] > first[0]
            else None
        )
    return result
