"""Liquidity sweep overlay on the chart. Spec: ROADMAP.md › 2.11, confluences.md › Liquidity
sweep.

Candles as in tests/detectors/test_sweep.py (gold doji threshold 0.065): bullish BOS of 11.0
at candle 3, swing high 11.5, candle 6 runs to 11.8, bearish BOS at candle 8.
"""

from __future__ import annotations

from conftest import build_series
from plotly_helpers import chart_overlays

from backtester.engine.replay import Replay
from backtester.ui.chart_figure import DEFAULT_CONFIG
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


def traces_at(cursor):
    replay = Replay(build_series(SWEEP, symbol="XAUUSD"))
    traces, messages = chart_overlays(replay, ["sweep"], cursor, 0)
    assert messages == []
    return {t.name: t for t in traces}


def test_liquidity_sweep_in_the_panel_after_session_zones():
    assert OVERLAYS["sweep"].label == "Liquidity sweep"
    keys = list(OVERLAYS)
    assert keys.index("sweep") == keys.index("session_zones") + 1


def test_nothing_until_the_bos_candle():
    assert traces_at(7) == {}


def test_magenta_line_from_the_highest_swept_swing_to_the_sweeping_candle():
    t = traces_at(8)
    line, wick = t["Sweep"], t["Sweep wick"]
    # highest swept high 11.5 has its wick on candle 3; the sweeping candle is 6
    assert list(line.x) == [3, 6, None] and list(line.y) == [11.5, 11.5, None]
    assert line.line.color == DEFAULT_CONFIG.sweep_color == "#ff00ff"
    assert list(wick.x) == [6] and list(wick.y) == [11.8]
    text = wick.text[0]
    assert "Bearish liquidity sweep of highs" in text
    assert "high 11.500" in text and "high 11.000" in text  # every swept high listed
    assert "bearish BOS of 10.900" in text
