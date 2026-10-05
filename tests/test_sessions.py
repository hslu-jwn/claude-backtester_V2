"""Session clock. Spec: strategy-session-zones.md › Sessions.

All expected times are written in UTC. Reminders: EDT = UTC-4, EST = UTC-5, BST = UTC+1,
GMT = UTC+0, JST = UTC+9 (no DST).
2026 DST changes: US 8 Mar / 1 Nov, Europe 29 Mar / 25 Oct.
2025 DST changes: US 9 Mar / 2 Nov, Europe 30 Mar / 26 Oct.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from itertools import pairwise

import pytest

from backtester.sessions import (
    Session,
    SessionConfig,
    SessionStart,
    next_session_start,
    session_of,
    session_starts,
)

TOKYO, LONDON, NEW_YORK = Session.TOKYO, Session.LONDON, Session.NEW_YORK


def utc(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def starts_on(day: str) -> dict[Session, datetime]:
    """Session -> UTC start of the sessions whose trading date is `day`."""
    d = date.fromisoformat(day)
    found = session_starts(utc(day) - timedelta(days=1), utc(day) + timedelta(days=2))
    return {s.session: s.start for s in found if s.trading_date == d}


@pytest.mark.parametrize(
    ("day", "tokyo", "london", "new_york"),
    [
        # US and Europe both on summer time: London 03:00 ET, NY 08:00 ET, Tokyo 20:00 ET.
        ("2026-07-15", "2026-07-15 00:00", "2026-07-15 07:00", "2026-07-15 12:00"),
        # Both on winter time: London 03:00 ET, NY 08:00 ET, Tokyo 19:00 ET (previous day).
        ("2026-01-14", "2026-01-14 00:00", "2026-01-14 08:00", "2026-01-14 13:00"),
        # US on summer, Europe still on winter: London 08:00 GMT = 04:00 EDT.
        ("2026-03-09", "2026-03-09 00:00", "2026-03-09 08:00", "2026-03-09 12:00"),
        ("2026-03-27", "2026-03-27 00:00", "2026-03-27 08:00", "2026-03-27 12:00"),
        # Europe switched to summer: London back to 03:00 ET.
        ("2026-03-30", "2026-03-30 00:00", "2026-03-30 07:00", "2026-03-30 12:00"),
        # Europe back on winter, US still on summer: London 08:00 GMT = 04:00 EDT.
        ("2026-10-26", "2026-10-26 00:00", "2026-10-26 08:00", "2026-10-26 12:00"),
        ("2026-10-30", "2026-10-30 00:00", "2026-10-30 08:00", "2026-10-30 12:00"),
        # Both on winter time again.
        ("2026-11-02", "2026-11-02 00:00", "2026-11-02 08:00", "2026-11-02 13:00"),
        # Same mismatch weeks in 2025 (different dates).
        ("2025-03-10", "2025-03-10 00:00", "2025-03-10 08:00", "2025-03-10 12:00"),
        ("2025-03-31", "2025-03-31 00:00", "2025-03-31 07:00", "2025-03-31 12:00"),
        ("2025-10-27", "2025-10-27 00:00", "2025-10-27 08:00", "2025-10-27 12:00"),
        ("2025-11-03", "2025-11-03 00:00", "2025-11-03 08:00", "2025-11-03 13:00"),
    ],
)
def test_session_starts_follow_each_citys_dst(day, tokyo, london, new_york):
    assert starts_on(day) == {TOKYO: utc(tokyo), LONDON: utc(london), NEW_YORK: utc(new_york)}


def test_tokyo_is_00_utc_all_year_so_its_new_york_time_moves():
    # Monday's Tokyo session opens on Sunday evening in New York.
    assert starts_on("2026-03-02")[TOKYO] == utc("2026-03-02 00:00")  # Sun 19:00 EST
    assert starts_on("2026-03-09")[TOKYO] == utc("2026-03-09 00:00")  # Sun 20:00 EDT
    assert starts_on("2026-11-02")[TOKYO] == utc("2026-11-02 00:00")  # Sun 19:00 EST


def test_no_sessions_on_the_weekend():
    found = session_starts(utc("2026-03-07 00:00"), utc("2026-03-09 00:00"))
    assert found == []


def test_each_session_ends_when_the_next_starts_and_friday_ny_ends_at_monday_tokyo():
    found = session_starts(utc("2026-03-05 00:00"), utc("2026-03-10 00:00"))
    assert [s.session for s in found[:4]] == [TOKYO, LONDON, NEW_YORK, TOKYO]
    for a, b in pairwise(found):
        assert a.end == b.start
    friday_ny = next(
        s for s in found if s.trading_date == date(2026, 3, 6) and s.session is NEW_YORK
    )
    assert (friday_ny.start, friday_ny.end) == (utc("2026-03-06 13:00"), utc("2026-03-09 00:00"))
    assert found[-1].end == utc("2026-03-10 00:00")  # end known even for the last in range


def test_candle_at_a_session_start_belongs_to_the_new_session():
    # Summer: NY starts 12:00 UTC (08:00 EDT).
    assert session_of(utc("2026-07-15 11:55")).session is LONDON  # 07:55 ET
    ny = session_of(utc("2026-07-15 12:00"))
    assert (ny.session, ny.trading_date) == (NEW_YORK, date(2026, 7, 15))
    assert session_of(utc("2026-07-15 06:59")).session is TOKYO
    assert session_of(utc("2026-07-15 07:00")).session is LONDON


def test_mismatch_week_candle_at_03_et_is_still_tokyo():
    # 9 Mar 2026: 07:00 UTC = 03:00 EDT, but London opens at 08:00 GMT.
    assert session_of(utc("2026-03-09 07:00")).session is TOKYO
    assert session_of(utc("2026-03-09 08:00")).session is LONDON
    assert session_of(utc("2026-10-26 07:30")).session is TOKYO
    assert session_of(utc("2026-10-26 08:00")).session is LONDON


def test_sunday_open_before_tokyo_belongs_to_no_session():
    # Sun 1 Mar 2026, US winter: market opens 17:00 EST = 22:00 UTC, Tokyo 19:00 EST.
    assert session_of(utc("2026-03-01 22:00")) is None
    assert session_of(utc("2026-03-01 23:55")) is None  # 18:55 EST
    tokyo = session_of(utc("2026-03-02 00:00"))  # 19:00 EST
    assert (tokyo.session, tokyo.trading_date) == (TOKYO, date(2026, 3, 2))


def test_sunday_open_on_the_us_dst_change_day():
    # Sun 8 Mar 2026: the US switched at 02:00, market opens 17:00 EDT = 21:00 UTC,
    # Tokyo still 00:00 UTC = 20:00 EDT. 17:00..19:55 EDT is the ignored Sunday open.
    assert session_of(utc("2026-03-08 21:00")) is None
    assert session_of(utc("2026-03-08 23:55")) is None
    assert session_of(utc("2026-03-09 00:00")).session is TOKYO


def test_friday_ny_lasts_until_friday_midnight_new_york_then_weekend():
    friday = session_of(utc("2026-03-06 21:55"))  # Fri 16:55 EST, last gold candle
    assert (friday.session, friday.trading_date) == (NEW_YORK, date(2026, 3, 6))
    assert session_of(utc("2026-03-07 04:59")).session is NEW_YORK  # Fri 23:59 EST
    assert session_of(utc("2026-03-07 05:00")) is None  # Sat 00:00 EST
    assert session_of(utc("2026-03-07 12:00")) is None  # Saturday


def test_next_session_start():
    assert next_session_start(utc("2026-03-06 13:00")).start == utc("2026-03-09 00:00")
    nxt = next_session_start(utc("2026-07-15 11:59"))
    assert (nxt.session, nxt.start) == (NEW_YORK, utc("2026-07-15 12:00"))
    assert next_session_start(utc("2026-07-15 12:00")).start == utc("2026-07-16 00:00")


def test_start_times_come_from_the_config():
    config = SessionConfig(london=SessionStart(time(7, 0), "Europe/London"))
    found = session_starts(utc("2026-07-15 00:00"), utc("2026-07-16 00:00"), config)
    assert [s.start for s in found if s.session is LONDON] == [utc("2026-07-15 06:00")]


def test_naive_or_non_utc_times_are_rejected():
    with pytest.raises(ValueError):
        session_of(datetime(2026, 7, 15, 12, 0))  # noqa: DTZ001
