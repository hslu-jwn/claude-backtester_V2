"""Stop loss and take profit for strategy 1.

Spec: strategy-session-zones.md › Stop loss, › Take profit (reworked 2026-10-07).
Described for a long, short mirrored. All R values are on the chart (bid) prices:
1R = entry - SL, costs not included.

Stop loss: below the entry confluence's low, minus a buffer (`sl_buffer_atr_mult` x 5m
ATR). If the confluence is small (height < `small_confluence_atr_mult` x 5m ATR), below the
BOS leg's low instead. SL size, in 5m ATR at the entry: tighter than `min_sl_atr_mult` ->
widened to it; wider than `max_sl_atr_mult` -> no trade (both off by default). The
break-even moves are the engine's (EngineConfig, Order.break_even_after_tp1).

Take profit:
1. Reversal levels above the entry, all existing at the entry: the bottom of a live
   resistance session zone, an untouched 1h swing high (no later 1h wick reached it), the
   bottom of an unmitigated (never tapped) bearish 1h OB. No 1h FVGs. Levels less than
   `obstacle_cluster_r` apart count as one (chained); a cluster's level is its nearest
   price. A TP sits `tp_buffer_atr_mult` x 5m ATR below its level.
2. Limit: the bottom of the nearest unmitigated bearish 4H OB above the entry (a TP sits
   below it at the latest) and `tp_cap_r`. 4H OB closer than `min_rr` -> no trade.
3. TP1 = the first level at or beyond `min_rr` within the limit. TP2 = the furthest of the
   next 1 + `obstacles_passable` levels within the limit; none -> everything at TP1.
4. No level within [min_rr, limit] -> one TP at `min_rr`.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from backtester.core.models import Direction
from backtester.core.series import SeriesView
from backtester.detectors.equilibrium import EquilibriumConfig, equilibrium_stop_loss
from backtester.detectors.order_block import OrderBlockConfig, OrderBlockDetector
from backtester.detectors.settings import DEFAULT_DETECTORS
from backtester.detectors.shared import DetectorPool
from backtester.detectors.swings import SwingKind, SwingPoint
from backtester.detectors.zone import ZoneBox, ZoneState, ZoneTransition
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.setup import EntrySignal
from backtester.strategy.session_zone_sweep.zones import Role

# the swing kind that blocks a trade in each direction (a long runs into highs)
BLOCKING_SWING = {Direction.BULLISH: SwingKind.HIGH, Direction.BEARISH: SwingKind.LOW}

# where a level / TP comes from
ZONE, SWING, OB, MIN_RR = "session zone", "1h swing", "1h OB", "min R"
EPS = 1e-9  # R comparisons: a level at exactly min_rr / the cap is in reach


def _sign(direction: Direction) -> int:
    return 1 if direction is Direction.BULLISH else -1


@dataclass(frozen=True, slots=True)
class Level:
    price: float
    source: str  # ZONE, SWING or OB


class UnmitigatedOrderBlocks:
    """Order blocks never tapped so far. `update(view)` once per closed candle, in order."""

    def __init__(
        self,
        doji_max_body: float,
        order_block: OrderBlockConfig = DEFAULT_DETECTORS.order_block,
        *,
        detector: OrderBlockDetector | None = None,
    ):
        self._ob = (
            detector if detector is not None else OrderBlockDetector(doji_max_body, order_block)
        )
        self.zones: list[ZoneBox] = []

    def update(self, view: SeriesView) -> None:
        for e in self._ob.update(view):
            if isinstance(e, ZoneTransition):
                if e.state is not ZoneState.ACTIVE and e.zone in self.zones:
                    self.zones.remove(e.zone)
            else:
                self.zones.append(e.zone)

    def near_edges(self, direction: Direction, entry: float) -> list[float]:
        """Near edges of the OBs against `direction` beyond `entry`, nearest first (a long
        is blocked by bearish OBs, reached at their bottom)."""
        sign = _sign(direction)
        prices = [z.near for z in self.zones if z.direction is not direction]
        return sorted((p for p in prices if sign * p > sign * entry), key=lambda p: sign * p)


class ObstacleTracker:
    """1h reversal levels: untouched swings and unmitigated OBs. `update(view)` once per
    closed 1h candle, in order."""

    def __init__(
        self, doji_max_body: float, order_block: OrderBlockConfig = DEFAULT_DETECTORS.order_block
    ):
        pool = DetectorPool(doji_max_body)
        self._swings = pool.swings
        self._obs = UnmitigatedOrderBlocks(
            doji_max_body, order_block, detector=pool.order_block(order_block)
        )
        self._untouched: list[SwingPoint] = []

    def update(self, view: SeriesView) -> None:
        candle = view.current
        self._untouched = [
            s
            for s in self._untouched
            if (candle.high < s.price if s.kind is SwingKind.HIGH else candle.low > s.price)
        ]
        self._untouched += self._swings.update(view)
        self._obs.update(view)

    def levels(self, direction: Direction, entry: float) -> list[Level]:
        """Levels beyond `entry` in the trade's direction, nearest first."""
        sign = _sign(direction)
        found = [
            Level(s.price, SWING)
            for s in self._untouched
            if s.kind is BLOCKING_SWING[direction] and sign * s.price > sign * entry
        ]
        found += [Level(p, OB) for p in self._obs.near_edges(direction, entry)]
        return sorted(found, key=lambda lv: sign * lv.price)


@dataclass(frozen=True, slots=True)
class Targets:
    stop_loss: float
    take_profit: float  # TP1 (the whole position when take_profit_2 is None)
    take_profit_2: float | None
    tp1_from: str  # ZONE, SWING, OB or MIN_RR
    tp2_from: str | None
    limit: float | None = None  # the 4H OB's near edge (None: no 4H OB beyond the entry)
    sl_at_bos_leg: bool = False  # SL below the BOS move's low (the confluence was small)
    sl_widened: bool = False  # SL widened to min_sl_atr_mult x ATR


