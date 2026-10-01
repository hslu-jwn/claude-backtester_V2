"""Strategy interface.

The engine calls `on_candle` once per closed base-timeframe candle with lookahead-safe views
of every timeframe the strategy declared. A strategy returns orders in price terms
(entry, SL, TP); the engine fills them and records results in R.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from backtester.core.models import Direction, Timeframe
from backtester.core.series import SeriesView


@dataclass(frozen=True, slots=True)
class Order:
    direction: Direction
    entry: float  # filled at the close of the current base candle
    stop_loss: float
    take_profit: float
    tags: frozenset[str] = field(default_factory=frozenset)  # e.g. {"last_1.5h"}
    reason: str = ""  # human-readable trail for the chart / debugging


class Strategy(ABC):
    base_timeframe: Timeframe
    timeframes: tuple[Timeframe, ...]  # all timeframes the strategy needs, incl. base

    @abstractmethod
    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        """`now` = close time of the current base candle. A view is None until its first
        candle has closed."""
