"""V2.5c layout contracts; fixture numbers are hand calculated."""

import json
from types import SimpleNamespace

import pytest
from dash import Dash, dcc, html, no_update
from test_results_page import RUN
from test_results_page import results_dir as fixture_results_dir

from backtester.data.sources import SymbolSources
from backtester.ui import chart_side, prop_firm_card, settings_panel
from backtester.ui.pages import chart, results

results_dir = fixture_results_dir


def walk(node):
    if isinstance(node, (list, tuple)):
        for child in node:
            yield from walk(child)
    elif hasattr(node, "to_plotly_json"):
        yield node
        yield from walk(getattr(node, "children", None))


def find(node, id_):
    return next(n for n in walk(node) if getattr(n, "id", None) == id_)


def unique_ids(node):
    ids = [json.dumps(n.id, sort_keys=True) for n in walk(node) if hasattr(n, "id")]
    assert len(ids) == len(set(ids))


def test_chart_tabs_keep_forms_mounted_once(results_dir):
    page = chart.layout(SymbolSources({}), results_dir=results_dir)
    unique_ids(page)
    tabs = find(page, "chart-tabs")
    assert isinstance(tabs, dcc.Tabs) and tabs.value == "trades"
    assert [t.label for t in tabs.children] == ["Trades", "Overlays", "Backtest", "Strategy"]
    for id_ in ("bt-symbols", "bt-dates", "bt-preset", "bt-run", "bt-status"):
        find(find(page, "chart-tab-backtest"), id_)
    find(find(page, "chart-tab-strategy"), "chart-strategy")
    find(find(page, "chart-tab-overlays"), "chart-overlays")
    settings = find(page, "pop-settings")
    assert "chart-overlay-types" not in str(settings)
    assert all(not getattr(n, "open", False) for n in walk(settings) if isinstance(n, html.Details))
    assert "pop-backtest" not in str(page) and "pop-strategy" not in str(page)


def test_chart_strip_fixture_and_empty(tmp_path, results_dir):
    strip = find(chart.layout(SymbolSources({}), results_dir=results_dir), "chart-key-strip")
    for value in ("-1.05 R", "33.3%", "2.15 R", RUN):
        assert value in str(strip)
    assert "Results →" in str(strip)
    empty = tmp_path / "empty"
    empty.mkdir()
    assert "—" in str(find(chart.layout(SymbolSources({}), results_dir=empty), "chart-key-strip"))
    assert "ch-card-result" not in str(chart_side.panel(None))


def test_results_skeleton_defaults_and_columns(results_dir):
    page = results.layout(RUN, results_dir)
    unique_ids(page)
    assert find(page, "rs-tab").value == "trades"
    find(page, "rs-equity")
    find(page, "pf-body")
    strip = str(find(page, "rs-key-strip"))
    for value in ("-1.05 R", "33.3%", "Expectancy", "Prop pass %"):
        assert value in strip
    table = find(page, "rs-trades")
    essential = {"time", "symbol", "direction", "r_net", "exit"}
    assert {c["id"] for c in table.columns} - set(table.hidden_columns) == essential
    find(page, "rs-more-columns")
    assert all(not getattr(n, "open", False) for n in walk(page) if isinstance(n, html.Details))


def test_middle_prop_probability_and_missing():
    card = {
        "status": "ok",
        "rows": [
            {"risk": r, "attempts": 10, "pass_probability": p}
            for r, p in [(0.005, 0.1), (0.01, 0.4), (0.015, 0.2)]
        ],
    }
    assert prop_firm_card.middle_pass(card) == "40.0 %"
    assert prop_firm_card.middle_pass(None) == "—"
    card["rows"][1]["attempts"] = 0
    assert prop_firm_card.middle_pass(card) == "—"


def test_performance_optional_outputs_and_folds(results_dir):
    folder = results_dir / RUN
    assert "—" in str(results.diagnostics(folder))
    (folder / "skill_bounds.json").write_text(
        json.dumps({"scores": {"detrended_net_r": 4.25, "lower95": -0.5}})
    )
    (folder / "profile.json").write_text(
        json.dumps(
            {
                "strongest_skill_cells": [
                    {"dimension": "session", "condition": "London", "lower90_bca": 0.8}
                ]
            }
        )
    )
    text = str(results.diagnostics(folder))
    assert "4.25" in text and "London" in text
    (folder / "drawdown_bounds.json").write_text("{invalid")
    assert "Skill vs trend" in str(results.diagnostics(folder))
    content = results.performance(results.read_trades(folder))
    folds = [n for n in walk(content) if isinstance(n, html.Details)]
    assert folds and all(not n.open for n in folds)


