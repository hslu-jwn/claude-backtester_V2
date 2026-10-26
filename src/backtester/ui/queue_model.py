"""Queue panel logic of the Research page, without Dash (the panel is `ui/queue_panel.py`).

Spec: research-runner.md > Job queue, briefs/v26c-cards-lanes.md section C (decisions of the
user, 2026-10-26).

- `QueueOps`: the actions of the buttons (start runner, stop, cancel, retry, queue a grid).
  Every action returns the message the panel shows; nothing raises into the page.
  The runner is started by an injectable `spawner` (a detached background process, so tests
  never start one); the runner lock decides that there is only one, the panel only avoids
  asking for a second one (runner alive, or one was just started).
- The one-time MT5 test (`--retest`) is CLI only: `QueueOps.queue_grid` never passes it.
- `pipeline_text`: what a research card shows about its pipeline, from `pipeline.json` and the
  queue job of that grid (a pending job reads "queued"; a cancelled / failed job wins over a
  `pipeline.json` that still says running).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
import warnings
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from backtester.jobs.config import DEFAULT_CONFIG
from backtester.jobs.queue import Queue, queue_status
from backtester.paths import HOME_DIR, RESULTS_DIR
from backtester.tools.queue import add_grid
from backtester.tools.research_pipeline import progress, read_state, research_folder

PIPELINE_MODULE = "backtester.tools.research_pipeline"
RUNNER_MODULE = "backtester.tools.queue"
RUNNER_LOG = "runner.out.log"  # stdout / stderr of the detached runner, in the queue folder
START_GRACE = 20.0  # seconds after a Start during which a second Start is refused
LOG_LINES = 20
LOG_BYTES = 16384  # only the end of a log is read
MAX_ROWS = 50
NO_SENSOR = "no sensor"
NO_LOG = "no log yet"
NO_JOBS = "No jobs."
STATE_ORDER = {"running": 0, "pending": 1, "failed": 2, "cancelled": 3, "done": 4}
ACTIVE = ("pending", "running")
JOB_ID = re.compile(r"[A-Za-z0-9_-]+")
DASH = "–"
# Windows process flags (the constants only exist in `subprocess` there)
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000


def make_queue(results_dir: Path = RESULTS_DIR, home: Path = HOME_DIR) -> Queue:
    return Queue(root=Path(results_dir) / "queue", home=home)


# --- the detached runner -------------------------------------------------------------------


def runner_argv() -> list[str]:
    return [
        sys.executable,
        "-m",
        RUNNER_MODULE,
        "run",
        "--workers",
        str(DEFAULT_CONFIG.workers),
    ]


def spawn_detached(argv: list[str], cwd: Path, log_path: Path, popen: Callable = subprocess.Popen):
    """Start `argv` as a background process that keeps running after the page and the app are
    closed: its own process group and (Windows) its own hidden console, no pipe to this
    process (output goes to `log_path`), no stdin. The hidden console is shared by the jobs the
    runner starts, so they open no windows."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    options: dict = {}
    if os.name == "nt":
        options["creationflags"] = CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    else:
        options["start_new_session"] = True
    with log_path.open("ab") as out:
        return popen(
            argv,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            close_fds=True,
            **options,
        )


# --- grids ---------------------------------------------------------------------------------


def grid_options(grids_dir: Path, home: Path = HOME_DIR) -> list[dict]:
    """`research/grids/*.toml` as dropdown options; the value is the path relative to the V2
    root when it lies below it (as the CLI examples write it), else the absolute path."""
    try:
        files = sorted(Path(grids_dir).glob("*.toml"), key=lambda p: p.name.lower())
    except OSError:
        return []
    options = []
    for path in files:
        try:
            value = path.resolve().relative_to(Path(home).resolve()).as_posix()
        except ValueError:
            value = str(path.resolve())
        options.append({"label": path.name, "value": value})
    return options


# --- actions -------------------------------------------------------------------------------


