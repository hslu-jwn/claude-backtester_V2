"""Random-entry baseline (kind B of the Monte Carlo report): is the strategy's choice better
than a coin flip on the same days?

Spec: risk-management.md > Monte Carlo report, B (ROADMAP 12.1). Gap fade: the same gap days with
the same stop and exit; per day a coin picks the strategy's direction (fade) or the other one
(follow). The two trade lists come from two runs that differ only in that choice
(`GapFadeConfig.mode`). Trades are matched per (symbol, entry day); a day present in only one
list, or twice in one list, raises ValueError (the lists must come from the same days).

Works on any objects with `symbol`, `entry_time` and `r_net` (TradeResult, TradeRecord).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

PERCENT = 100.0
LOW_PCT, HIGH_PCT = 5.0, 95.0


@dataclass(frozen=True, slots=True)
class RandomBaselineConfig:
    runs: int = 1000  # spec: 1,000 runs
    seed: int = 42  # spec: every random draw seeded with 42
    p_strategy: float = 0.5  # chance per day to take the strategy's trade (coin flip)

    def __post_init__(self) -> None:
        if self.runs < 1:
            raise ValueError("runs must be >= 1")
        if not 0.0 <= self.p_strategy <= 1.0:
            raise ValueError("p_strategy must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class RandomBaselineResult:
    strategy_net_r: float
    run_net_r: tuple[float, ...]  # one total net R per random run
    percentile: float  # % of the runs with net R strictly below the strategy's
    mean: float
    p5: float
    p95: float
    days: int  # matched days


def _by_day(trades: Iterable, label: str) -> dict[tuple[str, object], float]:
    out: dict[tuple[str, object], float] = {}
    for t in trades:
        key = (t.symbol, t.entry_time.date())
        if key in out:
            raise ValueError(f"{label}: two trades on {key[0]} {key[1]} (one trade a day expected)")
        out[key] = t.r_net
    return out


def random_entry_baseline(
    strategy_trades: Sequence,
    alternative_trades: Sequence,
    config: RandomBaselineConfig | None = None,
) -> RandomBaselineResult:
    """Net R of `config.runs` random runs, each picking per matched day the strategy's trade
    (probability `p_strategy`) or the alternative's, and the strategy's percentile among them."""
    cfg = config or RandomBaselineConfig()
    mine = _by_day(strategy_trades, "strategy trades")
    other = _by_day(alternative_trades, "alternative trades")
    if mine.keys() != other.keys():
        diff = sorted(mine.keys() ^ other.keys(), key=str)[:3]
        raise ValueError(f"the trade lists cover different days, e.g. {diff}")
    keys = sorted(mine, key=str)
    a = np.array([mine[k] for k in keys])
    b = np.array([other[k] for k in keys])
    rng = np.random.default_rng(cfg.seed)
    pick_strategy = rng.random((cfg.runs, len(keys))) < cfg.p_strategy
    runs = np.where(pick_strategy, a, b).sum(axis=1)
    strategy_net = float(a.sum())
    return RandomBaselineResult(
        strategy_net_r=strategy_net,
        run_net_r=tuple(float(x) for x in runs),
        percentile=float((runs < strategy_net).mean() * PERCENT),
        mean=float(runs.mean()),
        p5=float(np.percentile(runs, LOW_PCT)),
        p95=float(np.percentile(runs, HIGH_PCT)),
        days=len(keys),
    )
