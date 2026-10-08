"""FVG overlay on the chart. Spec: ROADMAP.md › 2.5, confluences.md › Fair value gap.

Gold M5 candles (open, high, low, close). Candles 1 and 3 leave a bullish gap
4403-4410 (candle 1 high, candle 3 low), confirmed by candle 3. With the default ATR(14)
every candle here is in the ATR warm-up, so candle 2 is never a strong move: the FVG only
exists with the strong-move filter off (`OFF`, the default).
"""

from __future__ import annotations

from conftest import build_series
from overlay_helpers import boxes, by_layer, chart_overlays, hovers, points

from backtester.engine.replay import Replay
from backtester.ui.chart_config import DEFAULT_CONFIG
from backtester.ui.drawing import Hover
from backtester.ui.overlays import OVERLAYS, OverlaySettings, overlay_options

OFF = OverlaySettings()
FVG = [
    (4400.0, 4402.0, 4398.0, 4401.0),  # 0
    (4401.0, 4403.0, 4399.0, 4402.0),  # 1: candle 1, high 4403
    (4402.0, 4420.0, 4401.0, 4418.0),  # 2: the push
    (4418.0, 4425.0, 4410.0, 4422.0),  # 3: candle 3, low 4410 -> bullish FVG 4403-4410
]
ABOVE = (4422.0, 4428.0, 4415.0, 4426.0)  # stays above the FVG: no tap
TAP = (4420.0, 4421.0, 4408.0, 4415.0)  # red, wick into the FVG
CONFIRM = (4415.0, 4422.0, 4412.0, 4420.0)  # green close above 4410
INVALIDATE = (4415.0, 4416.0, 4400.0, 4401.0)  # close below 4403


def gold_replay(*ohlc) -> Replay:
    return Replay(build_series(list(ohlc), symbol="XAUUSD"))


ALL = ["fvg", "fvg.confirmed", "fvg.invalidated"]  # FVG with both dropdown sub-entries


def drawn_at(replay, cursor, settings=OFF, first_x=0, keys=ALL):
    drawings, messages = chart_overlays(replay, keys, cursor, first_x, settings=settings)
    assert messages == []
    return by_layer(drawings)


def test_fvg_is_in_the_panel_after_bos_with_its_sub_entries_right_below():
    assert OVERLAYS["fvg"].label == "FVG"
    assert list(OVERLAYS)[:3] == ["swings", "bos", "fvg"]  # roadmap order
    options = overlay_options(["fvg"])
    values = [o["value"] for o in options]
    i = values.index("fvg")
    assert values[i : i + 3] == ALL
    assert options[i + 1]["label"].endswith("↳ ★ confirmations")
    assert options[i + 2]["label"].endswith("↳ ✕ invalidations")
    assert not options[i + 1]["disabled"]
    assert overlay_options([])[i + 1]["disabled"]  # FVG not ticked


def test_nothing_before_candle_3_closes():
    replay = gold_replay(*FVG)
    assert drawn_at(replay, 2) == {}


def test_active_box_from_candle_1_to_the_cursor_with_hover_over_the_box_no_dot():
    replay = gold_replay(*FVG, *[ABOVE] * 4)
    t = drawn_at(replay, 7)
    assert boxes(t["FVG box"]) == [(1, 7, 4403.0, 4410.0)]
    assert t["FVG box"][0].fill is not None
    [hover] = t["FVG"]
    assert isinstance(hover, Hover)  # a hover area along the box, no dot on candle 3
    assert (hover.x0, hover.x1, hover.y) == (1, 7, 4406.5)
    text = hover.text
    assert "Bullish FVG 4403.000 – 4410.000 (size 7.000)" in text
    assert "no ATR yet: not a strong move" in text
    assert "M5 trend: none yet (no BOS)" in text
    assert "state: active" in text
    assert "FVG state" not in t


