"""Shared zone drawing. Spec: ROADMAP.md › 2.5, 2.6.

Fake zone events (an event with a `zone`) so the drawing is tested without a detector.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from backtester.core.models import Direction
from backtester.detectors.base import Event
from backtester.detectors.zone import ZoneBox, ZoneKind
from backtester.ui.overlays import OverlayContext
from backtester.ui.zone_overlay import ZoneStyle, draw_zones, hover_xs, stack_lanes

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


def boxes_per_trace(traces):
    return [len([x for x in t.x if x is None]) for t in traces if t.name.startswith("Z box")]


def test_lanes_separate_only_overlapping_boxes():
    a, b = (0, 10, 1.0, 2.0), (5, 15, 1.5, 2.5)  # overlap
    c = (5, 15, 3.0, 4.0)  # same time, other prices
    d = (10, 20, 1.0, 2.0)  # starts where a ends: only touches
    assert stack_lanes([a, b, c, d]) == [0, 1, 0, 0]
    assert stack_lanes([]) == []


def test_overlapping_zones_are_in_separate_traces_so_their_fills_stack_darker():
    traces = draw(fake(0, 2, 1.0, 2.0), fake(3, 5, 1.5, 2.5), fake(3, 5, 3.0, 4.0))
    assert boxes_per_trace(traces) == [2, 1]  # the overlapping one alone in a second trace
    fills = {t.fillcolor for t in traces if t.name == "Z box"}
    assert fills == {"rgba(8,153,129,0.2)"}  # same color: overlaps just add up


def test_both_directions_share_the_color():
    traces = draw(fake(0, 2, 1.0, 2.0), fake(0, 2, 5.0, 6.0, Direction.BEARISH))
    (box,) = [t for t in traces if t.name == "Z box"]
    assert boxes_per_trace([box]) == [2]


def test_hover_points_only_near_both_ends_of_a_long_box():
    assert hover_xs(1, 7, 2, 10) == [1, 3, 5, 7]
    assert hover_xs(0, 100, 2, 10) == [0, 2, 4, 6, 8, 92, 94, 96, 98, 100]
