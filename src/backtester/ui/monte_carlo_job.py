"""The one Full Monte Carlo run in this server process, as a results page shows it (no Dash).

Spec: risk-management.md > Monte Carlo report and > Prop-firm field (where it shows); ROADMAP
12.7 / 5.6. The "Full Monte Carlo" button runs `python -m backtester.tools.monte_carlo --run
<run id>` (about 35 min with kind D) as a child process and writes `report.html` +
`summary.json` into `results/monte_carlo/<run id>/`. The job lives here, so leaving the page and
coming back shows it again. One run at a time (`AlreadyRunning`).

States of `snapshot(run_id)`: idle (no report), ready (report on disk), running, error,
cancelled, busy (another run's Monte Carlo is running). `report` / `href` are set whenever a
report exists, also while a rerun is going on.
"""

from __future__ import annotations

import json
import re
import sys
import threading
from collections.abc import Callable
from pathlib import Path

from backtester.paths import RESULTS_DIR
from backtester.ui import process_job as pj
from backtester.ui.process_job import ProcessJob

MONTE_CARLO_DIR = "monte_carlo"
REPORT = "report.html"
SUMMARY = "summary.json"
REPORT_PREFIX = "/monte-carlo/"
RUN_ID = re.compile(r"[A-Za-z0-9_.-]+")
KINDS = {
    "A": "day reshuffle + FTMO",
    "B": "random entries",
    "C": "random fills",
    "D": "random price paths",
}
_KIND_LINE = re.compile(r"kind ([A-D])\b")
_PATH_LINE = re.compile(r"(\S+) path (\d+)/(\d+)")
BUSY_TEXT = "Another Monte Carlo is running ({run}). One at a time."
CANCELLED_TEXT = "Monte Carlo cancelled."
STARTING_TEXT = "Starting …"
NO_REPORT_TEXT = "The Monte Carlo finished without a report."


class AlreadyRunning(RuntimeError):
    """A Full Monte Carlo is already running; only one runs at a time."""


class RunNotFound(ValueError):
    """No such run folder (or not a run id)."""


_lock = threading.Lock()
_current: tuple[str, int, ProcessJob] | None = None  # (run id, symbols, job)


def current() -> ProcessJob | None:
    return _current[2] if _current else None


def reset() -> None:
    """Forget the job (tests)."""
    global _current
    with _lock:
        _current = None


def is_running() -> bool:
    return _current is not None and not _current[2].finished


def out_dir(run_id: str, results_dir: Path = RESULTS_DIR) -> Path:
    return Path(results_dir) / MONTE_CARLO_DIR / run_id


def report_exists(run_id: str, results_dir: Path = RESULTS_DIR) -> bool:
    folder = out_dir(run_id, results_dir)
    return (folder / REPORT).is_file() and (folder / SUMMARY).is_file()


def _symbol_count(folder: Path) -> int:
    try:
        return max(len(json.loads((folder / "summary.json").read_text("utf-8"))["symbols"]), 1)
    except (OSError, ValueError, KeyError, TypeError):
        return 1


def start(
    run_id: str, results_dir: Path = RESULTS_DIR, extra_args: tuple[str, ...] = (),
    spawn: Callable = pj.spawn_process, killer: Callable = pj.kill_tree,
) -> ProcessJob:  # fmt: skip
    """Start the full report for a run in the background."""
    global _current
    folder = Path(results_dir) / run_id
    if (
        not RUN_ID.fullmatch(run_id or "")
        or run_id in (".", "..")
        or not (folder / "trades.csv").is_file()
        or not (folder / "summary.json").is_file()
    ):
        raise RunNotFound(f"no run {run_id!r}")
    with _lock:
        if _current is not None and not _current[2].finished:
            raise AlreadyRunning(BUSY_TEXT.format(run=_current[0]))
        argv = [
            sys.executable, "-m", "backtester.tools.monte_carlo", "--run", run_id,
            "--results-dir", str(results_dir), "--out", str(out_dir(run_id, results_dir)),
            *extra_args,
        ]  # fmt: skip
        job = ProcessJob.start(argv, spawn=spawn, killer=killer)
        _current = (run_id, _symbol_count(folder), job)
        return job


def cancel() -> bool:
    """Stop the running Monte Carlo; False when none runs."""
    job = _current[2] if _current else None
    if job is None or job.finished:
        return False
    job.cancel()
    return True


def _progress(lines: list[str], symbols: int) -> tuple[str, float | None]:
    """(detail text, percent or None) from the tool's output lines."""
    kind = None
    for line in reversed(lines):
        m = _KIND_LINE.match(line.strip())
        if m:
            kind = m.group(1)
            break
    if kind is None:
        return STARTING_TEXT, None
    text = f"Kind {kind} · {KINDS[kind]}"
    if kind != "D":
        return text, None
    done, total, last = 0, 0, ""
    for line in lines:
        m = _PATH_LINE.search(line)
        if m:
            done += 1
            total = int(m.group(3)) * symbols
            last = f"{m.group(1)} path {m.group(2)}/{m.group(3)}"
    if not total:
        return text, None
    return f"{text} · {last}", min(done / total, 1.0) * 100


def format_elapsed(seconds: float) -> str:
    s = int(seconds)
    h, rest = divmod(s, 3600)
    m, sec = divmod(rest, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def snapshot(run_id: str, results_dir: Path = RESULTS_DIR, now: float | None = None) -> dict:
    """Everything a results page shows about the Monte Carlo of `run_id`."""
    report = report_exists(run_id, results_dir)
    snap = {
        "state": "ready" if report else "idle",
        "report": report,
        "href": f"{REPORT_PREFIX}{run_id}/{REPORT}" if report else None,
        "detail": "",
        "percent": None,
        "elapsed": "",
        "message": "",
    }
    if _current is None:
        return snap
    job_run, symbols, job = _current
    if job_run != run_id:
        if not job.finished:
            snap.update(state="busy", message=BUSY_TEXT.format(run=job_run))
        return snap
    if not job.finished:
        detail, percent = _progress(job.lines(), symbols)
        snap.update(state="running", detail=detail, percent=percent)
    elif job.cancel_requested:
        snap.update(state="cancelled", message=CANCELLED_TEXT)
    elif job.returncode != 0 or not report:
        lines = job.lines()
        last = lines[-1] if lines and job.returncode else NO_REPORT_TEXT
        snap.update(state="error", message=last)
    snap["elapsed"] = format_elapsed(job.elapsed(now))
    return snap
