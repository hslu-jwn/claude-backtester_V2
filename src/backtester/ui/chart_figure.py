"""Candlestick figure for the chart page (Plotly only, no Dash). Spec: ROADMAP.md › 1.1.

Candles are placed at x = 0, 1, 2, … (their position in the frame), not at their time, so
weekends, holidays and the daily break take no space, as on TradingView. The x-axis labels
are approximate open times (UTC): one label at the first candle of each time step, with the
step chosen from the visible time span (`time_ticks`). Hover shows the exact open time.

During replay (1.2) the figure gets only the candles of a `SeriesView` (`frame_from_candles`),
drawn at their absolute positions (`first_x`), so the x positions match the full chart.

Session lines (1.3): a dashed vertical line at each session start (`sessions.py`), through
the middle of the candle the session starts on (NY 08:00: the 08:00 candle), drawn
only over the candles in the frame, so during replay no line appears past the cursor.
One switch shows or hides all session lines; hidden on timeframes above `session_max_timeframe`.

Candles are three traces (`CANDLE_TRACES`): the candlestick draws only the filled bodies
(line width 0, because Plotly also draws a box-plot "median" line 1 px inside every body,
which made the top edge of up candles look thick); the wicks (`fig.data[1]`) go from the
body to the high and low only, so they never cross a body; the edges (`fig.data[2]`) are a
thin outline around each body. The body width is set with the layout's box gap, so the
outline fits exactly.

Overlays (Phase 2, `ui/overlays.py`) are passed in as neutral drawing objects
(`ui/drawing.py`), turned into Plotly traces by `ui/plotly_render.py` and drawn on top of
the candles; the candlestick trace always stays `fig.data[0]`, overlays start at
`fig.data[CANDLE_TRACES]`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from math import log10

import pandas as pd
import plotly.graph_objects as go

from backtester.core.models import Candle, Timeframe
from backtester.data.dukascopy import POINT_FACTORS
from backtester.data.resample import CANDLE_COLUMNS
from backtester.detectors.trend import TrendConfig
from backtester.sessions import DEFAULT_SESSIONS, Session, SessionConfig, session_starts
from backtester.ui.drawing import Drawing
from backtester.ui.plotly_render import to_plotly

# Label steps in minutes. All divide a week, so steps are anchored on a Monday 00:00 UTC.
TICK_STEPS = (5, 15, 30, 60, 120, 240, 360, 720, 1440, 10080)
_MONDAY = pd.Timestamp("1970-01-05", tz="UTC")


@dataclass(frozen=True)
class ChartConfig:
    max_candles: int = 20_000  # above this the page asks for a shorter range / higher timeframe
    max_ticks: int = 10  # at most this many x-axis labels in the visible range
    y_padding: float = 0.05  # fraction of the visible high-low range added above and below
    replay_window: int = 1500  # replay draws at most this many candles up to the cursor
    replay_visible: int = 120  # candles shown left of the cursor after each replay step
    replay_right_space: int = 10  # empty candle slots right of the cursor
    replay_min_visible: int = 5  # at least this many candles left of the cursor (e.g. on H4)
    replay_speeds: tuple[int, ...] = (1, 2, 5, 10, 20)  # autoplay choices, candles per second
    replay_default_speed: int = 5
    # Colors (white, like the user's TradingView).
    up_body: str = "#6f9ceb"
    down_body: str = "#000000"
    edge_color: str = "#000000"
    edge_width: float = 0.5  # very thin, so a small blue body still looks blue
    body_width: float = 0.6  # share of the space per candle
    wick_color: str = "#000000"
    wick_width: float = 1
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
    trend_badge_spacing: float = 0.05  # paper height between the stacked trend badges
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
    zone_hover_step: int = 2  # zone hover points along the box, one every this many candles
    zone_hover_ends: int = 10  # ... only over this many candles at each end of a long box
    trend: TrendConfig = field(default_factory=TrendConfig)  # overall-trend timeframe
    overall_trend_warmup_days: int = 60  # overall-trend history loaded before the chart range
    marker_size: int = 9

    def session_color(self, session: Session) -> str:
        return getattr(self, f"{session.value}_color")


DEFAULT_CONFIG = ChartConfig()
CANDLE_TRACES = 3  # candlestick bodies, wicks, edges; overlays come after them


def price_digits(symbol: str) -> int:
    """Decimals of the quoted price (gold 3, GBPUSD 5, GBPJPY 3)."""
    return round(log10(POINT_FACTORS[symbol])) if symbol in POINT_FACTORS else 5


def time_ticks(
    ts: pd.Series, lo: int, hi: int, max_ticks: int = ChartConfig.max_ticks
) -> tuple[list[int], list[str]]:
    """Labels for candles lo..hi (inclusive) of `ts` (open times, UTC, oldest first).

    Uses the smallest step from TICK_STEPS that gives at most `max_ticks` labels over the
    visible time span, and puts a label on the first candle of each step. Steps hold
    different numbers of candles (a step can end at a weekend or the daily break), so when
    two labels are closer than half the average spacing only the later one is kept.
    Returns (candle positions, label texts).
    """
    lo, hi = max(lo, 0), min(hi, len(ts) - 1)
    if hi < lo:
        return [], []
    visible = ts.iloc[lo : hi + 1]
    span = (visible.iloc[-1] - visible.iloc[0]) / pd.Timedelta(minutes=1)
    step = next((s for s in TICK_STEPS if span / s <= max_ticks), TICK_STEPS[-1])
    if span / step > max_ticks:  # longer than max_ticks weeks: use multiples of a week
        step *= -(-int(span / step) // max_ticks)

    bucket = ((visible - _MONDAY) / pd.Timedelta(minutes=step)).astype("int64")
    first = bucket.ne(bucket.shift()).to_numpy()  # first candle of each step
    min_gap = (hi - lo + 1) / (2 * max_ticks)
    positions: list[int] = []
    for i in first.nonzero()[0]:
        if positions and lo + i - positions[-1] < min_gap:
            positions.pop()
        positions.append(lo + int(i))
    return positions, _labels([ts.iloc[p] for p in positions], daily=step >= 1440)


def _labels(starts: list[pd.Timestamp], daily: bool) -> list[str]:
    labels = []
    for i, t in enumerate(starts):
        prev = starts[i - 1] if i else None
        if prev is None or prev.year != t.year:
            fmt = "%Y-%m-%d" if daily else "%Y-%m-%d %H:%M"
        elif daily or prev.date() != t.date():
            fmt = "%b %d" if daily else "%b %d %H:%M"
        else:
            fmt = "%H:%M"
        labels.append(t.strftime(fmt))
    return labels


def y_range(frame: pd.DataFrame, lo: int, hi: int, padding: float) -> list[float] | None:
    """Price range of candles lo..hi (inclusive) plus padding, or None if none are visible."""
    visible = frame.iloc[max(lo, 0) : max(hi + 1, 0)]
    if visible.empty:
        return None
    low, high = float(visible["low"].min()), float(visible["high"].max())
    pad = (high - low) * padding if high > low else abs(high) * 1e-4  # flat: avoid a zero range
    return [low - pad, high + pad]


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


def _session_shapes(
    ts: pd.Series,
    timeframe: Timeframe,
    first_x: int,
    config: ChartConfig,
) -> tuple[list[dict], list[dict]]:
    """Layout shapes and labels for the session lines."""
    if timeframe.value > config.session_max_timeframe.value:
        return [], []
    lines = session_line_positions(ts, timeframe, first_x)
    shapes = [
        {
            "type": "line",
            "xref": "x",
            "yref": "paper",
            "x0": x,
            "x1": x,
            "y0": 0,
            "y1": 1,
            "line": {
                "color": config.session_color(s),
                "width": config.session_line_width,
                "dash": config.session_line_dash,
            },
            "layer": "below",
        }
        for x, s in lines
    ]
    labels = [
        {
            "x": x,
            "y": 1,
            "xref": "x",
            "yref": "paper",
            "text": SESSION_LABELS[s],
            "showarrow": False,
            "xanchor": "left",
            "yanchor": "top",
            "font": {"color": config.session_color(s), "size": 10},
        }
        for x, s in lines
    ]
    return shapes, labels


def _wicks(frame: pd.DataFrame, first_x: int, config: ChartConfig) -> go.Scatter:
    """Upper (body top to high) and lower (low to body bottom) wick of every candle."""
    top = frame[["open", "close"]].max(axis=1)
    bottom = frame[["open", "close"]].min(axis=1)
    xs: list[float | None] = []
    ys: list[float | None] = []
    for i, (high, low, t, b) in enumerate(zip(frame["high"], frame["low"], top, bottom)):
        x = first_x + i
        xs += [x, x, None, x, x, None]
        ys += [t, high, None, low, b, None]
    return go.Scatter(
        x=xs,
        y=ys,
        mode="lines",
        line={"color": config.wick_color, "width": config.wick_width},
        hoverinfo="skip",
        name="wicks",
    )


def _edges(frame: pd.DataFrame, first_x: int, config: ChartConfig) -> go.Scatter:
    """Outline of every body (a flat line for a doji), `body_width` wide."""
    top = frame[["open", "close"]].max(axis=1)
    bottom = frame[["open", "close"]].min(axis=1)
    half = config.body_width / 2
    xs: list[float | None] = []
    ys: list[float | None] = []
    for i, (t, b) in enumerate(zip(top, bottom)):
        left, right = first_x + i - half, first_x + i + half
        xs += [left, right, right, left, left, None]
        ys += [t, t, b, b, t, None]
    return go.Scatter(
        x=xs,
        y=ys,
        mode="lines",
        line={"color": config.edge_color, "width": config.edge_width},
        hoverinfo="skip",
        name="edges",
    )


def _axis_style(config: ChartConfig) -> dict:
    return {
        "showgrid": config.show_grid,
        "gridcolor": config.grid_color,
        "zeroline": False,
        "showline": True,
        "linecolor": config.axis_color,
        "ticks": "outside",
        "tickcolor": config.axis_color,
        "showspikes": True,
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": config.spike_color,
    }


def frame_from_candles(candles: Sequence[Candle]) -> pd.DataFrame:
    """Candles (e.g. from a `SeriesView`) as a frame with the cache adapter's columns."""
    frame = pd.DataFrame(
        [(c.ts, c.open, c.high, c.low, c.close, c.volume, c.spread) for c in candles],
        columns=CANDLE_COLUMNS,
    )
    frame["ts"] = pd.to_datetime(frame["ts"], utc=True)
    return frame


