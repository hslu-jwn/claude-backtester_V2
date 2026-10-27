"""Research pipeline per grid: resumable steps, pipeline.json, queue add-grid.

Spec: research-runner.md > Pipeline (ROADMAP V2.6 step 3, briefs/v26c-test-cases.md A).
The research runner and the Monte Carlo tool are replaced by stubs; nothing runs a backtest.
"""

from __future__ import annotations

import json
import threading

import pytest

from backtester.jobs.queue import Queue
from backtester.tools import research_pipeline as rp

GRID = """
strategy = "opening_range"
symbols = ["US500"]

[base]
entry_mode = "range"

[grid]
range_minutes = [5, 15]
"""

CHOSEN = {"id": "v001", "name": "range_minutes=5", "dev_run": "20260101-000000_US500"}


@pytest.fixture
def grid(tmp_path):
    path = tmp_path / "g.toml"
    path.write_text(GRID, encoding="utf-8")
    return path


@pytest.fixture
def results(tmp_path):
    return tmp_path / "results"


class Stubs:
    """Records the calls and plays the research runner / Monte Carlo tool."""

    def __init__(self, results, *, chosen=CHOSEN, status="dev_only"):
        self.results = results
        self.chosen = chosen
        self.status = status
        self.research_calls = []
        self.mc_calls = []
        self.research_error = None
        self.mc_error = None

    def research(self, grid, **kwargs):
        self.research_calls.append((str(grid), kwargs))
        if self.research_error:
            raise self.research_error
        return {"status": self.status, "message": "ok", "chosen": self.chosen}

    def monte_carlo(self, dev_run, results_dir, out):
        self.mc_calls.append((dev_run, results_dir, out))
        if self.mc_error:
            raise self.mc_error
        out.mkdir(parents=True, exist_ok=True)
        (out / "summary.json").write_text("{}", encoding="utf-8")
        return {"kind": "stub", "runs": 7, "paths": 0, "seed": 1}


def run(grid, results, stubs, **kwargs):
    return rp.run_pipeline(
        grid,
        results_dir=results,
        research_fn=stubs.research,
        monte_carlo_fn=stubs.monte_carlo,
        log=lambda *a: None,
        **kwargs,
    )


def steps(state):
    return {s["name"]: s for s in state["steps"]}


def test_changed_selection_controls_invalidate_completed_pipeline(grid, results):
    stubs = Stubs(results)
    run(grid, results, stubs)
    folder = rp.research_folder(grid, results)
    guard = folder / "research.json"
    guard.write_text('{"test":{"status":"done","run":1}}', encoding="utf-8")
    grid.write_text("min_trades = 999999\n" + GRID, encoding="utf-8")
    assert rp.research_folder(grid, results) == folder
    stubs.chosen = None
    state = run(grid, results, stubs)
    assert len(stubs.research_calls) == 2
    assert state["chosen"] is None
    assert "monte_carlo" in state["inputs"]["missing"]
    assert guard.read_text(encoding="utf-8") == '{"test":{"status":"done","run":1}}'
    assert all(c[1]["dev_only"] and not c[1]["retest"] for c in stubs.research_calls)
    run(grid, results, stubs)
    assert len(stubs.research_calls) == 2


def test_a1_happy_path_writes_pipeline_json(grid, results):
    stubs = Stubs(results)
    state = run(grid, results, stubs)
    folder = rp.research_folder(grid, results)
    saved = json.loads((folder / "pipeline.json").read_text(encoding="utf-8"))
    assert saved == json.loads(json.dumps(state))
    assert [s["name"] for s in saved["steps"]] == ["research", "monte_carlo", "card_inputs"]
    assert all(s["state"] == "done" for s in saved["steps"])
    assert all(s["started"] and s["ended"] and s["error"] is None for s in saved["steps"])
    assert saved["state"] == "done" and saved["current"] is None
    assert saved["version"] == 1 and saved["id"] == folder.name
    assert saved["chosen"] == {"id": "v001", "dev_run": CHOSEN["dev_run"]}


def test_a2_research_call_is_dev_only_single_worker_never_retest(grid, results):
    stubs = Stubs(results)
    run(grid, results, stubs)
    ((path, kwargs),) = stubs.research_calls
    assert path == str(grid)
    assert kwargs["dev_only"] is True and kwargs["workers"] == 1 and kwargs["retest"] is False
    assert kwargs["results_dir"] == results
    with pytest.raises(SystemExit):  # no such option
        rp.parse_args([str(grid), "--retest"])


def test_a3_monte_carlo_goes_where_the_card_reads_it(grid, results):
    stubs = Stubs(results)
    state = run(grid, results, stubs)
    ((dev_run, results_dir, out),) = stubs.mc_calls
    assert dev_run == CHOSEN["dev_run"] and results_dir == results
    assert out == results / "monte_carlo" / CHOSEN["dev_run"]
    assert state["monte_carlo"] == {
        "kind": "stub",
        "runs": 7,
        "paths": 0,
        "seed": 1,
        "out": f"monte_carlo/{CHOSEN['dev_run']}",
    }


