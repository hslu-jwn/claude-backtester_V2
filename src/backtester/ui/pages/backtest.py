"""Backtest page `/backtest` (ROADMAP 7.6): the running backtest with a large progress bar.

"Run" in the chart toolbar starts the backtest in the background (ui/backtest_job.py) and opens
this page. It shows the run's symbols, days, strategy and preset, a large bar with the percent,
the candles done of the total, the elapsed time and the ETA, and a **Cancel** button that
stops the run (nothing is saved for a cancelled run). The job lives on the server, so leaving
the page and coming back shows it again. When the run is done the page opens its results
(`/results/<run id>`); a failed or cancelled run stays here with its message until the next
run starts. **Cancel closes the running view** (user 2026-10-20): once the run has really
stopped the page swaps to the list of previous backtests with a short "Backtest cancelled"
line that fades out. Without a job the page is that list (newest first: date, strategy,
symbols, days, trades, net R; each row opens `/results/<run id>`), or "No backtest yet".
"""

from __future__ import annotations

from pathlib import Path

from dash import Dash, Input, Output, dcc, html, no_update

from backtester.paths import RESULTS_DIR
from backtester.ui import backtest_job as bj
from backtester.ui import layout as ui
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
    "timer_disabled", "page", "children",
)  # fmt: skip
CANCELLED_TOAST = "Cancelled"


def _meta(key: str, value: str) -> html.Span:
    return html.Span([html.Span(key, className="bj-meta-key"), value], className="bj-meta")


def _stat(key: str, id_: str, value: str) -> html.Div:
    return html.Div(
        [html.Div(key, className="bj-stat-key"), html.Div(value, id=id_, className="bj-stat-val")],
        className="bj-stat",
    )


def run_rows(results_dir: Path = RESULTS_DIR) -> list[dict]:
    """The previous backtests, newest first: one row per results folder with a readable
    summary.json (broken or empty ones are skipped)."""
    rows = []
    for option in results.list_runs(results_dir):
        run_id = option["value"]
        folder = Path(results_dir) / run_id
        summary = results._read_json(folder / "summary.json")
        if not summary:
            continue
        combined = summary.get("combined") or {}
        rows.append(
            {
                "id": run_id,
                "date": results.run_date(run_id, summary),
                "strategy": results.strategy_label(results._read_json(folder / "settings.json")),
                "symbols": ", ".join(summary.get("symbols", [])),
                "days": f"{summary.get('start')} → {summary.get('end')}",
                "trades": combined.get("trades"),
                "net_r": combined.get("net_r_net"),
            }
        )
    return rows


def runs_list(results_dir: Path = RESULTS_DIR, toast: str | None = None) -> html.Div:
    """The Backtest page without a running job: the previous backtests, each row a link."""
    rows = run_rows(results_dir)
    head = ["Date", "Strategy", "Symbols", "Days (UTC)", "Trades", "Net R"]
    body = [
        dcc.Link(
            [
                html.Span(r["date"]),
                html.Span(r["strategy"]),
                html.Span(r["symbols"]),
                html.Span(r["days"], className="bj-days"),
                html.Span("—" if r["trades"] is None else f"{r['trades']:,}", className="bj-num"),
                html.Span(
                    results.fmt_r(r["net_r"]), className=f"bj-num {results.tone(r['net_r'])}"
                ),
            ],
            href=f"{bj.RESULTS_PREFIX}{r['id']}",
            className="bj-row",
        )
        for r in rows
    ]
    title = "Backtests" if rows else NO_RUN_TEXT
    sub = (
        "Click a run to open its results."
        if rows
        else "Start one with Run in the chart's Backtest menu."
    )
    card = [html.Div([html.Span(title), ui.info(sub)], className="bj-list-head")]
    if rows:
        card += [
            html.Details(
                [html.Summary("More columns"), html.Span("Days (UTC)")],
                id="bj-more-columns",
                open=False,
                className="ui-details bj-column-toggle",
            ),
            html.Div(
                [html.Span(h, className="bj-days" if h == "Days (UTC)" else "") for h in head],
                className="bj-row bj-row-head",
            ),
            html.Div(body, className="bj-rows"),
        ]
    page = [
        ui.page(
            html.Div(card[0], className="ui-key-strip"),
            html.Div(card[1:], id="backtest-runs", className="bj-card"),
        ),
        risk_link(),
    ]
    if toast:
        page.insert(
            0,
            html.Div(
                toast,
                title="Backtest cancelled. Nothing was saved.",
                className="bj-toast",
                id="bj-toast",
            ),
        )
    return html.Div(page, className="bj-page")


def cancel_page(snap: dict, results_dir: Path = RESULTS_DIR):
    """The page for a poll that sees the cancel finished: the list of previous backtests with
    the toast, and the job is forgotten. Anything else: `no_update`."""
    if snap["state"] != "cancelled":
        return no_update
    bj.dismiss()
    return runs_list(results_dir, CANCELLED_TOAST)


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
        "message": snap["message"] if state == "error" else "",
        "cancel_disabled": not snap["cancellable"],
        "timer_disabled": state != "running",
        "page": snap["href"] if snap["href"] else no_update,
        "children": no_update,
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
                ],
                className="bj-actions",
            ),
        ],
        className="bj-card",
    )
    timer = dcc.Interval(id="bj-timer", interval=REFRESH_MS, disabled=out["timer_disabled"])
    # Move the existing components so callback targets remain mounted exactly once.
    head, metas, bar, detail, stats, message, actions = card.children
    head.children[0].className = "bj-state"
    head.children.append(metas)
    strip = html.Div(
        [head, *stats.children, actions], id="bj-key-strip", className="ui-key-strip bj-strip"
    )
    card.children = [bar, detail, message]
    return html.Div([timer, ui.page(strip, card), risk_link()], className="bj-page")


def risk_link():
    return dcc.Link(
        "Risk & prop firm: open a run's results",
        href="/backtest#backtest-runs",
        className="bj-risk-link",
    )


def press_cancel(clicks: int | None) -> bool:
    """The Cancel button: True when it stopped a running backtest."""
    return bool(clicks) and bj.cancel()


def page(results_dir: Path = RESULTS_DIR):
    """What `/backtest` shows: the running (or failed) job, else the list of previous
    backtests (after a cancel with the toast; the cancelled job is forgotten)."""
    job = bj.current()
    if job is not None:
        snap = bj.snapshot(job)
        if snap["state"] == "cancelled":
            return cancel_page(snap, results_dir)
        if snap["state"] != "done":
            return layout(snap)
        if snap["href"]:
            return results.layout(snap["href"].removeprefix(bj.RESULTS_PREFIX), results_dir)
    return runs_list(results_dir)


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
        Output("page", "children", allow_duplicate=True),
        Input("bj-timer", "n_intervals"),
        prevent_initial_call=True,
    )
    def _poll(_):
        job = bj.current()
        if job is None:  # the server was restarted while the page was open
            return (no_update,) * 9 + (True, no_update, no_update)
        snap = bj.snapshot(job)
        out = poll_outputs(snap)
        out["children"] = cancel_page(snap)
        return tuple(out[k] for k in POLL_KEYS)

    @app.callback(
        Output("bj-cancel", "children"),
        Input("bj-cancel", "n_clicks"),
        prevent_initial_call=True,
    )
    def _cancel(clicks):
        return "Cancelling …" if press_cancel(clicks) else no_update
