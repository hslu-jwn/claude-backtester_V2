"""Daily net R of a trade list: the one shared helper of the trial log, the Monte Carlo report and
the portfolio tool.

Spec: risk-management.md > Trial log and deflated Sharpe > Daily Sharpe (ROADMAP 12.13). A day is a
weekday of the period, cut at midnight `Europe/Prague`; a trade belongs to its exit day; a trade
exiting on a weekend moves to the next weekday, one outside the period to the first / last day;
days without trades are 0. `risk.monte_carlo.build_days` (kind A) follows the same rule (a test keeps
the two equal).
"""

from __future__ import annotations

from bisect import bisect_left
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, time, timedelta
from math import isfinite
from zoneinfo import ZoneInfo

import numpy as np

from backtester.core.models import Direction, Timeframe

PRAGUE = ZoneInfo("Europe/Prague")


def weekdays(start: date, end: date) -> list[date]:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def daily_net_r(trades: Sequence, start: date, end: date) -> np.ndarray:
    """Net R per weekday of start..end (trades need `exit_time` tz-aware and `r_net`)."""
    days = weekdays(start, end)
    out = np.zeros(len(days))
    if not days:
        return out
    index = {day: i for i, day in enumerate(days)}
    for t in trades:
        day = t.exit_time.astimezone(PRAGUE).date()
        i = index.get(day)
        if i is None:
            i = min(bisect_left(days, day), len(days) - 1)
        out[i] += t.r_net
    return out


def _midnight(day: date) -> datetime:
    return datetime.combine(day, time(), PRAGUE).astimezone(UTC)


def _cuts(trade):
    day = trade.entry_time.astimezone(PRAGUE).date() + timedelta(days=1)
    while (cut := _midnight(day)) <= trade.exit_time:
        yield cut
        day += timedelta(days=1)


def _field(part, key, default=None):
    return part.get(key, default) if isinstance(part, Mapping) else getattr(part, key, default)


