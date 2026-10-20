"""Backtest page `/backtest` (ROADMAP 7.6): the running backtest with a large progress bar.

"Run" in the chart toolbar starts the backtest in the background (ui/backtest_job.py) and opens
this page. It shows the run's symbols, days, strategy and preset, a large bar with the percent,
the candles done of the total, the elapsed time and the ETA, and a **Cancel** button that
stops the run (nothing is saved for a cancelled run). The job lives on the server, so leaving
the page and coming back shows it again. When the run is done the page opens its results
(`/results/<run id>`); a failed or cancelled run stays here with its message until the next
run starts. Without a job the page shows the newest results, or "No backtest yet".
"""

from __future__ import annotations

from pathlib import Path

from dash import Dash, Input, Output, dcc, html, no_update

from backtester.paths import RESULTS_DIR
from backtester.ui import backtest_job as bj
from backtester.ui.pages import results

PATH = "/backtest"
REFRESH_MS = 500
TITLES = {
    "running": "Backtest running",
    "done": "Backtest done",
    "error": "Backtest failed",
    "cancelled": "Backtest cancelled",
}
NO_RUN_TEXT = "No backtest yet"
POLL_KEYS = (
    "title", "track", "fill", "pct", "detail", "elapsed", "eta", "message", "cancel_disabled",
    "timer_disabled", "page",
)  # fmt: skip


def _meta(key: str, value: str) -> html.Span:
    return html.Span([html.Span(key, className="bj-meta-key"), value], className="bj-meta")


def _stat(key: str, id_: str, value: str) -> html.Div:
    return html.Div(
        [html.Div(key, className="bj-stat-key"), html.Div(value, id=id_, className="bj-stat-val")],
        className="bj-stat",
    )


def poll_outputs(snap: dict) -> dict:
    """What the page shows for a snapshot, one value per output."""
    state = snap["state"]
    return {
        "title": TITLES[state],
        "track": "bj-track bj-loading" if snap["loading"] else "bj-track",
        "fill": {"width": f"{snap['percent']:.1f}%"},
        "pct": snap["percent_text"],
        "detail": snap["detail"],
        "elapsed": snap["elapsed"],
        "eta": snap["eta"],
        "message": snap["message"],
        "cancel_disabled": not snap["cancellable"],
        "timer_disabled": state != "running",
        "page": snap["href"] if snap["href"] else no_update,
        "state": state,
    }


def layout(snap: dict) -> html.Div:
    """The page for one snapshot of the job (`backtest_job.snapshot`); the callbacks keep
    it up to date in the browser."""
    out = poll_outputs(snap)
    card = html.Div(
        [
            html.Div(
                [
                    html.Div(out["title"], id="bj-title", className="bj-title"),
                    html.Div(snap["strategy"], className="bj-strategy"),
                ],
                className="bj-head",
            ),
            html.Div(
                [
                    _meta("Symbols", ", ".join(snap["symbols"])),
                    _meta("Days (UTC)", snap["days"]),
                    _meta("Preset", snap["preset"]),
                ],
                className="bj-metas",
            ),
            html.Div(
                [
                    html.Div(
                        html.Div(id="bj-fill", className="bj-fill", style=out["fill"]),
                        id="bj-track",
                        className=out["track"],
                    ),
                    html.Div(out["pct"], id="bj-pct", className="bj-pct"),
                ],
                className="bj-barrow",
            ),
            html.Div(out["detail"], id="bj-detail", className="bj-detail"),
            html.Div(
                [
                    _stat("Elapsed", "bj-elapsed", out["elapsed"]),
                    _stat("Time left (ETA)", "bj-eta", out["eta"]),
                ],
                className="bj-stats",
            ),
            html.Div(out["message"], id="bj-message", className="bj-message"),
            html.Div(
                [
                    html.Button(
                        "Cancel backtest",
                        id="bj-cancel",
                        className="bj-cancel",
                        n_clicks=0,
                        disabled=out["cancel_disabled"],
                    ),
                    dcc.Link("← Chart", href="/", className="bj-back"),
                ],
                className="bj-actions",
            ),
        ],
        className="bj-card",
    )
    timer = dcc.Interval(id="bj-timer", interval=REFRESH_MS, disabled=out["timer_disabled"])
    return html.Div([timer, card], className="bj-page")


def press_cancel(clicks: int | None) -> bool:
    """The Cancel button: True when it stopped a running backtest."""
    return bool(clicks) and bj.cancel()


def page(results_dir: Path = RESULTS_DIR):
    """What `/backtest` shows: the running (or failed / cancelled) job, else the newest results."""
    job = bj.current()
    if job is not None:
        snap = bj.snapshot(job)
        if snap["state"] != "done":
            return layout(snap)
        if snap["href"]:
            return results.layout(snap["href"].removeprefix(bj.RESULTS_PREFIX), results_dir)
    runs = results.list_runs(results_dir)
    if runs:
        return results.layout(runs[0]["value"], results_dir)
    return html.Div(
        [
            html.Div(
                [
                    html.Div(NO_RUN_TEXT, className="bj-title"),
                    html.Div("Start one with Run in the chart's Backtest menu.",
                             className="bj-strategy"),
                    dcc.Link("← Chart", href="/", className="bj-back"),
                ],
                className="bj-card",
            )
        ],
        className="bj-page",
    )  # fmt: skip


def register_callbacks(app: Dash) -> None:
    @app.callback(
        Output("bj-title", "children"),
        Output("bj-track", "className"),
        Output("bj-fill", "style"),
        Output("bj-pct", "children"),
        Output("bj-detail", "children"),
        Output("bj-elapsed", "children"),
        Output("bj-eta", "children"),
        Output("bj-message", "children"),
        Output("bj-cancel", "disabled"),
        Output("bj-timer", "disabled"),
        Output("url", "pathname", allow_duplicate=True),
        Input("bj-timer", "n_intervals"),
        prevent_initial_call=True,
    )
    def _poll(_):
        job = bj.current()
        if job is None:  # the server was restarted while the page was open
            return (no_update,) * 9 + (True, no_update)
        out = poll_outputs(bj.snapshot(job))
        return tuple(out[k] for k in POLL_KEYS)

    @app.callback(
        Output("bj-cancel", "children"),
        Input("bj-cancel", "n_clicks"),
        prevent_initial_call=True,
    )
    def _cancel(clicks):
        return "Cancelling …" if press_cancel(clicks) else no_update
