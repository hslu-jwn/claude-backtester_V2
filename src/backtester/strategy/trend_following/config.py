"""Tunable parameters for strategy 4 (trend following, Kaufman style).

Spec: strategy-trend-following.md. Defaults follow the spec.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backtester.core.models import Timeframe

TIMEFRAMES = (Timeframe.M15, Timeframe.M30, Timeframe.H1, Timeframe.H4, Timeframe.D1)


class Signal(Enum):
    BREAKOUT = "breakout"  # close beyond the highest high / lowest low of the previous N candles
    SMA = "sma"  # close crosses the SMA(N) of closes
    KAMA = "kama"  # Kaufman adaptive moving average rises / falls by more than the filter


@dataclass(frozen=True, slots=True)
class TrendFollowingConfig:
    timeframe: Timeframe = Timeframe.H4  # signal, ATR and stop all on this one timeframe
    signal: Signal = Signal.BREAKOUT
    breakout_period: int = 20  # breakout: previous N candles (current excluded)
    sma_period: int = 50  # sma: SMA of the closes over N candles
    kama_er_period: int = 10  # kama: efficiency ratio over this many candles
    kama_fast: int = 2  # kama: fast smoothing period
    kama_slow: int = 30  # kama: slow smoothing period
    kama_filter: float = 0.1  # kama: signal needs a change > this x std of the last changes
    kama_filter_period: int = 20  # kama: number of KAMA changes the filter's std is taken over
    atr_period: int = 20  # Wilder ATR of the strategy timeframe
    stop_atr_mult: float = 3.0  # protective stop = this x ATR from the entry (1R)

    def __post_init__(self) -> None:
        if self.timeframe not in TIMEFRAMES:
            raise ValueError("timeframe must be one of 15m, 30m, 1h, 4h, 1d")
        if self.breakout_period < 1:
            raise ValueError("breakout_period must be >= 1")
        if self.sma_period < 2:
            raise ValueError("sma_period must be >= 2")
        if self.kama_er_period < 1:
            raise ValueError("kama_er_period must be >= 1")
        if self.kama_fast < 1 or self.kama_slow <= self.kama_fast:
            raise ValueError("kama periods need 1 <= kama_fast < kama_slow")
        if self.kama_filter < 0:
            raise ValueError("kama_filter must be >= 0")
        if self.kama_filter_period < 2:
            raise ValueError("kama_filter_period must be >= 2")
        if self.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if self.stop_atr_mult <= 0:
            raise ValueError("stop_atr_mult must be > 0")
