"""Tunable parameters for strategy 3 (no-wick candle in the trend).

Spec: strategy-no-wick.md. Defaults follow the spec.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backtester.core.models import Timeframe

# entry timeframe -> the timeframe whose trend counts with TrendSource.HIGHER
HIGHER_TIMEFRAME = {
    Timeframe.M5: Timeframe.M15,
    Timeframe.M15: Timeframe.H1,
    Timeframe.M30: Timeframe.H4,
    Timeframe.H1: Timeframe.H4,
}


class TrendSource(Enum):
    HIGHER = "higher"  # the next higher timeframe's trend
    SAME = "same"  # the entry timeframe's own trend


class EntryMode(Enum):
    CLOSE = "close"  # at the signal candle's close
    BODY_END = "body_end"  # limit at the signal candle's open (the no-wick end of the body)
    MIDDLE = "middle"  # limit at (high + low) / 2 of the signal candle


@dataclass(frozen=True, slots=True)
class NoWickConfig:
    timeframe: Timeframe = Timeframe.M15  # entry timeframe: 5m, 15m, 30m or 1h
    trend_source: TrendSource = TrendSource.HIGHER
    entry_mode: EntryMode = EntryMode.CLOSE
    max_wick_share: float = 0.0  # largest wick on the no-wick side, share of the range
    sl_buffer: float = 0.10  # share of the distance entry -> swing, beyond the swing
    rr: float = 1.0  # TP at this multiple of the risk
    order_expiry_candles: int = 6  # a limit order waits this many entry-TF candles

    def __post_init__(self) -> None:
        if self.timeframe not in HIGHER_TIMEFRAME:
            raise ValueError("timeframe must be one of 5m, 15m, 30m, 1h")
        if not 0 <= self.max_wick_share < 1:
            raise ValueError("max_wick_share must be >= 0 and < 1")
        if self.sl_buffer < 0:
            raise ValueError("sl_buffer must be >= 0")
        if self.rr <= 0:
            raise ValueError("rr must be > 0")
        if self.order_expiry_candles < 1:
            raise ValueError("order_expiry_candles must be >= 1")
