"""Balanced price range detector.

Spec: confluences.md › Balanced price range, › Strong-move filter, › Validation.
- Overlap of an older FVG and a newer FVG in the opposite direction, where the older one
  is invalidated by the move that creates the newer one: by a candle from the newer FVG's
  candle 1 to its candle 3 (rule set by the user). An older FVG still open when the newer
  one forms, or finished before its candle 1, forms no BPR.
- Range = the overlap of the two FVG ranges, using the older one's stored range; edges
  that only touch are no overlap. Direction = the newer FVG's direction.
- Several older FVGs invalidated by the move each form their own BPR with the newer one;
  an older FVG forms at most one BPR (the first newer FVG that qualifies).
- Exists from the close of the newer FVG's candle 3. Validation via zone.ZoneBook,
  starting with the next candle. Staleness rules, if any, are the strategy's.
- Built on FvgDetector, so the FVG strong-move filter (`BprConfig.fvg`) applies.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backtester.core.series import SeriesView
from backtester.detectors.base import Detector, Event
from backtester.detectors.fvg import FairValueGap, FvgConfig, FvgDetector
from backtester.detectors.swings import SwingConfig
from backtester.detectors.zone import ZoneBook, ZoneBox, ZoneKind, ZoneState, ZoneTransition


@dataclass(frozen=True, slots=True)
class BprConfig:
    fvg: FvgConfig = field(default_factory=FvgConfig)


@dataclass(frozen=True, slots=True)
class BalancedPriceRange(Event):
    """Exists from the newer FVG's candle 3 (`confirmed_index`)."""

    zone: ZoneBox
    newer: ZoneBox  # the FVG that formed it (its direction is the BPR's)
    older: ZoneBox  # the opposite FVG it invalidated
    older_invalidated_index: int  # candle that invalidated the older FVG


def overlap(a: ZoneBox, b: ZoneBox) -> tuple[float, float] | None:
    """(top, bottom) of the overlap of two ranges; None if they don't overlap."""
    top, bottom = min(a.top, b.top), max(a.bottom, b.bottom)
    return (top, bottom) if top > bottom else None


class BprDetector(Detector[BalancedPriceRange | ZoneTransition]):
    """Incremental: `update(view)` once per closed candle, in order. Emits the transitions
    of earlier BPRs caused by this candle, then the BPRs that exist from this candle."""

    def __init__(self, doji_max_body: float, config: BprConfig | None = None):
        self.config = config = config or BprConfig()
        self._fvg = FvgDetector(doji_max_body, config.fvg)
        self._book = ZoneBook(doji_max_body)
        # FVGs invalidated by one of the last 3 candles and not paired yet: (zone, index)
        self._invalidated: list[tuple[ZoneBox, int]] = []

    @classmethod
    def for_symbol(
        cls, symbol: str, config: BprConfig | None = None, swing_config: SwingConfig | None = None
    ) -> BprDetector:
        return cls((swing_config or SwingConfig()).doji_threshold(symbol), config)

    @property
    def open_zones(self) -> list[ZoneBox]:
        """BPRs not confirmed or invalidated yet."""
        return self._book.open_zones

    def update(self, view: SeriesView) -> list[BalancedPriceRange | ZoneTransition]:
        fvg_events = self._fvg.update(view)  # raises if out of order
        events: list[BalancedPriceRange | ZoneTransition] = list(self._book.on_candle(view))
        # a newer FVG confirmed now has candle 1 two candles back
        self._invalidated = [(z, i) for z, i in self._invalidated if i >= view.cursor - 2]
        for e in fvg_events:
            if isinstance(e, ZoneTransition) and e.state is ZoneState.INVALIDATED:
                self._invalidated.append((e.zone, e.confirmed_index))
            elif isinstance(e, FairValueGap):
                events.extend(self._pair(e))
        return events

    def _pair(self, fvg: FairValueGap) -> list[BalancedPriceRange]:
        newer, out, unpaired = fvg.zone, [], []
        for older, index in self._invalidated:
            found = None
            if older.direction is not newer.direction and index >= newer.start_index:
                found = overlap(older, newer)
            if found is None:
                unpaired.append((older, index))
                continue
            top, bottom = found
            zone = ZoneBox(
                ZoneKind.BPR,
                newer.direction,
                top,
                bottom,
                min(older.start_index, newer.start_index),
                newer.created_index,
                newer.created_at,
            )
            self._book.add(zone)
            out.append(
                BalancedPriceRange(fvg.confirmed_index, fvg.confirmed_at, zone, newer, older, index)
            )
        self._invalidated = unpaired
        return out
