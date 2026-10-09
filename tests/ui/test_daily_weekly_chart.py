"""D and W on the chart: buttons, trading-day labels on the time axis, no session lines,
the day boundary in the chart key. Spec: ROADMAP.md › 4.0b part 2."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from backtester.core.models import Candle, Timeframe
from backtester.core.series import CandleSeries
from backtester.data.resample import DayBoundary
from backtester.engine.replay import Replay
from backtester.ui.chart_config import DEFAULT_CONFIG
from backtester.ui.chart_data import ChartData
from backtester.ui.pages import chart


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def data(timeframe: Timeframe, opens: list[str], boundary=DayBoundary.NEW_YORK_17) -> ChartData:
    candles = [Candle(ts(t), 100, 101, 99, 100.5) for t in opens]
    replay = Replay(CandleSeries("XAUUSD", timeframe, candles))
    return ChartData(replay, lambda o: [], replace(DEFAULT_CONFIG, day_boundary=boundary))


def test_d_and_w_buttons():
    assert chart.TIMEFRAMES[-2:] == ["D1", "W1"]
    assert [chart.timeframe_label(t) for t in ("D1", "W1")] == ["D", "W"]


def test_daily_candles_are_named_by_their_trading_day_weekly_by_the_monday():
    # D: 09-13 21:00 .. 09-14 21:00 UTC is Monday 09-14's trading day
    d = data(Timeframe.D1, ["2026-09-13 21:00", "2026-09-14 21:00"])
    assert d.candles(0, 2)["t"] == [ts("2026-09-14").timestamp(), ts("2026-09-15").timestamp()]
    w = data(Timeframe.W1, ["2026-09-11 21:00"])  # closes Friday 09-18
    assert w.candles(0, 1)["t"] == [ts("2026-09-14").timestamp()]
    utc = data(Timeframe.D1, ["2026-09-14 00:00"], DayBoundary.UTC)
    assert utc.candles(0, 1)["t"] == [ts("2026-09-14").timestamp()]
    m5 = data(Timeframe.M5, ["2026-09-14 12:05"])
    assert m5.candles(0, 1)["t"] == [ts("2026-09-14 12:05").timestamp()]


def test_no_session_lines_on_d_and_w():
    d = data(Timeframe.D1, ["2026-09-13 21:00", "2026-09-14 21:00"])
    assert d.sessions(0, 2) == []


def test_the_day_boundary_is_part_of_the_key_of_d_and_w_only():
    utc = chart.with_boundary(DEFAULT_CONFIG, "UTC")
    assert utc.day_boundary is DayBoundary.UTC
    assert chart.with_boundary(DEFAULT_CONFIG, "nonsense") is DEFAULT_CONFIG
    base = chart.chart_key("XAUUSD", "D1", "2026-09-02", "2026-09-30")
    assert chart.chart_key("XAUUSD", "D1", "2026-09-02", "2026-09-30", utc) == base + "|UTC"
    m5 = chart.chart_key("XAUUSD", "M5", "2026-09-02", "2026-09-30", utc)
    assert m5 == chart.chart_key("XAUUSD", "M5", "2026-09-02", "2026-09-30")
