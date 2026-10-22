"""Random-fills test (kind C of the Monte Carlo report): does the result survive worse fills?

Spec: risk-management.md > Monte Carlo report, C (ROADMAP 12.6). Every market fill of a trade
(the entry, and the exit when it is a stop) gets an extra slippage drawn uniform from 0 to
`factor` x the symbol's slippage setting (`SymbolCosts.slippage`, price units), converted to R by
the trade's stop distance |entry - initial_stop| and subtracted from `r_net`. Take profits are
limit orders: no slippage. The engine applies no slippage to signal (time) exits and the spec
names only entries and stop hits, so `slipped_exit_reasons` is stop loss and break-even (a
stop order) by default. Each stopped exit part gets its own draw, weighted by its share.

Works on any objects with `symbol`, `entry`, `initial_stop`, `exit_reason` (an `ExitReason` or
its string value) and `r_net` (TradeResult, TradeRecord).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np

from backtester.engine.costs import DEFAULT_SYMBOL_COSTS, SymbolCosts

LOW_PCT, MID_PCT, HIGH_PCT = 5.0, 50.0, 95.0


@dataclass(frozen=True, slots=True)
class RandomFillsConfig:
    runs: int = 1000  # spec: 1,000 runs
    seed: int = 42  # spec: every random draw seeded with 42
    factor: float = 2.0  # slippage per fill uniform in [0, factor x setting]
    slipped_exit_reasons: frozenset[str] = frozenset({"stop_loss", "break_even"})

    def __post_init__(self) -> None:
        if self.runs < 1:
            raise ValueError("runs must be >= 1")
        if self.factor < 0:
            raise ValueError("factor must be >= 0")


@dataclass(frozen=True, slots=True)
class RandomFillsResult:
    base_net_r: float  # the trades as they are
    run_net_r: tuple[float, ...]  # one total net R per random run
    p5: float
    p50: float
    p95: float


def _reason(trade) -> str:
    r = trade.exit_reason
    return getattr(r, "value", r)


def market_fills(trade, config: RandomFillsConfig) -> int:
    """Number of market fills of a trade: the entry, plus the exit if it is a stop."""
    return 1 + len(_stop_shares(trade, config))


def _stop_shares(trade, config: RandomFillsConfig) -> list[float]:
    parts = getattr(trade, "parts", ())
    if not parts:
        return [1.0] if _reason(trade) in config.slipped_exit_reasons else []
    shares = []
    for part in parts:
        reason = part["reason"] if isinstance(part, dict) else part.reason
        if getattr(reason, "value", reason) in config.slipped_exit_reasons:
            shares.append(part["share"] if isinstance(part, dict) else part.share)
    return shares


def max_slippage_r(trade, slippage: float, config: RandomFillsConfig | None = None) -> list[float]:
    """Upper bound in R of each market fill's draw: factor x slippage / stop distance."""
    cfg = config or RandomFillsConfig()
    risk = abs(trade.entry - trade.initial_stop)
    if risk <= 0:
        raise ValueError("the trade has no stop distance")
    bound = cfg.factor * slippage / risk
    return [bound, *(bound * share for share in _stop_shares(trade, cfg))]


def random_fills(
    trades: Sequence,
    config: RandomFillsConfig | None = None,
    costs: Mapping[str, SymbolCosts] = DEFAULT_SYMBOL_COSTS,
) -> RandomFillsResult:
    """Total net R of `config.runs` runs with random extra slippage on every market fill."""
    cfg = config or RandomFillsConfig()
    rng = np.random.default_rng(cfg.seed)
    base = np.array([t.r_net for t in trades], dtype=float)
    reduction = np.zeros((cfg.runs, len(trades)))
    for i, t in enumerate(trades):
        if t.symbol not in costs:
            raise KeyError(f"no slippage setting for symbol {t.symbol}")
        for bound in max_slippage_r(t, costs[t.symbol].slippage, cfg):
            reduction[:, i] += rng.uniform(0.0, bound, cfg.runs) if bound > 0 else 0.0
    runs = (base - reduction).sum(axis=1)
    p5, p50, p95 = np.percentile(runs, [LOW_PCT, MID_PCT, HIGH_PCT])
    return RandomFillsResult(
        base_net_r=float(base.sum()),
        run_net_r=tuple(float(x) for x in runs),
        p5=float(p5),
        p50=float(p50),
        p95=float(p95),
    )
