"""Engine review findings #3-5 and #10: validation and closure notifications."""

from dataclasses import replace

import pytest
from conftest import DEFAULT_START, build_series

from backtester.core.models import Direction, Timeframe
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.base import Order, Strategy

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
QUIET = (100, 100.5, 99.5, 100)
TOUCH = (100, 101, 98.5, 100.5)
NO_COSTS = EngineConfig(
    costs=CostConfig(spread_enabled=False, commission_enabled=False),
    break_even_at_next_session=False,
)


class OrdersAt(Strategy):
    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)

    def __init__(self, orders, pending=None):
        self.orders = orders
        self.pending = pending or {}
        self.cursor = -1
        self.closed = []

    def on_candle(self, now, views):
        self.cursor = views[self.base_timeframe].cursor
        return self.orders.get(self.cursor, [])

    def pending_limit_orders(self):
        return self.pending.get(self.cursor, [])

    def on_trade_closed(self, ref, result):
        self.closed.append((ref, result))


def run(strategy, ohlc=None):
    return run_backtest(strategy, [build_series(ohlc or [QUIET, TOUCH])], NO_COSTS)


def limit():
    return Order(LONG, 99, 98, 103, limit_fill=True, ref="limit")


@pytest.mark.parametrize("at", [0, 1])
def test_limit_fill_requires_placement_at_a_previous_step(at):
    # An order chosen from this candle's low must never be accepted retrospectively.
    order = replace(limit(), entry=99.5 if at == 0 else 98.5)
    strategy = OrdersAt({at: [order]})
    with pytest.raises(ValueError, match="placed"):
        run(strategy)


def test_limit_placement_on_fill_step_is_too_late():
    order = limit()
    with pytest.raises(ValueError, match="placed"):
        run(OrdersAt({1: [order]}, {1: [order]}))


@pytest.mark.parametrize(
    "changes",
    [{"entry": 98.75}, {"stop_loss": 97}, {"take_profit": 104}, {"ref": "other"}],
)
def test_limit_fill_cannot_change_previously_placed_order(changes):
    order = limit()
    with pytest.raises(ValueError, match="placed"):
        run(OrdersAt({1: [replace(order, **changes)]}, {0: [order]}))


def test_one_pending_limit_cannot_fill_twice():
    order = limit()
    with pytest.raises(ValueError, match="placed"):
        run(OrdersAt({1: [order, order]}, {0: [order]}))


def test_cancelled_limit_cannot_fill_later():
    order = limit()
    with pytest.raises(ValueError, match="placed"):
        run(OrdersAt({2: [order]}, {0: [order]}), [QUIET, QUIET, TOUCH])


def test_previously_placed_limit_retains_fill_candle_sl_and_ignores_tp():
    order = replace(limit(), take_profit=100)
    strategy = OrdersAt({1: [replace(order)]}, {0: [order]})
    [trade] = run(strategy)
    assert trade.entry == 99 and trade.entry_time == DEFAULT_START + 2 * Timeframe.M5.duration
    assert trade.exit_reason is ExitReason.END_OF_DATA
    assert trade.r_gross == pytest.approx(1.5)
    strategy = OrdersAt({1: [order]}, {0: [order]})
    [loss] = run(strategy, [QUIET, (100, 101, 97, 100.5)])
    assert loss.exit_reason is ExitReason.STOP_LOSS and loss.r_gross == -1


@pytest.mark.parametrize("direction", [LONG, SHORT])
def test_previously_placed_limit_allows_existing_gap_at_open_fill(direction):
    order = limit()
    candles = [QUIET, (98.75, 98.9, 98.5, 98.8)]
    if direction is SHORT:
        order = replace(order, direction=SHORT, entry=101, stop_loss=102, take_profit=97)
        candles = [QUIET, (101.25, 101.5, 101.1, 101.2)]
    strategy = OrdersAt({1: [replace(order, entry=candles[1][0])]}, {0: [order]})
    [trade] = run(strategy, candles)
    assert trade.entry == candles[1][0] and trade.initial_stop == order.stop_loss
    assert trade.take_profit == order.take_profit


@pytest.mark.parametrize("field", ["tp1_share", "tp2_share"])
@pytest.mark.parametrize("share", [-0.25, 0, float("nan"), float("inf"), -float("inf")])
def test_partial_exit_shares_must_be_finite_and_positive(field, share):
    order = Order(
        LONG, 100, 98, 102, take_profit_2=104, take_profit_3=106, tp1_share=0.5, tp2_share=0.25
    )
    with pytest.raises(ValueError, match=field):
        run(OrdersAt({0: [replace(order, **{field: share})]}))


@pytest.mark.parametrize("share", [0.5, 0.75])
def test_partial_exit_shares_must_leave_positive_remainder(share):
    order = Order(
        LONG, 100, 98, 102, take_profit_2=104, take_profit_3=106, tp1_share=0.5, tp2_share=share
    )
    with pytest.raises(ValueError, match="share"):
        run(OrdersAt({0: [order]}))


@pytest.mark.parametrize(
    "field", ["entry", "stop_loss", "take_profit", "take_profit_2", "take_profit_3"]
)
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_order_rejects_nonfinite_prices_before_level_validation(field, value):
    # Other levels are deliberately invalid: the finite check must run first.
    order = Order(LONG, 100, 101, 99, take_profit_2=98, take_profit_3=97)
    with pytest.raises(ValueError, match=rf"{field}.*finite"):
        run(OrdersAt({0: [replace(order, **{field: value})]}))


@pytest.mark.parametrize("ref", [None, "trade"])
def test_end_of_data_notifies_strategy_once_with_returned_result(ref):
    order = Order(LONG, 100, 98, None, ref=ref)
    strategy = OrdersAt({0: [order], 1: [replace(order, entry=100.5)]})
    trades = run(strategy)
    assert len(trades) == 2
    assert strategy.closed == [(ref, trade) for trade in trades]
    assert all(result is trade for (_, result), trade in zip(strategy.closed, trades))
    assert all(trade.exit_reason is ExitReason.END_OF_DATA for trade in trades)
