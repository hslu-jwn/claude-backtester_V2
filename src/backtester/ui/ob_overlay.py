"""Order block overlay. Spec: ROADMAP.md › 2.6, confluences.md › Order block, › Validation.

Drawn by `ui/zone_overlay.py`: every OB yellow, whatever its direction (rule set by the
user), from the leg's first candle until the candle that confirms or invalidates it (to the
cursor while open). It appears at the candle it exists from: the BOS candle, or with the
strong-move filter the first strong candle of the move away. Hover over the box: direction
and range, the swing, the BOS, the strong candle and the state at the cursor.

The "OB strong-move filter" switch on the chart page
(`OverlaySettings.ob_strong_move_filter`, default on) decides whether the move away needs
a strong candle.
"""

from __future__ import annotations

from collections.abc import Sequence

from backtester.detectors.order_block import OrderBlock, OrderBlockConfig, OrderBlockDetector
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
from backtester.ui.zone_overlay import ZONE_PARTS, ZoneStyle, draw_zones, steps_text


def detect_obs(
    replay: Replay, settings: OverlaySettings = DEFAULT_SETTINGS
) -> list[OrderBlock | ZoneTransition]:
    config = OrderBlockConfig(strong_move_filter=settings.ob_strong_move_filter)
    try:
        detector = OrderBlockDetector.for_symbol(replay.symbol, config)
    except KeyError as e:
        raise OverlayUnavailable(e.args[0]) from e
    return run_detector(detector, replay)


def _strong_text(ob: OrderBlock, ctx: OverlayContext) -> str:
    if ob.strong_index is None:
        return "no strong candle in the move away yet (filter off)"
    return (
        f"strong candle: closed {ob.strong_at:%Y-%m-%d %H:%M} UTC "
        f"(needed range {ob.strong_threshold:.{ctx.digits}f}, k × ATR)"
    )


def hover_text(ob: OrderBlock, history: Sequence[ZoneTransition], ctx: OverlayContext) -> str:
    zone, digits = ob.zone, ctx.digits
    return (
        f"{zone.direction.value.capitalize()} OB {zone.bottom:.{digits}f} – {zone.top:.{digits}f} "
        f"(size {zone.top - zone.bottom:.{digits}f})<br>"
        f"leg into swing {ob.swing.kind.value} {ob.swing.price:.{digits}f} "
        f"(confirmed {ob.swing.confirmed_at:%Y-%m-%d %H:%M} UTC)<br>"
        f"{ob.bos.direction.value} BOS of {ob.bos.price:.{digits}f}: candle closed "
        f"{ob.bos.confirmed_at:%Y-%m-%d %H:%M} UTC<br>"
        f"{_strong_text(ob, ctx)}<br>"
        f"exists from: candle closed {ob.confirmed_at:%Y-%m-%d %H:%M} UTC<br>"
        f"{steps_text(history)}"
    )


def draw_obs(events: Sequence[OrderBlock | ZoneTransition], ctx: OverlayContext):
    cfg = ctx.config
    style = ZoneStyle("OB", cfg.ob_color, cfg.ob_fill_opacity, cfg.ob_invalidated_opacity)
    return draw_zones(events, ctx, style, hover_text)


OB = register(OverlayType("ob", "Order block", detect_obs, draw_obs, parts=ZONE_PARTS, order="2.6"))
