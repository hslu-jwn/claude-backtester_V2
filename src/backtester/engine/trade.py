"""Trade record, expressed in R.

R = (exit - entry) / (entry - initial_stop) for longs (mirrored for shorts).
The trade keeps its price levels so risk/ can size it and the chart can draw the
TradingView-style position box (entry line, green target zone, red risk zone, R:R).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from backtester.core.models import Direction


class ExitReason(Enum):
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    BREAK_EVEN = "break_even"
    END_OF_DATA = "end_of_data"


@dataclass(slots=True)
class Trade:
    symbol: str
    direction: Direction
    entry_time: datetime
    entry: float
    initial_stop: float
    stop_loss: float  # current SL (may move to break-even)
    take_profit: float
    tags: frozenset[str] = field(default_factory=frozenset)
    exit_time: datetime | None = None
    exit_price: float | None = None
    exit_reason: ExitReason | None = None
    max_adverse_r: float = 0.0  # worst floating R seen, for the account simulator

    @property
    def risk(self) -> float:
        return abs(self.entry - self.initial_stop)

    @property
    def r_multiple(self) -> float | None:
        if self.exit_price is None:
            return None
        sign = 1 if self.direction is Direction.BULLISH else -1
        return sign * (self.exit_price - self.entry) / self.risk
