"""Settings generated from the config dataclasses. Spec: ROADMAP.md › 4.1."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import time

import pytest

from backtester.core.models import Timeframe
from backtester.detectors.zone import ZoneKind
from backtester.runner import RunSettings
from backtester.settings import (
    SettingsError,
    field_comments,
    form_values,
    from_dict,
    from_json,
    leaves,
    settings_from_values,
    to_dict,
    to_json,
)


def by_path():
    return {leaf.path: leaf for leaf in leaves()}


def test_every_config_value_is_a_setting_with_the_spec_default():
    found = by_path()
    for path, kind, default in [
        ("strategy.zone_kill", "bool", True),
        ("strategy.zone_kill_breaks", "int", 3),
        ("strategy.entry_bos_with_trend", "bool", False),
        ("strategy.min_rr", "float", 1.2),
        ("strategy.max_sl_atr_mult", "optional_float", None),
        ("strategy.zone_timeframe", "enum", "M30"),
        ("strategy.confluence_kinds", "enum_set", ["BPR", "BREAKER", "FVG", "ORDER_BLOCK"]),
        ("strategy.fvg.strong_move_filter", "bool", False),
        ("strategy.order_block.strong_move.atr_mult", "float", 2.0),
        ("strategy.swings.doji_max_body.XAUUSD", "float", 0.065),
        ("strategy.sessions.tokyo.local_time", "time", "09:00"),
        ("engine.costs.symbols.GBPJPY.spread", "float", 0.010),
        ("engine.costs.commission_enabled", "bool", True),
        ("engine.break_even_at_next_session", "bool", True),
        ("warmup_days", "int", 14),
    ]:
        assert (found[path].kind, found[path].default) == (kind, default), path
    assert "Timeframe" not in str(found["strategy.zone_timeframe"].options)
    assert found["strategy.zone_timeframe"].options[:2] == ("M1", "M5")


def test_linked_and_unused_values_are_not_shown():
    paths = set(by_path())
    assert not any(p.startswith("engine.sessions") for p in paths)
    assert "strategy.strong_move.atr_mult" not in paths
    assert "strategy.strong_move.atr_period" in paths  # the 5m ATR for SL / TP sizes


def test_help_text_comes_from_the_field_comments():
    found = by_path()
    assert found["strategy.zone_kill"].help == "off: breaks only flip a zone, none kills it"
    assert found["strategy.entry_bos_with_trend"].help.startswith("step 3 with the 5m trend")
    assert found["engine.costs.symbols.XAUUSD.spread"].help == "ask - bid in price units"

    @dataclass(frozen=True)
    class Example:
        # explained above
        # over two lines
        a: int = 1
        b: dict = field(default_factory=dict)  # trailing wins

        c: float = 0.5

    assert field_comments(Example) == {
        "a": "explained above over two lines",
        "b": "trailing wins",
        "c": "",
    }


def test_form_values_round_trip_to_the_same_settings():
    assert to_json(settings_from_values(form_values())) == to_json(RunSettings())
    assert from_json(to_json(RunSettings())) == RunSettings()
    assert from_json("") == RunSettings()


def test_values_from_the_form_become_typed_settings():
    values = {
        "strategy.zone_kill": False,
        "strategy.zone_kill_breaks": 2.0,  # number inputs may send floats
        "strategy.max_sl_atr_mult": 3,
        "strategy.min_sl_atr_mult": "",  # empty = off
        "strategy.zone_timeframe": "H1",
        "strategy.confluence_kinds": ["FVG"],
        "strategy.sessions.london.local_time": "07:30",
        "engine.costs.symbols.XAUUSD.spread": 0.3,
        "unknown.path": 1,  # e.g. an older preset: ignored
    }
    s = settings_from_values(values)
    assert s.strategy.zone_kill is False and s.strategy.zone_kill_breaks == 2
    assert s.strategy.max_sl_atr_mult == 3.0 and s.strategy.min_sl_atr_mult is None
    assert s.strategy.zone_timeframe is Timeframe.H1
    assert s.strategy.confluence_kinds == frozenset({ZoneKind.FVG})
    assert s.strategy.sessions.london.local_time == time(7, 30)
    assert s.engine.sessions == s.strategy.sessions  # one setting for both
    assert s.engine.costs.symbols["XAUUSD"].spread == 0.3
    assert s.engine.costs.symbols["GBPUSD"].spread == 0.00003  # untouched


@pytest.mark.parametrize(
    ("values", "path"),
    [
        ({"strategy.zone_kill_breaks": 0}, "strategy"),  # dataclass check (>= 1)
        ({"strategy.zone_kill_breaks": 2.5}, "strategy.zone_kill_breaks"),
        ({"strategy.min_rr": None}, "strategy.min_rr"),
        ({"strategy.min_rr": "abc"}, "strategy.min_rr"),
        ({"strategy.sessions.tokyo.local_time": "9h"}, "strategy.sessions.tokyo.local_time"),
        ({"strategy.zone_timeframe": "M7"}, "strategy.zone_timeframe"),
        ({"warmup_days": -1}, None),
    ],
)
def test_invalid_values_name_their_field(values, path):
    with pytest.raises(SettingsError) as e:
        settings_from_values(values)
    assert e.value.path == path


def test_a_runs_settings_json_loads_back():
    data = json.loads(json.dumps(to_dict(RunSettings())))
    assert from_dict(data) == RunSettings()
    assert from_dict({"strategy": {"min_rr": 1.5}}).strategy.min_rr == 1.5
