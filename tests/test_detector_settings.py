"""Detector settings shared by every strategy (ROADMAP C.3).

`RunSettings.detectors` (swings, FVG, order block, equilibrium) is one group for all
strategies; a strategy config holds only what is its own. Old settings JSON (presets,
`strategy.fvg...`) is migrated on load.
"""

from __future__ import annotations

import dataclasses
import json
from types import MappingProxyType

import pytest

from backtester.detectors.equilibrium import EquilibriumConfig
from backtester.detectors.fvg import FvgConfig
from backtester.detectors.order_block import OrderBlockConfig
from backtester.detectors.settings import DetectorSettings
from backtester.detectors.swings import SwingConfig
from backtester.runner import RunSettings
from backtester.settings import (
    from_dict,
    from_json,
    leaves,
    settings_from_values,
    to_dict,
    to_json,
)
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
from backtester.strategy.ny_index_sweep.strategy import NyIndexSweep
from backtester.strategy.registry import make_strategy
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.strategy import SessionZoneSweep

MOVED = ("swings", "fvg", "order_block", "equilibrium")


def test_defaults_are_the_detector_configs_defaults():
    d = DetectorSettings()
    assert d.swings == SwingConfig()
    assert d.fvg == FvgConfig()
    assert d.order_block == OrderBlockConfig()
    assert d.equilibrium == EquilibriumConfig()
    assert RunSettings().detectors == d


def test_detector_settings_are_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        DetectorSettings().fvg = FvgConfig()  # type: ignore[misc]


@pytest.mark.parametrize("cls", [SessionZoneSweepConfig, NyIndexSweepConfig])
def test_strategy_configs_no_longer_hold_the_shared_detectors(cls):
    names = {f.name for f in dataclasses.fields(cls)}
    assert not names & set(MOVED)


def test_both_strategies_had_the_same_defaults_so_nothing_changes_for_either():
    """Pins why one shared default is right: the two strategies used the same ones."""
    assert RunSettings().detectors.swings.doji_threshold("NAS100") == pytest.approx(
        0.17674500587544067
    )
    assert RunSettings().detectors.order_block.strong_move_filter is True
    assert RunSettings().detectors.fvg.strong_move_filter is False


def test_settings_menu_has_the_detectors_group_and_no_strategy_copies():
    paths = {leaf.path for leaf in leaves()}
    for path in (
        "detectors.fvg.strong_move_filter",
        "detectors.order_block.strong_move.atr_mult",
        "detectors.swings.doji_max_body.XAUUSD",
        "detectors.equilibrium.sl_buffer",
    ):
        assert path in paths, path
    assert not [p for p in paths if any(p.startswith(f"strategy.{m}.") for m in MOVED)]


def test_menu_values_change_the_shared_group():
    s = settings_from_values({"detectors.fvg.strong_move_filter": True})
    assert s.detectors.fvg.strong_move_filter is True
    assert s.strategy == RunSettings().strategy  # nothing else moved


def test_json_round_trip_keeps_detectors():
    s = settings_from_values({"detectors.swings.doji_max_body.XAUUSD": 0.5})
    again = from_json(to_json(s))
    assert again.detectors.swings.doji_max_body["XAUUSD"] == 0.5
    assert again == s


def old_format() -> dict:
    """What a preset saved before C.3 looks like: the detector configs inside strategy."""
    data = to_dict(RunSettings())
    data["strategy"].update({k: data["detectors"][k] for k in MOVED})
    del data["detectors"]
    return data


def test_old_settings_json_is_migrated():
    data = old_format()
    data["strategy"]["fvg"]["strong_move_filter"] = True
    data["strategy"]["swings"]["doji_max_body"]["XAUUSD"] = 0.5
    data["strategy"]["equilibrium"]["sl_buffer"] = 0.2
    s = from_dict(data)
    assert s.detectors.fvg.strong_move_filter is True
    assert s.detectors.swings.doji_max_body["XAUUSD"] == 0.5
    assert s.detectors.equilibrium.sl_buffer == 0.2
    assert s.strategy == SessionZoneSweepConfig()  # the rest of strategy is untouched


def test_old_json_through_from_json_and_the_cache_key_is_the_new_format():
    data = old_format()
    data["strategy"]["order_block"]["strong_move_filter"] = False
    new = from_json(json.dumps(data))
    assert new.detectors.order_block.strong_move_filter is False
    assert "fvg" not in json.loads(to_json(new))["strategy"]


def test_new_detectors_win_over_stale_strategy_copies():
    data = to_dict(RunSettings())
    data["detectors"]["fvg"]["strong_move_filter"] = True
    data["strategy"]["fvg"] = {"strong_move_filter": False}
    assert from_dict(data).detectors.fvg.strong_move_filter is True


def test_to_dict_has_detectors_beside_strategy_and_engine():
    data = to_dict(RunSettings())
    assert set(data) == {"strategy", "detectors", "engine", "warmup_days"}
    assert set(data["detectors"]) == set(MOVED)


def test_strategy_1_uses_the_shared_detectors():
    off = DetectorSettings(order_block=OrderBlockConfig(strong_move_filter=False))
    a = SessionZoneSweep("XAUUSD", SessionZoneSweepConfig(), off)
    b = SessionZoneSweep("XAUUSD", SessionZoneSweepConfig())
    assert a.setups.detectors.order_block.strong_move_filter is False
    assert b.setups.detectors.order_block.strong_move_filter is True


def test_strategy_2_uses_the_shared_detectors():
    swings = SwingConfig(MappingProxyType({"NAS100": 0.5}))
    s = NyIndexSweep("NAS100", NyIndexSweepConfig(), DetectorSettings(swings=swings))
    assert s.doji_max_body == 0.5
    assert NyIndexSweep("NAS100", NyIndexSweepConfig()).doji_max_body == pytest.approx(
        0.17674500587544067
    )


def test_registry_passes_the_detectors_to_the_strategy():
    swings = SwingConfig(MappingProxyType({"NAS100": 0.25, "XAUUSD": 0.5}))
    s = make_strategy("NAS100", NyIndexSweepConfig(), DetectorSettings(swings=swings))
    assert s.doji_max_body == 0.25
    s1 = make_strategy("XAUUSD", SessionZoneSweepConfig(), DetectorSettings(swings=swings))
    assert isinstance(s1, SessionZoneSweep) and s1.setups.doji_max_body == 0.5
