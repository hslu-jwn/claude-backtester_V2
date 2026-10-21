"""The settings panel for either strategy (ROADMAP 8.6): the strategy popover picks which
fields, presets and defaults apply; the store remembers the strategy."""

from __future__ import annotations

from dataclasses import replace

from backtester.presets import DEFAULT, list_presets, load_preset, save_preset
from backtester.runner import RunSettings
from backtester.settings import form_values
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
from backtester.strategy.registry import default_config
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.ui import settings_panel as sp

S1, S2, S3, S4, S5, S6, S7 = (
    "session_zone_sweep",
    "ny_index_sweep",
    "no_wick",
    "trend_following",
    "gap_fade",
    "opening_range",
    "gap_momentum",
)


def ny_settings(**changes) -> RunSettings:
    return RunSettings(strategy=replace(NyIndexSweepConfig(), **changes))


def widgets_for(strategy, **changes):
    values = {
        leaf.path: sp.to_widget(leaf.kind, leaf.default) for leaf in sp.strategy_leaves(strategy)
    }
    for key, value in changes.items():
        values[key.replace("__", ".")] = value
    return values


# --- which fields -------------------------------------------------------------------------


def test_every_setting_of_every_strategy_has_a_group():
    for name in (S1, S2, S3, S4, S5, S6, S7):
        groups = sp.grouped(sp.strategy_leaves(name))
        assert sp.OTHER not in groups, (name, groups.get(sp.OTHER))
        assert set(groups) <= set(sp.GROUPS)


def test_strategy_2_has_its_groups_and_not_strategy_1_fields():
    paths = {leaf.path for leaf in sp.strategy_leaves(S2)}
    assert {"strategy.sweep_lookback", "strategy.min_tp1_r", "strategy.windows.am.start"} <= paths
    assert "strategy.zone_kill" not in paths
    assert "engine.break_even_at_next_session" not in paths  # strategy 2 skips it
    assert "detectors.fvg.strong_move_filter" in paths  # the shared detectors are in both
    assert sp.group_of("strategy.windows.am.start") == "Windows"


def test_strategy_1_fields_are_unchanged():
    paths = {leaf.path for leaf in sp.strategy_leaves(S1)}
    assert "engine.break_even_at_next_session" in paths
    assert "strategy.sweep_lookback" not in paths


def test_a_path_with_different_defaults_gets_one_widget_per_strategy():
    fields = {wp: (leaf, owners) for wp, leaf, owners in sp.panel_fields()}
    one, two = fields["strategy.confluence_kinds"], fields[f"{S2}:strategy.confluence_kinds"]
    assert one[1] == {S1} and two[1] == {S2}
    assert "EQUILIBRIUM" not in sp.options_of(one[0], S1)  # strategy 1: its own switch
    assert "EQUILIBRIUM" in sp.options_of(two[0], S2)
    assert two[0].path == "strategy.confluence_kinds"  # the settings path, not the widget id
    assert sp.real_path(f"{S2}:strategy.confluence_kinds") == "strategy.confluence_kinds"


def test_shared_paths_have_one_widget_owned_by_both():
    fields = {wp: owners for wp, _, owners in sp.panel_fields()}
    assert fields["warmup_days"] == {S1, S2, S3, S4, S5, S6, S7}
    assert fields["strategy.zone_kill"] == {S1}
    assert fields["strategy.min_tp1_r"] == {S2}


# --- the store ----------------------------------------------------------------------------


def test_store_remembers_the_strategy_and_old_stores_are_strategy_1():
    store = sp.store_for(ny_settings(min_tp1_r=1.5), {"strategy.min_tp1_r": 1.5})
    assert store["strategy"] == S2
    s = sp.store_settings(store)
    assert isinstance(s.strategy, NyIndexSweepConfig) and s.strategy.min_tp1_r == 1.5
    old = {"preset": "Default", "values": {"strategy.min_rr": 1.5}, "key": "x"}  # before 8.6
    assert isinstance(sp.store_settings(old).strategy, SessionZoneSweepConfig)
    assert sp.store_settings(old).strategy.min_rr == 1.5


def test_empty_store_is_the_defaults_of_the_asked_strategy():
    assert sp.store_settings(None) == RunSettings()
    assert sp.store_settings({"strategy": S2}) == RunSettings(strategy=NyIndexSweepConfig())


def test_store_json_is_empty_only_for_strategy_1_defaults():
    assert sp.store_json(None) == ""
    ny = RunSettings(strategy=NyIndexSweepConfig())
    assert '"ny_index_sweep"' in sp.store_json(sp.store_for(ny, form_values(ny)))


# --- the panel logic ----------------------------------------------------------------------


def test_picking_strategy_2_loads_its_defaults_and_the_default_preset():
    store = sp.store_for(RunSettings(), {"strategy.min_rr": 1.5}, "My S1 preset")
    out = sp.form_update({"strategy": S2}, {}, store, strategy=S1)
    assert out["error"] is None
    assert out["store"]["strategy"] == S2 and out["store"]["preset"] == DEFAULT
    assert out["widgets"]["strategy.min_tp1_r"] == 1.2
    assert "strategy.min_rr" not in out["widgets"]
    assert out["changed"] == []
    assert isinstance(sp.store_settings(out["store"]).strategy, NyIndexSweepConfig)


def test_picking_the_current_strategy_again_changes_nothing():
    settings = ny_settings(min_tp1_r=1.5)
    store = sp.store_for(settings, form_values(settings))
    out = sp.form_update({"strategy": S2}, {}, store, strategy=S2)
    assert out["widgets"] is None and out["store"] is None


