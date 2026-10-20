"""The one backtest running in this server process (ui/backtest_job.py), shown on the Backtest
page. Spec: ROADMAP.md > 7.6. Runs are faked: no data is read."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from backtester.runner import RunSettings
from backtester.strategy.opening_range.config import OpeningRangeConfig
from backtester.ui import backtest_job as bj


class FakeRun:
    def __init__(self):
        self.done = self.total = 0
        self.load_done = self.load_total = 0
        self.folder: Path | None = None
        self.error: Exception | None = None
        self.cancelled = False
        self.finished = False
        self.cancel_called = False

    def cancel(self):
        self.cancel_called = True


@pytest.fixture(autouse=True)
def clean():
    bj.reset()
    yield
    bj.reset()


def begin(run=None, settings=None, now=100.0, preset="Default"):
    run = run or FakeRun()
    job = bj.start(
        ["AUDUSD", "XAUUSD"], date(2026, 9, 2), date(2026, 9, 30), settings, None, preset,
        starter=lambda *a, **k: run, clock=lambda: now,
    )  # fmt: skip
    return job, run


def test_eta_needs_some_progress_and_scales_with_what_is_left():
    assert bj.eta_seconds(0, 1000, 30.0) is None  # nothing done yet
    assert bj.eta_seconds(5, 1000, 30.0) is None  # too little to tell
    assert bj.eta_seconds(250, 1000, 30.0) == pytest.approx(90.0)  # 3x what took 30 s
    assert bj.eta_seconds(1000, 1000, 30.0) == 0.0
    assert bj.eta_seconds(10, 0, 30.0) is None  # total not known yet


def test_durations_read_like_a_clock():
    assert [bj.format_duration(s) for s in (0, 7.4, 65, 3725)] == [
        "0:00",
        "0:07",
        "1:05",
        "1:02:05",
    ]
    assert bj.format_duration(None) == "—"


def test_percent_is_capped_and_zero_while_loading():
    assert bj.percent(250, 1000) == 25.0 and bj.percent(5, 0) == 0.0 and bj.percent(9, 3) == 100.0


def test_errors_read_like_sentences_not_python_reprs():
    assert bj.error_message(KeyError("no doji threshold for BTCUSD: set it")) == (
        "no doji threshold for BTCUSD: set it"  # no quotes around a KeyError's text
    )
    assert bj.error_message(ValueError("XAUUSD: no cached day")) == "XAUUSD: no cached day"
    assert bj.error_message(RuntimeError()) == "RuntimeError"  # empty text: the type


def test_job_remembers_what_runs_and_the_strategy_name():
    job, _ = begin(settings=RunSettings(strategy=OpeningRangeConfig()), preset="Mine")
    snap = bj.snapshot(job, now=100.0)
    assert snap["symbols"] == ["AUDUSD", "XAUUSD"]
    assert snap["days"] == "2026-09-02 → 2026-09-30"
    assert snap["strategy"] == "Strategy 6 · Opening-range breakout" and snap["preset"] == "Mine"


def test_default_settings_are_strategy_1():
    job, _ = begin()
    assert bj.snapshot(job, now=100.0)["strategy"] == "Strategy 1 · Session zone sweep"


def test_snapshot_of_a_running_job_loading_then_running():
    job, run = begin(now=100.0)
    snap = bj.snapshot(job, now=103.0)  # nothing reported yet
    assert snap["state"] == "running" and snap["percent"] == 0.0 and snap["phase"] == "loading"
    assert snap["detail"] == bj.LOADING_TEXT and snap["elapsed"] == "0:03" and snap["eta"] == "—"
    run.load_done, run.load_total = 400, 1000  # phase 1: candles are read
    snap = bj.snapshot(job, now=110.0)
    assert snap["phase"] == "loading" and snap["percent"] == 40.0 and snap["percent_text"] == "40%"
    assert snap["detail"] == bj.LOADING_TEXT and snap["eta"] == "0:15"
    assert snap["cancellable"] is True
    run.load_done = run.load_total
    run.done, run.total = 250, 1000  # phase 2: the run restarts the bar at 0 %
    snap = bj.snapshot(job, now=130.0)
    assert snap["phase"] == "running" and snap["percent"] == 25.0 and snap["percent_text"] == "25%"
    assert snap["detail"] == "Running · phase 2 of 2 · 250 of 1,000 candles"
    assert snap["elapsed"] == "0:30" and snap["eta"] == "1:30"


def test_the_last_step_is_writing_the_results():
    job, run = begin()
    run.done = run.total = 1000
    snap = bj.snapshot(job, now=110.0)
    assert snap["state"] == "running" and snap["detail"] == "Writing results …"
    assert snap["cancellable"] is False  # nothing left to stop


def test_a_finished_job_points_to_its_results_and_keeps_its_final_time():
    job, run = begin(now=100.0)
    run.finished, run.done, run.total = True, 1000, 1000
    run.folder = Path("results/20261008-120000_AUDUSD-XAUUSD")
    snap = bj.snapshot(job, now=150.0)
    assert snap["state"] == "done" and snap["percent"] == 100.0
    assert snap["href"] == "/results/20261008-120000_AUDUSD-XAUUSD"
    later = bj.snapshot(job, now=999.0)  # the clock stops when the run ends
    assert later["elapsed"] == snap["elapsed"] == "0:50"


def test_failed_and_cancelled_jobs():
    job, run = begin()
    run.finished, run.error = True, KeyError("no doji threshold for X")
    snap = bj.snapshot(job, now=101.0)
    assert snap["state"] == "error" and snap["message"] == "no doji threshold for X"
    bj.reset()
    job, run = begin()
    run.finished, run.cancelled = True, True
    snap = bj.snapshot(job, now=101.0)
    assert snap["state"] == "cancelled" and "cancelled" in snap["message"].lower()


def test_only_one_backtest_at_a_time():
    job, run = begin()
    with pytest.raises(bj.JobRunning):
        begin()
    assert bj.current() is job and bj.is_running()
    run.finished = True  # when it is over the next one may start
    assert not bj.is_running()
    second, _ = begin()
    assert bj.current() is second


def test_cancel_stops_the_running_job_only():
    assert bj.cancel() is False  # nothing runs
    job, run = begin()
    assert bj.cancel() is True and run.cancel_called
    snap = bj.snapshot(job, now=101.0)  # still running until the thread reaches its next step
    assert snap["state"] == "running" and snap["detail"] == "Cancelling …"
    assert snap["cancellable"] is False
    run.finished = run.cancelled = True
    assert bj.cancel() is False
