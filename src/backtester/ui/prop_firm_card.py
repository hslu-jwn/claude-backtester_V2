"""The "Prop firm" card and the "Full Monte Carlo" block on a backtest's results page.

Spec: risk-management.md > Prop-firm field (where it shows; decided by the user 2026-10-20),
ROADMAP 5.6 / 12.7.

- **Prop firm card:** pass probability (both phases), fails split daily loss / max loss, average
  and median days to pass and the chance the funded account is lost, at 0.5 / 1 / 1.5 % base
  risk, each with a "fixed" and an "adaptive" column (ROADMAP 5.7; the adaptive one also shows the
  share of trades skipped by the daily budget), from the day reshuffle Monte Carlo of the run's R
  trades (`risk/prop_card.py`). The firm is a dropdown
  (`risk.prop_card.FIRMS`; FTMO 2-Step so far). A big run takes 20-30 s, so the numbers are
  computed in a background process once and cached in the run folder (`ui/prop_card_job.py`);
  the card shows "Calculating" until then. A page build only reads the cache; the first poll
  starts the calculation.
- **Full Monte Carlo:** runs the whole report (`tools/monte_carlo --run`) in the background
  (`ui/monte_carlo_job.py`, ~35 min); progress, Cancel, "Open report" in a new tab
  (`ui/report_route.py`), "Run again". Survives leaving the page.
"""

from __future__ import annotations

from pathlib import Path

from dash import Dash, Input, Output, State, dcc, html, no_update

from backtester.paths import RESULTS_DIR
from backtester.risk import prop_card
from backtester.ui import monte_carlo_job as mj
from backtester.ui import prop_card_job as pj
from backtester.ui.monte_carlo_job import format_elapsed
from backtester.ui.run_paths import run_folder

PERCENT = 100.0
DASH = "—"
CARD_REFRESH_MS = 1000
MC_REFRESH_MS = 1000
HIDDEN = {"display": "none"}
CARD_ROWS = (
    "Pass probability (both phases)",
    "Failed: daily loss",
    "Failed: max loss",
    "Average days to pass",
    "Median days to pass",
    "Trades skipped by the daily budget",
)
MODES = ("Fixed", "Adaptive")
HOW_TEXT = (
    "Estimated by reshuffling the {days} trading days {runs:,} times and playing every order as "
    "{label} challenge attempts (Phase 1, Phase 2, then a funded account). Trades still open "
    "count as if at their stop, so the daily-loss check is conservative and the pass rate a "
    "little too low. Pass probability uses finished attempts; unfinished attempts are shown "
    "as a share of all attempts. Passing days are played to their end. "
    "Adaptive: open trades reserve their initial risk; the risk shrinks with the room to the "
    "max-loss line (down to {floor:g} x the base risk, never above it). New entries fit a daily "
    "budget of {budget:g} % of the initial balance (trades that do not fit are skipped)."
)
WAITING_TEXT = "Waiting for another calculation to finish …"


def _pct(value: float | None, digits: int = 1) -> str:
    return DASH if value is None else f"{value * PERCENT:.{digits}f} %"


def _share(count: int, attempts: int) -> str:
    return DASH if not attempts else f"{count / attempts * PERCENT:.0f} %"


def _risk_label(risk: float) -> str:
    return f"{risk * PERCENT:g} % risk"


def _days(value: float | None) -> str:
    return DASH if value is None else f"{value:.0f}"


def _skipped(row: dict) -> str:
    """Share of the trades the daily budget skipped (adaptive lines only)."""
    return _share(row.get("skipped_trades", 0), row.get("trades_seen", 0))


