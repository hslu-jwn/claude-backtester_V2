"""BOS + trend overlay. Spec: ROADMAP.md › 2.3, confluences.md › Break of structure (BOS),
› Trend.

Per BOS: a red horizontal line at the broken swing's price, from the swing's extreme-wick
candle to the candle whose close broke it, a "BOS" label over the line (above it for a
bullish BOS, below for a bearish one), and a dot at the line's end on the breaking
candle with the hover text.

Two badges in the chart's top-left corner show the trend at the replay cursor (or the last
candle): the **overall trend** (the trend on `TrendConfig.overall_timeframe`, default 4H,
confluences.md › Trend) and the trend of the shown timeframe. Both use every BOS up to the
cursor, also those before the replay window. The overall trend is run on the replay's
overall series one closed candle at a time, as the replay clock reveals them, so at each
cursor it only knows the overall-timeframe candles closed by then; that series starts
`ChartConfig.overall_trend_warmup_days` before the chart range.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import plotly.graph_objects as go

from backtester.core.models import Direction, Timeframe
from backtester.detectors.base import Event
from backtester.detectors.bos import BosDetector, BreakOfStructure
from backtester.detectors.swings import SwingConfig
from backtester.detectors.trend import Trend, TrendChange, TrendDetector, TrendState
from backtester.engine.replay import Replay
from backtester.ui.overlays import (
    OverlayContext,
    OverlayType,
    OverlayUnavailable,
    register,
    run_detector,
)


@dataclass(frozen=True, slots=True)
class TrendBos(Event):
    """A BOS with the trend before it and the trend change it caused (if any)."""

    bos: BreakOfStructure
    before: Trend
    change: TrendChange | None


@dataclass(frozen=True, slots=True)
class OverallTrendChange(Event):
    """A change of the overall trend, at the base candle (`confirmed_index`) whose close is
    the first one at or after the overall-timeframe candle that caused it."""

    change: TrendChange  # on the overall timeframe (its indices are that series')
    timeframe: Timeframe


def _bos_detector(symbol: str, config: SwingConfig | None) -> BosDetector:
    try:
        return BosDetector.for_symbol(symbol, config)
    except KeyError as e:
        raise OverlayUnavailable(e.args[0]) from e


def detect_bos(
    replay: Replay, config: SwingConfig | None = None
) -> list[TrendBos | OverallTrendChange]:
    """BOS of the shown timeframe (with the trend they set) and, if the replay has an
    overall series, the overall trend's changes."""
    return [*_chart_bos(replay, config), *detect_overall_trend(replay, config)]


def detect_overall_trend(
    replay: Replay, config: SwingConfig | None = None
) -> list[OverallTrendChange]:
    timeframe = replay.overall_timeframe
    if timeframe is None:
        return []
    detector, fed, out = TrendDetector(_bos_detector(replay.symbol, config)), 0, []
    for cursor in range(len(replay)):
        view = replay.overall_view(cursor)
        if view is None:
            continue
        # every overall candle closed by now, each once, in order (warm-up ones at cursor 0)
        for i in range(fed, view.cursor + 1):
            for change in detector.update(view.at(i)):
                out.append(OverallTrendChange(cursor, replay.close_time(cursor), change, timeframe))
        fed = view.cursor + 1
    return out


def _chart_bos(replay: Replay, config: SwingConfig | None) -> list[TrendBos]:
    detector = _bos_detector(replay.symbol, config)
    state, events = TrendState(), []
    for bos in run_detector(detector, replay):
        before = state.trend
        events.append(
            TrendBos(bos.confirmed_index, bos.confirmed_at, bos, before, state.on_bos(bos))
        )
    return events


def trend_effect(event: TrendBos) -> str:
    # every BOS sets or flips the trend (a break with the trend is no BOS)
    if event.before is Trend.NONE:
        return f"first BOS: {event.change.trend.value}trend"
    return f"trend: {event.before.value} → {event.change.trend.value} (flip)"


