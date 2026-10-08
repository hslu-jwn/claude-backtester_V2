"""Swings overlay on the chart. Spec: ROADMAP.md › 2.2."""

from __future__ import annotations

from conftest import build_series
from plotly_helpers import chart_overlays

from backtester.engine.replay import Replay
from backtester.ui.overlays import OVERLAYS, OverlayContext, OverlayUnavailable
from backtester.ui.swing_overlay import detect_swings, draw_swings

GREEN = (4400.0, 4410.0, 4399.0, 4405.0)
RED = (4405.0, 4407.0, 4390.0, 4391.0)
DOJI = (4391.0, 4420.0, 4389.0, 4391.03)
GREEN2 = (4391.0, 4400.0, 4392.0 - 2.5, 4399.0)


def gold_replay(*ohlc) -> Replay:
    return Replay(build_series(list(ohlc), symbol="XAUUSD"))


def test_swings_are_in_the_dropdown():
    assert "swings" in OVERLAYS and OVERLAYS["swings"].label == "Swings"


def test_marker_at_extreme_wick_line_and_hover_dot_at_confirming_candle():
    replay = gold_replay(GREEN, RED, DOJI, GREEN2)
    traces, messages = chart_overlays(replay, ["swings"], cursor=3, first_x=0)
    assert messages == []
    by_name = {}
    for t in traces:
        by_name.setdefault(t.name, []).append(t)
    line, triangle, dot = by_name["swing high"]
    assert list(triangle.x) == [0] and list(triangle.y) == [4410.0]
    assert list(dot.x) == [1] and list(triangle.marker.symbol) == ["triangle-down"]
    assert list(line.x) == [0, 1, None]
    assert "Swing high 4410.000" in dot.text[0]
    low_line, low_triangle, low_dot = by_name["swing low"]
    # low: red (low 4390) then, skipping the doji, green (low 4389.5) -> 4389.5 at candle 3
    assert list(low_triangle.y) == [4389.5] and list(low_dot.x) == [3]
    # extreme wick on the confirming candle: the line still spans from the red candle
    assert list(low_line.x) == [1, 3, None] and list(low_line.y) == [4389.5, 4389.5, None]


def test_replay_cursor_hides_swings_not_yet_confirmed():
    replay = gold_replay(GREEN, RED, DOJI, GREEN2)
    traces, _ = chart_overlays(replay, ["swings"], cursor=2, first_x=0)
    assert {t.name for t in traces} == {"swing high"}


def test_symbol_without_doji_threshold_shows_a_message():
    replay = Replay(build_series([GREEN, RED], symbol="EURUSD"))
    traces, messages = chart_overlays(replay, ["swings"], cursor=1, first_x=0)
    assert traces == []
    assert messages and messages[0].startswith("Swings: no doji threshold for EURUSD")
    try:
        detect_swings(replay)
    except OverlayUnavailable:
        pass
    else:
        raise AssertionError("expected OverlayUnavailable")


def test_gbp_pairs_have_a_threshold_so_their_swings_are_drawn():
    # the bug behind "swings don't show": GBP pairs had no threshold, so the overlay was
    # only a note in the message line
    for symbol in ("GBPUSD", "GBPJPY"):
        replay = Replay(
            build_series([(1.30, 1.31, 1.29, 1.305), (1.305, 1.307, 1.28, 1.285)], symbol=symbol)
        )
        traces, messages = chart_overlays(replay, ["swings"], cursor=1, first_x=0)
        assert messages == [] and {t.name for t in traces} == {"swing high"}


def test_draw_nothing_for_no_swings():
    assert draw_swings([], OverlayContext("XAUUSD", 0, 0)) == []
