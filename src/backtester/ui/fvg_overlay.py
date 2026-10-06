"""FVG overlay. Spec: ROADMAP.md › 2.5, confluences.md › Fair value gap, › Validation.

Drawn by `ui/zone_overlay.py`: every FVG green, whatever its direction (rule set by the
user), so overlapping FVGs (imbalances) show darker. Hover over the box: direction and
range, candle 2 against the strong-move threshold, the shown timeframe's trend at candle 3
(the strategy uses only FVGs with that trend) and the state at the cursor.

All FVGs are drawn, in both directions. The "FVG strong-move filter" switch on the chart
page (`OverlaySettings.fvg_strong_move_filter`, default off) decides whether candle 2 must
be a strong move.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from backtester.core.models import Direction
from backtester.detectors.base import Event
from backtester.detectors.bos import BosDetector
from backtester.detectors.fvg import FairValueGap, FvgConfig, FvgDetector
from backtester.detectors.trend import Trend, TrendDetector
from backtester.detectors.zone import ZoneBox, ZoneTransition
from backtester.engine.replay import Replay
from backtester.ui.overlays import (
    DEFAULT_SETTINGS,
    OverlayContext,
    OverlaySettings,
    OverlayType,
    OverlayUnavailable,
    register,
)
from backtester.ui.zone_overlay import ZONE_PARTS, ZoneStyle, draw_zones, steps_text

TREND_DIRECTION = {Trend.UP: Direction.BULLISH, Trend.DOWN: Direction.BEARISH}


@dataclass(frozen=True, slots=True)
class ChartFvg(Event):
    """An FVG with the shown timeframe's trend after its candle 3 closed."""

    fvg: FairValueGap
    trend: Trend

    @property
    def zone(self) -> ZoneBox:
        return self.fvg.zone


def detect_fvgs(
    replay: Replay, settings: OverlaySettings = DEFAULT_SETTINGS
) -> list[ChartFvg | ZoneTransition]:
    config = FvgConfig(strong_move_filter=settings.fvg_strong_move_filter)
    try:
        fvgs = FvgDetector.for_symbol(replay.symbol, config)
        trend = TrendDetector(BosDetector.for_symbol(replay.symbol))
    except KeyError as e:
        raise OverlayUnavailable(e.args[0]) from e
    out: list[ChartFvg | ZoneTransition] = []
    for cursor in range(len(replay)):
        view = replay.view(cursor)
        trend.update(view)  # trend after this candle, incl. a BOS made by it
        for event in fvgs.update(view):
            if isinstance(event, FairValueGap):
                event = ChartFvg(event.confirmed_index, event.confirmed_at, event, trend.trend)
            out.append(event)
    return out


def _trend_text(event: ChartFvg, timeframe_name: str) -> str:
    if event.trend is Trend.NONE:
        return f"{timeframe_name} trend: none yet (no BOS)"
    with_trend = TREND_DIRECTION[event.trend] is event.fvg.direction
    return (
        f"{timeframe_name} trend: {event.trend.value} ({'with' if with_trend else 'against'} trend)"
    )


def _strong_text(fvg: FairValueGap, digits: int) -> str:
    size = f"candle 2 range {fvg.middle_range:.{digits}f}"
    if fvg.middle_threshold is None:
        return f"{size}, no ATR yet: not a strong move"
    verdict = "strong move" if fvg.strong else "not a strong move"
    return f"{size}, strong from {fvg.middle_threshold:.{digits}f} (k × ATR): {verdict}"


def hover_text(event: ChartFvg, history: Sequence[ZoneTransition], ctx: OverlayContext) -> str:
    fvg, zone, digits = event.fvg, event.zone, ctx.digits
    return (
        f"{zone.direction.value.capitalize()} FVG {zone.bottom:.{digits}f} – {zone.top:.{digits}f} "
        f"(size {zone.top - zone.bottom:.{digits}f})<br>"
        f"confirmed: candle 3 closed {fvg.confirmed_at:%Y-%m-%d %H:%M} UTC<br>"
        f"{_strong_text(fvg, digits)}<br>"
        f"{_trend_text(event, ctx.timeframe.name)}<br>"
        f"{steps_text(history)}"
    )


def draw_fvgs(events: Sequence[ChartFvg | ZoneTransition], ctx: OverlayContext):
    cfg = ctx.config
    style = ZoneStyle("FVG", cfg.fvg_color, cfg.fvg_fill_opacity, cfg.fvg_invalidated_opacity)
    return draw_zones(events, ctx, style, hover_text)


FVG = register(OverlayType("fvg", "FVG", detect_fvgs, draw_fvgs, parts=ZONE_PARTS, order=2.5))