def hover_text(event: TrendBos, digits: int) -> str:
    bos, swing = event.bos, event.bos.swing
    return (
        f"{bos.direction.value.capitalize()} BOS {bos.price:.{digits}f}<br>"
        f"broke swing {swing.kind.value} (wick: {swing.ts:%Y-%m-%d %H:%M} UTC candle)<br>"
        f"close {bos.close:.{digits}f}, candle closed {bos.confirmed_at:%Y-%m-%d %H:%M} UTC<br>"
        f"{trend_effect(event)}"
    )


def draw_bos(
    events: Sequence[TrendBos | OverallTrendChange], ctx: OverlayContext
) -> list[go.Scatter]:
    events = [e for e in events if isinstance(e, TrendBos)]
    if not events:
        return []
    color = ctx.config.bos_color
    breaks = [e.bos for e in events]
    line_x, line_y = [], []
    for b in breaks:
        line_x += [b.swing.index, b.confirmed_index, None]
        line_y += [b.price, b.price, None]
    return [
        go.Scatter(
            x=line_x,
            y=line_y,
            mode="lines",
            line={"color": color, "width": 1},
            hoverinfo="skip",
            name="BOS",
        ),
        go.Scatter(
            x=[(b.swing.index + b.confirmed_index) / 2 for b in breaks],
            y=[b.price for b in breaks],
            mode="text",
            text=["BOS"] * len(breaks),
            textposition=[
                "top center" if b.direction is Direction.BULLISH else "bottom center"
                for b in breaks
            ],
            textfont={"color": color, "size": 10},
            hoverinfo="skip",
            name="BOS label",
        ),
        go.Scatter(
            x=[b.confirmed_index for b in breaks],
            y=[b.price for b in breaks],
            mode="markers",
            marker={"symbol": "circle", "color": color, "size": ctx.config.marker_size // 2 + 1},
            text=[hover_text(e, ctx.digits) for e in events],
            hovertemplate="%{text}<extra></extra>",
            name="BOS",
        ),
    ]


def trend_badges(
    events: Sequence[TrendBos | OverallTrendChange], ctx: OverlayContext
) -> list[go.layout.Annotation]:
    """Overall trend (if the replay has an overall series) and the shown timeframe's trend
    after the last change at or before the cursor (`events` are all of them)."""
    cfg = ctx.config
    overall = [e for e in events if isinstance(e, OverallTrendChange)]
    chart = [e.change for e in events if isinstance(e, TrendBos) and e.change is not None]
    badges = []
    if ctx.overall_timeframe is not None:
        last = overall[-1].change if overall else None
        title = f"Overall trend ({ctx.overall_timeframe.name})"
        badges.append(_badge_text(title, last, ctx.overall_timeframe))
    badges.append(_badge_text(f"{ctx.timeframe.name} trend", chart[-1] if chart else None))
    colors = {
        Trend.UP: cfg.trend_up_color,
        Trend.DOWN: cfg.trend_down_color,
        Trend.NONE: cfg.trend_none_color,
    }
    return [
        go.layout.Annotation(
            text=text,
            xref="paper",
            yref="paper",
            x=0.005,
            y=0.995 - i * cfg.trend_badge_spacing,
            xanchor="left",
            yanchor="top",
            showarrow=False,
            bgcolor=colors[trend],
            font={"color": "#ffffff", "size": 12 if i == 0 else 11},
            borderpad=4,
            name="trend",
        )
        for i, (text, trend) in enumerate(badges)
    ]


def _badge_text(
    title: str, last: TrendChange | None, timeframe: Timeframe | None = None
) -> tuple[str, Trend]:
    if last is None:
        return f"{title}: none (no BOS yet)", Trend.NONE
    candle = f"{timeframe.name} candle" if timeframe else "candle"
    text = (
        f"{title}: {last.trend.value.upper()} · since {last.bos.direction.value} BOS, "
        f"{candle} closed {last.confirmed_at:%Y-%m-%d %H:%M} UTC"
    )
    return text, last.trend


BOS = register(OverlayType("bos", "BOS + trend", detect_bos, draw_bos, trend_badges))
