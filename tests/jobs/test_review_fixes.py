"""Regression cases for the V2.6a review; finite children, no external services."""

import http.client
import io
import json
import multiprocessing as mp
import os
import subprocess
import sys
import time
from contextlib import redirect_stdout
from dataclasses import replace
from pathlib import Path

import pytest

from backtester import filelock
from backtester.jobs import storage, temperature
from backtester.jobs.processes import process_identity, terminate_tree
from backtester.jobs.queue import Queue, Runner, RunnerLock, queue_status
from backtester.tools.queue import main


def test_replace_and_read_retry_permission_errors(tmp_path, monkeypatch):
    path = tmp_path / "value.json"
    original = os.replace
    calls = []

    def busy(*args):
        calls.append(1)
        if len(calls) < 3:
            raise PermissionError(5, "sharing violation")
        original(*args)

    monkeypatch.setattr(filelock.os, "replace", busy)
    storage.atomic_json(path, {"value": 1})
    assert len(calls) == 3
    original_open = Path.open
    calls.clear()

    def busy_open(self, *args, **kwargs):
        calls.append(1)
        if len(calls) < 3:
            raise PermissionError(5, "sharing violation")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", busy_open)
    assert storage.read_json(path) == {"value": 1}
    assert len(calls) == 3


def test_permission_retry_is_bounded(tmp_path, monkeypatch):
    now = [0.0]
    monkeypatch.setattr(filelock.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(
        filelock.time, "sleep", lambda seconds: now.__setitem__(0, now[0] + seconds)
    )
    monkeypatch.setattr(filelock.os, "replace", lambda *a: (_ for _ in ()).throw(PermissionError()))
    with pytest.raises(PermissionError):
        storage.atomic_json(tmp_path / "value.json", {})
    assert 4.9 <= now[0] <= 5.1
    assert not list(tmp_path.glob("*.tmp"))


def test_guard_allows_unrelated_live_pid(tmp_path):
    (tmp_path / "runner.lock").write_text(str(os.getpid()))
    with (
        RunnerLock(tmp_path),
        pytest.raises(RuntimeError, match="already running"),
        RunnerLock(tmp_path),
    ):
        pass


def test_start_intent_is_durable_before_popen(tmp_path):
    q = Queue(tmp_path)
    job = q.add(["backtester.tools.research"])

    def crash(*args, **kwargs):
        saved = q.get(job.id)
        assert (saved.state, saved.pid, saved.attempts) == ("running", None, 1)
        assert saved.starting
        raise RuntimeError("injected death before launch")

    r = Runner(q, popen=crash, sensor=lambda: 50, sender=lambda _: None)
    with pytest.raises(RuntimeError, match="injected death"):
        r.tick()
    Runner(q, sensor=lambda: 50, sender=lambda _: None).recover()
    assert (q.get(job.id).state, q.get(job.id).attempts) == ("pending", 1)


def test_failure_saving_launched_pid_cleans_up_child(tmp_path, monkeypatch):
    q = Queue(tmp_path)
    job = q.add(["backtester.tools.research"])
    children = []
    original = q.save

    def fail_pid_save(j):
        if j.pid is not None:
            raise RuntimeError("injected PID save failure")
        original(j)

    def launch(argv, **kwargs):
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(25)"], **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(q, "save", fail_pid_save)
    r = Runner(q, popen=launch, sensor=lambda: 50, sender=lambda _: None)
    try:
        with pytest.raises(RuntimeError, match="PID save failure"):
            r.tick()
        assert children[0].poll() is not None
        saved = q.get(job.id)
        assert (saved.state, saved.pid, saved.attempts) == ("running", None, 1)
    finally:
        for child in children:
            if child.poll() is None:
                terminate_tree(child.pid)
            child.wait(timeout=10)


@pytest.mark.parametrize("bad", ["{", '{"unknown": true}', "[]"])
def test_bad_job_is_skipped_warned_once_and_reported(tmp_path, caplog, bad):
    q = Queue(tmp_path)
    good = q.add(["backtester.tools.research"])
    q.path("broken").write_text(bad)
    assert q.jobs() == [good]
    assert q.jobs() == [good]
    assert sum("broken.json" in record.message for record in caplog.records) == 1
    r = Runner(q, sensor=lambda: 90, sender=lambda _: None)
    r.recover()
    r.tick()
    assert queue_status(q)["broken"] == ["broken.json"]
    with pytest.raises(ValueError, match="Broken job file.*broken.json"):
        q.get("broken")


def test_stale_status_and_reused_pid(tmp_path, capsys):
    q = Queue(tmp_path)
    saved = {"pid": os.getpid(), "updated": "2000-01-01", "paused": True, "temperature": 99}
    storage.atomic_json(tmp_path / "status.json", saved)
    status = queue_status(q)
    assert not status["runner_alive"]
    assert status["temperature"] is None and not status["paused"]
    assert status["last_seen"] == saved
    main(["status"], queue=q)
    text = capsys.readouterr().out
    assert "runner: not running" in text and "last seen 2000-01-01" in text
    with RunnerLock(tmp_path):
        assert queue_status(q)["runner_alive"]


def test_clean_removes_job_lock_and_logs_are_relative(tmp_path):
    q = Queue(tmp_path / "queue")
    job = q.add(["backtester.tools.research"])
    raw = json.loads(q.path(job.id).read_text())
    assert raw["log"] == f"queue/logs/{job.id}.log"
    assert Path(job.log) == q.root / "logs" / f"{job.id}.log"
    q.update(job.id, lambda j: replace(j, state="done", ended="2000-01-01T00:00:00+00:00"))
    assert q.clean(1) == 1
    assert not q.path(job.id).with_suffix(".lock").exists()


def test_new_stop_is_honored_and_old_stop_is_removed(tmp_path):
    q = Queue(tmp_path)
    q.stop()
    r = Runner(q, sensor=lambda: 50, sender=lambda _: None)
    r.run(drain=True)
    assert r.stopping
    assert "stop request" in (tmp_path / "runner.log").read_text().lower()
    # The release is later than this stop request: it is stale for the next runner.
    stop = tmp_path / "stop"
    os.utime(stop, (1, 1))
    r = Runner(q, sensor=lambda: 50, sender=lambda _: None)
    r.run(drain=True)
    assert not r.stopping and not stop.exists()


def test_sensor_timeout_and_http_exception(tmp_path, monkeypatch):
    calls = []

    def broken(url, timeout):
        calls.append(timeout)
        raise http.client.HTTPException("incomplete response")

    monkeypatch.setattr(temperature, "urlopen", broken)
    assert temperature.read_temperature("http://localhost/", timeout=0.25) is None
    r = Runner(Queue(tmp_path), sensor_timeout=0.75, sender=lambda _: None)
    assert r.sensor() is None
    assert calls == [0.25, 0.75]


def read_while_replacing(root, ready, stop):
    q = Queue(Path(root))
    ready.set()
    while not stop.is_set():
        # Keep an actual read handle open across a writer replacement on Windows.
        with storage.retry_permission(
            lambda: (q.root / "status.json").open(encoding="utf-8")
        ) as stream:
            time.sleep(0.002)
            assert isinstance(json.load(stream), dict)
        output = io.StringIO()
        with redirect_stdout(output):
            main(["status", "--json"], queue=q)
        assert json.loads(output.getvalue())["counts"]["pending"] == 1


def test_status_reader_process_while_runner_writes(tmp_path):
    q = Queue(tmp_path)
    q.add(["backtester.tools.research"])
    r = Runner(q, sensor=lambda: 90, sender=lambda _: None)
    r.tick()
    ctx = mp.get_context("spawn")
    ready, stop = ctx.Event(), ctx.Event()
    p = ctx.Process(target=read_while_replacing, args=(str(tmp_path), ready, stop))
    try:
        p.start()
        assert ready.wait(10)
        for _ in range(50):
            r.tick()
            j = q.jobs()[0]
            with q.locked(j.id):
                q.save(j)
        stop.set()
        p.join(10)
        assert p.exitcode == 0
    finally:
        stop.set()
        if p.is_alive():
            p.terminate()
        p.join(10)


def test_cancel_real_child_and_grandchild(tmp_path):
    q = Queue(tmp_path)
    job = q.add(["backtester.tools.research"])
    marker = tmp_path / "grandchild.pid"
    children = []

    def launch(argv, **kwargs):
        code = (
            "import subprocess,sys,time,pathlib; "
            "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(25)']); "
            f"pathlib.Path({str(marker)!r}).write_text(str(p.pid)); time.sleep(25)"
        )
        child = subprocess.Popen([sys.executable, "-c", code], **kwargs)
        children.append(child)
        return child

    r = Runner(q, popen=launch, sensor=lambda: 50, sender=lambda _: None)
    grandchild = None
    try:
        r.tick()
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        grandchild = int(marker.read_text())
        q.cancel(job.id)
        children[0].wait(timeout=10)
        deadline = time.monotonic() + 5
        while process_identity(grandchild) is not None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert process_identity(grandchild) is None
        assert process_identity(children[0].pid) is None
    finally:
        for child in children:
            if child.poll() is None:
                terminate_tree(child.pid)
            child.wait(timeout=10)
        if grandchild and process_identity(grandchild) is not None:
            if os.name == "nt":
                terminate_tree(grandchild)
            else:
                import signal

                os.kill(grandchild, signal.SIGKILL)
