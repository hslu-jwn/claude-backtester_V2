"""Break of structure (BOS).

Spec: confluences.md › Break of structure (BOS).
- Bullish BOS: a GREEN candle closes above the most recent confirmed swing high (its wick
  price). Bearish mirrored: a red candle closes below the most recent swing low. A wick
  alone never counts, and only a move in the BOS direction can cause it. A doji (body <=
  the symbol's doji threshold) is neither green nor red, so it never causes a BOS.
- The swing must already be confirmed when the breaking candle closes, so a swing confirmed
  by the candle itself is not used.
- A BOS only happens AGAINST the current trend (see detectors/trend.py): in a downtrend a
  close below the latest swing low (a lower low) is no BOS, it changes nothing, but that
  level is used up all the same. So BOS directions alternate; before the first BOS either
  direction counts. The detector tracks the trend itself (trend = direction of the last
  BOS).
- Only the most recent swing high (low) can be broken, and only once. Once it is broken,
  there is no new bullish (bearish) BOS until a new swing high (low) is confirmed, even
  if price later closes above an older, higher, never-broken high.
Note: strategy 1's "5m BOS" (strategy-session-zones.md › Entry sequence step 3) is this
BOS on the 5m chart.
"""

from __future__ import annotations

from dataclasses import dataclass

from backtester.core.models import Candle, Direction
from backtester.core.series import SeriesView
from backtester.detectors.base import Detector, Event
from backtester.detectors.swings import (
    SwingConfig,
    SwingDetector,
    SwingKind,
    SwingPoint,
    is_doji,
)

# The swing kind a BOS of each direction breaks.
BROKEN_KIND = {Direction.BULLISH: SwingKind.HIGH, Direction.BEARISH: SwingKind.LOW}


@dataclass(frozen=True, slots=True)
class BreakOfStructure(Event):
    """Confirmed by the breaking candle (`confirmed_index`)."""

    direction: Direction
    swing: SwingPoint  # the broken swing
    close: float  # close of the breaking candle

    @property
    def price(self) -> float:
        """The broken level (the swing's wick price)."""
        return self.swing.price


def breaks(direction: Direction, candle: Candle, level: float, doji_max_body: float) -> bool:
    """True if `candle` closes beyond `level` with a move in `direction` (never a doji)."""
    if is_doji(candle, doji_max_body):
        return False
    if direction is Direction.BULLISH:
        return candle.is_green and candle.close > level
    return candle.is_red and candle.close < level


class BosDetector(Detector[BreakOfStructure]):
    """Incremental: `update(view)` once per closed candle, in order. Runs its own swing
    detector on the same view; the swings it saw are in `swings`."""

    def __init__(self, swing_detector: SwingDetector):
        self._swing_detector = swing_detector
        self.swings: list[SwingPoint] = []
        self.new_swings: list[SwingPoint] = []
        # most recent swing of each direction's kind that is not broken yet
        self._open: dict[Direction, SwingPoint | None] = dict.fromkeys(Direction)
        self.trend: Direction | None = None  # direction of the last BOS (None: no BOS yet)

    @classmethod
    def for_symbol(cls, symbol: str, config: SwingConfig | None = None) -> BosDetector:
        return cls(SwingDetector.for_symbol(symbol, config))

    def update(self, view: SeriesView) -> list[BreakOfStructure]:
        # the swing detector checks the call order (once per candle, in order)
        self.new_swings = new_swings = self._swing_detector.update(view)
        candle = view.current
        events = []
        for direction, swing in self._open.items():
            if swing is not None and breaks(
                direction, candle, swing.price, self._swing_detector.doji_max_body
            ):
                self._open[direction] = None  # used up, also by a break with the trend
                if direction is self.trend:
                    continue
                self.trend = direction
                events.append(
                    BreakOfStructure(
                        confirmed_index=view.cursor,
                        confirmed_at=candle.ts + view.timeframe.duration,
                        direction=direction,
                        swing=swing,
                        close=candle.close,
                    )
                )
        # swings confirmed by this candle only count from the next candle on
        for swing in new_swings:
            self.swings.append(swing)
            for direction, kind in BROKEN_KIND.items():
                if swing.kind is kind:
                    self._open[direction] = swing
        return events
