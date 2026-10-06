"""Swings overlay. Spec: ROADMAP.md › 2.2, confluences.md › Swing high / low.

Per swing: a triangle at the swing price on the candle with the extreme wick (▼ high,
▲ low), a thin line at that price to the confirming candle, and a dot on the confirming
candle with the hover text. Swings have no state yet (BOS in 2.3 uses them).
"""

from __future__ import annotations

from collections.abc import Sequence

import plotly.graph_objects as go

from backtester.detectors.swings import SwingConfig, SwingDetector, SwingKind, SwingPoint
from backtester.engine.replay import Replay
from backtester.ui.overlays import (
    OverlayContext,
    OverlayType,
    OverlayUnavailable,
    register,
    run_detector,
)


def detect_swings(replay: Replay, config: SwingConfig | None = None) -> list[SwingPoint]:
    try:
        detector = SwingDetector.for_symbol(replay.symbol, config)
    except KeyError as e:
        raise OverlayUnavailable(e.args[0]) from e
    return run_detector(detector, replay)


def hover_text(swing: SwingPoint, digits: int) -> str:
    return (
        f"Swing {swing.kind.value} {swing.price:.{digits}f}<br>"
        f"wick: {swing.ts:%Y-%m-%d %H:%M} UTC candle<br>"
        f"confirmed: close {swing.confirmed_at:%Y-%m-%d %H:%M} UTC"
    )


def draw_swings(swings: Sequence[SwingPoint], ctx: OverlayContext) -> list[go.Scatter]:
    cfg = ctx.config
    traces = []
    for kind, color, symbol in (
        (SwingKind.HIGH, cfg.swing_high_color, "triangle-down"),
        (SwingKind.LOW, cfg.swing_low_color, "triangle-up"),
    ):
        points = [s for s in swings if s.kind is kind]
        if not points:
            continue
        line_x, line_y = [], []
        for s in points:
            line_x += [s.index, s.confirmed_index, None]
            line_y += [s.price, s.price, None]
        name = f"swing {kind.value}"
        traces += [
            go.Scatter(
                x=line_x,
                y=line_y,
                mode="lines",
                line={"color": color, "width": 1},
                hoverinfo="skip",
                name=name,
            ),
            go.Scatter(
                x=[s.index for s in points],
                y=[s.price for s in points],
                mode="markers",
                marker={"symbol": symbol, "color": color, "size": cfg.marker_size},
                hoverinfo="skip",
                name=name,
            ),
            go.Scatter(
                x=[s.confirmed_index for s in points],
                y=[s.price for s in points],
                mode="markers",
                marker={"symbol": "circle", "color": color, "size": cfg.marker_size // 2 + 1},
                text=[hover_text(s, ctx.digits) for s in points],
                hovertemplate="%{text}<extra></extra>",
                name=name,
            ),
        ]
    return traces


SWINGS = register(OverlayType("swings", "Swings", detect_swings, draw_swings))
