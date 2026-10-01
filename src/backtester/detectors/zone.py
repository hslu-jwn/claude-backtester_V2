"""Zone type and the shared validation state machine.

Spec: confluences.md › Validation (applies to FVG, OB, breaker, BPR, no exceptions).
- Tap: a wick into the zone.
- Confirmed: a candle closes beyond the boundary in the zone's bias direction
  (bullish: green close above the top). Only then usable for entry.
- Invalidated: a candle closes beyond the opposite boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backtester.core.models import Candle, Direction


class ZoneKind(Enum):
    FVG = "fvg"
    ORDER_BLOCK = "order_block"
    BREAKER = "breaker"
    BPR = "bpr"
    SESSION = "session"


class ZoneState(Enum):
    ACTIVE = "active"  # formed, not touched yet
    TAPPED = "tapped"
    CONFIRMED = "confirmed"
    INVALIDATED = "invalidated"


@dataclass(slots=True)
class Zone:
    kind: ZoneKind
    direction: Direction
    top: float
    bottom: float
    created_index: int  # candle that confirmed the zone's existence
    state: ZoneState = ZoneState.ACTIVE

    def on_candle(self, candle: Candle) -> ZoneState:
        """Advance the state with one newly closed candle and return the new state."""
        raise NotImplementedError("TODO: implement per spec › Validation")
