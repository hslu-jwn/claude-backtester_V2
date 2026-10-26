"""Queue panel of the Research page: key strip, runner buttons, queue-a-grid, compact job list.

Spec: briefs/v26c-cards-lanes.md section C (user decisions 2026-10-26); logic in
`ui/queue_model.py` (no Dash there). The panel refreshes every 5 s with a `dcc.Interval` that
exists only while the page is open. Elapsed times and log tails update in place (their own
callback), so an open log `details()` is not collapsed by a refresh; the job rows themselves are
rebuilt only when a job changes state or attempts.
"""

from __future__ import annotations

from datetime import UTC, datetime

from dash import ALL, Dash, Input, Output, State, ctx, dcc, html, no_update

from backtester.ui import queue_model as qm
from backtester.ui.layout import details, info, key_strip

REFRESH_MS = 5000
TITLE = "Queue"
HINT = (
    "Heavy jobs (research pipelines) run one after another in a background runner. The runner "
    "keeps running after you close this page; stop it with Stop. The one-time MT5 test of a "
    "variant is started from the command line only."
)
START_HINT = "Start one background runner with 8 workers (only one runner can exist)"
STOP_HINT = "Finish the running jobs, then the runner exits; no new job starts"
GRID_HINT = "Queue the research pipeline (development period only) of a grid file"
PLACEHOLDER = "Queue a grid …"
CANCEL_ID, RETRY_ID, ELAPSED_ID, LOG_ID = "qp-cancel", "qp-retry", "qp-elapsed", "qp-log"


def _button(label, component_id, hint, **kwargs):
    return html.Button(
        label, id=component_id, n_clicks=0, title=hint, className="rr-button qp-button", **kwargs
    )


def job_row(job, now: datetime) -> html.Div:
    chip_title = qm.job_state_text(job) if job.state in ("failed", "cancelled") else job.state
    actions = []
    if job.state in qm.ACTIVE:
        actions.append(
            html.Button(
                "Cancel",
                id={"type": CANCEL_ID, "job": job.id},
                n_clicks=0,
                className="rr-button qp-button",
            )
        )
    if job.state in ("failed", "cancelled"):
        actions.append(
            html.Button(
                "Retry",
                id={"type": RETRY_ID, "job": job.id},
                n_clicks=0,
                className="rr-button qp-button",
            )
        )
    return html.Div(
        [
            html.Div(
                [
                    html.Span(job.name, className="qp-name", title=job.id),
                    html.Span(job.state, className=f"qp-chip qp-{job.state}", title=chip_title),
                    html.Span(
                        qm.elapsed_text(job, now),
                        id={"type": ELAPSED_ID, "job": job.id},
                        className="qp-elapsed",
                        title="Elapsed",
                    ),
                    html.Span(
                        f"{job.attempts} / {job.max_attempts}",
                        className="qp-attempts",
                        title="Attempts used / allowed",
                    ),
                    *actions,
                ],
                className="qp-row-main",
            ),
            details(
                "log",
                html.Pre(
                    qm.log_tail(job.log),
                    id={"type": LOG_ID, "job": job.id},
                    className="qp-log-text",
                ),
            ),
        ],
        className=f"qp-row qp-row-{job.state}",
    )


FINISHED = ("done", "cancelled")


def _capped(jobs: list, now: datetime) -> list:
    rows = [job_row(j, now) for j in jobs[: qm.MAX_ROWS]]
    if len(jobs) > qm.MAX_ROWS:
        rows.append(html.Div(f"{len(jobs) - qm.MAX_ROWS} more", className="qp-empty"))
    return rows


def job_list(jobs: list, now: datetime):
    """Running, pending and failed jobs visible; finished ones in a closed "Finished (N)"
    section (V2.5: essentials visible, the rest behind Details)."""
    shown = qm.ordered_jobs(jobs)
    if not shown:
        return [html.Div(qm.NO_JOBS, className="qp-empty")]
    active = [j for j in shown if j.state not in FINISHED]
    finished = [j for j in shown if j.state in FINISHED]
    rows = _capped(active, now)
    if finished:
        rows.append(details(f"Finished ({len(finished)})", html.Div(_capped(finished, now))))
    return rows


def signature(jobs: list) -> list:
    return [[j.id, j.state, j.attempts] for j in jobs]


