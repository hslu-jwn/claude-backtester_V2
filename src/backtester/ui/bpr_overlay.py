"""BPR overlay. Spec: ROADMAP.md › 2.8, confluences.md › Balanced price range, › Validation.

Drawn by `ui/zone_overlay.py`: every BPR purple, whatever its direction (rule set by the
user), from the older FVG's candle 1 until the candle that confirms or invalidates it (to
the cursor while open). It appears at the newer FVG's candle 3. Hover over the box:
direction and range, the two FVGs, the candle that invalidated the older one and the state
at the cursor.

BPRs are built from FVGs, so the "FVG strong-move filter" switch
(`OverlaySettings.fvg_strong_move_filter`, default off) applies to them as well.
"""

from __future__ import annotations

from collections.abc import Sequence

from backtester.detectors.bpr import BalancedPriceRange, BprConfig, BprDetector
from backtester.detectors.fvg import FvgConfig
from backtester.detectors.zone import ZoneBox, ZoneTransition
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


def detect_bprs(
    replay: Replay, settings: OverlaySettings = DEFAULT_SETTINGS
) -> list[BalancedPriceRange | ZoneTransition]:
    config = BprConfig(FvgConfig(strong_move_filter=settings.fvg_strong_move_filter))
    try:
        detector = BprDetector.for_symbol(replay.symbol, config, settings.swing_config)
    except KeyError as e:
        raise OverlayUnavailable(e.args[0]) from e
    return run_detector(detector, replay)


def _fvg_text(label: str, zone: ZoneBox, digits: int) -> str:
    return (
        f"{label}: {zone.direction.value} FVG {zone.bottom:.{digits}f} – {zone.top:.{digits}f} "
        f"(candle 3 closed {zone.created_at:%Y-%m-%d %H:%M} UTC)"
    )


def hover_text(
    bpr: BalancedPriceRange, history: Sequence[ZoneTransition], ctx: OverlayContext
) -> str:
    zone, digits = bpr.zone, ctx.digits
    return (
        f"{zone.direction.value.capitalize()} BPR {zone.bottom:.{digits}f} – {zone.top:.{digits}f} "
        f"(size {zone.top - zone.bottom:.{digits}f})\n"
        f"{_fvg_text('older', bpr.older, digits)}\n"
        f"{_fvg_text('newer', bpr.newer, digits)}\n"
        f"older invalidated by candle {bpr.older_invalidated_index - bpr.newer.start_index + 1} "
        f"of the newer FVG\n"
        f"exists from: candle closed {bpr.confirmed_at:%Y-%m-%d %H:%M} UTC\n"
        f"{steps_text(history)}"
    )


def draw_bprs(events: Sequence[BalancedPriceRange | ZoneTransition], ctx: OverlayContext):
    cfg = ctx.config
    style = ZoneStyle("BPR", cfg.bpr_color, cfg.bpr_fill_opacity, cfg.bpr_invalidated_opacity)
    return draw_zones(events, ctx, style, hover_text)


BPR = register(
    OverlayType(
        "bpr", "BPR", detect_bprs, draw_bprs, parts=ZONE_PARTS, order="2.8", group=zone_group
    )
)
