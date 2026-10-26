"""Queue panel of the Research page (ui/queue_model.py, ui/queue_panel.py) and the pipeline
state on the research cards. Spec: briefs/v26c-cards-lanes.md section C, test cases C1-C25
(briefs/v26c-test-cases.md). A real `Queue` in tmp_path (job files only, nothing is run); the
runner is never started: Start gets a fake spawner, Stop / Cancel / Retry a fake queue."""

from __future__ import annotations

import json
import subprocess
import warnings
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from backtester.jobs.queue import Queue
from backtester.ui import queue_model as qm
from backtester.ui import queue_panel
from backtester.ui.pages import research

PIPELINE = "backtester.tools.research_pipeline"
GRID = """
strategy = "opening_range"
symbols = ["US500"]

[base]
entry_mode = "range"

[grid]
range_minutes = [5, 15]
"""
ALIVE = {"runner_alive": True, "counts": {}, "temperature": 61.5, "paused": False}
DEAD = {"runner_alive": False, "counts": {}, "temperature": None, "paused": False}


def _json(component) -> str:
    return json.dumps(component, default=lambda o: o.to_plotly_json())


class FakeQueue:
    """Records cancel / retry / stop; raises what `errors` says."""

    def __init__(self, tmp_path, errors=None):
        self.root = tmp_path / "queue"
        self.home = tmp_path
        self.calls = []
        self.errors = errors or {}
        self.broken = []

    def _call(self, name, *args):
        self.calls.append((name, *args))
        if name in self.errors:
            raise self.errors[name]

    def cancel(self, job_id):
        self._call("cancel", job_id)

    def retry(self, job_id):
        self._call("retry", job_id)

    def stop(self):
        self._call("stop")

    def jobs(self):
        return []


class Spawner:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def __call__(self, argv, cwd, log_path):
        self.calls.append((list(argv), cwd, log_path))
        if self.error:
            raise self.error


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


@pytest.fixture
def results(tmp_path):
    return tmp_path / "results"


@pytest.fixture
def queue(results, tmp_path):
    return Queue(root=results / "queue", home=tmp_path)


@pytest.fixture
def grids(tmp_path):
    folder = tmp_path / "research" / "grids"
    folder.mkdir(parents=True)
    (folder / "orb.toml").write_text(GRID, encoding="utf-8")
    (folder / "a_grid.toml").write_text(GRID, encoding="utf-8")
    (folder / "notes.txt").write_text("x", encoding="utf-8")
    return folder


def make_ops(queue, status=DEAD, **kwargs):
    return qm.QueueOps(queue, status=lambda _q: dict(status), **kwargs)


def add_job(queue, state="pending", name=None, argv=None, **changes):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # the duplicate-argv warning is not under test here
        job = queue.add(argv or [PIPELINE, "research/grids/orb.toml"], name=name)
    if state != "pending" or changes:
        job = queue.update(job.id, lambda j: replace(j, state=state, **changes))
    return job


def iso(seconds_ago):
    return (datetime.now(UTC) - timedelta(seconds=seconds_ago)).isoformat()


# --- C1, C2, C4: layout --------------------------------------------------------------------


def test_layout_empty_queue(queue, grids):
    text = _json(queue_panel.layout(make_ops(queue, grids_dir=grids)))
    assert "No jobs." in text and "no sensor" in text
    for key in ("qp-keys", "qp-start", "qp-stop", "qp-grid", "qp-queue-grid", "qp-jobs"):
        assert key in text
    assert '"interval": 5000' in text and "qp-interval" in text
    ids = _components(queue_panel.layout(make_ops(queue, grids_dir=grids)))
    assert ids["qp-start"].disabled is False and ids["qp-stop"].disabled is True


def _components(root):
    found = {}

    def walk(node):
        node_id = getattr(node, "id", None)
        if isinstance(node_id, str):
            found[node_id] = node
        children = getattr(node, "children", None)
        for child in children if isinstance(children, list) else [children]:
            if hasattr(child, "to_plotly_json"):
                walk(child)

    walk(root)
    return found


