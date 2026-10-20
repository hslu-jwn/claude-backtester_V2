"""A child process started by the app and watched from its pages (no Dash imports).

Used by the prop-firm card (`prop_card_job.py`) and the Full Monte Carlo button
(`monte_carlo_job.py`). The process lives in the server process' memory (not in a browser
store), so leaving the page and coming back shows it again. Its stdout / stderr lines are kept
(the last `KEEP_LINES`) for progress text; `cancel` kills the process and its children.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from collections import deque
from collections.abc import Callable

KEEP_LINES = 200


def kill_tree(process) -> None:
    """Stop `process` and everything it started (the Monte Carlo tool runs worker processes)."""
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True, check=False,
        )  # fmt: skip
    else:
        process.terminate()


def spawn_process(argv: list[str], **kwargs):
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.Popen(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=flags,
        **kwargs,
    )


class ProcessJob:
    def __init__(self, process, killer: Callable, clock: Callable[[], float]):
        self._process = process
        self._killer = killer
        self._clock = clock
        self._lines: deque[str] = deque(maxlen=KEEP_LINES)
        self._lock = threading.Lock()
        self.started = clock()
        self.finished_at: float | None = None
        self.cancel_requested = False

    @classmethod
    def start(
        cls, argv: list[str], spawn: Callable = spawn_process, killer: Callable = kill_tree,
        clock: Callable[[], float] = time.monotonic,
    ) -> ProcessJob:  # fmt: skip
        env = {**os.environ, "PYTHONUNBUFFERED": "1"}
        job = cls(spawn(argv, env=env), killer, clock)
        threading.Thread(target=job._read, daemon=True).start()
        return job

    def _read(self) -> None:
        for raw in self._process.stdout:
            line = raw.rstrip("\r\n")
            if line.strip():
                with self._lock:
                    self._lines.append(line)

    @property
    def returncode(self) -> int | None:
        return self._process.poll()

    @property
    def finished(self) -> bool:
        done = self._process.poll() is not None
        if done and self.finished_at is None:
            self.finished_at = self._clock()
        return done

    def lines(self) -> list[str]:
        with self._lock:
            return list(self._lines)

    def elapsed(self, now: float | None = None) -> float:
        end = self.finished_at if self.finished_at is not None else (now or self._clock())
        return max(end - self.started, 0.0)

    def cancel(self) -> None:
        if self.cancel_requested or self.finished:
            return
        self.cancel_requested = True
        self._killer(self._process)
