import csv
import json
import multiprocessing as mp
import time
from datetime import UTC, date, datetime
from pathlib import Path

from backtester.analytics.trial_log import append, count_only


def append_worker(path):
    for i in range(200):
        append(count_only("queue-test", "test", 1, str(i)), Path(path))


def folder_worker(path):
    from backtester.runner import allocate_run_folder

    for _ in range(10):
        allocate_run_folder(["TEST"], Path(path), now=datetime(2026, 1, 1, tzinfo=UTC))


def series_worker(root):
    from backtester.tools.research_series import ensure

    root = Path(root)
    folder = root / "series"
    folder.mkdir(exist_ok=True)
    ensure(
        folder,
        date(2026, 1, 5),
        date(2026, 1, 6),
        None,
        root / "trials.jsonl",
        ("test", "test", {}, ["TEST"], "test"),
        trades=[],
    )


def publish_worker(root):
    from types import SimpleNamespace

    from backtester.tools.research import _publish_dev_run

    root = Path(root)
    for _ in range(3):
        _publish_dev_run(root / "source", SimpleNamespace(symbols=["TEST"]), root / "runs", "p")


def grid_worker(root):
    from backtester.tools import research

    root = Path(root)
    research.load_grid = lambda *args: object()
    research.expand = lambda spec: ([], 1, False)
    research.grid_id = lambda *args: "same-grid"

    def write_shared_state(*args, **kwargs):
        path = root / "counter.json"
        value = json.loads(path.read_text()) if path.exists() else 0
        time.sleep(0.02)
        path.write_text(json.dumps(value + 1))
        return {}

    research._run_research_locked = write_shared_state
    for _ in range(3):
        research.run_research("fake.toml", results_dir=root)


def run_workers(target, path, count=4):
    ctx = mp.get_context("spawn")
    processes = [ctx.Process(target=target, args=(str(path),)) for _ in range(count)]
    try:
        for p in processes:
            p.start()
        for p in processes:
            p.join(30)
        assert all(p.exitcode == 0 for p in processes)
    finally:
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join()


def test_concurrent_trial_appends(tmp_path):
    path = tmp_path / "trials.jsonl"
    run_workers(append_worker, path)
    lines = path.read_text().splitlines()
    assert len(lines) == 800
    assert all(json.loads(line)["family"] == "queue-test" for line in lines)
    assert not (tmp_path / "trials.jsonl.lock").exists()
    assert (tmp_path / ".locks" / "trials.jsonl.lock").exists()


def test_concurrent_run_folders(tmp_path):
    run_workers(folder_worker, tmp_path)
    assert len(list(tmp_path.iterdir())) == 40


def test_concurrent_series(tmp_path):
    run_workers(series_worker, tmp_path)
    with (tmp_path / "series" / "daily.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert [r["date"] for r in rows] == ["2026-01-05", "2026-01-06"]
    assert not list(tmp_path.rglob("*.tmp"))
    assert {p.name for p in (tmp_path / "series").iterdir()} == {"daily.csv"}
    assert (tmp_path / ".locks" / "series" / "series" / "daily.csv.lock").exists()


def test_concurrent_development_publishing(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "summary.json").write_text("{}")
    (source / "settings.json").write_text("{}")
    run_workers(publish_worker, tmp_path)
    runs = list((tmp_path / "runs").iterdir())
    assert len(runs) == 12
    for folder in runs:
        assert json.loads((folder / "summary.json").read_text())["run_id"] == folder.name
        assert json.loads((folder / "settings.json").read_text())["preset"] == "p"


def test_same_grid_writers_are_serialized(tmp_path):
    run_workers(grid_worker, tmp_path)
    assert json.loads((tmp_path / "counter.json").read_text()) == 12
    assert not list((tmp_path / "research").glob("*.lock"))
    assert (tmp_path / ".locks" / "research" / "same-grid.lock").exists()
