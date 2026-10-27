"""The bot runs a strategy chosen by name (ROADMAP V2.6d step 1, the user 2026-10-27): the
forward-test default stays strategy 6; `--strategy fill_probe` runs the fill-collection test
tool on many symbols at a tiny risk, with its own comment prefix so its trades never mix with
strategy 6's."""

from __future__ import annotations

import pytest
from test_bot import SYM, World

from backtester.live import bot as bot_module
from backtester.live.bot import BotConfig
from backtester.strategy.fill_probe.config import FillProbeConfig
from backtester.strategy.fill_probe.strategy import FillProbe
from backtester.strategy.opening_range.strategy import OpeningRange
from backtester.strategy.registry import REGISTRY


def test_default_is_the_forward_strategy():
    cfg = BotConfig()
    assert cfg.strategy_name == "opening_range" and cfg.comment_prefix == "orb"


def test_cli_without_strategy_keeps_the_forward_defaults():
    cfg = bot_module.parse_config([])
    assert cfg.strategy_name == "opening_range"
    assert cfg.symbols == bot_module.FORWARD_SYMBOLS
    assert cfg.risk_percent == BotConfig.risk_percent and cfg.comment_prefix == "orb"
    assert cfg.strategy == bot_module.forward_strategy_config()


def test_cli_fill_probe_uses_its_symbols_risk_prefix_and_config():
    cfg = bot_module.parse_config(["--strategy", "fill_probe"])
    assert cfg.strategy_name == "fill_probe" and cfg.comment_prefix == "fp"
    assert cfg.symbols == bot_module.FILL_PROBE_SYMBOLS and len(cfg.symbols) >= 15
    assert cfg.risk_percent == bot_module.FILL_PROBE_RISK_PERCENT <= 0.05
    assert isinstance(cfg.strategy, FillProbeConfig)


def test_cli_explicit_risk_and_symbols_win():
    cfg = bot_module.parse_config(
        ["--strategy", "fill_probe", "--risk", "0.03", "--symbols", "eurusd"]
    )
    assert cfg.risk_percent == 0.03 and cfg.symbols == ("EURUSD",)


def test_unknown_strategy_is_refused():
    with pytest.raises(ValueError, match="strategy"):
        BotConfig(strategy_name="no_such_strategy")


def test_bot_builds_the_chosen_strategy_per_symbol(tmp_path):
    world = World(tmp_path)
    bot = world.bot(strategy_name="fill_probe", strategy=FillProbeConfig(), comment_prefix="fp")
    assert isinstance(bot.symbols[SYM].strategy, FillProbe)
    assert isinstance(world.bot().symbols[SYM].strategy, OpeningRange)


def test_the_fill_probe_stays_out_of_the_research_registry():
    # a test tool: no research tool, grid, golden list or ranking may ever pick it up
    assert "fill_probe" not in REGISTRY
