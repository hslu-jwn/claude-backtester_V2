"""Order block detector.

Spec: confluences.md › Order block, › Strong-move filter, › Validation.
Described for a bullish OB, bearish mirrored:
- Only OBs that led to a BOS: at a bullish BOS, the OB is the red leg into the most recent
  swing low, including a low confirmed by the BOS candle itself (rule set by the user).
- Leg: walking back from the low's red turn candle, every red candle until the first green
  one; dojis are skipped and their wicks don't count. Range = lowest to highest wick of the
  red candles only, so a lower wick on the green turn candle is NOT in the OB (rule set by
  the user).
- Exists from the close of the BOS candle. With the strong-move filter on (default for
  OBs), at least one candle of the move away must be a strong move: the window runs from
  the low's green turn candle up to the candle BEFORE the one that confirms the next swing
  high (that candle starts the pullback and doesn't count, rule set by the user). The OB
  then exists from the later of the BOS candle and the first strong candle; if the next
  swing high is confirmed first, there is no OB.
- Validation via zone.ZoneBook, starting with the candle after the one it exists from.
Since a BOS only happens against the trend, OBs only form where the trend flips.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from backtester.core.models import Candle, Direction
from backtester.core.series import SeriesView
from backtester.detectors.atr import StrongMoveConfig, StrongMoveFilter
from backtester.detectors.base import Detector, Event
from backtester.detectors.bos import BosDetector, BreakOfStructure
from backtester.detectors.swings import SwingConfig, SwingDetector, SwingKind, SwingPoint, is_doji
from backtester.detectors.zone import ZoneBook, ZoneBox, ZoneKind, ZoneTransition

# The swing an OB of each direction is the leg into, and the swing that ends its move away.
LEG_SWING = {Direction.BULLISH: SwingKind.LOW, Direction.BEARISH: SwingKind.HIGH}
END_SWING = {Direction.BULLISH: SwingKind.HIGH, Direction.BEARISH: SwingKind.LOW}


@dataclass(frozen=True, slots=True)
class OrderBlockConfig:
    strong_move_filter: bool = True  # a candle of the move away must be a strong move
    strong_move: StrongMoveConfig = field(default_factory=StrongMoveConfig)


@dataclass(frozen=True, slots=True)
class OrderBlock(Event):
    """Exists from `confirmed_index`: the BOS candle, or the first strong candle after it."""

    zone: ZoneBox  # start_index = the leg's first candle
    swing: SwingPoint  # the swing the leg runs into
    bos: BreakOfStructure  # the BOS the move away made
    strong_index: int | None  # first strong candle of the move away so far (None: none)
    strong_threshold: float | None  # range that candle needed (k x ATR before it)
    strong_at: datetime | None  # close time of that candle

    @property
    def direction(self) -> Direction:
        return self.zone.direction


@dataclass(slots=True)
class _Pending:
    """An OB whose BOS happened but whose move away had no strong candle yet."""

    direction: Direction
    swing: SwingPoint
    bos: BreakOfStructure
    leg: tuple[int, float, float]  # (first candle, bottom, top)


def leg_color(direction: Direction, candle: Candle) -> bool:
    """The candle has the leg's color: red for a bullish OB, green for a bearish one."""
    return candle.is_red if direction is Direction.BULLISH else candle.is_green


def find_leg(
    view: SeriesView, direction: Direction, swing: SwingPoint, doji_max_body: float
) -> tuple[int, float, float]:
    """(first candle, bottom, top) of the leg into `swing`: its same-color turn candle and
    the same-color candles before it up to the first opposite-color one, dojis skipped."""
    first, low, high = swing.first_index, float("inf"), float("-inf")
    for i in range(swing.first_index, -1, -1):
        candle = view[i]
        if is_doji(candle, doji_max_body):
            continue
        if not leg_color(direction, candle):
            break
        first, low, high = i, min(low, candle.low), max(high, candle.high)
    return first, low, high


class OrderBlockDetector(Detector[OrderBlock | ZoneTransition]):
    """Incremental: `update(view)` once per closed candle, in order. Emits the transitions
    of earlier OBs caused by this candle, then an OB that exists from this candle."""

    def __init__(self, doji_max_body: float, config: OrderBlockConfig | None = None):
        self.config = config = config or OrderBlockConfig()
        self.doji_max_body = doji_max_body
        self._bos = BosDetector(SwingDetector(doji_max_body))
        self._filter = StrongMoveFilter(config.strong_move)
        self._book = ZoneBook(doji_max_body)
        self._pending: list[_Pending] = []

    @classmethod
    def for_symbol(
        cls,
        symbol: str,
        config: OrderBlockConfig | None = None,
        swing_config: SwingConfig | None = None,
    ) -> OrderBlockDetector:
        return cls((swing_config or SwingConfig()).doji_threshold(symbol), config)

    @property
    def open_zones(self) -> list[ZoneBox]:
        """OBs not confirmed or invalidated yet."""
        return self._book.open_zones

    def update(self, view: SeriesView) -> list[OrderBlock | ZoneTransition]:
        # the swing detector inside checks the call order (once per candle, in order)
        swings_before = len(self._bos.swings)
        breaks = self._bos.update(view)
        new_swings = self._bos.swings[swings_before:]
        self._filter.update(view)
        events: list[OrderBlock | ZoneTransition] = list(self._book.on_candle(view))

        still = []
        for p in self._pending:
            if any(s.kind is END_SWING[p.direction] for s in new_swings):
                continue  # the move away ended without a strong candle: no OB
            if self._filter.is_strong(view.cursor):
                events.append(self._create(view, p, view.cursor))
            else:
                still.append(p)
        self._pending = still

        for bos in breaks:
            swing = self._latest(LEG_SWING[bos.direction])
            if swing is None:
                continue
            leg = find_leg(view, bos.direction, swing, self.doji_max_body)
            pending = _Pending(bos.direction, swing, bos, leg)
            strong = self._first_strong(swing.confirmed_index, view.cursor)
            if not self.config.strong_move_filter or strong is not None:
                events.append(self._create(view, pending, strong))
            else:
                self._pending.append(pending)
        return events

    def _latest(self, kind: SwingKind) -> SwingPoint | None:
        """Most recent swing of `kind`, also one confirmed by the current candle."""
        return next((s for s in reversed(self._bos.swings) if s.kind is kind), None)

    def _first_strong(self, start: int, stop: int) -> int | None:
        return next((i for i in range(start, stop + 1) if self._filter.is_strong(i)), None)

    def _create(self, view: SeriesView, p: _Pending, strong: int | None) -> OrderBlock:
        first, bottom, top = p.leg
        closed_at = view.current.ts + view.timeframe.duration
        zone = ZoneBox(
            ZoneKind.ORDER_BLOCK, p.direction, top, bottom, first, view.cursor, closed_at
        )
        self._book.add(zone)
        threshold = strong_at = None
        if strong is not None:
            threshold = self._filter.threshold_at(strong)
            strong_at = view[strong].ts + view.timeframe.duration
        return OrderBlock(
            view.cursor, closed_at, zone, p.swing, p.bos, strong, threshold, strong_at
        )
