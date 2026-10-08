"""Zone type and the shared validation state machine.

Spec: confluences.md › Validation (applies to FVG, OB, breaker, BPR, no exceptions).
Described for a bullish zone (price comes from above), bearish mirrored:
- Tap: a wick INTO the zone (low < top); touching the top is no tap. The candle that
  confirms the zone's existence can't tap it; checking starts with the next candle.
- Confirmed (usable for entry): after a tap, a green candle closes above the top. The tap
  may be on the same candle (wick into the zone, green close above it). A doji never
  confirms. A close above the top without a tap first does nothing.
- Invalidated: any candle (doji included) closes below the bottom, tapped or not.
- Confirmed and invalidated are final: the zone is no longer checked. (Inverse FVGs and
  similar uses of an invalidated zone belong to a strategy; the invalidation event keeps
  the zone's box for that.)

Session zones are not handled here: their flips and second-break kill are strategy 1
rules (strategy/session_zone_sweep/zones.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from backtester.core.models import Candle, Direction
from backtester.core.series import SeriesView
from backtester.detectors.base import Event
from backtester.detectors.swings import is_doji


class ZoneKind(Enum):
    FVG = "fvg"
    ORDER_BLOCK = "order_block"
    BREAKER = "breaker"
    BPR = "bpr"
    EQUILIBRIUM = "equilibrium"  # discount half of a leg (strategy-specific, see the strategy)


class ZoneState(Enum):
    ACTIVE = "active"  # formed, not tapped yet
    TAPPED = "tapped"
    CONFIRMED = "confirmed"
    INVALIDATED = "invalidated"

    @property
    def finished(self) -> bool:
        return self in (ZoneState.CONFIRMED, ZoneState.INVALIDATED)


@dataclass(frozen=True, slots=True)
class ZoneBox:
    """A zone's fixed geometry. Its identity: two equal boxes are the same zone."""

    kind: ZoneKind
    direction: Direction  # bias: a bullish zone is used from above
    top: float
    bottom: float
    start_index: int  # first candle of the pattern (left edge when drawn)
    created_index: int  # candle that confirmed the zone's existence
    created_at: datetime  # close time of that candle

    def __post_init__(self) -> None:
        if self.top <= self.bottom:
            raise ValueError(f"zone top {self.top} must be above its bottom {self.bottom}")
        if self.start_index > self.created_index:
            raise ValueError("a zone can't start after the candle that confirms it")

    @property
    def near(self) -> float:
        """The edge price reaches first (bullish: the top)."""
        return self.top if self.direction is Direction.BULLISH else self.bottom

    @property
    def far(self) -> float:
        """The opposite edge (bullish: the bottom)."""
        return self.bottom if self.direction is Direction.BULLISH else self.top


@dataclass(frozen=True, slots=True)
class ZoneTransition(Event):
    """A zone's state change, confirmed by the candle that caused it."""

    zone: ZoneBox
    previous: ZoneState
    state: ZoneState
    close: float  # close of that candle


def _sign(direction: Direction) -> int:
    return 1 if direction is Direction.BULLISH else -1


def taps(zone: ZoneBox, candle: Candle) -> bool:
    """The candle's wick goes into the zone past its near edge (a touch is no tap)."""
    wick = candle.low if zone.direction is Direction.BULLISH else candle.high
    return _sign(zone.direction) * wick < _sign(zone.direction) * zone.near


def closes_beyond_near(zone: ZoneBox, candle: Candle, doji_max_body: float) -> bool:
    """A candle of the zone's bias color (never a doji) closes beyond the near edge."""
    if is_doji(candle, doji_max_body):
        return False
    color = candle.is_green if zone.direction is Direction.BULLISH else candle.is_red
    return color and _sign(zone.direction) * candle.close > _sign(zone.direction) * zone.near


def closes_beyond_far(zone: ZoneBox, candle: Candle) -> bool:
    """Any candle closes beyond the far edge (bullish: below the bottom)."""
    return _sign(zone.direction) * candle.close < _sign(zone.direction) * zone.far


class ZoneValidator:
    """The validation state of one zone, advanced one closed candle at a time."""

    def __init__(self, zone: ZoneBox, doji_max_body: float):
        self.zone = zone
        self.doji_max_body = doji_max_body
        self.state = ZoneState.ACTIVE
        self._last_index = zone.created_index

    def on_candle(self, view: SeriesView) -> list[ZoneTransition]:
        """Check `view.current`, a candle after the zone's last checked one. Returns the
        transitions it causes (tap and confirmation can both happen on one candle)."""
        if view.cursor <= self._last_index:
            raise ValueError(
                f"zone checked with candle {view.cursor}, expected a candle after "
                f"{self._last_index}"
            )
        self._last_index = view.cursor
        if self.state.finished:
            return []
        candle, zone = view.current, self.zone
        closed_at = candle.ts + view.timeframe.duration
        out: list[ZoneTransition] = []

        def move(state: ZoneState) -> None:
            out.append(
                ZoneTransition(view.cursor, closed_at, zone, self.state, state, candle.close)
            )
            self.state = state

        if closes_beyond_far(zone, candle):
            move(ZoneState.INVALIDATED)
            return out
        if self.state is ZoneState.ACTIVE and taps(zone, candle):
            move(ZoneState.TAPPED)
        if self.state is ZoneState.TAPPED and closes_beyond_near(zone, candle, self.doji_max_body):
            move(ZoneState.CONFIRMED)
        return out


class ZoneBook:
    """The zones a detector still checks. `on_candle(view)` once per closed candle, in
    order, BEFORE adding zones confirmed by that candle; finished zones are dropped."""

    def __init__(self, doji_max_body: float):
        self.doji_max_body = doji_max_body
        self._open: list[ZoneValidator] = []

    def add(self, zone: ZoneBox) -> None:
        self._open.append(ZoneValidator(zone, self.doji_max_body))

    @property
    def open_zones(self) -> list[ZoneBox]:
        return [v.zone for v in self._open]

    def on_candle(self, view: SeriesView) -> list[ZoneTransition]:
        out = [t for v in self._open for t in v.on_candle(view)]
        self._open = [v for v in self._open if not v.state.finished]
        return out
