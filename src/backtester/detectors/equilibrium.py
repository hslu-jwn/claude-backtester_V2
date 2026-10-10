"""Equilibrium (EQ) of a BOS move.

Spec: confluences.md › Equilibrium (reworked 2026-10-10), used by both strategies.
Described bullish, bearish mirrored:
- Leg: from the swing low (after a liquidity sweep: the sweep extreme, its wick) to the
  high wick of the BOS candle, fixed at the BOS candle. Without a sweep: from the lowest
  low between the broken swing's wick candle and the BOS candle (`move_start`).
- EQ = the 50% level. As a zone (zone.py) it is the leg's lower half: top = 50%, bottom =
  the leg's low. So a wick below 50% taps it, a green close back above 50% confirms it and
  only a close below the leg's low invalidates it. It exists from the close of the BOS
  candle; validation starts with the next candle.
- Stop loss (`equilibrium_stop_loss`): beyond the leg's low, buffer = 10% of the distance
  from the leg's low to the deepest wick into the EQ before the entry; toggle: beyond that
  deepest wick instead, same buffer. A wick below the leg's low (no close, so the EQ is
  still valid): always beyond that wick (user, 2026-10-10).

`EquilibriumDetector` makes one EQ per BOS of its own swings (detectors/bos.py, via the
sweep detector, so only real BOS) for the chart and strategies that use those BOS.
Strategy 1 builds its EQs from its own 5m breaks with `equilibrium_box`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backtester.core.models import Direction
from backtester.core.series import SeriesView
from backtester.detectors.base import Detector, Event
from backtester.detectors.bos import BreakOfStructure
from backtester.detectors.sweep import SweepConfig, SweepDetector
from backtester.detectors.swings import SwingConfig
from backtester.detectors.zone import ZoneBook, ZoneBox, ZoneKind, ZoneTransition


def _sign(direction: Direction) -> int:
    return 1 if direction is Direction.BULLISH else -1


@dataclass(frozen=True, slots=True)
class EquilibriumConfig:
    sl_buffer: float = 0.10  # share of the leg's low -> deepest wick distance
    sl_at_deepest_wick: bool = False  # EQ-only toggle: SL beyond the deepest wick

    def __post_init__(self) -> None:
        if self.sl_buffer < 0:
            raise ValueError("sl_buffer must be >= 0")


@dataclass(frozen=True, slots=True)
class Equilibrium(Event):
    """Confirmed by the BOS candle (`confirmed_index` = `zone.created_index`)."""

    zone: ZoneBox  # the leg's discount half (bullish: 50% down to the leg's low)
    bos: BreakOfStructure
    leg_start: float  # the leg's low (bullish), the sweep extreme when `swept`
    leg_end: float  # the BOS candle's high wick (bullish)
    swept: bool  # the BOS came with a liquidity sweep

    @property
    def level(self) -> float:
        """The 50% level."""
        return self.zone.near


def move_start(view: SeriesView, direction: Direction, start: int) -> tuple[int, float]:
    """(index, price) of the opposite extreme from candle `start` (the broken swing's wick
    candle) to the current candle: the low a bullish BOS move started from."""
    sign = _sign(direction)
    best_i, best = start, None
    for i, c in enumerate(view.window(start, view.cursor + 1), start):
        wick = c.low if sign > 0 else c.high
        if best is None or sign * wick < sign * best:
            best_i, best = i, wick
    return best_i, best


def equilibrium_box(
    direction: Direction,
    start_index: int,
    start_price: float,
    bos_index: int,
    end_price: float,
    created_at: datetime,
) -> ZoneBox:
    """The EQ zone of a leg from `start_price` (candle `start_index`) to the BOS candle's
    wick `end_price`: bullish 50% down to the low, bearish mirrored."""
    mid = (start_price + end_price) / 2
    top, bottom = (mid, start_price) if direction is Direction.BULLISH else (start_price, mid)
    return ZoneBox(ZoneKind.EQUILIBRIUM, direction, top, bottom, start_index, bos_index, created_at)


def deepest_wick(view: SeriesView, zone: ZoneBox) -> float | None:
    """The deepest wick (bullish: lowest low) of the candles after the EQ's BOS candle up to
    and including the current one; None if there are none yet."""
    candles = view.window(zone.created_index + 1, view.cursor + 1)
    if not candles:
        return None
    if zone.direction is Direction.BULLISH:
        return min(c.low for c in candles)
    return max(c.high for c in candles)


def equilibrium_stop_loss(zone: ZoneBox, deepest: float, config: EquilibriumConfig) -> float:
    """Spec example (long): leg low 100, EQ 150, deepest wick 140 -> 96 (toggle: 136);
    wick 95 below the low -> 94.5."""
    sign, low = _sign(zone.direction), zone.far
    distance = abs(deepest - low)
    below_low = sign * (deepest - low) < 0
    base = deepest if config.sl_at_deepest_wick or below_low else low
    return base - sign * config.sl_buffer * distance


class EquilibriumDetector(Detector[Equilibrium | ZoneTransition]):
    """Incremental: `update(view)` once per closed candle, in order. Emits an `Equilibrium`
    at each BOS candle and the `ZoneTransition`s of the EQs (validated from the candle
    after their BOS)."""

    def __init__(self, doji_max_body: float, sweep: SweepConfig | None = None):
        self.sweeps = SweepDetector(doji_max_body, sweep)
        self._book = ZoneBook(doji_max_body)

    @classmethod
    def for_symbol(
        cls, symbol: str, config: SwingConfig | None = None, sweep: SweepConfig | None = None
    ) -> EquilibriumDetector:
        return cls((config or SwingConfig()).doji_threshold(symbol), sweep)

    def update(self, view: SeriesView) -> list[Equilibrium | ZoneTransition]:
        sweeps = {s.bos: s for s in self.sweeps.update(view)}  # checks the call order
        out: list[Equilibrium | ZoneTransition] = list(self._book.on_candle(view))
        candle = view.current
        for bos in self.sweeps.breaks:
            sweep = sweeps.get(bos)
            if sweep is not None:
                start_index, start = sweep.index, sweep.extreme
            else:
                start_index, start = move_start(view, bos.direction, bos.swing.index)
            end = candle.high if bos.direction is Direction.BULLISH else candle.low
            zone = equilibrium_box(
                bos.direction, start_index, start, view.cursor, end, bos.confirmed_at
            )
            self._book.add(zone)
            out.append(
                Equilibrium(view.cursor, bos.confirmed_at, zone, bos, start, end, sweep is not None)
            )
        return out
