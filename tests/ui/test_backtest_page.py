"""The Backtest page (`/backtest`): the running backtest with a large progress bar, its numbers
and a Cancel button; without a job the newest results. Spec: ROADMAP.md > 7.6."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from dash import no_update

from backtester.data.sources import SymbolSources
from backtester.ui import app as app_module
from backtester.ui import backtest_job as bj
from backtester.ui import nav
from backtester.ui.pages import backtest, chart


class FakeRun:
    def __init__(self):
        self.done = self.total = 0
        self.folder: Path | None = None
        self.error: Exception | None = None
        self.cancelled = self.finished = False
        self.cancel_called = False

    def cancel(self):
        self.cancel_called = True


@pytest.fixture(autouse=True)
def clean():
    bj.reset()
    yield
    bj.reset()


def begin(run=None):
    run = run or FakeRun()
    bj.start(["AUDUSD", "XAUUSD"], date(2026, 9, 2), date(2026, 9, 30), None, None, "Default",
             starter=lambda *a, **k: run, clock=lambda: 100.0)  # fmt: skip
    return run


def text(component) -> str:
    return str(component)


def test_running_page_has_the_large_bar_numbers_and_cancel_button():
    begin()
    page = text(backtest.layout(bj.snapshot(bj.current(), now=105.0)))
    for id_ in ("bj-fill", "bj-pct", "bj-detail", "bj-elapsed", "bj-eta", "bj-cancel",
                "bj-timer", "bj-title", "bj-message"):  # fmt: skip
        assert f"'{id_}'" in page
    for shown in ("AUDUSD, XAUUSD", "2026-09-02 → 2026-09-30", "Strategy 1 · Session zone sweep",
                  "Default", "Cancel"):  # fmt: skip
        assert shown in page


def test_bar_is_striped_while_candles_load_and_plain_after():
    run = begin()
    assert "bj-loading" in backtest.poll_outputs(bj.snapshot(bj.current(), now=101.0))["track"]
    run.done, run.total = 5, 1000
    assert backtest.poll_outputs(bj.snapshot(bj.current(), now=102.0))["track"] == "bj-track"


def test_poll_outputs_follow_the_job():
    run = begin()
    run.done, run.total = 250, 1000
    out = backtest.poll_outputs(bj.snapshot(bj.current(), now=130.0))
    assert out["fill"] == {"width": "25.0%"} and out["pct"] == "25%"
    assert out["detail"] == "250 of 1,000 candles" and out["elapsed"] == "0:30"
    assert out["eta"] == "1:30" and out["cancel_disabled"] is False
    assert out["timer_disabled"] is False and out["page"] is no_update
    assert out["title"] == "Backtest running"


def test_finished_job_opens_its_results_and_stops_polling():
    run = begin()
    run.finished, run.done, run.total = True, 1000, 1000
    run.folder = Path("results/20261008-120000_AUDUSD-XAUUSD")
    out = backtest.poll_outputs(bj.snapshot(bj.current(), now=150.0))
    assert out["fill"] == {"width": "100.0%"} and out["timer_disabled"] is True
    assert out["page"] == "/results/20261008-120000_AUDUSD-XAUUSD"
    assert out["title"] == "Backtest done"


def test_failed_and_cancelled_jobs_say_so_and_stay_on_the_page():
    run = begin()
    run.finished, run.error = True, KeyError("no doji threshold for X")
    out = backtest.poll_outputs(bj.snapshot(bj.current(), now=101.0))
    assert out["title"] == "Backtest failed" and out["message"] == "no doji threshold for X"
    assert out["page"] is no_update and out["timer_disabled"] is True
    assert out["cancel_disabled"] is True
    bj.reset()
    run = begin()
    run.finished, run.cancelled = True, True
    out = backtest.poll_outputs(bj.snapshot(bj.current(), now=101.0))
    assert out["title"] == "Backtest cancelled" and "Nothing was saved" in out["message"]


def test_cancel_button_cancels_the_job_and_shows_it():
    run = begin()
    assert backtest.press_cancel(1) is True and run.cancel_called
    assert backtest.press_cancel(0) is False  # the page being built is not a click
    out = backtest.poll_outputs(bj.snapshot(bj.current(), now=101.0))
    assert out["detail"] == "Cancelling …" and out["cancel_disabled"] is True


def test_no_job_shows_the_newest_results_or_an_empty_page(tmp_path):
    assert "No backtest yet" in text(backtest.page(tmp_path))
    old = tmp_path / "20261001-090000_XAUUSD"
    new = tmp_path / "20261008-120000_XAUUSD"
    for folder in (old, new):
        folder.mkdir()
        (folder / "summary.json").write_text(json.dumps({"symbols": ["XAUUSD"]}))
        (folder / "trades.csv").write_text("")
    page = text(backtest.page(tmp_path))
    assert "rs-run-id" in page and "20261008-120000_XAUUSD" in page


def test_running_job_wins_over_results_and_a_failed_one_stays_visible(tmp_path):
    run = begin()
    assert "bj-cancel" in text(backtest.page(tmp_path))
    run.finished, run.error = True, ValueError("boom")
    assert "boom" in text(backtest.page(tmp_path))  # until the next run starts
    run.error, run.cancelled = None, True
    assert "Nothing was saved" in text(backtest.page(tmp_path))
    bj.reset()
    assert "No backtest yet" in text(backtest.page(tmp_path))


def test_app_routes_backtest_and_the_nav_marks_it():
    assert app_module.page_for("/backtest", SymbolSources({})) is not None
    assert nav.section_of("/backtest") == "backtest"
    assert nav.section_of("/results/x") == "backtest"
    assert nav.section_of("/") == "chart"
    assert nav.backtest_href() == "/backtest"


def test_run_goes_to_the_backtest_page_and_a_second_run_says_so():
    run = FakeRun()
    started = []

    def fake_start(symbols, start, end, settings, sources, preset):
        started.append((symbols, start, end, preset))
        return run

    status, page = chart.start_backtest(
        None, ["AUDUSD"], "2026-09-02", "2026-09-30", fake_start, preset="Default"
    )
    assert started == [(["AUDUSD"], date(2026, 9, 2), date(2026, 9, 30), "Default")]
    assert page == "/backtest" and status == ""
    status, page = chart.start_backtest(None, ["XAUUSD"], "2026-09-02", "2026-09-30", fake_start)
    assert page is no_update and "already running" in status and len(started) == 1


def test_run_needs_symbols_and_days():
    status, page = chart.start_backtest(None, [], "2026-09-02", "2026-09-30")
    assert status.startswith("Pick one or more symbols") and page is no_update
    assert bj.current() is None