def _table(card: dict) -> html.Table:
    fixed = card["rows"]
    adaptive = card.get("adaptive_rows") or [None] * len(fixed)
    # one column per (base risk, mode): fixed first, then adaptive
    cols = [c for f, a in zip(fixed, adaptive, strict=True) for c in ((f, False), (a, True))
            if c[0] is not None]  # fmt: skip
    funded = f"Funded account lost within {card['funded_days']} days"
    cells = [
        (CARD_ROWS[0], [_pct(r["pass_probability"]) if r["attempts"] else DASH for r, _ in cols]),
        ("Unfinished attempts (share of all)", [_pct(r.get("unfinished_share")) for r, _ in cols]),
        (CARD_ROWS[1], [_share(r["fail_daily"], r.get("total_attempts", r["attempts"])) for r, _ in cols]),
        (CARD_ROWS[2], [_share(r["fail_max"], r.get("total_attempts", r["attempts"])) for r, _ in cols]),
        (CARD_ROWS[3], [_days(r.get("average_days_to_pass")) for r, _ in cols]),
        (CARD_ROWS[4], [_days(r["median_days_to_pass"]) for r, _ in cols]),
        (funded, [_pct(r["funded_lost_probability"]) for r, _ in cols]),
    ]  # fmt: skip
    if card.get("adaptive_rows"):
        cells.append(
            (CARD_ROWS[5], [_skipped(r) if is_adaptive else DASH for r, is_adaptive in cols])
        )
    modes = 2 if card.get("adaptive_rows") else 1
    head = html.Thead([
        html.Tr([html.Th("")] + [html.Th(_risk_label(r["risk"]), colSpan=modes) for r in fixed]),
        html.Tr([html.Th("")] + [html.Th(MODES[int(is_a)]) for _, is_a in cols],
                className="pf-modes"),
    ])  # fmt: skip
    body = html.Tbody([html.Tr([html.Td(label)] + [html.Td(v) for v in values])
                       for label, values in cells])  # fmt: skip
    return html.Table([head, body], className="rs-table pf-table")


def card_body(status: dict) -> html.Div:
    """The card's content for a `prop_card_job.request` answer."""
    state = status["state"]
    if state in ("running", "queued"):
        text = (
            f"Calculating … {format_elapsed(status.get('elapsed', 0.0))}"
            if state == "running"
            else WAITING_TEXT
        )
        return html.Div(
            [html.Div(text, className="pf-note"), html.Div(html.Div(className="pf-bar-run"),
                                                             className="pf-bar")]
        )  # fmt: skip
    if state == "error":
        return html.Div(f"Could not calculate: {status['message']}", className="pf-note pf-error")
    card = status["card"]
    if card["status"] != "ok":
        return html.Div(card["reason"], className="pf-note")
    ad = card.get("adaptive") or {"floor": 0.0, "daily_budget": 0.0}
    how = HOW_TEXT.format(days=card["days"], runs=card["runs"], label=card["label"],
                          floor=ad["floor"], budget=ad["daily_budget"] * PERCENT)  # fmt: skip
    return html.Div([_table(card), html.Div(how, className="pf-how")])


def timer_disabled(status: dict) -> bool:
    return status["state"] not in ("running", "queued")


def poll_card(run_id: str | None, firm: str, results_dir: Path = RESULTS_DIR):
    """(card content, timer disabled) for one poll; starts the calculation when none exists."""
    folder = run_folder(run_id, results_dir)
    if folder is None or not (folder / "trades.csv").is_file():
        return no_update, True
    status = pj.request(folder, firm)
    return card_body(status), timer_disabled(status)


# ---- Full Monte Carlo --------------------------------------------------------------------


def mc_outputs(snap: dict) -> dict:
    """What the Monte Carlo block shows for a `monte_carlo_job.snapshot`."""
    state = snap["state"]
    running = state == "running"
    if running:
        status = f"{snap['detail']} · {snap['elapsed']}"
    elif state == "ready":
        status = "Report ready."
    else:
        status = snap["message"]
    percent = snap["percent"]
    return {
        "status": status,
        "start_label": "Run again" if snap["report"] else "Full Monte Carlo",
        "start_disabled": state in ("running", "busy"),
        "cancel_style": {} if running else HIDDEN,
        "open_href": snap["href"],
        "open_style": {} if snap["report"] else HIDDEN,
        "track_style": {} if running else HIDDEN,
        "track_class": "mc-track mc-loading" if running and percent is None else "mc-track",
        "fill_style": {"width": f"{(percent or 0.0):.1f}%"},
        "timer_disabled": state not in ("running", "busy"),
    }


MC_POLL_KEYS = (
    "status", "fill_style", "track_style", "track_class", "start_label", "start_disabled",
    "cancel_style", "open_href", "open_style", "timer_disabled",
)  # fmt: skip


def press_start(clicks: int | None, run_id: str | None, results_dir: Path = RESULTS_DIR) -> bool:
    """The Full Monte Carlo button: True when it started a run."""
    if not clicks or not run_id:
        return False
    try:
        mj.start(run_id, results_dir)
    except (mj.AlreadyRunning, mj.RunNotFound):
        return False
    return True


def press_cancel(clicks: int | None) -> bool:
    return bool(clicks) and mj.cancel()


