"""Chart replay without a browser: stepping, start candle, timeframe switch, and that
nothing after the cursor is sent to the browser. Spec: ROADMAP.md › 1.2, 4.0a part 4."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from m1_frames import m1

from backtester.core.models import Timeframe
from backtester.data.dukascopy import cache_path
from backtester.data.sources import SymbolSources
from backtester.detectors.trend import TrendConfig
from backtester.ui.chart_config import DEFAULT_CONFIG, ChartConfig
from backtester.ui.pages.chart import (
    REPLAY_OFF,
    base_payload,
    default_span,
    load_replay,
    replay_delta,
    replay_step,
    span_candles,
)

SPIKE = 200.0  # high of the 11:00 candle on 09-02: must never show before it closes


def utc(text: str) -> int:
    return int(datetime.fromisoformat(text).replace(tzinfo=UTC).timestamp())


def rows(day: str, start_hour: int, hours: int):
    out = []
    for i in range(hours * 12):
        h, m = divmod(start_hour * 60 + 5 * i, 60)
        hhmm = f"{h:02d}:{m:02d}"
        high = SPIKE if (day, hhmm) == ("2026-09-02", "11:00") else 101.0
        out.append((hhmm, 100.0, high, 99.0, 100.5, 1.0, 0.2))
    return m1(*out, day=day)


@pytest.fixture
def cache(tmp_path):
    """09-01: M5 candles 09:00-09:55 (12). 09-02: 09:00-11:55 (36), spike at 11:00."""
    for day, frame in [
        ("2026-09-01", rows("2026-09-01", 9, 1)),
        ("2026-09-02", rows("2026-09-02", 9, 3)),
    ]:
        path = cache_path(tmp_path, "XAUUSD", date.fromisoformat(day))
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(path, index=False)
    return SymbolSources({"XAUUSD": tmp_path})


def replay_of(cache, timeframe="M5", config=DEFAULT_CONFIG):
    replay, _ = load_replay(cache, "XAUUSD", timeframe, "2026-09-01", "2026-09-02", config)
    return replay


def started(cache):
    """Replay switched on and started at the default candle (09-02 09:00, cursor 12)."""
    replay = replay_of(cache)
    state = replay_step("toggle", REPLAY_OFF, replay)
    return replay, replay_step("play", replay_step("play", state, replay), replay)


def payload_at(replay_state, timeframe="M5", cache=None, span=None):
    payload, message = base_payload(
        cache, "XAUUSD", timeframe, "2026-09-01", "2026-09-02", replay_state, span
    )
    return payload, message


def view_of(payload, types=()):
    return {"key": payload["key"], "cursor": payload["cursor"], "types": list(types)}


def step_delta(cache, replay, payload, new_state):
    cursor = replay.cursor_at(datetime.fromisoformat(new_state["now"]))
    return replay_delta(cache, view_of(payload), replay, cursor, payload["key"], [])


def test_toggle_asks_for_a_start_and_defaults_to_the_first_candle_of_the_last_day(cache):
    replay = replay_of(cache)
    state = replay_step("toggle", REPLAY_OFF, replay)
    assert state["on"] and state["picking"]
    assert state["now"] == state["start"] == "2026-09-02T09:05:00Z"  # close of 09:00 candle
    assert replay_step("toggle", state, replay) == REPLAY_OFF
    payload, message = payload_at(state, cache=cache)  # picking: the whole range to click in
    assert payload["picking"] and payload["cursor"] == len(replay) - 1
    assert "click the candle" in message


def test_only_candles_up_to_the_cursor_are_sent(cache):
    _, state = started(cache)
    payload, message = payload_at(state, cache=cache)
    assert payload["cursor"] == 12 and len(payload["candles"]["t"]) == 13  # candles 0..12
    assert payload["candles"]["t"][-1] == utc("2026-09-02 09:00")
    assert "candle 13 of 48" in message and "closed at 09:05" in message


def test_forward_sends_exactly_one_candle_and_back_drops_it(cache):
    replay, state = started(cache)
    payload, _ = payload_at(state, cache=cache)
    fwd = replay_step("forward", state, replay)
    delta = step_delta(cache, replay, payload, fwd)
    assert (delta["from"], delta["to"]) == (12, 13)
    assert delta["candles"]["t"] == [utc("2026-09-02 09:05")] and delta["candles"]["x0"] == 13
    back = replay_step("back", fwd, replay)
    assert back["now"] == state["now"]
    moved = {**view_of(payload), "cursor": 13}
    delta = replay_delta(cache, moved, replay, 12, payload["key"], [])
    assert delta["drop"] == 1 and "candles" not in delta


def test_future_spike_is_never_sent_until_it_closes(cache):
    replay, state = started(cache)
    payload, _ = payload_at(state, cache=cache)
    view = view_of(payload)
    seen = list(payload["candles"]["h"])
    # step to the 10:55 candle (cursor 35): the 11:00 spike candle is still in the future
    for _ in range(35 - 12):
        state = replay_step("forward", state, replay)
        delta = step_delta(cache, replay, {**payload, "cursor": view["cursor"]}, state)
        view["cursor"] = delta["to"]
        seen += delta["candles"]["h"]
    assert view["cursor"] == 35 and max(seen) < SPIKE
    assert max(payload_at(state, cache=cache)[0]["candles"]["h"]) < SPIKE
    state = replay_step("forward", state, replay)
    delta = step_delta(cache, replay, {**payload, "cursor": 35}, state)
    assert delta["candles"]["h"] == [SPIKE]


def test_a_delta_for_other_candles_is_not_built(cache):
    replay, state = started(cache)
    payload, _ = payload_at(state, cache=cache)
    stale = {**view_of(payload), "key": "XAUUSD|H1|2026-09-01|2026-09-02"}
    assert replay_delta(cache, stale, replay, 13, payload["key"], []) is None
    assert replay_delta(cache, None, replay, 13, payload["key"], []) is None


def test_back_stops_at_the_first_candle_and_forward_at_the_last(cache):
    replay = replay_of(cache)
    state = replay_step("click", replay_step("toggle", REPLAY_OFF, replay), replay, clicked_x=0)
    assert replay_step("back", state, replay)["now"] == state["now"]
    state = replay_step("click", state, replay, clicked_x=47)
    assert replay_step("forward", state, replay)["now"] == state["now"]


def test_autoplay_steps_on_ticks_and_stops_at_the_last_candle(cache):
    replay = replay_of(cache)
    state = replay_step("click", replay_step("toggle", REPLAY_OFF, replay), replay, clicked_x=45)
    state = replay_step("play", state, replay)
    assert state["playing"]
    state = replay_step("tick", state, replay)
    assert state["playing"] and state["now"] == "2026-09-02T11:55:00Z"
    state = replay_step("tick", state, replay)  # reaches the last candle
    assert not state["playing"] and state["now"] == "2026-09-02T12:00:00Z"
    assert replay_step("tick", state, replay) == state  # stale tick: nothing


def test_click_sets_the_start_and_start_button_returns_to_it(cache):
    replay = replay_of(cache)
    state = replay_step("click", replay_step("toggle", REPLAY_OFF, replay), replay, clicked_x=20)
    assert not state["picking"] and state["start"] == state["now"] == "2026-09-02T09:45:00Z"
    moved = replay_step("forward", replay_step("forward", state, replay), replay)
    assert replay_step("start", moved, replay)["now"] == state["start"]


def test_switching_timeframe_keeps_the_replay_time_and_steps_on_that_timeframe(cache):
    m5 = replay_of(cache)
    state = replay_step("click", replay_step("toggle", REPLAY_OFF, m5), m5, clicked_x=31)
    assert state["now"] == "2026-09-02T10:40:00Z"  # 10:35 M5 candle closed
    h1 = replay_of(cache, "H1")
    payload, _ = payload_at(replay_step("data", state, h1), "H1", cache)
    # H1 candles closed by 10:40: 09-01 09:00 and 09-02 09:00; 10:00 is still forming
    assert payload["candles"]["t"] == [utc("2026-09-01 09:00"), utc("2026-09-02 09:00")]
    state = replay_step("forward", state, h1)
    assert state["now"] == "2026-09-02T11:00:00Z"  # one H1 step


def test_dates_without_the_replay_time_restart_at_the_default(cache):
    replay = replay_of(cache)
    state = replay_step("click", replay_step("toggle", REPLAY_OFF, replay), replay, clicked_x=3)
    day2, _ = load_replay(cache, "XAUUSD", "M5", "2026-09-02", "2026-09-02")
    new = replay_step("data", state, day2)
    assert new["picking"] and new["now"] == "2026-09-02T09:05:00Z"
    assert replay_step("data", new, day2) == new


def test_overall_trend_series_has_warm_up_days_and_no_unclosed_candle(cache):
    # chart 09-02 only; the overall series also has 09-01 (warm-up, cached day before)
    config = ChartConfig(trend=TrendConfig(overall_timeframe=Timeframe.H1))
    replay, _ = load_replay(cache, "XAUUSD", "M5", "2026-09-02", "2026-09-02", config)
    assert replay.overall_timeframe is Timeframe.H1
    first = replay.overall_view(0)
    assert first[0].ts.day == 1 and first.current.ts.hour == 9  # 09-01 09:00 H1 candle
    for cursor in range(len(replay) - 1):
        # the 11:00 H1 candle (with the spike) closes at 12:00, the last M5 candle's close
        assert max(c.high for c in replay.overall_view(cursor)) < SPIKE
    assert replay.overall_view(len(replay) - 1).current.high == SPIKE
    default, _ = load_replay(cache, "XAUUSD", "M5", "2026-09-02", "2026-09-02")
    assert default.overall_timeframe is Timeframe.H4


def test_switching_timeframe_keeps_the_visible_time_span_with_smaller_candles(cache):
    m5 = replay_of(cache)
    state = replay_step("click", replay_step("toggle", REPLAY_OFF, m5), m5, clicked_x=31)
    span = default_span(Timeframe.M5)  # set when replay is switched on, on M5
    assert span == {"left": 600, "right": 50}  # 120 candles / 10 slots of 5 minutes
    p5, _ = payload_at(state, "M5", cache, span)
    m1 = replay_of(cache, "M1")
    p1, _ = payload_at(replay_step("data", state, m1), "M1", cache, span)
    # same minutes left and right of the cursor; on M1 that is 5x as many candles
    r5, r1 = p5["range"], p1["range"]
    assert (p5["cursor"] + 0.5 - r5["from"]) * 5 == (p1["cursor"] + 0.5 - r1["from"]) * 1 == 600
    assert (r5["to"] - p5["cursor"] - 0.5) * 5 == (r1["to"] - p1["cursor"] - 0.5) * 1 == 50
    assert p1["span"] == p5["span"] == span  # the browser keeps it for the next steps
    # same replay time (the fixture has one minute every 5: the 10:35 M1 candle is the last)
    assert p1["candles"]["t"][-1] == utc("2026-09-02 10:35")


def test_span_on_a_high_timeframe_keeps_a_minimum_of_candles():
    left, right = span_candles({"left": 600, "right": 50}, Timeframe.H4)
    assert left == DEFAULT_CONFIG.replay_min_visible and right == 1.0
    left, _ = span_candles({"left": 10_000, "right": 5}, Timeframe.M1)
    assert left == DEFAULT_CONFIG.replay_window
