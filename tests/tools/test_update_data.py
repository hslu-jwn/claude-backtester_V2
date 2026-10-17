"""The update job: runs a plan with fake backends (ROADMAP 7.5). No terminal, no network."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from datetime import date

import pytest

from backtester.data.update import BINANCE, HISTDATA, MT5, Plan, Skip, Task
from backtester.tools import update_data
from backtester.tools.update_data import Backends, Progress, run_plan

D = date.fromisoformat
TODAY = D("2026-10-17")


def task(source, symbol, first="2026-10-15", last="2026-10-16", months=()):
    return Task(source, symbol, D(first), D(last), months)


def plan_of(*tasks, skipped=()):
    return Plan(TODAY, tuple(tasks), tuple(skipped))


class Recorder:
    """Fake backends that record calls; `fail` = symbols whose download raises."""

    def __init__(self, fail=()):
        self.calls, self.fail, self.sessions = [], set(fail), 0

    def _do(self, label, t):
        if t.symbol in self.fail:
            raise RuntimeError(f"{t.symbol} broke")
        self.calls.append((label, t.symbol))
        return f"{t.first}..{t.last} ok"

    def backends(self):
        @contextmanager
        def mt5():
            self.sessions += 1
            yield lambda t, log: self._do(MT5, t)

        return Backends(
            mt5=mt5,
            binance=lambda t, log, today: self._do(BINANCE, t),
            histdata=lambda t, log: self._do(HISTDATA, t),
        )


@pytest.fixture(autouse=True)
def idle_job():
    update_data.join(5)
    yield
    update_data.join(5)


def test_run_plan_runs_every_task_with_one_mt5_session():
    rec = Recorder()
    progress = Progress()
    plan = plan_of(task(MT5, "NAS100"), task(MT5, "US500"), task(BINANCE, "BTCUSDT"),
                   task(HISTDATA, "XAUUSD"))  # fmt: skip
    run_plan(plan, rec.backends(), progress)
    assert rec.calls == [(MT5, "NAS100"), (MT5, "US500"), (BINANCE, "BTCUSDT"),
                         (HISTDATA, "XAUUSD")]  # fmt: skip
    assert rec.sessions == 1
    s = progress.snapshot()
    assert len(s["done"]) == 4 and s["errors"] == []


def test_an_error_in_one_symbol_still_updates_the_others():
    rec = Recorder(fail={"US500", "BTCUSDT"})
    progress = Progress()
    plan = plan_of(task(MT5, "NAS100"), task(MT5, "US500"), task(MT5, "XAUUSD"),
                   task(BINANCE, "BTCUSDT"), task(BINANCE, "ETHUSDT"))  # fmt: skip
    run_plan(plan, rec.backends(), progress)
    assert [c[1] for c in rec.calls] == ["NAS100", "XAUUSD", "ETHUSDT"]
    s = progress.snapshot()
    assert len(s["done"]) == 3
    assert len(s["errors"]) == 2
    assert any("US500" in e and "broke" in e for e in s["errors"])
    assert any("BTCUSDT" in e for e in s["errors"])


def test_a_terminal_that_cannot_be_opened_is_one_error_and_other_sources_still_run():
    rec = Recorder()

    @contextmanager
    def broken():
        raise ConnectionError("terminal is not running")
        yield

    backends = rec.backends()
    backends = Backends(mt5=broken, binance=backends.binance, histdata=backends.histdata)
    progress = Progress()
    run_plan(plan_of(task(MT5, "NAS100"), task(BINANCE, "BTCUSDT")), backends, progress)
    s = progress.snapshot()
    assert [c[1] for c in rec.calls] == ["BTCUSDT"]
    assert len(s["errors"]) == 1 and "terminal is not running" in s["errors"][0]


def test_progress_line_names_source_symbol_position_and_range():
    seen = []
    progress = Progress()

    @contextmanager
    def mt5():
        yield lambda t, log: seen.append(progress.snapshot()["line"]) or "ok"

    backends = Backends(mt5=mt5, binance=None, histdata=None)
    run_plan(plan_of(task(MT5, "NAS100"), task(MT5, "US500")), backends, progress)
    assert seen == [
        "MT5 NAS100 1/2 · 2026-10-15..2026-10-16",
        "MT5 US500 2/2 · 2026-10-15..2026-10-16",
    ]


def test_progress_state_transitions():
    p = Progress()
    assert p.snapshot() == {
        "running": False,
        "line": "",
        "done": [],
        "errors": [],
        "finished_at": None,
    }
    assert p.begin() is True and p.begin() is False  # a second job cannot start
    p.set_line("MT5 NAS100 1/1")
    p.add_done("MT5 NAS100: ok")
    p.add_error("MT5 US500: broke")
    s = p.snapshot()
    assert s["running"] and s["line"] == "MT5 NAS100 1/1" and s["finished_at"] is None
    p.finish()
    s = p.snapshot()
    assert not s["running"] and s["line"] == "" and s["finished_at"]
    assert s["done"] == ["MT5 NAS100: ok"] and s["errors"] == ["MT5 US500: broke"]
    s["done"].append("x")  # a snapshot is a copy
    assert p.snapshot()["done"] == ["MT5 NAS100: ok"]
    assert p.begin() is True  # a new job starts clean
    assert p.snapshot()["done"] == [] and p.snapshot()["finished_at"] is None


def test_start_background_runs_in_a_thread_and_a_second_start_is_refused():
    release, entered = threading.Event(), threading.Event()
    calls = []

    @contextmanager
    def mt5():
        def download(t, log):
            entered.set()
            release.wait(5)
            calls.append(t.symbol)
            return "ok"

        yield download

    backends = Backends(mt5=mt5, binance=None, histdata=None)
    plan = plan_of(task(MT5, "NAS100"))
    assert update_data.start_background(backends, plan) is True
    assert entered.wait(5)
    assert update_data.state()["running"] is True
    assert update_data.start_background(backends, plan) is False
    release.set()
    update_data.join(5)
    s = update_data.state()
    assert not s["running"] and s["finished_at"] and calls == ["NAS100"]
    assert len(s["done"]) == 1 and s["errors"] == []


def test_a_crash_while_planning_is_reported_and_the_job_ends():
    def boom():
        raise OSError("disk gone")

    assert update_data.start_background(Recorder().backends(), boom) is True
    update_data.join(5)
    s = update_data.state()
    assert not s["running"] and any("disk gone" in e for e in s["errors"])


def test_empty_plan_finishes_with_a_note_and_skipped_symbols_are_listed():
    progress = Progress()
    plan = plan_of(skipped=[Skip(MT5, "US30", "no cache, use the full download tool")])
    run_plan(plan, Recorder().backends(), progress)
    s = progress.snapshot()
    assert any("up to date" in line for line in s["done"])
    assert any("US30" in e for e in s["errors"])  # nothing downloaded for it: shown to the user


def test_format_plan_for_the_dry_run():
    plan = plan_of(task(MT5, "NAS100"), task(HISTDATA, "XAUUSD", months=(D("2026-10-01"),)),
                   skipped=[Skip(BINANCE, "ETHUSDT", "no cache")])  # fmt: skip
    text = update_data.format_plan(plan)
    assert "MT5 NAS100 2026-10-15..2026-10-16" in text
    assert "histdata XAUUSD 2026-10" in text
    assert "skip binance ETHUSDT: no cache" in text
    assert "nothing to do" in update_data.format_plan(plan_of())
