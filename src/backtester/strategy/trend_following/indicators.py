"""Incremental indicators of strategy 4: rolling channel, SMA, momentum, Dunnigan swings, KAMA.

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


class SmaBandCross:
    """Close crossing SMA(N) shifted by `band_atr` x ATR (+ for longs, - for shorts).

    Spec: strategy-trend-following.md › Trend signal (`sma`, SMA band). Long when the
    previous close was at or below the previous line and this close is above this line;
    mirrored for shorts. With a band, the ATR of this and the previous candle must be known.
    Also strategy 2's trend filter (strategy-ny-indices.md › Trend filter).
    """

    def __init__(self, period: int, band_atr: float = 0.0):
        if period < 2:
            raise ValueError("period must be >= 2")
        if band_atr < 0:
            raise ValueError("band_atr must be >= 0")
        self.band_atr = band_atr
        self._sma = Sma(period)
        self._prev: tuple[float, float, float | None] | None = None  # close, SMA, ATR

    def update(self, close: float, atr: float | None) -> Direction | None:
        sma = self._sma.update(close)
        prev, self._prev = self._prev, (close, sma, atr) if sma is not None else None
        if sma is None or prev is None:
            return None
        prev_close, prev_sma, prev_atr = prev
        band = self.band_atr
        if band > 0 and (atr is None or prev_atr is None):
            return None
        for direction in (Direction.BULLISH, Direction.BEARISH):
            sign = 1 if direction is Direction.BULLISH else -1
            line = sma + (sign * band * atr if band > 0 else 0)
            prev_line = prev_sma + (sign * band * prev_atr if band > 0 else 0)
            if sign * (prev_close - prev_line) <= 0 and sign * (close - line) > 0:
                return direction
        return None


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


class Momentum:
    """Sign of close - close N candles ago: LONG above 0, SHORT below, None at exactly 0 or
    before N + 1 closes exist. The event repeats on every candle while the sign holds."""

    def __init__(self, period: int):
        if period < 1:
            raise ValueError("period must be >= 1")
        self.period = period
        self._closes: deque[float] = deque(maxlen=period + 1)

    def update(self, close: float) -> Direction | None:
        self._closes.append(close)
        if len(self._closes) <= self.period:
            return None
        change = close - self._closes[0]
        if change > 0:
            return Direction.BULLISH
        return Direction.BEARISH if change < 0 else None


class DunniganSwings:
    """Dunnigan swings (p. 152) and the programmable "Dunnigan trend" signal.

    Spec: strategy-trend-following.md › Dunnigan swings. State: `upswing` (True / False /
    None) and the reference candle `_ref` = (high, low) of the highest candle of the upswing
    (lowest of the downswing).
    - Upswing: a candle with a higher high replaces the reference (an outside candle too, so
      the swing top is the true highest high; the swing itself does not change). A candle
      whose high AND low are both below the reference's starts a downswing: the reference's
      high becomes `swing_top`, and the candle is the new reference. Anything else (inside,
      equal) changes nothing.
    - Downswing: mirrored (lower low replaces the reference; high and low both above it
      start an upswing and record `swing_bottom` = the reference's low).
    Initial state (conservative, Claude): undecided, the first candle is the reference. The
    first later candle with a higher high and higher low (lower / lower) starts the first
    upswing (downswing) and *no* top / bottom is recorded for it, so no signal exists before
    a real swing top / bottom was seen. Equal prices never count as higher / lower.

    `update(candle)` returns the signal: LONG when the last two candles each made a higher
    high and a higher low than the candle before AND the close is above the most recent
    swing top (mirrored: LL + LH, close below the most recent swing bottom); else None.
    """

    def __init__(self) -> None:
        self.upswing: bool | None = None
        self.swing_top: float | None = None
        self.swing_bottom: float | None = None
        self._ref: tuple[float, float] | None = None
        self._last: deque[Candle] = deque(maxlen=3)

    def update(self, candle: Candle) -> Direction | None:
        self._advance(candle)
        self._last.append(candle)
        if len(self._last) < 3:
            return None
        a, b, c = self._last
        for direction, level in (
            (Direction.BULLISH, self.swing_top),
            (Direction.BEARISH, self.swing_bottom),
        ):
            sign = 1 if direction is Direction.BULLISH else -1
            if level is None or sign * (c.close - level) <= 0:
                continue
            if all(
                sign * (n.high - p.high) > 0 and sign * (n.low - p.low) > 0
                for p, n in ((a, b), (b, c))
            ):
                return direction
        return None

    def _advance(self, candle: Candle) -> None:
        if self._ref is None:
            self._ref = (candle.high, candle.low)
            return
        high, low = self._ref
        if self.upswing is None:
            if candle.high > high and candle.low > low:
                self.upswing, self._ref = True, (candle.high, candle.low)
            elif candle.high < high and candle.low < low:
                self.upswing, self._ref = False, (candle.high, candle.low)
            return
        sign = 1 if self.upswing else -1  # +1: following an upswing, -1: a downswing
        if sign * (candle.high - high) < 0 and sign * (candle.low - low) < 0:
            # both below (upswing) / both above (downswing): the swing turns
            if self.upswing:
                self.swing_top = high
            else:
                self.swing_bottom = low
            self.upswing = not self.upswing
            self._ref = (candle.high, candle.low)
        elif (candle.high > high) if self.upswing else (candle.low < low):
            self._ref = (candle.high, candle.low)  # a new extreme of the running swing
