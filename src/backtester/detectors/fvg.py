"""Fair value gap detector.

Spec: confluences.md › Fair value gap, › Strong-move filter, › Validation.
- 3-candle pattern; the gap lies between the wicks of candle 1 and candle 3, candle 2's
  wick is ignored. Bullish: candle 3's low > candle 1's high, zone = candle 1's high to
  candle 3's low. Bearish mirrored. Equal wicks are no gap; candle 2's color doesn't matter.
- Every gap is an FVG, in both directions and whatever the trend. Which direction is used
  (e.g. only with the trend of the FVG's own timeframe) is decided by the strategy.
- Strong-move filter (switch `FvgConfig.strong_move_filter`, default OFF, rule set by the
  user): when on, candle 2 must be a strong move (range >= k x the ATR of the candles before it, same timeframe).
- Exists from the close of candle 3 (`confirmed_index`). Validation via zone.ZoneBook,
  starting with the candle after candle 3.
- Gaps across the daily break or a weekend count like any other (the detector doesn't
  know about time).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backtester.core.models import Candle, Direction
from backtester.core.series import SeriesView
from backtester.detectors.atr import StrongMoveConfig, StrongMoveFilter
from backtester.detectors.base import Detector, Event
from backtester.detectors.swings import SwingConfig
from backtester.detectors.zone import ZoneBook, ZoneBox, ZoneKind, ZoneTransition


@dataclass(frozen=True, slots=True)
class FvgConfig:
    strong_move_filter: bool = False  # on: candle 2 must be a strong move
    strong_move: StrongMoveConfig = field(default_factory=StrongMoveConfig)


@dataclass(frozen=True, slots=True)
class FairValueGap(Event):
    """Confirmed by candle 3 (`confirmed_index`); candle 1 is `zone.start_index`."""

    zone: ZoneBox
    middle_range: float  # candle 2's range (high - low)
    middle_threshold: float | None  # range candle 2 needed to be strong (None: ATR warm-up)
    strong: bool  # candle 2 was a strong move (always True while the filter is on)

    @property
    def direction(self) -> Direction:
        return self.zone.direction


def gap(c1: Candle, c3: Candle) -> tuple[Direction, float, float] | None:
    """(direction, top, bottom) of the gap between candle 1's and candle 3's wicks."""
    if c3.low > c1.high:
        return Direction.BULLISH, c3.low, c1.high
    if c3.high < c1.low:
        return Direction.BEARISH, c1.low, c3.high
    return None


class FvgDetector(Detector[FairValueGap | ZoneTransition]):
    """Incremental: `update(view)` once per closed candle, in order. Emits the
    transitions of earlier FVGs caused by this candle, then an FVG confirmed by it."""

    def __init__(self, doji_max_body: float, config: FvgConfig | None = None):
        self.config = config = config or FvgConfig()
        self._filter = StrongMoveFilter(config.strong_move)
        self._book = ZoneBook(doji_max_body)
        self._next = 0  # cursor expected next

    @classmethod
    def for_symbol(
        cls, symbol: str, config: FvgConfig | None = None, swing_config: SwingConfig | None = None
    ) -> FvgDetector:
        """The symbol's doji threshold decides which candles can confirm an FVG."""
        return cls((swing_config or SwingConfig()).doji_threshold(symbol), config)

    @property
    def open_zones(self) -> list[ZoneBox]:
        """FVGs not confirmed or invalidated yet."""
        return self._book.open_zones

    def update(self, view: SeriesView) -> list[FairValueGap | ZoneTransition]:
        if view.cursor != self._next:
            raise ValueError(
                f"FvgDetector.update must be called once per candle in order: "
                f"expected cursor {self._next}, got {view.cursor}"
            )
        self._next += 1
        self._filter.update(view)
        events: list[FairValueGap | ZoneTransition] = list(self._book.on_candle(view))
        if view.cursor < 2:
            return events
        c1, c2, c3 = view.last(3)
        found = gap(c1, c3)
        if found is None:
            return events
        middle = view.cursor - 1
        strong = self._filter.is_strong(middle)
        if self.config.strong_move_filter and not strong:
            return events
        direction, top, bottom = found
        closed_at = c3.ts + view.timeframe.duration
        zone = ZoneBox(ZoneKind.FVG, direction, top, bottom, middle - 1, view.cursor, closed_at)
        self._book.add(zone)
        events.append(
            FairValueGap(
                view.cursor, closed_at, zone, c2.range, self._filter.threshold_at(middle), strong
            )
        )
        return events