def _mc_block(run_id: str, results_dir: Path) -> html.Div:
    out = mc_outputs(mj.snapshot(run_id, results_dir))
    return html.Div(
        [
            html.Div(
                [
                    html.Button(out["start_label"], id="mc-start", n_clicks=0,
                                className="mc-btn", disabled=out["start_disabled"]),
                    html.Button("Cancel", id="mc-cancel", n_clicks=0, className="mc-btn mc-cancel",
                                style=out["cancel_style"]),
                    html.A("Open report", id="mc-open", href=out["open_href"], target="_blank",
                           rel="noopener", className="mc-btn mc-open", style=out["open_style"]),
                    html.Span(out["status"], id="mc-status", className="mc-status"),
                ],
                className="mc-row",
            ),
            html.Div(html.Div(id="mc-fill", className="mc-fill", style=out["fill_style"]),
                     id="mc-track", className=out["track_class"], style=out["track_style"]),
            html.Div(
                "Runs all four Monte Carlo kinds on this run and writes a report (about 35 minutes "
                "with kind D, the random price paths).",
                className="pf-how",
            ),
            dcc.Interval(id="mc-timer", interval=MC_REFRESH_MS, disabled=out["timer_disabled"]),
        ],
        className="mc-block",
    )  # fmt: skip


def layout(run_id: str, folder: Path, results_dir: Path = RESULTS_DIR) -> html.Details:
    """The card (open by default, folds) with the firm dropdown, the numbers and the Monte
    Carlo block; shows a cached card at once, else polls (the poll starts the calculation)."""
    cached = pj.peek(folder, prop_card.DEFAULT_FIRM)
    status = {"state": "ready", "card": cached} if cached else {"state": "running", "elapsed": 0.0}
    firms = [{"label": p.label, "value": k} for k, p in prop_card.FIRMS.items()]
    return html.Details(
        [
            html.Summary("Prop firm", className="rs-section-title pf-summary"),
            html.Div(
                [
                    dcc.Dropdown(id="pf-firm", options=firms, value=prop_card.DEFAULT_FIRM,
                                 clearable=False, searchable=False, className="pf-firm"),
                    html.Div(card_body(status), id="pf-body", className="pf-body"),
                    dcc.Interval(id="pf-timer", interval=CARD_REFRESH_MS,
                                 disabled=timer_disabled(status)),
                    _mc_block(run_id, results_dir),
                ],
                className="pf-inner",
            ),
        ],
        open=True,
        className="pf-card",
    )  # fmt: skip


def register_callbacks(app: Dash, results_dir: Path = RESULTS_DIR) -> None:
    @app.callback(
        Output("pf-body", "children"),
        Output("pf-timer", "disabled"),
        Input("pf-timer", "n_intervals"),
        Input("pf-firm", "value"),
        State("rs-run-id", "data"),
    )
    def _card(_, firm, run_id):
        return poll_card(run_id, firm or prop_card.DEFAULT_FIRM, results_dir)

    @app.callback(
        Output("mc-status", "children"),
        Output("mc-fill", "style"),
        Output("mc-track", "style"),
        Output("mc-track", "className"),
        Output("mc-start", "children"),
        Output("mc-start", "disabled"),
        Output("mc-cancel", "style"),
        Output("mc-open", "href"),
        Output("mc-open", "style"),
        Output("mc-timer", "disabled"),
        Input("mc-timer", "n_intervals"),
        State("rs-run-id", "data"),
    )
    def _mc_poll(_, run_id):
        if not run_id:
            return (no_update,) * 9 + (True,)
        out = mc_outputs(mj.snapshot(run_id, results_dir))
        return tuple(out[k] for k in MC_POLL_KEYS)

    @app.callback(
        Output("mc-timer", "disabled", allow_duplicate=True),
        Output("mc-status", "children", allow_duplicate=True),
        Input("mc-start", "n_clicks"),
        State("rs-run-id", "data"),
        prevent_initial_call=True,
    )
    def _mc_start(clicks, run_id):
        if press_start(clicks, run_id, results_dir):
            return False, mj.STARTING_TEXT
        return no_update, no_update

    @app.callback(
        Output("mc-status", "children", allow_duplicate=True),
        Input("mc-cancel", "n_clicks"),
        prevent_initial_call=True,
    )
    def _mc_cancel(clicks):
        return "Cancelling …" if press_cancel(clicks) else no_update
