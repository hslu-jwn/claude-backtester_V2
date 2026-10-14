"""Incremental indicators of strategy 4: rolling channel, SMA and KAMA.

Spec: strategy-trend-following.md › Trend signal. Each indicator is fed one closed candle
(or close) at a time, in order, and only ever holds what it has been fed, so it cannot look
ahead. Nothing here knows which timeframe it runs on.
"""

from __future__ import annotations

import math
from collections import deque

from backtester.core.models import Candle, Direction


class RollingChannel:
    """Highest high and lowest low of the previous N candles (the current one excluded)."""

    def __init__(self, period: int):
        if period < 1:
            raise ValueError("period must be >= 1")
        self.period = period
        self._highs: deque[float] = deque(maxlen=period)
        self._lows: deque[float] = deque(maxlen=period)

    def update(self, candle: Candle) -> tuple[float, float] | None:
        """(highest high, lowest low) of the N candles before `candle`; None until N exist.
        Then `candle` joins the window."""
        channel = (max(self._highs), min(self._lows)) if len(self._highs) == self.period else None
        self._highs.append(candle.high)
        self._lows.append(candle.low)
        return channel


class Sma:
    """Simple moving average of the last N closes."""

    def __init__(self, period: int):
        if period < 1:
            raise ValueError("period must be >= 1")
        self.period = period
        self._closes: deque[float] = deque(maxlen=period)
        self._sum = 0.0

    def update(self, close: float) -> float | None:
        if len(self._closes) == self.period:
            self._sum -= self._closes[0]
        self._closes.append(close)
        self._sum += close
        return self._sum / self.period if len(self._closes) == self.period else None


class Kama:
    """Kaufman's adaptive moving average with the change filter.

    ER = |close - close[n]| / sum |close[i] - close[i-1]| over n candles (0 if the sum is 0)
    SC = (ER * (2/(fast+1) - 2/(slow+1)) + 2/(slow+1))^2
    KAMA = KAMA[1] + SC * (close - KAMA[1]), seeded with the close of candle n (the first
    candle that has n changes behind it; candles are counted from 0).

    `signal` after an update: LONG when KAMA - KAMA[1] > f, SHORT when < -f, with
    f = filter_mult x the sample standard deviation (n - 1) of the last `filter_period`
    KAMA changes (this candle's included). None until that many changes exist.
    """

    def __init__(
        self, er_period: int, fast: int, slow: int, filter_mult: float, filter_period: int
    ):
        self.er_period = er_period
        self._fast = 2 / (fast + 1)
        self._slow = 2 / (slow + 1)
        self.filter_mult = filter_mult
        self._closes: deque[float] = deque(maxlen=er_period + 1)
        self._changes: deque[float] = deque(maxlen=filter_period)
        self.value: float | None = None
        self.last_change: float | None = None

    def update(self, close: float) -> float | None:
        self._closes.append(close)
        if len(self._closes) <= self.er_period:
            return None
        if self.value is None:
            self.value = close  # the seed
            return self.value
        closes = self._closes
        path = sum(abs(b - a) for a, b in zip(list(closes)[:-1], list(closes)[1:], strict=True))
        er = abs(close - closes[0]) / path if path else 0.0
        sc = (er * (self._fast - self._slow) + self._slow) ** 2
        previous = self.value
        self.value = previous + sc * (close - previous)
        self.last_change = self.value - previous
        self._changes.append(self.last_change)
        return self.value

    @property
    def signal(self) -> Direction | None:
        if self.last_change is None or len(self._changes) < self._changes.maxlen:
            return None
        n = len(self._changes)
        mean = sum(self._changes) / n
        std = math.sqrt(sum((c - mean) ** 2 for c in self._changes) / (n - 1))
        threshold = self.filter_mult * std
        if self.last_change > threshold:
            return Direction.BULLISH
        if self.last_change < -threshold:
            return Direction.BEARISH
        return None
