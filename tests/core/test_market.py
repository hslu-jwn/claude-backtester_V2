"""Bounded cross-symbol observations: design/multi-symbol.md, delivery 1a."""

from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from conftest import build_series

from backtester.core.errors import LookaheadError
from backtester.core.market import MarketCalendar, ReferenceInput
from backtester.core.models import Timeframe as TF
from backtester.engine.market_replay import MarketReplay

START = datetime(2026, 3, 16, 10, tzinfo=UTC)
MIN = timedelta(minutes=1)


def spec(symbol="B", **kwargs):
    return ReferenceInput(symbol, "reference", (TF.M1,), max_age=MIN, **kwargs)


def series(symbol="B", tf=TF.M1, start=START, n=3):
    return build_series([(100, 101, 99, 100)] * n, tf, start, symbol)


def test_closed_only_retained_immutable_and_new_ranges():
    replay = MarketReplay((spec(),), [series()])
    first = replay.advance(START)
    assert first.views["B"][TF.M1] is None
    assert not first.ready
    second = replay.advance(START + MIN)
    view = second.views["B"][TF.M1]
    assert view.cursor == 0
    assert second.availability["B"][TF.M1].last_close_time == START + MIN
    assert second.newly_closed["B"][TF.M1] == range(1)
    with pytest.raises(LookaheadError):
        _ = view[1]
    with pytest.raises(TypeError):
        second.views["B"][TF.M1] = None
    with pytest.raises(TypeError):
        second.views["C"] = {}
    third = replay.advance(START + 3 * MIN)
    assert third.newly_closed["B"][TF.M1] == range(1, 3)
    assert [third.views["B"][TF.M1].at(i).current.ts for i in range(1, 3)] == [
        START + MIN, START + 2 * MIN,
    ]
    assert replay.advance(START + 3 * MIN).newly_closed["B"][TF.M1] == range(3, 3)
    assert view.cursor == 0 and first.views["B"][TF.M1] is None
    with pytest.raises(ValueError, match="backward"):
        replay.advance(START)
    assert not hasattr(second, "view_at")


def test_equal_time_batch_and_higher_timeframe_boundary():
    inputs = (spec("B"), ReferenceInput("C", "daily", (TF.M1, TF.H1), max_age=MIN))
    histories = [series(), series("C"), series("C", TF.H1)]
    one = MarketReplay(inputs, histories).advance(START + timedelta(hours=1))
    two = MarketReplay(inputs[::-1], histories[::-1]).advance(START + timedelta(hours=1))
    assert one.availability == two.availability
    assert one.views["C"][TF.H1].cursor == 0
    earlier = MarketReplay(inputs, histories).advance(START + timedelta(minutes=59))
    assert earlier.views["C"][TF.H1] is None


def test_missing_empty_short_warmup_and_incomplete_window():
    replay = MarketReplay((spec(min_candles=3, require_contiguous=True),), [series(n=2)])
    assert replay.advance(START + 2 * MIN).availability["B"][TF.M1].status == "not_ready"
    missing = replay.advance(START + 4 * MIN).availability["B"][TF.M1]
    assert missing.status == "missing" and missing.age == 2 * MIN
    assert missing.reason
    empty = MarketReplay((spec(),), [series(n=0)]).advance(START)
    assert empty.availability["B"][TF.M1].status == "missing"
    from backtester.core.series import CandleSeries
    candles = series(n=4)._candles
    hole = CandleSeries("B", TF.M1, [candles[0], candles[2], candles[3]])
    status = MarketReplay((spec(min_candles=3, require_contiguous=True),), [hole]).advance(
        START + 4 * MIN
    )
    assert status.availability["B"][TF.M1].status == "not_ready"


@pytest.mark.parametrize("day,ny_hour", [(2, 14), (16, 13), (30, 13)])
def test_us_eu_dst_mismatch_sessions_holidays_and_weekend(day, ny_hour):
    # US changes on March 8; Europe on March 29. Both calendars use local civil time.
    now = datetime(2026, 3, day, ny_hour, 31, tzinfo=UTC)
    ny = MarketCalendar("ny", "America/New_York", time(9, 30), time(16))
    eu = MarketCalendar("london", "Europe/London", time(8), time(16, 30))
    assert ny.is_open(now) and eu.is_open(now)
    assert not ny.is_open(now - timedelta(hours=1))
    holiday = replace(ny, holidays=(now.date(),))
    assert not holiday.is_open(now)
    old = series(start=now - timedelta(days=3), n=1)
    snap = MarketReplay((spec(calendar=holiday),), [old]).advance(now)
    assert snap.availability["B"][TF.M1].status == "closed" and snap.ready
    assert not ny.is_open(datetime(2026, 3, 21, 15, tzinfo=UTC))


