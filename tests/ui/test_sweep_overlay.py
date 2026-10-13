"""Liquidity sweep overlay on the chart. Spec: ROADMAP.md › 2.11, confluences.md › Liquidity
sweep.

Candles as in tests/detectors/test_sweep.py (gold doji threshold 0.065): bullish BOS of 11.0
at candle 3, swing high 11.5, candle 6 runs to 11.8, bearish BOS at candle 8.
"""

from __future__ import annotations

from conftest import build_series
from overlay_helpers import by_layer, chart_overlays, hovers, lines, points

from backtester.detectors.sweep import SweepConfig
from backtester.engine.replay import Replay
from backtester.ui.chart_config import DEFAULT_CONFIG
from backtester.ui.overlays import OVERLAYS

SWEEP = [
    (10.0, 11.0, 9.5, 10.8),  # 0 green
    (10.8, 10.9, 10.0, 10.2),  # 1 red: swing high 11.0
    (10.2, 10.6, 9.8, 10.5),  # 2 green: swing low 9.8
    (10.5, 11.5, 10.4, 11.3),  # 3 green: bullish BOS of 11.0
    (11.3, 11.4, 10.9, 11.0),  # 4 red: swing high 11.5 (wick on candle 3)
    (11.0, 11.3, 10.95, 11.2),  # 5 green: swing low 10.9
    (11.2, 11.8, 11.1, 11.7),  # 6 green: the top, takes 11.0 and 11.5
    (11.7, 11.75, 11.2, 11.3),  # 7 red
    (11.3, 11.35, 10.8, 10.85),  # 8 red: bearish BOS of 10.9 -> sweep
]


def drawn_at(cursor):
    replay = Replay(build_series(SWEEP, symbol="XAUUSD"))
    drawings, messages = chart_overlays(replay, ["sweep"], cursor, 0)
    assert messages == []
    return by_layer(drawings)


def test_liquidity_sweep_in_the_panel_after_session_zones():
    assert OVERLAYS["sweep"].label == "Liquidity sweep"
    keys = list(OVERLAYS)
    assert keys.index("sweep") == keys.index("session_zones") + 1


def test_nothing_until_the_bos_candle():
    assert drawn_at(7) == {}


def test_magenta_line_from_the_highest_swept_swing_to_the_sweeping_candle():
    t = drawn_at(8)
    line, wick = t["Sweep"], t["Sweep wick"]
    # highest swept high 11.5 has its wick on candle 3; the sweeping candle is 6
    assert lines(line) == [(3, 6, 11.5, 11.5)]
    assert line[0].color == DEFAULT_CONFIG.sweep_color == "#ff00ff"
    assert points(wick) == [(6, 11.8)] and wick[0].shape == "triangle-down"
    text = hovers(wick)[0]
    assert "Bearish liquidity sweep of highs" in text
    assert "high 11.500" in text and "high 11.000" in text  # every swept high listed
    assert "bearish BOS of 10.900" in text


def test_toolbar_sweep_tweak_becomes_the_overlay_settings_sweep_config():
    from backtester.ui.pages.chart import overlay_settings, sweep_config

    assert sweep_config(None) == SweepConfig()  # nothing chosen: today's rules
    assert sweep_config({"tol": "none", "cancel": "off", "n": 3}) == SweepConfig()
    chosen = sweep_config({"tol": "0.25", "cancel": "c2"})
    assert chosen.equal_tolerance_atr == 0.25 and chosen.two_closes_cancel
    assert chosen.cancel_closes == 2 and not chosen.cancel_wick_first
    wick = sweep_config({"cancel": "w3", "n": 5, "top": True})
    assert (wick.cancel_closes, wick.cancel_wick_first) == (3, True)
    assert wick.lookback_swings == 5 and wick.bos_before_top
    assert overlay_settings([], "", {"tol": "0", "cancel": "off"}).sweep.equal_tolerance_atr == 0.0
