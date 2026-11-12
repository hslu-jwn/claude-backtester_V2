"""Immutable linked-order intent. Spec: design/multi-symbol.md › B.

Quantities are positive relative exposures; Direction supplies their sign. Ordered
tuple positions identify legs within a group. This contract declares execution policy;
it neither executes orders nor changes the legacy Order/TradeResult contracts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from math import isfinite
from typing import TYPE_CHECKING

from backtester.core.market import MarketView, ReferenceInput
from backtester.core.models import Direction

if TYPE_CHECKING:
    from backtester.engine.group_trade import GroupResult


class EntryPolicy(Enum):
    """Predeclared synchronized entry. Spec: design/multi-symbol.md › B."""

    NEXT_OPEN_ALL_OR_NONE = "next_open_all_or_none"


class ExitPolicy(Enum):
    """Executable group exit after a stop. Spec: design/multi-symbol.md › B."""

    ALL_LEGS_NEXT_OPEN_AFTER_STOP = "all_legs_next_open_after_stop"


@dataclass(frozen=True, slots=True)
class GroupLeg:
    """Scale-free exposure and initial price risk. Spec: design/multi-symbol.md › B."""

    symbol: str
    direction: Direction
    quantity: float
    stop_distance: float
    take_profit_distance: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol:
            raise ValueError("symbol must be a nonempty string")
        if not isinstance(self.direction, Direction):
            raise ValueError("direction must be a Direction")  # noqa: TRY004 - contract
        for name in ("quantity", "stop_distance", "take_profit_distance"):
            value = getattr(self, name)
            if name == "take_profit_distance" and value is None:
                continue
            if not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")


@dataclass(frozen=True, slots=True)
class GroupOrder:
    """Ordered atomic intent, before any fills. Spec: design/multi-symbol.md › B."""

    group_id: str
    legs: tuple[GroupLeg, ...]
    intent_time: datetime
    entry_policy: EntryPolicy
    exit_policy: ExitPolicy
    expiry_minutes: float
    reason: str = ""
    tags: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not isinstance(self.group_id, str) or not self.group_id:
            raise ValueError("group_id must be a nonempty string")
        if not isinstance(self.legs, tuple) or len(self.legs) < 2:
            raise ValueError("legs must be an ordered tuple of at least two legs")
        if any(not isinstance(leg, GroupLeg) for leg in self.legs):
            raise ValueError("legs must contain GroupLeg instances")
        if len({leg.symbol for leg in self.legs}) != len(self.legs):
            raise ValueError("legs must have distinct symbols")
        if self.intent_time.utcoffset() != timedelta(0):
            raise ValueError("intent_time must be UTC-aware")
        if not isinstance(self.entry_policy, EntryPolicy):
            raise ValueError("entry_policy must be an EntryPolicy")  # noqa: TRY004 - contract
        if not isinstance(self.exit_policy, ExitPolicy):
            raise ValueError("exit_policy must be an ExitPolicy")  # noqa: TRY004 - contract
        if not isfinite(self.expiry_minutes) or self.expiry_minutes <= 0:
            raise ValueError("expiry_minutes must be finite and positive")
        object.__setattr__(self, "tags", frozenset(self.tags))


class GroupStrategy(ABC):
    """Bounded group decisions. Spec: design/multi-symbol.md › B.

    Declare leg timeframe/freshness overrides in references, alongside extra read-only
    symbols. The engine always makes traded legs required M1 inputs. open_groups is
    an immutable tuple of accepted GroupOrders with remaining exposure, never engine
    position objects or unbounded histories.
    """

    legs: tuple[str, ...]
    references: tuple[ReferenceInput, ...] = ()

    @abstractmethod
    def on_group_candle(self, now: datetime, market: MarketView) -> list[GroupOrder]:
        """Decide at the union M1 close, using only the supplied bounded snapshot."""

    def group_exits(
        self, now: datetime, market: MarketView, open_groups: tuple[GroupOrder, ...],
    ) -> list[str]:
        """Request next-open exits for group IDs. Default: none."""
        return []

    def on_group_closed(self, result: GroupResult) -> None:
        """Receive each fully closed group once. Default: nothing."""
