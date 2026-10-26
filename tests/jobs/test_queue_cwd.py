"""Queue jobs in a lane folder (briefs/v26c-test-cases.md B). Spec: research-runner.md > Lanes.

The lane registry is a hand-written `lanes.json` in a temporary "V2 root"; no git, no child
process: the runner's `popen` is a recorder.
"""

from __future__ import annotations

import json
import os
import sys
import warnings
from dataclasses import replace
from pathlib import Path

import pytest

from backtester.jobs.queue import Job, Queue, Runner
from backtester.tools.queue import main

pytestmark = pytest.mark.filterwarnings("ignore:A pending/running job")

ARGV = ["backtester.tools.research_pipeline", "g.toml"]


class Child:
    pid = 910000

    def poll(self):
        return None


@pytest.fixture
def home(tmp_path):
    root = tmp_path / "V2"
    (root / "results").mkdir(parents=True)
    return root


@pytest.fixture
def lane(tmp_path, home):
    path = tmp_path / "bt-lane-momo"
    (path / "src").mkdir(parents=True)
    entry = {
        "name": "momo",
        "path": str(path),
        "branch": "lane/momo",
        "base_commit": "abc",
        "created": "2026-10-26T00:00:00+00:00",
    }
    (home / "lanes.json").write_text(json.dumps({"lanes": [entry]}), encoding="utf-8")
    return path


def queue(tmp_path, home):
    return Queue(tmp_path / "queue", home=home)


def rig(q, **kwargs):
    launched = []

    def launch(argv, **opts):
        launched.append((argv, opts))
        return Child()

    return Runner(q, popen=launch, sensor=lambda: 60, sender=lambda s: None, **kwargs), launched


def test_b1_default_job_runs_in_the_v2_root_without_env(tmp_path, home):
    q = queue(tmp_path, home)
    job = q.add(ARGV)
    assert job.cwd is None
    runner, launched = rig(q)
    runner.tick()
    ((argv, opts),) = launched
    assert argv == [sys.executable, "-m", *ARGV]
    assert Path(opts["cwd"]) == home.resolve()
    assert "env" not in opts


def test_b1_old_job_file_without_cwd_loads(tmp_path, home):
    q = queue(tmp_path, home)
    job = q.add(ARGV)
    path = q.path(job.id)
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["cwd"]
    path.write_text(json.dumps(data), encoding="utf-8")
    assert q.get(job.id).cwd is None


def test_b2_registered_lane_by_path_and_by_name(tmp_path, home, lane):
    q = queue(tmp_path, home)
    by_path = q.add(ARGV, cwd=str(lane))
    by_name = q.add(ARGV, cwd="momo")
    assert by_path.cwd == str(lane.resolve()) and by_name.cwd == str(lane.resolve())
    assert q.get(by_path.id).cwd == str(lane.resolve())
    runner, launched = rig(q, workers=2)
    runner.tick()
    assert len(launched) == 2
    assert all(Path(opts["cwd"]) == lane.resolve() for _, opts in launched)


def test_b3_unregistered_folders_are_refused(tmp_path, home, lane):
    q = queue(tmp_path, home)
    other = tmp_path / "bt-lane-other"
    other.mkdir()
    (tmp_path / "somefile").write_text("x", encoding="utf-8")
    for bad in (
        other,
        tmp_path,
        home.parent,
        lane.parent,
        lane / "src",  # inside a lane is not the lane
        lane / ".." / "bt-lane-other",
        tmp_path / "somefile",
        tmp_path / "missing",
        "other",
        "../elsewhere",
        home / "results",
    ):
        with pytest.raises(ValueError, match="cwd"):
            q.add(ARGV, cwd=str(bad))
    assert q.jobs() == []


def test_b3_registered_lane_without_folder_is_refused(tmp_path, home, lane):
    lane.joinpath("src").rmdir()
    lane.rmdir()
    with pytest.raises(ValueError, match="cwd|folder"):
        queue(tmp_path, home).add(ARGV, cwd="momo")


def test_b4_v2_root_is_the_default(tmp_path, home):
    q = queue(tmp_path, home)
    assert q.add(ARGV, cwd=str(home)).cwd is None
    assert q.add(ARGV, cwd=str(home / ".")).cwd is None


def test_b5_lane_job_env_points_data_to_v2_and_code_to_the_lane(tmp_path, home, lane, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "keepme")
    monkeypatch.setenv("BACKTESTER_HOME", "something-else")
    q = queue(tmp_path, home)
    q.add(ARGV, cwd="momo")
    runner, launched = rig(q)
    runner.tick()
    ((_, opts),) = launched
    env = opts["env"]
    assert Path(env["BACKTESTER_HOME"]) == home.resolve()
    parts = env["PYTHONPATH"].split(os.pathsep)
    assert Path(parts[0]) == lane.resolve() / "src" and parts[1:] == ["keepme"]
    assert env["PATH"] == os.environ["PATH"]  # the rest of the environment is kept


def test_b6_lane_removed_after_queueing_fails_the_job(tmp_path, home, lane):
    q = queue(tmp_path, home)
    job = q.add(ARGV, cwd="momo")
    (home / "lanes.json").write_text(json.dumps({"lanes": []}), encoding="utf-8")
    runner, launched = rig(q)
    runner.tick()
    done = q.get(job.id)
    assert launched == []
    assert (done.state, done.exit_code) == ("failed", -1)
    assert "cwd" in Path(done.log).read_text(encoding="utf-8")


def test_b7_cli_add_cwd(tmp_path, home, lane, capsys):
    q = queue(tmp_path, home)
    main(["add", "--cwd", "momo", "--", *ARGV], queue=q)
    main(["add-grid", "research/grids/momo.toml", "--cwd", str(lane)], queue=q)
    a, b = q.jobs()
    assert a.cwd == str(lane.resolve()) and b.cwd == str(lane.resolve())
    assert b.argv == ["backtester.tools.research_pipeline", "research/grids/momo.toml"]
    capsys.readouterr()
    with pytest.raises(SystemExit) as raised:
        main(["add", "--cwd", str(tmp_path), "--", *ARGV], queue=q)
    assert raised.value.code != 0
    assert "cwd" in capsys.readouterr().err
    assert len(q.jobs()) == 2


def test_b8_same_argv_in_another_cwd_is_no_duplicate(tmp_path, home, lane):
    q = queue(tmp_path, home)
    q.add(ARGV)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        q.add(ARGV, cwd="momo")
    with pytest.warns(UserWarning, match="same argv"):
        q.add(ARGV, cwd="momo")


def test_retry_keeps_cwd(tmp_path, home, lane):
    q = queue(tmp_path, home)
    job = q.add(ARGV, cwd="momo")
    q.update(job.id, lambda j: replace(j, state="failed"))
    assert q.retry(job.id).cwd == str(lane.resolve())


def test_job_dataclass_default():
    assert Job("x", "n", ["backtester.a"]).cwd is None
