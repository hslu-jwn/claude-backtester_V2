"""Synthetic research splits, with hand-written outcomes and no market data reads."""

from dataclasses import replace
from datetime import UTC, date, datetime
from types import SimpleNamespace

from backtester.data.news import Calendar, NewsConfig, ScheduleEvent
from backtester.tools.news_diagnostics import news_split


def ts(value):
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def test_day_minute_and_no_calendar_buckets_and_source_periods():
    release = ts("2020-01-03T13:30:00")
    event = ScheduleEvent(
        "one", release, release.date(), None, None, "minute", "USD", "US", "High", "Test", "A"
    )
    later = replace(
        event,
        event_id="two",
        scheduled_at=ts("2025-10-24T13:30:00"),
        day=date(2025, 10, 24),
        source_provider="B",
    )
    unrelated = replace(event, event_id="three", currency="JPY")
    medium = replace(
        event,
        event_id="four",
        impact="Medium",
        day=date(2020, 1, 6),
        scheduled_at=ts("2020-01-06T13:30:00"),
    )
    calendar = Calendar(
        (event, later, unrelated, medium), "synthetic-hash", date(2020, 1, 2), date(2026, 10, 23)
    )
    trades = [
        SimpleNamespace(symbol="EURUSD", entry_time=ts(t), r_net=r)
        for t, r in [
            ("2019-12-31T13:30:00", -1),
            ("2020-01-03T13:30:59", 2),
            ("2020-01-03T13:31:00", 3),
            ("2020-01-06T13:30:00", 4),
            ("2025-10-24T13:30:00", 5),
            ("2026-10-26T13:30:00", -2),
        ]
    ]
    rows = news_split(trades, calendar, NewsConfig())
    for dimension in ("day", "minute"):
        group = [r for r in rows if r["dimension"] == dimension]
        assert sum(r["trades"] for r in group) == 6
        assert sum(r["net_r"] for r in group) == 11
        missing = [r for r in group if r["bucket"] == "no_calendar"]
        assert sum(r["trades"] for r in missing) == 2
    day = [r for r in rows if r["dimension"] == "day" and r["bucket"] == "news"]
    minute = [r for r in rows if r["dimension"] == "minute" and r["bucket"] == "news"]
    assert sum(r["net_r"] for r in day) == 10
    assert sum(r["net_r"] for r in minute) == 7
    assert len({r["source_period"] for r in day}) == 2
    assert all(r["calendar_sha256"] == "synthetic-hash" for r in rows)
    merged = news_split(trades, calendar, replace(NewsConfig(), separate_source_periods=False))
    assert len({r["source_period"] for r in merged if r["bucket"] == "news"}) == 1
    assert news_split(trades, None, NewsConfig()) == []


def test_nonexact_high_is_news_day_but_unknown_minute():
    event = ScheduleEvent(
        "one", None, date(2020, 1, 3), None, None, "date", "USD", "US", "High", "Test", "A"
    )
    calendar = Calendar((event,), "synthetic", date(2020, 1, 2), date(2026, 10, 23))
    trade = SimpleNamespace(symbol="EURUSD", entry_time=ts("2020-01-03T13:30:00"), r_net=1)
    rows = news_split([trade], calendar, NewsConfig())
    assert {(r["dimension"], r["bucket"]) for r in rows} == {
        ("day", "news"),
        ("minute", "uncertain"),
    }
