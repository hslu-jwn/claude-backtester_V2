"""BOS + trend overlay on the chart. Spec: ROADMAP.md › 2.3."""

from __future__ import annotations

from datetime import UTC, date, datetime

import plotly.graph_objects as go
from conftest import build_series

from backtester.core.models import Timeframe
from backtester.detectors.trend import Trend, TrendConfig
from backtester.engine.replay import Replay
from backtester.ui.bos_overlay import detect_overall_trend
from backtester.ui.chart_figure import DEFAULT_CONFIG, ChartConfig
from backtester.ui.overlays import OVERLAYS
from backtester.ui.pages.chart import chart_overlays, replay_chart, warmup_start

# swing high 4410 (wick on candle 0, confirmed 1), swing low 4389 (candle 2, confirmed 2)
GREEN = (4400.0, 4410.0, 4399.0, 4405.0)
RED = (4405.0, 4407.0, 4390.0, 4391.0)
GREEN2 = (4391.0, 4400.0, 4389.0, 4399.0)
BREAK_DOWN = (4399.0, 4401.0, 4380.0, 4381.0)  # 3: bearish BOS of 4389, confirms high 4401
GREEN3 = (4381.0, 4395.0, 4379.0, 4394.0)  # 4: swing low 4379
BREAK_UP = (4394.0, 4405.0, 4393.0, 4404.0)  # 5: bullish BOS of 4401 -> uptrend


def gold_replay(*ohlc) -> Replay:
    return Replay(build_series(list(ohlc), symbol="XAUUSD"))


def split(traces):
    annotations = [t for t in traces if isinstance(t, go.layout.Annotation)]
    by_name = {}
    for t in traces:
        if not isinstance(t, go.layout.Annotation):
            by_name.setdefault(t.name, []).append(t)
    return by_name, annotations


def test_bos_is_in_the_dropdown():
    assert OVERLAYS["bos"].label == "BOS + trend"


def test_red_line_from_swing_wick_to_breaking_candle_with_label_and_hover_dot():
    replay = gold_replay(GREEN, RED, GREEN2, BREAK_DOWN)
    traces, messages = chart_overlays(replay, ["bos"], cursor=3, first_x=0)
    assert messages == []
    by_name, _ = split(traces)
    line, dot = by_name["BOS"]
    (label,) = by_name["BOS label"]
    assert list(line.x) == [2, 3, None] and list(line.y) == [4389.0, 4389.0, None]
    assert line.line.color == DEFAULT_CONFIG.bos_color == "#f23645"
    assert list(label.text) == ["BOS"] and list(label.textposition) == ["bottom center"]
    assert list(dot.x) == [3] and list(dot.y) == [4389.0]
    assert "Bearish BOS 4389.000" in dot.text[0]
    assert "first BOS: downtrend" in dot.text[0]


def test_hover_shows_a_flip():
    replay = gold_replay(GREEN, RED, GREEN2, BREAK_DOWN, GREEN3, BREAK_UP)
    traces, _ = chart_overlays(replay, ["bos"], cursor=5, first_x=0)
    by_name, _ = split(traces)
    _, dot = by_name["BOS"]
    assert list(dot.x) == [3, 5]
    assert "trend: down → up (flip)" in dot.text[1]
    assert list(by_name["BOS label"][0].textposition) == ["bottom center", "top center"]


def test_trend_badge_follows_the_cursor():
    replay = gold_replay(GREEN, RED, GREEN2, BREAK_DOWN, GREEN3, BREAK_UP)
    texts = []
    for cursor in (2, 3, 5):
        _, (badge,) = split(chart_overlays(replay, ["bos"], cursor=cursor, first_x=0)[0])
        texts.append(badge.text)
    assert texts[0] == "M5 trend: none (no BOS yet)"
    assert texts[1].startswith("M5 trend: DOWN · since bearish BOS, candle closed")
    assert texts[2].startswith("M5 trend: UP · since bullish BOS")


def test_badge_keeps_the_trend_from_a_bos_before_the_replay_window():
    replay = gold_replay(GREEN, RED, GREEN2, BREAK_DOWN, GREEN3)
    traces, _ = chart_overlays(replay, ["bos"], cursor=4, first_x=4)
    by_name, (badge,) = split(traces)
    assert by_name == {}  # the BOS itself is outside the window
    assert badge.text.startswith("M5 trend: DOWN")


def test_replay_cursor_hides_bos_not_yet_closed():
    replay = gold_replay(GREEN, RED, GREEN2, BREAK_DOWN)
    by_name, _ = split(chart_overlays(replay, ["bos"], cursor=2, first_x=0)[0])
    assert by_name == {}


