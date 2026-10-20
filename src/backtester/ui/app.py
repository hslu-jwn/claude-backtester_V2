"""Dash app entry point: `python -m backtester.ui.app` → http://127.0.0.1:8050

One top bar on every page (ui/nav.py): Chart · Backtest · Risk · Live; Live is red while the
bot runs and the app opens on `/live` then (ROADMAP 7.3).

Pages: the running backtest (`/backtest`, pages/backtest.py: progress bar, Cancel; ROADMAP 7.6),
chart (`/`, pages/chart.py; `/?symbol=…&from=…&to=…&t0=…&t1=…` opens it focused on
one trade, from the results page) and a backtest's results (`/results/<run id>`,
pages/results.py, opened when a backtest started from the toolbar finishes). The Risk &
Prop Firm page (pages/risk.py) comes in Phase 5. The demo bot's monitor and account
connection are `/live` (pages/live.py, ROADMAP 7.2 / 7.3). Each symbol is read from the cache of its
own data source (`data/sources.py`). A page is built when it is opened, so symbols cached
while the app runs appear after a reload.
"""

from __future__ import annotations

import argparse

from dash import Dash, Input, Output, State, dcc, html

from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.ui import backtest_job, nav, report_route
from backtester.ui.pages import backtest, chart, live, results

RESULTS_PREFIX = "/results/"
LIVE_PATH = "/live"


def page_for(pathname: str | None, sources: SymbolSources, search: str | None = None):
    if pathname == LIVE_PATH:
        return live.layout()
    if pathname == backtest.PATH:
        return backtest.page()
    if pathname and pathname.startswith(RESULTS_PREFIX):
        return results.layout(pathname.removeprefix(RESULTS_PREFIX))
    return chart.layout(sources, focus=chart.focus_from_query(search))


def create_app(sources: SymbolSources = DEFAULT_SOURCES) -> Dash:
    app = Dash(__name__, title="Backtester", suppress_callback_exceptions=True)
    app.layout = html.Div([dcc.Location(id="url"), nav.layout(), html.Div(id="page")])
    app.validation_layout = html.Div(
        [
            dcc.Location(id="url"),
            nav.layout(),
            html.Div(id="page"),
            chart.layout(sources),
            results.layout(""),
            live.layout(),
            backtest.layout(backtest_job.PLACEHOLDER),
        ]
    )

    @app.callback(Output("page", "children"), Input("url", "pathname"), State("url", "search"))
    def _page(pathname, search):
        return page_for(pathname, sources, search)

    report_route.register(app.server)
    nav.register_callbacks(app)
    chart.register_callbacks(app, sources)
    results.register_callbacks(app)
    backtest.register_callbacks(app)
    live.register_callbacks(app)
    return app


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", type=int, default=8050)
    p.add_argument("--debug", action="store_true", help="Dash dev tools and auto reload")
    args = p.parse_args(argv)
    create_app().run(port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
