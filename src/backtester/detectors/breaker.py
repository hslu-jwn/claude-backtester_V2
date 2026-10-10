"""Breaker block detector.

Spec: confluences.md › Breaker block (rules set by the user 2026-10-10), › Validation.
Described bullish, bearish mirrored:
- Created by every bullish BOS (detectors/bos.py, so only real BOS): the BOS candle closes
  above the most recent swing high H. The breaker is the move up that formed H.
- Range = the last unbroken run of green candles into H, lowest to highest wick of those
  green candles: walking back from H's green turn candle, dojis are skipped (their wicks
  don't count) and the first red candle ends the run. The red turn candle is not part of
  it, so a higher wick on it is not in the zone. (Same walk as the OB leg,
  `order_block.find_leg`, with the other color.)
- Bias bullish. Exists from the close of the BOS candle; validation (zone.ZoneBook) starts
  with the next candle.
"""

from __future__ import annotations

from dataclasses import dataclass

from backtester.core.models import Direction
from backtester.core.series import SeriesView
from backtester.detectors.base import Detector, Event
from backtester.detectors.bos import BosDetector, BreakOfStructure
from backtester.detectors.order_block import find_leg
from backtester.detectors.swings import SwingConfig, SwingDetector, SwingPoint
from backtester.detectors.zone import ZoneBook, ZoneBox, ZoneKind, ZoneTransition

# find_leg walks the candles of a direction's OB color (red for bullish), so a bullish
# breaker (green run) uses the bearish walk
RUN_COLOR = {Direction.BULLISH: Direction.BEARISH, Direction.BEARISH: Direction.BULLISH}


@dataclass(frozen=True, slots=True)
class BreakerBlock(Event):
    """Exists from the BOS candle (`confirmed_index`)."""

    zone: ZoneBox  # start_index = the run's first candle
    swing: SwingPoint  # the broken swing (H)
    bos: BreakOfStructure

    @property
    def direction(self) -> Direction:
        return self.zone.direction


class BreakerDetector(Detector[BreakerBlock | ZoneTransition]):
    """Incremental: `update(view)` once per closed candle, in order. Emits the transitions
    of earlier breakers caused by this candle, then a breaker made by this candle's BOS."""

    def __init__(self, doji_max_body: float):
        self.doji_max_body = doji_max_body
        self._bos = BosDetector(SwingDetector(doji_max_body))
        self._book = ZoneBook(doji_max_body)

    @classmethod
    def for_symbol(cls, symbol: str, config: SwingConfig | None = None) -> BreakerDetector:
        return cls((config or SwingConfig()).doji_threshold(symbol))

    def update(self, view: SeriesView) -> list[BreakerBlock | ZoneTransition]:
        breaks = self._bos.update(view)  # the swing detector inside checks the call order
        events: list[BreakerBlock | ZoneTransition] = list(self._book.on_candle(view))
        for bos in breaks:
            first, bottom, top = find_leg(
                view, RUN_COLOR[bos.direction], bos.swing, self.doji_max_body
            )
            zone = ZoneBox(
                ZoneKind.BREAKER, bos.direction, top, bottom, first, view.cursor, bos.confirmed_at
            )
            self._book.add(zone)
            events.append(BreakerBlock(view.cursor, bos.confirmed_at, zone, bos.swing, bos))
        return events
