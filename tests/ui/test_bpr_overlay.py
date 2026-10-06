"""BPR overlay on the chart. Spec: ROADMAP.md › 2.8, confluences.md › Balanced price range.

Gold M5 candles (open, high, low, close): a bearish FVG 4130-4140 (candles 0-2), candle 4
closes above 4140 (invalidates it), candle 5's low 4135 leaves a bullish FVG 4125-4135,
so a bullish BPR 4130-4135 exists from candle 5.
"""

from __future__ import annotations

from conftest import build_series

from backtester.engine.replay import Replay
from backtester.ui.chart_figure import DEFAULT_CONFIG
from backtester.ui.overlays import DEFAULT_SETTINGS, OVERLAYS, OverlaySettings, overlay_options
from backtester.ui.pages.chart import chart_overlays

BPR = [
    (4150.0, 4152.0, 4140.0, 4142.0),  # 0: low 4140
    (4142.0, 4143.0, 4120.0, 4122.0),  # 1
    (4122.0, 4130.0, 4115.0, 4118.0),  # 2: high 4130 -> bearish FVG 4130-4140
    (4118.0, 4125.0, 4116.0, 4124.0),  # 3: high 4125
    (4124.0, 4150.0, 4123.0, 4148.0),  # 4: closes above 4140
    (4148.0, 4160.0, 4135.0, 4158.0),  # 5: low 4135 -> bullish FVG 4125-4135 -> BPR
]
TAP = (4158.0, 4159.0, 4132.0, 4134.0)  # 6: wick into 4130-4135
CONFIRM = (4134.0, 4145.0, 4133.0, 4144.0)  # 7: green close above 4135
ALL = ["bpr", "bpr.confirmed", "bpr.invalidated"]


def gold_replay(*ohlc) -> Replay:
    return Replay(build_series(list(ohlc), symbol="XAUUSD"))


def traces_at(replay, cursor, settings=DEFAULT_SETTINGS, keys=ALL):
    traces, messages = chart_overlays(replay, keys, cursor, 0, settings=settings)
    assert messages == []
    return {t.name: t for t in traces}


def box(trace):
    xs, ys = list(trace.x), list(trace.y)
    return [(xs[i], xs[i + 1], ys[i], ys[i + 2]) for i in range(0, len(xs), 6)]


def test_bpr_in_the_panel_after_order_block_with_sub_entries():
    assert OVERLAYS["bpr"].label == "BPR"
    assert list(OVERLAYS)[:5] == ["swings", "bos", "fvg", "ob", "bpr"]
    values = [o["value"] for o in overlay_options(["bpr"])]
    i = values.index("bpr")
    assert values[i : i + 3] == ALL


def test_nothing_before_the_newer_fvgs_candle_3_then_a_purple_box():
    replay = gold_replay(*BPR, TAP)
    assert traces_at(replay, 4) == {}
    t = traces_at(replay, 5)
    assert box(t["BPR box"]) == [(0, 5, 4130.0, 4135.0)]  # from the older FVG's candle 1
    assert t["BPR box"].fillcolor.startswith("rgba(156,39,176,")  # purple #9c27b0
    assert DEFAULT_CONFIG.bpr_color == "#9c27b0"
    text = t["BPR"].text[0]
    assert "Bullish BPR 4130.000 – 4135.000 (size 5.000)" in text
    assert "older: bearish FVG 4130.000 – 4140.000" in text
    assert "newer: bullish FVG 4125.000 – 4135.000" in text
    assert "older invalidated by candle 2 of the newer FVG" in text
    assert "state: active" in text


def test_box_ends_at_confirmation_with_its_marker():
    replay = gold_replay(*BPR, TAP, CONFIRM, (4144.0, 4150.0, 4143.0, 4149.0))
    t = traces_at(replay, 8)
    assert box(t["BPR box"]) == [(0, 7, 4130.0, 4135.0)]
    assert list(t["BPR state"].marker.symbol) == ["star"]
    assert "state: confirmed" in t["BPR"].text[0]


def test_follows_the_fvg_strong_move_filter_switch():
    replay = gold_replay(*BPR)
    on = OverlaySettings(fvg_strong_move_filter=True)
    assert traces_at(replay, 5, on) == {}  # ATR warm-up: no strong candle 2, no FVG
