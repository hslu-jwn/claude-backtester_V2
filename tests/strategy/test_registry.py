"""Strategy registry and the template folder (ROADMAP C.3).

A new strategy is one folder under `strategy/` plus one line in `strategy/registry.py`.
`_template/` is the starting point and must stay a working (order-less) strategy.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from backtester.core.models import Timeframe
from backtester.data.resample import H4Alignment
from backtester.engine.backtest import run_backtest
from backtester.strategy import registry
from backtester.strategy._template.config import TemplateConfig
from backtester.strategy._template.strategy import TemplateStrategy
from backtester.strategy.base import Strategy
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
from backtester.strategy.ny_index_sweep.strategy import NyIndexSweep
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.strategy import SessionZoneSweep

STRATEGY_DIR = Path(registry.__file__).parent


def test_registered_names_and_order():
    assert list(registry.REGISTRY) == ["session_zone_sweep", "ny_index_sweep"]


def test_names_are_the_folder_names():
    for name, spec in registry.REGISTRY.items():
        assert spec.name == name
        assert (STRATEGY_DIR / name).is_dir(), f"strategy/{name}/ missing"


@pytest.mark.parametrize(
    ("config", "name", "cls"),
    [
        (SessionZoneSweepConfig(), "session_zone_sweep", SessionZoneSweep),
        (NyIndexSweepConfig(), "ny_index_sweep", NyIndexSweep),
    ],
)
def test_config_maps_to_name_and_strategy(config, name, cls):
    assert registry.strategy_name(config) == name
    assert registry.spec_for_config(config).strategy_cls is cls
    strategy = registry.make_strategy("XAUUSD", config)
    assert type(strategy) is cls


def test_default_config_by_name():
    assert registry.default_config("ny_index_sweep") == NyIndexSweepConfig()
    assert registry.default_config("session_zone_sweep") == SessionZoneSweepConfig()


def test_unknown_name_and_config_are_refused_with_the_known_names():
    with pytest.raises(ValueError, match="ny_index_sweep"):
        registry.default_config("nope")
    with pytest.raises(TypeError, match="no registered strategy"):
        registry.make_strategy("XAUUSD", object())


def test_every_registered_strategy_follows_the_contract():
    for spec in registry.REGISTRY.values():
        assert issubclass(spec.strategy_cls, Strategy)
        assert dataclasses.is_dataclass(spec.config_cls)
        assert spec.config_cls.__dataclass_params__.frozen  # configs are frozen
        assert spec.label
        strategy = spec.strategy_cls("XAUUSD", spec.config_cls())
        assert strategy.base_timeframe in strategy.timeframes
        assert isinstance(strategy.full_history, tuple)
        assert isinstance(strategy.h4_alignment, H4Alignment)


def test_strategy_base_defaults_are_the_old_getattr_defaults():
    """The runner used getattr(strategy, "h4_alignment", UTC) / ("full_history", ())."""
    template = TemplateStrategy("XAUUSD", TemplateConfig())
    assert template.h4_alignment is H4Alignment.UTC
    assert template.full_history == ()
    assert SessionZoneSweep("XAUUSD", SessionZoneSweepConfig()).h4_alignment is H4Alignment.UTC
    assert NyIndexSweep("XAUUSD", NyIndexSweepConfig()).h4_alignment is H4Alignment.NEW_YORK


def test_template_is_a_working_strategy_that_never_trades(make_series):
    strategy = TemplateStrategy("TEST", TemplateConfig())
    ohlc = [(1.0, 1.1, 0.9, 1.0 + 0.01 * (i % 5)) for i in range(60)]
    series = make_series(ohlc, strategy.base_timeframe)
    assert run_backtest(strategy, [series]) == []


def test_template_is_not_registered():
    assert all(spec.strategy_cls is not TemplateStrategy for spec in registry.REGISTRY.values())
    assert TemplateStrategy("TEST", TemplateConfig()).base_timeframe is Timeframe.M5


def test_template_config_validates():
    with pytest.raises(ValueError):
        TemplateConfig(min_rr=0)


def test_template_folder_has_a_readme_with_the_steps():
    text = (STRATEGY_DIR / "_template" / "README.md").read_text(encoding="utf8")
    for needle in ("registry.py", "docs/", "no-lookahead", "tests/strategy/"):
        assert needle in text


def test_run_settings_accept_every_registered_config():
    """`runner.StrategyConfig` (RunSettings.strategy's type) lists each registered config."""
    from typing import get_args

    from backtester.runner import StrategyConfig

    assert set(get_args(StrategyConfig)) == {s.config_cls for s in registry.REGISTRY.values()}
