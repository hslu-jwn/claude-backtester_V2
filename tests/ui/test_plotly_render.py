"""Neutral drawing objects -> Plotly traces. Spec: ROADMAP.md › 4.0a (step 1)."""

from __future__ import annotations

import plotly.graph_objects as go

from backtester.ui.chart_figure import DEFAULT_CONFIG
from backtester.ui.drawing import Badge, Box, Hover, Label, Line, Marker
from backtester.ui.plotly_render import to_plotly


def render(*drawings):
    return to_plotly(drawings, DEFAULT_CONFIG)


def test_a_run_of_one_layer_and_style_is_one_trace_in_order():
    a = Line(0, 2, 1.0, 1.0, "L", "#ff0000")
    b = Line(3, 5, 2.0, 2.0, "L", "#ff0000")
    other = Line(0, 1, 3.0, 3.0, "L", "#00ff00")  # other color: own trace
    traces = render(a, b, other)
    assert [t.name for t in traces] == ["L", "L"]
    assert list(traces[0].x) == [0, 2, None, 3, 5, None]
    assert list(traces[1].y) == [3.0, 3.0, None]


def test_overlapping_filled_boxes_go_to_separate_traces_outlines_do_not():
    filled = [Box(0, 4, 1.0, 2.0, "B", fill="#089981", fill_opacity=0.2),
              Box(2, 6, 1.5, 2.5, "B", fill="#089981", fill_opacity=0.2)]  # fmt: skip
    traces = render(*filled)
    assert len(traces) == 2 and traces[0].fillcolor == "rgba(8,153,129,0.2)"
    assert traces[0].line.width == 0  # no edge
    outlines = [
        Box(b.x0, b.x1, b.bottom, b.top, "O", edge="#2962ff", edge_dash="dot") for b in filled
    ]
    (outline,) = render(*outlines)
    assert outline.fill is None and outline.line.dash == "dot"


def test_markers_hover_labels_and_badges():
    m = Marker(3, 1.5, "M", "star", "#089981", 7, hover="a\nb", outline=1)
    label = Label(1.5, 2.0, "R:R 2.00", "R", "#131722", anchor="top center")
    hover = Hover(0, 4, 1.0, "zone", "H")
    badge = Badge("trend: UP", "#089981", 1, "trend")
    marker, text, points, annotation = render(m, label, hover, badge)
    assert list(marker.marker.symbol) == ["star"] and marker.marker.line.width == 1
    assert list(marker.text) == ["a<br>b"]  # line breaks as HTML
    assert list(text.textposition) == ["top center"] and text.mode == "text"
    assert list(points.x) == [0, 2, 4] and points.marker.opacity == 0  # every 2nd candle + end
    assert isinstance(annotation, go.layout.Annotation)
    assert annotation.y == 0.995 - DEFAULT_CONFIG.trend_badge_spacing