def test_a3b_default_monte_carlo_uses_tool_defaults(results, monkeypatch):
    from backtester.tools import monte_carlo

    seen = {}

    def fake_main(argv):
        seen["argv"] = argv
        return 0

    monkeypatch.setattr(monte_carlo, "main", fake_main)
    out = results / "monte_carlo" / "RUN"
    info = rp.default_monte_carlo("RUN", results, out)
    # only the run, where to read it and where to write: every other setting is the tool default
    assert seen["argv"] == ["--run", "RUN", "--results-dir", str(results), "--out", str(out)]
    defaults = monte_carlo.ToolConfig()
    assert (info["runs"], info["paths"], info["seed"]) == (
        defaults.runs,
        defaults.paths,
        defaults.seed,
    )
    assert "kind" in info


def test_a4_resume_skips_done_steps(grid, results):
    stubs = Stubs(results)
    stubs.mc_error = RuntimeError("mc broke")
    first = run(grid, results, stubs)
    assert steps(first)["research"]["state"] == "done"
    assert steps(first)["monte_carlo"]["state"] == "failed"
    stubs.mc_error = None
    stubs.chosen = None  # a rerun must take the chosen variant from pipeline.json
    second = run(grid, results, stubs)
    assert len(stubs.research_calls) == 1
    assert len(stubs.mc_calls) == 2
    assert second["state"] == "done"
    assert steps(second)["monte_carlo"]["error"] is None
    assert second["chosen"]["dev_run"] == CHOSEN["dev_run"]


def test_a5_done_pipeline_reruns_nothing(grid, results):
    stubs = Stubs(results)
    run(grid, results, stubs)
    again = run(grid, results, stubs)
    assert len(stubs.research_calls) == 1 and len(stubs.mc_calls) == 1
    assert again["state"] == "done"


def test_a6_running_step_after_crash_is_run_again(grid, results):
    stubs = Stubs(results)
    run(grid, results, stubs)
    folder = rp.research_folder(grid, results)
    state = json.loads((folder / "pipeline.json").read_text(encoding="utf-8"))
    for s in state["steps"][1:]:
        s.update(state="running" if s["name"] == "monte_carlo" else "pending", ended=None)
    state["state"] = "running"
    (folder / "pipeline.json").write_text(json.dumps(state), encoding="utf-8")
    (results / "monte_carlo" / CHOSEN["dev_run"] / "summary.json").unlink()
    final = run(grid, results, stubs)
    assert len(stubs.research_calls) == 1 and len(stubs.mc_calls) == 2
    assert final["state"] == "done"


def test_a7_research_failure_is_recorded_and_retried(grid, results):
    stubs = Stubs(results)
    stubs.research_error = ValueError("no cached data for US500")
    state = run(grid, results, stubs)
    by = steps(state)
    assert by["research"]["state"] == "failed"
    assert "no cached data for US500" in by["research"]["error"]
    assert by["research"]["ended"]
    assert by["monte_carlo"]["state"] == "pending" and by["card_inputs"]["state"] == "pending"
    assert state["state"] == "failed" and not stubs.mc_calls
    saved = rp.read_state(rp.research_folder(grid, results))
    assert saved["state"] == "failed"
    stubs.research_error = None
    state = run(grid, results, stubs)
    assert state["state"] == "done" and len(stubs.research_calls) == 2


def test_a7b_unfinished_research_status_fails_the_step(grid, results):
    stubs = Stubs(results, status="refused")
    state = run(grid, results, stubs)
    assert steps(state)["research"]["state"] == "failed"
    assert "refused" in steps(state)["research"]["error"]


def test_a8_monte_carlo_systemexit_fails_step_only(grid, results):
    stubs = Stubs(results)
    stubs.mc_error = SystemExit("run 'x' is unreadable")
    state = run(grid, results, stubs)
    by = steps(state)
    assert by["research"]["state"] == "done"
    assert by["monte_carlo"]["state"] == "failed"
    assert "unreadable" in by["monte_carlo"]["error"]
    assert by["card_inputs"]["state"] == "pending" and state["state"] == "failed"


def test_a9_no_chosen_variant_skips_monte_carlo(grid, results):
    stubs = Stubs(results, chosen=None, status="no_test")
    state = run(grid, results, stubs)
    by = steps(state)
    assert not stubs.mc_calls
    assert by["monte_carlo"]["state"] == "done" and "no chosen variant" in by["monte_carlo"]["note"]
    assert state["state"] == "done" and state["chosen"] is None


