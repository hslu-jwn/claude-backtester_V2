"""FVG overlay. Spec: ROADMAP.md › 2.5, confluences.md › Fair value gap, › Validation.

Per FVG: a filled box from candle 1 to the candle that confirmed or invalidated it, or to
the cursor while it is still active or tapped (no length limit: it extends until used).
Green = bullish, red = bearish; invalidated FVGs stay drawn, fainter. No marker on candle
3 (rule set by the user): hovering over the box shows the hover text (range, candle 2
against the strong-move threshold, the shown timeframe's trend at candle 3, which the
strategy uses only FVGs with, and the state at the cursor). It comes from invisible points
along the middle of the box, one every `ChartConfig.zone_hover_step` candles over the
first and last `zone_hover_ends` candles (where it formed and where price is now; the middle
of a very long box has none, which keeps the figure small).
A tap has no marker (user's choice; the hover text lists it). The panel sub-entries "↳ ★ confirmations" and
"↳ ✕ invalidations" under FVG add ★ / ✕ where it was confirmed / invalidated (drawing only: the
box ends there either way).

All FVGs are drawn, in both directions. The "FVG strong-move filter" switch on the chart
page (`OverlaySettings.fvg_strong_move_filter`, default off) decides whether candle 2 must
be a strong move.
The state is rebuilt from the transitions confirmed at or before the cursor, so replay
shows each FVG as it was known then.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import plotly.graph_objects as go

from backtester.core.models import Direction
from backtester.detectors.base import Event
from backtester.detectors.bos import BosDetector
from backtester.detectors.fvg import FairValueGap, FvgConfig, FvgDetector
from backtester.detectors.trend import Trend, TrendDetector
from backtester.detectors.zone import ZoneBox, ZoneState, ZoneTransition
from backtester.engine.replay import Replay
from backtester.ui.overlays import (
    DEFAULT_SETTINGS,
    OverlayContext,
    OverlaySettings,
    OverlayType,
    OverlayUnavailable,
    register,
)

TRANSITION_SYMBOL = {
    ZoneState.CONFIRMED: "star",
    ZoneState.INVALIDATED: "x",
}
TREND_DIRECTION = {Trend.UP: Direction.BULLISH, Trend.DOWN: Direction.BEARISH}


@dataclass(frozen=True, slots=True)
class ChartFvg(Event):
    """An FVG with the shown timeframe's trend after its candle 3 closed."""

    fvg: FairValueGap
    trend: Trend


def detect_fvgs(
    replay: Replay, settings: OverlaySettings = DEFAULT_SETTINGS
) -> list[ChartFvg | ZoneTransition]:
    config = FvgConfig(strong_move_filter=settings.fvg_strong_move_filter)
    try:
        fvgs = FvgDetector.for_symbol(replay.symbol, config)
        trend = TrendDetector(BosDetector.for_symbol(replay.symbol))
    except KeyError as e:
        raise OverlayUnavailable(e.args[0]) from e
    out: list[ChartFvg | ZoneTransition] = []
    for cursor in range(len(replay)):
        view = replay.view(cursor)
        trend.update(view)  # trend after this candle, incl. a BOS made by it
        for event in fvgs.update(view):
            if isinstance(event, FairValueGap):
                event = ChartFvg(event.confirmed_index, event.confirmed_at, event, trend.trend)
            out.append(event)
    return out


def fvg_history(
    events: Sequence[ChartFvg | ZoneTransition],
) -> list[tuple[ChartFvg, list[ZoneTransition]]]:
    """Each FVG with its transitions among `events`, in order."""
    transitions: dict[ZoneBox, list[ZoneTransition]] = {}
    for e in events:
        if isinstance(e, ZoneTransition):
            transitions.setdefault(e.zone, []).append(e)
    return [(e, transitions.get(e.fvg.zone, [])) for e in events if isinstance(e, ChartFvg)]


def box_end(history: Sequence[ZoneTransition], cursor: int) -> int:
    """Last candle the box is drawn over: the confirming/invalidating candle, else the
    cursor."""
    return history[-1].confirmed_index if history and history[-1].state.finished else cursor


def hover_xs(x0: int, x1: int, step: int, ends: int) -> list[int]:
    """Candles of a box from x0 to x1 that get a hover point: every `step` candles within
    `ends` candles of either end, and x1."""
    xs = {x for x in range(x0, x1 + 1, step) if x - x0 < ends or x1 - x < ends}
    return sorted({*xs, x1})


def _rgba(hex_color: str, opacity: float) -> str:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{opacity})"


def _trend_text(event: ChartFvg, timeframe_name: str) -> str:
    if event.trend is Trend.NONE:
        return f"{timeframe_name} trend: none yet (no BOS)"
    with_trend = TREND_DIRECTION[event.trend] is event.fvg.direction
    return (
        f"{timeframe_name} trend: {event.trend.value} ({'with' if with_trend else 'against'} trend)"
    )


