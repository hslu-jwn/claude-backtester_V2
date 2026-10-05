"""Dash app entry point: `python -m backtester.ui.app` → http://127.0.0.1:8050

Pages: chart (pages/chart.py). The Risk & Prop Firm page (pages/risk.py) comes in Phase 5.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from dash import Dash

from backtester.data.dukascopy import DEFAULT_CACHE_DIR
from backtester.ui.pages import chart


def create_app(cache_dir: Path = DEFAULT_CACHE_DIR) -> Dash:
    app = Dash(__name__, title="Backtester")
    app.layout = chart.layout(cache_dir)
    chart.register_callbacks(app, cache_dir)
    return app


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    p.add_argument("--port", type=int, default=8050)
    p.add_argument("--debug", action="store_true", help="Dash dev tools and auto reload")
    args = p.parse_args(argv)
    create_app(args.cache_dir).run(port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
