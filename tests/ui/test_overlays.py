"""Overlay switch, type dropdown and the no-lookahead filter. Spec: ROADMAP.md › Phase 2.

Uses a fake detector (one event per green candle) in a private registry, so these tests
don't depend on which real detectors are registered.
"""

from __future__ import annotations

from datetime import UTC, datetime

import plotly.graph_objects as go
from conftest import build_series

from backtester.core.series import SeriesView
from backtester.detectors.base import Detector, Event
from backtester.engine.replay import Replay
from backtester.ui.chart_figure import CANDLE_TRACES, DEFAULT_CONFIG, ChartConfig
from backtester.ui.overlays import (
    OverlayContext,
    OverlayType,
    OverlayUnavailable,
    dropdown_options,
    overlay_traces,
    run_detector,
    visible_events,
)
from backtester.ui.pages.chart import chart_overlays, replay_chart, selected_overlays

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
    return [go.Scatter(x=[e.confirmed_index for e in events], y=[1.0] * len(events), name="g")]


def fake_registry(**extra) -> dict[str, OverlayType]:
    green = OverlayType("green", "Green", lambda r: run_detector(GreenCandles(), r), draw_markers)
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


def test_dropdown_lists_registered_types_in_order():
    registry = fake_registry(red=OverlayType("red", "Red", lambda r: [], draw_markers))
    assert dropdown_options(registry) == [
        {"label": "Green", "value": "green"},
        {"label": "Red", "value": "red"},
    ]


def test_only_selected_types_are_drawn_and_unknown_keys_are_ignored():
    replay = replay_of(GREEN, RED, GREEN)
    registry = fake_registry()
    traces, messages = chart_overlays(replay, ["green", "gone"], 2, 0, registry=registry)
    assert [list(t.x) for t in traces] == [[0, 2]]
    assert messages == []
    assert chart_overlays(replay, [], 2, 0, registry=registry) == ([], [])


def test_unavailable_overlay_becomes_a_message_not_an_error():
    def refuse(replay):
        raise OverlayUnavailable("doji threshold not defined for TEST")

    registry = fake_registry(no=OverlayType("no", "Nope", refuse, draw_markers))
    ctx = OverlayContext("TEST", cursor=0, first_x=0)
    replay = replay_of(GREEN)
    traces, messages = overlay_traces(lambda o: o.detect(replay), ["green", "no"], ctx, registry)
    assert len(traces) == 1
    assert messages == ["Nope: doji threshold not defined for TEST"]


def test_replay_draws_only_events_confirmed_up_to_the_cursor():
    replay = replay_of(GREEN, RED, GREEN, GREEN)
    registry = fake_registry()
    # cursor 1: candle 1 (closes 00:10) is the latest closed candle
    state = {"on": True, "picking": False, "playing": False, "start": None}
    state["now"] = datetime(2026, 1, 5, 0, 10, tzinfo=UTC).isoformat()
    fig, _, _ = replay_chart(replay, state, overlay_keys=["green"], registry=registry)
    assert list(fig.data[CANDLE_TRACES].x) == [0]
    state["now"] = datetime(2026, 1, 5, 0, 20, tzinfo=UTC).isoformat()
    fig, _, _ = replay_chart(replay, state, overlay_keys=["green"], registry=registry)
    assert list(fig.data[CANDLE_TRACES].x) == [0, 2, 3]
    assert isinstance(fig.data[0], go.Candlestick)


def test_replay_overlays_start_at_the_first_drawn_candle():
    replay = replay_of(GREEN, GREEN, GREEN, GREEN)
    config = ChartConfig(replay_window=2)
    state = {"on": True, "picking": False, "playing": False, "start": None}
    state["now"] = datetime(2026, 1, 5, 0, 20, tzinfo=UTC).isoformat()
    fig, _, _ = replay_chart(
        replay, state, config, overlay_keys=["green"], registry=fake_registry()
    )
    assert list(fig.data[CANDLE_TRACES].x) == [2, 3]
    assert DEFAULT_CONFIG.replay_window > 2
