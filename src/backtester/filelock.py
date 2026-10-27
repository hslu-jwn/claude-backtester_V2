"""Portable advisory file locks; independent of application layers."""

import json
import os
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileLockConfig:
    timeout: float = 30
    poll: float = 0.05


DEFAULT_LOCK_CONFIG = FileLockConfig()


def retry_permission(action, timeout: float = 5, poll: float = 0.05):
    """Retry `action` while Windows refuses a file another process has open (PermissionError)."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            return action()
        except PermissionError:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise
            time.sleep(min(poll, remaining))


def atomic_json(path: Path, data) -> None:
    """Write JSON to a unique temporary file, then replace `path` (retrying Windows sharing)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        retry_permission(lambda: os.replace(name, path))
    finally:
        Path(name).unlink(missing_ok=True)


def symbol_mutation_lock(cache_dir: Path, symbol: str) -> Path:
    """Shared exclusion for MT5 day writers and offline repair capture/publication."""
    if not symbol.isalnum() or symbol != symbol.upper():
        raise ValueError("expected an uppercase alphanumeric symbol")
    return Path(cache_dir) / "_v26b_locks" / f"{symbol}.lock"


@contextmanager
def file_lock(path: Path, timeout: float = DEFAULT_LOCK_CONFIG.timeout):
    """Exclusive sidecar lock, released by the OS even after a process crashes.

    The file stays empty: Windows may lock byte 0 past the end of the file, and writing a padding
    byte raced with another process already holding that byte (PermissionError on flush).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        deadline = time.monotonic() + timeout
        while True:
            try:
                stream.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Timed out acquiring file lock: {path.name}") from exc
                time.sleep(DEFAULT_LOCK_CONFIG.poll)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
