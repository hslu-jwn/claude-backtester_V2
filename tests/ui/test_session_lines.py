"""Session start lines on the chart. Spec: ROADMAP.md › 1.3, strategy-session-zones.md › Sessions.

Summer 2026 starts (UTC): Tokyo 00:00, London 07:00, New York 12:00.
"""

from __future__ import annotations

import pandas as pd

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.data.adapters.cache_adapter import candles_from_frame
from backtester.sessions import Session
from backtester.ui.chart_figure import (
    DEFAULT_CONFIG,
    build_candle_figure,
    session_line_positions,
)
from backtester.ui.pages.chart import replay_figure

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


def line_colors(fig) -> list[str]:
    return [shape.line.color for shape in fig.layout.shapes]


def test_lines_sit_on_the_left_edge_of_the_candle_opening_at_each_start():
    # Wed 15 Jul 2026, H1 candles 00:00..23:00 at x = 0..23.
    ts = hourly("2026-07-15 00:00", 24)["ts"]
    assert session_line_positions(ts, Timeframe.H1) == [
        (-0.5, TOKYO),
        (6.5, LONDON),
        (11.5, NEW_YORK),
    ]


def test_us_and_europe_dst_mismatch_week_moves_london_line():
    # Mon 9 Mar 2026: London 08:00 UTC (GMT), New York 12:00 UTC (EDT).
    ts = hourly("2026-03-09 00:00", 24)["ts"]
    assert session_line_positions(ts, Timeframe.H1) == [
        (-0.5, TOKYO),
        (7.5, LONDON),
        (11.5, NEW_YORK),
    ]


def test_positions_follow_first_x():
    ts = hourly("2026-07-15 00:00", 24)["ts"]
    assert [x for x, _ in session_line_positions(ts, Timeframe.H1, first_x=100)] == [
        99.5,
        106.5,
        111.5,
    ]


def test_h4_line_is_placed_inside_the_candle_containing_the_start():
    # H4 candles 00, 04, 08, 12, 16, 20: London 07:00 is 3/4 into the 04:00 candle (x 0.5..1.5).
    ts = candles(list(pd.date_range("2026-07-15", periods=6, freq="4h", tz="UTC")))["ts"]
    assert session_line_positions(ts, Timeframe.H4) == [
        (-0.5, TOKYO),
        (0.5 + 0.75, LONDON),
        (2.5, NEW_YORK),
    ]


def test_sunday_open_gets_no_line_and_tokyo_line_follows():
    # Sun 1 Mar 2026: market opens 22:00 UTC (17:00 EST), Tokyo at 00:00 UTC (19:00 EST).
    ts = hourly("2026-03-01 22:00", 4)["ts"]  # 22:00, 23:00, 00:00, 01:00
    assert session_line_positions(ts, Timeframe.H1) == [(1.5, TOKYO)]


def test_start_inside_a_gap_goes_to_the_next_candle_of_the_session():
    # Gold daily break style gap over the London start (07:00): candles 05:00, 06:00, 09:00.
    ts = candles(
        [
            pd.Timestamp(t, tz="UTC")
            for t in ("2026-07-15 05:00", "2026-07-15 06:00", "2026-07-15 09:00")
        ]
    )["ts"]
    assert session_line_positions(ts, Timeframe.H1) == [(1.5, LONDON)]


def test_session_without_candles_gets_no_line():
    # Candles on Friday NY and then Monday London: Monday's Tokyo session had none.
    ts = candles([pd.Timestamp(t, tz="UTC") for t in ("2026-07-17 20:00", "2026-07-20 07:00")])[
        "ts"
    ]
    assert session_line_positions(ts, Timeframe.H1) == [(0.5, LONDON)]


def test_lines_have_session_colors_and_labels():
    fig = build_candle_figure(hourly("2026-07-15 00:00", 24), "XAUUSD", Timeframe.H1)
    assert line_colors(fig) == ["#f5c518", "#2962ff", "#f23645"]  # yellow, blue, red
    assert [a.text for a in fig.layout.annotations] == ["Tokyo", "London", "NY"]
    assert all(s.yref == "paper" and (s.y0, s.y1) == (0, 1) for s in fig.layout.shapes)


def test_one_switch_hides_all_session_lines():
    frame = hourly("2026-07-15 00:00", 24)
    fig = build_candle_figure(frame, "XAUUSD", Timeframe.H1, show_sessions=False)
    assert fig.layout.shapes == () and fig.layout.annotations == ()
    series = CandleSeries("XAUUSD", Timeframe.H1, candles_from_frame(frame))
    fig, _ = replay_figure(series.view(23), DEFAULT_CONFIG, show_sessions=False)
    assert fig.layout.shapes == ()


def test_no_lines_on_daily_candles():
    frame = candles(list(pd.date_range("2026-07-13", periods=5, freq="1D", tz="UTC")))
    assert build_candle_figure(frame, "XAUUSD", Timeframe.D1).layout.shapes == ()


def test_replay_draws_no_line_past_the_cursor():
    frame = hourly("2026-07-15 00:00", 24)
    series = CandleSeries("XAUUSD", Timeframe.H1, candles_from_frame(frame))
    fig, _ = replay_figure(series.view(10), DEFAULT_CONFIG)  # cursor at the 10:00 candle
    assert [s.x0 for s in fig.layout.shapes] == [-0.5, 6.5]  # NY (11.5) not yet
    fig, _ = replay_figure(series.view(11), DEFAULT_CONFIG)  # 11:00 candle: NY opens next
    assert [s.x0 for s in fig.layout.shapes] == [-0.5, 6.5]
    fig, _ = replay_figure(series.view(12), DEFAULT_CONFIG)
    assert [s.x0 for s in fig.layout.shapes] == [-0.5, 6.5, 11.5]
