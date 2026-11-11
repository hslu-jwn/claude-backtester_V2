"""Engine-owned bounded reference provider, alongside the unchanged Replay.

Spec: design/multi-symbol.md > A and One logical clock. Batch reference closes between
primary callbacks (equivalent to union close events); expose every intervening index.
Only the engine advances time. Strategies receive MarketView, never this provider.
"""

from bisect import bisect_left
from collections.abc import Sequence
from datetime import datetime
from itertools import pairwise
from types import MappingProxyType

from backtester.core.market import Availability, MarketView, ReferenceInput, require_utc
from backtester.core.models import Timeframe
from backtester.core.mtf import HigherTimeframeClock
from backtester.core.series import CandleSeries


class MarketReplay:
    def __init__(self, inputs: Sequence[ReferenceInput], series: Sequence[CandleSeries]):
        self.inputs = tuple(sorted(inputs, key=lambda item: item.symbol))
        if len({i.symbol for i in inputs}) != len(inputs):
            raise ValueError("duplicate reference symbol declaration")
        expected = {(i.symbol, tf) for i in inputs for tf in i.timeframes}
        actual = {(s.symbol, s.timeframe) for s in series}
        if len(actual) != len(series) or actual != expected:
            raise ValueError("reference series must match declarations exactly")
        for s in series:
            for candle in s._candles:
                require_utc(candle.ts)
        self._clocks = {(s.symbol, s.timeframe): HigherTimeframeClock(s) for s in series}
        self._cursors = dict.fromkeys(expected, -1)
        self._now: datetime | None = None

    def advance(self, now: datetime) -> MarketView:
        require_utc(now)
        if self._now is not None and now < self._now:
            raise ValueError("market clock cannot move backward")
        self._now = now
        views, availability, newly = {}, {}, {}
        reasons = []
        for item in self.inputs:
            symbol_views, statuses, ranges = {}, {}, {}
            minutes = self._clocks[(item.symbol, Timeframe.M1)].view_at(now)
            for tf in sorted(item.timeframes, key=lambda tf: tf.value):
                key = (item.symbol, tf)
                view = self._clocks[key].view_at(now)
                cursor = view.cursor if view is not None else -1
                ranges[tf] = range(self._cursors[key] + 1, cursor + 1)
                self._cursors[key] = cursor
                symbol_views[tf] = view
                close = view.current.ts + tf.duration if view is not None else None
                age = now - close if close is not None else None
                status, reason = "ready", ""
                if view is None:
                    status, reason = "missing", "no closed observations"
                elif age > item.max_age and item.calendar.is_open(now):
                    status, reason = "missing", "freshness limit exceeded"
                elif len(view) < item.min_candles:
                    status, reason = "not_ready", "insufficient warm-up"
                elif item.require_contiguous and (
                    self._has_hole(view, item)
                    or (tf is not Timeframe.M1 and self._incomplete_minutes(view, minutes, item))
                ):
                    status, reason = "not_ready", "incomplete observation window"
                elif age > item.max_age:
                    status, reason = "closed", "scheduled closure"
                ready = status in ("ready", "closed")
                statuses[tf] = Availability(status, ready, close, age,
                                            cursor if cursor >= 0 else None, reason)
                if item.required and not ready:
                    reasons.append(f"{item.symbol}/{tf.name}: {reason}")
            views[item.symbol] = MappingProxyType(symbol_views)
            availability[item.symbol] = MappingProxyType(statuses)
            newly[item.symbol] = MappingProxyType(ranges)
        return MarketView(now, MappingProxyType(views), MappingProxyType(availability),
                          MappingProxyType(newly), not reasons, tuple(reasons))

    @staticmethod
    def _incomplete_minutes(view, minutes, item: ReferenceInput) -> bool:
        start = view[-item.min_candles].ts
        end = view.current.ts + view.timeframe.duration
        expected = start
        if minutes is not None:
            left = bisect_left(minutes, start, key=lambda candle: candle.ts)
            right = bisect_left(minutes, end, key=lambda candle: candle.ts)
            for candle in minutes.window(left, right):
                while expected < candle.ts:
                    if item.calendar.is_open(expected):
                        return True
                    expected += Timeframe.M1.duration
                expected = candle.ts + Timeframe.M1.duration
        while expected < end:
            if item.calendar.is_open(expected):
                return True
            expected += Timeframe.M1.duration
        return False

    @staticmethod
    def _has_hole(view, item: ReferenceInput) -> bool:
        # Only inspect the declared readiness window; never inspect future candles.
        candles = view.last(item.min_candles)
        duration = view.timeframe.duration
        for previous, current in pairwise(candles):
            expected = previous.ts + duration
            while expected < current.ts:
                if item.calendar.is_open(expected):
                    return True
                expected += duration
        return False
