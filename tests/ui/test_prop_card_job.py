"""Background computation of the prop-firm card (ui/prop_card_job.py): cache first, one
process at a time, queued runs wait, errors stay visible. Processes are faked."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
from fakes import FakeProcess, Spawner

from backtester.risk import prop_card as pc
from backtester.ui import prop_card_job as pj

sys.path.insert(0, str(Path(__file__).parents[1] / "risk"))
from test_prop_card import CARD, FAST, write_run


@pytest.fixture(autouse=True)
def clean():
    pj.reset()
    yield
    pj.reset()


def wait_for(cond, seconds=2.0):
    end = time.monotonic() + seconds
    while time.monotonic() < end and not cond():
        time.sleep(0.01)
    return cond()


def req(folder, spawn):
    return pj.request(
        folder, "ftmo_2step", spawn=spawn, killer=lambda p: None, preset=FAST, card=CARD
    )


def test_a_cached_card_is_ready_without_starting_a_process(tmp_path):
    run = write_run(tmp_path / "r1")
    pc.ensure_card(run, "ftmo_2step", FAST, CARD)
    spawn = Spawner()
    status = req(run, spawn)
    assert status["state"] == "ready" and status["card"]["status"] == "ok" and not spawn.calls


def test_without_a_cache_the_card_process_starts_once(tmp_path):
    run = write_run(tmp_path / "r1")
    spawn = Spawner(FakeProcess())
    assert req(run, spawn)["state"] == "running"
    assert req(run, spawn)["state"] == "running"
    argv = spawn.calls[0][0]
    assert argv[1:3] == ["-m", "backtester.risk.prop_card"] and argv[3] == "r1"
    assert "--results-dir" in argv and len(spawn.calls) == 1


def test_a_second_run_waits_while_one_computes(tmp_path):
    a, b = write_run(tmp_path / "a"), write_run(tmp_path / "b")
    first = FakeProcess()
    spawn = Spawner(first, FakeProcess())
    req(a, spawn)
    assert req(b, spawn)["state"] == "queued" and len(spawn.calls) == 1
    first.finish(0)
    assert wait_for(lambda: not pj.busy())
    assert req(b, spawn)["state"] == "running" and len(spawn.calls) == 2


def test_finished_process_gives_the_cached_card(tmp_path):
    run = write_run(tmp_path / "r1")
    proc = FakeProcess()
    spawn = Spawner(proc)
    req(run, spawn)
    pc.ensure_card(run, "ftmo_2step", FAST, CARD)  # what the process would have written
    proc.finish(0)
    assert wait_for(lambda: req(run, spawn)["state"] == "ready")


def test_a_failed_process_shows_its_last_line_and_is_not_restarted(tmp_path):
    run = write_run(tmp_path / "r1")
    proc = FakeProcess(["Traceback\n", "KeyError: boom\n"])
    spawn = Spawner(proc)
    req(run, spawn)
    proc.finish(1)
    assert wait_for(lambda: req(run, spawn)["state"] == "error")
    status = req(run, spawn)
    assert "KeyError: boom" in status["message"] and len(spawn.calls) == 1


def test_a_clean_exit_without_a_card_is_an_error_too(tmp_path):
    run = write_run(tmp_path / "r1")
    proc = FakeProcess()
    spawn = Spawner(proc)
    req(run, spawn)
    proc.finish(0)
    assert wait_for(lambda: req(run, spawn)["state"] == "error")


def test_peek_reads_the_cache_only(tmp_path):
    run = write_run(tmp_path / "r1")
    assert pj.peek(run, "ftmo_2step", preset=FAST, card=CARD) is None
    pc.ensure_card(run, "ftmo_2step", FAST, CARD)
    assert pj.peek(run, "ftmo_2step", preset=FAST, card=CARD)["status"] == "ok"
