import json
import multiprocessing as mp
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from backtester.jobs.queue import Queue, Runner, RunnerLock, process_identity
from backtester.jobs.temperature import TemperatureGuard, parse_temperature, read_temperature


def acquire_worker(root, ready, release, output):
    try:
        with RunnerLock(Path(root)):
            output.put(True)
            ready.set()
            release.wait(5)
    except RuntimeError:
        output.put(False)


def test_roundtrip_order_validation_and_retry(tmp_path):
    q = Queue(tmp_path)
    a = q.add(["backtester.tools.research", "a"])
    b = q.add(["backtester.tools.research", "b"], priority=3)
    assert q.get(a.id) == a
    assert [j.id for j in q.pending()] == [b.id, a.id]
    assert not list(tmp_path.rglob("*.tmp"))
    for argv in ([], ["os"], ["backtester."], ["backtester.x;bad"], ["-c"]):
        with pytest.raises(ValueError):
            q.add(argv)
    with pytest.warns(UserWarning, match="same argv"):
        q.add(a.argv)
    q.cancel(a.id)
    assert q.get(a.id).state == "cancelled"
    assert q.retry(a.id).attempts == 0
    assert q.get(a.id).state == "pending"


def test_atomic_failure_preserves_old_job(tmp_path, monkeypatch):
    from backtester.jobs import storage

    q = Queue(tmp_path)
    job = q.add(["backtester.tools.research"])
    monkeypatch.setattr(storage.os, "replace", lambda *a: (_ for _ in ()).throw(OSError("disk")))
    with pytest.raises(OSError):
        q.update(job.id, lambda j: replace(j, state="failed"))
    assert q.get(job.id).state == "pending"
    assert not list(tmp_path.rglob("*.tmp"))


class Child:
    next_pid = 900000

    def __init__(self, code=None):
        self.code = code
        self.pid = Child.next_pid
        Child.next_pid += 1

    def poll(self):
        return self.code


def rig(tmp_path, **kwargs):
    children = []

    def launch(argv, **opts):
        assert argv[:2] == [sys.executable, "-m"]
        assert opts["cwd"].is_absolute()
        assert opts["stderr"] == subprocess.STDOUT
        child = Child()
        children.append(child)
        return child

    runner = Runner(
        Queue(tmp_path), popen=launch, sensor=lambda: 72, sender=lambda s: None, **kwargs
    )
    return runner, children


def test_capacity_completion_retry_failure(tmp_path):
    sent = []
    r, children = rig(tmp_path, workers=1)
    r.sender = sent.append
    a = r.queue.add(["backtester.tools.research", "a"])
    b = r.queue.add(["backtester.tools.research", "b"])
    r.tick()
    assert len(children) == 1
    children[0].code = 0
    r.tick()
    assert r.queue.get(a.id).state == "done"
    assert len(children) == 2
    children[1].code = 1
    r.tick()
    assert len(children) == 3
    children[2].code = 1
    r.tick()
    failed = r.queue.get(b.id)
    assert (failed.state, failed.attempts, failed.exit_code) == ("failed", 2, 1)
    assert len(sent) == 1 and "failed" in sent[0]
    assert json.loads((tmp_path / "status.json").read_text())["counts"]["failed"] == 1


def test_stop_drains_and_cancel_wins(tmp_path, monkeypatch):
    r, children = rig(tmp_path, workers=1)
    a = r.queue.add(["backtester.tools.research", "a"])
    b = r.queue.add(["backtester.tools.research", "b"])
    r.tick()
    import backtester.jobs.queue as queue_module

    monkeypatch.setattr(queue_module, "process_identity", lambda pid: 1.0)
    r.queue.update(a.id, lambda j: replace(j, process_started=1.0))
    killed = []
    r.queue.cancel(a.id, terminate=killed.append)
    assert killed == [children[0].pid]
    r.queue.stop()
    children[0].code = 1
    r.tick()
    assert r.queue.get(a.id).state == "cancelled"
    assert r.queue.get(b.id).state == "pending"
    assert r.stopping and not r.active


