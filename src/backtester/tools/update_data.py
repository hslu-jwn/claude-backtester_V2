"""Bring the data caches up to yesterday (ROADMAP 7.5, the chart page's "Update data" button).

    python -m backtester.tools.update_data --dry-run     # print what would be fetched
    python -m backtester.tools.update_data               # fetch it

The plan (`data/update.py`): per cache and symbol everything after the last cached UTC day up
to yesterday. MT5 cache from the running terminal (one session for all symbols, like
`tools/mt5_download.py`), Binance for BTC / ETH-USDT, and histdata months once they are over
(plain form download + import, a captcha is reported and never worked around). A failing
symbol is reported and does not stop the others. Nothing runs at app start.

For the UI: `start_background() -> bool` (False when a job already runs) starts the job in a
daemon thread, `state() -> dict` is polled by the page:

    running      bool
    line         one short progress line, e.g. "MT5 US500 3/26 · 2026-10-15..2026-10-16"
    done         finished lines, one per symbol
    errors       error lines (a symbol without any cache is listed here too)
    finished_at  ISO UTC time of the last finished job, or None

No login is read or printed. This module is app level: it may import `live/`; the data layer
may not.
"""

from __future__ import annotations

import argparse
import threading
import time
from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, date, datetime

from backtester.data.update import (
    BINANCE,
    DEFAULT_CONFIG,
    HISTDATA,
    MT5,
    Plan,
    Task,
    UpdateConfig,
    histdata_pair,
    last_cached_day,
    plan_update,
    select_import_files,
)

LABELS = {MT5: "MT5", BINANCE: "Binance", HISTDATA: "histdata"}
NO_CACHE_PREFIX = "no cache"
NOTHING_TO_DO = "all caches are up to date"

Log = Callable[[str], None]
Download = Callable[[Task, Log], str]  # fetch one task, return a short summary


@dataclass(frozen=True)
class Backends:
    """What actually fetches. `mt5()` opens the terminal session once and yields the download
    function for all MT5 tasks; the others are called per task. Fakes in the tests."""

    mt5: Callable[[], AbstractContextManager[Download]]
    binance: Callable[[Task, Log, date], str]
    histdata: Download


# --- shared state ---------------------------------------------------------------------------


