"""Atomic queue JSON with bounded retries for Windows sharing violations."""

import json
import os
import tempfile
import time
from pathlib import Path

from backtester.filelock import file_lock  # noqa: F401 -- compatibility re-export
from backtester.jobs.config import DEFAULT_CONFIG


def retry_permission(action):
    deadline = time.monotonic() + DEFAULT_CONFIG.io_timeout
    while True:
        try:
            return action()
        except PermissionError:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise
            time.sleep(min(DEFAULT_CONFIG.io_poll, remaining))


def read_json(path: Path):
    def read():
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)

    return retry_permission(read)


def atomic_json(path: Path, data):
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
