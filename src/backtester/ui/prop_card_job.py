"""Background computation of the prop-firm card (no Dash imports).

Spec: risk-management.md > Prop-firm field (where it shows), ROADMAP 5.6. A card of a big run
takes 20-30 s, so it is computed in a child process (`python -m backtester.risk.prop_card`,
no GIL fight with the server) that writes `prop_firm.json` into the run folder. `request`
answers for a run folder: the cached card ("ready"), a running process, a queue wait (one
process at a time) or an error (kept until the server restarts, so a failing run is not retried
on every poll).
"""

from __future__ import annotations

import sys
import threading
from collections.abc import Callable
from pathlib import Path

from backtester.risk import prop_card as pc
from backtester.ui.process_job import ProcessJob, kill_tree, spawn_process

NO_CARD_TEXT = "The calculation finished without a result."

_lock = threading.Lock()
_jobs: dict[tuple[str, str, str], ProcessJob] = {}  # (results dir, run id, firm)


def reset() -> None:
    """Forget every job (tests)."""
    with _lock:
        _jobs.clear()


def busy() -> bool:
    return any(not j.finished for j in _jobs.values())


def peek(folder: Path, firm: str = pc.DEFAULT_FIRM, preset=None, card=None) -> dict | None:
    """The cached card, or None; starts nothing (page layouts use this)."""
    return pc.cached_card(Path(folder), firm, preset, card)


def _argv(folder: Path, firm: str) -> list[str]:
    return [
        sys.executable, "-m", "backtester.risk.prop_card", folder.name, "--firm", firm,
        "--results-dir", str(folder.parent),
    ]  # fmt: skip


def request(
    folder: Path, firm: str = pc.DEFAULT_FIRM, preset=None, card=None,
    spawn: Callable = spawn_process, killer: Callable = kill_tree,
) -> dict:  # fmt: skip
    """{"state": "ready", "card"} | {"state": "running"/"queued", "elapsed"} |
    {"state": "error", "message"}; starts the calculation when nothing has it yet."""
    folder = Path(folder)
    cached = pc.cached_card(folder, firm, preset, card)
    if cached is not None:
        return {"state": "ready", "card": cached}
    key = (str(folder.parent), folder.name, firm)
    with _lock:
        job = _jobs.get(key)
        if job is not None and not job.finished:
            return {"state": "running", "elapsed": job.elapsed()}
        if job is not None:  # finished, yet no card: failed (kept; no restart loop)
            lines = job.lines()
            message = lines[-1] if lines and job.returncode else NO_CARD_TEXT
            return {"state": "error", "message": message}
        if any(not j.finished for j in _jobs.values()):
            return {"state": "queued", "elapsed": 0.0}
        _jobs[key] = ProcessJob.start(_argv(folder, firm), spawn=spawn, killer=killer)
        return {"state": "running", "elapsed": 0.0}
