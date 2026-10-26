"""Portable advisory file locks; independent of application layers."""

import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileLockConfig:
    timeout: float = 30
    poll: float = 0.05


DEFAULT_LOCK_CONFIG = FileLockConfig()


@contextmanager
def file_lock(path: Path, timeout: float = DEFAULT_LOCK_CONFIG.timeout):
    """Exclusive sidecar lock, released by the OS even after a process crashes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"\0")
            stream.flush()
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