def test_layout_with_all_job_states(queue, tmp_path):
    pending = add_job(queue, "pending", name="pending one")
    running = add_job(queue, "running", name="running one", started=iso(125), attempts=1)
    done = add_job(queue, "done", name="done one", started=iso(100), ended=iso(40), attempts=1)
    failed = add_job(queue, "failed", name="failed one", exit_code=3, attempts=2)
    cancelled = add_job(queue, "cancelled", name="cancelled one")
    text = _json(queue_panel.layout(make_ops(queue)))
    for name in ("pending one", "running one", "done one", "failed one", "cancelled one"):
        assert name in text
    for state in ("pending", "running", "done", "failed", "cancelled"):
        assert f"qp-chip qp-{state}" in text
    assert "1 / 2" in text and "2 / 2" in text and "1m 00s" in text  # attempts, done elapsed
    buttons = {(b, j.id) for b in ("qp-cancel", "qp-retry") for j in (pending, running, done, failed, cancelled)
               if f'"type": "{b}", "job": "{j.id}"' in text}  # fmt: skip
    assert buttons == {
        ("qp-cancel", pending.id), ("qp-cancel", running.id),
        ("qp-retry", failed.id), ("qp-retry", cancelled.id),
    }  # fmt: skip
    assert '"open": false' in text and "no log yet" in text  # the log is in a closed details


def test_runner_alive_disables_start_and_enables_stop(queue):
    alive = _components(queue_panel.layout(make_ops(queue, ALIVE)))
    assert alive["qp-start"].disabled is True and alive["qp-stop"].disabled is False
    dead = _components(queue_panel.layout(make_ops(queue, DEAD)))
    assert dead["qp-start"].disabled is False and dead["qp-stop"].disabled is True


def test_start_disabled_while_a_runner_is_starting(queue, tmp_path):
    clock = Clock()
    ops = make_ops(queue, spawner=Spawner(), clock=clock)
    ops.start()
    assert queue_panel.view(ops)["start_disabled"] is True
    clock.now += qm.START_GRACE + 1
    assert queue_panel.view(ops)["start_disabled"] is False


# --- C3: key strip -------------------------------------------------------------------------


def key_values(status, broken=()):
    snap = qm.snapshot(qm.QueueOps(FakeQueue(Path("x")), status=lambda _q: status))
    snap["broken"] = list(broken)
    return {i["label"]: i["value"] for i in qm.key_items(snap)}


def test_key_strip_values():
    counts = {"pending": 2, "running": 1, "done": 5, "failed": 3, "cancelled": 4}
    got = key_values({**ALIVE, "counts": counts, "paused": True, "stopping": False})
    assert got == {
        "Pending": 2, "Running": 1, "Done": 5, "Failed": 3, "CPU": "61.5 °C",
        "Paused": "yes", "Runner": "yes",
    }  # fmt: skip
    none = key_values({**DEAD, "counts": {}})
    assert none["Pending"] == none["Failed"] == 0
    assert none["CPU"] == "no sensor" and none["Paused"] == "no" and none["Runner"] == "no"
    assert key_values({**ALIVE, "stopping": True})["Runner"] == "stopping"


def test_broken_job_file_is_named_and_the_rest_renders(queue):
    add_job(queue, "done", name="fine job")
    (queue.root / "jobs" / "bad.json").write_text("{nope", encoding="utf-8")
    state = queue_panel.view(make_ops(queue))
    text = _json(state["keys"]) + _json(state["jobs"])
    assert "bad.json" in text and "fine job" in text


# --- C5-C8: start --------------------------------------------------------------------------


def test_start_calls_the_spawner_once(queue, tmp_path):
    spawner = Spawner()
    ops = make_ops(queue, spawner=spawner)
    message = ops.start()
    assert len(spawner.calls) == 1
    argv, cwd, log = spawner.calls[0]
    assert argv[1:] == ["-m", "backtester.tools.queue", "run", "--workers", "8"]
    assert cwd == queue.home and log == queue.root / "runner.out.log"
    assert "started" in message


def test_start_refused_while_a_runner_is_alive(queue):
    spawner = Spawner()
    message = make_ops(queue, ALIVE, spawner=spawner).start()
    assert spawner.calls == [] and "already running" in message


