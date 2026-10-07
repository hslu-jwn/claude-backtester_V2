"""Stop loss and take profit for strategy 1.

Spec: strategy-session-zones.md › Stop loss, › Take profit. Described for a long, short
mirrored. All R values are on the chart (bid) prices: 1R = entry - SL, costs not included.

Stop loss: below the entry confluence's low, minus a buffer (`sl_buffer_atr_mult` x 5m
ATR). If the confluence is small (height < `small_confluence_atr_mult` x 5m ATR), below the
BOS leg's low instead. The break-even move is the engine's (EngineConfig).

Take profit:
1. Target = the bottom of the nearest live resistance session zone above the entry,
   capped at `tp_cap_r` (3R).
2. No such zone (price already above it): the nearest 1h level (an obstacle, see 3.)
   between 1.2R and 2R (`fallback_tp_r_range`); if there is none, 2R.
3. Obstacles: untouched 1h swing highs and unmitigated (never tapped) bearish 1h FVGs /
   OBs, all existing at the entry; an obstacle's level is the price reached first (swing
   price, zone bottom). Levels less than `obstacle_cluster_r` apart count as one (chained).
   The TP may pass at most `obstacles_passable` of them below it and otherwise sits just
   below the next one (`tp_buffer_atr_mult` x 5m ATR below its lowest level).
4. Final TP < `min_rr` (1.2R) -> no trade.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from backtester.core.models import Direction
from backtester.core.series import SeriesView
from backtester.detectors.fvg import FvgDetector
from backtester.detectors.order_block import OrderBlockDetector
from backtester.detectors.swings import SwingDetector, SwingKind, SwingPoint
from backtester.detectors.zone import ZoneBox, ZoneState, ZoneTransition
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.setup import EntrySignal
from backtester.strategy.session_zone_sweep.zones import Role

# the swing kind that blocks a trade in each direction (a long runs into highs)
BLOCKING_SWING = {Direction.BULLISH: SwingKind.HIGH, Direction.BEARISH: SwingKind.LOW}


def _sign(direction: Direction) -> int:
    return 1 if direction is Direction.BULLISH else -1


class ObstacleTracker:
    """1h obstacles. `update(view)` once per closed 1h candle, in order."""

    def __init__(self, doji_max_body: float, config: SessionZoneSweepConfig):
        self._swings = SwingDetector(doji_max_body)
        self._fvg = FvgDetector(doji_max_body, config.fvg)
        self._ob = OrderBlockDetector(doji_max_body, config.order_block)
        self._untouched: list[SwingPoint] = []
        self._unmitigated: list[ZoneBox] = []

    def update(self, view: SeriesView) -> None:
        candle = view.current
        self._untouched = [
            s
            for s in self._untouched
            if (candle.high < s.price if s.kind is SwingKind.HIGH else candle.low > s.price)
        ]
        self._untouched += self._swings.update(view)
        for e in [*self._fvg.update(view), *self._ob.update(view)]:
            if isinstance(e, ZoneTransition):
                if e.state is not ZoneState.ACTIVE and e.zone in self._unmitigated:
                    self._unmitigated.remove(e.zone)
            else:
                self._unmitigated.append(e.zone)

    def levels(self, direction: Direction, entry: float) -> list[float]:
        """Obstacle prices beyond `entry` in the trade's direction, nearest first."""
        sign = _sign(direction)
        prices = [s.price for s in self._untouched if s.kind is BLOCKING_SWING[direction]]
        # a long is blocked by bearish zones, reached at their bottom (their near edge)
        prices += [z.near for z in self._unmitigated if z.direction is not direction]
        return sorted((p for p in prices if sign * p > sign * entry), key=lambda p: sign * p)


@dataclass(frozen=True, slots=True)
class Targets:
    stop_loss: float
    take_profit: float
    target: str  # where the TP came from: "zone", "zone_cap", "fallback_level", ...
    sl_at_bos_leg: bool = False  # SL below the BOS move's low (the confluence was small)


def stop_loss(signal: EntrySignal, atr: float | None, config: SessionZoneSweepConfig) -> float:
    sign = _sign(signal.direction)
    atr_value = atr or 0.0  # no ATR yet (warm-up): no buffer, never "small"
    base = signal.bos.leg_extreme if is_small(signal, atr, config) else signal.confluence.far
    return base - sign * config.sl_buffer_atr_mult * atr_value


def is_small(signal: EntrySignal, atr: float | None, config: SessionZoneSweepConfig) -> bool:
    """The entry confluence is small (height < k x ATR): the SL goes below the BOS leg."""
    zone = signal.confluence
    return atr is not None and zone.top - zone.bottom < config.small_confluence_atr_mult * atr


def target_zone_level(
    direction: Direction, entry: float, live_zones: Iterable[tuple[Role | None, float, float]]
) -> float | None:
    """Near edge of the nearest opposite-role session zone beyond the entry (long: the
    bottom of the nearest resistance zone above it). `live_zones`: (role, top, bottom)."""
    sign = _sign(direction)
    wanted = Role.RESISTANCE if direction is Direction.BULLISH else Role.SUPPORT
    levels = [bottom if sign > 0 else top for role, top, bottom in live_zones if role is wanted]
    beyond = [p for p in levels if sign * p > sign * entry]
    return min(beyond, key=lambda p: sign * p) if beyond else None


def take_profit(
    direction: Direction,
    entry: float,
    sl: float,
    zone_level: float | None,
    obstacles: list[float],
    atr: float | None,
    config: SessionZoneSweepConfig,
) -> tuple[float, str] | None:
    """(TP, where it came from), or None if the final TP is below the minimum R:R."""
    sign, risk = _sign(direction), abs(entry - sl)

    def r(price: float) -> float:
        return sign * (price - entry) / risk

    def at_r(value: float) -> float:
        return entry + sign * value * risk

    buffer = config.tp_buffer_atr_mult * (atr or 0.0)
    if zone_level is not None:
        tp, source = zone_level, "zone"
        if r(tp) > config.tp_cap_r:
            tp, source = at_r(config.tp_cap_r), "zone_cap"
    else:
        low, high = config.fallback_tp_r_range
        in_range = [p for p in obstacles if low <= r(p) <= high]
        if in_range:
            tp, source = in_range[0] - sign * buffer, "fallback_level"
        else:
            tp, source = at_r(high), "fallback_max"

    clusters: list[list[float]] = []
    for p in obstacles:  # nearest first
        if r(p) >= r(tp):
            break
        if clusters and r(p) - r(clusters[-1][-1]) < config.obstacle_cluster_r:
            clusters[-1].append(p)
        else:
            clusters.append([p])
    if len(clusters) > config.obstacles_passable:
        tp, source = clusters[config.obstacles_passable][0] - sign * buffer, "obstacle"
    if r(tp) < config.min_rr:
        return None
    return tp, source


def targets(
    signal: EntrySignal,
    atr: float | None,
    live_zones: Iterable[tuple[Role | None, float, float]],
    obstacles: ObstacleTracker,
    config: SessionZoneSweepConfig,
) -> Targets | None:
    sl = stop_loss(signal, atr, config)
    if _sign(signal.direction) * (signal.close - sl) <= 0:
        return None  # the SL level is not below the entry (can't happen for a valid setup)
    level = target_zone_level(signal.direction, signal.close, live_zones)
    found = take_profit(
        signal.direction,
        signal.close,
        sl,
        level,
        obstacles.levels(signal.direction, signal.close),
        atr,
        config,
    )
    if found is None:
        return None
    return Targets(sl, *found, sl_at_bos_leg=is_small(signal, atr, config))
