"""Swings overlay on the chart. Spec: ROADMAP.md › 2.2."""

from __future__ import annotations

from conftest import build_series
from overlay_helpers import by_layer, chart_overlays, hovers, lines, points

from backtester.engine.replay import Replay
from backtester.ui.drawing import Marker
from backtester.ui.overlays import DEFAULT_SETTINGS, OVERLAYS, OverlayContext, OverlayUnavailable
from backtester.ui.swing_overlay import detect_swings, draw_swings

GREEN = (4400.0, 4410.0, 4399.0, 4405.0)
RED = (4405.0, 4407.0, 4390.0, 4391.0)
DOJI = (4391.0, 4420.0, 4389.0, 4391.03)
GREEN2 = (4391.0, 4400.0, 4392.0 - 2.5, 4399.0)


def gold_replay(*ohlc) -> Replay:
    return Replay(build_series(list(ohlc), symbol="XAUUSD"))


def markers(drawings, shape):
    return [d for d in drawings if isinstance(d, Marker) and d.shape == shape]


def test_swings_are_in_the_dropdown():
    assert "swings" in OVERLAYS and OVERLAYS["swings"].label == "Swings"


def test_marker_at_extreme_wick_line_and_hover_dot_at_confirming_candle():
    replay = gold_replay(GREEN, RED, DOJI, GREEN2)
    drawings, messages = chart_overlays(replay, ["swings"], cursor=3, first_x=0)
    assert messages == []
    layers = by_layer(drawings)
    high = layers["swing high"]
    assert points(markers(high, "triangle-down")) == [(0, 4410.0)]  # ▼ at the wick
    assert points(markers(high, "circle")) == [(1, 4410.0)]  # dot on the confirming candle
    assert lines(high) == [(0, 1, 4410.0, 4410.0)]
    assert "Swing high 4410.000" in hovers(high)[0]
    low = layers["swing low"]
    # low: red (low 4390) then, skipping the doji, green (low 4389.5) -> 4389.5 at candle 3
    assert points(markers(low, "triangle-up")) == [(3, 4389.5)]
    assert [x for x, _ in points(markers(low, "circle"))] == [3]
    # extreme wick on the confirming candle: the line still spans from the red candle
    assert lines(low) == [(1, 3, 4389.5, 4389.5)]


def test_replay_cursor_hides_swings_not_yet_confirmed():
    replay = gold_replay(GREEN, RED, DOJI, GREEN2)
    drawings, _ = chart_overlays(replay, ["swings"], cursor=2, first_x=0)
    assert set(by_layer(drawings)) == {"swing high"}


def test_symbol_without_doji_threshold_shows_a_message():
    replay = Replay(build_series([GREEN, RED], symbol="FOOBAR"))
    drawings, messages = chart_overlays(replay, ["swings"], cursor=1, first_x=0)
    assert drawings == []
    assert messages and messages[0].startswith("Swings: no doji threshold for FOOBAR")
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
        drawings, messages = chart_overlays(replay, ["swings"], cursor=1, first_x=0)
        assert messages == [] and set(by_layer(drawings)) == {"swing high"}


def test_draw_nothing_for_no_swings():
    assert draw_swings([], OverlayContext("XAUUSD", 0, 0)) == []


def test_doji_threshold_from_the_settings_menu():
    """Settings › Detectors › Doji threshold: raised to 10, GREEN (body 5) and GREEN2
    (body 8) are dojis too, so only RED counts and no swing is confirmed (with the spec's
    0.065 there are both); the other symbols keep the spec's threshold."""
    from backtester.settings import settings_from_values, to_json
    from backtester.ui.pages.chart import overlay_settings

    assert overlay_settings([], "").doji_max_body == ()
    strategy = to_json(settings_from_values({"strategy.swings.doji_max_body.XAUUSD": 10.0}))
    settings = overlay_settings([], strategy)
    assert settings.doji_max_body == (("XAUUSD", 10.0),)
    assert settings.swing_config.doji_threshold("XAUUSD") == 10.0
    assert settings.swing_config.doji_threshold("GBPUSD") == (
        DEFAULT_SETTINGS.swing_config.doji_threshold("GBPUSD")
    )
    replay = gold_replay(GREEN, RED, DOJI, GREEN2)
    drawings, _ = chart_overlays(replay, ["swings"], cursor=3)
    assert set(by_layer(drawings)) == {"swing high", "swing low"}
    drawings, messages = chart_overlays(replay, ["swings"], cursor=3, settings=settings)
    assert drawings == [] and messages == []


def test_doji_range_share_from_the_settings_menu_reaches_the_overlay_detectors():
    from backtester.detectors.swings import RangeShare
    from backtester.settings import settings_from_values, to_json
    from backtester.ui.pages.chart import overlay_settings

    assert overlay_settings([], "").swing_config.doji_range_share == 0.0
    strategy = to_json(settings_from_values({"strategy.swings.doji_range_share": 0.1}))
    config = overlay_settings([], strategy).swing_config
    assert config.doji_range_share == 0.1
    assert isinstance(config.doji_threshold("NAS100"), RangeShare)
