"""Session start lines on the chart. Spec: ROADMAP.md › 1.3, strategy-session-zones.md › Sessions.

Summer 2026 starts (UTC): Tokyo 00:00, London 07:00, New York 12:00.
"""

from __future__ import annotations

import pandas as pd

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.data.adapters.cache_adapter import candles_from_frame
from backtester.engine.replay import Replay
from backtester.sessions import Session
from backtester.ui.chart_config import session_line_positions
from backtester.ui.chart_data import ChartData

TOKYO, LONDON, NEW_YORK = Session.TOKYO, Session.LONDON, Session.NEW_YORK


def candles(times: list[pd.Timestamp]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ts": pd.Series(times),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1.0,
            "spread": 0.3,
        }
    )


def hourly(start: str, periods: int) -> pd.DataFrame:
    return candles(list(pd.date_range(start, periods=periods, freq="1h", tz="UTC")))


def lines_sent(frame, timeframe=Timeframe.H1, cursor=None) -> list[list]:
    """Session lines the page sends with candles 0..cursor: (x, color, label)."""
    series = CandleSeries("XAUUSD", timeframe, candles_from_frame(frame))
    data = ChartData(Replay(series), lambda o: [])
    stop = len(series) if cursor is None else cursor + 1
    return data.sessions(0, stop)


def test_lines_go_through_the_candle_opening_at_each_start():
    # Wed 15 Jul 2026, H1 candles 00:00..23:00 at x = 0..23.
    ts = hourly("2026-07-15 00:00", 24)["ts"]
    assert session_line_positions(ts, Timeframe.H1) == [
        (0.0, TOKYO),
        (7.0, LONDON),
        (12.0, NEW_YORK),
    ]


def test_us_and_europe_dst_mismatch_week_moves_london_line():
    # Mon 9 Mar 2026: London 08:00 UTC (GMT), New York 12:00 UTC (EDT).
    ts = hourly("2026-03-09 00:00", 24)["ts"]
    assert session_line_positions(ts, Timeframe.H1) == [
        (0.0, TOKYO),
        (8.0, LONDON),
        (12.0, NEW_YORK),
    ]


def test_positions_follow_first_x():
    ts = hourly("2026-07-15 00:00", 24)["ts"]
    assert [x for x, _ in session_line_positions(ts, Timeframe.H1, first_x=100)] == [
        100.0,
        107.0,
        112.0,
    ]


def test_h4_line_goes_through_the_candle_containing_the_start():
    # H4 candles 00, 04, 08, 12, 16, 20: London 07:00 is in the 04:00 candle (x 1).
    ts = candles(list(pd.date_range("2026-07-15", periods=6, freq="4h", tz="UTC")))["ts"]
    assert session_line_positions(ts, Timeframe.H4) == [
        (0.0, TOKYO),
        (1.0, LONDON),
        (3.0, NEW_YORK),
    ]


def test_sunday_open_gets_no_line_and_tokyo_line_follows():
    # Sun 1 Mar 2026: market opens 22:00 UTC (17:00 EST), Tokyo at 00:00 UTC (19:00 EST).
    ts = hourly("2026-03-01 22:00", 4)["ts"]  # 22:00, 23:00, 00:00, 01:00
    assert session_line_positions(ts, Timeframe.H1) == [(2.0, TOKYO)]


def test_start_inside_a_gap_goes_to_the_next_candle_of_the_session():
    # Gold daily break style gap over the London start (07:00): candles 05:00, 06:00, 09:00.
    ts = candles(
        [
            pd.Timestamp(t, tz="UTC")
            for t in ("2026-07-15 05:00", "2026-07-15 06:00", "2026-07-15 09:00")
        ]
    )["ts"]
    assert session_line_positions(ts, Timeframe.H1) == [(2.0, LONDON)]


def test_session_without_candles_gets_no_line():
    # Candles on Friday NY and then Monday London: Monday's Tokyo session had none.
    ts = candles([pd.Timestamp(t, tz="UTC") for t in ("2026-07-17 20:00", "2026-07-20 07:00")])[
        "ts"
    ]
    assert session_line_positions(ts, Timeframe.H1) == [(1.0, LONDON)]


def test_lines_have_session_colors_and_labels():
    lines = lines_sent(hourly("2026-07-15 00:00", 24))
    assert [color for _, color, _ in lines] == ["#f5c518", "#2962ff", "#f23645"]  # Y, B, R
    assert [label for _, _, label in lines] == ["Tokyo", "London", "NY"]


def test_no_lines_on_daily_candles():
    frame = candles(list(pd.date_range("2026-07-13", periods=5, freq="1D", tz="UTC")))
    assert lines_sent(frame, Timeframe.D1) == []


def test_replay_sends_no_line_past_the_cursor():
    frame = hourly("2026-07-15 00:00", 24)
    assert [x for x, _, _ in lines_sent(frame, cursor=10)] == [0, 7]  # NY (12) not yet
    assert [x for x, _, _ in lines_sent(frame, cursor=11)] == [0, 7]  # NY opens next
    assert [x for x, _, _ in lines_sent(frame, cursor=12)] == [0, 7, 12]  # NY's candle
