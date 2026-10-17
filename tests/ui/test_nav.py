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


def test_backtest_link_goes_to_the_newest_run(tmp_path):
    assert nav.backtest_href(tmp_path) == "/results/"
    for name in ("2026-01-01_a", "2026-02-01_b"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "summary.json").write_text(json.dumps({"symbols": ["X"]}))
    assert nav.backtest_href(tmp_path) == "/results/2026-02-01_b"


def test_risk_has_no_link_yet():
    text = json.dumps(nav.layout(), default=lambda o: o.to_plotly_json())
    assert "nav-off" in text and '"href": "/live"' in text and '"href": "/"' in text


def test_the_app_builds_with_the_nav_callbacks():
    app = app_module.create_app()
    outputs = " ".join(app.callback_map)
    assert "nav-status.children" in outputs and "nav-landed.data" in outputs
