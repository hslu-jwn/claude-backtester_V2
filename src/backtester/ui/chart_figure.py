"""Candlestick figure for the chart page (Plotly only, no Dash). Spec: ROADMAP.md › 1.1.

Candles are placed at x = 0, 1, 2, … (their position in the frame), not at their time, so
weekends, holidays and the daily break take no space, as on TradingView. The x-axis labels
are approximate open times (UTC): one label at the first candle of each time step, with the
step chosen from the visible time span (`time_ticks`). Hover shows the exact open time.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log10

import pandas as pd
import plotly.graph_objects as go

from backtester.core.models import Timeframe
from backtester.data.dukascopy import POINT_FACTORS

# Label steps in minutes. All divide a week, so steps are anchored on a Monday 00:00 UTC.
TICK_STEPS = (5, 15, 30, 60, 120, 240, 360, 720, 1440, 10080)
_MONDAY = pd.Timestamp("1970-01-05", tz="UTC")


@dataclass(frozen=True)
class ChartConfig:
    max_candles: int = 20_000  # above this the page asks for a shorter range / higher timeframe
    max_ticks: int = 10  # at most this many x-axis labels in the visible range
    y_padding: float = 0.05  # fraction of the visible high-low range added above and below
    up_color: str = "#26a69a"
    down_color: str = "#ef5350"
    background: str = "#131722"
    grid_color: str = "#2a2e39"
    text_color: str = "#d1d4dc"


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


def build_candle_figure(
    frame: pd.DataFrame, symbol: str, timeframe: Timeframe, config: ChartConfig = DEFAULT_CONFIG
) -> go.Figure:
    """Candlesticks for `frame` (columns ts, open, high, low, close, volume, spread)."""
    digits = price_digits(symbol)
    n = len(frame)
    hover_time = frame["ts"].dt.strftime("%Y-%m-%d %H:%M")
    fig = go.Figure(
        go.Candlestick(
            x=list(range(n)),
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
    tickvals, ticktext = time_ticks(frame["ts"], 0, n - 1, config.max_ticks)
    fig.update_layout(
        title={"text": f"{symbol} · {timeframe.name} · bid · UTC", "x": 0.01},
        paper_bgcolor=config.background,
        plot_bgcolor=config.background,
        font={"color": config.text_color},
        margin={"l": 10, "r": 70, "t": 40, "b": 30},
        dragmode="pan",
        hovermode="closest",
        showlegend=False,
        uirevision=f"{symbol}-{timeframe.name}-{n}",
    )
    fig.update_xaxes(
        range=[-0.5, n - 0.5],
        tickmode="array",
        tickvals=tickvals,
        ticktext=ticktext,
        rangeslider_visible=False,
        gridcolor=config.grid_color,
        showspikes=True,
        spikemode="across",
        spikethickness=1,
    )
    fig.update_yaxes(
        side="right",
        range=y_range(frame, 0, n - 1, config.y_padding),
        tickformat=f".{digits}f",
        gridcolor=config.grid_color,
        showspikes=True,
        spikemode="across",
        spikethickness=1,
    )
    return fig