def test_second_quick_start_does_not_spawn_again(queue):
    clock, spawner = Clock(), Spawner()
    ops = make_ops(queue, spawner=spawner, clock=clock)
    ops.start()
    clock.now += 2
    assert "just started" in ops.start()
    assert len(spawner.calls) == 1
    clock.now += qm.START_GRACE
    ops.start()  # still no runner after the grace period: asking again is allowed
    assert len(spawner.calls) == 2


def test_spawner_failure_is_a_message(queue):
    spawner = Spawner(error=OSError("no python"))
    ops = make_ops(queue, spawner=spawner)
    assert "Could not start the runner: no python" in ops.start()
    assert not ops.starting()  # nothing was started, a new try is allowed at once


# --- C9: the real spawner ------------------------------------------------------------------


def test_spawn_detached_is_detached(tmp_path):
    seen = {}

    def popen(argv, **kwargs):
        seen["argv"], seen["kwargs"] = argv, kwargs
        return "process"

    log = tmp_path / "q" / "runner.out.log"
    assert qm.spawn_detached(["py", "-m", "x"], tmp_path, log, popen=popen) == "process"
    kwargs = seen["kwargs"]
    assert kwargs["stdin"] is subprocess.DEVNULL and kwargs["stderr"] is subprocess.STDOUT
    assert kwargs["stdout"] is not subprocess.PIPE and kwargs["cwd"] == tmp_path
    assert kwargs["close_fds"] is True and log.parent.is_dir()
    if qm.os.name == "nt":
        flags = kwargs["creationflags"]
        assert flags & qm.CREATE_NEW_PROCESS_GROUP and flags & qm.CREATE_NO_WINDOW
    else:
        assert kwargs["start_new_session"] is True


# --- C10, C11: stop, cancel, retry ---------------------------------------------------------


def test_stop_calls_the_queue_only_with_a_runner(tmp_path):
    fake = FakeQueue(tmp_path)
    assert "Stop requested" in make_ops(fake, ALIVE).stop()
    assert fake.calls == [("stop",)]
    fake = FakeQueue(tmp_path)
    assert "nothing to stop" in make_ops(fake, DEAD).stop()
    assert fake.calls == []  # a stale stop file would stop the next runner


def test_cancel_and_retry_call_the_queue(tmp_path):
    fake = FakeQueue(tmp_path)
    ops = make_ops(fake)
    assert "Cancelled" in ops.cancel("job_1")
    assert "Queued again" in ops.retry("job_2")
    assert fake.calls == [("cancel", "job_1"), ("retry", "job_2")]


def test_queue_errors_become_messages(tmp_path):
    fake = FakeQueue(
        tmp_path, errors={"cancel": ValueError("Only pending/running jobs can be cancelled"),
                          "retry": ValueError("Cancelled child is still exiting")},
    )  # fmt: skip
    ops = make_ops(fake)
    assert "Only pending/running" in ops.cancel("a")
    assert "still exiting" in ops.retry("b")


def test_bad_job_ids_are_refused(tmp_path):
    fake = FakeQueue(tmp_path)
    ops = make_ops(fake)
    for bad in ("../x", "a b", "", None, 5):
        assert "Not a job id" in ops.cancel(bad) and "Not a job id" in ops.retry(bad)
    assert fake.calls == []


def test_real_queue_cancel_and_retry(queue):
    job = add_job(queue, "pending")
    ops = make_ops(queue)
    assert "Cancelled" in ops.cancel(job.id) and queue.get(job.id).state == "cancelled"
    assert "Queued again" in ops.retry(job.id) and queue.get(job.id).state == "pending"
    assert "failed" in ops.retry(job.id)  # a pending job cannot be retried: message only


# --- C12-C15: queue a grid, no retest ------------------------------------------------------


def test_queue_grid_calls_add_grid_without_retest(queue, grids):
    calls = []

    def fake_add_grid(q, toml, **kwargs):
        calls.append((q, toml, kwargs))
        return replace(add_job(queue), id="job_x")

    ops = make_ops(queue, grids_dir=grids, add_grid_fn=fake_add_grid)
    value = ops.grids()[0]["value"]
    message = ops.queue_grid(value)
    assert len(calls) == 1 and calls[0][0] is queue and calls[0][1] == value
    assert calls[0][2] == {}  # no retest, no dev_only, no cwd
    assert "Queued" in message and "job_x" in message


