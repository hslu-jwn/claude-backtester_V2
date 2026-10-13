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

Reworked rules (user, 2026-10-12, all off by default until the user settles them on the chart):
- `equal_tolerance_atr` not None: a candle is a candidate only if its wick is beyond the
  required level: the least extreme of the last N highs lying within the tolerance (in
  ATR of this timeframe, known before the candle) of the most extreme one. 0 is the spec's
  "the most extreme of the last N must be taken", inf is "one of the last N" (None, the
  default, is that too). While the ATR is not known the tolerance is 0.
- `two_closes_cancel`: `cancel_closes` (2) consecutive closes beyond the swept level
  (dojis skipped, they neither count nor break the streak) make it a breakout, not a
  sweep: the candidate is dropped and the levels the closes are beyond are no longer
  sweepable. `cancel_wick_first`: only the newest candle of the streak must close beyond,
  the older ones need just their wick beyond ("one wick, one close").
- `bos_before_top`: the BOS must break a swing made before the top candle (the structure
  the move up was built on); a break of the top candle's own low or of a later low is
  ignored and the candidate waits for another BOS (or expires).

Edge cases (confirmed by the user, spec › Liquidity sweep):
- A bullish BOS candle always closes above the high it breaks, so it is itself a candidate.
- A doji's wick can sweep.
- One candle can be both the sweeping candle and the BOS candle.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime

from backtester.core.models import Candle, Direction
from backtester.core.series import SeriesView
from backtester.detectors.atr import Atr
from backtester.detectors.base import Detector, Event
from backtester.detectors.bos import BosDetector, BreakOfStructure
from backtester.detectors.swings import (
    SwingConfig,
    SwingDetector,
    SwingKind,
    SwingPoint,
    is_doji,
)

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
    # None: one of the last N is enough; else the tolerance (x ATR) of the "same height" rule
    equal_tolerance_atr: float | None = None
    atr_period: int = 14  # ATR the tolerance is measured in
    two_closes_cancel: bool = False  # closes beyond the level: breakout, not a sweep
    cancel_closes: int = 2  # how many consecutive closes beyond make it a breakout
    # the older candles of that streak need only their wick beyond, the newest a close
    cancel_wick_first: bool = False
    # the BOS must break a swing made before the top, not the top candle's own low or later
    bos_before_top: bool = False

    def __post_init__(self) -> None:
        if self.equal_tolerance_atr is not None and self.equal_tolerance_atr < 0:
            raise ValueError("equal_tolerance_atr must be >= 0")
        if self.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if self.cancel_closes < 1:
            raise ValueError("cancel_closes must be >= 1")
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
    detector on the same view (`bos`); the current candle's BOS are in `breaks`."""

    def __init__(self, doji_max_body: float, config: SweepConfig | None = None):
        self.doji_max_body = doji_max_body
        self.config = config or SweepConfig()
        self.bos = BosDetector(SwingDetector(doji_max_body))
        self._atr = Atr(self.config.atr_period)
        self._sides = {d: _Side() for d in Direction}
        self.breaks: list[BreakOfStructure] = []

    @classmethod
    def for_symbol(
        cls, symbol: str, config: SwingConfig | None = None, sweep: SweepConfig | None = None
    ) -> SweepDetector:
        return cls((config or SwingConfig()).doji_threshold(symbol), sweep)

    def update(self, view: SeriesView) -> list[LiquiditySweep]:
        # the swing detector inside checks the call order (once per candle, in order)
        atr_before = self._atr.current  # known at the previous close
        self._atr.update(view)
        swings_before = len(self.bos.swings)
        self.breaks = self.bos.update(view)
        breaks = {b.direction: b for b in self.breaks}
        new_swings = self.bos.swings[swings_before:]
        events = []
        for direction, side in self._sides.items():
            c = side.candidate
            if c is not None and view.cursor - c.index > self.config.bos_within:
                side.candidate = None  # no BOS in time: no sweep from this top
            self._take(view, direction, side, atr_before)
            if self.config.two_closes_cancel:
                self._cancel_breakout(view, direction, side)
            bos = breaks.get(direction)
            if bos is not None:
                c = side.candidate
                if c is not None and self.config.bos_before_top and bos.swing.index >= c.index:
                    continue  # breaks a swing made at or after the top: not the structure
                if c is not None:
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

    def _required(
        self, direction: Direction, levels: list[SwingPoint], atr: float | None
    ) -> SwingPoint | None:
        """The level a wick must be beyond: the least extreme level within the tolerance
        of the most extreme one (`equal_tolerance_atr`)."""
        if not levels:
            return None
        multiple = self.config.equal_tolerance_atr or 0.0
        tolerance = 0.0 if atr is None else (math.inf if math.isinf(multiple) else multiple * atr)
        sign = 1 if direction is Direction.BEARISH else -1
        top = max(s.price * sign for s in levels)
        group = [s for s in levels if top - s.price * sign <= tolerance]
        return min(group, key=lambda s: s.price * sign)

    def _cancel_breakout(self, view: SeriesView, direction: Direction, side: _Side) -> None:
        """`cancel_closes` consecutive (non-doji) candles beyond the swept level, the newest
        closing beyond it: no sweep, the levels the closes are beyond are accepted and drop
        out. With `cancel_wick_first` the older candles need only their wick beyond."""
        c = side.candidate
        if c is None:
            return
        level = c.swept[-1].price
        counted, closes = 0, []
        for i in range(view.cursor, -1, -1):
            candle = view[i]
            if is_doji(candle, self.doji_max_body):
                continue
            closed = beyond(direction, candle.close, level)
            wick_only = self.config.cancel_wick_first and counted > 0
            if not (beyond(direction, wick(direction, candle), level) if wick_only else closed):
                return
            counted += 1
            if closed:
                closes.append(candle.close)
            if counted == self.config.cancel_closes:
                break
        else:
            return
        accepted = min(closes) if direction is Direction.BEARISH else max(closes)
        side.levels = [s for s in side.levels if not beyond(direction, accepted, s.price)]
        side.candidate = None

    def _take(
        self, view: SeriesView, direction: Direction, side: _Side, atr: float | None = None
    ) -> None:
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
        if swept and self.config.equal_tolerance_atr is not None:
            required = self._required(direction, side.levels, atr)
            if required not in swept:
                swept = []
        if not swept:
            side.candidate = None  # nothing swept; a top it went beyond is no sweep any more
            return
        swept.sort(key=lambda s: s.price, reverse=direction is Direction.BULLISH)
        side.candidate = _Candidate(view.cursor, candle.ts, price, tuple(swept))
