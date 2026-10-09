"""Keep the view when switching timeframe: the days the new view needs. Spec: ROADMAP.md ›
4.0b part 1. (Centring itself happens in the browser, `chart.js` `showView`.)"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

from backtester.core.models import Timeframe
from backtester.ui.chart_config import DEFAULT_CONFIG
from backtester.ui.pages.chart import dates_for_view, estimated_candles

SEP = [date(2026, 9, 1) + timedelta(days=i) for i in range(30)]  # 09-01 .. 09-30
CONFIG = replace(DEFAULT_CONFIG, switch_warmup_candles=0)


def view(at: str, count: float) -> dict:
    return {"center": datetime.fromisoformat(at).replace(tzinfo=UTC).timestamp(), "count": count}


def test_a_switch_up_adds_the_days_the_view_needs():
    # 120 5m candles around 09-15 12:15 on the days 09-15..09-15; switch to 1h: +-60 hours
    found = dates_for_view(
        SEP, date(2026, 9, 15), date(2026, 9, 15), view("2026-09-15T12:15", 120), Timeframe.H1,
        CONFIG,
    )  # fmt: skip
    assert found == (date(2026, 9, 13), date(2026, 9, 18))  # 12:15 - 60h .. + 60h


def test_warm_up_candles_are_added_on_the_left():
    config = replace(DEFAULT_CONFIG, switch_warmup_candles=48)  # 48 hours on 1h
    found = dates_for_view(
        SEP, date(2026, 9, 15), date(2026, 9, 15), view("2026-09-15T12:15", 120), Timeframe.H1,
        config,
    )  # fmt: skip
    assert found == (date(2026, 9, 11), date(2026, 9, 18))


def test_the_shown_days_are_kept_when_they_cover_the_view():
    assert (
        dates_for_view(SEP, SEP[0], SEP[-1], view("2026-09-15T12:15", 120), Timeframe.M30, CONFIG)
        is None
    )


def test_the_days_stop_at_a_missing_day():
    days = [d for d in SEP if d != date(2026, 9, 12)]
    found = dates_for_view(
        days, date(2026, 9, 15), date(2026, 9, 15), view("2026-09-15T12:15", 120), Timeframe.H4,
        CONFIG,
    )  # fmt: skip
    assert found == (date(2026, 9, 13), date(2026, 9, 25))  # 09-12 missing, +-10 days


def test_a_switch_down_keeps_only_the_needed_days_when_the_range_is_too_long():
    # a month on 1m is ~43,000 candles: only the days around the view are loaded
    assert estimated_candles(SEP[0], SEP[-1], Timeframe.M1) > CONFIG.max_candles
    found = dates_for_view(SEP, SEP[0], SEP[-1], view("2026-09-15T12:15", 120), Timeframe.M1,
                           CONFIG)  # fmt: skip
    assert found == (date(2026, 9, 15), date(2026, 9, 15))


def test_a_centre_on_an_uncached_day_changes_nothing():
    assert dates_for_view([], SEP[0], SEP[1], view("2026-09-15T12:15", 120), Timeframe.H1) is None
