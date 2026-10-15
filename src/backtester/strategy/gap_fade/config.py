"""Settings of strategy 5 (gap fade): every tunable value with its spec default.

Spec: docs/strategy-gap-fade.md (rule set by the user, 2026-10-15).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo


@dataclass(frozen=True, slots=True)
class GapFadeConfig:
    zone: str = "America/New_York"  # time zone of the cash session (DST via zoneinfo)
    cash_open: time = time(9, 30)  # entry at the close of the 1m candle closing at this time
    cash_close: time = time(16, 0)  # the close of this candle is the previous cash close (TP)
    atr_period: int = 14  # Wilder ATR over the daily cash sessions
    min_gap_atr: float = 0.1  # smallest |gap| in daily ATR that is traded (inclusive)
    max_gap_atr: float = 1.0  # |gap| in daily ATR must be below this (exclusive)
    stop_gap_mult: float = 1.0  # stop = entry -/+ this x |gap| (1.0 = 1:1 in price)
    exit_time: time = time(16, 0)  # an open trade closes at the close of this candle

    def __post_init__(self) -> None:
        ZoneInfo(self.zone)  # raises for an unknown zone
        if self.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if self.min_gap_atr <= 0:
            raise ValueError("min_gap_atr must be > 0")
        if self.max_gap_atr <= self.min_gap_atr:
            raise ValueError("max_gap_atr must be > min_gap_atr")
        if self.stop_gap_mult <= 0:
            raise ValueError("stop_gap_mult must be > 0")
        if self.cash_close <= self.cash_open:
            raise ValueError("cash_close must be after cash_open")
        if self.exit_time <= self.cash_open:
            raise ValueError("exit_time must be after cash_open")
