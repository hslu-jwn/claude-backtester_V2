"""Dash app entry point: `python -m backtester.ui.app` → http://127.0.0.1:8050

Pages: chart (pages/chart.py). The Risk & Prop Firm page (pages/risk.py) comes in Phase 5.
Each symbol is read from the cache of its own data source (`data/sources.py`). The layout is
rebuilt on every page load, so symbols cached while the app runs appear after a reload.
"""

from __future__ import annotations

import argparse

from dash import Dash

from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.ui.pages import chart


def create_app(sources: SymbolSources = DEFAULT_SOURCES) -> Dash:
    app = Dash(__name__, title="Backtester")
    app.layout = lambda: chart.layout(sources)
    chart.register_callbacks(app, sources)
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
