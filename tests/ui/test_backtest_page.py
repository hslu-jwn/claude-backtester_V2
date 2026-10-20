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
        self.load_done = self.load_total = 0
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


def test_bar_is_striped_only_before_loading_reports_and_plain_after():
    run = begin()
    assert "bj-loading" in backtest.poll_outputs(bj.snapshot(bj.current(), now=101.0))["track"]
    run.load_done, run.load_total = 40, 100
    out = backtest.poll_outputs(bj.snapshot(bj.current(), now=102.0))
    assert out["track"] == "bj-track" and out["pct"] == "40%"
    assert out["fill"] == {"width": "40.0%"} and out["detail"] == "Loading data · phase 1 of 2"
    run.done, run.total = 5, 1000
    assert backtest.poll_outputs(bj.snapshot(bj.current(), now=103.0))["track"] == "bj-track"


def test_poll_outputs_follow_the_job():
    run = begin()
    run.done, run.total = 250, 1000
    out = backtest.poll_outputs(bj.snapshot(bj.current(), now=130.0))
    assert out["fill"] == {"width": "25.0%"} and out["pct"] == "25%"
    assert (
        out["detail"] == "Running · phase 2 of 2 · 250 of 1,000 candles"
        and out["elapsed"] == "0:30"
    )
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
    assert out["timer_disabled"] is True


def test_cancel_button_cancels_the_job_and_shows_it():
    run = begin()
    assert backtest.press_cancel(1) is True and run.cancel_called
    assert backtest.press_cancel(0) is False  # the page being built is not a click
    out = backtest.poll_outputs(bj.snapshot(bj.current(), now=101.0))
    assert out["detail"] == "Cancelling …" and out["cancel_disabled"] is True


def make_run(folder: Path, symbols=("XAUUSD",), net=-1.5, trades=7, strategy=None, created=None):
    folder.mkdir(parents=True)
    summary = {
        "symbols": list(symbols), "start": "2026-09-01", "end": "2026-09-30",
        "combined": {"trades": trades, "net_r_net": net},
    }  # fmt: skip
    if created:
        summary["created"] = created
    (folder / "summary.json").write_text(json.dumps(summary))
    if strategy:
        (folder / "settings.json").write_text(json.dumps({"strategy": {"name": strategy}}))
    (folder / "trades.csv").write_text("")


def test_run_rows_newest_first_with_strategy_symbols_days_trades_and_net_r(tmp_path):
    make_run(tmp_path / "20261001-090000_XAUUSD", trades=3, net=2.25)  # no settings: strategy 1
    make_run(
        tmp_path / "20261008-120000_NAS100-US500", ("NAS100", "US500"), -12.5, 40,
        "opening_range", "2026-10-08T12:00:30+00:00",
    )  # fmt: skip
    rows = backtest.run_rows(tmp_path)
    assert [r["id"] for r in rows] == ["20261008-120000_NAS100-US500", "20261001-090000_XAUUSD"]
    new, old = rows
    assert new["strategy"] == "Strategy 6 · Opening-range breakout"
    assert old["strategy"] == "Strategy 1 · Session zone sweep"
    assert new["symbols"] == "NAS100, US500" and new["days"] == "2026-09-01 → 2026-09-30"
    assert new["trades"] == 40 and new["net_r"] == -12.5 and old["net_r"] == 2.25
    assert new["date"] == "2026-10-08 12:00 UTC" and old["date"] == "2026-10-01 09:00 UTC"


def test_run_rows_skip_broken_and_missing_summaries_and_cope_with_missing_numbers(tmp_path):
    make_run(tmp_path / "20261001-090000_OK")
    (tmp_path / "20261002-090000_BROKEN").mkdir()
    (tmp_path / "20261002-090000_BROKEN" / "summary.json").write_text("{not json")
    (tmp_path / "20261003-090000_NOSUMMARY").mkdir()
    (tmp_path / "20261004-090000_EMPTY").mkdir()
    (tmp_path / "20261004-090000_EMPTY" / "summary.json").write_text("{}")
    (tmp_path / "20261005-090000_THIN").mkdir()
    (tmp_path / "20261005-090000_THIN" / "summary.json").write_text('{"symbols": ["X"]}')
    rows = backtest.run_rows(tmp_path)
    assert [r["id"] for r in rows] == ["20261005-090000_THIN", "20261001-090000_OK"]
    assert rows[0]["trades"] is None and rows[0]["net_r"] is None
    assert backtest.run_rows(tmp_path / "missing") == []


def test_list_page_rows_open_their_results_and_show_net_r(tmp_path):
    make_run(tmp_path / "20261008-120000_XAUUSD", net=-1.5)
    page = text(backtest.page(tmp_path))
    assert "/results/20261008-120000_XAUUSD" in page and "-1.50 R" in page
    assert "Backtest cancelled" not in page


def test_no_job_and_no_runs_says_so(tmp_path):
    assert "No backtest yet" in text(backtest.page(tmp_path))


def test_running_job_wins_over_the_list_and_a_failed_one_stays_visible(tmp_path):
    make_run(tmp_path / "20261008-120000_XAUUSD")
    run = begin()
    assert "bj-cancel" in text(backtest.page(tmp_path))
    run.finished, run.error = True, ValueError("boom")
    assert "boom" in text(backtest.page(tmp_path))  # until the next run starts
    assert bj.current() is not None


def test_a_cancelled_run_closes_the_page_and_shows_the_list_with_a_toast(tmp_path):
    make_run(tmp_path / "20261008-120000_XAUUSD")
    run = begin()
    run.finished, run.cancelled = True, True
    page = text(backtest.page(tmp_path))
    assert "bj-cancel" not in page and "bj-fill" not in page
    assert "Backtest cancelled" in page and "/results/20261008-120000_XAUUSD" in page
    assert bj.current() is None  # the job is gone: the next visit shows the plain list
    assert "Backtest cancelled" not in text(backtest.page(tmp_path))


def test_poll_swaps_in_the_list_once_the_cancel_has_really_stopped(tmp_path):
    run = begin()
    assert backtest.cancel_page(bj.snapshot(bj.current(), now=101.0), tmp_path) is no_update
    run.cancel_called = True  # asked, but still running: the page keeps "Cancelling …"
    assert backtest.cancel_page(bj.snapshot(bj.current(), now=101.0), tmp_path) is no_update
    run.finished, run.cancelled = True, True
    swapped = backtest.cancel_page(bj.snapshot(bj.current(), now=102.0), tmp_path)
    assert "Backtest cancelled" in text(swapped) and bj.current() is None


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