@dataclass(frozen=True, slots=True)
class Rejected:
    reason: str


def stop_loss(
    signal: EntrySignal,
    atr: float | None,
    config: SessionZoneSweepConfig,
    equilibrium: EquilibriumConfig = DEFAULT_DETECTORS.equilibrium,
) -> float:
    if signal.eq_deepest is not None:  # equilibrium: its own rule, no ATR buffer
        return equilibrium_stop_loss(signal.confluence, signal.eq_deepest, equilibrium)
    sign = _sign(signal.direction)
    atr_value = atr or 0.0  # no ATR yet (warm-up): no buffer, never "small"
    base = signal.bos.leg_extreme if is_small(signal, atr, config) else signal.confluence.far
    return base - sign * config.sl_buffer_atr_mult * atr_value


def is_small(signal: EntrySignal, atr: float | None, config: SessionZoneSweepConfig) -> bool:
    """The entry confluence is small (height < k x ATR): the SL goes below the BOS leg.
    Never for an equilibrium (its SL is beyond the leg anyway)."""
    zone = signal.confluence
    return (
        signal.eq_deepest is None
        and atr is not None
        and zone.top - zone.bottom < config.small_confluence_atr_mult * atr
    )


def zone_levels(
    direction: Direction, entry: float, live_zones: Iterable[tuple[Role | None, float, float]]
) -> list[Level]:
    """Near edges of the opposite-role session zones beyond the entry (long: the bottoms
    of the resistance zones above it). `live_zones`: (role, top, bottom)."""
    sign = _sign(direction)
    wanted = Role.RESISTANCE if direction is Direction.BULLISH else Role.SUPPORT
    levels = [bottom if sign > 0 else top for role, top, bottom in live_zones if role is wanted]
    return [Level(p, ZONE) for p in levels if sign * p > sign * entry]


def take_profit(
    direction: Direction,
    entry: float,
    sl: float,
    levels: Iterable[Level],
    limit: float | None,
    atr: float | None,
    config: SessionZoneSweepConfig,
) -> tuple[float, float | None, str, str | None] | Rejected:
    """(TP1, TP2, TP1 source, TP2 source), or Rejected if the 4H limit is below min_rr.
    `levels`: reversal levels beyond the entry (any order); `limit`: the 4H OB's edge."""
    sign, risk = _sign(direction), abs(entry - sl)

    def r(price: float) -> float:
        return sign * (price - entry) / risk

    buffer = sign * config.tp_buffer_atr_mult * (atr or 0.0)
    cap = config.tp_cap_r
    if limit is not None:
        limit_r = r(limit - buffer)
        if limit_r < config.min_rr - EPS:
            return Rejected(f"4H OB at {limit_r:.2f}R, below the minimum {config.min_rr}R")
        cap = min(cap, limit_r)

    clusters: list[list[Level]] = []
    for lv in sorted(levels, key=lambda lv: sign * lv.price):
        if clusters and r(lv.price) - r(clusters[-1][-1].price) < config.obstacle_cluster_r:
            clusters[-1].append(lv)
        else:
            clusters.append([lv])
    tps = [(c[0].price - buffer, c[0].source) for c in clusters]
    in_reach = [i for i, (p, _) in enumerate(tps) if config.min_rr - EPS <= r(p) <= cap + EPS]
    if not in_reach:
        return entry + sign * config.min_rr * risk, None, MIN_RR, None
    first = in_reach[0]
    tp1, tp1_from = tps[first]
    further = [
        t for t in tps[first + 1 : first + 2 + config.obstacles_passable] if r(t[0]) <= cap + EPS
    ]
    if not further:
        return tp1, None, tp1_from, None
    tp2, tp2_from = further[-1]
    return tp1, tp2, tp1_from, tp2_from


def targets(
    signal: EntrySignal,
    atr: float | None,
    live_zones: Iterable[tuple[Role | None, float, float]],
    obstacles: ObstacleTracker,
    limits: UnmitigatedOrderBlocks,
    config: SessionZoneSweepConfig,
    equilibrium: EquilibriumConfig = DEFAULT_DETECTORS.equilibrium,
) -> Targets | Rejected:
    sign, entry = _sign(signal.direction), signal.close
    sl = stop_loss(signal, atr, config, equilibrium)
    if sign * (entry - sl) <= 0:
        return Rejected("SL not beyond the entry")  # can't happen for a valid setup
    widened = False
    if atr is not None:
        if (
            config.min_sl_atr_mult is not None
            and sign * (entry - sl) < config.min_sl_atr_mult * atr
        ):
            sl, widened = entry - sign * config.min_sl_atr_mult * atr, True
        if (
            config.max_sl_atr_mult is not None
            and sign * (entry - sl) > config.max_sl_atr_mult * atr
        ):
            size = sign * (entry - sl) / atr
            return Rejected(f"SL {size:.2f} x ATR, wider than {config.max_sl_atr_mult} x ATR")
    levels = zone_levels(signal.direction, entry, live_zones)
    levels += obstacles.levels(signal.direction, entry)
    edges = limits.near_edges(signal.direction, entry)
    limit = edges[0] if edges else None
    found = take_profit(signal.direction, entry, sl, levels, limit, atr, config)
    if isinstance(found, Rejected):
        return found
    tp1, tp2, tp1_from, tp2_from = found
    return Targets(
        sl,
        tp1,
        tp2,
        tp1_from,
        tp2_from,
        limit,
        sl_at_bos_leg=is_small(signal, atr, config),
        sl_widened=widened,
    )
