"""Results page of one backtest run: `/results/<run id>`. Spec: ROADMAP.md › 4.0 (placeholder
until 3.6): the summary table of `summary.json` (per symbol and combined, as the command
line prints it), the notes, the files in the run folder and the raw summary.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from dash import dcc, html

from backtester.run import format_summary
from backtester.runner import RESULTS_DIR

_RUN_ID = re.compile(r"^[A-Za-z0-9_.-]+$")


def run_folder(run_id: str, results_dir: Path = RESULTS_DIR) -> Path | None:
    """The run's folder, or None for a name that isn't a run folder (no paths outside)."""
    if not _RUN_ID.match(run_id or "") or run_id in (".", ".."):
        return None
    folder = Path(results_dir) / run_id
    return folder if (folder / "summary.json").is_file() else None


def layout(run_id: str, results_dir: Path = RESULTS_DIR) -> html.Div:
    back = dcc.Link("← Chart", href="/", className="rs-back")
    folder = run_folder(run_id, results_dir)
    if folder is None:
        return html.Div([back, html.H2("Run not found"), html.P(run_id)], className="rs-page")
    summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    files = sorted(p.name for p in folder.iterdir() if p.is_file())
    return html.Div(
        [
            back,
            html.H2(f"Backtest {summary.get('run_id', run_id)}"),
            html.P(
                f"{', '.join(summary.get('symbols', []))} · {summary.get('start')} to "
                f"{summary.get('end')} (UTC days) · results/{folder.name}"
            ),
            html.Pre(format_summary(summary), className="rs-table"),
            *(
                [html.H4("Notes"), html.Ul([html.Li(n) for n in summary["notes"]])]
                if summary.get("notes")
                else []
            ),
            html.H4("Files"),
            html.Ul([html.Li(f) for f in files]),
            html.Details([html.Summary("summary.json"), html.Pre(json.dumps(summary, indent=2))]),
            html.P("The full results page (trade list, equity curve) comes with step 3.6."),
        ],
        className="rs-page",
    )