def test_queue_grid_adds_the_pipeline_job(queue, grids):
    ops = make_ops(queue, grids_dir=grids)
    value = next(o["value"] for o in ops.grids() if o["label"] == "orb.toml")
    ops.queue_grid(value)
    (job,) = queue.jobs()
    assert job.argv == [PIPELINE, value] and job.name == "pipeline orb" and job.cwd is None


def test_queue_grid_refuses_other_paths_and_empty(queue, grids, tmp_path):
    calls = []
    ops = make_ops(queue, grids_dir=grids, add_grid_fn=lambda *a, **k: calls.append(a))
    outside = tmp_path / "other.toml"
    outside.write_text(GRID, encoding="utf-8")
    for bad in (str(outside), "../other.toml", "research/grids/../../other.toml", "orb.toml"):
        assert "not in research/grids" in ops.queue_grid(bad)
    assert "Choose a grid" in ops.queue_grid(None) and "Choose a grid" in ops.queue_grid("")
    assert calls == []


def test_duplicate_grid_warns_in_the_message_but_queues(queue, grids):
    ops = make_ops(queue, grids_dir=grids)
    value = ops.grids()[0]["value"]
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # the duplicate warning must not escape into the page
        ops.queue_grid(value)
        message = ops.queue_grid(value)
    assert "already pending or running" in message and len(queue.jobs()) == 2


def test_add_grid_errors_become_messages(queue, grids):
    def boom(*_a, **_k):
        raise ValueError("bad")

    ops = make_ops(queue, grids_dir=grids, add_grid_fn=boom)
    assert "Could not queue the grid: bad" in ops.queue_grid(ops.grids()[0]["value"])


def test_no_retest_anywhere_in_the_panel(queue, grids):
    text = _json(queue_panel.layout(make_ops(queue, grids_dir=grids))).lower()
    assert "retest" not in text
    assert "retest" not in Path(queue_panel.__file__).read_text(encoding="utf-8").lower()


def test_grid_dropdown_options(queue, grids, tmp_path):
    options = make_ops(queue, grids_dir=grids).grids()
    assert [o["label"] for o in options] == ["a_grid.toml", "orb.toml"]
    assert [o["value"] for o in options] == [
        "research/grids/a_grid.toml",
        "research/grids/orb.toml",
    ]
    assert qm.grid_options(tmp_path / "missing", tmp_path) == []
    assert _json(queue_panel.layout(make_ops(queue, grids_dir=grids))).count("orb.toml") >= 1


# --- C16-C19: rows -------------------------------------------------------------------------


def test_log_tail(tmp_path):
    log = tmp_path / "j.log"
    log.write_text("\n".join(f"line {i}" for i in range(50)), encoding="utf-8")
    tail = qm.log_tail(log).splitlines()
    assert len(tail) == qm.LOG_LINES and tail[-1] == "line 49" and tail[0] == "line 30"
    assert qm.log_tail(tmp_path / "missing.log") == qm.NO_LOG
    (tmp_path / "empty.log").write_text("", encoding="utf-8")
    assert qm.log_tail(tmp_path / "empty.log") == qm.NO_LOG
    (tmp_path / "bin.log").write_bytes(b"ok \xff\xfe line\r\nsecond")
    assert "second" in qm.log_tail(tmp_path / "bin.log")  # bad bytes do not crash
    big = tmp_path / "big.log"
    big.write_text("x" * 5_000_000 + "\nlast line", encoding="utf-8")
    assert qm.log_tail(big).endswith("last line") and len(qm.log_tail(big)) <= qm.LOG_BYTES


def test_log_tail_of_a_job_in_the_row(queue):
    job = add_job(queue, "running", started=iso(5))
    Path(job.log).write_text("hello from the job\nsecond line\n", encoding="utf-8")
    assert "hello from the job" in _json(queue_panel.view(make_ops(queue))["jobs"])