def test_a10_existing_monte_carlo_summary_is_reused(grid, results):
    out = results / "monte_carlo" / CHOSEN["dev_run"]
    out.mkdir(parents=True)
    (out / "summary.json").write_text("{}", encoding="utf-8")
    stubs = Stubs(results)
    state = run(grid, results, stubs)
    assert not stubs.mc_calls
    assert steps(state)["monte_carlo"]["state"] == "done"
    assert "already" in steps(state)["monte_carlo"]["note"]


def test_a11_card_inputs_are_read_not_computed(grid, results):
    folder = rp.research_folder(grid, results)
    folder.mkdir(parents=True)
    (folder / "profile.json").write_text("{}", encoding="utf-8")
    (folder / "research.json").write_text(
        json.dumps({"sensitivity": {"status": "gentle"}}), encoding="utf-8"
    )
    (folder / "variants.csv").write_text(
        "variant_id,flags\nv001,few_trades;one_half\nv002,\n", encoding="utf-8"
    )
    stubs = Stubs(results)
    state = run(grid, results, stubs)
    inputs = state["inputs"]
    assert "profile" in inputs["present"] and "monte_carlo" in inputs["present"]
    assert "monkeys" in inputs["missing"] and "bayes" in inputs["missing"]
    assert inputs["stability"] == "gentle"
    assert inputs["flags"] == ["few_trades", "one_half"]
    assert steps(state)["card_inputs"]["state"] == "done"


def test_a12_bad_grid_exit_2_no_pipeline_json(tmp_path, results, capsys):
    missing = tmp_path / "nope.toml"
    assert rp.main([str(missing), "--results-dir", str(results)]) == 2
    assert "no grid file" in capsys.readouterr().err
    bad = tmp_path / "bad.toml"
    bad.write_text("strategy = 'nope'", encoding="utf-8")
    assert rp.main([str(bad), "--results-dir", str(results)]) == 2
    assert not list(results.rglob("pipeline.json"))


def test_a13_second_pipeline_on_same_grid_is_refused(grid, results):
    inside = threading.Event()
    release = threading.Event()
    stubs = Stubs(results)
    real = stubs.research

    def slow(grid_path, **kwargs):
        inside.set()
        assert release.wait(10)
        return real(grid_path, **kwargs)

    first = {}

    def worker():
        first["state"] = rp.run_pipeline(
            grid,
            results_dir=results,
            research_fn=slow,
            monte_carlo_fn=stubs.monte_carlo,
            log=lambda *a: None,
        )

    t = threading.Thread(target=worker)
    t.start()
    try:
        assert inside.wait(10)
        with pytest.raises(rp.PipelineBusy):
            run(grid, results, Stubs(results))
        assert (
            rp.progress(rp.read_state(rp.research_folder(grid, results))) == "step 1 of 3: research"
        )
    finally:
        release.set()
        t.join(10)
    assert first["state"]["state"] == "done"


def test_a14_progress_text_and_atomic_write(grid, results):
    folder = rp.research_folder(grid, results)
    assert rp.read_state(folder) is None
    assert rp.progress(None) == "queued"
    stubs = Stubs(results)
    state = run(grid, results, stubs)
    assert rp.progress(state) == "done"
    assert not list(folder.glob("*.tmp"))
    failing = Stubs(results)
    failing.mc_error = RuntimeError("boom")
    other = results / "other"
    state = run(grid, other, failing)
    assert rp.progress(state) == "failed: monte_carlo: RuntimeError: boom"
    running = {
        "state": "running",
        "current": "monte_carlo",
        "steps": [{"name": n} for n in rp.STEPS],
    }
    assert rp.progress(running) == "step 2 of 3: monte_carlo"
    assert rp.progress({"state": "pending", "steps": [{"name": n} for n in rp.STEPS]}) == "queued"
    assert rp.read_state(folder.parent / "does-not-exist") is None
    (folder / "pipeline.json").write_text("{broken", encoding="utf-8")
    assert rp.read_state(folder) is None


def test_a15_folder_is_the_runner_folder(grid):
    from backtester.tools.research_grid import expand, grid_id, load_grid

    spec = load_grid(grid)
    variants, _, _ = expand(spec)
    assert rp.research_folder(grid, "R").name == grid_id(spec, variants)
    assert rp.research_folder(grid, "R").parent.as_posix().endswith("R/research")


def test_a16_queue_add_grid_queues_the_pipeline(tmp_path):
    from backtester.tools.queue import main

    q = Queue(tmp_path)
    main(["add-grid", "research/grids/x.toml"], queue=q)
    main(["add-grid", "research/grids/y.toml", "--dev-only"], queue=q)
    main(["add-grid", "research/grids/z.toml", "--retest"], queue=q)
    a, b, c = q.jobs()
    assert a.argv == ["backtester.tools.research_pipeline", "research/grids/x.toml"]
    assert b.argv == ["backtester.tools.research_pipeline", "research/grids/y.toml"]
    assert c.argv == [
        "backtester.tools.research",
        "research/grids/z.toml",
        "--workers",
        "1",
        "--retest",
    ]
    assert a.name == "pipeline x"