def test_strategy_settings_are_collapsible_and_notes_are_tooltips():
    page = settings_panel.layout()
    groups = [n for n in walk(page) if isinstance(n, html.Details)]
    assert groups and groups[0].open
    assert all(not n.open for n in groups[1:])
    assert "ui-info" in str(page)


def callback(app, output):
    return next(v["callback"].__wrapped__ for k, v in app.callback_map.items() if output in k)


def test_results_callbacks_filter_metrics_keep_equity_and_restore_columns(results_dir, monkeypatch):
    app = Dash(__name__)
    results.register_callbacks(app, results_dir)
    monkeypatch.setattr(prop_firm_card.pj, "peek", lambda *_: None)
    strip, equity = callback(app, "rs-key-strip.children")("XAUUSD", None, RUN)
    assert "+0.05 R" in str(strip)
    assert equity["net"] == pytest.approx([0, 1.1, 0.05])
    assert callback(app, "rs-trades.hidden_columns")(["More columns"]) == []
    assert (
        set(callback(app, "rs-trades.hidden_columns")([]))
        == {c["id"] for c in results.TRADE_COLUMNS} - results.ESSENTIAL_COLUMNS
    )
    # Switching the lower tab updates only rs-content, never the equity canvas/data.
    content = callback(app, "rs-content.children")("overview", "XAUUSD", RUN)
    assert "Avg realized R" in str(content) and "rs-equity" not in str(content)


def test_moved_backtest_callback_and_newest_trade_focus(results_dir, monkeypatch):
    app = Dash(__name__)
    sources = SymbolSources({})
    chart.register_callbacks(app, sources, results_dir=results_dir)
    calls = []
    monkeypatch.setattr(
        chart, "start_backtest", lambda *a, **kw: calls.append((a, kw)) or ("", "/backtest")
    )
    run = callback(app, "bt-status.children")
    assert run(0, [], None, None, None) == (no_update, no_update)
    assert run(1, ["GBPUSD"], "2026-09-02", "2026-09-30", None) == ("", "/backtest")
    assert calls[0][0] == (sources, ["GBPUSD"], "2026-09-02", "2026-09-30")
    # Both lists use the same focus callback, with distinct pattern IDs.
    monkeypatch.setattr(
        chart,
        "ctx",
        SimpleNamespace(triggered=[{"value": 1}], triggered_id={"type": "run-trade", "index": 2}),
    )
    focus_cb = next(
        v["callback"].__wrapped__
        for v in app.callback_map.values()
        if any(i["id"].startswith('{"index"') and "run-trade" in i["id"] for i in v["inputs"])
    )
    focus, message = focus_cb([], [1], {"on": False})
    assert (focus["symbol"], focus["tf"]) == ("GBPUSD", "M5")
    assert message is no_update
    assert focus_cb([], [1], {"on": True})[0] is no_update


def test_diagnostics_wrong_shapes_are_missing_not_page_errors(results_dir):
    folder = results_dir / RUN
    for filename, value in (
        ("skill_bounds.json", {"scores": [1]}),
        ("profile.json", {"strongest_skill_cells": 4}),
        ("drawdown_bounds.json", {"rows": "bad"}),
    ):
        (folder / filename).write_text(json.dumps(value))
    assert "—" in str(results.diagnostics(folder))


def test_empty_run_keeps_equity_mount(results_dir):
    (results_dir / RUN / "trades.csv").write_text("")
    page = results.layout(RUN, results_dir)
    find(page, "rs-equity")
    assert "No trades." in str(page)


def test_page_children_have_no_nested_component_lists(results_dir):
    for page in (
        chart.layout(SymbolSources({}), results_dir=results_dir),
        results.layout(RUN, results_dir),
    ):
        for node in walk(page):
            children = getattr(node, "children", None)
            if isinstance(children, list):
                assert not any(isinstance(child, list) for child in children), type(node).__name__


def test_drawdown_bounds_show_units_and_intervals(results_dir):
    (results_dir / RUN / "drawdown_bounds.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "q": 0.95,
                        "bounds_r": {"median": 4, "upper90": 6, "upper95": 8},
                        "bounds_pct": {"0.01": {"median": 4, "upper90": 6, "upper95": 8}},
                    }
                ]
            }
        )
    )
    text = str(results.diagnostics(results_dir / RUN))
    for value in ("95.0%", "90% upper", "8.00", "% balance at 1% risk"):
        assert value in text
