"""Candlestick figure for the chart page (Plotly only, no Dash). Spec: ROADMAP.md › 1.1.

Candles are placed at x = 0, 1, 2, … (their position in the frame), not at their time, so
weekends, holidays and the daily break take no space, as on TradingView. The x-axis labels
are approximate open times (UTC): one label at the first candle of each time step, with the
step chosen from the visible time span (`time_ticks`). Hover shows the exact open time.

During replay (1.2) the figure gets only the candles of a `SeriesView` (`frame_from_candles`),
drawn at their absolute positions (`first_x`), so the x positions match the full chart.

Session lines (1.3): a dashed vertical line at each session start (`sessions.py`), drawn
only over the candles in the frame, so during replay no line appears past the cursor.
One switch shows or hides all session lines; hidden on timeframes above `session_max_timeframe`.

Overlays (Phase 2, `ui/overlays.py`) are passed in as ready-made traces and drawn on top
of the candles; the candlestick trace always stays `fig.data[0]`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import log10

import pandas as pd
import plotly.graph_objects as go
from plotly.basedatatypes import BaseTraceType

from backtester.core.models import Candle, Timeframe
from backtester.data.dukascopy import POINT_FACTORS
from backtester.data.resample import CANDLE_COLUMNS
from backtester.sessions import DEFAULT_SESSIONS, Session, SessionConfig, session_starts

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
    replay_speeds: tuple[int, ...] = (1, 2, 5, 10, 20)  # autoplay choices, candles per second
    replay_default_speed: int = 5
    up_color: str = "#26a69a"
    down_color: str = "#ef5350"
    background: str = "#131722"
    grid_color: str = "#2a2e39"
    text_color: str = "#d1d4dc"
    tokyo_color: str = "#f5c518"
    london_color: str = "#2962ff"
    new_york_color: str = "#f23645"
    session_line_width: int = 1
    session_line_dash: str = "dash"
    session_max_timeframe: Timeframe = Timeframe.H4  # more lines than candles above this
    swing_high_color: str = "#ff9800"
    swing_low_color: str = "#00bcd4"
    marker_size: int = 9

    def session_color(self, session: Session) -> str:
        return getattr(self, f"{session.value}_color")


DEFAULT_CONFIG = ChartConfig()


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

    x is the start's place on the candle axis: the left edge of the candle opening at it
    (x - 0.5), or a point inside the candle containing it (H4). A start inside a gap (e.g.
    after a holiday) goes to the next candle's left edge, if that candle is still in the
    session; sessions without candles get no line.
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
        if opens.iloc[i] + duration > start:
            offset = (start - opens.iloc[i]) / duration
        elif i + 1 < len(opens) and opens.iloc[i + 1] < pd.Timestamp(s.end):
            i, offset = i + 1, 0.0
        else:
            continue
        positions.append((first_x + i - 0.5 + offset, s.session))
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
    overlays: Sequence[BaseTraceType] = (),
) -> go.Figure:
    """Candlesticks for `frame` (columns ts, open, high, low, close, volume, spread).

    The first candle is drawn at x = `first_x`. `x_range` is the initially visible x range
    (default: all candles); labels and price range fit the candles inside it.
    `show_sessions` draws the session start lines; `overlays` are extra traces (markers of
    detected patterns) added after the candles.
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
            increasing={"line": {"color": config.up_color}, "fillcolor": config.up_color},
            decreasing={"line": {"color": config.down_color}, "fillcolor": config.down_color},
            name=symbol,
        )
    )
    fig.add_traces(list(overlays))
    tickvals, ticktext = time_ticks(frame["ts"], lo, hi, config.max_ticks)
    shapes, labels = (
        _session_shapes(frame["ts"], timeframe, first_x, config) if show_sessions else ([], [])
    )
    fig.update_layout(
        shapes=shapes,
        annotations=labels,
        title={"text": f"{symbol} · {timeframe.name} · bid · UTC", "x": 0.01},
        paper_bgcolor=config.background,
        plot_bgcolor=config.background,
        font={"color": config.text_color},
        margin={"l": 10, "r": 70, "t": 40, "b": 30},
        dragmode="pan",
        hovermode="closest",
        showlegend=False,
        uirevision=f"{symbol}-{timeframe.name}-{first_x}-{n}",
    )
    fig.update_xaxes(
        range=[x0, x1],
        tickmode="array",
        tickvals=[first_x + p for p in tickvals],
        ticktext=ticktext,
        rangeslider_visible=False,
        gridcolor=config.grid_color,
        showspikes=True,
        spikemode="across",
        spikethickness=1,
    )
    fig.update_yaxes(
        side="right",
        range=y_range(frame, lo, hi, config.y_padding),
        tickformat=f".{digits}f",
        gridcolor=config.grid_color,
        showspikes=True,
        spikemode="across",
        spikethickness=1,
    )
    return fig
