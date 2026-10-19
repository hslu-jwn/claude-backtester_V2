"""Load candles while scrolling (user, 2026-10-19): the days to add when the view comes near
the left / right edge of the loaded candles. Spec: ROADMAP.md › 4.0b (chart page)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

from backtester.core.models import Timeframe
from backtester.ui.chart_config import DEFAULT_CONFIG
from backtester.ui.pages.chart import estimated_candles, extend_dates

D = date(2026, 1, 1)
CACHED = [D + timedelta(days=i) for i in range(200)]  # 01-01 .. 07-19
# 288 M5 candles a day: a chunk of 2880 is 10 days
CONFIG = replace(DEFAULT_CONFIG, extend_candles=2880, max_candles=20_000)
M5 = Timeframe.M5


def day(n: int) -> date:
    return D + timedelta(days=n)


def test_left_edge_adds_a_chunk_of_days_before_the_start():
    assert extend_dates(CACHED, day(50), day(80), "left", M5, config=CONFIG) == (day(40), day(80))


def test_right_edge_adds_a_chunk_of_days_after_the_end():
    assert extend_dates(CACHED, day(50), day(80), "right", M5, config=CONFIG) == (day(50), day(90))


def test_chunk_size_follows_the_timeframe():
    h1 = extend_dates(CACHED, day(150), day(160), "left", Timeframe.H1, config=CONFIG)
    assert h1 == (day(30), day(160))  # 2880 hours = 120 days


def test_it_stops_at_the_start_of_the_cache_and_then_gives_nothing_more():
    assert extend_dates(CACHED, day(3), day(20), "left", M5, config=CONFIG) == (day(0), day(20))
    assert extend_dates(CACHED, day(0), day(20), "left", M5, config=CONFIG) is None


def test_it_stops_at_the_end_of_the_cache():
    assert extend_dates(CACHED, day(150), day(195), "right", M5, config=CONFIG) == (
        day(150),
        day(199),
    )
    assert extend_dates(CACHED, day(150), day(199), "right", M5, config=CONFIG) is None


def test_it_does_not_cross_a_hole_in_the_cache():
    cached = [d for d in CACHED if d != day(45)]
    assert extend_dates(cached, day(50), day(60), "left", M5, config=CONFIG) == (day(46), day(60))
    assert extend_dates(cached, day(46), day(60), "left", M5, config=CONFIG) is None
    assert extend_dates(cached, day(30), day(40), "right", M5, config=CONFIG) == (
        day(30),
        day(44),
    )


def test_shown_days_that_are_not_cached_give_nothing():
    assert extend_dates(CACHED, day(300), day(310), "left", M5, config=CONFIG) is None
    assert extend_dates([], day(1), day(2), "left", M5, config=CONFIG) is None


def test_over_the_candle_limit_the_far_side_is_dropped():
    config = replace(CONFIG, max_candles=288 * 25)  # 25 days of 5m
    first, last = extend_dates(CACHED, day(50), day(70), "left", M5, config=config)
    assert first == day(40) and last == day(64)  # 25 days; the right end made room
    assert estimated_candles(first, last, M5) <= config.max_candles
    first, last = extend_dates(CACHED, day(50), day(70), "right", M5, config=config)
    assert last == day(80) and first == day(56)


def test_the_far_side_is_not_dropped_below_what_the_view_shows():
    config = replace(CONFIG, max_candles=288 * 25)
    at = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=65)
    view = {"center": at.timestamp(), "count": 2880}  # 10 days of 5m: day 60 .. 70
    # day 40..70 would be 31 days: the view needs the right end, so the left chunk is cut
    assert extend_dates(CACHED, day(50), day(70), "left", M5, view, config) == (day(46), day(70))
    # without a view limit the right end is dropped instead
    assert extend_dates(CACHED, day(50), day(70), "left", M5, config=config) == (day(40), day(64))
    # already at the limit and the view needs everything: nothing to add
    assert extend_dates(CACHED, day(46), day(70), "left", M5, view, config) is None
    wide = {"center": at.timestamp(), "count": 288 * 24}
    assert extend_dates(CACHED, day(46), day(70), "left", M5, wide, config) is None