class QueueOps:
    """What the panel buttons do. `status` is `jobs.queue.queue_status`, `add_grid` is
    `tools.queue.add_grid`, `spawner` starts the detached runner (all injectable)."""

    def __init__(
        self,
        queue: Queue,
        *,
        spawner: Callable = spawn_detached,
        grids_dir: Path | None = None,
        add_grid_fn: Callable = add_grid,
        status: Callable = queue_status,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.queue = queue
        self.spawner = spawner
        self.grids_dir = (
            Path(grids_dir) if grids_dir is not None else self.queue.home / "research" / "grids"
        )
        self.add_grid_fn = add_grid_fn
        self.status_fn = status
        self.clock = clock
        self._started: float | None = None

    def status(self) -> dict:
        return self.status_fn(self.queue)

    def starting(self) -> bool:
        """A runner was started a moment ago and may not hold the lock yet."""
        return self._started is not None and self.clock() - self._started < START_GRACE

    def grids(self) -> list[dict]:
        return grid_options(self.grids_dir, self.queue.home)

    def start(self) -> str:
        if self.status()["runner_alive"]:
            return "A runner is already running."
        if self.starting():
            return "A runner was just started; wait a few seconds."
        try:
            self.spawner(runner_argv(), cwd=self.queue.home, log_path=self.queue.root / RUNNER_LOG)
        except OSError as exc:
            return f"Could not start the runner: {exc}"
        self._started = self.clock()
        return "Runner started (it keeps running after you close the page)."

    def stop(self) -> str:
        if not self.status()["runner_alive"]:
            return "No runner is running; nothing to stop."
        self.queue.stop()
        return "Stop requested: running jobs finish, no new job starts."

    def cancel(self, job_id: str) -> str:
        return self._job_action("cancel", job_id, "Cancelled")

    def retry(self, job_id: str) -> str:
        return self._job_action("retry", job_id, "Queued again")

    def _job_action(self, action: str, job_id, done: str) -> str:
        if not isinstance(job_id, str) or not JOB_ID.fullmatch(job_id):
            return "Not a job id."
        try:
            getattr(self.queue, action)(job_id)
        except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
            return f"{action.capitalize()} failed: {exc}"
        return f"{done}: {job_id}"

    def queue_grid(self, grid) -> str:
        if not grid:
            return "Choose a grid first."
        if grid not in {o["value"] for o in self.grids()}:
            return "That grid is not in research/grids."
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                job = self.add_grid_fn(self.queue, grid)
            except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
                return f"Could not queue the grid: {exc}"
        text = f"Queued the pipeline of {Path(grid).name}: {job.id}"
        if any("same argv" in str(w.message) for w in caught):
            text += " (the same grid was already pending or running)"
        return text


# --- snapshot, rows ------------------------------------------------------------------------


def snapshot(ops: QueueOps) -> dict:
    status = ops.status()
    counts = status.get("counts") or {}
    return {
        "counts": counts,
        "temperature": status.get("temperature"),
        "paused": bool(status.get("paused")),
        "runner_alive": bool(status.get("runner_alive")),
        "stopping": bool(status.get("stopping")),
        "broken": list(status.get("broken") or []),
    }


def key_items(snap: dict) -> list[dict]:
    counts = snap["counts"]
    temperature = snap["temperature"]
    items = [
        {"label": "Pending", "value": counts.get("pending", 0)},
        {"label": "Running", "value": counts.get("running", 0)},
        {"label": "Done", "value": counts.get("done", 0), "sign": "green"},
        {
            "label": "Failed",
            "value": counts.get("failed", 0),
            "sign": "red" if counts.get("failed", 0) else None,
            "tooltip": "Broken job files: " + ", ".join(snap["broken"]) if snap["broken"] else "",
        },
        {
            "label": "CPU",
            "value": NO_SENSOR if temperature is None else f"{temperature:g} °C",
            "tooltip": "CPU temperature from LibreHardwareMonitor (Remote Web Server)",
        },
        {
            "label": "Paused",
            "value": "yes" if snap["paused"] else "no",
            "tooltip": "The runner holds back new jobs while the CPU is too hot",
        },
        {
            "label": "Runner",
            "value": ("stopping" if snap["stopping"] else "yes") if snap["runner_alive"] else "no",
            "sign": "green" if snap["runner_alive"] else None,
        },
    ]
    return items


def ordered_jobs(jobs: list) -> list:
    """Running, pending, failed, cancelled, done; the newest first inside a state."""
    newest_first = sorted(jobs, key=lambda j: j.id, reverse=True)
    return sorted(newest_first, key=lambda j: STATE_ORDER.get(j.state, len(STATE_ORDER)))


def _time(text) -> datetime | None:
    try:
        value = datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def duration_text(seconds: float) -> str:
    seconds = max(int(seconds), 0)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def elapsed_text(job, now: datetime | None = None) -> str:
    start = _time(job.started)
    if job.state == "pending" or start is None:
        return DASH
    end = (now or datetime.now(UTC)) if job.state == "running" else _time(job.ended)
    return DASH if end is None else duration_text((end - start).total_seconds())


def log_tail(path, lines: int = LOG_LINES, size: int = LOG_BYTES) -> str:
    try:
        with open(path, "rb") as stream:
            stream.seek(0, os.SEEK_END)
            end = stream.tell()
            stream.seek(max(end - size, 0))
            data = stream.read()
    except (OSError, TypeError, ValueError):
        return NO_LOG
    text = data.decode("utf-8", errors="replace").replace("\r\n", "\n")
    kept = text.splitlines()[-lines:]
    return "\n".join(kept) if kept else NO_LOG


# --- pipeline state of a research card -----------------------------------------------------

_grid_cache: dict[tuple, str | None] = {}


def _grid_id(grid_path: Path, results_dir: Path) -> str | None:
    try:
        key = (str(grid_path), grid_path.stat().st_mtime_ns, str(results_dir))
    except OSError:
        return None
    if key not in _grid_cache:
        try:
            _grid_cache[key] = research_folder(grid_path, results_dir).name
        except Exception:  # noqa: BLE001 - an invalid grid file must never break the page
            _grid_cache[key] = None
    return _grid_cache[key]


def pipeline_jobs(jobs: list, home: Path, results_dir: Path) -> dict:
    """research folder id -> the queue job that stands for it: an active (pending / running)
    one, else the newest. Only pipeline jobs count; the grid file is read relative to the
    job's cwd (a lane) or the V2 root."""
    found: dict[str, tuple] = {}
    for job in jobs:
        if job.argv[:1] != [PIPELINE_MODULE] or len(job.argv) < 2:
            continue
        grid = Path(job.argv[1])
        if not grid.is_absolute():
            grid = Path(job.cwd or home) / grid
        rid = _grid_id(grid, Path(results_dir))
        if rid is None:
            continue
        rank = (job.state in ACTIVE, job.id)
        if rid not in found or rank > found[rid][0]:
            found[rid] = (rank, job)
    return {rid: job for rid, (_, job) in found.items()}


def job_state_text(job) -> str:
    if job.state == "cancelled":
        return "job cancelled"
    code = f" (exit {job.exit_code})" if job.exit_code is not None else ""
    return f"job failed{code}"


def pipeline_text(state: dict | None, job) -> str | None:
    """The card text: "queued", "step 2 of 3: monte_carlo", "done", "failed: <step>: <error>",
    "job cancelled" / "job failed (exit N)", or None (no pipeline and no job for this grid)."""
    if job is not None:
        if job.state == "pending":
            return "queued"  # pipeline.json appears only once the research step starts
        if job.state in ("cancelled", "failed") and (
            state is None or state.get("state") in ("running", "pending")
        ):
            return job_state_text(job)
    if state is None:
        return "queued" if job is not None and job.state == "running" else None
    return progress(state)


def pipeline_texts(rids, queue: Queue | None, results_dir: Path = RESULTS_DIR) -> dict:
    """research folder id -> card text (see `pipeline_text`) for every id in `rids`."""
    jobs = {}
    if queue is not None:
        try:
            jobs = pipeline_jobs(queue.jobs(), queue.home, results_dir)
        except OSError:
            jobs = {}
    return {
        rid: pipeline_text(read_state(Path(results_dir) / "research" / rid), jobs.get(rid))
        for rid in set(rids)
    }


def attach_pipeline(rows: list[dict], queue: Queue | None, results_dir: Path = RESULTS_DIR) -> None:
    """Set `row["pipeline"]` (text or None) on every research row, in place."""
    texts = pipeline_texts(
        [r["research_id"] for r in rows if r.get("research_id")], queue, results_dir
    )
    for row in rows:
        row["pipeline"] = texts.get(row.get("research_id"))


def pipeline_class(text: str | None) -> str:
    base = "rr-chip rr-pipeline"
    if not text:
        return base
    if text.startswith(("failed", "job ")):
        return base + " rr-pipe-failed"
    if text == "done":
        return base + " rr-pipe-done"
    return base + " rr-pipe-active"
