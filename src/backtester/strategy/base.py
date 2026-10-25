"""Strategy interface.

The engine calls `on_candle` once per closed base-timeframe candle with lookahead-safe views
of every timeframe the strategy declared. A strategy returns orders in price terms
(entry, SL, TP); the engine fills them and records results in R. An order may close in
two parts (`tp1_share` of the position at `take_profit`, the rest at `take_profit_2`) or
three (`tp1_share`, `tp2_share`, the rest at `take_profit_3`). When a trade has closed,
the engine calls `on_trade_closed(order.ref, result)` before the strategy's next
`on_candle` (strategy 2: one open trade per setup, re-entries). A strategy can close open trades at
the current close with `exits` (ExitReason.SIGNAL); an order may have no take profit.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.data.resample import H4Alignment

if TYPE_CHECKING:
    from backtester.engine.trade import TradeResult


@dataclass(frozen=True, slots=True)
class Order:
    direction: Direction
    entry: float  # filled at the close of the current base candle (or see `limit_fill`)
    stop_loss: float
    # TP1 (the whole position when take_profit_2 is None); None: no take profit, the trade
    # ends at its SL, a signal exit (`Strategy.exits`) or the end of data
    take_profit: float | None
    tags: frozenset[str] = field(default_factory=frozenset)  # e.g. {"last_1.5h"}
    reason: str = ""  # human-readable trail for the chart / debugging
    confluence: str = ""  # entry confluence type, e.g. "fvg" (results split by it)
    take_profit_2: float | None = None  # the rest of the position closes here
    tp1_share: float = 1.0  # share closed at TP1; < 1 only with a take_profit_2
    break_even_after_tp1: bool = False  # SL of the rest to break-even (with costs) after TP1
    take_profit_3: float | None = None  # with a TP3: TP2 closes tp2_share, TP3 the rest
    tp2_share: float | None = None
    ref: object = None  # the strategy's handle, passed back in on_trade_closed
    # a limit order that traded at `entry` inside the current candle (low <= entry <= high):
    # must have been exposed by pending_limit_orders() at the previous step. Filled at
    # `entry`, not at the close. In its fill candle only the SL counts.
    limit_fill: bool = False


class UnsupportedSymbolError(ValueError):
    """The strategy has no rules for this symbol (e.g. no session). A clear one-line message
    for the user, not a bug: the command line prints it without a traceback."""


class Strategy(ABC):
    # Engine-supplied execution check, before the strategy consumes a pending limit.
    # None preserves touch fills. Spec: risk-management.md > Costs > Limit penetration.
    limit_fill_check: Callable[[Order, Candle, datetime], bool] | None = None
    base_timeframe: Timeframe
    timeframes: tuple[Timeframe, ...]  # all timeframes the strategy needs, incl. base
    # the engine's break-even at the next session start (strategy 1's rule)
    uses_session_break_even: bool = True
    # how the runner loads 4h candles for this strategy (strategy 2: New York-aligned)
    h4_alignment: H4Alignment = H4Alignment.UTC
    # calendar days of history the strategy needs before the first run day (indicators);
    # the runner loads at least this many (strategy 4: SMA 200 on 1d needs ~300)
    min_warmup_days: int = 0
    # timeframes loaded from the first cached day instead of the warm-up start
    full_history: tuple[Timeframe, ...] = ()

    @abstractmethod
    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        """`now` = close time of the current base candle. A view is None until its first
        candle has closed."""

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        """The trade of the order with `ref` has closed (all parts). Default: nothing."""

    def pending_limit_orders(self) -> list[Order]:
        """Unfilled limits placed by this close, eligible from the next candle only.

        The engine snapshots these after each step. A later on_candle may return each
        order once, unchanged except for an entry at the open when a candle gaps past
        its limit (Spec: strategy-no-wick.md › Entry). Omit cancelled/expired orders.
        """
        return []

    def exits(self) -> list[object]:
        """Refs (`Order.ref`) of open trades to close at the current base candle's close.
        Called by the engine right after `on_candle`; a ref that is not open is ignored.
        Default: none (strategy 4: stop-and-reverse)."""
        return []

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        """The order with `ref` was not filled: its costs were above the cost filter
        or tick rounding made its levels invalid (risk-management.md > Costs).
        Default: nothing."""

    def session_records(self, run_end: datetime | None = None) -> list[dict]:
        """What the strategy saw per session, JSON-ready, for the results file (ROADMAP
        3.4). Records still open end at `run_end`. Default: nothing."""
        return []
