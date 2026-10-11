"""Tunable parameters for strategy 2 (NY Open index sweep).

Spec: strategy-ny-indices.md › Backtest options. Defaults follow the spec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from backtester.detectors.equilibrium import EquilibriumConfig
from backtester.detectors.fvg import FvgConfig
from backtester.detectors.order_block import OrderBlockConfig
from backtester.detectors.swings import SwingConfig
from backtester.detectors.zone import ZoneKind
from backtester.strategy.ny_index_sweep.windows import WindowConfig

# confluence ranking when several are hit by the same candle (› General): best first
RANKING = (
    ZoneKind.ORDER_BLOCK,
    ZoneKind.BREAKER,
    ZoneKind.BPR,
    ZoneKind.FVG,
    ZoneKind.EQUILIBRIUM,
)


class AthMode(Enum):
    FIB = "fib"  # extension of the setup-TF BoS leg
    FIXED_R = "fixed_r"


@dataclass(frozen=True, slots=True)
class NyIndexSweepConfig:
    windows: WindowConfig = field(default_factory=WindowConfig)  # AM / PM, best time
    include_best_time_trades: bool = True  # off: trades tagged "best time" are not taken
    max_trades_per_session: int = 1  # per window and index, every re-entry counts

    # sweep (confluences.md › Liquidity sweep)
    sweep_lookback: int = 3  # a wick beyond the most extreme of the last N swings of the sweep TF
    sweep_close_beyond_counts: bool = True  # off: a sweep-TF close beyond the level cancels
    bos_within_am: int = 10  # setup-TF BoS within X sweep-TF candles of the extreme
    bos_within_pm: int = 10
    tap_timeout: int = 25  # 3rd confluence tapped within X setup-TF candles of the BoS

    # confluences
    confluence_kinds: frozenset[ZoneKind] = frozenset(RANKING)  # each type on / off
    entry_tf_confluence: bool = True  # off: enter at the close of the entry-TF BoS candle

    # stop loss (› Stop Loss)
    sl_buffer: float = 0.10  # share of the 3rd confluence's height beyond its far edge
    narrow_confluence_atr_mult: float = 0.0  # > 0: narrower 3rd confluence -> SL at sweep
    equilibrium: EquilibriumConfig = field(default_factory=EquilibriumConfig)

    # take profit (› Take Profit)
    cluster_r: float = 0.2  # rejection zones closer than this count as one
    min_tp1_r: float = 1.2  # TP1 at the first zone at or beyond this R
    ath_mode: AthMode = AthMode.FIB
    fib_levels: tuple[float, ...] = (1.382, 1.5, 1.618, 2.0)
    fixed_r_levels: tuple[float, ...] = (1.2, 1.5, 1.8)

    # detectors
    swings: SwingConfig = field(default_factory=SwingConfig)  # doji threshold per symbol
    fvg: FvgConfig = field(default_factory=FvgConfig)  # strong-move filter default off
    order_block: OrderBlockConfig = field(default_factory=OrderBlockConfig)  # first version
    atr_period: int = 14  # for the narrow-confluence threshold

    def __post_init__(self) -> None:
        if self.max_trades_per_session < 1:
            raise ValueError("max_trades_per_session must be >= 1")
        if self.sweep_lookback < 1:
            raise ValueError("sweep_lookback must be >= 1")
        if min(self.bos_within_am, self.bos_within_pm, self.tap_timeout) < 0:
            raise ValueError("bos_within_* and tap_timeout must be >= 0")
        if self.sl_buffer < 0 or self.narrow_confluence_atr_mult < 0:
            raise ValueError("sl_buffer and narrow_confluence_atr_mult must be >= 0")
        if not self.fib_levels or not self.fixed_r_levels:
            raise ValueError("the ATH fallback needs at least one level")