def test_open_box_extends_to_the_cursor_until_it_is_used():
    replay = gold_replay(*FVG, *[ABOVE] * 30, TAP, CONFIRM)
    assert boxes(drawn_at(replay, 33)["FVG box"]) == [(1, 33, 4403.0, 4410.0)]
    assert boxes(drawn_at(replay, 34)["FVG box"]) == [(1, 34, 4403.0, 4410.0)]  # tapped
    assert boxes(drawn_at(replay, 35)["FVG box"]) == [(1, 35, 4403.0, 4410.0)]  # confirmed


def test_replay_shows_the_state_at_the_cursor_and_the_box_ends_at_confirmation():
    replay = gold_replay(*FVG, TAP, CONFIRM, ABOVE)
    tapped = drawn_at(replay, 4)
    assert "state: tapped" in hovers(tapped["FVG"])[0]
    assert "FVG state" not in tapped  # no marker for a tap
    assert boxes(tapped["FVG box"]) == [(1, 4, 4403.0, 4410.0)]

    later = drawn_at(replay, 6)
    assert boxes(later["FVG box"]) == [(1, 5, 4403.0, 4410.0)]  # ends at the confirming candle
    [mark] = later["FVG state"]
    assert mark.shape == "star" and mark.part == "confirmed"
    assert points([mark]) == [(5, 4410.0)]  # at the top edge (where price comes from)
    assert "state: confirmed" in hovers(later["FVG"])[0]


def test_invalidated_fvg_ends_at_that_candle_drawn_fainter():
    replay = gold_replay(*FVG, INVALIDATE)
    t = drawn_at(replay, 4)
    assert "FVG box" not in t
    [faded] = t["FVG box (invalidated)"]
    assert boxes([faded]) == [(1, 4, 4403.0, 4410.0)]
    assert faded.fill_opacity == DEFAULT_CONFIG.fvg_invalidated_opacity
    [mark] = t["FVG state"]
    assert mark.shape == "x" and mark.y == 4403.0  # far edge


def test_strong_move_filter_switch_off_by_default():
    replay = gold_replay(*FVG, ABOVE)
    assert not OverlaySettings().fvg_strong_move_filter
    assert drawn_at(replay, 4, OverlaySettings(fvg_strong_move_filter=True)) == {}
    assert "FVG" in drawn_at(replay, 4, OFF)


def test_symbol_without_doji_threshold_shows_a_message():
    replay = Replay(build_series(FVG, symbol="EURUSD"))
    drawings, messages = chart_overlays(replay, ["fvg"], 3, 0, settings=OFF)
    assert drawings == [] and messages and messages[0].startswith("FVG:")


def test_confirmation_and_invalidation_markers_only_with_their_sub_entries():
    confirmed = gold_replay(*FVG, TAP, CONFIRM)
    t = drawn_at(confirmed, 5, keys=["fvg", "fvg.invalidated"])
    assert "FVG state" not in t  # no ★ without its sub-entry, and taps have no marker
    assert boxes(t["FVG box"]) == [(1, 5, 4403.0, 4410.0)]  # box still ends there

    invalidated = gold_replay(*FVG, INVALIDATE)
    t = drawn_at(invalidated, 4, keys=["fvg", "fvg.confirmed"])
    assert "FVG state" not in t and "FVG box (invalidated)" in t


def test_a_sub_entry_alone_draws_nothing():
    replay = gold_replay(*FVG, TAP, CONFIRM)
    assert drawn_at(replay, 5, keys=["fvg.confirmed", "fvg.invalidated"]) == {}


def test_every_fvg_is_green_whatever_its_direction():
    bearish = [(8800 - o, 8800 - lo, 8800 - h, 8800 - c) for o, h, lo, c in FVG]  # mirrored
    for ohlc, direction in ((FVG, "Bullish"), (bearish, "Bearish")):
        t = drawn_at(gold_replay(*ohlc), 3)
        assert hovers(t["FVG"])[0].startswith(f"{direction} FVG")
        assert t["FVG box"][0].fill == DEFAULT_CONFIG.fvg_color == "#089981"
