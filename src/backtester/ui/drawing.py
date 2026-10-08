"""Neutral drawing objects: what overlays draw, independent of the chart library.
Spec: ROADMAP.md › 4.0a (step 1).

Overlays return a list of these; `ui/chart_data.py` turns them into JSON for the browser,
where `ui/assets/chart.js` draws them on the Lightweight Charts chart.

Coordinates: x is the chart candle position (the candle's absolute index in the shown
series, as everywhere on the chart; fractional values sit between candles, e.g. a label
in the middle of a line). The renderer maps a position to the candle's open time when its
library needs times. y is a price. Colors are "#rrggbb", opacities 0..1. Hover and label
texts use "\\n" for line breaks.

`layer` names a group of objects of one kind and style (e.g. "FVG box"); a renderer may
draw a run of consecutive objects with the same layer and style as one series, in the
order given. Later layers draw on top of earlier ones. `part` is the overlay's panel
sub-entry the object belongs to (e.g. "confirmed" for a zone's ★), None for the overlay
itself: the chart shows it only while that sub-entry is ticked.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Dash = Literal["solid", "dash", "dot"]
Shape = Literal["circle", "triangle-up", "triangle-down", "star", "x"]
# where a label sits relative to its point, e.g. "top center" = above it
Anchor = Literal[
    "top left",
    "top center",
    "top right",
    "middle left",
    "middle center",
    "middle right",
    "bottom left",
    "bottom center",
    "bottom right",
]


@dataclass(frozen=True, slots=True)
class Box:
    """A rectangle from candle x0 to x1, bottom to top. `fill` None: outline only; `edge`
    None: no outline. Overlapping filled boxes stack (the overlap is darker)."""

    x0: float
    x1: float
    bottom: float
    top: float
    layer: str
    fill: str | None = None
    fill_opacity: float = 0.0
    edge: str | None = None
    edge_opacity: float | None = None  # None: the plain color
    edge_dash: Dash = "solid"
    edge_width: float = 1
    part: str | None = None


@dataclass(frozen=True, slots=True)
class Line:
    """A straight line from (x0, y0) to (x1, y1)."""

    x0: float
    x1: float
    y0: float
    y1: float
    layer: str
    color: str
    width: float = 1
    dash: Dash = "solid"
    part: str | None = None


@dataclass(frozen=True, slots=True)
class Marker:
    """A symbol at one point; `hover` is its hover text (None: no hover). `outline` > 0
    draws an outline of that width in the marker's color."""

    x: float
    y: float
    layer: str
    shape: Shape
    color: str
    size: float
    hover: str | None = None
    outline: float = 0
    part: str | None = None


@dataclass(frozen=True, slots=True)
class Label:
    """Text at a point, placed at `anchor` relative to it."""

    x: float
    y: float
    text: str
    layer: str
    color: str
    size: float = 10
    anchor: Anchor = "middle center"
    part: str | None = None


@dataclass(frozen=True, slots=True)
class Hover:
    """Invisible hover area along price y from candle x0 to x1 (e.g. through the middle
    of a zone box): pointing at it shows `text`."""

    x0: float
    x1: float
    y: float
    text: str
    layer: str
    part: str | None = None


@dataclass(frozen=True, slots=True)
class Badge:
    """A status badge in the chart's top-left corner, stacked by `row` (0 = top)."""

    text: str
    background: str
    row: int
    layer: str
    size: float = 11
    color: str = "#ffffff"


Drawing = Box | Line | Marker | Label | Hover | Badge
