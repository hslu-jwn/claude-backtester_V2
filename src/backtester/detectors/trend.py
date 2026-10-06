"""Trend, defined only by BOS.

Spec: confluences.md › Trend.
- After a bullish BOS the market is in an uptrend, after a bearish BOS in a downtrend.
- It stays in that trend until a BOS in the other direction, which flips it immediately.
- A break in the trend's own direction is no BOS (detectors/bos.py), so every BOS after
  the first one flips the trend.
- Before the first BOS there is no trend.
- The **overall trend** is the trend on one fixed timeframe, 4H by default (setting:
  `TrendConfig.overall_timeframe`). The detector itself is timeframe-agnostic; callers
  run it on that timeframe.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

from backtester.core.models import Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.detectors.base import Detector, Event
from backtester.detectors.bos import BosDetector, BreakOfStructure


@dataclass(frozen=True, slots=True)
class TrendConfig:
    overall_timeframe: Timeframe = Timeframe.H4  # the timeframe of the overall trend


class Trend(Enum):
    NONE = "none"
    UP = "up"
    DOWN = "down"


TREND_AFTER = {Direction.BULLISH: Trend.UP, Direction.BEARISH: Trend.DOWN}


@dataclass(frozen=True, slots=True)
class TrendChange(Event):
    """Confirmed by the BOS candle that set the trend."""

    previous: Trend
    trend: Trend
    bos: BreakOfStructure


class TrendState:
    """The trend rule, one BOS at a time (shared by the detector and the chart)."""

    def __init__(self) -> None:
        self.trend = Trend.NONE

    def on_bos(self, bos: BreakOfStructure) -> TrendChange | None:
        """The change `bos` causes (None only if it is in the trend's direction, which the
        BOS detector never emits)."""
        new = TREND_AFTER[bos.direction]
        if new is self.trend:
            return None
        change = TrendChange(bos.confirmed_index, bos.confirmed_at, self.trend, new, bos)
        self.trend = new
        return change


def trend_at(bos_events: Sequence[BreakOfStructure], cursor: int) -> TrendChange | None:
    """The change that set the trend at candle `cursor` (None: no BOS yet, no trend)."""
    state, last = TrendState(), None
    for bos in bos_events:
        if bos.confirmed_index > cursor:
            break
        last = state.on_bos(bos) or last
    return last


class TrendDetector(Detector[TrendChange]):
    """Incremental: `update(view)` once per closed candle, in order. Emits a change when a
    BOS sets or flips the trend; `trend` is the trend after the latest candle."""

    def __init__(self, bos_detector: BosDetector):
        self._bos_detector = bos_detector
        self._state = TrendState()

    @property
    def trend(self) -> Trend:
        return self._state.trend

    def update(self, view: SeriesView) -> list[TrendChange]:
        changes = [self._state.on_bos(bos) for bos in self._bos_detector.update(view)]
        return [c for c in changes if c is not None]
