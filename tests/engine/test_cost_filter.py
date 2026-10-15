"""Cost filter in the engine: an order whose spread + commission in R is above
`CostConfig.max_cost_r` is not filled, and the strategy is told (`on_order_skipped`).
Spec: risk-management.md › Costs › Cost filter.
"""

from __future__ import annotations

import pytest
from conftest import DEFAULT_START, build_series

from backtester.core.models import Direction, Timeframe
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig, SymbolCosts
from backtester.strategy.base import Order, Strategy

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
FLAT = (100.0, 100.1, 99.9, 100.0)
# spread 0.2, commission 4 USD per lot, 100 USD per price unit and lot:
# SL 2 away -> 0.1 + 0.02 = 0.12 R; SL 1 away -> 0.2 + 0.04 = 0.24 R
SYMBOL = SymbolCosts(spread=0.2, commission_per_lot=4.0, contract_size=100)


class OneOrder(Strategy):
    """Enters `orders` (direction, SL) at the first candle's close; records skips."""

    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)
    uses_session_break_even = False

    def __init__(self, orders):
        self.orders = orders
        self.skipped = []

    def on_candle(self, now, views):
        base = views[Timeframe.M5]
        if base.cursor != 0:
            return []
        close = base.current.close
        return [Order(d, close, sl, None, ref=i) for i, (d, sl) in enumerate(self.orders)]

    def on_order_skipped(self, ref, now):
        self.skipped.append((ref, now))


def run(orders, **cost_kw):
    strategy = OneOrder(orders)
    cost = CostConfig(symbols={"TEST": SYMBOL}, **cost_kw)
    trades = run_backtest(strategy, [build_series([FLAT] * 3)], EngineConfig(costs=cost))
    return strategy, trades


def test_default_is_off():
    assert CostConfig().max_cost_r == 0
    strategy, trades = run([(LONG, 99.0)])  # 0.24 R of costs, still filled
    assert len(trades) == 1 and strategy.skipped == []


def test_order_above_the_limit_is_skipped_and_the_strategy_told():
    strategy, trades = run([(LONG, 98.0), (LONG, 99.0)], max_cost_r=0.15)
    assert [t.initial_stop for t in trades] == [98.0]
    assert [ref for ref, _ in strategy.skipped] == [1]
    assert strategy.skipped[0][1] == DEFAULT_START + Timeframe.M5.duration  # first close


def test_cost_equal_to_the_limit_is_filled():
    _, trades = run([(LONG, 98.0)], max_cost_r=0.12)  # 0.1 + 0.02 in floating point
    assert len(trades) == 1


def test_short_is_the_mirror():
    strategy, trades = run([(SHORT, 102.0), (SHORT, 101.0)], max_cost_r=0.15)
    assert [t.initial_stop for t in trades] == [102.0]
    assert [ref for ref, _ in strategy.skipped] == [1]


def test_only_the_costs_that_are_switched_on_count():
    # spread off: SL 1 away costs 0.04 R of commission only
    _, trades = run([(LONG, 99.0)], max_cost_r=0.05, spread_enabled=False)
    assert len(trades) == 1
    _, trades = run([(LONG, 99.0)], max_cost_r=0.05, commission_enabled=False)
    assert trades == []  # 0.2 R of spread


def test_negative_limit_is_rejected():
    with pytest.raises(ValueError):
        CostConfig(max_cost_r=-0.1)


def test_strategy_without_the_hook_just_loses_the_order():
    class Plain(OneOrder):
        on_order_skipped = Strategy.on_order_skipped

    strategy = Plain([(LONG, 99.0)])
    cost = CostConfig(symbols={"TEST": SYMBOL}, max_cost_r=0.1)
    assert run_backtest(strategy, [build_series([FLAT] * 3)], EngineConfig(costs=cost)) == []
