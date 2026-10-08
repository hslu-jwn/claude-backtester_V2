"""Settings panel: groups, labels, and what a change / reset / invalid value does.
Spec: ROADMAP.md › 4.1."""

from __future__ import annotations

from backtester.data.sources import SymbolSources
from backtester.runner import RunSettings
from backtester.settings import form_values, leaves, settings_from_values
from backtester.ui import settings_panel as sp
from backtester.ui.pages import chart


def widgets(**changes):
    """The panel's widget values for the defaults, with `changes` (path with "__" for ".")."""
    by_path = {leaf.path: leaf for leaf in leaves()}
    values = {p: sp.to_widget(by_path[p].kind, v) for p, v in form_values().items()}
    for key, value in changes.items():
        values[key.replace("__", ".")] = value
    return values


def test_every_setting_has_a_group_in_the_order_asked_for():
    groups = sp.grouped(leaves())
    assert sp.OTHER not in groups
    assert list(groups) == list(sp.GROUPS)
    assert [leaf.path for leaf in groups["Session zones"]] == [
        "strategy.zone_timeframe",
        "strategy.zone_kill",
        "strategy.zone_kill_breaks",
    ]
    assert "strategy.entry_bos_with_trend" in [leaf.path for leaf in groups["Entry"]]
    assert {sp.section_of(leaf.path) for leaf in groups["Costs"]} >= {"XAUUSD", "GBPJPY"}


def test_labels_and_choices():
    assert sp.label_of("strategy.zone_kill_breaks") == "Breaks that kill a zone"
    assert sp.label_of("engine.costs.symbols.GBPUSD.spread") == "Spread (price)"
    assert sp.label_of("strategy.swings.doji_max_body.GBPJPY") == "GBPJPY"
    assert sp.label_of("strategy.some_new_field") == "Some new field"  # fallback
    kinds = next(leaf for leaf in leaves() if leaf.path == "strategy.confluence_kinds")
    assert sp.options_of(kinds) == ["FVG", "ORDER_BLOCK", "BPR"]  # no breaker / equilibrium
    tf = next(leaf for leaf in leaves() if leaf.path == "strategy.zone_timeframe")
    assert "M30" in sp.options_of(tf) and "D1" not in sp.options_of(tf)


def test_opening_the_panel_shows_the_stored_settings():
    store = sp.store_for(RunSettings(), {"strategy.zone_kill": False})
    out = sp.form_update(None, {}, store)
    assert out["widgets"]["strategy.zone_kill"] == []  # switch off
    assert out["widgets"]["strategy.min_rr"] == 1.2  # the rest at the defaults
    empty = sp.form_update(None, {}, None)
    assert empty["widgets"]["strategy.zone_kill"] == ["on"] and empty["changed"] == []


def test_a_valid_change_is_stored_at_once_with_a_new_key():
    out = sp.form_update("field", widgets(strategy__zone_kill=[], strategy__min_rr=1.5), None)
    assert out["error"] is None and out["widgets"] is None  # the inputs keep what they show
    assert out["changed"] == ["strategy.zone_kill", "strategy.min_rr"]
    settings = sp.store_settings(out["store"])
    assert settings.strategy.zone_kill is False and settings.strategy.min_rr == 1.5
    assert out["store"]["key"] != sp.settings_key(RunSettings())
    assert out["store"]["preset"] == sp.DEFAULT_PRESET
    again = sp.form_update(
        "field", widgets(strategy__zone_kill=[], strategy__min_rr=1.5), out["store"]
    )
    assert again["store"] is None  # nothing new to store


def test_an_invalid_value_is_named_and_not_stored():
    out = sp.form_update("field", widgets(strategy__zone_kill_breaks=None), None)
    assert out["store"] is None
    assert out["error"] == (
        "strategy.zone_kill_breaks",
        "Breaks that kill a zone: a value is needed",
    )
    rule = sp.form_update("field", widgets(strategy__tp_cap_r=1.0), None)  # below min_rr
    assert rule["error"][0] == "strategy" and "tp_cap_r" in rule["error"][1]
    assert sp.status_text(None, [], out["error"]).startswith("Not applied")


def test_reset_one_field_or_all():
    changed = widgets(strategy__min_rr=2.0, strategy__tp1_share=0.3)
    out = sp.form_update({"reset": "strategy.min_rr"}, changed, None)
    assert out["widgets"]["strategy.min_rr"] == 1.2 and out["widgets"]["strategy.tp1_share"] == 0.3
    assert out["changed"] == ["strategy.tp1_share"]
    out = sp.form_update("reset-all", changed, None)
    assert out["changed"] == [] and out["widgets"]["strategy.tp1_share"] == 0.5


def test_store_json_is_empty_for_the_defaults_so_caches_are_shared():
    assert sp.store_json(None) == ""
    assert sp.store_json(sp.store_for(RunSettings(), form_values())) == ""
    changed = settings_from_values({"strategy.min_rr": 1.5})
    assert sp.store_json(sp.store_for(changed, {"strategy.min_rr": 1.5})) != ""
    broken = {"values": {"strategy.min_rr": "x"}}
    assert sp.store_settings(broken) == RunSettings()  # an old invalid store: the defaults


def test_the_panel_is_on_the_chart_page():
    page = str(chart.layout(SymbolSources({})))
    assert "st-modal" in page and "settings-current" in page and "Settings…" in page
