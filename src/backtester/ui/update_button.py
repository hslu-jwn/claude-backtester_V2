"""The chart toolbar's "Update data" button (ROADMAP 7.5).

A click starts `tools/update_data` in its one background thread (a click while it runs does
nothing); an interval polls its state and shows the current line, then "Updated n · k errors"
(the error lines in the tooltip). Nothing runs when the app starts.
"""

from __future__ import annotations

from dash import Dash, Input, Output, ctx, dcc, html

from backtester.tools import update_data

POLL_MS = 2000
BUTTON_ID, STATUS_ID, TICK_ID = "update-btn", "update-status", "update-tick"


def layout() -> list:
    """Button, status text and the poll interval (off until a job runs)."""
    return [
        html.Button(
            "⟳ Update data",
            id=BUTTON_ID,
            title="Update the MT5, Binance and histdata caches",
            className="tb-btn tb-update",
            n_clicks=0,
        ),
        html.Span(id=STATUS_ID, className="tb-update-status"),
        dcc.Interval(id=TICK_ID, interval=POLL_MS, disabled=True),
    ]


def refresh(trigger: str | None) -> dict:
    """Start the job when the button was clicked, then describe the job state for the UI."""
    if trigger == BUTTON_ID:
        update_data.start_background()  # False while one runs: nothing else to do
    s = update_data.state()
    if s["running"]:
        text, title = s["line"] or "Updating...", ""
    elif s["finished_at"]:
        n = len(s["errors"])
        text = f"Updated {len(s['done'])} · {n} error{'' if n == 1 else 's'}"
        title = "\n".join(s["errors"])
    else:
        text, title = "", ""
    return {
        "text": text,
        "title": title,
        "button_disabled": bool(s["running"]),
        "interval_disabled": not s["running"],
    }


def register_callbacks(app: Dash) -> None:
    @app.callback(
        Output(STATUS_ID, "children"),
        Output(STATUS_ID, "title"),
        Output(BUTTON_ID, "disabled"),
        Output(TICK_ID, "disabled"),
        Input(BUTTON_ID, "n_clicks"),
        Input(TICK_ID, "n_intervals"),
    )
    def _update(_clicks, _ticks):
        v = refresh(ctx.triggered_id)
        return v["text"], v["title"], v["button_disabled"], v["interval_disabled"]
