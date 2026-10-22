"""Folders shared by the app, the runner and the MT5 tools (anchored to the project root)."""

from __future__ import annotations

import os
from pathlib import Path


def home() -> Path:
    """Project repository root; set BACKTESTER_HOME before importing consumers to override."""
    if env := os.environ.get("BACKTESTER_HOME"):
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent.parent


def results_dir() -> Path:
    return home() / "results"


def data_dir() -> Path:
    return home() / "data"


HOME_DIR = home()
RESULTS_DIR = HOME_DIR / "results"
DATA_DIR = HOME_DIR / "data"