def daily_mtm_from_marks(
    trades: Sequence, start: date, end: date, marks: Mapping[tuple[str, datetime], float]
) -> tuple[np.ndarray, np.ndarray]:
    """Daily (net R, signed time-weighted position), with bid marks at Prague cuts.

    Spec: risk-management.md > Trial log and deflated Sharpe > Marked-to-market daily series.
    All R inputs are signed/weighted as saved. Marks never contain future candles.
    """
    days = weekdays(start, end)
    net, position = np.zeros(len(days)), np.zeros(len(days))
    if not days:
        return net, position
    position_index = {day: i for i, day in enumerate(days)}

    def index(day):
        return min(bisect_left(days, day), len(days) - 1)

    for t in trades:
        entry_time, exit_time = t.entry_time, t.exit_time
        if entry_time.utcoffset() is None or exit_time.utcoffset() is None:
            raise ValueError("trade times must be timezone-aware")
        if exit_time < entry_time:
            raise ValueError("trade exit precedes entry")
        sign = 1 if t.direction in (Direction.BULLISH, "long") else -1
        if t.direction not in (Direction.BULLISH, Direction.BEARISH, "long", "short"):
            raise ValueError("invalid trade direction")
        weight = getattr(t, "risk_weight", 1.0)
        # Intraday trades need no prices; their complete result is already known at exit.
        cuts = list(_cuts(t))
        commission = getattr(t, "commission_r", 0.0)
        carry = getattr(t, "swap_r", 0.0) + getattr(t, "funding_r", 0.0)
        if not all(isfinite(v) for v in (t.r_net, commission, carry, weight)):
            raise ValueError("nonfinite trade R")
        net[index(entry_time.astimezone(PRAGUE).date())] -= commission
        parts = []
        for part in getattr(t, "parts", ()):
            at = _field(part, "time")
            at = datetime.fromisoformat(at) if isinstance(at, str) else at
            parts.append((at, _field(part, "share"), part))
        parts.sort(key=lambda p: p[0])
        if (
            any(
                at < entry_time or at > exit_time or not isfinite(share) or share <= 0
                for at, share, _ in parts
            )
            or sum(p[1] for p in parts) > 1 + 1e-9
        ):
            raise ValueError("invalid partial exits")

        previous = 0.0
        if cuts:
            risk = abs(t.entry - t.initial_stop)
            if not isfinite(risk) or risk <= 0 or weight <= 0:
                raise ValueError("invalid stop risk")
            spread = getattr(t, "spread_r", 0.0) * risk / weight
            fill = getattr(t, "entry_fill", None)
            if fill is None:
                fill = t.entry + (spread if sign > 0 else 0.0)
            if not all(isfinite(v) for v in (fill, spread)):
                raise ValueError("nonfinite fill/spread")
            for n, cut in enumerate(cuts, 1):
                try:
                    bid = marks[t.symbol, cut]
                except KeyError:
                    raise ValueError(f"missing mark for {t.symbol} at {cut}") from None
                if not isfinite(bid):
                    raise ValueError("nonfinite mark")
                closed, realized = 0.0, 0.0
                for at, share, part in parts:
                    if at >= cut:
                        break
                    px = _field(part, "fill")
                    if px is None:
                        px = _field(part, "price") + (spread if sign < 0 else 0.0)
                    realized += share * sign * (px - fill) / risk * weight
                    closed += share
                mark = bid + (spread if sign < 0 else 0.0)
                value = realized + (1 - closed) * sign * (mark - fill) / risk * weight
                value += carry * n / len(cuts)
                net[index((cut.astimezone(PRAGUE) - timedelta(days=1)).date())] += value - previous
                previous = value
        net[index(exit_time.astimezone(PRAGUE).date())] += t.r_net + commission - previous

        # Integrate remaining size, splitting at partial exits and local day boundaries.
        at, share = entry_time, 1.0
        for until, closed, _ in [*parts, (exit_time, 0.0, None)]:
            while at < until:
                day = at.astimezone(PRAGUE).date()
                left, right = _midnight(day), _midnight(day + timedelta(days=1))
                stop = min(until, right)
                if day in position_index:
                    position[position_index[day]] += (
                        sign * share * (stop - at).total_seconds() / (right - left).total_seconds()
                    )
                at = stop
            share -= closed
    return net, position


def daily_net_r_mtm(trades: Sequence, start: date, end: date, sources):
    """Load bid marks through SymbolSources; one read per consecutive cached-day block.

    Spec: risk-management.md > Trial log and deflated Sharpe > Marked-to-market daily series.
    M1 timestamps are opens: only ts + one minute <= cut is eligible.
    """
    queries = {}
    for t in trades:
        queries.setdefault(t.symbol, set()).update(_cuts(t))
    marks = {}
    for symbol, requested in queries.items():
        if not requested:
            continue
        cuts = sorted(requested)
        cached = sorted({d for d in sources.cached_days(symbol) if d <= cuts[-1].date()})
        # Include the preceding cached day for a gap/weekend before the earliest cut.
        before = [d for d in cached if d < cuts[0].date()]
        first = before[-1] if before else cuts[0].date()
        blocks = []
        for day in (d for d in cached if d >= first):
            if blocks and day == blocks[-1][1] + timedelta(days=1):
                blocks[-1][1] = day
            else:
                blocks.append([day, day])
        adapter = sources.adapter(symbol)
        latest = {}
        for first, last in blocks:
            frame = adapter.fetch_frame(
                symbol,
                Timeframe.M1,
                datetime.combine(first, time(), UTC),
                datetime.combine(last + timedelta(days=1), time(), UTC),
            )
            if frame.empty:
                continue
            frame = frame.sort_values("ts")
            closed = frame["ts"] + timedelta(minutes=1)
            for cut in cuts:
                i = closed.searchsorted(cut, side="right") - 1
                if i >= 0:
                    stamp = closed.iloc[i]
                    if cut not in latest or stamp > latest[cut]:
                        marks[symbol, cut] = float(frame["close"].iloc[i])
                        latest[cut] = stamp
    return daily_mtm_from_marks(trades, start, end, marks)
