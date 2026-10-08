"""Overlay switch, type dropdown and the no-lookahead filter. Spec: ROADMAP.md › Phase 2.

Uses a fake detector (one event per green candle) in a private registry, so these tests
don't depend on which real detectors are registered.
"""

from __future__ import annotations

from conftest import build_series
from overlay_helpers import chart_overlays

from backtester.core.series import SeriesView
from backtester.detectors.base import Detector, Event
from backtester.engine.replay import Replay
from backtester.ui.chart_data import ChartData
from backtester.ui.drawing import Marker
from backtester.ui.overlays import (
    DEFAULT_SETTINGS,
    OverlayContext,
    OverlayType,
    OverlayUnavailable,
    overlay_drawings,
    overlay_options,
    overlay_summary,
    register,
    run_detector,
    visible_events,
)
from backtester.ui.pages.chart import selected_overlays

GREEN = (1.0, 1.2, 0.9, 1.1)
RED = (1.1, 1.2, 0.9, 1.0)


class GreenCandles(Detector[Event]):
    """Fake detector: an event at every green candle. Records the views it was given."""

    def __init__(self, seen: list[int] | None = None):
        self.seen = seen if seen is not None else []

    def update(self, view: SeriesView) -> list[Event]:
        assert isinstance(view, SeriesView)
        self.seen.append(view.cursor)
        c = view.current
        return [Event(view.cursor, c.ts + view.timeframe.duration)] if c.is_green else []


def draw_markers(events, ctx: OverlayContext):
    return [Marker(e.confirmed_index, 1.0, "g", "circle", "#000000", 5) for e in events]


def fake_registry(**extra) -> dict[str, OverlayType]:
    green = OverlayType(
        "green", "Green", lambda r, _s: run_detector(GreenCandles(), r), draw_markers
    )
    return {"green": green, **extra}


def replay_of(*ohlc) -> Replay:
    return Replay(build_series(list(ohlc)))


def test_run_detector_feeds_every_candle_once_in_order_as_views():
    seen: list[int] = []
    events = run_detector(GreenCandles(seen), replay_of(GREEN, RED, GREEN, GREEN))
    assert seen == [0, 1, 2, 3]
    assert [e.confirmed_index for e in events] == [0, 2, 3]


def test_visible_events_stop_at_the_cursor_and_start_at_first_x():
    events = run_detector(GreenCandles(), replay_of(GREEN, GREEN, GREEN, GREEN, GREEN))
    assert [e.confirmed_index for e in visible_events(events, cursor=2)] == [0, 1, 2]
    assert [e.confirmed_index for e in visible_events(events, cursor=3, first_x=2)] == [2, 3]


def test_switch_off_means_no_overlays_whatever_the_dropdown_says():
    assert selected_overlays([], ["green"]) == []
    assert selected_overlays(None, ["green"]) == []
    assert selected_overlays(["on"], None) == []
    assert selected_overlays(["on"], ["green"]) == ["green"]


def test_panel_lists_registered_types_in_order_disabled_while_the_switch_is_off():
    registry = fake_registry(red=OverlayType("red", "Red", lambda r, _s: [], draw_markers))
    assert overlay_options(registry=registry) == [
        {"label": "Green", "value": "green", "disabled": False},
        {"label": "Red", "value": "red", "disabled": False},
    ]
    assert all(o["disabled"] for o in overlay_options(enabled=False, registry=registry))


def test_register_keeps_the_roadmap_order_whatever_the_import_order():
    registry = {}
    for key, order in (("d", "2.11"), ("c", "2.5"), ("a", "2.2"), ("b", "2.3")):
        overlay = OverlayType(key, key.upper(), lambda r, _s: [], draw_markers, order=order)
        register(overlay, registry)
    assert list(registry) == ["a", "b", "c", "d"]  # 2.11 after 2.5


def test_sub_entries_right_under_their_type_only_tickable_while_it_is():
    def noop(replay, settings):
        return []

    registry = {
        "a": OverlayType("a", "A", noop, draw_markers, parts=(("x", "★ xs"),)),
        "b": OverlayType("b", "B", noop, draw_markers),
    }
    values = [(o["value"], o["disabled"]) for o in overlay_options([], True, registry)]
    assert values == [("a", False), ("a.x", True), ("b", False)]
    ticked = overlay_options(["a"], True, registry)
    assert ticked[1]["disabled"] is False and ticked[1]["label"].endswith("↳ ★ xs")
    assert overlay_summary(["b", "a", "a.x"], registry) == "Overlay types: A, B"
    assert overlay_summary([], registry) == "Overlay types"


def test_only_selected_types_are_drawn_and_unknown_keys_are_ignored():
    replay = replay_of(GREEN, RED, GREEN)
    registry = fake_registry()
    traces, messages = chart_overlays(replay, ["green", "gone"], 2, 0, registry=registry)
    assert [d.x for d in traces] == [0, 2]
    assert messages == []
    assert chart_overlays(replay, [], 2, 0, registry=registry) == ([], [])


def test_unavailable_overlay_becomes_a_message_not_an_error():
    def refuse(replay, _settings):
        raise OverlayUnavailable("doji threshold not defined for TEST")

    registry = fake_registry(no=OverlayType("no", "Nope", refuse, draw_markers))
    ctx = OverlayContext("TEST", cursor=0, first_x=0)
    replay = replay_of(GREEN)
    drawings, messages = overlay_drawings(
        lambda o: o.detect(replay, DEFAULT_SETTINGS), ["green", "no"], ctx, registry
    )
    assert len(drawings) == 1
    assert messages == ["Nope: doji threshold not defined for TEST"]


def test_the_browser_gets_only_events_confirmed_up_to_the_cursor():
    replay = replay_of(GREEN, RED, GREEN, GREEN)
    registry = fake_registry()
    data = ChartData(replay, lambda o: o.detect(replay, DEFAULT_SETTINGS), registry=registry)

    def xs(cursor):
        return sorted(d["x"] for d in data.full(["green"], cursor)["types"]["green"])

    assert xs(1) == [0]  # cursor 1: candle 1 (closes 00:10) is the latest closed candle
    assert xs(3) == [0, 2, 3]
    delta = data.delta(["green"], 1, 2)
    assert [d["x"] for d in delta["add"]] == [2] and delta["remove"] == []
