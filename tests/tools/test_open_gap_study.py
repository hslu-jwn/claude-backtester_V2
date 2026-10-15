"""Open / gap / trend-day study tool. Spec: ROADMAP.md › 11.2."""

from __future__ import annotations

import csv
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from backtester.analytics.open_gap import Bar, OpenGapConfig, cash_days, missing_weekdays
from backtester.tools import open_gap_study

NY = ZoneInfo("America/New_York")
MON = date(2026, 9, 14)


def at(d, hh, mm):
    return datetime.combine(d, time(hh, mm), NY).astimezone(UTC)


def session(d, base=100.0, minutes=range(390), over=None):
    over = over or {}
    out = []
    for m in minutes:
        o, h, lo, c = over.get(m, (base, base + 0.5, base - 0.5, base))
        out.append(Bar(at(d, 9, 30) + timedelta(minutes=m), o, h, lo, c))
    return out


def week_bars(n_days=6):
    """Mon..Fri then the next Monday (skipping the weekend), with gaps and a trend day."""
    dates = [
        MON + timedelta(days=i)
        for i in range(n_days + 2)
        if (MON + timedelta(days=i)).weekday() < 5
    ]
    out = []
    for i, d in enumerate(dates):
        out += session(d, base=100.0 + 0.4 * (i % 3), over={389: (100, 101, 99, 100.0 + i * 0.1)})
    return out


# --- missing weekdays ---------------------------------------------------------------------------


def test_missing_weekdays_lists_weekdays_without_any_cash_bar():
    bars = session(MON) + session(MON + timedelta(days=3))  # Mon and Thu
    days = cash_days(bars, OpenGapConfig(atr_period=2))
    assert missing_weekdays(days) == [MON + timedelta(days=1), MON + timedelta(days=2)]


def test_missing_weekdays_without_a_gap_or_with_no_days():
    days = cash_days(session(MON) + session(MON + timedelta(days=1)), OpenGapConfig())
    assert missing_weekdays(days) == []
    assert missing_weekdays([]) == []


def test_missing_weekdays_do_not_count_the_weekend():
    friday, monday = MON + timedelta(days=4), MON + timedelta(days=7)
    days = cash_days(session(friday) + session(monday), OpenGapConfig())
    assert missing_weekdays(days) == []


# --- the command -----------------------------------------------------------------------------------


@pytest.fixture
def fake_loader(monkeypatch):
    bars = week_bars(14)
    monkeypatch.setattr(open_gap_study, "load_m1", lambda symbol, start, end, cfg=None: bars)
    return bars


def run(tmp_path, *extra):
    argv = ["--symbols", "NAS100", "US500", "--atr-period", "2", "--out", str(tmp_path), *extra]
    return open_gap_study.main(argv)


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_main_writes_all_files_with_a_symbol_column(tmp_path, fake_loader, capsys):
    assert run(tmp_path) == 0
    for name in ("days.csv", "exclusions.csv", "gap_fill.csv", "first30.csv",
                 "trend_days.csv", "extremes.csv", "last_hour.csv"):  # fmt: skip
        rows = read(tmp_path / name)
        assert rows, name
        assert {r["symbol"] for r in rows} == {"NAS100", "US500"}, name
    text = capsys.readouterr().out
    assert "NAS100" in text and "gap" in text.lower()


def test_exclusions_count_reasons_per_symbol_and_half(tmp_path, fake_loader):
    assert run(tmp_path) == 0
    rows = read(tmp_path / "exclusions.csv")
    warm = [r for r in rows if r["symbol"] == "NAS100" and r["reason"] == "atr_warmup"]
    assert warm and sum(int(r["days"]) for r in warm) == 2  # atr_period 2
    assert {r["half"] for r in rows} <= {"2020-22", "2023-26"}


def test_a_symbol_that_cannot_be_loaded_is_skipped_with_a_message(tmp_path, monkeypatch, capsys):
    bars = week_bars(14)

    def loader(symbol, start, end, cfg=None):
        if symbol == "US500":
            raise ValueError("no cached days")
        return bars

    monkeypatch.setattr(open_gap_study, "load_m1", loader)
    assert run(tmp_path) == 0
    assert "US500" in capsys.readouterr().out
    assert {r["symbol"] for r in read(tmp_path / "days.csv")} == {"NAS100"}


def test_days_csv_has_one_row_per_regular_day_with_the_fields(tmp_path, fake_loader):
    run(tmp_path)
    rows = [r for r in read(tmp_path / "days.csv") if r["symbol"] == "NAS100"]
    assert {"date", "gap_atr", "gap_bucket", "filled_same_day", "trend", "last_hour_event"} <= set(
        rows[0]
    )
    assert len(rows) == len({r["date"] for r in rows}) > 5
