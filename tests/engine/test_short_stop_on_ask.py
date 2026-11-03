"""A short's SL is a buy stop: the broker triggers it when the ask reaches the SL and fills it
there, not when the bid does (rule set by the user, 2026-11-03).
Spec: risk-management.md › Costs › Short stop on ask.
"""

from __future__ import annotations

from conftest import DEFAULT_START, build_candles, build_series
from test_cost_filter import FLAT, LONG, SHORT, OneOrder

from backtester.core.models import Timeframe
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig, SymbolCosts
from backtester.engine.trade import ExitReason, OpenTrade

# entry at the first close 100.0 (bid), spread 0.2, no slippage or commission
SYMBOL = SymbolCosts(spread=0.2, commission_per_lot=0.0, contract_size=100)


def run(direction, sl, candle, **cost_kw):
    cost = CostConfig(symbols={"TEST": SYMBOL}, spread_table=None, **cost_kw)
    series = build_series([FLAT, candle, FLAT])
    (trade,) = run_backtest(OneOrder([(direction, sl)]), [series], EngineConfig(costs=cost))
    return trade


def test_default_is_on():
    assert CostConfig().short_sl_on_ask is True


def test_ask_at_the_sl_stops_the_short_and_fills_at_the_sl():
    trade = run(SHORT, 101.0, (100.0, 100.85, 99.9, 100.0))  # ask high 101.05
    assert trade.exit_reason is ExitReason.STOP_LOSS
    assert trade.exit_price == 100.8  # the bid when the ask touched 101.0
    assert trade.exit_fill == 101.0


def test_ask_below_the_sl_does_not_stop():
    trade = run(SHORT, 101.0, (100.0, 100.75, 99.9, 100.0))  # ask high 100.95
    assert trade.exit_reason is not ExitReason.STOP_LOSS


def test_gap_through_the_sl_fills_at_the_ask_of_the_open():
    trade = run(SHORT, 101.0, (101.5, 101.6, 101.4, 101.5))
    assert trade.exit_price == 101.5 and trade.exit_fill == 101.7


def test_switch_off_reproduces_the_bid_trigger():
    trade = run(SHORT, 101.0, (100.0, 100.85, 99.9, 100.0), short_sl_on_ask=False)
    assert trade.exit_reason is not ExitReason.STOP_LOSS
    trade = run(SHORT, 101.0, (100.0, 101.0, 99.9, 100.0), short_sl_on_ask=False)
    assert trade.exit_price == 101.0 and abs(trade.exit_fill - 101.2) < 1e-9


def test_long_still_stops_on_the_bid():
    trade = run(LONG, 99.0, (100.0, 100.1, 99.05, 100.0))
    assert trade.exit_reason is not ExitReason.STOP_LOSS
    trade = run(LONG, 99.0, (100.0, 100.1, 99.0, 100.0))
    assert trade.exit_fill == 99.0


def _short(**kw):
    return OpenTrade(
        symbol="TEST", direction=SHORT, entry_time=DEFAULT_START, entry_candle=DEFAULT_START,
        entry=100.0, entry_fill=100.0, initial_stop=101.0, stop_loss=101.0, take_profit=None,
        break_even_check=None, break_even_level=99.8, spread=0.2, **kw,
    )  # fmt: skip


def test_break_even_stop_keeps_its_bid_trigger_and_fill():
    # BE level 99.8 is the bid that nets 0 R (fill 99.8 + spread = entry 100.0); the broker SL
    # for it is 100.0, triggered by the ask, so the fill does not change
    candle = build_candles(
        [(99.0, 99.79, 98.9, 99.0), (99.0, 99.8, 98.9, 99.0)], Timeframe.M5, DEFAULT_START
    )
    for on_ask in (True, False):
        trade = _short(short_sl_on_ask=on_ask)
        trade.move_to_break_even(DEFAULT_START)
        trade.on_candle(candle[0], DEFAULT_START + Timeframe.M5.duration)
        assert not trade.is_closed
        trade.on_candle(candle[1], DEFAULT_START + 2 * Timeframe.M5.duration)
        assert trade.parts[0].price == 99.8 and abs(trade.parts[0].fill - 100.0) < 1e-9
