"""Tunable parameters for strategy 1.

Spec: strategy-session-zones.md › Backtest options. Defaults follow the spec; values marked
TBD in the spec are placeholders to be swept, not decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backtester.core.models import Timeframe
from backtester.detectors.atr import StrongMoveConfig
from backtester.detectors.equilibrium import EquilibriumConfig
from backtester.detectors.fvg import FvgConfig
from backtester.detectors.order_block import OrderBlockConfig
from backtester.detectors.swings import SwingConfig
from backtester.detectors.zone import ZoneKind
from backtester.sessions import DEFAULT_SESSIONS, SessionConfig


@dataclass(frozen=True, slots=True)
class SessionZoneSweepConfig:
    # 5m ATR for the SL / TP sizes (its period; the strong-move filter settings are per
    # FVG / OB below)
    strong_move: StrongMoveConfig = field(default_factory=StrongMoveConfig)
    fvg: FvgConfig = field(default_factory=FvgConfig)  # strong-move filter default off
    order_block: OrderBlockConfig = field(default_factory=OrderBlockConfig)  # filter on
    swings: SwingConfig = field(default_factory=SwingConfig)  # doji threshold per symbol
    sessions: SessionConfig = DEFAULT_SESSIONS  # session starts, each in its city's time

    # session zones (strategy-session-zones.md › Session zones, › Zone flips)
    zone_timeframe: Timeframe = Timeframe.M30  # zones, sweep and reaction candles
    zone_kill: bool = True  # off: breaks only flip a zone, none kills it
    zone_kill_breaks: int = 3  # the 3rd break kills a zone for the rest of its session

    # step 3 with the 5m trend (strategy-session-zones.md › Entry sequence): off = only a
    # real 5m BOS (against the 5m trend) counts; on = also a close above the last 5m swing
    # high while the 5m chart is already in the trade's direction
    entry_bos_with_trend: bool = False

    # step 4: the confluence types that can trigger an entry (the equilibrium has its own
    # switch below)
    confluence_kinds: frozenset[ZoneKind] = frozenset(
        {ZoneKind.FVG, ZoneKind.ORDER_BLOCK, ZoneKind.BREAKER, ZoneKind.BPR}
    )
    use_equilibrium: bool = True  # the BOS move's equilibrium is an entry confluence too
    # EQ stop loss (› Stop loss, EQ): beyond the leg's low + 10% of its distance to the
    # deepest wick into the EQ; toggle: beyond that wick instead
    equilibrium: EquilibriumConfig = field(default_factory=EquilibriumConfig)

    # stop loss
    sl_buffer_atr_mult: float = 0.0  # TBD: buffer below the confluence, as ATR fraction
    small_confluence_atr_mult: float = 0.5  # confluence height < this * ATR -> SL below BOS leg
    # SL size in 5m ATR at the entry (› Stop loss, SL size); None = off
    max_sl_atr_mult: float | None = None  # wider SL -> no trade
    min_sl_atr_mult: float | None = None  # tighter SL -> widened to this (off; to be swept)

    # take profit (› Take profit, reworked 2026-10-07)
    tp_cap_r: float = 3.0  # no TP beyond this R
    min_rr: float = 1.2  # TP1 at or beyond this; also the TP when no level is in reach
    obstacles_passable: int = 0  # TP2: further levels it may pass after TP1 (test 0-3)
    obstacle_cluster_r: float = 0.2  # reversal levels closer than this count as one
    obstacle_timeframe: Timeframe = Timeframe.H1  # session zones + these highs / OBs
    limit_timeframe: Timeframe = Timeframe.H4  # OBs here are a hard TP limit
    tp_buffer_atr_mult: float = 0.0  # TBD: "just below" a level, as 5m ATR fraction
    tp1_share: float = 0.5  # share of the position closed at TP1
    break_even_after_tp1: bool = True  # SL of the rest to break-even (with costs)

    # session filters
    tag_last_minutes_before_next_session: int = 90  # entries this close to the next start
    include_last_minutes_trades: bool = True  # off: those tagged entries are not taken
    skip_tokyo: bool = False  # ignore the zones active in the Tokyo session
    friday_ny_carries_to_monday_tokyo: bool = True  # Friday NY zones live on in Monday Tokyo

    def __post_init__(self) -> None:
        if self.zone_kill_breaks < 1:
            raise ValueError("zone_kill_breaks must be >= 1")
        if not 0 < self.tp1_share <= 1:
            raise ValueError("tp1_share must be in (0, 1]")
        if self.tp_cap_r < self.min_rr:
            raise ValueError("tp_cap_r must be >= min_rr")
        if self.obstacles_passable < 0:
            raise ValueError("obstacles_passable must be >= 0")
