"""Equilibrium overlay. Spec: ROADMAP.md › 8.2.2, confluences.md › Equilibrium.

Drawn by `ui/zone_overlay.py`: per BOS, the leg's discount half (bullish: 50% level down to
the leg's low; bearish mirrored), indigo whatever its direction (display choice, same as
the Trades overlay's EQ), from the leg's first candle (the sweep extreme or the start of
the BOS move) until it is confirmed / invalidated, or to the cursor while open. It
appears at the BOS candle. Hover: the leg, where it starts, the 50% level and the state.
"""

from __future__ import annotations

from collections.abc import Sequence

from backtester.detectors.equilibrium import Equilibrium, EquilibriumDetector
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


def detect_equilibria(
    replay: Replay, settings: OverlaySettings = DEFAULT_SETTINGS
) -> list[Equilibrium | ZoneTransition]:
    try:
        detector = EquilibriumDetector.for_symbol(
            replay.symbol, settings.swing_config, settings.sweep
        )
    except KeyError as e:
        raise OverlayUnavailable(e.args[0]) from e
    return run_detector(detector, replay)


def hover_text(eq: Equilibrium, history: Sequence[ZoneTransition], ctx: OverlayContext) -> str:
    zone, digits = eq.zone, ctx.digits
    start = "sweep extreme" if eq.swept else "start of the BOS move"
    return (
        f"{zone.direction.value.capitalize()} equilibrium {eq.level:.{digits}f} (50%)\n"
        f"leg {eq.leg_start:.{digits}f} ({start}) → {eq.leg_end:.{digits}f} (BOS candle wick)\n"
        f"zone {zone.bottom:.{digits}f} – {zone.top:.{digits}f}\n"
        f"exists from: BOS candle closed {eq.confirmed_at:%Y-%m-%d %H:%M} UTC\n"
        f"{steps_text(history)}"
    )


def draw_equilibria(events: Sequence[Equilibrium | ZoneTransition], ctx: OverlayContext):
    cfg = ctx.config
    style = ZoneStyle(
        "EQ", cfg.equilibrium_color, cfg.equilibrium_fill_opacity, cfg.bpr_invalidated_opacity
    )
    return draw_zones(events, ctx, style, hover_text)


EQUILIBRIUM = register(
    OverlayType(
        "eq",
        "Equilibrium",
        detect_equilibria,
        draw_equilibria,
        parts=ZONE_PARTS,
        order="8.2.2",
        group=zone_group,
    )
)
