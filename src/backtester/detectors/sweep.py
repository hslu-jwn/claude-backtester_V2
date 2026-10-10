"""Liquidity sweep detector.

Spec: confluences.md › Liquidity sweep.
Described for a sweep of highs (bearish: it leads to a bearish BOS), lows mirrored:
- Candidate: a candle whose wick goes ABOVE one of the last N confirmed swing highs
  (`SweepConfig.lookback_swings`, default 3; touching is no sweep). A close above the
  high still counts (`close_beyond_counts`, default on); off: a candle closing above a
  high doesn't sweep that high. The swing must be confirmed by an earlier candle than
  the sweeping one. The same high can be taken more than once. The swept level is the
  furthest high taken among the last N (more than N taken: level #N).
- The candidate is the top of the move: a later candle going above its high replaces it
  (it takes the same highs and more) and restarts the count below. With
  `close_beyond_counts` off such a candle may sweep nothing (it closed above every high);
  price then went above the top before any BOS, so the candidate is dropped.
- It becomes a liquidity sweep when a bearish BOS (detectors/bos.py, so only against the
  trend) happens before price goes above the candidate's high, at most
  `SweepConfig.bos_within` candles (default 10) after the top (same candle = 0). The
  sweep exists from the close of that BOS candle. A lower high in between doesn't matter.
- With no BOS in time, there is no sweep: the candidate is dropped, and a later candle
  taking one of the last N highs starts a new one, even below the old top.

Edge cases (confirmed by the user, spec › Liquidity sweep):
- A bullish BOS candle always closes above the high it breaks, so it is itself a candidate.
- A doji's wick can sweep.
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


def wick(direction: Direction, candle: Candle) -> float:
    """The wick a sweep of `direction` reaches with: the high for a sweep of highs."""
    return candle.high if direction is Direction.BEARISH else candle.low


def beyond(direction: Direction, price: float, level: float) -> bool:
    """`price` is strictly past `level` on the swept side (above it for a sweep of highs)."""
    return price > level if direction is Direction.BEARISH else price < level


@dataclass(frozen=True, slots=True)
class SweepConfig:
    lookback_swings: int = 3  # N: a wick beyond one of the last N swings is a candidate
    bos_within: int = 10  # X: the BOS must close at most X candles after the top
    close_beyond_counts: bool = True  # off: a candle closing beyond a level doesn't sweep it

    def __post_init__(self) -> None:
        if self.lookback_swings < 1:
            raise ValueError("lookback_swings must be >= 1")
        if self.bos_within < 0:
            raise ValueError("bos_within must be >= 0")


@dataclass(frozen=True, slots=True)
class LiquiditySweep(Event):
    """Exists from the BOS candle (`confirmed_index`), not from the sweeping candle."""

    direction: Direction  # bearish: a sweep of highs (leads to a bearish BOS)
    index: int  # the sweeping candle (the top of the move)
    ts: datetime  # open time of that candle
    extreme: float  # its wick (the top of the move)
    swept: tuple[SwingPoint, ...]  # the swings it took among the last N, least to most extreme
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
    """State of one sweep direction: the confirmed swings of the kind it takes (only the
    last N are kept) and the current top."""

    levels: list[SwingPoint] = field(default_factory=list)
    candidate: _Candidate | None = None


class SweepDetector(Detector[LiquiditySweep]):
    """Incremental: `update(view)` once per closed candle, in order. Runs its own BOS
    detector on the same view (`bos`)."""

    def __init__(self, doji_max_body: float, config: SweepConfig | None = None):
        self.doji_max_body = doji_max_body
        self.config = config or SweepConfig()
        self.bos = BosDetector(SwingDetector(doji_max_body))
        self._sides = {d: _Side() for d in Direction}

    @classmethod
    def for_symbol(
        cls, symbol: str, config: SwingConfig | None = None, sweep: SweepConfig | None = None
    ) -> SweepDetector:
        return cls((config or SwingConfig()).doji_threshold(symbol), sweep)

    def update(self, view: SeriesView) -> list[LiquiditySweep]:
        # the swing detector inside checks the call order (once per candle, in order)
        swings_before = len(self.bos.swings)
        breaks = {b.direction: b for b in self.bos.update(view)}
        new_swings = self.bos.swings[swings_before:]
        events = []
        for direction, side in self._sides.items():
            c = side.candidate
            if c is not None and view.cursor - c.index > self.config.bos_within:
                side.candidate = None  # no BOS in time: no sweep from this top
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
                side.candidate = None
        # swings confirmed by this candle can only be taken from the next candle on
        for swing in new_swings:
            for direction, side in self._sides.items():
                if swing.kind is SWEPT_KIND[direction]:
                    side.levels = [*side.levels, swing][-self.config.lookback_swings :]
        return events

    def _take(self, view: SeriesView, direction: Direction, side: _Side) -> None:
        """Make the current candle the candidate if it is the new top and took a level."""
        candle = view.current
        price = wick(direction, candle)
        if side.candidate is not None and not beyond(direction, price, side.candidate.extreme):
            return
        swept = [
            s
            for s in side.levels
            if beyond(direction, price, s.price)
            and (self.config.close_beyond_counts or not beyond(direction, candle.close, s.price))
        ]
        if not swept:
            side.candidate = None  # nothing swept; a top it went beyond is no sweep any more
            return
        swept.sort(key=lambda s: s.price, reverse=direction is Direction.BULLISH)
        side.candidate = _Candidate(view.cursor, candle.ts, price, tuple(swept))
