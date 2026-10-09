"""Swings overlay. Spec: ROADMAP.md › 2.2, confluences.md › Swing high / low.

Per swing: a triangle at the swing price on the candle with the extreme wick (▼ high,
▲ low), a thin line at that price over the turn candles (first turn candle to confirming
candle, so it shows even when the extreme wick is on the confirming candle), and a dot on
the confirming candle with the hover text. Swings have no state yet (BOS in 2.3 uses them).
"""

from __future__ import annotations

from collections.abc import Sequence

from backtester.detectors.swings import SwingConfig, SwingDetector, SwingKind, SwingPoint
from backtester.engine.replay import Replay
from backtester.ui.drawing import Drawing, Line, Marker
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
        f"Swing {swing.kind.value} {swing.price:.{digits}f}\n"
        f"wick: {swing.ts:%Y-%m-%d %H:%M} UTC candle\n"
        f"confirmed: close {swing.confirmed_at:%Y-%m-%d %H:%M} UTC"
    )


def draw_swings(swings: Sequence[SwingPoint], ctx: OverlayContext) -> list[Drawing]:
    cfg = ctx.config
    out: list[Drawing] = []
    for kind, color, shape in (
        (SwingKind.HIGH, cfg.swing_high_color, "triangle-down"),
        (SwingKind.LOW, cfg.swing_low_color, "triangle-up"),
    ):
        points = [s for s in swings if s.kind is kind]
        name = f"swing {kind.value}"
        out += [
            Line(s.first_index, s.confirmed_index, s.price, s.price, name, color) for s in points
        ]
        out += [Marker(s.index, s.price, name, shape, color, cfg.marker_size) for s in points]
        out += [
            Marker(
                s.confirmed_index,
                s.price,
                name,
                "circle",
                color,
                cfg.marker_size // 2 + 1,
                hover=hover_text(s, ctx.digits),
            )
            for s in points
        ]
    return out


SWINGS = register(
    OverlayType(
        "swings",
        "Swings",
        lambda replay, settings: detect_swings(replay, settings.swing_config),
        draw_swings,
        order="2.2",
    )
)
