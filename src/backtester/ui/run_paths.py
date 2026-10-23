"""Resolve UI run identifiers for results, prop cards and Monte Carlo jobs."""

from __future__ import annotations

import re
from pathlib import Path

from backtester.paths import RESULTS_DIR

_RUN_ID = re.compile(r"[A-Za-z0-9_.-]+")
_VARIANT_ID = re.compile(r"research~([A-Za-z0-9_.-]+)~([A-Za-z0-9_.-]+)")


def run_folder(run_id: str, results_dir: Path = RESULTS_DIR) -> Path | None:
    """The run's folder, or None for a name that isn't a run folder (no paths outside).
    `research~<research id>~<variant id>` is a research variant's folder."""
    variant = _VARIANT_ID.fullmatch(run_id or "")
    if variant:
        if {".", ".."} & set(variant.groups()):
            return None
        folder = Path(results_dir) / "research" / variant[1] / "variants" / variant[2]
        return folder if (folder / "summary.json").is_file() else None
    if not _RUN_ID.fullmatch(run_id or "") or run_id in (".", ".."):
        return None
    folder = Path(results_dir) / run_id
    return folder if (folder / "summary.json").is_file() else None
