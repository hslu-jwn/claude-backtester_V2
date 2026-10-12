"""Stop loss and take profit for strategy 2.

Spec: strategy-ny-indices.md › Stop Loss, › Take Profit (with the user's answers of
2026-10-11). Described for a long, short mirrored.

Stop loss:
- Standard: below the 3rd confluence's low (its far edge), buffer = `sl_buffer` (10%) of
  its height. With `narrow_confluence_atr_mult` > 0 and a 3rd confluence narrower than
  that many ATRs of its timeframe: below the sweep extreme instead (same buffer).
- EQ as 3rd confluence: detectors/equilibrium.py `equilibrium_stop_loss` (beyond the leg's
  low with 10% of the distance to the deepest wick into it before the entry; toggle:
  beyond that wick; a wick below the low: beyond the wick).
Take profit, three equal parts (fewer when levels run out, the last one closes the rest):
- Rejection zones (AM: 1h + 4h, PM: 15m) above the entry: untouched swing highs (price)
  and bearish FVG / OB / breaker / BPR never tapped since they formed (near edge = bottom).
  Those below `min_tp1_r` (1.2R) are ignored; the rest cluster (each level less than
  `cluster_r` above the previous joins it); a cluster's level is its highest-timeframe
  zone's (same timeframe: the nearest).
- TP1, TP2, TP3 = the first clusters. Too few: fallback levels beyond the last TP (the
  entry if none), at or beyond 1.2R: fib extension of the setup-TF BoS leg (sweep extreme
  = 0, BoS candle high = 1; 1.382 / 1.5 / 1.618 / 2.0) or fixed R (1.2 / 1.5 / 1.8).
- After TP1 the SL moves to break-even including costs (engine).
"""

from __future__ import annotations

from dataclasses import dataclass

from backtester.core.models import Direction, Timeframe
from backtester.detectors.equilibrium import EquilibriumConfig, equilibrium_stop_loss
from backtester.detectors.settings import DEFAULT_DETECTORS
from backtester.detectors.zone import ZoneKind
from backtester.strategy.ny_index_sweep.config import AthMode, NyIndexSweepConfig
from backtester.strategy.ny_index_sweep.frames import Frame
from backtester.strategy.ny_index_sweep.setup import Signal
from backtester.strategy.ny_index_sweep.windows import Window

EPS = 1e-9
PARTS = 3
REJECTION_TFS = {Window.AM: (Timeframe.H1, Timeframe.H4), Window.PM: (Timeframe.M15,)}
REJECTION_KINDS = {ZoneKind.FVG, ZoneKind.ORDER_BLOCK, ZoneKind.BREAKER, ZoneKind.BPR}
# where a level came from, for the reason text
SWING, ZONE, FIB, FIXED = "swing", "zone", "fib", "fixed_r"


@dataclass(frozen=True, slots=True)
class Level:
    price: float
    tf: Timeframe
    source: str  # SWING / ZONE (+ kind) / FIB / FIXED


@dataclass(frozen=True, slots=True)
class Targets:
    stop_loss: float
    sl_from: str  # "3rd confluence", "sweep extreme" or "equilibrium"
    take_profits: tuple[Level, ...]  # 1 to 3, nearest first


@dataclass(frozen=True, slots=True)
class Rejected:
    reason: str


def _sign(direction: Direction) -> int:
    return 1 if direction is Direction.BULLISH else -1


def stop_loss(
    signal: Signal,
    frames: dict[Timeframe, Frame],
    config: NyIndexSweepConfig,
    equilibrium: EquilibriumConfig = DEFAULT_DETECTORS.equilibrium,
) -> tuple[float, str]:
    box, sign = signal.z3.box, _sign(signal.direction)
    if box.kind is ZoneKind.EQUILIBRIUM:
        return equilibrium_stop_loss(box, signal.deepest, equilibrium), "equilibrium"
    height = box.top - box.bottom
    buffer = sign * config.sl_buffer * height
    atr = frames[signal.z3.tf].atr() if config.narrow_confluence_atr_mult > 0 else None
    if atr is not None and height < config.narrow_confluence_atr_mult * atr:
        return signal.setup.extreme - buffer, "sweep extreme"
    return box.far - buffer, "3rd confluence"


