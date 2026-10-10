"""Equilibrium overlay on the chart. Spec: ROADMAP.md › 8.2.2, confluences.md › Equilibrium.

Same candles as tests/detectors/test_equilibrium_detector.py (gold doji threshold 0.065):
a bearish EQ from the BOS at candle 3 (no sweep), a bullish EQ 8.7 - 9.15 from the BOS at
candle 8 after a sweep of lows (candle 4), tapped by 9, confirmed by 10.
"""

from __future__ import annotations

import pytest
from conftest import build_series
from overlay_helpers import boxes, by_layer, chart_overlays, hovers

from backtester.engine.replay import Replay
from backtester.ui.chart_config import DEFAULT_CONFIG
from backtester.ui.overlays import OVERLAYS, overlay_options

OHLC = [
    (10.0, 10.5, 9.9, 10.4),
    (10.4, 10.45, 9.5, 9.6),
    (9.6, 9.9, 9.55, 9.8),
    (9.8, 9.85, 9.0, 9.1),  # 3: bearish BOS
    (9.1, 9.15, 8.7, 8.8),  # 4: the bottom
    (8.8, 9.3, 8.75, 9.2),
    (9.2, 9.25, 8.9, 9.0),
    (9.0, 9.2, 8.95, 9.15),
    (9.15, 9.6, 9.1, 9.55),  # 8: bullish BOS
    (9.55, 9.58, 9.1, 9.2),  # 9: tap
    (9.2, 9.5, 9.12, 9.45),  # 10: confirms
]
ALL = ["eq", "eq.confirmed", "eq.invalidated"]


def drawn_at(cursor):
    replay = Replay(build_series(OHLC, symbol="XAUUSD"))
    drawings, messages = chart_overlays(replay, ALL, cursor, 0)
    assert messages == []
    return by_layer(drawings)


def test_in_the_panel_with_sub_entries():
    assert OVERLAYS["eq"].label == "Equilibrium"
    values = [o["value"] for o in overlay_options(["eq"])]
    i = values.index("eq")
    assert values[i : i + 3] == ALL


def test_box_appears_at_the_bos_candle_and_ends_at_its_confirmation():
    assert drawn_at(7)["EQ box"] and len(drawn_at(7)["EQ box"]) == 1  # only the bearish one
    t = drawn_at(8)
    bull = [b for b in boxes(t["EQ box"]) if b[0] == 4]
    assert bull == [
        (4, 8, 8.7, pytest.approx(9.15))
    ]  # from the sweep extreme's candle, at the BOS candle
    assert t["EQ box"][0].fill == DEFAULT_CONFIG.equilibrium_color
    text = next(h for h in hovers(t["EQ"]) if "Bullish" in h)
    assert "Bullish equilibrium 9.150 (50%)" in text
    assert "leg 8.700 (sweep extreme) → 9.600 (BOS candle wick)" in text
    assert "state: active" in text
    t = drawn_at(10)
    assert [b for b in boxes(t["EQ box"]) if b[0] == 4] == [(4, 10, 8.7, pytest.approx(9.15))]
    assert [m.shape for m in t["EQ state"]] == ["star"]