def _strong_text(fvg: FairValueGap, digits: int) -> str:
    size = f"candle 2 range {fvg.middle_range:.{digits}f}"
    if fvg.middle_threshold is None:
        return f"{size}, no ATR yet: not a strong move"
    verdict = "strong move" if fvg.strong else "not a strong move"
    return f"{size}, strong from {fvg.middle_threshold:.{digits}f} (k × ATR): {verdict}"


def hover_text(
    event: ChartFvg, history: Sequence[ZoneTransition], digits: int, timeframe_name: str
) -> str:
    fvg, zone = event.fvg, event.fvg.zone
    state = history[-1].state if history else ZoneState.ACTIVE
    steps = "".join(
        f"<br>{t.state.value}: candle closed {t.confirmed_at:%m-%d %H:%M} UTC" for t in history
    )
    return (
        f"{zone.direction.value.capitalize()} FVG {zone.bottom:.{digits}f} – {zone.top:.{digits}f} "
        f"(size {zone.top - zone.bottom:.{digits}f})<br>"
        f"confirmed: candle 3 closed {fvg.confirmed_at:%Y-%m-%d %H:%M} UTC<br>"
        f"{_strong_text(fvg, digits)}<br>"
        f"{_trend_text(event, timeframe_name)}<br>"
        f"state: {state.value}{steps}"
    )


def draw_fvgs(events: Sequence[ChartFvg | ZoneTransition], ctx: OverlayContext) -> list[go.Scatter]:
    cfg = ctx.config
    history = fvg_history(events)
    if not history:
        return []
    shown = {ZoneState(p) for p in ctx.parts}
    colors = {Direction.BULLISH: cfg.fvg_bullish_color, Direction.BEARISH: cfg.fvg_bearish_color}
    # one filled trace per (direction, invalidated): boxes separated by None
    boxes: dict[tuple[Direction, bool], tuple[list, list]] = {}
    hover_x, hover_y, hover_text_ = [], [], []
    marks_x, marks_y, marks_symbol, marks_color, marks_text = [], [], [], [], []
    for event, steps in history:
        zone = event.fvg.zone
        invalidated = bool(steps) and steps[-1].state is ZoneState.INVALIDATED
        x0, x1 = zone.start_index, box_end(steps, ctx.cursor)
        xs, ys = boxes.setdefault((zone.direction, invalidated), ([], []))
        xs += [x0, x1, x1, x0, x0, None]
        ys += [zone.bottom, zone.bottom, zone.top, zone.top, zone.bottom, None]
        color = colors[zone.direction]
        text = hover_text(event, steps, ctx.digits, ctx.timeframe.name)
        hx = hover_xs(x0, x1, cfg.zone_hover_step, cfg.zone_hover_ends)
        hover_x += hx
        hover_y += [(zone.top + zone.bottom) / 2] * len(hx)
        hover_text_ += [text] * len(hx)
        for t in steps:
            if t.state not in shown:
                continue
            marks_x.append(t.confirmed_index)
            marks_y.append(zone.far if t.state is ZoneState.INVALIDATED else zone.near)
            marks_symbol.append(TRANSITION_SYMBOL[t.state])
            marks_color.append(color)
            marks_text.append(
                f"{zone.direction.value.capitalize()} FVG {t.state.value}<br>"
                f"candle closed {t.confirmed_at:%Y-%m-%d %H:%M} UTC, close {t.close:.{ctx.digits}f}"
            )
    traces = [
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            fill="toself",
            fillcolor=_rgba(
                colors[direction],
                cfg.fvg_invalidated_opacity if invalidated else cfg.fvg_fill_opacity,
            ),
            line={"color": _rgba(colors[direction], 0.5 if invalidated else 1.0), "width": 1},
            hoverinfo="skip",
            name=f"{direction.value} FVG" + (" (invalidated)" if invalidated else ""),
        )
        for (direction, invalidated), (xs, ys) in boxes.items()
    ]
    traces.append(
        go.Scatter(
            x=hover_x,
            y=hover_y,
            mode="markers",
            marker={"size": cfg.marker_size, "opacity": 0},  # invisible, only for hover
            text=hover_text_,
            hovertemplate="%{text}<extra></extra>",
            name="FVG",
        )
    )
    if marks_x:
        traces.append(
            go.Scatter(
                x=marks_x,
                y=marks_y,
                mode="markers",
                marker={
                    "symbol": marks_symbol,
                    "color": marks_color,
                    "size": cfg.marker_size - 2,
                    "line": {"color": marks_color, "width": 1},
                },
                text=marks_text,
                hovertemplate="%{text}<extra></extra>",
                name="FVG state",
            )
        )
    return traces


FVG = register(
    OverlayType(
        "fvg",
        "FVG",
        detect_fvgs,
        draw_fvgs,
        parts=(
            (ZoneState.CONFIRMED.value, "★ confirmations"),
            (ZoneState.INVALIDATED.value, "✕ invalidations"),
        ),
        order=2.5,
    )
)