def rejection_levels(
    direction: Direction, entry: float, frames: dict[Timeframe, Frame], tfs: tuple[Timeframe, ...]
) -> list[Level]:
    """Untouched swings and never-tapped opposite zones beyond `entry`, any order."""
    sign, opposite = (
        _sign(direction),
        (Direction.BEARISH if direction is Direction.BULLISH else Direction.BULLISH),
    )
    out = []
    for tf in tfs:
        frame = frames[tf]
        out += [Level(s.price, tf, SWING) for s in frame.untouched(direction, entry)]
        out += [
            Level(z.box.near, tf, f"{ZONE} {z.box.kind.value}")
            for z in frame.untapped.values()
            if z.box.direction is opposite
            and z.box.kind in REJECTION_KINDS
            and sign * (z.box.near - entry) > 0
        ]
    return [lv for lv in out if sign * (lv.price - entry) > 0]


def cluster(levels: list[Level], r, cluster_r: float, sign: int) -> list[Level]:
    """One level per cluster (chained: less than `cluster_r` from the previous level):
    its highest-timeframe zone's, the nearest on a tie. `levels` nearest first."""
    groups: list[list[Level]] = []
    for lv in levels:
        if groups and r(lv.price) - r(groups[-1][-1].price) < cluster_r:
            groups[-1].append(lv)
        else:
            groups.append([lv])
    return [max(g, key=lambda lv: (lv.tf.value, -sign * lv.price)) for g in groups]


def take_profits(
    signal: Signal,
    sl: float,
    frames: dict[Timeframe, Frame],
    config: NyIndexSweepConfig,
) -> tuple[Level, ...]:
    d, entry, sign = signal.direction, signal.close, _sign(signal.direction)
    risk = abs(entry - sl)

    def r(price: float) -> float:
        return sign * (price - entry) / risk

    tfs = REJECTION_TFS[signal.setup.window.kind]
    found = [
        lv
        for lv in rejection_levels(d, entry, frames, tfs)
        if r(lv.price) >= config.min_tp1_r - EPS
    ]
    found.sort(key=lambda lv: sign * lv.price)
    tps = cluster(found, r, config.cluster_r, sign)[:PARTS]
    if len(tps) < PARTS:
        last = tps[-1].price if tps else entry
        for price, source in fallback_levels(signal, entry, risk, config):
            if len(tps) == PARTS:
                break
            if r(price) >= config.min_tp1_r - EPS and sign * (price - last) > EPS:
                tps.append(Level(price, signal.setup.route.setup_tf, source))
                last = price
    return tuple(tps)


def fallback_levels(
    signal: Signal, entry: float, risk: float, config: NyIndexSweepConfig
) -> list[tuple[float, str]]:
    """The ATH fallback levels, nearest first."""
    sign = _sign(signal.direction)
    if config.ath_mode is AthMode.FIB:
        low, high = signal.setup.extreme, signal.setup.bos_high
        prices = [(low + f * (high - low), FIB) for f in config.fib_levels]
    else:
        prices = [(entry + sign * rr * risk, FIXED) for rr in config.fixed_r_levels]
    return sorted(prices, key=lambda p: sign * p[0])


def targets(
    signal: Signal,
    frames: dict[Timeframe, Frame],
    config: NyIndexSweepConfig,
    equilibrium: EquilibriumConfig = DEFAULT_DETECTORS.equilibrium,
) -> Targets | Rejected:
    sign = _sign(signal.direction)
    sl, sl_from = stop_loss(signal, frames, config, equilibrium)
    if sign * (signal.close - sl) <= 0:
        return Rejected("SL not beyond the entry (closed back below the 3rd confluence)")
    tps = take_profits(signal, sl, frames, config)
    if not tps:
        return Rejected(f"no TP at or beyond {config.min_tp1_r}R")
    return Targets(sl, sl_from, tps)
