"""V2.5a cases: page renders; exactly four tabs; global actions once;
closed details; skeleton optional slots; CSS colours centralized and loaded first;
callback IDs retained; gear reaches connection settings; no back links.
"""

import json
import re
from pathlib import Path

from dash import dcc, html

from backtester.data.sources import SymbolSources
from backtester.ui import app as app_module
from backtester.ui import nav

UI = Path(__file__).resolve().parents[2] / "src/backtester/ui"


def walk(node):
    if isinstance(node, (list, tuple)):
        for child in node:
            yield from walk(child)
    elif hasattr(node, "to_plotly_json"):
        yield node
        yield from walk(getattr(node, "children", None))


def test_helpers():
    from backtester.ui.layout import details, info, key_strip, page, tabs_below

    fold = details("Details", html.Div("body"))
    assert isinstance(fold, html.Details) and fold.open is False
    assert isinstance(fold.children[0], html.Summary)
    assert info("explanation").title == "explanation"
    strip = key_strip([{"label": "Net R", "value": "+2", "sign": "green", "tooltip": "net"}])
    assert "green" in str(strip) and "net" in str(strip)
    tabs = tabs_below([dcc.Tab(label="Trades", value="trades")], value="trades")
    assert isinstance(tabs, dcc.Tabs)
    assert len(list(walk(page(strip, html.Div("main"), html.Div("side"), tabs)))) > 5
    assert page(strip, html.Div("main")) is not None


def test_global_actions_and_exact_tabs():
    nodes = list(walk(nav.layout()))
    links = [
        n for n in nodes if isinstance(n, dcc.Link) and getattr(n, "id", "").startswith("nav-")
    ]
    assert [n.children for n in links] == ["Chart", "Backtest", "Research", "Live"]
    ids = [getattr(n, "id", None) for n in nodes]
    for identifier in ("nav-status", "nav-settings", "update-btn", "update-status", "update-tick"):
        assert ids.count(identifier) == 1
    gear = next(n for n in nodes if getattr(n, "id", None) == "nav-settings")
    assert gear.href == "/live#connection"
    assert not (UI / "pages/risk.py").exists()


def test_pages_render_and_global_callback_ids_exist(tmp_path):
    from backtester.ui import backtest_job
    from backtester.ui.pages import backtest, chart, live, research, results

    layouts = [
        nav.layout(),
        chart.layout(SymbolSources({})),
        backtest.layout(backtest_job.PLACEHOLDER),
        backtest.runs_list(tmp_path),
        results.layout("missing", tmp_path),
        research.layout(),
        live.layout(),
    ]
    ids = [getattr(n, "id", None) for layout in layouts for n in walk(layout)]
    assert ids.count("update-btn") == 1
    assert ids.count("update-status") == 1
    assert "connection" in ids
    for layout in layouts:
        rendered = json.dumps(layout, default=lambda obj: obj.to_plotly_json(), ensure_ascii=False)
        assert "\u2190 Chart" not in rendered
    app = app_module.create_app(SymbolSources({}))
    assert "update-status.children" in " ".join(app.callback_map)
    response = app.server.test_client().get("/")
    assert response.status_code == 200
    css = re.findall(r'href="([^"]+\.css[^"]*)"', response.get_data(as_text=True))
    assert "theme.css" in css[0]


def test_css_has_one_colour_source():
    for path in (UI / "assets").glob("*.css"):
        if path.name != "theme.css":
            assert not re.findall(
                r"#[0-9a-fA-F]{3,8}\b|rgba?\(", path.read_text(encoding="utf-8")
            ), path.name
    theme = (UI / "assets/theme.css").read_text(encoding="utf-8")
    for token in (
        "bg",
        "panel",
        "raised",
        "line",
        "text",
        "muted",
        "green",
        "red",
        "amber",
        "accent",
    ):
        assert f"--{token}:" in theme


def test_chart_surfaces_use_stylesheet_tokens():
    from backtester.ui.chart_config import ChartConfig
    from backtester.ui.pages import live, results
    from backtester.ui.theme import color

    config = ChartConfig()
    assert config.background == color("bg")
    assert config.text_color == color("text")
    assert config.grid_color == color("line")
    assert config.up_body == "#6f9ceb" and config.down_body == "#000000"
    histogram = results.histogram_figure([])
    assert histogram.layout.paper_bgcolor == color("panel")
    assert histogram.layout.font.color == color("text")
    figure = live.trades_figure({"pct": [], "equity": []})
    assert figure.layout.paper_bgcolor == color("panel")
    assert figure.layout.xaxis.color == color("muted")


def test_update_status_visible_only_while_running(monkeypatch):
    from types import SimpleNamespace

    from dash import Dash

    from backtester.ui import update_button

    app = Dash(__name__)
    update_button.register_callbacks(app)
    callback = next(iter(app.callback_map.values()))["callback"].__wrapped__
    monkeypatch.setattr(update_button, "ctx", SimpleNamespace(triggered_id=None))
    for running in (True, False):
        monkeypatch.setattr(
            update_button,
            "refresh",
            lambda _, running=running: {
                "text": "MT5 XAUUSD" if running else "Updated 1",
                "title": "MT5 XAUUSD" if running else "Updated 1",
                "button_disabled": running,
                "interval_disabled": not running,
            },
        )
        values = callback(0, 0)
        assert values[3] == values[1]
        assert values[4]["display"] == ("inline" if running else "none")
        assert values[2] == running and values[5] == (not running)


def test_connection_gear_opens_once_and_allows_closing():
    import shutil
    import subprocess

    import pytest

    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is needed for the connection navigation DOM harness")
    script = r"""
const fs = require("fs");
const assert = require("assert");
let mutation, fold = null, scrolls = 0;
const events = {};
global.location = { pathname: "/live", hash: "#connection" };
global.window = { addEventListener: (name, cb) => { events[name] = cb; } };
global.document = {
  documentElement: {},
  getElementById: () => fold,
  addEventListener: (name, cb) => { events[name] = cb; },
};
global.MutationObserver = class {
  constructor(cb) { mutation = cb; }
  observe() {}
};
global.setTimeout = (cb) => cb();
eval(fs.readFileSync(process.argv[1], "utf8"));
mutation(); // route not rendered yet
fold = { open: false, scrollIntoView: () => { scrolls++; } };
mutation();
assert.equal(fold.open, true);
assert.equal(scrolls, 1);
fold.open = false;
mutation(); // Live polling must not reopen a fold the user closed
assert.equal(fold.open, false);
events.click({ target: { closest: () => true } });
assert.equal(fold.open, true);
assert.equal(scrolls, 2);
"""
    subprocess.run(
        [node, "-e", script, str(UI / "assets/connection.js")],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
