"""The top bar on every page: Chart · Backtest · Risk · Live and the bot status (ROADMAP 7.3).

Spec: docs/live-trading.md › App layout and Live page. The Live link turns red while the bot runs
(fresh heartbeat in `results/live/status.json`, read every few seconds). The app opens on `/live`
when the bot runs at the first load of a browser session, else on the chart.

Backtest links to `/backtest`: the running backtest with its progress bar, else the newest run's
results (or "No backtest yet"). Risk has no page yet (pages/risk.py is a stub): it is shown
greyed out, not as a link.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from dash import Dash, Input, Output, State, dcc, html, no_update

from backtester.live.status import STATUS_NAME, read_status
from backtester.paths import RESULTS_DIR
from backtester.ui import live_model

LIVE_DIR = RESULTS_DIR / "live"
REFRESH_MS = 3000
BOOT_DELAY_MS = 200  # the landing check runs once, this long after the page is shown
RESULTS_PREFIX = "/results/"
BACKTEST_PATH = "/backtest"  # the running backtest, else the newest results


def section_of(pathname: str | None) -> str:
    """Which top-bar entry is active for a path: chart, backtest or live."""
    if pathname == live_model.LIVE_PATH:
        return "live"
    if pathname == BACKTEST_PATH or (pathname and pathname.startswith(RESULTS_PREFIX)):
        return "backtest"
    return "chart"


def link_classes(pathname: str | None, bot_live: bool) -> dict[str, str]:
    section = section_of(pathname)
    out = {name: "nav-link" + (" active" if section == name else "") for name in
           ("chart", "backtest", "live")}  # fmt: skip
    if bot_live:
        out["live"] += " nav-red"
    return out


def backtest_href() -> str:
    return BACKTEST_PATH


def layout() -> html.Div:
    return html.Div(
        [
            dcc.Interval(id="nav-interval", interval=REFRESH_MS),
            dcc.Interval(id="nav-boot", interval=BOOT_DELAY_MS, max_intervals=1),
            dcc.Store(id="nav-landed", storage_type="session"),
            html.Div("BACKTESTER", className="nav-brand"),
            dcc.Link("Chart", id="nav-chart", href="/", className="nav-link"),
            dcc.Link("Backtest", id="nav-backtest", href=BACKTEST_PATH, className="nav-link"),
            html.Span("Risk", className="nav-link nav-off", title="Not built yet"),
            dcc.Link("Live", id="nav-live", href=live_model.LIVE_PATH, className="nav-link"),
            html.Div(className="nav-spacer"),
            html.Div("Bot not running", id="nav-status", className="nav-status nav-idle"),
        ],
        className="nav-bar",
    )


def register_callbacks(app: Dash, out_dir: Path = LIVE_DIR):
    @app.callback(
        Output("nav-chart", "className"),
        Output("nav-backtest", "className"),
        Output("nav-live", "className"),
        Output("nav-status", "children"),
        Output("nav-status", "className"),
        Input("url", "pathname"),
        Input("nav-interval", "n_intervals"),
    )
    def _nav(pathname, _):
        view = live_model.nav_view(read_status(out_dir / STATUS_NAME), datetime.now(UTC))
        cls = link_classes(pathname, view["live"])
        return (
            cls["chart"],
            cls["backtest"],
            cls["live"],
            view["text"],
            f"nav-status nav-{view['level']}",
        )

    @app.callback(
        Output("url", "pathname"),
        Output("nav-landed", "data"),
        Input("nav-boot", "n_intervals"),
        State("url", "pathname"),
        State("nav-landed", "data"),
        prevent_initial_call=True,
    )
    def _landing(_, pathname, landed):
        status = read_status(out_dir / STATUS_NAME)
        target = live_model.landing_path(pathname, bool(landed), status, datetime.now(UTC))
        return (target if target else no_update), True