def build_candle_figure(
    frame: pd.DataFrame,
    symbol: str,
    timeframe: Timeframe,
    config: ChartConfig = DEFAULT_CONFIG,
    first_x: int = 0,
    x_range: tuple[float, float] | None = None,
    show_sessions: bool = True,
    overlays: Sequence[Drawing] = (),
) -> go.Figure:
    """Candlesticks for `frame` (columns ts, open, high, low, close, volume, spread).

    The first candle is drawn at x = `first_x`. `x_range` is the initially visible x range
    (default: all candles); labels and price range fit the candles inside it.
    `show_sessions` draws the session start lines; `overlays` are drawing objects of
    detected patterns, drawn after the candles (badges, e.g. the trend, as layout
    annotations after the session labels).
    """
    digits = price_digits(symbol)
    n = len(frame)
    last_x = first_x + n - 1
    x0, x1 = x_range or (first_x - 0.5, last_x + 0.5)
    lo, hi = max(round(x0), first_x) - first_x, min(round(x1), last_x) - first_x
    hover_time = frame["ts"].dt.strftime("%Y-%m-%d %H:%M")
    fig = go.Figure(
        go.Candlestick(
            x=list(range(first_x, first_x + n)),
            open=frame["open"],
            high=frame["high"],
            low=frame["low"],
            close=frame["close"],
            customdata=list(zip(hover_time, frame["spread"])),
            hovertemplate=(
                "%{customdata[0]} UTC<br>"
                f"O %{{open:.{digits}f}}  H %{{high:.{digits}f}}<br>"
                f"L %{{low:.{digits}f}}  C %{{close:.{digits}f}}<br>"
                f"spread %{{customdata[1]:.{digits}f}}<extra></extra>"
            ),
            increasing={"line": {"width": 0}, "fillcolor": config.up_body},
            decreasing={"line": {"width": 0}, "fillcolor": config.down_body},
            name=symbol,
        )
    )
    fig.add_traces([_wicks(frame, first_x, config), _edges(frame, first_x, config)])
    overlays = to_plotly(overlays, config)
    fig.add_traces([o for o in overlays if not isinstance(o, go.layout.Annotation)])
    tickvals, ticktext = time_ticks(frame["ts"], lo, hi, config.max_ticks)
    shapes, labels = (
        _session_shapes(frame["ts"], timeframe, first_x, config) if show_sessions else ([], [])
    )
    fig.update_layout(
        shapes=shapes,
        annotations=labels + [o for o in overlays if isinstance(o, go.layout.Annotation)],
        title={"text": f"{symbol} · {timeframe.name} · bid · UTC", "x": 0.01},
        paper_bgcolor=config.background,
        plot_bgcolor=config.background,
        font={"color": config.text_color},
        margin={"l": 10, "r": 70, "t": 40, "b": 30},
        dragmode="pan",
        hovermode="closest",
        boxgap=1 - config.body_width,  # candlestick body width (one candle per x step)
        boxgroupgap=0,
        showlegend=False,
        uirevision=f"{symbol}-{timeframe.name}-{first_x}-{n}",
    )
    fig.update_xaxes(
        range=[x0, x1],
        tickmode="array",
        tickvals=[first_x + p for p in tickvals],
        ticktext=ticktext,
        rangeslider_visible=False,
        **_axis_style(config),
    )
    fig.update_yaxes(
        side="right",
        range=y_range(frame, lo, hi, config.y_padding),
        tickformat=f".{digits}f",
        **_axis_style(config),
    )
    return fig