def view(ops: qm.QueueOps) -> dict:
    """Everything the refresh callback sets, read once."""
    snap = qm.snapshot(ops)
    jobs = ops.queue.jobs()
    snap["broken"] = list(ops.queue.broken)
    return {
        "keys": key_strip(qm.key_items(snap)),
        "start_disabled": snap["runner_alive"] or ops.starting(),
        "stop_disabled": not snap["runner_alive"],
        "jobs": job_list(jobs, datetime.now(UTC)),
        "signature": signature(jobs),
    }


def layout(ops: qm.QueueOps) -> html.Div:
    state = view(ops)
    return html.Div(
        [
            html.Div([html.Span(TITLE, className="rr-title"), info(HINT)], className="rr-head"),
            html.Div(state["keys"], id="qp-keys"),
            html.Div(
                [
                    _button(
                        "Start runner", "qp-start", START_HINT, disabled=state["start_disabled"]
                    ),
                    _button("Stop", "qp-stop", STOP_HINT, disabled=state["stop_disabled"]),
                    dcc.Dropdown(
                        id="qp-grid",
                        options=ops.grids(),
                        value=None,
                        placeholder=PLACEHOLDER,
                        className="rr-select qp-grid",
                    ),
                    _button("Queue pipeline", "qp-queue-grid", GRID_HINT),
                ],
                className="rr-controls",
            ),
            html.Div("", id="qp-message", className="qp-message", role="status"),
            html.Div(state["jobs"], id="qp-jobs", className="qp-jobs"),
            dcc.Store(id="qp-signature", data=state["signature"]),
            dcc.Store(id="qp-nonce", data=0),
            dcc.Interval(id="qp-interval", interval=REFRESH_MS),
        ],
        id="qp-panel",
        className="qp-panel",
    )


def dispatch(ops: qm.QueueOps, triggered, value, grid) -> str | None:
    """Run the action of the clicked button. `value` is the clicked n_clicks (a button that
    was only re-rendered has 0 / None and does nothing). Returns the message, or None."""
    if not value:
        return None
    if triggered == "qp-start":
        return ops.start()
    if triggered == "qp-stop":
        return ops.stop()
    if triggered == "qp-queue-grid":
        return ops.queue_grid(grid)
    if isinstance(triggered, dict):
        if triggered.get("type") == CANCEL_ID:
            return ops.cancel(triggered.get("job"))
        if triggered.get("type") == RETRY_ID:
            return ops.retry(triggered.get("job"))
    return None


def register_callbacks(app: Dash, ops: qm.QueueOps) -> None:
    @app.callback(
        Output("qp-message", "children"),
        Output("qp-nonce", "data"),
        Input("qp-start", "n_clicks"),
        Input("qp-stop", "n_clicks"),
        Input("qp-queue-grid", "n_clicks"),
        Input({"type": CANCEL_ID, "job": ALL}, "n_clicks"),
        Input({"type": RETRY_ID, "job": ALL}, "n_clicks"),
        State("qp-grid", "value"),
        State("qp-nonce", "data"),
        prevent_initial_call=True,
    )
    def _act(_start, _stop, _queue, _cancel, _retry, grid, nonce):
        value = ctx.triggered[0]["value"] if ctx.triggered else None
        message = dispatch(ops, ctx.triggered_id, value, grid)
        if message is None:
            return no_update, no_update
        return message, (nonce or 0) + 1

    @app.callback(
        Output("qp-keys", "children"),
        Output("qp-start", "disabled"),
        Output("qp-stop", "disabled"),
        Output("qp-jobs", "children"),
        Output("qp-signature", "data"),
        Input("qp-interval", "n_intervals"),
        Input("qp-nonce", "data"),
        State("qp-signature", "data"),
    )
    def _refresh(_tick, _nonce, previous):
        state = view(ops)
        same = previous == state["signature"]
        return (
            state["keys"],
            state["start_disabled"],
            state["stop_disabled"],
            no_update if same else state["jobs"],
            no_update if same else state["signature"],
        )

    @app.callback(
        Output({"type": ELAPSED_ID, "job": ALL}, "children"),
        Output({"type": LOG_ID, "job": ALL}, "children"),
        Input("qp-interval", "n_intervals"),
        Input("qp-nonce", "data"),
    )
    def _live(_tick, _nonce):
        jobs = {j.id: j for j in ops.queue.jobs()}
        now = datetime.now(UTC)
        elapsed, logs = ctx.outputs_list
        return (
            [qm.elapsed_text(jobs[o["id"]["job"]], now) if o["id"]["job"] in jobs else no_update
             for o in elapsed],
            [qm.log_tail(jobs[o["id"]["job"]].log) if o["id"]["job"] in jobs else no_update
             for o in logs],
        )  # fmt: skip
