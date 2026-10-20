"""Top bar (ROADMAP 7.3): active section, red Live link, Backtest target, callbacks wired."""

from __future__ import annotations

import json

from backtester.ui import app as app_module
from backtester.ui import nav


def test_section_of_paths():
    assert nav.section_of("/") == "chart"
    assert nav.section_of(None) == "chart"
    assert nav.section_of("/live") == "live"
    assert nav.section_of("/results/run1") == "backtest"
    assert nav.section_of("/results/") == "backtest"
    assert nav.section_of("/whatever") == "chart"


def test_link_classes_active_and_red():
    cls = nav.link_classes("/live", True)
    assert "active" in cls["live"] and "nav-red" in cls["live"]
    assert "active" not in cls["chart"] and "nav-red" not in cls["chart"]
    quiet = nav.link_classes("/", False)
    assert "active" in quiet["chart"] and "nav-red" not in quiet["live"]
    assert "nav-red" in nav.link_classes("/", True)["live"]  # red on every page


def test_backtest_link_goes_to_the_backtest_page():
    """/backtest shows the running backtest, else the newest run (tests/ui/test_backtest_page.py)."""
    assert nav.backtest_href() == "/backtest"
    assert '"href": "/backtest"' in json.dumps(nav.layout(), default=lambda o: o.to_plotly_json())


def test_risk_has_no_link_yet():
    text = json.dumps(nav.layout(), default=lambda o: o.to_plotly_json())
    assert "nav-off" in text and '"href": "/live"' in text and '"href": "/"' in text


def test_the_app_builds_with_the_nav_callbacks():
    app = app_module.create_app()
    outputs = " ".join(app.callback_map)
    assert "nav-status.children" in outputs and "nav-landed.data" in outputs
