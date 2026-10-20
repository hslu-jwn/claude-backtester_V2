"""BOS + trend overlay on the chart. Spec: ROADMAP.md › 2.3."""

from __future__ import annotations

from datetime import UTC, date, datetime

from conftest import build_series
from overlay_helpers import by_layer, chart_overlays, hovers, lines, points

from backtester.core.models import Timeframe
from backtester.detectors.trend import Trend, TrendConfig
from backtester.engine.replay import Replay
from backtester.ui.bos_overlay import detect_overall_trend
from backtester.ui.chart_config import DEFAULT_CONFIG, ChartConfig
from backtester.ui.chart_data import ChartData
from backtester.ui.drawing import Badge, Label, Marker
from backtester.ui.overlays import DEFAULT_SETTINGS, OVERLAYS
from backtester.ui.pages.chart import _cached_events, warmup_start

# swing high 4410 (wick on candle 0, confirmed 1), swing low 4389 (candle 2, confirmed 2)
GREEN = (4400.0, 4410.0, 4399.0, 4405.0)
RED = (4405.0, 4407.0, 4390.0, 4391.0)
GREEN2 = (4391.0, 4400.0, 4389.0, 4399.0)
BREAK_DOWN = (4399.0, 4401.0, 4380.0, 4381.0)  # 3: bearish BOS of 4389, confirms high 4401
GREEN3 = (4381.0, 4395.0, 4379.0, 4394.0)  # 4: swing low 4379
BREAK_UP = (4394.0, 4405.0, 4393.0, 4404.0)  # 5: bullish BOS of 4401 -> uptrend


def gold_replay(*ohlc) -> Replay:
    return Replay(build_series(list(ohlc), symbol="XAUUSD"))


def split(drawings):
    """(drawings per layer without the badges, badges)."""
    badges = [d for d in drawings if isinstance(d, Badge)]
    return by_layer(d for d in drawings if not isinstance(d, Badge)), badges


def test_bos_is_in_the_dropdown():
    assert OVERLAYS["bos"].label == "BOS + trend"


def test_red_line_from_swing_wick_to_breaking_candle_with_label_and_hover_dot():
    replay = gold_replay(GREEN, RED, GREEN2, BREAK_DOWN)
    drawings, messages = chart_overlays(replay, ["bos"], cursor=3, first_x=0)
    assert messages == []
    layers, _ = split(drawings)
    assert lines(layers["BOS"]) == [(2, 3, 4389.0, 4389.0)]
    assert layers["BOS"][0].color == DEFAULT_CONFIG.bos_color == "#f23645"
    [label] = layers["BOS label"]
    assert isinstance(label, Label) and (label.text, label.anchor) == ("BOS", "bottom center")
    assert points(layers["BOS"]) == [(3, 4389.0)]  # the dot on the breaking candle
    [text] = hovers(layers["BOS"])
    assert "Bearish BOS 4389.000" in text
    assert "first BOS: downtrend" in text


def test_hover_shows_a_flip():
    replay = gold_replay(GREEN, RED, GREEN2, BREAK_DOWN, GREEN3, BREAK_UP)
    drawings, _ = chart_overlays(replay, ["bos"], cursor=5, first_x=0)
    layers, _ = split(drawings)
    assert [x for x, _ in points(layers["BOS"])] == [3, 5]
    assert "trend: down → up (flip)" in hovers(layers["BOS"])[1]
    assert [lb.anchor for lb in layers["BOS label"]] == ["bottom center", "top center"]


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
    drawings, _ = chart_overlays(replay, ["bos"], cursor=4, first_x=4)
    layers, (badge,) = split(drawings)
    assert layers == {}  # the BOS itself is outside the window
    assert badge.text.startswith("M5 trend: DOWN")


def test_replay_cursor_hides_bos_not_yet_closed():
    replay = gold_replay(GREEN, RED, GREEN2, BREAK_DOWN)
    layers, _ = split(chart_overlays(replay, ["bos"], cursor=2, first_x=0)[0])
    assert layers == {}


def test_badges_go_to_the_browser_separately_from_the_drawings():
    replay = gold_replay(GREEN, RED, GREEN2, BREAK_DOWN)
    data = ChartData(replay, lambda o: _cached_events(replay, o, DEFAULT_SETTINGS, None))
    payload = data.full(["bos"], 3)
    [badge] = payload["badges"]["bos"]
    assert (
        badge["t"].startswith("M5 trend: DOWN") and badge["bg"] == DEFAULT_CONFIG.trend_down_color
    )
    assert all(d["k"] != "badge" for d in payload["types"]["bos"])
    assert any(isinstance(d, Marker) for d in data.drawn("bos", 3).groups[0])


def test_symbol_without_doji_threshold_shows_a_message():
    replay = Replay(build_series([GREEN, RED], symbol="FOOBAR"))
    drawings, messages = chart_overlays(replay, ["bos"], cursor=1, first_x=0)
    assert drawings == []
    assert messages[0].startswith("BOS + trend: no doji threshold for FOOBAR")


# --- overall trend (confluences.md › Trend: the 4H by default, a setting) --------------

FLAT = (4400.0, 4400.0, 4400.0, 4400.0)  # dojis: no swings, no BOS on the M5 chart


def with_overall(overall_ohlc, start=None) -> Replay:
    kwargs = {"start": start} if start else {}
    h1 = build_series(overall_ohlc, Timeframe.H1, symbol="XAUUSD", **kwargs)
    return Replay(build_series([FLAT] * 60, symbol="XAUUSD"), overall=h1)


def badges(replay, cursor, first_x=0):
    _, found = split(chart_overlays(replay, ["bos"], cursor, first_x)[0])
    return [b.text for b in found]


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
    assert overall.background == DEFAULT_CONFIG.trend_down_color
    assert overall.row == 0


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
