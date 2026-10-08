"""Order block overlay on the chart. Spec: ROADMAP.md › 2.6, confluences.md › Order block.

Gold M5 candles (open, high, low, close): a swing high 4410 (confirmed by candle 1), the
red leg 1-3 into the swing low 4390 (confirmed by candle 4), then candle 5 closes above
4410: a bullish BOS, so the leg is a bullish OB 4390-4409. With the default ATR(14) every
candle is in the ATR warm-up (never strong), so the OB only exists with the OB filter off.
"""

from __future__ import annotations

from conftest import build_series
from overlay_helpers import boxes, by_layer, chart_overlays, hovers

from backtester.engine.replay import Replay
from backtester.ui.chart_config import DEFAULT_CONFIG
from backtester.ui.overlays import OVERLAYS, OverlaySettings, overlay_options

OFF = OverlaySettings(ob_strong_move_filter=False)
OB = [
    (4400.0, 4410.0, 4399.0, 4408.0),  # 0 green
    (4408.0, 4409.0, 4400.0, 4402.0),  # 1 red: confirms high 4410, first leg candle
    (4402.0, 4403.0, 4395.0, 4397.0),  # 2 red
    (4397.0, 4398.0, 4390.0, 4392.0),  # 3 red
    (4392.0, 4400.0, 4391.0, 4399.0),  # 4 green: confirms low 4390
    (4399.0, 4415.0, 4398.0, 4414.0),  # 5 green: bullish BOS of 4410
]
TAP = (4414.0, 4415.0, 4405.0, 4406.0)  # 6 red: wick into the OB
CONFIRM = (4406.0, 4412.0, 4405.0, 4411.0)  # 7 green: close above 4409
ALL = ["ob", "ob.confirmed", "ob.invalidated"]


def gold_replay(*ohlc) -> Replay:
    return Replay(build_series(list(ohlc), symbol="XAUUSD"))


def drawn_at(replay, cursor, settings=OFF, keys=ALL):
    drawings, messages = chart_overlays(replay, keys, cursor, 0, settings=settings)
    assert messages == []
    return by_layer(drawings)


def test_order_block_in_the_panel_after_fvg_with_sub_entries():
    assert OVERLAYS["ob"].label == "Order block"
    assert list(OVERLAYS)[:4] == ["swings", "bos", "fvg", "ob"]
    values = [o["value"] for o in overlay_options(["ob"])]
    i = values.index("ob")
    assert values[i : i + 3] == ALL


def test_nothing_before_the_bos_then_a_yellow_box_from_the_legs_first_candle():
    replay = gold_replay(*OB, TAP)
    assert drawn_at(replay, 4) == {}
    t = drawn_at(replay, 5)
    assert boxes(t["OB box"]) == [(1, 5, 4390.0, 4409.0)]
    assert t["OB box"][0].fill == DEFAULT_CONFIG.ob_color == "#fbc02d"  # yellow
    text = hovers(t["OB"])[0]
    assert "Bullish OB 4390.000 – 4409.000 (size 19.000)" in text
    assert "leg into swing low 4390.000" in text
    assert "bullish BOS of 4410.000" in text
    assert "no strong candle in the move away yet (filter off)" in text
    assert "state: active" in text


def test_box_ends_at_confirmation_with_its_marker():
    replay = gold_replay(*OB, TAP, CONFIRM, (4411.0, 4420.0, 4410.0, 4418.0))
    t = drawn_at(replay, 8)
    assert boxes(t["OB box"]) == [(1, 7, 4390.0, 4409.0)]
    assert [m.shape for m in t["OB state"]] == ["star"]
    assert "state: confirmed" in hovers(t["OB"])[0]


def test_ob_strong_move_filter_switch_on_by_default():
    replay = gold_replay(*OB)
    assert OverlaySettings().ob_strong_move_filter
    assert drawn_at(replay, 5, OverlaySettings()) == {}  # no strong candle (ATR warm-up)
    assert "OB" in drawn_at(replay, 5, OFF)
