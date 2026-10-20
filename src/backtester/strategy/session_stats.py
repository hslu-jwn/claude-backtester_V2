"""Daily session statistics built incrementally from 1m candles (strategies 5 and 7).

A *session* is the candles closing in (`open_time`, `close_time`] of one local day (the candle
closing at `open_time` is the open price, not part of the session). A session is *regular* when a
candle closes at `close_time`. Only regular sessions feed the previous close, the Wilder ATR and the
daily-return sd; the value known before today's open is what the properties return. Same
definitions as `analytics/open_gap.py`. Spec: strategy-gap-fade.md, strategy-gap-momentum.md.
"""

from __future__ import annotations

import math
import statistics
from collections import deque
from datetime import date, time
from itertools import pairwise

from backtester.core.models import Candle


class SessionStats:
    def __init__(self, open_time: time, close_time: time, atr_period: int, vol_days: int = 0):
        self.open_time, self.close_time = open_time, close_time
        self.atr_period, self.vol_days = atr_period, vol_days
        # the session in progress
        self._day: date | None = None
        self._high = self._low = self._last_close = 0.0
        self._has_close = False
        # state of the sessions finished so far
        self.prev_regular = False  # the last finished session was regular
        self.prev_high: float | None = None  # its high / low (only meaningful when regular)
        self.prev_low: float | None = None
        self.prev_close: float | None = None  # close of the last regular session
        self.atr: float | None = None
        self._trs: list[float] = []  # true ranges until the ATR has `atr_period` days
        # closes of the last vol_days + 1 regular sessions (vol_days returns)
        self._closes: deque[float] = deque(maxlen=vol_days + 1)

    def take_in(self, day: date, t: time, candle: Candle) -> None:
        """A candle closing in (open_time, close_time] on local `day`."""
        if day != self._day:
            self.finish()
            self._day = day
            self._high, self._low, self._has_close = candle.high, candle.low, False
        else:
            self._high = max(self._high, candle.high)
            self._low = min(self._low, candle.low)
        self._last_close = candle.close
        if t == self.close_time:
            self._has_close = True

    def finish(self) -> None:
        """Close the session in progress (called at the next open)."""
        if self._day is None:
            return
        self.prev_regular = self._has_close
        self.prev_high, self.prev_low = self._high, self._low
        if self._has_close:
            tr = self._high - self._low
            if self.prev_close is not None:
                tr = max(tr, abs(self._high - self.prev_close), abs(self._low - self.prev_close))
            self.prev_close = self._last_close
            if self.vol_days:
                self._closes.append(self._last_close)
            period = self.atr_period
            if self.atr is None:
                self._trs.append(tr)
                if len(self._trs) == period:
                    self.atr = sum(self._trs) / period
            else:
                self.atr = (self.atr * (period - 1) + tr) / period
        self._day = None

    def vol_sd(self) -> float | None:
        """Sample sd of the last `vol_days` close-to-close log returns; None until they exist."""
        if not self.vol_days or len(self._closes) < self.vol_days + 1:
            return None
        closes = list(self._closes)
        return statistics.stdev(math.log(b / a) for a, b in pairwise(closes))


class TimedExit:
    """The one open day trade of a strategy and its time exit (strategies 5 and 7): queued for
    `Strategy.exits` at the close of the candle closing at `exit_time`, or at the first later
    candle (half day, data hole, next day) when that candle is missing."""

    def __init__(self) -> None:
        self._ref: object | None = None
        self._ref_date: date | None = None
        self._next_ref = 0
        self._to_close: list[object] = []

    def open(self, today: date) -> int:
        """Register a new trade entered today; returns its `Order.ref`."""
        self._ref, self._ref_date = self._next_ref, today
        self._next_ref += 1
        return self._next_ref - 1

    def check(self, local, exit_time: time) -> None:
        """`local` = close time of the current candle in the session's zone."""
        if self._ref is None or self._ref_date is None:
            return
        if local.date() > self._ref_date or local.time() >= exit_time:
            self._to_close.append(self._ref)
            self._ref = self._ref_date = None

    def take(self) -> list[object]:
        out, self._to_close = self._to_close, []
        return out

    def forget(self, ref: object) -> None:
        """The trade with `ref` ended (never filled, stop or target hit) before its time exit."""
        if ref == self._ref:
            self._ref = self._ref_date = None
