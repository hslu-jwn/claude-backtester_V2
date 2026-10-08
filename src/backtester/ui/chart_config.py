"""Chart settings and helpers shared by the chart page and the overlays (no Plotly, no
Dash). Spec: ROADMAP.md › 1.1, 1.3, 4.0a.

`ChartConfig` holds the chart's tunable values and colors (white, like the user's
TradingView). `session_line_positions` places the session start lines (1.3): through the
middle of the candle the session starts on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import log10

import pandas as pd

from backtester.core.models import Timeframe
from backtester.data.dukascopy import POINT_FACTORS
from backtester.detectors.trend import TrendConfig
from backtester.sessions import DEFAULT_SESSIONS, Session, SessionConfig, session_starts


@dataclass(frozen=True)
class ChartConfig:
    max_candles: int = 20_000  # above this the page asks for a shorter range / higher timeframe
    y_padding: float = 0.05  # fraction of the visible high-low range added above and below
    replay_window: int = 1500  # the replay span shows at most this many candles left of the cursor
    replay_visible: int = 120  # candles shown left of the cursor after each replay step
    replay_right_space: int = 10  # empty candle slots right of the cursor
    replay_min_visible: int = 5  # at least this many candles left of the cursor (e.g. on H4)
    replay_speeds: tuple[int, ...] = (1, 2, 5, 10, 20)  # autoplay choices, candles per second
    replay_default_speed: int = 5
    # Colors (white, like the user's TradingView).
    up_body: str = "#6f9ceb"
    down_body: str = "#000000"
    edge_color: str = "#000000"
    wick_color: str = "#000000"
    background: str = "#ffffff"
    text_color: str = "#131722"
    axis_color: str = "#131722"  # axis lines and tick marks
    show_grid: bool = False
    grid_color: str = "#f0f3fa"  # very faint, used when show_grid is on
    spike_color: str = "#9598a1"  # crosshair lines
    accent_color: str = "#2962ff"  # replay button while replay is on
    tokyo_color: str = "#f5c518"
    london_color: str = "#2962ff"
    new_york_color: str = "#f23645"
    session_line_width: int = 1
    session_line_dash: str = "dash"
    session_max_timeframe: Timeframe = Timeframe.H4  # more lines than candles above this
    swing_high_color: str = "#ff9800"
    swing_low_color: str = "#00bcd4"
    bos_color: str = "#f23645"  # BOS line, label and hover dot (both directions)
    trend_up_color: str = "#089981"  # trend badge background
    trend_down_color: str = "#f23645"
    trend_none_color: str = "#9598a1"
    sweep_color: str = "#ff00ff"  # liquidity sweep line and wick marker (both directions)
    # zones: one color per type, both directions (overlaps stack darker); the edge and
    # markers use the color, the fill a light shade of it; invalidated zones are fainter
    fvg_color: str = "#089981"  # green
    fvg_fill_opacity: float = 0.18
    fvg_invalidated_opacity: float = 0.07
    ob_color: str = "#fbc02d"  # yellow
    ob_fill_opacity: float = 0.25
    ob_invalidated_opacity: float = 0.1
    bpr_color: str = "#9c27b0"  # purple
    bpr_fill_opacity: float = 0.22
    bpr_invalidated_opacity: float = 0.08
    session_zone_fill_opacity: float = 0.2  # color = the session the zone is active in
    session_zone_line_dash: str = "dot"
    session_zone_min_timeframe: Timeframe = Timeframe.M5  # 30m zones shown down to this
    # higher timeframes loaded with the chart for overlays built on them (session zones)
    higher_timeframes: tuple[Timeframe, ...] = (Timeframe.M30,)
    # trades (strategy 1, ROADMAP 3.3b): TradingView-style position boxes
    trade_profit_color: str = "#089981"  # entry -> TP
    trade_loss_color: str = "#f23645"  # entry -> SL
    trade_box_opacity: float = 0.2
    trade_entry_color: str = "#787b86"  # entry line
    trade_break_even_color: str = "#2962ff"  # the moved SL, from the candle it moved on
    sl_ref_color: str = "#787b86"  # BOS move's low when the SL was placed there
    trade_tp1_color: str = "#089981"  # TP1 line inside the green box (two TPs, 3.3c)
    equilibrium_color: str = "#3f51b5"  # entry confluence: the BOS move's discount half
    equilibrium_fill_opacity: float = 0.15
    trend: TrendConfig = field(default_factory=TrendConfig)  # overall-trend timeframe
    overall_trend_warmup_days: int = 60  # overall-trend history loaded before the chart range
    marker_size: int = 9

    def session_color(self, session: Session) -> str:
        return getattr(self, f"{session.value}_color")


DEFAULT_CONFIG = ChartConfig()


def price_digits(symbol: str) -> int:
    """Decimals of the quoted price (gold 3, GBPUSD 5, GBPJPY 3)."""
    return round(log10(POINT_FACTORS[symbol])) if symbol in POINT_FACTORS else 5


SESSION_LABELS = {Session.TOKYO: "Tokyo", Session.LONDON: "London", Session.NEW_YORK: "NY"}


def session_line_positions(
    ts: pd.Series,
    timeframe: Timeframe,
    first_x: int = 0,
    sessions: SessionConfig = DEFAULT_SESSIONS,
) -> list[tuple[float, Session]]:
    """(x, session) for each session start within the candles `ts` (open times, UTC).

    x is the middle of the candle the session starts on (rule set by the user): the candle
    containing the start time (NY 08:00: the 08:00 candle; on H4 the 4h candle it falls
    in). A start inside a gap (e.g. after a holiday) goes to the next candle, if that
    candle is still in the session; sessions without candles get no line.
    """
    if ts.empty:
        return []
    duration = pd.Timedelta(timeframe.duration)
    opens = ts.reset_index(drop=True)
    first, end = opens.iloc[0].to_pydatetime(), (opens.iloc[-1] + duration).to_pydatetime()
    positions = []
    for s in session_starts(first, end, sessions):
        start = pd.Timestamp(s.start)
        i = int(opens.searchsorted(start, side="right")) - 1
        if i >= 0 and opens.iloc[i] + duration > start:
            pass  # the candle containing the start
        elif i + 1 < len(opens) and opens.iloc[i + 1] < pd.Timestamp(s.end):
            i += 1
        else:
            continue
        positions.append((float(first_x + i), s.session))
    return positions
