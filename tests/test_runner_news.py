"""The news blackout reaches real runs: runner -> engine calendar wiring. Spec: docs/news.md."""

from __future__ import annotations

import csv
import io
from dataclasses import replace
from datetime import date

import pytest
from test_runner import MON, SETTINGS, TUE, cache  # noqa: F401 (fixture)

from backtester import runner
from backtester.data import news
from backtester.data.news import CSV_COLUMNS, Calendar, ImpactWindow, NewsConfig, ScheduleEvent


def write_csv(path, when="2020-01-02T13:30:00Z", name="Synthetic"):
    row = dict.fromkeys(CSV_COLUMNS, "") | {
        "event_id": "one", "dedupe_key": "synthetic-one",
        "scheduled_timestamp_utc": when, "scheduled_date_utc": when[:10],
        "scheduled_date_local": when[:10], "source_timezone": "America/New_York",
        "time_precision": "minute", "time_label": "08:30:00", "currency": "USD",
        "country": "US", "impact": "High", "impact_rank": "3", "event_name": name,
        "point_in_time_verified": "false", "source_provider": "synthetic-A",
    }  # fmt: skip
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(CSV_COLUMNS)
    writer.writerow([row[c] for c in CSV_COLUMNS])
    path.write_bytes(stream.getvalue().encode("utf-8"))
    return path


@pytest.fixture
def loads(monkeypatch):
    calls = []
    real = news.load_calendar

    def counting(config):
        calls.append(config.path)
        return real(config)

    monkeypatch.setattr(news, "load_calendar", counting)
    return calls


def test_off_reads_no_file(tmp_path, loads):
    path = write_csv(tmp_path / "news.csv")
    assert news.execution_calendar(NewsConfig(path=str(path))) is None
    assert loads == []


def test_on_loads_once_per_file_version_and_reloads_a_changed_file(tmp_path, loads):
    path = write_csv(tmp_path / "news.csv")
    config = NewsConfig(path=str(path), enabled=True)
    first = news.execution_calendar(config)
    assert isinstance(first, Calendar) and len(first.events) == 1
    assert news.execution_calendar(config) is first
    assert len(loads) == 1
    write_csv(path, name="Synthetic, changed size")
    second = news.execution_calendar(config)
    assert second is not first and second.sha256 != first.sha256
    assert len(loads) == 2


def test_on_with_a_missing_file_is_no_calendar(tmp_path):
    config = NewsConfig(path=str(tmp_path / "absent.csv"), enabled=True)
    assert news.execution_calendar(config) is None


def test_an_invalid_existing_file_fails_instead_of_disabling(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("not,a,calendar\n", encoding="utf-8")
    with pytest.raises(ValueError):
        news.execution_calendar(NewsConfig(path=str(path), enabled=True))


def _event_at(when) -> Calendar:
    event = ScheduleEvent(
        "synthetic", when, when.date(), None, None, "minute", "USD", "US", "High", "Synthetic",
        "test",
    )  # fmt: skip
    return Calendar((event,), "synthetic-hash", date(2020, 1, 2), date(2026, 10, 23))


def _settings(enabled: bool):
    config = replace(
        SETTINGS.engine.news, enabled=enabled, events="impact", high=ImpactWindow(1, 1)
    )
    return replace(SETTINGS, engine=replace(SETTINGS.engine, news=config))


def test_the_runner_hands_the_calendar_to_the_engine_and_blocks_the_entry(cache, monkeypatch):  # noqa: F811
    baseline = runner.run_backtests(["XAUUSD"], MON, TUE, _settings(False), cache, workers=1)
    assert baseline.trades, "the scenario must trade for this test to mean anything"
    blocked_at = baseline.trades[0].entry_time
    seen = []

    def fake(config):
        seen.append(config.enabled)
        return _event_at(blocked_at) if config.enabled else None

    monkeypatch.setattr(runner, "execution_calendar", fake)
    off = runner.run_backtests(["XAUUSD"], MON, TUE, _settings(False), cache, workers=1)
    on = runner.run_backtests(["XAUUSD"], MON, TUE, _settings(True), cache, workers=1)
    assert off.trades == baseline.trades
    assert blocked_at not in [t.entry_time for t in on.trades]
    assert len(on.trades) < len(baseline.trades)
    assert seen == [False, True]
