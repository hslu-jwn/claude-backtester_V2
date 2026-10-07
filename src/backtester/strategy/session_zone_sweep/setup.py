"""Entry sequence state machine, one per session zone (direction = the zone's role).

Spec: strategy-session-zones.md › Entry sequence, › Invalidation & reset, › Zone flips.
Described for a long on a support zone, short mirrored:

1. SWEEP: a 30m candle's wick goes into the zone (low < top; a touch is no sweep).
2. REACTION: a green 30m candle (never a doji) closes above the zone. It may be the sweep
   candle itself. A red close never counts.
3. BOS: a bullish 5m BOS that closes during that 30m candle or after. Only a real BOS
   (against the 5m trend) counts, unless `entry_bos_with_trend` is on: then any green 5m
   close above the most recent unbroken 5m swing high counts, also in a 5m uptrend.
4. CONFLUENCE: a bullish FVG / OB / BPR that came into existence at or after the BOS leg's
   low is tapped and then confirmed by a green 5m close above it (zone.py validation), on
   a candle after the BOS candle -> enter at that close (`EntrySignal`).

Resets: a real bearish 5m BOS after the bullish one -> back to SWEEP. After an entry the
sequence restarts at SWEEP and only 30m candles closing after the entry count. The zone's
expiry (its session is over) or kill ends the setup (handled by the strategy). A red 30m
close below support (a zone break that flips it to resistance) is the short setup's 30m
reaction: it starts directly at BOS.

`StructureTracker` is strategy 1's view of 5m structure: the shared BOS rule plus the
with-trend breaks the BOS detector swallows (needed for `entry_bos_with_trend`).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from backtester.core.models import Candle, Direction
from backtester.core.series import SeriesView
from backtester.detectors.bos import BROKEN_KIND, breaks
from backtester.detectors.swings import SwingDetector, SwingPoint, is_doji
from backtester.detectors.zone import ZoneBox
from backtester.strategy.session_zone_sweep.zones import SessionZone


def _sign(direction: Direction) -> int:
    return 1 if direction is Direction.BULLISH else -1


@dataclass(frozen=True, slots=True)
class StructureBreak:
    """A close beyond the most recent unbroken swing in `direction` (each level once).
    `is_bos`: it was against the trend, i.e. a real BOS (confluences.md › BOS)."""

    direction: Direction
    index: int  # the breaking candle
    at: datetime  # its close time
    swing: SwingPoint  # the broken swing
    is_bos: bool
    leg_index: int  # the BOS leg's extreme candle (long: lowest low since the swing's wick)
    leg_extreme: float  # its wick price (long: that low)


class StructureTracker:
    """5m swings, BOS and with-trend breaks. `update(view)` once per closed candle, in
    order. Same BOS rule as detectors/bos.py; `trend` = direction of the last real BOS."""

    def __init__(self, doji_max_body: float):
        self._swings = SwingDetector(doji_max_body)
        self.doji_max_body = doji_max_body
        self._open: dict[Direction, SwingPoint | None] = dict.fromkeys(Direction)
        self.trend: Direction | None = None

    def update(self, view: SeriesView) -> list[StructureBreak]:
        new_swings = self._swings.update(view)  # checks the call order
        candle = view.current
        out = []
        for direction, swing in self._open.items():
            if swing is None or not breaks(direction, candle, swing.price, self.doji_max_body):
                continue
            self._open[direction] = None
            is_bos = direction is not self.trend
            if is_bos:
                self.trend = direction
            leg_index, leg_extreme = _leg(view, direction, swing.index)
            closed_at = candle.ts + view.timeframe.duration
            out.append(
                StructureBreak(
                    direction, view.cursor, closed_at, swing, is_bos, leg_index, leg_extreme
                )
            )
        for swing in new_swings:  # swings confirmed now only count from the next candle
            for direction, kind in BROKEN_KIND.items():
                if swing.kind is kind:
                    self._open[direction] = swing
        return out


def _leg(view: SeriesView, direction: Direction, start: int) -> tuple[int, float]:
    """(index, price) of the opposite extreme between the broken swing's wick candle and
    the breaking candle: the low a bullish break started from."""
    sign = _sign(direction)
    best_i, best = start, None
    for i, c in enumerate(view.window(start, view.cursor + 1), start):
        wick = c.low if sign > 0 else c.high
        if best is None or sign * wick < sign * best:
            best_i, best = i, wick
    return best_i, best


class Step(Enum):
    SWEEP = "sweep"
    REACTION = "reaction"
    BOS = "bos"
    CONFLUENCE = "confluence"


@dataclass(frozen=True, slots=True)
class EntrySignal:
    """The setup is complete: enter at the close of 5m candle `index`."""

    direction: Direction
    zone: SessionZone
    confluence: ZoneBox
    bos: StructureBreak
    reaction_open: datetime  # open time of the 30m reaction candle
    index: int  # 5m candle that confirmed the confluence
    at: datetime  # its close time = entry time
    close: float  # entry price


class Setup:
    """The entry sequence for one zone in one direction."""

    def __init__(self, zone: SessionZone, direction: Direction, with_trend_bos: bool = False):
        self.zone = zone
        self.direction = direction
        self.with_trend_bos = with_trend_bos
        self.reset()

    def reset(self, not_before: datetime | None = None) -> None:
        self.step = Step.SWEEP
        self.not_before = not_before  # only 30m candles closing after this count
        self.reaction_open: datetime | None = None
        self.bos: StructureBreak | None = None

    @property
    def _near(self) -> float:
        """The zone edge price comes back from (long: the top)."""
        return self.zone.top if self.direction is Direction.BULLISH else self.zone.bottom

    def on_30m(self, candle: Candle, closed_at: datetime, doji_max_body: float) -> bool:
        """Steps 1 and 2 with a closed 30m candle; True if it was the 30m reaction."""
        if self.step not in (Step.SWEEP, Step.REACTION):
            return False
        if self.not_before is not None and closed_at <= self.not_before:
            return False
        sign = _sign(self.direction)
        wick = candle.low if sign > 0 else candle.high
        if self.step is Step.SWEEP and sign * wick < sign * self._near:
            self.step = Step.REACTION
        if self.step is Step.REACTION and _reacts(
            self.direction, candle, self._near, doji_max_body
        ):
            self.step, self.reaction_open = Step.BOS, candle.ts
            return True
        return False

    def start_from_flip(self, candle: Candle) -> None:
        """A break of the zone that flipped it into this direction is the 30m reaction."""
        self.reset()
        self.step, self.reaction_open = Step.BOS, candle.ts

    def on_breaks(self, structure_breaks: Iterable[StructureBreak]) -> None:
        """Step 3, and the cancel by an opposite BOS, with 5m breaks in time order."""
        for b in structure_breaks:
            same_way = b.direction is self.direction
            if self.step is Step.BOS:
                counts = b.is_bos or self.with_trend_bos
                if same_way and counts and b.at > self.reaction_open:
                    self.step, self.bos = Step.CONFLUENCE, b
            elif self.step is Step.CONFLUENCE and b.is_bos and not same_way:
                if b.index > self.bos.index:
                    self.reset(self.not_before)

    def accepts(self, confluence: ZoneBox, confirmed_index: int) -> bool:
        """Step 4: may `confluence`, confirmed by 5m candle `confirmed_index`, trigger?"""
        return (
            self.step is Step.CONFLUENCE
            and confluence.direction is self.direction
            and confluence.created_index >= self.bos.leg_index
            and confirmed_index > self.bos.index
        )


def _reacts(direction: Direction, candle: Candle, near: float, doji_max_body: float) -> bool:
    if is_doji(candle, doji_max_body):
        return False
    color = candle.is_green if direction is Direction.BULLISH else candle.is_red
    return color and _sign(direction) * candle.close > _sign(direction) * near
