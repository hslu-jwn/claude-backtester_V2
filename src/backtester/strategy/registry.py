"""The strategies the runner, the command line and the results know by name.

A new strategy is one folder under `strategy/` (start from `_template/`) plus one entry
in `_SPECS` below. Nothing else needs to change: the runner builds the strategy from its
config (`make_strategy`), `run.py --strategy` takes the names, the results file records
`strategy_name(config)`.

Spec: ROADMAP.md › C.3.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from backtester.detectors.settings import DetectorSettings
from backtester.strategy.base import Strategy
from backtester.strategy.gap_fade.config import GapFadeConfig
from backtester.strategy.gap_fade.strategy import GapFade
from backtester.strategy.no_wick.config import NoWickConfig
from backtester.strategy.no_wick.strategy import NoWick
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
from backtester.strategy.ny_index_sweep.strategy import NyIndexSweep
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.strategy import SessionZoneSweep
from backtester.strategy.trend_following.config import TrendFollowingConfig
from backtester.strategy.trend_following.strategy import TrendFollowing


@dataclass(frozen=True, slots=True)
class StrategySpec:
    name: str  # the folder name under strategy/, `--strategy`, results settings.json
    label: str  # for menus
    config_cls: type  # frozen dataclass with the spec defaults
    strategy_cls: type[Strategy]  # called as strategy_cls(symbol, config, detectors)


_SPECS = (
    StrategySpec(
        "session_zone_sweep", "Strategy 1 · Session zone sweep",
        SessionZoneSweepConfig, SessionZoneSweep,
    ),
    StrategySpec(
        "ny_index_sweep", "Strategy 2 · NY Open index sweep", NyIndexSweepConfig, NyIndexSweep
    ),
    StrategySpec("no_wick", "Strategy 3 · No-wick candle in the trend", NoWickConfig, NoWick),
    StrategySpec(
        "trend_following", "Strategy 4 · Trend following (Kaufman)",
        TrendFollowingConfig, TrendFollowing,
    ),
    StrategySpec("gap_fade", "Strategy 5 · Gap fade (index open)", GapFadeConfig, GapFade),
)  # fmt: skip

REGISTRY: Mapping[str, StrategySpec] = MappingProxyType({s.name: s for s in _SPECS})


def spec_for_config(config: object) -> StrategySpec:
    for spec in REGISTRY.values():
        if isinstance(config, spec.config_cls):
            return spec
    raise TypeError(f"no registered strategy for a {type(config).__name__} config")


def make_strategy(
    symbol: str, config: object, detectors: DetectorSettings | None = None
) -> Strategy:
    """The strategy the config belongs to, with the shared detector settings."""
    return spec_for_config(config).strategy_cls(symbol, config, detectors)


def strategy_name(config: object) -> str:
    return spec_for_config(config).name


def default_config(name: str) -> object:
    """The config of a strategy with the spec defaults."""
    try:
        return REGISTRY[name].config_cls()
    except KeyError:
        raise ValueError(f"unknown strategy {name!r} (known: {', '.join(REGISTRY)})") from None
