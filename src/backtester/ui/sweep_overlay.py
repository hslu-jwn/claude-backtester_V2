"""Liquidity sweep overlay. Spec: ROADMAP.md › 2.11, confluences.md › Liquidity sweep.

Per sweep (detector defaults: last 3 swings, BOS within 10 candles): a thin magenta line
at the swept swing's price, from that swing's extreme-wick candle to the sweeping candle,
and a small marker on the sweeping wick with the hover text. If several swings were taken,
the line goes to the most extreme of them and the hover lists all (display choice). It
appears at the BOS candle that made it a sweep, not before.
"""

from __future__ import annotations

from collections.abc import Sequence

from backtester.core.models import Direction
from backtester.detectors.sweep import LiquiditySweep, SweepDetector
from backtester.detectors.swings import SwingConfig
from backtester.engine.replay import Replay
from backtester.ui.drawing import Drawing, Line, Marker
from backtester.ui.overlays import (
    OverlayContext,
    OverlayType,
    OverlayUnavailable,
    register,
    run_detector,
)


def detect_sweeps(replay: Replay, config: SwingConfig | None = None) -> list[LiquiditySweep]:
    try:
        detector = SweepDetector.for_symbol(replay.symbol, config)
    except KeyError as e:
        raise OverlayUnavailable(e.args[0]) from e
    return run_detector(detector, replay)


def hover_text(sweep: LiquiditySweep, digits: int) -> str:
    kind = "highs" if sweep.direction is Direction.BEARISH else "lows"
    taken = "\n".join(
        f"  {s.kind.value} {s.price:.{digits}f} (wick: {s.ts:%Y-%m-%d %H:%M} UTC candle)"
        for s in reversed(sweep.swept)
    )
    bos = sweep.bos
    return (
        f"{sweep.direction.value.capitalize()} liquidity sweep of {kind}\n"
        f"sweeping wick {sweep.extreme:.{digits}f} (candle {sweep.ts:%Y-%m-%d %H:%M} UTC)\n"
        f"took:\n{taken}\n"
        f"{bos.direction.value} BOS of {bos.price:.{digits}f}: candle closed "
        f"{bos.confirmed_at:%Y-%m-%d %H:%M} UTC, {bos.confirmed_index - sweep.index} "
        f"candles after the top (sweep exists from here)"
    )


def draw_sweeps(events: Sequence[LiquiditySweep], ctx: OverlayContext) -> list[Drawing]:
    color = ctx.config.sweep_color
    return [
        *(
            Line(s.swing.index, s.index, s.swing.price, s.swing.price, "Sweep", color)
            for s in events
        ),
        *(
            Marker(
                s.index,
                s.extreme,
                "Sweep wick",
                "triangle-down" if s.direction is Direction.BEARISH else "triangle-up",
                color,
                ctx.config.marker_size // 2 + 2,
                hover=hover_text(s, ctx.digits),
            )
            for s in events
        ),
    ]


SWEEP = register(
    OverlayType(
        "sweep",
        "Liquidity sweep",
        lambda replay, settings: detect_sweeps(replay, settings.swing_config),
        draw_sweeps,
        order="2.11",
    )
)
