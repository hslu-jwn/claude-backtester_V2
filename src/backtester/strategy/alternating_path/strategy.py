"""Causal alternating M15 path. Spec: strategy-alternating-path.md > Assumptions A1-A9."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime, time, timedelta
from itertools import pairwise
from math import isfinite
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.detectors.settings import DetectorSettings
from backtester.strategy.alternating_path.config import SYMBOLS, AlternatingPathConfig
from backtester.strategy.base import Order, Strategy

if TYPE_CHECKING:
    from backtester.engine.trade import TradeResult


class _M15Aggregator:
    """Spec: A1. Observe a bucket only when its final consecutive M1 has closed."""

    def __init__(self, minutes: int = 15):
        self._minutes = minutes
        self._start: datetime | None = None
        self._candles: list[Candle] = []

    def update(self, candle: Candle) -> Candle | None:
        ts = candle.ts.astimezone(UTC)
        start = ts.replace(
            minute=ts.minute // self._minutes * self._minutes, second=0, microsecond=0
        )
        if start != self._start:
            self._start = start
            self._candles = []
        self._candles.append(candle)
        if ts + Timeframe.M1.duration != start + timedelta(minutes=self._minutes):
            return None
        candles = self._candles
        if len(candles) != self._minutes:
            return None
        for i, c in enumerate(candles):
            if (
                c.ts != start + i * Timeframe.M1.duration
                or not all(isfinite(p) and p > 0 for p in (c.open, c.high, c.low, c.close))
                or c.high < max(c.open, c.close)
                or c.low > min(c.open, c.close)
                or c.high < c.low
            ):
                return None
        return Candle(
            start,
            candles[0].open,
            max(c.high for c in candles),
            min(c.low for c in candles),
            candles[-1].close,
        )


class _ObservedAtr:
    """Spec: A2. First valid close establishes prev_close, without a true range."""

    def __init__(self, period: int):
        self._period = period
        self._previous: float | None = None
        self._seed: list[float] = []
        self.value: float | None = None

    def update(self, bar: Candle) -> float | None:
        if self._previous is not None:
            tr = max(bar.high, self._previous) - min(bar.low, self._previous)
            if self.value is None:
                self._seed.append(tr)
                if len(self._seed) == self._period:
                    self.value = sum(self._seed) / self._period
                    self._seed.clear()
            else:
                self.value = ((self._period - 1) * self.value + tr) / self._period
        self._previous = bar.close
        return self.value


class AlternatingPath(Strategy):
    base_timeframe = Timeframe.M1
    timeframes = (Timeframe.M1,)
    uses_session_break_even = False
    min_warmup_days = 5

    def __init__(
        self,
        symbol: str,
        config: AlternatingPathConfig | None = None,
        detectors: DetectorSettings | None = None,
    ):
        self.symbol = symbol
        self.config = config = config or AlternatingPathConfig()
        self._tz = ZoneInfo("Europe/London")
        self._first = time.fromisoformat(config.first_signal_london)
        self._last = time.fromisoformat(config.last_signal_london)
        self._deadline_clock = time.fromisoformat(config.exit_deadline_london)
        self._aggregator = _M15Aggregator(config.aggregation_minutes)
        self._atr = _ObservedAtr(config.atr_period)
        self._window: deque[Candle] = deque(maxlen=config.alternating_changes + 1)
        self._last_close: datetime | None = None
        self._ref: object | None = None
        self._due: datetime | None = None
        self._exit_queued = False

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        view = views.get(Timeframe.M1)
        if view is None:
            return []
        candle = view.current
        if candle.ts + Timeframe.M1.duration != now:
            return []
        if self._last_close is not None and now <= self._last_close:
            return []
        self._last_close = now
        if self._ref is not None and self._due is not None and now >= self._due:
            self._exit_queued = True
        bar = self._aggregator.update(candle)
        if bar is None:
            return []
        prior = self._atr.value
        self._atr.update(bar)  # features advance even while a trade is open
        self._window.append(bar)
        local = now.astimezone(self._tz)
        due = now + timedelta(minutes=self.config.holding_minutes)
        deadline = datetime.combine(local.date(), self._deadline_clock, self._tz)
        if (
            self._ref is not None
            or self.symbol not in SYMBOLS
            or local.weekday() >= 5
            or not self._first <= local.time() <= self._last
            or due > deadline
            or prior is None
            or not isfinite(prior)
            or prior <= 0
            or len(self._window) != self.config.alternating_changes + 1
        ):
            return []
        pairs = list(pairwise(self._window))
        if any(b.ts - a.ts != timedelta(minutes=self.config.aggregation_minutes) for a, b in pairs):
            return []
        deltas = [b.close - a.close for a, b in pairs]
        if any(d == 0 for d in deltas) or any((a > 0) == (b > 0) for a, b in pairwise(deltas)):
            return []
        if sum(abs(d) for d in deltas) / prior < self.config.path_activity_atr_min:
            return []
        side = (1 if deltas[-1] > 0 else -1) * (
            1 if self.config.response_mode == "FOLLOW_LAST" else -1
        )
        distance = self.config.stop_atr_multiplier * prior
        self._ref = (self.symbol, now)
        self._due = due
        return [
            Order(
                direction=Direction.BULLISH if side > 0 else Direction.BEARISH,
                entry=candle.close,
                stop_loss=candle.close - side * distance,
                take_profit=None,
                ref=self._ref,
                reason="Alternating M15 path",
            )
        ]

    def exits(self) -> list[object]:
        if not self._exit_queued:
            return []
        self._exit_queued = False
        return [self._ref] if self._ref is not None else []

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        self._forget(ref)

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        self._forget(ref)

    def _forget(self, ref: object) -> None:
        if ref == self._ref:
            self._ref = self._due = None
            self._exit_queued = False
