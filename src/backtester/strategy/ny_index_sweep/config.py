"""Tunable parameters for strategy 2 (NY Open index sweep).

Spec: strategy-ny-indices.md › Backtest options. Defaults follow the spec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from backtester.core.models import Timeframe
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


FILTER_TIMEFRAMES = (Timeframe.M15, Timeframe.H1, Timeframe.H4)


@dataclass(frozen=True, slots=True)
class TrendFilterConfig:
    """Trade only in the direction of the last SMA-band cross (strategy 4's `sma` signal)
    on `timeframe` (spec › Backtest options › Trend filter). Off by default."""

    enabled: bool = False
    timeframe: Timeframe = Timeframe.H1  # 15m / 1h / 4h (New York-aligned as in strategy 2)
    sma_period: int = 50
    band_atr: float = 1.0  # line = SMA +/- this x ATR (0 = the plain cross)
    atr_period: int = 20  # Wilder ATR of the filter timeframe

    def __post_init__(self) -> None:
        if self.timeframe not in FILTER_TIMEFRAMES:
            raise ValueError("trend filter timeframe must be 15m, 1h or 4h")
        if self.sma_period < 2:
            raise ValueError("trend filter sma_period must be >= 2")
        if self.band_atr < 0:
            raise ValueError("trend filter band_atr must be >= 0")
        if self.atr_period < 1:
            raise ValueError("trend filter atr_period must be >= 1")


@dataclass(frozen=True, slots=True)
class NyIndexSweepConfig:
    windows: WindowConfig = field(default_factory=WindowConfig)  # AM / PM, best time
    include_best_time_trades: bool = True  # off: trades tagged "best time" are not taken
    max_trades_per_session: int = 1  # per window and index, every re-entry counts
    trend_filter: TrendFilterConfig = field(default_factory=TrendFilterConfig)

    # sweep (confluences.md › Liquidity sweep)
    sweep_lookback: int = 3  # a wick beyond one of the last N swings of the sweep TF
    sweep_close_beyond_counts: bool = True  # off: a sweep-TF close beyond the level cancels
    # off: a wick beyond one of the last N swings is enough (today's rule). On: the most
    # extreme of the last N must be taken, or one within `sweep_equal_tolerance_atr` x ATR
    # (sweep TF) below it ("equal highs"; 0 = the most extreme only)
    sweep_equal_highs: bool = False
    sweep_equal_tolerance_atr: float = 0.0
    # breakout filter (confluences.md > Liquidity sweep): this many consecutive sweep-TF
    # candles (dojis skipped) closing beyond the level cancel the setup. 0 = off, 2 / 3.
    # `wick_first`: the older candles of that streak need only their wick beyond.
    sweep_breakout_closes: int = 0
    sweep_breakout_wick_first: bool = False
    # the setup-TF BoS must break a swing made before the sweep extreme's candle
    bos_before_top: bool = False
    bos_within_am: int = 10  # setup-TF BoS within X sweep-TF candles of the extreme
    bos_within_pm: int = 10
    tap_timeout: int = 25  # 3rd confluence tapped within X setup-TF candles of the BoS

    # confluences
    confluence_kinds: frozenset[ZoneKind] = frozenset(RANKING)  # each type on / off
    entry_tf_confluence: bool = True  # off: enter at the close of the entry-TF BoS candle

    # stop loss (› Stop Loss)
    sl_buffer: float = 0.10  # share of the 3rd confluence's height beyond its far edge
    narrow_confluence_atr_mult: float = 0.0  # > 0: narrower 3rd confluence -> SL at sweep

    # take profit (› Take Profit)
    cluster_r: float = 0.2  # rejection zones closer than this count as one
    min_tp1_r: float = 1.2  # TP1 at the first zone at or beyond this R
    ath_mode: AthMode = AthMode.FIB
    fib_levels: tuple[float, ...] = (1.382, 1.5, 1.618, 2.0)
    fixed_r_levels: tuple[float, ...] = (1.2, 1.5, 1.8)

    # swings, FVG, order block and equilibrium: `RunSettings.detectors` (shared)
    atr_period: int = 14  # for the narrow-confluence threshold

    def __post_init__(self) -> None:
        if self.max_trades_per_session < 1:
            raise ValueError("max_trades_per_session must be >= 1")
        if self.sweep_lookback < 1:
            raise ValueError("sweep_lookback must be >= 1")
        if self.sweep_equal_tolerance_atr < 0 or self.sweep_breakout_closes < 0:
            raise ValueError("sweep_equal_tolerance_atr and sweep_breakout_closes must be >= 0")
        if min(self.bos_within_am, self.bos_within_pm, self.tap_timeout) < 0:
            raise ValueError("bos_within_* and tap_timeout must be >= 0")
        if self.sl_buffer < 0 or self.narrow_confluence_atr_mult < 0:
            raise ValueError("sl_buffer and narrow_confluence_atr_mult must be >= 0")
        if not self.fib_levels or not self.fixed_r_levels:
            raise ValueError("the ATH fallback needs at least one level")