def test_recovery_dead_surviving_and_exhausted(tmp_path):
    r, _ = rig(tmp_path)
    for i in range(3):
        j = r.queue.add(["backtester.tools.research", str(i)])
        r.queue.update(
            j.id,
            lambda j, i=i: replace(
                j, state="running", pid=100 + i, process_started=1.0, attempts=2 if i == 2 else 1
            ),
        )
    r.identity = lambda pid: 1.0 if pid == 101 else None
    r.recover()
    jobs = r.queue.jobs()
    assert [j.state for j in jobs] == ["pending", "running", "failed"]
    r.stopping = True
    r.tick()
    assert r.queue.get(jobs[1].id).state == "running"
    r.identity = lambda pid: None
    r.tick()
    assert r.queue.get(jobs[1].id).state == "pending"


def test_reused_pid_is_recovered(tmp_path):
    r, _ = rig(tmp_path)
    j = r.queue.add(["backtester.tools.research"])
    r.queue.update(
        j.id, lambda j: replace(j, state="running", pid=123, process_started=10.0, attempts=1)
    )
    r.identity = lambda pid: 20.0
    r.recover()
    assert r.queue.get(j.id).state == "pending"


def test_runner_lock_stale_live_and_race(tmp_path):
    tmp_path.joinpath("runner.lock").write_text("99999999")
    with RunnerLock(tmp_path), pytest.raises(RuntimeError, match="runner"), RunnerLock(tmp_path):
        pass
    ctx = mp.get_context("spawn")
    ready, release, output = ctx.Event(), ctx.Event(), ctx.Queue()
    workers = [
        ctx.Process(target=acquire_worker, args=(str(tmp_path), ready, release, output))
        for _ in range(2)
    ]
    try:
        for p in workers:
            p.start()
        assert ready.wait(10)
        results = [output.get(timeout=10) for _ in workers]
        assert sorted(results) == [False, True]
    finally:
        release.set()
        for p in workers:
            p.join(10)
            if p.is_alive():
                p.terminate()
                p.join()
    assert all(p.exitcode == 0 for p in workers)


def sensor_tree(value="72,5 °C"):
    return {
        "Text": "root",
        "Children": [
            {
                "Text": "GPU",
                "ImageURL": "images/nvidia.png",
                "Children": [{"Text": "Package", "Value": "99 °C"}],
            },
            {
                "Text": "AMD Ryzen",
                "ImageURL": "images/cpu.png",
                "Children": [
                    {
                        "Text": "Temperatures",
                        "Children": [
                            {"Text": "CPU Package", "Value": value},
                            {"Text": "Core Max", "Value": "70.0 °C"},
                        ],
                    }
                ],
            },
        ],
    }


def test_temperature_parse_and_timeout(monkeypatch):
    assert parse_temperature(sensor_tree()) == 72.5
    assert parse_temperature({"Text": "GPU", "Children": []}) is None
    from backtester.jobs import temperature

    def timeout(url, timeout):
        assert timeout == 2
        raise TimeoutError()

    monkeypatch.setattr(temperature, "urlopen", timeout)
    assert read_temperature("http://localhost:8085/data.json") is None


def test_hysteresis_unreadable_and_telegram(tmp_path):
    now = [0.0]
    r, _ = rig(tmp_path, clock=lambda: now[0])
    messages = []
    r.sender = messages.append
    r.queue.add(["backtester.tools.research"])
    r.sensor = lambda: 85
    r.tick()
    assert r.guard.paused and not r.active
    now[0] = 1801
    r.tick()
    r.tick()
    assert len(messages) == 1 and "paused" in messages[0]
    r.sensor = lambda: 83
    r.tick()
    assert r.guard.paused
    r.sensor = lambda: None
    r.tick()
    r.tick()
    assert not r.guard.paused and r.active
    assert r.status()["warning"]
    assert (tmp_path / "runner.log").read_text().count("temperature unavailable") == 1
    r.sensor = lambda: 80
    r.tick()
    assert r.status()["warning"] is None
    g = TemperatureGuard(85, 80)
    assert g.update(85) and g.update(81) and not g.update(80)


def test_crash_notification_and_sender_error(tmp_path):
    r, _ = rig(tmp_path)
    messages = []
    r.sender = messages.append
    r.tick = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    with pytest.raises(RuntimeError, match="boom"):
        r.run(drain=True)
    assert len(messages) == 1 and "crashed" in messages[0]
    r.sender = lambda text: (_ for _ in ()).throw(OSError("send"))
    r.notify("test")  # never propagate sender errors


