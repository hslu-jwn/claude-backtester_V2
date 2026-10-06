"""Chart replay without a browser: stepping, start candle, timeframe switch, and that
nothing after the cursor reaches the figure. Spec: ROADMAP.md › 1.2."""

from __future__ import annotations

from datetime import date

import pytest
from m1_frames import m1

from backtester.data.dukascopy import cache_path
from backtester.data.sources import SymbolSources
from backtester.ui.chart_figure import DEFAULT_CONFIG, ChartConfig
from backtester.ui.pages.chart import (
    REPLAY_OFF,
    load_replay,
    replay_chart,
    replay_step,
    visible_axes,
)

SPIKE = 200.0  # high of the 11:00 candle on 09-02: must never show before it closes


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


def test_toggle_asks_for_a_start_and_defaults_to_the_first_candle_of_the_last_day(cache):
    replay = replay_of(cache)
    state = replay_step("toggle", REPLAY_OFF, replay)
    assert state["on"] and state["picking"]
    assert state["now"] == state["start"] == "2026-09-02T09:05:00Z"  # close of 09:00 candle
    assert replay_step("toggle", state, replay) == REPLAY_OFF


def test_only_candles_up_to_the_cursor_are_drawn(cache):
    replay, state = started(cache)
    fig, message, store = replay_chart(replay, state)
    assert list(fig.data[0].x) == list(range(13))  # cursor 12 -> candles 0..12
    assert store["ts"][-1] == "2026-09-02T09:00:00Z"
    assert "candle 13 of 48" in message and "closed at 09:05" in message


def test_forward_adds_exactly_one_candle_and_back_removes_it(cache):
    replay, state = started(cache)
    fwd = replay_step("forward", state, replay)
    assert len(replay_chart(replay, fwd)[0].data[0].x) == 14
    assert replay_step("back", fwd, replay)["now"] == state["now"]


def test_future_spike_is_not_in_the_figure_or_its_axes_until_it_closes(cache):
    replay, state = started(cache)
    # step to the 10:55 candle (cursor 35): the 11:00 spike candle is still in the future
    for _ in range(35 - 12):
        state = replay_step("forward", state, replay)
    fig, _, store = replay_chart(replay, state)
    assert max(fig.data[0].high) < SPIKE and max(store["high"]) < SPIKE
    assert fig.layout.yaxis.range[1] < SPIKE
    _, _, yrange = visible_axes({"xaxis.range": [0, 60]}, store)  # pan into the future
    assert yrange[1] < SPIKE
    state = replay_step("forward", state, replay)
    assert max(replay_chart(replay, state)[0].data[0].high) == SPIKE


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
    _, _, store = replay_chart(h1, replay_step("data", state, h1))
    # H1 candles closed by 10:40: 09-01 09:00 and 09-02 09:00; 10:00 is still forming
    assert store["ts"] == ["2026-09-01T09:00:00Z", "2026-09-02T09:00:00Z"]
    state = replay_step("forward", state, h1)
    assert state["now"] == "2026-09-02T11:00:00Z"  # one H1 step


def test_dates_without_the_replay_time_restart_at_the_default(cache):
    replay = replay_of(cache)
    state = replay_step("click", replay_step("toggle", REPLAY_OFF, replay), replay, clicked_x=3)
    day2, _ = load_replay(cache, "XAUUSD", "M5", "2026-09-02", "2026-09-02")
    new = replay_step("data", state, day2)
    assert new["picking"] and new["now"] == "2026-09-02T09:05:00Z"
    assert replay_step("data", new, day2) == new


def test_replay_window_limits_drawn_candles_but_keeps_positions(cache):
    config = ChartConfig(replay_window=5)
    replay = replay_of(cache, config=config)
    state = replay_step("click", replay_step("toggle", REPLAY_OFF, replay), replay, clicked_x=20)
    fig, _, store = replay_chart(replay, state, config)
    assert list(fig.data[0].x) == [16, 17, 18, 19, 20] and store["x0"] == 16
    tickvals, _, _ = visible_axes({"xaxis.range": [17.6, 18.4]}, store)
    assert tickvals == [18]