class Progress:
    """The thread-safe state of one job at a time (`snapshot()` is what the UI polls)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running = False
        self._line = ""
        self._done: list[str] = []
        self._errors: list[str] = []
        self._finished_at: str | None = None

    def begin(self) -> bool:
        """Start a job: False when one is already running. A new job clears the old lines."""
        with self._lock:
            if self._running:
                return False
            self._running, self._line = True, ""
            self._done, self._errors, self._finished_at = [], [], None
            return True

    def set_line(self, text: str) -> None:
        with self._lock:
            self._line = text

    def add_done(self, text: str) -> None:
        with self._lock:
            self._done.append(text)

    def add_error(self, text: str) -> None:
        with self._lock:
            self._errors.append(text)

    def finish(self) -> None:
        with self._lock:
            self._running, self._line = False, ""
            self._finished_at = datetime.now(UTC).isoformat(timespec="seconds")

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "running": self._running,
                "line": self._line,
                "done": list(self._done),
                "errors": list(self._errors),
                "finished_at": self._finished_at,
            }


# --- running a plan -------------------------------------------------------------------------


def _span(task: Task) -> str:
    return f"{task.first}..{task.last}"


def run_plan(plan: Plan, backends: Backends, progress: Progress, log: Log | None = None) -> None:
    """Fetch every task of `plan`; an error in one task is recorded and the rest still run.
    `log` additionally gets every progress line (the command line prints them)."""

    def say(text: str) -> None:
        progress.set_line(text)
        if log:
            log(text)

    def run_task(task: Task, position: str, download: Callable[[], str]) -> None:
        head = f"{LABELS[task.source]} {task.symbol}"
        say(f"{head} {position} · {_span(task)}")
        try:
            summary = download()
        except Exception as e:  # one symbol must not stop the others  # noqa: BLE001
            progress.add_error(f"{head}: {type(e).__name__}: {e}")
        else:
            progress.add_done(f"{head}: {summary}")

    for skip in plan.skipped:
        if skip.reason.startswith(NO_CACHE_PREFIX):  # needs the user: shown, the rest is noise
            progress.add_error(f"{LABELS[skip.source]} {skip.symbol}: {skip.reason}")
    by_source = {s: [t for t in plan.tasks if t.source == s] for s in (MT5, BINANCE, HISTDATA)}
    if not plan.tasks:
        progress.add_done(NOTHING_TO_DO)

    def line_log(task: Task, position: str) -> Log:
        return lambda text: say(f"{LABELS[task.source]} {task.symbol} {position} · {text}")

    mt5_tasks = by_source[MT5]
    if mt5_tasks:
        try:
            with backends.mt5() as download:
                for i, task in enumerate(mt5_tasks, 1):
                    pos = f"{i}/{len(mt5_tasks)}"
                    run_task(task, pos, lambda t=task, p=pos: download(t, line_log(t, p)))
        except Exception as e:  # the terminal could not be opened (or closed badly)  # noqa: BLE001
            progress.add_error(f"MT5: {type(e).__name__}: {e}")
    for i, task in enumerate(by_source[BINANCE], 1):
        pos = f"{i}/{len(by_source[BINANCE])}"
        run_task(task, pos, lambda t=task, p=pos: backends.binance(t, line_log(t, p), plan.today))
    for i, task in enumerate(by_source[HISTDATA], 1):
        pos = f"{i}/{len(by_source[HISTDATA])}"
        run_task(task, pos, lambda t=task, p=pos: backends.histdata(t, line_log(t, p)))


# --- real backends --------------------------------------------------------------------------


def mt5_backend(config: UpdateConfig = DEFAULT_CONFIG):
    from contextlib import contextmanager
    from datetime import timedelta

    @contextmanager
    def open_session():
        from backtester.data.adapters.mt5_adapter import Mt5Adapter
        from backtester.data.mt5_download import DEFAULT_CLOCK, DEFAULT_NAMES, download_symbol
        from backtester.live.connection import session
        from backtester.live.trading_settings import load_trading_settings

        settings = load_trading_settings()
        names = {**DEFAULT_NAMES, **{s: n for s, n in settings.symbols.items() if n != s}}
        clock = settings.server_clock or DEFAULT_CLOCK
        with session(settings, None) as mt5:
            adapter = Mt5Adapter(mt5, clock, names)

            def download(task: Task, log: Log) -> str:
                start = task.first - timedelta(days=config.mt5_overlap_days)
                r = download_symbol(adapter, task.symbol, start, task.last, log=log)
                if r.days_written == 0:
                    return "no new days (nothing recorded yet)"
                return f"{r.days_written} days {r.first_day}..{r.last_day} ({r.bars:,} bars)"

            yield download

    return open_session


def binance_backend(task: Task, log: Log, today: date) -> str:
    from backtester.data.binance import BinanceConfig, download_symbol

    results = download_symbol(
        task.symbol, task.first, task.last, BinanceConfig(), today=today, log=log
    )
    bars = sum(r.bars for r in results)
    missing = sum(r.missing_days for r in results)
    note = f", {missing} daily files not published yet" if missing else ""
    return f"{bars:,} bars{note}"


def histdata_backend(task: Task, log: Log) -> str:
    from backtester.data.cache import DEFAULT_CACHE_DIR
    from backtester.data.histdata import files_in, import_symbol
    from backtester.tools.histdata_download import DEFAULT_ROOT, RequestsClient, run

    last = last_cached_day(DEFAULT_CACHE_DIR, task.symbol)
    periods = [f"{m:%Y%m}" for m in task.months]
    out = run(RequestsClient(), [histdata_pair(task.symbol)], periods, DEFAULT_ROOT, log=log)
    wanted = set(task.months)
    files = select_import_files(files_in(DEFAULT_ROOT / task.symbol), last)
    if not any(f.month in wanted for f in files):
        why = "; ".join(f"{p}: {m}" for _, p, m in out.errors) or "not published or refused"
        raise RuntimeError(f"no histdata file for {periods[0]}..{periods[-1]} ({why})")
    result = import_symbol(task.symbol, files, DEFAULT_CACHE_DIR)
    notes = []
    if out.missing or out.errors or out.stopped:
        notes.append(f"{len(out.missing) + len(out.errors)} months not fetched")
    return f"{len(result.days_written)} days imported" + (f" ({', '.join(notes)})" if notes else "")


def real_backends(config: UpdateConfig = DEFAULT_CONFIG) -> Backends:
    return Backends(mt5=mt5_backend(config), binance=binance_backend, histdata=histdata_backend)


# --- the one background job -----------------------------------------------------------------

JOB = Progress()
_thread: threading.Thread | None = None


def state() -> dict:
    return JOB.snapshot()


def join(timeout: float | None = None) -> None:
    """Wait for the background job (tests, command line)."""
    thread = _thread
    if thread is not None:
        thread.join(timeout)


def _utc_today() -> date:
    return datetime.now(UTC).date()


def _job(backends: Backends, plan: Plan | Callable[[], Plan] | None) -> None:
    try:
        resolved = plan() if callable(plan) else plan or plan_update(_utc_today())
        run_plan(resolved, backends, JOB)
    except Exception as e:  # never leave the job "running"  # noqa: BLE001
        JOB.add_error(f"update failed: {type(e).__name__}: {e}")
    finally:
        JOB.finish()


def start_background(
    backends: Backends | None = None, plan: Plan | Callable[[], Plan] | None = None
) -> bool:
    """Start the update in a daemon thread; False when a job is already running.
    (`backends` / `plan` are for tests; the UI calls it without arguments.)"""
    global _thread
    if not JOB.begin():
        return False
    _thread = threading.Thread(
        target=_job, args=(backends or real_backends(), plan), name="update-data", daemon=True
    )
    _thread.start()
    return True


# --- command line ---------------------------------------------------------------------------


def format_plan(plan: Plan) -> str:
    lines = []
    for t in plan.tasks:
        what = ", ".join(f"{m:%Y-%m}" for m in t.months) if t.months else _span(t)
        lines.append(f"{LABELS[t.source]} {t.symbol} {what}")
    lines += [f"skip {s.source} {s.symbol}: {s.reason}" for s in plan.skipped]
    return "\n".join(lines) if plan.tasks else "\n".join(["nothing to do", *lines])


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="print the plan, fetch nothing")
    args = p.parse_args(argv)
    plan = plan_update(_utc_today())
    print(format_plan(plan), flush=True)
    if args.dry_run:
        return 0
    progress = Progress()
    progress.begin()
    started = time.monotonic()
    run_plan(plan, real_backends(), progress, log=lambda t: print(t, flush=True))
    progress.finish()
    s = progress.snapshot()
    print("\n".join(s["done"]), flush=True)
    if s["errors"]:
        print("ERRORS:\n" + "\n".join(s["errors"]), flush=True)
    print(f"finished in {time.monotonic() - started:.0f} s", flush=True)
    return 1 if s["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
