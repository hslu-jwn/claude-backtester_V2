"""Shared zone drawing. Spec: ROADMAP.md › 2.5, 2.6.

Fake zone events (an event with a `zone`) so the drawing is tested without a detector.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from backtester.core.models import Direction
from backtester.detectors.base import Event
from backtester.detectors.zone import ZoneBox, ZoneKind
from backtester.ui.drawing import Box, Hover
from backtester.ui.overlays import OverlayContext
from backtester.ui.zone_overlay import ZoneStyle, draw_zones, zone_group

T = datetime(2026, 1, 5, tzinfo=UTC)
STYLE = ZoneStyle("Z", "#089981", 0.2, 0.1)


@dataclass(frozen=True, slots=True)
class FakeZone(Event):
    zone: ZoneBox


def fake(start, created, bottom, top, direction=Direction.BULLISH):
    box = ZoneBox(ZoneKind.FVG, direction, top, bottom, start, created, T)
    return FakeZone(created, T, box)


def draw(*events, cursor=20):
    ctx = OverlayContext("XAUUSD", cursor, 0)
    return draw_zones(events, ctx, STYLE, lambda e, h, c: "hover")


def test_one_box_per_zone_each_filled_on_its_own_so_overlaps_stack_darker():
    drawings = draw(fake(0, 2, 1.0, 2.0), fake(3, 5, 1.5, 2.5), fake(3, 5, 3.0, 4.0))
    zone_boxes = [d for d in drawings if isinstance(d, Box)]
    assert [(b.x0, b.bottom, b.top) for b in zone_boxes] == [
        (0, 1.0, 2.0),
        (3, 1.5, 2.5),
        (3, 3.0, 4.0),
    ]
    # same color and opacity: the browser fills every box separately, overlaps add up
    assert {(b.fill, b.fill_opacity) for b in zone_boxes} == {("#089981", 0.2)}


def test_both_directions_share_the_color():
    drawings = draw(fake(0, 2, 1.0, 2.0), fake(0, 2, 5.0, 6.0, Direction.BEARISH))
    assert {b.fill for b in drawings if isinstance(b, Box)} == {"#089981"}


def test_a_zone_and_its_transitions_draw_together():
    zone = fake(0, 2, 1.0, 2.0)
    assert zone_group(zone) == zone.zone
    [hover] = [d for d in draw(zone) if isinstance(d, Hover)]
    assert (hover.x0, hover.x1, hover.y) == (0, 20, 1.5)  # along the box to the cursor
