"""Tunable parameters for strategy 1.

Spec: strategy-session-zones.md › Backtest options. Defaults follow the spec; values marked
TBD in the spec are placeholders to be swept, not decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backtester.core.models import Timeframe
from backtester.detectors.atr import StrongMoveConfig
from backtester.detectors.swings import SwingConfig
from backtester.sessions import DEFAULT_SESSIONS, SessionConfig


@dataclass(frozen=True, slots=True)
class SessionZoneSweepConfig:
    # strong-move filter (confluences.md); on/off per FVG / OB comes with those detectors
    strong_move: StrongMoveConfig = field(default_factory=StrongMoveConfig)
    swings: SwingConfig = field(default_factory=SwingConfig)  # doji threshold per symbol
    sessions: SessionConfig = DEFAULT_SESSIONS

    # session zones (strategy-session-zones.md › Session zones, › Zone flips)
    zone_timeframe: Timeframe = Timeframe.M30
    zone_kill_breaks: int = 3  # the 3rd break kills a zone for the rest of its session

    # entry sequence step 3 (strategy-session-zones.md › Entry sequence): off = only a real
    # 5m BOS (against the 5m trend) counts; on = also a close above the last 5m swing high
    # while the 5m chart is already in the trade's direction
    entry_bos_with_trend: bool = False

    # stop loss
    sl_buffer_atr_mult: float = 0.0  # TBD: buffer below the confluence, as ATR fraction
    small_confluence_atr_mult: float = 0.5  # confluence height < this * ATR -> SL below BOS leg

    # take profit
    tp_cap_r: float = 3.0
    min_rr: float = 1.2
    fallback_tp_r_range: tuple[float, float] = (1.2, 2.0)  # price already beyond the zone
    obstacles_passable: int = 0  # test 0-3
    obstacle_cluster_r: float = 0.2

    # session filters
    tag_last_minutes_before_next_session: int = 90
    include_last_minutes_trades: bool = True
    skip_tokyo: bool = False
    friday_ny_carries_to_monday_tokyo: bool = True

    def __post_init__(self) -> None:
        if self.zone_kill_breaks < 1:
            raise ValueError("zone_kill_breaks must be >= 1")
