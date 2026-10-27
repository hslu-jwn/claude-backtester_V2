"""Atomic queue JSON with bounded retries for Windows sharing violations."""

import json
from pathlib import Path

from backtester.filelock import atomic_json, file_lock  # noqa: F401 -- re-exports
from backtester.filelock import retry_permission as _retry
from backtester.jobs.config import DEFAULT_CONFIG


def retry_permission(action):
    return _retry(action, DEFAULT_CONFIG.io_timeout, DEFAULT_CONFIG.io_poll)


def read_json(path: Path):
    def read():
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)

    return retry_permission(read)
