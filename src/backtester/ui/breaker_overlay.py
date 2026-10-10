"""Breaker block overlay. Spec: ROADMAP.md › 2.7 / 8.2.3, confluences.md › Breaker block.

Drawn by `ui/zone_overlay.py`: every breaker orange, whatever its direction (rule set by
the user), from the run's first candle until it is confirmed / invalidated, or to the
cursor while open. It appears at the BOS candle. Hover: range, the broken swing, the BOS
and the state.
"""

from __future__ import annotations

from collections.abc import Sequence

from backtester.detectors.breaker import BreakerBlock, BreakerDetector
from backtester.detectors.zone import ZoneTransition
from backtester.engine.replay import Replay
from backtester.ui.overlays import (
    DEFAULT_SETTINGS,
    OverlayContext,
    OverlaySettings,
    OverlayType,
    OverlayUnavailable,
    register,
    run_detector,
)
from backtester.ui.zone_overlay import ZONE_PARTS, ZoneStyle, draw_zones, steps_text, zone_group


def detect_breakers(
    replay: Replay, settings: OverlaySettings = DEFAULT_SETTINGS
) -> list[BreakerBlock | ZoneTransition]:
    try:
        detector = BreakerDetector.for_symbol(replay.symbol, settings.swing_config)
    except KeyError as e:
        raise OverlayUnavailable(e.args[0]) from e
    return run_detector(detector, replay)


def hover_text(b: BreakerBlock, history: Sequence[ZoneTransition], ctx: OverlayContext) -> str:
    zone, digits = b.zone, ctx.digits
    return (
        f"{zone.direction.value.capitalize()} breaker {zone.bottom:.{digits}f} – "
        f"{zone.top:.{digits}f} (size {zone.top - zone.bottom:.{digits}f})\n"
        f"move into the swing {b.swing.kind.value} {b.swing.price:.{digits}f} "
        f"(wick: {b.swing.ts:%Y-%m-%d %H:%M} UTC candle)\n"
        f"exists from: BOS candle closed {b.confirmed_at:%Y-%m-%d %H:%M} UTC\n"
        f"{steps_text(history)}"
    )


def draw_breakers(events: Sequence[BreakerBlock | ZoneTransition], ctx: OverlayContext):
    cfg = ctx.config
    style = ZoneStyle(
        "Breaker", cfg.breaker_color, cfg.breaker_fill_opacity, cfg.breaker_invalidated_opacity
    )
    return draw_zones(events, ctx, style, hover_text)


BREAKER = register(
    OverlayType(
        "breaker",
        "Breaker block",
        detect_breakers,
        draw_breakers,
        parts=ZONE_PARTS,
        order="2.7",
        group=zone_group,
    )
)