def test_a_change_in_strategy_2_is_stored_with_the_strategy():
    out = sp.form_update(
        "field",
        widgets_for(S2, strategy__min_tp1_r=1.5, strategy__ath_mode="FIXED_R"),
        None,
        strategy=S2,
    )
    assert out["error"] is None
    assert out["changed"] == ["strategy.min_tp1_r", "strategy.ath_mode"]
    s = sp.store_settings(out["store"])
    assert isinstance(s.strategy, NyIndexSweepConfig) and s.strategy.min_tp1_r == 1.5


def test_float_list_widgets_are_numbers_separated_by_commas():
    assert sp.to_widget("float_list", [1.382, 1.5]) == "1.382, 1.5"
    assert sp.from_widget("float_list", "1.2, 1.5 ,1.8") == [1.2, 1.5, 1.8]
    assert sp.from_widget("float_list", "") == []
    out = sp.form_update(
        "field", widgets_for(S2, strategy__fib_levels="1.0, 2.0"), None, strategy=S2
    )
    assert out["error"] is None
    assert sp.store_settings(out["store"]).strategy.fib_levels == (1.0, 2.0)
    bad = sp.form_update(
        "field", widgets_for(S2, strategy__fib_levels="1.0, abc"), None, strategy=S2
    )
    assert bad["error"][0] == "strategy.fib_levels" and bad["store"] is None


def test_reset_all_goes_to_the_defaults_of_the_strategy():
    settings = ny_settings(min_tp1_r=1.5)
    store = sp.store_for(settings, form_values(settings))
    out = sp.form_update("reset-all", widgets_for(S2, strategy__min_tp1_r=1.5), store, strategy=S2)
    assert out["widgets"]["strategy.min_tp1_r"] == 1.2 and out["changed"] == []


# --- presets per strategy -----------------------------------------------------------------


def test_presets_are_listed_per_strategy_and_default_is_in_both(tmp_path):
    save_preset("tight sl", RunSettings(), tmp_path)
    save_preset("ny first", ny_settings(min_tp1_r=1.4), tmp_path)
    assert list_presets(tmp_path) == [DEFAULT, "ny first", "tight sl"]
    assert list_presets(tmp_path, S1) == [DEFAULT, "tight sl"]
    assert list_presets(tmp_path, S2) == [DEFAULT, "ny first"]


def test_default_preset_of_strategy_2_is_its_defaults(tmp_path):
    assert load_preset(DEFAULT, tmp_path, S2) == RunSettings(strategy=default_config(S2))
    assert load_preset(DEFAULT, tmp_path) == RunSettings()


def test_save_as_in_strategy_2_makes_a_strategy_2_preset(tmp_path):
    out = sp.form_update(
        "save-as",
        widgets_for(S2, strategy__min_tp1_r=1.5),
        None,
        name="ny a",
        folder=tmp_path,
        strategy=S2,
    )
    assert out["preset"] == "ny a" and out["presets"] == [DEFAULT, "ny a"]
    assert load_preset("ny a", tmp_path).strategy.min_tp1_r == 1.5
    assert list_presets(tmp_path, S1) == [DEFAULT]


def test_loading_a_preset_applies_it_in_its_strategy(tmp_path):
    save_preset("ny first", ny_settings(min_tp1_r=1.4), tmp_path)
    out = sp.form_update({"load": "ny first"}, widgets_for(S2), None, folder=tmp_path, strategy=S2)
    assert out["widgets"]["strategy.min_tp1_r"] == 1.4 and out["preset"] == "ny first"
    assert sp.store_settings(out["store"]).strategy.min_tp1_r == 1.4


# --- the widgets of the Dash callback -----------------------------------------------------


def test_only_the_widgets_of_the_shown_strategy_are_read():
    ids = ["warmup_days", "strategy.zone_kill", "strategy.min_tp1_r", "strategy.confluence_kinds",
           f"{S2}:strategy.confluence_kinds"]  # fmt: skip
    values = [14, ["on"], 1.5, ["FVG"], ["ORDER_BLOCK", "EQUILIBRIUM"]]
    s1 = sp.panel_widgets(ids, values, S1)
    assert s1 == {"warmup_days": 14, "strategy.zone_kill": ["on"],
                  "strategy.confluence_kinds": ["FVG"]}  # fmt: skip
    s2 = sp.panel_widgets(ids, values, S2)
    assert s2 == {"warmup_days": 14, "strategy.min_tp1_r": 1.5,
                  "strategy.confluence_kinds": ["ORDER_BLOCK", "EQUILIBRIUM"]}  # fmt: skip
    assert sp.panel_widgets(ids, values, S1, picked=S2) == s2  # the dropdown just changed


def test_rows_of_the_other_strategy_are_hidden_and_marks_follow_the_shown_strategy():
    ids = ["strategy.zone_kill", "strategy.min_tp1_r", f"{S2}:strategy.confluence_kinds"]
    classes = sp.row_classes(ids, [False, True, True], ["strategy.min_tp1_r"], None)
    assert classes == ["st-row st-hidden", "st-row st-changed", "st-row"]
    err = sp.row_classes(ids, [False, True, True], [], "strategy.confluence_kinds")
    assert err[2] == "st-row st-error"  # an error names the settings path, not the widget id


def test_the_page_lists_the_strategies_of_the_registry():
    from backtester.ui.pages import chart

    assert [s["value"] for s in chart.STRATEGIES] == [S1, S2, S3, S4, S5, S6, S7]
