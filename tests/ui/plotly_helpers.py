"""Overlay output as Plotly traces, for tests that check what the Plotly chart draws.

Overlays return neutral drawing objects (`ui/drawing.py`); the chart turns them into
traces with `ui/plotly_render.to_plotly`. These helpers do the same, so the tests check
the final traces.
"""

from __future__ import annotations

from backtester.ui.chart_figure import DEFAULT_CONFIG
from backtester.ui.pages import chart as page
from backtester.ui.plotly_render import to_plotly


def plotly(drawings, config=DEFAULT_CONFIG):
    return to_plotly(drawings, config)


def chart_overlays(*args, **kwargs):
    """`pages.chart.chart_overlays` with the drawings as Plotly traces."""
    drawings, messages = page.chart_overlays(*args, **kwargs)
    config = kwargs.get("config", args[4] if len(args) > 4 else DEFAULT_CONFIG)
    return plotly(drawings, config), messages
