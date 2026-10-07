"""Liquidity sweep overlay. Spec: ROADMAP.md › 2.11, confluences.md › Liquidity sweep.

Per sweep: a thin magenta line at the swept swing's price, from that swing's extreme-wick
candle to the sweeping candle, and a small marker on the sweeping wick with the hover text.
If several swings were taken, the line goes to the most extreme of them and the hover lists
all (display choice). It appears at the BOS candle that made it a sweep, not before.
"""

from __future__ import annotations

from collections.abc import Sequence

import plotly.graph_objects as go

from backtester.core.models import Direction
from backtester.detectors.sweep import LiquiditySweep, SweepDetector
from backtester.engine.replay import Replay
from backtester.ui.overlays import (
    OverlayContext,
    OverlayType,
    OverlayUnavailable,
    register,
    run_detector,
)


def detect_sweeps(replay: Replay) -> list[LiquiditySweep]:
    try:
        detector = SweepDetector.for_symbol(replay.symbol)
    except KeyError as e:
        raise OverlayUnavailable(e.args[0]) from e
    return run_detector(detector, replay)


def hover_text(sweep: LiquiditySweep, digits: int) -> str:
    kind = "highs" if sweep.direction is Direction.BEARISH else "lows"
    taken = "<br>".join(
        f"  {s.kind.value} {s.price:.{digits}f} (wick: {s.ts:%Y-%m-%d %H:%M} UTC candle)"
        for s in reversed(sweep.swept)
    )
    bos = sweep.bos
    return (
        f"{sweep.direction.value.capitalize()} liquidity sweep of {kind}<br>"
        f"sweeping wick {sweep.extreme:.{digits}f} (candle {sweep.ts:%Y-%m-%d %H:%M} UTC)<br>"
        f"took:<br>{taken}<br>"
        f"{bos.direction.value} BOS of {bos.price:.{digits}f}: candle closed "
        f"{bos.confirmed_at:%Y-%m-%d %H:%M} UTC (sweep exists from here)"
    )


def draw_sweeps(events: Sequence[LiquiditySweep], ctx: OverlayContext) -> list[go.Scatter]:
    if not events:
        return []
    color = ctx.config.sweep_color
    line_x, line_y = [], []
    for s in events:
        line_x += [s.swing.index, s.index, None]
        line_y += [s.swing.price, s.swing.price, None]
    return [
        go.Scatter(
            x=line_x,
            y=line_y,
            mode="lines",
            line={"color": color, "width": 1},
            hoverinfo="skip",
            name="Sweep",
        ),
        go.Scatter(
            x=[s.index for s in events],
            y=[s.extreme for s in events],
            mode="markers",
            marker={
                "symbol": [
                    "triangle-down" if s.direction is Direction.BEARISH else "triangle-up"
                    for s in events
                ],
                "color": color,
                "size": ctx.config.marker_size // 2 + 2,
            },
            text=[hover_text(s, ctx.digits) for s in events],
            hovertemplate="%{text}<extra></extra>",
            name="Sweep wick",
        ),
    ]


SWEEP = register(
    OverlayType(
        "sweep",
        "Liquidity sweep",
        lambda replay, _settings: detect_sweeps(replay),
        draw_sweeps,
        order="2.11",
    )
)
