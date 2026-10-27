"""Synthetic schedule tests; no delivered calendar is opened."""

from dataclasses import fields, replace
from datetime import UTC, date, datetime, timedelta

import pytest

from backtester.data.news import (
    Calendar,
    EventResults,
    ImpactWindow,
    InstrumentNews,
    NewsConfig,
    ScheduleEvent,
    blocked,
    matching_events,
    relevant,
)

RELEASE = datetime(2026, 1, 5, 13, 30, tzinfo=UTC)


def event(**kw):
    values = {
        "event_id": "one",
        "scheduled_at": RELEASE,
        "day": RELEASE.date(),
        "window_start": None,
        "window_end": None,
        "time_precision": "second",
        "currency": "USD",
        "country": "US",
        "impact": "High",
        "name": "Synthetic release",
        "source_provider": "synthetic",
    }
    return ScheduleEvent(**(values | kw))


def calendar(*events):
    return Calendar(tuple(events), "synthetic-sha", date(2020, 1, 2), date(2026, 10, 23))


def test_schedule_has_no_result_objects():
    assert not {"actual", "forecast", "previous"} & {f.name for f in fields(ScheduleEvent)}
    assert not {"actual", "forecast", "previous", "results"} & {f.name for f in fields(Calendar)}


def test_result_delay_one_tick_and_missing_release():
    schedule = calendar(event(), event(event_id="date", scheduled_at=None, time_precision="date"))
    results = EventResults(schedule, {"one": "2.5%", "date": "10K"})
    delay = timedelta(seconds=30)
    assert results.actual("one", RELEASE - timedelta(microseconds=1), delay) is None
    assert results.actual("one", RELEASE + delay - timedelta(microseconds=1), delay) is None
    assert results.actual("one", RELEASE + delay, delay) == "2.5%"
    assert results.actual("date", RELEASE + timedelta(days=1), delay) is None
    with pytest.raises(ValueError):
        results.actual("one", RELEASE, timedelta(seconds=-1))


def test_currency_first_country_fallback_global_explicit():
    config = NewsConfig()
    assert relevant(event(currency="EUR"), "EURUSD", config)
    assert not relevant(event(currency="JPY", country="US"), "EURUSD", config)
    assert relevant(event(currency="", country="US"), "EURUSD", config)
    assert not relevant(event(currency="GLOBAL"), "XAUUSD", config)
    config = replace(config, instruments={"XAUUSD": InstrumentNews("USD", "US", True)})
    assert relevant(event(currency="GLOBAL"), "XAUUSD", config)
    assert not relevant(event(), "MISSING", config)


@pytest.mark.parametrize(
    "symbol,currency",
    [
        ("XAUUSD", "USD"),
        ("GBPUSD", "GBP"),
        ("GBPJPY", "JPY"),
        ("NAS100", "USD"),
        ("US500", "USD"),
        ("US30", "USD"),
        ("US2000", "USD"),
        ("GER40", "EUR"),
        ("BTCUSD", "USD"),
        ("ETHUSD", "USD"),
    ],
)
def test_default_instrument_mapping(symbol, currency):
    assert relevant(event(currency=currency), symbol, NewsConfig())


def test_inclusive_boundaries_and_simultaneous_events():
    config = NewsConfig(enabled=True, high=ImpactWindow(5, 10))
    schedule = calendar(event(), event(event_id="two"))
    for at in (RELEASE - timedelta(minutes=5), RELEASE, RELEASE + timedelta(minutes=10)):
        assert blocked(at, "EURUSD", schedule, config)
        assert len(matching_events(at, "EURUSD", schedule, config)) == 2
    for at in (
        RELEASE - timedelta(minutes=5, microseconds=1),
        RELEASE + timedelta(minutes=10, microseconds=1),
    ):
        assert not blocked(at, "EURUSD", schedule, config)


def test_off_missing_calendar_flag_only_and_independent_impact_windows():
    schedule = calendar(event(impact="Medium"))
    config = NewsConfig(enabled=True, high=ImpactWindow(30, 30), medium=ImpactWindow(1, 2))
    assert not blocked(RELEASE, "EURUSD", schedule, NewsConfig())
    assert not blocked(RELEASE, "EURUSD", None, config)
    assert not blocked(RELEASE - timedelta(minutes=2), "EURUSD", schedule, config)
    assert blocked(RELEASE + timedelta(minutes=2), "EURUSD", schedule, config)
    flags = replace(config, policy="flag_only")
    assert not blocked(RELEASE, "EURUSD", schedule, flags)
    assert len(matching_events(RELEASE, "EURUSD", schedule, flags)) == 1


@pytest.mark.parametrize("precision", ["date", "unknown", "range"])
def test_uncertain_precision_block_day_or_explicit_skip(precision):
    kwargs = {"scheduled_at": None, "time_precision": precision}
    if precision == "range":
        kwargs.update(window_start=RELEASE, window_end=RELEASE + timedelta(days=1))
    schedule = calendar(event(**kwargs))
    config = NewsConfig(enabled=True, uncertain_policy="block_day")
    assert blocked(RELEASE.replace(hour=0), "EURUSD", schedule, config)
    assert blocked(RELEASE.replace(hour=23, minute=59), "EURUSD", schedule, config)
    assert not blocked(RELEASE - timedelta(days=1), "EURUSD", schedule, config)
    assert not blocked(RELEASE, "EURUSD", schedule, replace(config, uncertain_policy="skip"))


def test_an_impact_without_a_window_is_not_filtered_at_all():
    """Medium has no window (rule set by the user, 2026-10-27): neither its exact releases nor
    its day-only rows block anything; High day-only rows still block their day."""
    medium_exact = event(event_id="m1", impact="Medium")
    medium_day = event(event_id="m2", impact="Medium", scheduled_at=None, time_precision="date")
    high_day = event(event_id="h", scheduled_at=None, time_precision="date", day=date(2026, 1, 6))
    schedule = calendar(medium_exact, medium_day, high_day)
    config = NewsConfig(enabled=True)  # defaults: High 2 / 2, Medium 0 / 0, block_day
    assert (config.high, config.medium) == (ImpactWindow(2, 2), ImpactWindow(0, 0))
    assert matching_events(RELEASE, "EURUSD", schedule, config) == ()
    assert not blocked(RELEASE.replace(hour=0), "EURUSD", schedule, config)
    assert blocked(datetime(2026, 1, 6, 9, 0, tzinfo=UTC), "EURUSD", schedule, config)


@pytest.mark.parametrize("minutes", [-1, float("inf"), float("nan")])
def test_invalid_windows(minutes):
    with pytest.raises(ValueError):
        ImpactWindow(minutes, 0)


def test_naive_simulation_time_is_rejected():
    with pytest.raises(ValueError):
        blocked(RELEASE.replace(tzinfo=None), "EURUSD", calendar(event()), NewsConfig(enabled=True))
