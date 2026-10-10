"""Breaker block overlay. Spec: ROADMAP.md › 2.7 / 8.2.3, confluences.md › Breaker block.

Same candles as tests/detectors/test_breaker.py (gold doji threshold 0.065): a bullish
breaker 9.6 - 10.28 (candles 2-4) from the BOS at candle 7, tapped by 8, confirmed by 9.
"""

from __future__ import annotations

from conftest import build_series
from overlay_helpers import boxes, by_layer, chart_overlays, hovers

from backtester.engine.replay import Replay
from backtester.ui.chart_config import DEFAULT_CONFIG
from backtester.ui.overlays import OVERLAYS, overlay_options

OHLC = [
    (10.0, 10.3, 9.9, 10.2),
    (10.2, 10.25, 9.7, 9.8),
    (9.8, 10.0, 9.6, 9.95),
    (9.95, 10.05, 9.5, 9.96),
    (9.96, 10.28, 9.9, 10.25),
    (10.25, 10.6, 10.1, 10.15),
    (10.15, 10.3, 10.05, 10.25),
    (10.25, 10.8, 10.2, 10.75),  # 7: bullish BOS
    (10.75, 10.78, 10.2, 10.3),  # 8: tap
    (10.3, 10.5, 10.25, 10.45),  # 9: confirms
]
ALL = ["breaker", "breaker.confirmed", "breaker.invalidated"]


def drawn_at(cursor):
    replay = Replay(build_series(OHLC, symbol="XAUUSD"))
    drawings, messages = chart_overlays(replay, ALL, cursor, 0)
    assert messages == []
    return by_layer(drawings)


def test_in_the_panel_after_order_block_with_sub_entries():
    assert OVERLAYS["breaker"].label == "Breaker block"
    assert list(OVERLAYS)[:6] == ["swings", "bos", "fvg", "ob", "breaker", "bpr"]
    values = [o["value"] for o in overlay_options(["breaker"])]
    i = values.index("breaker")
    assert values[i : i + 3] == ALL


def test_orange_box_from_the_bos_candle_until_its_confirmation():
    assert drawn_at(6) == {}
    t = drawn_at(7)
    assert boxes(t["Breaker box"]) == [(2, 7, 9.6, 10.28)]
    assert t["Breaker box"][0].fill == DEFAULT_CONFIG.breaker_color == "#ff9800"
    text = hovers(t["Breaker"])[0]
    assert "Bullish breaker 9.600 – 10.280 (size 0.680)" in text
    assert "move into the swing high 10.600" in text
    assert "state: active" in text
    t = drawn_at(9)
    assert boxes(t["Breaker box"]) == [(2, 9, 9.6, 10.28)]
    assert [m.shape for m in t["Breaker state"]] == ["star"]