def test_ny_17_daily_close_and_crypto_scheduled_break():
    now = datetime(2026, 3, 16, 17, tzinfo=ZoneInfo("America/New_York")).astimezone(UTC)
    daily = series(tf=TF.D1, start=now - TF.D1.duration, n=1)
    cfg = ReferenceInput("B", "daily", (TF.M1, TF.D1), max_age=MIN)
    replay = MarketReplay((cfg,), [series(start=now - MIN), daily])
    assert replay.advance(now - MIN).views["B"][TF.D1] is None
    assert replay.advance(now).views["B"][TF.D1].current.ts + TF.D1.duration == now
    crypto = MarketCalendar("crypto", "UTC", time(), time(), weekdays=tuple(range(7)),
                            breaks=((time(10), time(11)),))
    snap = MarketReplay((spec(calendar=crypto),), [series(n=1)]).advance(START + 30 * MIN)
    assert snap.availability["B"][TF.M1].status == "closed"


def test_invalid_declarations_and_non_utc_input():
    with pytest.raises(ValueError):
        replace(spec(), timeframes=())
    with pytest.raises(ValueError):
        replace(spec(), max_age=-MIN)
    with pytest.raises(ValueError):
        replace(spec(), min_candles=0)
    with pytest.raises(ValueError):
        MarketReplay((spec(), spec()), [series()])
    with pytest.raises(ValueError):
        MarketReplay((spec(),), [series(), series()])
    with pytest.raises(ValueError):
        MarketReplay((spec(),), [])
    non_utc = START.astimezone(ZoneInfo("Europe/Zurich"))
    with pytest.raises(ValueError, match="UTC"):
        MarketReplay((spec(),), [series(start=non_utc)])


def test_optional_missing_input_reported_without_blocking_required_inputs():
    replay = MarketReplay((spec(), spec("C", required=False)), [series(), series("C", n=0)])
    snap = replay.advance(START + MIN)
    assert snap.ready and not snap.availability["C"][TF.M1].ready


def test_overnight_session_uses_opening_day_and_holes_ignore_scheduled_closure():
    calendar = MarketCalendar("overnight", "America/New_York", time(17), time(16),
                              weekdays=(6, 0, 1, 2, 3))
    assert calendar.is_open(datetime(2026, 3, 16, 2, tzinfo=UTC))  # Sunday session
    assert not calendar.is_open(datetime(2026, 3, 21, 2, tzinfo=UTC))
    from backtester.core.series import CandleSeries
    early = series(start=START.replace(hour=9, minute=59), n=1)
    late = series(start=START.replace(hour=11), n=1)
    gap_calendar = MarketCalendar("break", "UTC", breaks=((time(10), time(11)),))
    history = CandleSeries("B", TF.M1, [early._candles[0], late._candles[0]])
    snap = MarketReplay((spec(calendar=gap_calendar, min_candles=2),), [history]).advance(
        START.replace(hour=11, minute=1)
    )
    assert snap.ready


def test_higher_timeframe_partial_bucket_is_not_a_complete_signal_window():
    cfg = ReferenceInput("B", "hour", (TF.M1, TF.H1), max_age=MIN)
    # Resampling can produce an H1 candle from a partial M1 bucket. It is visible,
    # but it must not certify a complete observation window.
    partial = MarketReplay((cfg,), [series(n=59), series(tf=TF.H1, n=1)]).advance(
        START + timedelta(hours=1)
    )
    assert partial.views["B"][TF.H1] is not None
    assert partial.availability["B"][TF.H1].status == "not_ready"
    complete = MarketReplay((cfg,), [series(n=60), series(tf=TF.H1, n=1)]).advance(
        START + timedelta(hours=1)
    )
    assert complete.ready
