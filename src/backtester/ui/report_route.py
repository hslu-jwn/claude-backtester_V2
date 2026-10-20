"""Flask route that serves the Full Monte Carlo reports: `/monte-carlo/<run id>/report.html`.

Spec: ROADMAP 12.7 / 5.6. Only `report.html` and `summary.json` inside
`<results>/monte_carlo/<folder>/` are served: names with `..`, backslashes, a drive letter or a
leading slash are refused, and the resolved file must lie under the resolved root (a symlink
out of it is refused too). Everything else is a 404.
"""

from __future__ import annotations

from pathlib import Path

from flask import Flask, abort, send_file

from backtester.paths import RESULTS_DIR
from backtester.ui.monte_carlo_job import MONTE_CARLO_DIR, REPORT, REPORT_PREFIX, SUMMARY

SERVED = (REPORT, SUMMARY)


def safe_path(root: Path, name: str) -> Path | None:
    """The file `name` (folder/file) under `root`, or None when it isn't a served report file."""
    parts = name.split("/") if name else []
    if len(parts) != 2 or any(p in ("", ".", "..") or "\\" in p or ":" in p for p in parts):
        return None
    if parts[1] not in SERVED:
        return None
    base = Path(root).resolve()
    target = (base / parts[0] / parts[1]).resolve()
    if not target.is_relative_to(base) or not target.is_file():
        return None
    return target


def register(app: Flask, results_dir: Path = RESULTS_DIR) -> None:
    root = Path(results_dir) / MONTE_CARLO_DIR

    @app.route(f"{REPORT_PREFIX}<path:name>")
    def monte_carlo_report(name: str):
        target = safe_path(root, name)
        if target is None:
            abort(404)
        response = send_file(target, conditional=True)
        response.headers["Cache-Control"] = "no-cache"
        return response