def test_real_short_child_is_reaped(tmp_path):
    # Queue only accepts repository modules; injected launch runs a harmless finite fixture.
    def launch(argv, **kwargs):
        return subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(0)"], **kwargs)

    q = Queue(tmp_path)
    j = q.add(["backtester.tools.research"])
    r = Runner(q, popen=launch, sensor=lambda: 50, sender=lambda s: None, poll=0.01)
    r.run(drain=True)
    assert q.get(j.id).state == "done"
    assert process_identity(os.getpid()) is not None


def cancel_race(root, ready):
    q = Queue(Path(root))
    j = q.jobs()[0]
    ready.wait(10)
    q.cancel(j.id)


def test_runner_update_serializes_with_cancel(tmp_path):
    q = Queue(tmp_path)
    j = q.add(["backtester.tools.research"])
    ctx = mp.get_context("spawn")
    ready = ctx.Event()
    p = ctx.Process(target=cancel_race, args=(str(tmp_path), ready))
    p.start()
    try:
        with q.locked(j.id):
            ready.set()
            q.save(replace(q.get(j.id), state="running", attempts=1))
        p.join(10)
        assert p.exitcode == 0
        assert (q.get(j.id).state, q.get(j.id).attempts) == ("cancelled", 1)
    finally:
        if p.is_alive():
            p.terminate()
            p.join()


def test_cli_commands_and_clean(tmp_path, capsys):
    from backtester.tools.queue import main

    q = Queue(tmp_path)
    main(
        ["add", "--name", "orb", "--priority", "4", "--", "backtester.tools.research", "g"], queue=q
    )
    a = q.jobs()[0]
    assert a.priority == 4 and a.name == "orb"
    main(["add-grid", "grid.toml", "--dev-only", "--retest"], queue=q)
    assert q.jobs()[1].argv == [
        "backtester.tools.research",
        "grid.toml",
        "--workers",
        "1",
        "--retest",
        "--dev-only",
    ]
    capsys.readouterr()
    main(["status", "--json"], queue=q)
    assert json.loads(capsys.readouterr().out)["counts"]["pending"] == 2
    main(["cancel", a.id], queue=q)
    main(["retry", a.id], queue=q)
    assert q.get(a.id).state == "pending"
    main(["stop"], queue=q)
    assert (tmp_path / "stop").exists()
    q.update(a.id, lambda j: replace(j, state="done", ended="2000-01-01T00:00:00+00:00"))
    main(["clean", "--done-older-than", "1"], queue=q)
    assert len(q.jobs()) == 1


def test_telegram_without_configuration(monkeypatch):
    # Replace the integration module entirely: no credential store is read by this test.
    import types

    from backtester.jobs.queue import telegram_sender

    fake = types.ModuleType("backtester.live.telegram")
    fake.load_telegram = lambda: None
    fake.TelegramClient = lambda cfg: pytest.fail("no config must skip send")
    monkeypatch.setitem(sys.modules, "backtester.live.telegram", fake)
    telegram_sender("test")


def test_temperature_variants_and_validation():
    for name in ("CPU Package", "CPU (Tctl/Tdie)", "Core Max"):
        tree = sensor_tree("88.5 °C")
        tree["Children"][1]["Children"][0]["Children"][0]["Text"] = name
        assert parse_temperature(tree) == 88.5
    with pytest.raises(ValueError):
        TemperatureGuard(80, 85)
    with pytest.raises(ValueError):
        TemperatureGuard(float("nan"), 80)


def test_stop_waits_for_running_child(tmp_path):
    r, children = rig(tmp_path)
    r.queue.add(["backtester.tools.research"])
    r.tick()
    r.queue.stop()
    r.tick()
    assert r.stopping and r.active
    children[0].code = 0
    r.tick()
    assert not r.active


def test_lock_timeout(tmp_path):
    from backtester.jobs.storage import file_lock

    with (
        file_lock(tmp_path / "lock"),
        pytest.raises(TimeoutError, match="Timed out acquiring"),
        file_lock(tmp_path / "lock", timeout=0.01),
    ):
        pass