def test_job_order_and_cap(queue):
    ids = {
        s: add_job(queue, s, name=s) for s in ("done", "cancelled", "failed", "pending", "running")
    }
    newer = add_job(queue, "done", name="newer done")
    order = [j.name for j in qm.ordered_jobs(queue.jobs())]
    assert order == ["running", "pending", "failed", "cancelled", "newer done", "done"]
    assert ids and newer
    pending = next(j for j in queue.jobs() if j.state == "pending")
    many = [replace(pending, id=f"j{i:03d}") for i in range(qm.MAX_ROWS + 7)]
    rows = queue_panel.job_list(many, datetime.now(UTC))
    assert len(rows) == qm.MAX_ROWS + 1 and "7 more" in _json(rows[-1])


def test_finished_jobs_are_collapsed_below_the_active_ones(queue):
    # V2.5 rule: essentials visible, the rest behind Details (100 rebuild jobs hid the cards)
    for s in ("running", "pending", "failed"):
        add_job(queue, s, name=f"active {s}")
    for i in range(30):
        add_job(queue, "done", name=f"old {i}")
    add_job(queue, "cancelled", name="old cancelled")
    rows = queue_panel.job_list(queue.jobs(), datetime.now(UTC))
    assert len(rows) == 4  # three active rows + one collapsed section
    assert all("active" in _json(r) for r in rows[:3])
    last = rows[-1]
    assert last.__class__.__name__ == "Details" and not last.open
    assert "Finished (31)" in _json(last)


def test_only_finished_jobs_still_collapse(queue):
    add_job(queue, "done", name="old")
    [section] = queue_panel.job_list(queue.jobs(), datetime.now(UTC))
    assert section.__class__.__name__ == "Details" and "Finished (1)" in _json(section)


def test_elapsed_text():
    now = datetime(2026, 10, 26, 12, 0, 0, tzinfo=UTC)

    def job(state, started, ended=None):
        return type("J", (), {"state": state, "started": started, "ended": ended})()

    ago = lambda s: (now - timedelta(seconds=s)).isoformat()
    assert qm.elapsed_text(job("running", ago(45)), now) == "45s"
    assert qm.elapsed_text(job("running", ago(125)), now) == "2m 05s"
    assert qm.elapsed_text(job("running", ago(3725)), now) == "1h 02m"
    assert qm.elapsed_text(job("done", ago(100), ago(40)), now) == "1m 00s"
    assert qm.elapsed_text(job("pending", None), now) == "–"
    assert qm.elapsed_text(job("running", "garbage"), now) == "–"
    assert qm.elapsed_text(job("failed", ago(100), None), now) == "–"
    assert qm.elapsed_text(job("running", None), now) == "–"


# --- dispatch of the buttons ---------------------------------------------------------------


def test_dispatch_routes_clicks_and_ignores_rerenders(tmp_path):
    fake = FakeQueue(tmp_path)
    ops = make_ops(fake, ALIVE)
    assert queue_panel.dispatch(ops, "qp-stop", 1, None).startswith("Stop requested")
    queue_panel.dispatch(ops, {"type": "qp-cancel", "job": "a"}, 1, None)
    queue_panel.dispatch(ops, {"type": "qp-retry", "job": "b"}, 2, None)
    assert fake.calls == [("stop",), ("cancel", "a"), ("retry", "b")]
    fake.calls.clear()
    for value in (0, None):  # a re-rendered button is not a click
        assert queue_panel.dispatch(ops, "qp-stop", value, None) is None
        assert queue_panel.dispatch(ops, {"type": "qp-cancel", "job": "a"}, value, None) is None
    assert queue_panel.dispatch(ops, "qp-unknown", 1, None) is None
    assert fake.calls == []


def test_dispatch_start_and_grid(queue, grids):
    spawner = Spawner()
    ops = make_ops(queue, spawner=spawner, grids_dir=grids)
    queue_panel.dispatch(ops, "qp-start", 1, None)
    assert len(spawner.calls) == 1
    value = ops.grids()[0]["value"]
    assert "Queued" in queue_panel.dispatch(ops, "qp-queue-grid", 1, value)
    assert len(queue.jobs()) == 1


