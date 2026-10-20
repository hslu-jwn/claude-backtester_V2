"""The Full Monte Carlo run of the results page (ui/monte_carlo_job.py): server-side job, one at
a time, progress from the tool's output, report on disk. The tool itself is faked."""

from __future__ import annotations

import time

import pytest
from fakes import FakeProcess, Spawner

from backtester.ui import monte_carlo_job as mj

RUN = "20261008-120000_XAUUSD-GBPUSD"
OTHER = "20261009-090000_NAS100"


@pytest.fixture(autouse=True)
def clean():
    mj.reset()
    yield
    mj.reset()


@pytest.fixture
def results(tmp_path):
    for run in (RUN, OTHER):
        (tmp_path / run).mkdir()
        (tmp_path / run / "trades.csv").write_text("id\n")
        (tmp_path / run / "summary.json").write_text('{"symbols": ["XAUUSD", "GBPUSD"]}')
    return tmp_path


def wait_for(cond, seconds=2.0):
    end = time.monotonic() + seconds
    while time.monotonic() < end and not cond():
        time.sleep(0.01)
    return cond()


def start(results, proc=None, run=RUN, **kw):
    spawn = Spawner(proc or FakeProcess())
    job = mj.start(run, results, spawn=spawn, killer=lambda p: p.kill_tree(), **kw)
    return job, spawn


def write_report(results, run=RUN):
    out = results / "monte_carlo" / run
    out.mkdir(parents=True)
    (out / "report.html").write_text("<html>")
    (out / "summary.json").write_text("{}")


def test_start_runs_the_tool_for_the_run_into_its_report_folder(results):
    _, spawn = start(results, extra_args=("--paths", "0"))
    argv = spawn.calls[0][0]
    assert argv[1:4] == ["-m", "backtester.tools.monte_carlo", "--run"]
    assert argv[4] == RUN
    assert argv[argv.index("--out") + 1] == str(results / "monte_carlo" / RUN)
    assert argv[-2:] == ["--paths", "0"]
    assert mj.is_running() and mj.snapshot(RUN, results)["state"] == "running"


def test_only_one_runs_at_a_time(results):
    start(results)
    with pytest.raises(mj.AlreadyRunning):
        start(results, run=OTHER)
    snap = mj.snapshot(OTHER, results)
    assert snap["state"] == "busy" and RUN in snap["message"]
    assert mj.snapshot(RUN, results)["state"] == "running"


def test_unknown_run_ids_are_refused(results):
    for bad in ("..", "../x", "a/b", "", "missing"):
        with pytest.raises(mj.RunNotFound):
            mj.start(bad, results, spawn=Spawner())
    assert not mj.is_running()


def test_idle_without_a_report_ready_with_one(results):
    snap = mj.snapshot(RUN, results)
    assert snap["state"] == "idle" and snap["href"] is None and not snap["report"]
    write_report(results)
    snap = mj.snapshot(RUN, results)
    assert snap["state"] == "ready" and snap["report"]
    assert snap["href"] == f"/monte-carlo/{RUN}/report.html"


def test_progress_shows_the_kind_that_runs(results):
    proc = FakeProcess([f"run {RUN}: 100 trades\n", "kind B: follow run\n"])
    start(results, proc)
    assert wait_for(lambda: "Kind B" in mj.snapshot(RUN, results)["detail"])


def test_random_paths_show_the_path_count_and_a_percent(results):
    lines = ["kind D: random price paths\n"]
    lines += [f"  XAUUSD path {k}/20: 12 trades\n" for k in (1, 2, 3)]
    start(results, FakeProcess(lines))
    assert wait_for(lambda: "XAUUSD path 3/20" in mj.snapshot(RUN, results)["detail"])
    snap = mj.snapshot(RUN, results)
    assert "Kind D" in snap["detail"] and snap["percent"] == pytest.approx(3 / 40 * 100)


def test_later_kinds_are_named(results):
    lines = [
        "kind D: random price paths\n",
        "kind C: random fills\n",
        "kind A: day reshuffle + FTMO\n",
    ]
    start(results, FakeProcess(lines))
    assert wait_for(lambda: "Kind A" in mj.snapshot(RUN, results)["detail"])
    assert mj.snapshot(RUN, results)["percent"] is None


def test_finished_with_a_report_is_ready_and_a_new_start_is_possible(results):
    proc = FakeProcess()
    job, _ = start(results, proc)
    write_report(results)
    proc.finish(0)
    assert wait_for(lambda: job.finished)
    snap = mj.snapshot(RUN, results)
    assert snap["state"] == "ready" and snap["href"] and not mj.is_running()
    start(results, run=OTHER)
    assert mj.snapshot(OTHER, results)["state"] == "running"


def test_failure_shows_the_last_output_line(results):
    proc = FakeProcess(["Traceback (most recent call last):\n", "ValueError: no data\n"])
    job, _ = start(results, proc)
    assert wait_for(lambda: len(job.lines()) == 2)
    proc.finish(1)
    assert wait_for(lambda: job.finished)
    snap = mj.snapshot(RUN, results)
    assert snap["state"] == "error" and "ValueError: no data" in snap["message"]


def test_cancel_stops_the_process_and_shows_cancelled(results):
    proc = FakeProcess()
    job, _ = start(results, proc)
    assert mj.cancel() is True
    assert proc.killed and wait_for(lambda: job.finished)
    assert mj.snapshot(RUN, results)["state"] == "cancelled"
    assert mj.cancel() is False  # nothing runs now


def test_cancel_keeps_an_older_report_openable(results):
    write_report(results)
    start(results)
    mj.cancel()
    wait_for(lambda: mj.current().finished)
    snap = mj.snapshot(RUN, results)
    assert snap["state"] == "cancelled" and snap["report"] and snap["href"]


def test_elapsed_text_is_shown_while_running(results):
    start(results)
    assert mj.snapshot(RUN, results)["elapsed"].count(":") == 1
