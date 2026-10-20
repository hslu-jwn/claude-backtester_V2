"""The one backtest running in this server process, as the Backtest page shows it.

Spec: ROADMAP.md > 7.6. The job lives here (not in a browser store), so leaving the Backtest
page and coming back still shows it. One backtest at a time (`JobRunning` for a second
`start`). No Dash imports: the page (`pages/backtest.py`) only reads `snapshot`.

States of a snapshot: running (phase 1: candles are loaded, phase 2: run, then the results are
written; each phase has its own 0-100 % bar),
done (`href` = the results page), error (`message`), cancelled. A cancelled run writes no
results folder (`runner.BackgroundRun.cancel`).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

from backtester.runner import BackgroundRun, RunSettings, start_run
from backtester.strategy.registry import REGISTRY, strategy_name

RESULTS_PREFIX = "/results/"
ETA_MIN_SHARE = 0.02  # no ETA before this share of the candles is done (the first steps lie)
LOADING_TEXT = "Loading data · phase 1 of 2"
RUNNING_TEXT = "Running · phase 2 of 2"
CANCELLING_TEXT = "Cancelling …"
WRITING_TEXT = "Writing results …"
CANCELLED_TEXT = "Backtest cancelled. Nothing was saved."
NONE_TEXT = "—"


# a snapshot with nothing running: the page layout for Dash's validation layout
PLACEHOLDER = {
    "state": "running", "symbols": [], "days": "", "strategy": "", "preset": "", "percent": 0.0,
    "percent_text": "0%", "detail": "", "elapsed": NONE_TEXT, "eta": NONE_TEXT,
    "cancellable": True, "message": "", "href": None, "loading": False, "phase": "loading",
}  # fmt: skip


class JobRunning(RuntimeError):
    """A backtest is already running; only one runs at a time."""


@dataclass
class Job:
    run: BackgroundRun
    symbols: tuple[str, ...]
    start: date
    end: date
    strategy: str  # label, e.g. "Strategy 6 · Opening-range breakout"
    preset: str
    started: float
    finished_at: float | None = None
    cancel_requested: bool = False


_lock = threading.Lock()
_current: Job | None = None


def current() -> Job | None:
    """The newest job of this server process (running or finished), or None."""
    return _current


def reset() -> None:
    """Forget the job (tests)."""
    global _current
    with _lock:
        _current = None


def dismiss() -> None:
    """Forget a finished job (the page closes its view after a cancel); a running one stays."""
    global _current
    with _lock:
        if _current is not None and _current.run.finished:
            _current = None


def is_running() -> bool:
    return _current is not None and not _current.run.finished


def start(
    symbols,
    first: date,
    last: date,
    settings: RunSettings | None,
    sources,
    preset: str | None,
    starter: Callable[..., BackgroundRun] = start_run,
    clock: Callable[[], float] = time.monotonic,
) -> Job:
    """Start a backtest in the background; `JobRunning` while another one runs."""
    global _current
    with _lock:
        if _current is not None and not _current.run.finished:
            raise JobRunning("A backtest is already running.")
        settings = settings or RunSettings()
        run = starter(list(symbols), first, last, settings=settings, sources=sources, preset=preset)
        _current = Job(
            run,
            tuple(symbols),
            first,
            last,
            REGISTRY[strategy_name(settings.strategy)].label,
            preset or "Default",
            clock(),
        )
        return _current


def cancel() -> bool:
    """Ask the running backtest to stop; False when none runs."""
    job = _current
    if job is None or job.run.finished:
        return False
    job.cancel_requested = True
    job.run.cancel()
    return True


# --- numbers for the page --------------------------------------------------------------


def percent(done: int, total: int) -> float:
    """0-100: the share of the candles done (0 while the total isn't known)."""
    return min(done / total, 1.0) * 100 if total else 0.0


def eta_seconds(done: int, total: int, elapsed: float) -> float | None:
    """Seconds left, from the pace so far; None until enough is done to tell."""
    if not total or done / total < ETA_MIN_SHARE:
        return None
    return max(elapsed * (total - done) / done, 0.0)


def format_duration(seconds: float | None) -> str:
    """ "1:05" or "1:02:05"; "—" for None."""
    if seconds is None:
        return NONE_TEXT
    s = int(seconds)
    h, rest = divmod(s, 3600)
    m, sec = divmod(rest, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def error_message(error: BaseException) -> str:
    """An error as a sentence: a KeyError's text without its quotes, the type if it has none."""
    text = str(error.args[0]) if isinstance(error, KeyError) and error.args else str(error)
    return text or type(error).__name__


def snapshot(job: Job, now: float | None = None) -> dict:
    """Everything the page shows for `job`, as plain values."""
    run = job.run
    finished = run.finished
    if finished and job.finished_at is None:
        job.finished_at = now if now is not None else time.monotonic()
    end = (
        job.finished_at
        if job.finished_at is not None
        else (now if now is not None else time.monotonic())
    )
    elapsed = max(end - job.started, 0.0)
    done, total = run.done, run.total
    phase = "running" if total > 0 else "loading"
    phase_start = job.started  # the ETA of a phase counts from when that phase began
    if phase == "loading":  # the bar shows the loading phase until the run reports
        done, total = run.load_done, run.load_total
    else:
        phase_start = getattr(run, "load_finished_at", None) or job.started
    if not finished:
        state = "running"
    elif run.error is not None:
        state = "error"
    elif run.cancelled:
        state = "cancelled"
    else:
        state = "done"
    writing = state == "running" and phase == "running" and done >= total
    cancelling = state == "running" and job.cancel_requested
    pct = 100.0 if state == "done" else percent(done, total)
    if state == "running":
        if cancelling:
            detail = CANCELLING_TEXT
        elif writing:
            detail = WRITING_TEXT
        elif phase == "loading":
            detail = LOADING_TEXT
        else:
            detail = f"{RUNNING_TEXT} · {done:,} of {total:,} candles"
    else:
        detail = f"{done:,} of {total:,} candles" if phase == "running" else ""
    message = ""
    if state == "error":
        message = error_message(run.error)
    elif state == "cancelled":
        message = CANCELLED_TEXT
    return {
        "state": state,
        "symbols": list(job.symbols),
        "days": f"{job.start} → {job.end}",
        "strategy": job.strategy,
        "preset": job.preset,
        "percent": pct,
        "percent_text": f"{pct:.0f}%",
        "detail": detail,
        "elapsed": format_duration(elapsed),
        "eta": format_duration(eta_seconds(done, total, max(end - phase_start, 0.0)))
        if state == "running"
        else NONE_TEXT,
        "phase": phase,
        "loading": state == "running" and phase == "loading" and total == 0,  # nothing reported
        "cancellable": state == "running" and not writing and not cancelling,
        "message": message,
        "href": f"{RESULTS_PREFIX}{run.folder.name}" if state == "done" and run.folder else None,
    }
