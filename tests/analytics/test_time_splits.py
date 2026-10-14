"""R split by time: hour, weekday, month part, New York window. Spec: ROADMAP.md › 6.5
(knowledge base I-22)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from backtester.analytics.metrics import (
    SPLITS,
    by_hour,
    by_month_part,
    by_ny_window,
    by_weekday,
    split,
)


@dataclass(frozen=True)
class T:
    entry_time: datetime
    exit_time: datetime
    symbol: str = "XAUUSD"
    r_gross: float = 1.0
    r_net: float = 1.0
    planned_r: float | None = None


def at(y, m, d, h=12, minute=0):
    t = datetime(y, m, d, h, minute, tzinfo=UTC)
    return T(entry_time=t, exit_time=t)


def test_hour_is_the_utc_hour_of_the_entry():
    assert by_hour(at(2026, 9, 2, 8, 5)) == "08:00 UTC"
    assert by_hour(at(2026, 9, 2, 23, 59)) == "23:00 UTC"
    assert by_hour(at(2026, 9, 2, 0, 0)) == "00:00 UTC"


def test_weekday_is_numbered_so_it_sorts_monday_first():
    assert by_weekday(at(2026, 9, 2)) == "3 Wed"
    assert by_weekday(at(2026, 9, 4)) == "5 Fri"
    assert by_weekday(at(2026, 9, 6)) == "7 Sun"
    assert by_weekday(at(2026, 8, 31)) == "1 Mon"


# September 2026: Tue 1st ... Wed 30th. Weekdays: 1 2 3 4 | 7-11 | 14-18 | 21-25 | 28 29 30.
@pytest.mark.parametrize(
    ("day", "part"),
    [
        (1, "first 3 days"),
        (3, "first 3 days"),
        (4, "mid"),  # the 4th weekday
        (5, "mid"),  # a Saturday after 4 weekdays
        (25, "mid"),  # 4 weekdays left on and after it
        (27, "last 3 days"),  # a Sunday with 28 29 30 after it
        (28, "last 3 days"),
        (30, "last 3 days"),
    ],
)
def test_month_part_counts_weekdays_from_both_ends(day, part):
    assert by_month_part(at(2026, 9, day)) == part


def test_month_part_weekend_at_the_month_edges():
    assert by_month_part(at(2026, 8, 1)) == "first 3 days"  # Saturday, no weekday before it
    assert by_month_part(at(2026, 8, 30)) == "last 3 days"  # Sunday, only Monday 31st after


def test_a_short_month_edge_prefers_first():
    # Feb 2026 has 20 weekdays: nothing overlaps, but the rule must be deterministic anyway
    assert by_month_part(at(2026, 2, 2)) == "first 3 days"
    assert by_month_part(at(2026, 2, 27)) == "last 3 days"


@pytest.mark.parametrize(
    ("args", "window"),
    [
        ((2026, 9, 2, 13, 29), "Outside cash hours"),  # 09:29 EDT
        ((2026, 9, 2, 13, 30), "Open"),  # 09:30 EDT
        ((2026, 9, 2, 14, 59), "Open"),  # 10:59 EDT
        ((2026, 9, 2, 15, 0), "Midday"),  # 11:00 EDT
        ((2026, 9, 2, 18, 59), "Midday"),  # 14:59 EDT
        ((2026, 9, 2, 19, 0), "Close"),  # 15:00 EDT
        ((2026, 9, 2, 19, 59), "Close"),  # 15:59 EDT
        ((2026, 9, 2, 20, 0), "Outside cash hours"),  # 16:00 EDT
    ],
)
def test_new_york_windows_in_summer_time(args, window):
    assert by_ny_window(at(*args)) == window


def test_new_york_windows_follow_winter_time():
    assert by_ny_window(at(2026, 1, 14, 14, 30)) == "Open"  # 09:30 EST
    assert by_ny_window(at(2026, 1, 14, 13, 30)) == "Outside cash hours"  # 08:30 EST


def test_new_york_windows_across_the_dst_week():
    # US DST started 2026-03-08; the week before 14:30 UTC is 09:30 EST, after it 10:30 EDT
    assert by_ny_window(at(2026, 3, 6, 14, 30)) == "Open"
    assert by_ny_window(at(2026, 3, 9, 14, 30)) == "Open"
    assert by_ny_window(at(2026, 3, 9, 13, 29)) == "Outside cash hours"  # 09:29 EDT


def test_the_time_splits_are_in_the_results_page_list():
    assert {"Hour (UTC)", "Weekday", "Month part", "NY window"} <= set(SPLITS)


def test_time_groups_come_out_in_time_order_not_first_seen_order():
    trades = [at(2026, 9, 4, 15), at(2026, 9, 2, 8), at(2026, 9, 3, 9)]
    assert list(split(trades, by_hour)) == ["08:00 UTC", "09:00 UTC", "15:00 UTC"]
    assert list(split(trades, by_weekday)) == ["3 Wed", "4 Thu", "5 Fri"]
    # an ordinary key keeps the first-seen order
    from backtester.analytics.metrics import by_symbol

    assert list(split(trades, by_symbol)) == ["XAUUSD"]


def test_split_by_month_part_and_window_summarizes_each_group():
    trades = [at(2026, 9, 1, 13, 30), at(2026, 9, 15, 13, 30), at(2026, 9, 29, 19, 0)]
    parts = split(trades, by_month_part)
    assert list(parts) == ["first 3 days", "mid", "last 3 days"]  # in this order, always
    assert parts["mid"]["trades"] == 1
    windows = split(trades, by_ny_window)
    assert list(windows) == ["Open", "Close"]
    assert windows["Open"]["trades"] == 2
