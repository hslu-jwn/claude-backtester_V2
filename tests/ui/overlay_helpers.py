"""What the chart shows for a selection of overlay types, as drawing objects
(`ui/drawing.py`), for the overlay tests. The page sends the same objects to the browser
(`ui/chart_data.py`); there the overlay panel's ticks pick what is shown, here
`overlay_drawings` does (a sub-entry only with its overlay ticked).
"""

from __future__ import annotations

from backtester.ui.chart_config import DEFAULT_CONFIG
from backtester.ui.drawing import Badge, Box, Hover, Label, Line, Marker
from backtester.ui.overlays import (
    DEFAULT_SETTINGS,
    OVERLAYS,
    OverlayContext,
    overlay_drawings,
)
from backtester.ui.pages.chart import _cached_events


def chart_overlays(
    replay,
    keys,
    cursor,
    first_x=0,
    config=DEFAULT_CONFIG,
    registry=OVERLAYS,
    settings=DEFAULT_SETTINGS,
    sources=None,
):
    """(drawings, messages) of overlay types `keys` for candles first_x..cursor."""
    ctx = OverlayContext(
        replay.symbol, cursor, first_x, config, replay.timeframe, replay.overall_timeframe
    )
    return overlay_drawings(
        lambda o: _cached_events(replay, o, settings, sources), keys, ctx, registry
    )


def by_layer(drawings) -> dict[str, list]:
    """Drawings per layer name (e.g. "FVG box"), in order; badges under their layer."""
    out: dict[str, list] = {}
    for d in drawings:
        out.setdefault(d.layer, []).append(d)
    return out


def boxes(drawings) -> list[tuple]:
    """(x0, x1, bottom, top) of each box."""
    return [(d.x0, d.x1, d.bottom, d.top) for d in drawings if isinstance(d, Box)]


def lines(drawings) -> list[tuple]:
    """(x0, x1, y0, y1) of each line."""
    return [(d.x0, d.x1, d.y0, d.y1) for d in drawings if isinstance(d, Line)]


def points(drawings, kind=Marker) -> list[tuple]:
    """(x, y) of each marker (or label)."""
    return [(d.x, d.y) for d in drawings if isinstance(d, kind)]


def hovers(drawings) -> list[str]:
    """Hover texts: of hover areas and of markers that have one."""
    out = []
    for d in drawings:
        if isinstance(d, Hover):
            out.append(d.text)
        elif isinstance(d, Marker) and d.hover is not None:
            out.append(d.hover)
    return out


def texts(drawings) -> list[str]:
    return [d.text for d in drawings if isinstance(d, Label | Badge)]
