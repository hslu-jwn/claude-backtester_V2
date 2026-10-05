"""Replay stepping: only closed candles at the cursor, higher timeframes via the clock.
Spec: ROADMAP.md › 1.2, CLAUDE.md › Invariant #1."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from conftest import DEFAULT_START, build_series

from backtester.core.errors import LookaheadError
from backtester.core.models import Timeframe
from backtester.engine.replay import Replay


def flat(n: int, price: float = 1.0) -> list[tuple[float, float, float, float]]:
    return [(price + i, price + i + 0.5, price + i - 0.5, price + i) for i in range(n)]


def test_view_at_cursor_holds_exactly_the_closed_candles():
    replay = Replay(build_series(flat(5)))
    view = replay.view(2)
    assert len(view) == 3 and view.current.open == 3.0
    with pytest.raises(LookaheadError):
        view[3]


def test_now_is_the_close_time_and_cursor_at_inverts_it():
    replay = Replay(build_series(flat(3)))  # M5 candles open 00:00, 00:05, 00:10
    assert replay.close_time(0) == DEFAULT_START + timedelta(minutes=5)
    assert replay.cursor_at(DEFAULT_START + timedelta(minutes=5)) == 0
    assert replay.cursor_at(DEFAULT_START + timedelta(minutes=9)) == 0  # 00:05 still open
    assert replay.cursor_at(DEFAULT_START + timedelta(minutes=10)) == 1
    assert replay.cursor_at(DEFAULT_START + timedelta(minutes=4)) is None
    assert replay.cursor_at(datetime(2030, 1, 1, tzinfo=UTC)) == 2  # after the end: last


def test_h1_candle_appears_only_at_the_close_of_the_55_m5_candle():
    m5 = build_series(flat(24))  # 00:00 .. 01:55
    h1 = build_series(flat(2), Timeframe.H1)  # 00:00, 01:00
    replay = Replay(m5, [h1])
    assert replay.higher_view(10, Timeframe.H1) is None  # 00:50 candle, closes 00:55
    assert replay.higher_view(11, Timeframe.H1).cursor == 0  # 00:55 candle, closes 01:00
    assert replay.higher_view(22, Timeframe.H1).cursor == 0
    assert replay.higher_view(23, Timeframe.H1).cursor == 1


def test_higher_timeframe_must_be_higher_and_same_symbol():
    m5 = build_series(flat(2))
    with pytest.raises(ValueError, match="not higher"):
        Replay(m5, [build_series(flat(2))])
    with pytest.raises(ValueError, match="series in a TEST replay"):
        Replay(m5, [build_series(flat(2), Timeframe.H1, symbol="OTHER")])
    with pytest.raises(KeyError):
        Replay(m5).higher_view(0, Timeframe.H1)


def test_stepping_never_changes_what_was_already_visible():
    """No-lookahead: views at k are a prefix of views at k+1, and appending future
    candles to the history changes nothing visible at earlier cursors."""
    short = Replay(build_series(flat(24)), [build_series(flat(2), Timeframe.H1)])
    longer = Replay(build_series(flat(36)), [build_series(flat(3), Timeframe.H1)])
    for k in range(23):
        assert list(short.view(k)) == list(short.view(k + 1))[: k + 1]
        assert list(short.view(k)) == list(longer.view(k))
        a, b = short.higher_view(k, Timeframe.H1), longer.higher_view(k, Timeframe.H1)
        assert (a is None and b is None) or list(a) == list(b)
