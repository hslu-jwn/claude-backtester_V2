"""Neutral drawing objects (`ui/drawing.py`) as Plotly traces: the only place overlays
become Plotly. Spec: ROADMAP.md › 4.0a (step 1).

A run of consecutive objects of one kind, layer and style becomes one trace (named after
the layer), in order, so later layers draw on top:
- filled boxes: Plotly fills all boxes of one trace as one shape, so overlapping boxes
  would NOT stack inside a trace. They are spread over as few traces ("lanes") as needed
  so that no two boxes of one trace overlap; then the fills stack and overlaps are darker.
- hover areas: invisible points along the line, one every `ChartConfig.zone_hover_step`
  candles over the first and last `zone_hover_ends` candles and at the end (the middle of
  a very long box has none, which keeps the figure small).
- badges: layout annotations in the top-left corner.
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import groupby
from typing import TYPE_CHECKING

import plotly.graph_objects as go
from plotly.basedatatypes import BaseTraceType

from backtester.ui.drawing import Badge, Box, Drawing, Hover, Label, Line, Marker

if TYPE_CHECKING:
    from backtester.ui.chart_figure import ChartConfig

Rect = tuple[float, float, float, float]  # x0, x1, bottom, top
HOVER_TEMPLATE = "%{text}<extra></extra>"


def rgba(hex_color: str, opacity: float) -> str:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{opacity})"


def html(text: str) -> str:
    return text.replace("\n", "<br>")


def hover_xs(x0: int, x1: int, step: int, ends: int) -> list[int]:
    """Candles of a box from x0 to x1 that get a hover point: every `step` candles within
    `ends` candles of either end, and x1."""
    xs = {x for x in range(x0, x1 + 1, step) if x - x0 < ends or x1 - x < ends}
    return sorted({*xs, x1})


def _overlap(a: Rect, b: Rect) -> bool:
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]


def stack_lanes(boxes: Sequence[Rect]) -> list[int]:
    """A lane per box such that no two boxes of one lane overlap (greedy, by start)."""
    lanes: list[list[Rect]] = []  # boxes per lane that may still overlap later ones
    out = [0] * len(boxes)
    for i in sorted(range(len(boxes)), key=lambda i: boxes[i][0]):
        box = boxes[i]
        for lane, active in enumerate(lanes):
            active[:] = [b for b in active if b[1] > box[0]]
            if not any(_overlap(box, b) for b in active):
                break
        else:
            lanes.append([])
            lane = len(lanes) - 1
        lanes[lane].append(box)
        out[i] = lane
    return out


def _style_key(d: Drawing):
    if isinstance(d, Box):
        return (
            Box,
            d.layer,
            d.fill,
            d.fill_opacity,
            d.edge,
            d.edge_opacity,
            d.edge_dash,
            d.edge_width,
        )
    if isinstance(d, Line):
        return (Line, d.layer, d.color, d.width, d.dash)
    if isinstance(d, Marker):
        return (Marker, d.layer, d.color, d.size, d.outline, d.hover is None)
    if isinstance(d, Label):
        return (Label, d.layer, d.color, d.size)
    if isinstance(d, Hover):
        return (Hover, d.layer)
    return (Badge, id(d))  # one annotation each


def to_plotly(
    drawings: Sequence[Drawing], config: ChartConfig
) -> list[BaseTraceType | go.layout.Annotation]:
    """Traces (and badge annotations) for `drawings`, in order."""
    out: list[BaseTraceType | go.layout.Annotation] = []
    for key, run in groupby(drawings, _style_key):
        run = list(run)
        kind = key[0]
        if kind is Box:
            out += _boxes(run)
        elif kind is Line:
            out.append(_lines(run))
        elif kind is Marker:
            out.append(_markers(run))
        elif kind is Label:
            out.append(_labels(run))
        elif kind is Hover:
            out.append(_hovers(run, config))
        else:
            out += [_badge(b, config) for b in run]
    return out


def _path(boxes: Sequence[Box]) -> tuple[list, list]:
    xs, ys = [], []
    for b in boxes:
        xs += [b.x0, b.x1, b.x1, b.x0, b.x0, None]
        ys += [b.bottom, b.bottom, b.top, b.top, b.bottom, None]
    return xs, ys


def _line_style(color: str, width: float, dash: str) -> dict:
    return {"color": color, "width": width} | ({} if dash == "solid" else {"dash": dash})


def _boxes(boxes: list[Box]) -> list[go.Scatter]:
    style = boxes[0]
    if style.edge is None:
        line = {"width": 0}
    else:
        color = style.edge if style.edge_opacity is None else rgba(style.edge, style.edge_opacity)
        line = _line_style(color, style.edge_width, style.edge_dash)
    if style.fill is None:
        xs, ys = _path(boxes)
        return [go.Scatter(x=xs, y=ys, mode="lines", line=line, hoverinfo="skip", name=style.layer)]
    lanes = stack_lanes([(b.x0, b.x1, b.bottom, b.top) for b in boxes])
    traces = []
    for lane in range(max(lanes) + 1):
        xs, ys = _path([b for b, n in zip(boxes, lanes, strict=True) if n == lane])
        traces.append(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines",
                fill="toself",
                fillcolor=rgba(style.fill, style.fill_opacity),
                line=line,
                hoverinfo="skip",
                name=style.layer,
            )
        )
    return traces


def _lines(lines: list[Line]) -> go.Scatter:
    xs, ys = [], []
    for ln in lines:
        xs += [ln.x0, ln.x1, None]
        ys += [ln.y0, ln.y1, None]
    style = lines[0]
    return go.Scatter(
        x=xs,
        y=ys,
        mode="lines",
        line=_line_style(style.color, style.width, style.dash),
        hoverinfo="skip",
        name=style.layer,
    )


def _markers(markers: list[Marker]) -> go.Scatter:
    style = markers[0]
    marker = {
        "symbol": [m.shape for m in markers],
        "color": style.color,
        "size": style.size,
    }
    if style.outline:
        marker["line"] = {"color": style.color, "width": style.outline}
    hover = (
        {"hoverinfo": "skip"}
        if style.hover is None
        else {"text": [html(m.hover) for m in markers], "hovertemplate": HOVER_TEMPLATE}
    )
    return go.Scatter(
        x=[m.x for m in markers],
        y=[m.y for m in markers],
        mode="markers",
        marker=marker,
        name=style.layer,
        **hover,
    )


def _labels(labels: list[Label]) -> go.Scatter:
    style = labels[0]
    return go.Scatter(
        x=[lb.x for lb in labels],
        y=[lb.y for lb in labels],
        mode="text",
        text=[html(lb.text) for lb in labels],
        textposition=[lb.anchor for lb in labels],
        textfont={"color": style.color, "size": style.size},
        hoverinfo="skip",
        name=style.layer,
    )


def _hovers(hovers: list[Hover], config: ChartConfig) -> go.Scatter:
    xs, ys, texts = [], [], []
    for h in hovers:
        hx = hover_xs(h.x0, h.x1, config.zone_hover_step, config.zone_hover_ends)
        xs += hx
        ys += [h.y] * len(hx)
        texts += [html(h.text)] * len(hx)
    return go.Scatter(
        x=xs,
        y=ys,
        mode="markers",
        marker={"size": config.marker_size, "opacity": 0},  # invisible, only for hover
        text=texts,
        hovertemplate=HOVER_TEMPLATE,
        name=hovers[0].layer,
    )


def _badge(b: Badge, config: ChartConfig) -> go.layout.Annotation:
    return go.layout.Annotation(
        text=html(b.text),
        xref="paper",
        yref="paper",
        x=0.005,
        y=0.995 - b.row * config.trend_badge_spacing,
        xanchor="left",
        yanchor="top",
        showarrow=False,
        bgcolor=b.background,
        font={"color": b.color, "size": b.size},
        borderpad=4,
        name=b.layer,
    )
