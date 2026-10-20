"""Background child process of the UI (ui/process_job.py): output lines, finish, cancel."""

from __future__ import annotations

import time

from fakes import FakeProcess, Spawner

from backtester.ui import process_job as pj


def wait_for(cond, seconds=2.0):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if cond():
            return True
        time.sleep(0.01)
    return cond()


def test_lines_are_collected_and_the_job_finishes_with_the_exit_code():
    proc = FakeProcess(["kind C: random fills\n", "\n", "kind A: x\n"])
    spawn = Spawner(proc)
    job = pj.ProcessJob.start(["python", "-m", "x"], spawn=spawn, killer=lambda p: None)
    assert spawn.calls[0][0] == ["python", "-m", "x"]
    assert spawn.calls[0][1]["env"]["PYTHONUNBUFFERED"] == "1"
    assert wait_for(lambda: len(job.lines()) == 2)
    assert job.lines() == ["kind C: random fills", "kind A: x"] and not job.finished
    proc.finish(0)
    assert wait_for(lambda: job.finished) and job.returncode == 0


def test_cancel_kills_the_whole_process_tree_once():
    proc = FakeProcess()
    killed = []
    job = pj.ProcessJob.start(
        ["x"], spawn=Spawner(proc), killer=lambda p: (killed.append(p), proc.finish(1))
    )
    job.cancel()
    job.cancel()
    assert killed == [proc] and job.cancel_requested
    assert wait_for(lambda: job.finished)


def test_only_the_last_lines_are_kept():
    proc = FakeProcess([f"line {i}\n" for i in range(pj.KEEP_LINES + 50)], returncode=0)
    job = pj.ProcessJob.start(["x"], spawn=Spawner(proc), killer=lambda p: None)
    assert wait_for(lambda: job.lines() and job.lines()[-1] == f"line {pj.KEEP_LINES + 49}")
    assert len(job.lines()) == pj.KEEP_LINES


def test_elapsed_counts_from_the_start_and_stops_at_the_finish():
    proc = FakeProcess()
    job = pj.ProcessJob.start(["x"], spawn=Spawner(proc), killer=lambda p: None, clock=lambda: 10.0)
    assert job.elapsed(now=14.0) == 4.0
    proc.finish(0)
    assert wait_for(lambda: job.finished)
    assert job.elapsed(now=99.0) == 0.0 or job.elapsed(now=99.0) == job.elapsed(now=500.0)
