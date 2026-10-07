"""Liquidity sweep detector.

Spec: confluences.md › Liquidity sweep.
Described for a sweep of highs (bearish: it leads to a bearish BOS), lows mirrored:
- Candidate: a candle whose wick goes ABOVE a confirmed swing high (touching is no sweep,
  a close above still counts). Only highs confirmed since the last BOS count, plus the
  swing high that this BOS broke; the swing must be confirmed by an earlier candle than
  the sweeping one. Any such high counts, not only the most recent, and the same high can
  be taken more than once.
- The candidate is the top of the move: a later candle going above its high replaces it
  (it takes the same highs and more).
- It becomes a liquidity sweep when the next bearish BOS (detectors/bos.py, so only against
  the trend) happens before price goes above the candidate's high. The sweep exists from
  the close of that BOS candle. A lower high in between doesn't matter.
- With no BOS after the new high, there is no sweep.

Edge cases (confirmed by the user, spec › Liquidity sweep):
- A bullish BOS candle always closes above the high it breaks, so it is itself a candidate:
  every bearish BOS after a bullish one comes with a sweep.
- A doji's wick can sweep. Before the first BOS on the chart, every confirmed high counts.
- One candle can be both the sweeping candle and the BOS candle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from backtester.core.models import Candle, Direction
from backtester.core.series import SeriesView
from backtester.detectors.base import Detector, Event
from backtester.detectors.bos import BosDetector, BreakOfStructure
from backtester.detectors.swings import SwingConfig, SwingDetector, SwingKind, SwingPoint

# The swing kind a sweep of each direction takes (a bearish sweep takes highs).
SWEPT_KIND = {Direction.BEARISH: SwingKind.HIGH, Direction.BULLISH: SwingKind.LOW}
OPPOSITE = {Direction.BULLISH: Direction.BEARISH, Direction.BEARISH: Direction.BULLISH}


def wick(direction: Direction, candle: Candle) -> float:
    """The wick a sweep of `direction` reaches with: the high for a sweep of highs."""
    return candle.high if direction is Direction.BEARISH else candle.low


def beyond(direction: Direction, price: float, level: float) -> bool:
    """`price` is strictly past `level` on the swept side (above it for a sweep of highs)."""
    return price > level if direction is Direction.BEARISH else price < level


@dataclass(frozen=True, slots=True)
class LiquiditySweep(Event):
    """Exists from the BOS candle (`confirmed_index`), not from the sweeping candle."""

    direction: Direction  # bearish: a sweep of highs (leads to a bearish BOS)
    index: int  # the sweeping candle (the top of the move)
    ts: datetime  # open time of that candle
    extreme: float  # its wick (the top of the move)
    swept: tuple[SwingPoint, ...]  # the swings it took, least to most extreme
    bos: BreakOfStructure  # the BOS that made it a sweep

    @property
    def swing(self) -> SwingPoint:
        """The most extreme swing taken (the highest high for a sweep of highs)."""
        return self.swept[-1]


@dataclass(frozen=True, slots=True)
class _Candidate:
    index: int
    ts: datetime
    extreme: float
    swept: tuple[SwingPoint, ...]


@dataclass(slots=True)
class _Side:
    """State of one sweep direction: the swings it may take and the current top."""

    levels: list[SwingPoint] = field(default_factory=list)
    candidate: _Candidate | None = None


class SweepDetector(Detector[LiquiditySweep]):
    """Incremental: `update(view)` once per closed candle, in order. Runs its own BOS
    detector on the same view (`bos`)."""

    def __init__(self, doji_max_body: float):
        self.doji_max_body = doji_max_body
        self.bos = BosDetector(SwingDetector(doji_max_body))
        self._sides = {d: _Side() for d in Direction}

    @classmethod
    def for_symbol(cls, symbol: str, config: SwingConfig | None = None) -> SweepDetector:
        return cls((config or SwingConfig()).doji_threshold(symbol))

    def update(self, view: SeriesView) -> list[LiquiditySweep]:
        # the swing detector inside checks the call order (once per candle, in order)
        swings_before = len(self.bos.swings)
        breaks = {b.direction: b for b in self.bos.update(view)}
        new_swings = self.bos.swings[swings_before:]
        events = []
        for direction, side in self._sides.items():
            opposite = breaks.get(OPPOSITE[direction])
            if opposite is not None:
                # a new trend: only the level that BOS broke and later swings count
                side.levels, side.candidate = [opposite.swing], None
            self._take(view, direction, side)
            bos = breaks.get(direction)
            if bos is not None:
                if side.candidate is not None:
                    c = side.candidate
                    events.append(
                        LiquiditySweep(
                            bos.confirmed_index,
                            bos.confirmed_at,
                            direction,
                            c.index,
                            c.ts,
                            c.extreme,
                            c.swept,
                            bos,
                        )
                    )
                side.levels, side.candidate = [], None
        # swings confirmed by this candle can only be taken from the next candle on
        for swing in new_swings:
            for direction, side in self._sides.items():
                if swing.kind is SWEPT_KIND[direction]:
                    side.levels.append(swing)
        return events

    def _take(self, view: SeriesView, direction: Direction, side: _Side) -> None:
        """Make the current candle the candidate if it is the new top and took a level."""
        candle = view.current
        price = wick(direction, candle)
        if side.candidate is not None and not beyond(direction, price, side.candidate.extreme):
            return
        swept = [s for s in side.levels if beyond(direction, price, s.price)]
        if not swept:
            return
        swept.sort(key=lambda s: s.price, reverse=direction is Direction.BULLISH)
        side.candidate = _Candidate(view.cursor, candle.ts, price, tuple(swept))
