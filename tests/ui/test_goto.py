"""Go to a date / time: parsing and the days to load. Spec: ROADMAP.md › 4.0b part 4.
(Centring on the candle happens in the browser, `chart.js` `goto`.)"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from backtester.core.models import Timeframe
from backtester.ui.pages.chart import goto_dates, parse_goto

SEP = [date(2026, 9, 1) + timedelta(days=i) for i in range(30)]  # 09-01 .. 09-30


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2026-09-12 12:15", datetime(2026, 9, 12, 12, 15, tzinfo=UTC)),
        ("2026-09-12T12:15", datetime(2026, 9, 12, 12, 15, tzinfo=UTC)),
        (" 2026-09-12 8:05 UTC ", datetime(2026, 9, 12, 8, 5, tzinfo=UTC)),
        ("2026-09-12", datetime(2026, 9, 12, tzinfo=UTC)),
        ("2026-09-12 25:00", None),
        ("12.09.2026", None),
        ("", None),
        (None, None),
    ],
)
def test_parse(text, expected):
    assert parse_goto(text) == expected


def at(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def test_a_time_in_the_shown_days_loads_nothing():
    assert goto_dates(SEP, SEP[0], SEP[-1], at("2026-09-15 12:15"), Timeframe.M5) is None


def test_another_day_keeps_the_shown_length_centred_on_it():
    # 09-14..09-16 shown (2 days apart), go to 09-22: 09-21..09-23
    found = goto_dates(SEP, date(2026, 9, 14), date(2026, 9, 16), at("2026-09-22 08:00"),
                       Timeframe.M1)  # fmt: skip
    assert found == (date(2026, 9, 21), date(2026, 9, 23))


def test_the_days_stay_in_the_cached_run_and_the_candle_limit():
    found = goto_dates(SEP, date(2026, 9, 20), date(2026, 9, 30), at("2026-09-02 08:00"),
                       Timeframe.M5)  # fmt: skip
    assert found == (date(2026, 9, 1), date(2026, 9, 11))  # starts at the first cached day
    # a month shown on 1m would be too many candles: shorter
    first, last = goto_dates(SEP, SEP[0], SEP[0], at("2026-09-02 08:00"), Timeframe.M1)
    assert first <= date(2026, 9, 2) <= last


def test_an_uncached_day_is_a_message():
    assert "not in the cache" in goto_dates(SEP, SEP[0], SEP[5], at("2026-10-05 08:00"),
                                            Timeframe.M5)  # fmt: skip
