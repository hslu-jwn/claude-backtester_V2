"""Single-instance lock for the live bot (ROADMAP 13.4): `results/live/bot.lock` holds the PID of
the running bot. A lock whose PID is no longer alive is stale and is taken over.

The bot takes the lock at startup (`bot.main`), the Live page's Start button looks at it
(`ui/pages/live.py start_bot`), so a double click or a bot stuck in connect backoff (no fresh
heartbeat yet) can never start a second bot and duplicate orders.
"""

from __future__ import annotations

import contextlib
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

LOCK_NAME = "bot.lock"
UNREADABLE_STALE_S = 10.0  # a lock without a PID this old is a leftover, not a bot starting up
_STILL_ACTIVE = 259
_ACCESS_DENIED = 5


def pid_alive(pid: int) -> bool:
    """Is a process with this PID running? (Never `os.kill(pid, 0)` on Windows: it kills.)"""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = wintypes.HANDLE
        handle = kernel.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return ctypes.get_last_error() == _ACCESS_DENIED  # exists, not ours to open
        try:
            code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                return True
            return code.value == _STILL_ACTIVE
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read_pid(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def lock_holder(path: Path, alive: Callable[[int], bool] = pid_alive) -> int | None:
    """The PID of the live bot holding the lock; None when there is no lock or it is stale. A
    fresh lock without a readable PID (another bot is just writing it) counts as held (-1)."""
    if not path.exists():
        return None
    pid = _read_pid(path)
    if pid is None:
        try:
            fresh = time.time() - path.stat().st_mtime < UNREADABLE_STALE_S
        except OSError:
            return None
        return -1 if fresh else None
    return pid if alive(pid) else None


class BotLock:
    def __init__(
        self, path: Path, alive: Callable[[int], bool] = pid_alive, pid: int | None = None
    ):
        self.path, self.alive = path, alive
        self.pid = os.getpid() if pid is None else pid

    def acquire(self) -> bool:
        """Take the lock. False: another live bot holds it. A stale lock is replaced."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(3):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                holder = lock_holder(self.path, self.alive)
                if holder is not None and holder != self.pid:
                    return False
                if holder is None:
                    with contextlib.suppress(OSError):
                        self.path.unlink()
                    continue
                return True  # our own PID: already ours
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(str(self.pid))
            return True
        return False

    def release(self) -> None:
        """Remove the lock if it is still ours."""
        if _read_pid(self.path) == self.pid:
            with contextlib.suppress(OSError):
                self.path.unlink()
