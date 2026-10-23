"""Core value types shared by every layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from math import isfinite


class Direction(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"


class Timeframe(Enum):
    """Candle duration. Values are minutes."""

    M1 = 1
    M5 = 5
    M15 = 15
    M30 = 30
    H1 = 60
    H4 = 240
    D1 = 1440
    W1 = 10080

    def __init__(self, minutes: int) -> None:
        self._duration = timedelta(minutes=minutes)

    @property
    def duration(self) -> timedelta:
        return self._duration


@dataclass(frozen=True, slots=True)
class Candle:
    """One OHLCV bar. `ts` is the candle OPEN time (UTC).

    A candle is only knowable once it has closed, i.e. at `ts + timeframe.duration`.
    `spread` is the average ask − bid over the candle in price units (0 if the source has
    no ask prices, NaN if unknown for this candle).
    """

    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    spread: float = 0.0

    def __post_init__(self) -> None:
        if not all(isfinite(price) for price in (self.open, self.high, self.low, self.close)):
            raise ValueError(f"OHLC prices must be finite at {self.ts}")
        if self.ts.tzinfo is None or self.ts.utcoffset() is None:
            raise ValueError("Candle timestamp must be timezone-aware")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError(f"Inconsistent OHLC at {self.ts}: {self}")
        if self.high < self.low:
            raise ValueError(f"high < low at {self.ts}")

    @property
    def range(self) -> float:
        return self.high - self.low

    @property
    def body(self) -> float:
        return abs(self.close - self.open)

    @property
    def is_green(self) -> bool:
        return self.close > self.open

    @property
    def is_red(self) -> bool:
        return self.close < self.open
