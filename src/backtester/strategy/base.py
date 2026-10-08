"""Strategy interface.

The engine calls `on_candle` once per closed base-timeframe candle with lookahead-safe views
of every timeframe the strategy declared. A strategy returns orders in price terms
(entry, SL, TP); the engine fills them and records results in R. An order may close in
two parts: `tp1_share` of the position at `take_profit`, the rest at `take_profit_2`.
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
    take_profit: float  # TP1 (the whole position when take_profit_2 is None)
    tags: frozenset[str] = field(default_factory=frozenset)  # e.g. {"last_1.5h"}
    reason: str = ""  # human-readable trail for the chart / debugging
    confluence: str = ""  # entry confluence type, e.g. "fvg" (results split by it)
    take_profit_2: float | None = None  # the rest of the position closes here
    tp1_share: float = 1.0  # share closed at TP1; < 1 only with a take_profit_2
    break_even_after_tp1: bool = False  # SL of the rest to break-even (with costs) after TP1


class Strategy(ABC):
    base_timeframe: Timeframe
    timeframes: tuple[Timeframe, ...]  # all timeframes the strategy needs, incl. base

    @abstractmethod
    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        """`now` = close time of the current base candle. A view is None until its first
        candle has closed."""

    def session_records(self, run_end: datetime | None = None) -> list[dict]:
        """What the strategy saw per session, JSON-ready, for the results file (ROADMAP
        3.4). Records still open end at `run_end`. Default: nothing."""
        return []