def test_badge_is_drawn_as_a_layout_annotation():
    replay = gold_replay(GREEN, RED, GREEN2, BREAK_DOWN)
    state = {"on": True, "picking": False, "playing": False, "start": None}
    figure, _, _ = replay_chart(
        replay, {**state, "now": replay.close_time(3).isoformat()}, overlay_keys=["bos"]
    )
    assert any(a.text.startswith("M5 trend: DOWN") for a in figure.layout.annotations)
    assert all(not isinstance(t, go.layout.Annotation) for t in figure.data)


def test_symbol_without_doji_threshold_shows_a_message():
    replay = Replay(build_series([GREEN, RED], symbol="EURUSD"))
    traces, messages = chart_overlays(replay, ["bos"], cursor=1, first_x=0)
    assert traces == []
    assert messages[0].startswith("BOS + trend: no doji threshold for EURUSD")


# --- overall trend (confluences.md › Trend: the 4H by default, a setting) --------------

FLAT = (4400.0, 4400.0, 4400.0, 4400.0)  # dojis: no swings, no BOS on the M5 chart


def with_overall(overall_ohlc, start=None) -> Replay:
    kwargs = {"start": start} if start else {}
    h1 = build_series(overall_ohlc, Timeframe.H1, symbol="XAUUSD", **kwargs)
    return Replay(build_series([FLAT] * 60, symbol="XAUUSD"), overall=h1)


def badges(replay, cursor, first_x=0):
    _, annotations = split(chart_overlays(replay, ["bos"], cursor, first_x)[0])
    return [a.text for a in annotations]


def test_overall_trend_badge_comes_first_and_changes_only_when_its_candle_closed():
    # H1 bearish BOS on the 03:00 H1 candle, which closes at 04:00 = close of M5 candle 47
    replay = with_overall([GREEN, RED, GREEN2, BREAK_DOWN])
    before, after = badges(replay, 46), badges(replay, 47)
    assert before == ["Overall trend (H1): none (no BOS yet)", "M5 trend: none (no BOS yet)"]
    assert after[0] == (
        "Overall trend (H1): DOWN · since bearish BOS, H1 candle closed 2026-01-05 04:00 UTC"
    )
    assert after[1] == "M5 trend: none (no BOS yet)"


def test_overall_trend_from_warm_up_history_before_the_chart_range():
    # the H1 series starts a day before the M5 chart: its BOS is known at the first candle
    start = datetime(2026, 1, 4, 0, 0, tzinfo=UTC)
    replay = with_overall([GREEN, RED, GREEN2, BREAK_DOWN], start=start)
    assert badges(replay, 0)[0].startswith("Overall trend (H1): DOWN")
    (change,) = detect_overall_trend(replay)
    assert change.confirmed_index == 0 and change.change.confirmed_at.day == 4


def test_overall_trend_matches_a_run_on_the_overall_series_alone():
    replay = with_overall([GREEN, RED, GREEN2, BREAK_DOWN, GREEN3, BREAK_UP])
    changes = detect_overall_trend(replay)
    assert [(c.change.trend, c.confirmed_index) for c in changes] == [
        (Trend.DOWN, 47),  # H1 candle 3 closes 04:00
    ]  # H1 candle 5 (the flip) closes 06:00, after the last M5 candle (04:55)


def test_overall_badge_color_follows_the_overall_trend():
    replay = with_overall([GREEN, RED, GREEN2, BREAK_DOWN])
    _, (overall, _) = split(chart_overlays(replay, ["bos"], 47, 0)[0])
    assert overall.bgcolor == DEFAULT_CONFIG.trend_down_color


def test_warmup_start_stops_at_the_first_missing_day_or_the_limit():
    days = {date(2026, 9, d) for d in (1, 2, 4, 5, 6, 7)}
    assert warmup_start(days, date(2026, 9, 7), 60) == date(2026, 9, 4)  # 09-03 missing
    assert warmup_start(days, date(2026, 9, 7), 2) == date(2026, 9, 5)
    assert warmup_start(days, date(2026, 9, 1), 60) == date(2026, 9, 1)


def test_default_overall_timeframe_is_4h_and_can_be_changed():
    assert TrendConfig().overall_timeframe is Timeframe.H4
    assert DEFAULT_CONFIG.trend.overall_timeframe is Timeframe.H4
    h1 = ChartConfig(trend=TrendConfig(overall_timeframe=Timeframe.H1))
    assert h1.trend.overall_timeframe is Timeframe.H1
