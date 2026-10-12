"""Settings of either strategy in `RunSettings` (ROADMAP 8.6): the strategy config can be
strategy 1's or strategy 2's, the JSON carries its name, the menu lists its fields."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import time

import pytest

from backtester.presets import load_preset, save_preset
from backtester.runner import RunSettings
from backtester.settings import (
    SettingsError,
    from_dict,
    from_json,
    leaves,
    settings_from_values,
    to_dict,
    to_json,
)
from backtester.strategy.ny_index_sweep.config import AthMode, NyIndexSweepConfig
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig

NY = RunSettings(strategy=NyIndexSweepConfig())


def by_path(settings=None):
    return {leaf.path: leaf for leaf in leaves(settings)}


def test_the_json_carries_the_strategy_name():
    assert to_dict(RunSettings())["strategy"]["name"] == "session_zone_sweep"
    assert to_dict(NY)["strategy"]["name"] == "ny_index_sweep"


def test_round_trip_keeps_the_strategy_class_and_values():
    s = replace(NY, strategy=replace(NyIndexSweepConfig(), min_tp1_r=1.5, sweep_lookback=5))
    again = from_json(to_json(s))
    assert isinstance(again.strategy, NyIndexSweepConfig)
    assert again == s


def test_json_without_a_name_is_strategy_1():
    data = to_dict(RunSettings())
    del data["strategy"]["name"]
    assert isinstance(from_dict(data).strategy, SessionZoneSweepConfig)


def test_unknown_strategy_name_is_an_error_naming_the_field():
    data = to_dict(RunSettings())
    data["strategy"]["name"] = "nope"
    with pytest.raises(SettingsError, match="nope") as e:
        from_dict(data)
    assert e.value.path == "strategy.name"


def test_strategy_2_menu_has_its_own_fields_and_none_of_strategy_1s():
    found = by_path(NY)
    expected = [
        ("strategy.sweep_lookback", "int", 3),
        ("strategy.min_tp1_r", "float", 1.2),
        ("strategy.ath_mode", "enum", "FIB"),
        ("strategy.max_trades_per_session", "int", 1),
        ("strategy.windows.am.start", "time", "09:00"),
        ("strategy.windows.zone", "text", "America/New_York"),
        ("detectors.fvg.strong_move_filter", "bool", False),
        ("warmup_days", "int", 14),
    ]
    for path, kind, default in expected:
        assert (found[path].kind, found[path].default) == (kind, default), path
    assert "strategy.zone_kill" not in found and "strategy.min_rr" not in found


def test_strategy_2_float_lists_are_settings():
    found = by_path(NY)
    assert found["strategy.fib_levels"].kind == "float_list"
    assert found["strategy.fib_levels"].default == [1.382, 1.5, 1.618, 2.0]
    assert found["strategy.fixed_r_levels"].default == [1.2, 1.5, 1.8]


def test_float_list_values_are_converted_and_validated():
    s = settings_from_values({"strategy.fib_levels": [1.0, 2.5]}, NY)
    assert s.strategy.fib_levels == (1.0, 2.5)
    with pytest.raises(SettingsError, match="at least one level"):  # the config's own rule
        settings_from_values({"strategy.fixed_r_levels": []}, NY)
    with pytest.raises(SettingsError) as e:
        settings_from_values({"strategy.fib_levels": [1.0, "x"]}, NY)
    assert e.value.path == "strategy.fib_levels"


def test_values_of_the_menu_change_strategy_2_and_keep_its_class():
    s = settings_from_values(
        {
            "strategy.min_tp1_r": 1.5,
            "strategy.ath_mode": "FIXED_R",
            "strategy.windows.am.start": "09:15",
        },
        NY,
    )
    assert isinstance(s.strategy, NyIndexSweepConfig)
    assert s.strategy.min_tp1_r == 1.5 and s.strategy.ath_mode is AthMode.FIXED_R
    assert s.strategy.windows.am.start == time(9, 15)


def test_strategy_2_does_not_touch_engine_sessions():
    """The engine sessions follow strategy 1's session starts; strategy 2 has none."""
    s = settings_from_values({"strategy.min_tp1_r": 1.5}, NY)
    assert s.engine.sessions == RunSettings().engine.sessions


def test_strategy_1_menu_is_unchanged():
    found = by_path()
    assert found["strategy.min_rr"].default == 1.2
    assert "strategy.sweep_lookback" not in found
    assert "strategy.fib_levels" not in found


def test_presets_keep_the_strategy(tmp_path):
    s = replace(NY, strategy=replace(NyIndexSweepConfig(), min_tp1_r=1.4))
    save_preset("ny test", s, tmp_path)
    loaded = load_preset("ny test", tmp_path)
    assert isinstance(loaded.strategy, NyIndexSweepConfig) and loaded.strategy.min_tp1_r == 1.4
    text = (tmp_path / "ny test.json").read_text(encoding="utf8")
    assert json.loads(text)["settings"]["strategy"]["name"] == "ny_index_sweep"


def test_old_detector_migration_works_for_strategy_2_json_too():
    data = to_dict(NY)
    del data["detectors"]  # a preset saved before the shared group existed
    data["strategy"]["fvg"] = {"strong_move_filter": True}
    assert from_dict(data).detectors.fvg.strong_move_filter is True