def test_callbacks_register(queue, grids):
    from dash import Dash, html

    app = Dash(__name__, suppress_callback_exceptions=True)
    ops = make_ops(queue, grids_dir=grids)
    app.layout = html.Div(queue_panel.layout(ops))
    queue_panel.register_callbacks(app, ops)
    outputs = " ".join(app.callback_map)
    for part in ("qp-message", "qp-keys", "qp-jobs", "qp-elapsed", "qp-log"):
        assert part in outputs


# --- C20-C24: pipeline state on the card ---------------------------------------------------


def state_file(folder, overall, current=None, failed=None):
    names = ("research", "monte_carlo", "card_inputs")
    steps = []
    for name in names:
        step = {"name": name, "state": "pending", "error": None}
        if name == failed:
            step.update(state="failed", error="boom")
        steps.append(step)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "pipeline.json").write_text(
        json.dumps({"state": overall, "current": current, "steps": steps}), encoding="utf-8"
    )


@pytest.fixture
def grid_file(tmp_path, grids):
    return grids / "orb.toml"


def rid_of(tmp_path, results, grid_file):
    from backtester.tools.research_pipeline import research_folder

    return research_folder(grid_file, results).name


def research_row(rid, text=None):
    return {
        "is_research": True, "research_id": rid, "source": f"{rid} v1", "href": "/results/x",
        "strategy": "S", "flag_keys": [], "pipeline": text,
    }  # fmt: skip


@pytest.mark.parametrize(
    "text",
    ["queued", "step 2 of 3: monte_carlo", "done", "failed: monte_carlo: boom", "job cancelled"],
)
def test_card_shows_the_pipeline_text(text):
    assert f"Pipeline: {text}" in _json(research.card(research_row("g_1", text)))


def test_card_without_pipeline_text_or_plain_run_has_no_chip_text():
    assert "Pipeline:" not in _json(research.card(research_row("g_1", None)))
    plain = {"is_research": False, "source": "20261001-100000_XAUUSD", "href": "/results/x",
             "strategy": "S", "flag_keys": []}  # fmt: skip
    assert research.pipeline_chip(plain) is None
    assert "rr-pipeline" not in _json(research.card(plain))


def test_card_text_from_pipeline_json(results, grid_file, tmp_path):
    from backtester.tools.research_pipeline import read_state

    folder = results / "research" / rid_of(tmp_path, results, grid_file)
    assert qm.pipeline_text(read_state(folder), None) is None  # no pipeline, no job
    state_file(folder, "running", "monte_carlo")
    assert qm.pipeline_text(read_state(folder), None) == "step 2 of 3: monte_carlo"
    state_file(folder, "done")
    assert qm.pipeline_text(read_state(folder), None) == "done"
    state_file(folder, "failed", failed="monte_carlo")
    assert qm.pipeline_text(read_state(folder), None) == "failed: monte_carlo: boom"


def job_stub(state, **kw):
    return type("J", (), {"state": state, "exit_code": kw.get("exit_code")})()


def test_pending_job_reads_queued_even_over_old_state():
    for old in (None, {"state": "done", "steps": [], "current": None},
                {"state": "failed", "steps": [{"name": "x", "state": "failed", "error": "e"}]}):  # fmt: skip
        assert qm.pipeline_text(old, job_stub("pending")) == "queued"


def test_cancelled_or_failed_job_beats_a_running_state():
    running = {"state": "running", "current": "research", "steps": [{"name": "research"}]}
    assert qm.pipeline_text(running, job_stub("cancelled")) == "job cancelled"
    assert qm.pipeline_text(running, job_stub("failed", exit_code=3)) == "job failed (exit 3)"
    assert qm.pipeline_text(running, job_stub("failed")) == "job failed"
    assert qm.pipeline_text(None, job_stub("failed", exit_code=2)) == "job failed (exit 2)"
    pending_state = {"state": "pending", "steps": []}
    assert qm.pipeline_text(pending_state, job_stub("cancelled")) == "job cancelled"


def test_normal_flow_texts():
    running = {"state": "running", "current": "monte_carlo",
               "steps": [{"name": n} for n in ("research", "monte_carlo", "card_inputs")]}  # fmt: skip
    assert qm.pipeline_text(running, job_stub("running")) == "step 2 of 3: monte_carlo"
    assert qm.pipeline_text(None, job_stub("running")) == "queued"
    assert qm.pipeline_text({"state": "done", "steps": []}, job_stub("done")) == "done"
    failed = {"state": "failed", "steps": [{"name": "research", "state": "failed", "error": "x"}]}
    assert qm.pipeline_text(failed, job_stub("failed")) == "failed: research: x"
    assert qm.pipeline_text(None, job_stub("done")) is None