def test_defaults_are_frozen():
    from dataclasses import FrozenInstanceError

    from backtester.jobs.config import DEFAULT_CONFIG

    assert DEFAULT_CONFIG.workers == 8
    with pytest.raises(FrozenInstanceError):
        DEFAULT_CONFIG.workers = 10


def test_launch_failure_consumes_attempts(tmp_path):
    r, _ = rig(tmp_path)
    j = r.queue.add(["backtester.tools.research"])
    r.popen = lambda *a, **kw: (_ for _ in ()).throw(OSError("cannot start"))
    r.tick()
    assert r.queue.get(j.id).attempts == 1
    r.tick()
    assert r.queue.get(j.id).state == "failed"


def test_recovered_survivor_exhausts_attempts(tmp_path):
    r, _ = rig(tmp_path)
    sent = []
    r.sender = sent.append
    j = r.queue.add(["backtester.tools.research"], max_attempts=1)
    r.queue.update(
        j.id, lambda j: replace(j, state="running", attempts=1, pid=123, process_started=1.0)
    )
    r.identity = lambda pid: 1.0
    r.recover()
    assert j.id in r.active
    r.identity = lambda pid: None
    r.tick()
    assert r.queue.get(j.id).state == "failed"
    assert len(sent) == 1


def test_no_notifications_for_success_or_brief_pause(tmp_path):
    r, children = rig(tmp_path)
    sent = []
    r.sender = sent.append
    r.queue.add(["backtester.tools.research"])
    r.sensor = lambda: 90
    r.tick()
    r.sensor = lambda: 70
    r.tick()
    children[0].code = 0
    r.tick()
    assert not sent


def test_native_process_identity(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "psutil", None)
    assert process_identity(os.getpid()) is not None
    assert process_identity(99999999) is None


def test_terminate_tree_command(monkeypatch):
    from backtester.jobs import processes

    calls = []
    if os.name == "nt":
        monkeypatch.setattr(processes.subprocess, "run", lambda argv, **kw: calls.append(argv))
        processes.terminate_tree(123)
        assert calls == [["taskkill", "/T", "/F", "/PID", "123"]]
    else:
        import signal

        monkeypatch.setattr(processes.os, "killpg", lambda pid, sig: calls.append((pid, sig)))
        processes.terminate_tree(123)
        assert calls == [(123, signal.SIGKILL)]


def test_stop_during_launch_prevents_next_launch(tmp_path):
    r, children = rig(tmp_path)
    r.queue.add(["backtester.tools.research", "a"])
    r.queue.add(["backtester.tools.research", "b"])
    original = r.popen

    def launch(*args, **kwargs):
        child = original(*args, **kwargs)
        r.stopping = True  # the SIGINT handler does exactly this
        return child

    r.popen = launch
    r.tick()
    assert len(children) == 1
    assert len(r.queue.pending()) == 1


def test_child_output_appended_across_retries(tmp_path):
    def launch(argv, **kwargs):
        return subprocess.Popen(
            [
                sys.executable,
                "-c",
                'import sys; print("out"); print("err", file=sys.stderr); sys.exit(1)',
            ],
            **kwargs,
        )

    q = Queue(tmp_path)
    j = q.add(["backtester.tools.research"])
    sent = []
    Runner(q, popen=launch, sensor=lambda: 50, sender=sent.append, poll=0.01).run(drain=True)
    assert q.get(j.id).state == "failed"
    output = Path(j.log).read_text()
    assert output.count("out") == 2 and output.count("err") == 2
    assert len(sent) == 1


def test_only_one_notification_per_thermal_pause(tmp_path):
    now = [0.0]
    r, _ = rig(tmp_path, clock=lambda: now[0])
    sent = []
    r.sender = sent.append
    r.sensor = lambda: 90
    j = r.queue.add(["backtester.tools.research", "a"])
    r.tick()
    now[0] = 1801
    r.tick()
    r.queue.cancel(j.id)
    r.tick()
    r.queue.add(["backtester.tools.research", "b"])
    r.tick()
    now[0] = 3602
    r.tick()
    assert len(sent) == 1
