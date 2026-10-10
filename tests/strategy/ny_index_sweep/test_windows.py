"""AM / PM trading windows of strategy 2. Spec: strategy-ny-indices.md › General.

AM 09:00-11:30 ET (open 09:30, best time 09:50-10:10), PM 13:30-16:00 ET (open 14:00,
best time 13:50-14:10), New York DST (zoneinfo America/New_York), Monday to Friday.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time

import pytest

from backtester.strategy.ny_index_sweep.windows import (
    DEFAULT_WINDOWS,
    Window,
    WindowConfig,
    WindowTimes,
    is_best_time,
    window_of,
    window_on,
    windows_between,
)

AM, PM = Window.AM, Window.PM


def utc(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def test_summer_and_winter_times_in_utc():
    # EDT (UTC-4) in September, EST (UTC-5) in January
    am = window_on(date(2026, 9, 2), AM)
    assert (am.start, am.open, am.end) == (utc("2026-09-02 13:00"), utc("2026-09-02 13:30"),
                                            utc("2026-09-02 15:30"))  # fmt: skip
    assert (am.best_start, am.best_end) == (utc("2026-09-02 13:50"), utc("2026-09-02 14:10"))
    pm = window_on(date(2026, 1, 14), PM)
    assert (pm.start, pm.open, pm.end) == (utc("2026-01-14 18:30"), utc("2026-01-14 19:00"),
                                            utc("2026-01-14 21:00"))  # fmt: skip
    assert (pm.kind, pm.trading_date) == (PM, date(2026, 1, 14))


def test_dst_changes_move_the_windows_in_utc():
    # US DST starts Sunday 2026-03-08 and ends Sunday 2026-11-01 (Europe's dates don't matter)
    assert window_on(date(2026, 3, 6), AM).start == utc("2026-03-06 14:00")  # EST
    assert window_on(date(2026, 3, 9), AM).start == utc("2026-03-09 13:00")  # EDT
    assert window_on(date(2026, 3, 30), AM).start == utc("2026-03-30 13:00")  # EU switched too
    assert window_on(date(2026, 10, 30), PM).start == utc("2026-10-30 17:30")  # EDT
    assert window_on(date(2026, 11, 2), PM).start == utc("2026-11-02 18:30")  # EST


def test_no_windows_on_weekends():
    assert window_on(date(2026, 9, 5), AM) is None  # Saturday
    assert window_on(date(2026, 9, 6), PM) is None  # Sunday


def test_a_candle_belongs_to_the_window_it_closes_in():
    # AM 2026-09-02: 13:00-15:30 UTC. The 1m candle closing at 13:00 is before the window,
    # the one closing at 13:01 is its first, the one closing at 15:30 its last
    assert window_of(utc("2026-09-02 13:00")) is None
    assert window_of(utc("2026-09-02 13:01")) == window_on(date(2026, 9, 2), AM)
    assert window_of(utc("2026-09-02 15:30")).kind is AM
    assert window_of(utc("2026-09-02 15:31")) is None  # between AM and PM
    assert window_of(utc("2026-09-02 17:35")).kind is PM
    assert window_of(utc("2026-09-05 14:00")) is None  # Saturday


def test_best_time_tag_includes_both_edges():
    am = window_on(date(2026, 9, 2), AM)
    assert is_best_time(utc("2026-09-02 13:50"), am)
    assert is_best_time(utc("2026-09-02 14:10"), am)
    assert not is_best_time(utc("2026-09-02 13:49"), am)
    assert not is_best_time(utc("2026-09-02 14:11"), am)


def test_windows_between_lists_them_in_order():
    found = windows_between(utc("2026-09-04 00:00"), utc("2026-09-08 00:00"))
    assert [(w.trading_date, w.kind) for w in found] == [
        (date(2026, 9, 4), AM),
        (date(2026, 9, 4), PM),
        (date(2026, 9, 7), AM),
        (date(2026, 9, 7), PM),
    ]


def test_windows_are_settings():
    late = WindowConfig(am=WindowTimes(time(9, 30), time(12, 0), time(9, 30), time(10, 0),
                                       time(10, 30)))  # fmt: skip
    assert window_on(date(2026, 9, 2), AM, late).end == utc("2026-09-02 16:00")
    assert DEFAULT_WINDOWS.pm.open == time(14, 0)
    with pytest.raises(ValueError):
        WindowTimes(time(11, 0), time(10, 0), time(10, 30), time(10, 30), time(10, 40))