def test_attach_pipeline_with_real_queue_and_folder(queue, results, grid_file, tmp_path):
    rid = rid_of(tmp_path, results, grid_file)
    folder = results / "research" / rid
    state_file(folder, "running", "research")
    rows = [research_row(rid), {"is_research": False, "source": "plain"}]
    qm.attach_pipeline(rows, queue, results)
    assert rows[0]["pipeline"] == "step 1 of 3: research" and rows[1]["pipeline"] is None
    job = add_job(queue, "pending", argv=[PIPELINE, "research/grids/orb.toml"])
    qm.attach_pipeline(rows, queue, results)
    assert rows[0]["pipeline"] == "queued"  # pending job wins over the running state
    queue.cancel(job.id)
    qm.attach_pipeline(rows, queue, results)
    assert rows[0]["pipeline"] == "job cancelled"  # cancelled while pipeline.json says running
    qm.attach_pipeline(rows, None, results)  # no queue at all: pipeline.json only
    assert rows[0]["pipeline"] == "step 1 of 3: research"


def test_pipeline_jobs_mapping(queue, results, grid_file, tmp_path):
    rid = rid_of(tmp_path, results, grid_file)
    old = add_job(queue, "done", argv=[PIPELINE, "research/grids/orb.toml"])
    other_module = add_job(
        queue, "pending", argv=["backtester.tools.research", "research/grids/orb.toml"]
    )
    broken_grid = tmp_path / "research" / "grids" / "broken.toml"
    broken_grid.write_text("this is [not toml", encoding="utf-8")
    add_job(queue, "pending", argv=[PIPELINE, "research/grids/broken.toml"])
    add_job(queue, "pending", argv=[PIPELINE, "research/grids/missing.toml"])
    add_job(queue, "pending", argv=[PIPELINE])
    mapping = qm.pipeline_jobs(queue.jobs(), queue.home, results)
    assert list(mapping) == [rid] and mapping[rid].id == old.id and other_module
    newest = add_job(queue, "failed", argv=[PIPELINE, str(grid_file)])  # absolute path, same grid
    assert qm.pipeline_jobs(queue.jobs(), queue.home, results)[rid].id == newest.id
    active = add_job(queue, "running", argv=[PIPELINE, "research/grids/orb.toml"], started=iso(1))
    add_job(queue, "cancelled", argv=[PIPELINE, "research/grids/orb.toml"])  # newer, but not active
    assert qm.pipeline_jobs(queue.jobs(), queue.home, results)[rid].id == active.id


def test_pipeline_chip_classes():
    assert qm.pipeline_class("failed: x: y").endswith("rr-pipe-failed")
    assert qm.pipeline_class("job cancelled").endswith("rr-pipe-failed")
    assert qm.pipeline_class("done").endswith("rr-pipe-done")
    assert qm.pipeline_class("queued").endswith("rr-pipe-active")
    assert qm.pipeline_class(None) == "rr-chip rr-pipeline"


# --- C25: the Research page ----------------------------------------------------------------


def test_research_page_has_the_panel_and_the_old_ids(results, queue):
    page = _json(research.layout(results, make_ops(queue)))
    for part in ("qp-panel", "qp-interval", "rr-cards", "rr-reload", "rr-keys", "rr-strategy",
                 "rr-sort", "rr-more"):  # fmt: skip
        assert part in page


def test_page_callbacks_register_without_clashes(results, queue):
    from backtester.ui import app as app_module

    app = app_module.create_app()
    outputs = " ".join(app.callback_map)
    for part in ("rr-cards.children", "qp-message.children", "qp-jobs.children", "rr-pipeline"):
        assert part in outputs
    pipeline = next(k for k in app.callback_map if "rr-pipeline" in k)
    assert pipeline.count('["ALL"]') == 4  # two wildcards in each of the two outputs
