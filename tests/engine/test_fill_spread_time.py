"""A fill at a bar close pays the spread of the bar that just closed (rule set by the user,
2026-11-13, research-log "rollover-hour spread"): live buys sent at 18:00:0x New York still paid the
wide hour-17 rollover spread, while the table lookup at 18:00:00 gave hour 18's normal value.
Spec: risk-management.md › Costs › Spread at a bar close."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from conftest import build_series

from backtester.core.models import Direction, Timeframe
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig, SymbolCosts, fill_spread_time
from backtester.engine.spread_table import SpreadTable
from backtester.strategy.base import Order, Strategy

# 2026-01-05 is winter: 23:00 UTC = 18:00 New York
REOPEN = datetime(2026, 1, 5, 23, tzinfo=UTC)
TABLE = SpreadTable(values={"XAUUSD": {2026: {17: 1.2, 18: 0.3}}})


def costs(**kw):
    sym = SymbolCosts(spread=0.25, commission_per_lot=0.0, contract_size=1, slippage=0.0)
    return CostConfig(symbols={"XAUUSD": sym}, spread_table=TABLE, swap_enabled=False, **kw)


def test_fill_time_looks_one_microsecond_back():
    assert fill_spread_time(REOPEN) == REOPEN - timedelta(microseconds=1)
    assert fill_spread_time(None) is None


def test_the_reopen_instant_takes_the_rollover_hour_and_inside_a_bar_nothing_changes():
    c = costs()
    assert c.spread("XAUUSD", fill_spread_time(REOPEN)) == pytest.approx(1.2)
    later = REOPEN + timedelta(seconds=30)
    assert c.spread("XAUUSD", fill_spread_time(later)) == c.spread("XAUUSD", later) == 0.3


class EnterAtFirstClose(Strategy):
    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)
    uses_session_break_even = False

    def __init__(self, direction):
        self.direction = direction

    def on_candle(self, now, views):
        base = views[Timeframe.M5]
        if base.cursor != 0:
            return []
        close = base.current.close
        sl = close - 2.0 if self.direction is Direction.BULLISH else close + 2.0
        return [Order(self.direction, close, sl, None)]


FLAT = (100.0, 100.1, 99.9, 100.0)


def run(direction, first_open, **kw):
    series = build_series([FLAT] * 3, symbol="XAUUSD", start=first_open)
    return run_backtest(EnterAtFirstClose(direction), [series], EngineConfig(costs=costs(**kw)))


def test_a_long_entry_at_the_close_of_the_last_rollover_bar_pays_the_rollover_spread():
    # a short pays its spread at the exit (review B8), so only the long's entry changes
    (trade,) = run(Direction.BULLISH, REOPEN - Timeframe.M5.duration)  # bar 17:55-18:00 NY
    assert trade.entry_time == REOPEN
    assert trade.entry_fill == pytest.approx(101.2)
    assert trade.spread_r == pytest.approx(1.2 / 2.0)


def test_an_entry_at_the_close_of_the_first_bar_after_it_pays_hour_18():
    (trade,) = run(Direction.BULLISH, REOPEN)  # bar 18:00-18:05 New York
    assert trade.entry_fill == pytest.approx(100.3)


def test_the_cost_filter_sees_the_same_spread_as_the_fill():
    # SL 2.0 away: 1.2 / 2 = 0.6 R > 0.5 -> refused; at hour 18 (0.15 R) it would pass
    assert run(Direction.BULLISH, REOPEN - Timeframe.M5.duration, max_cost_r=0.5) == []
    (trade,) = run(Direction.BULLISH, REOPEN, max_cost_r=0.5)
    assert trade.spread_r == pytest.approx(0.15)


def test_signal_cost_of_a_strategy_uses_the_bar_that_just_closed():
    s = EnterAtFirstClose(Direction.BULLISH)
    s.configure_costs(costs())
    assert s.signal_price_cost("XAUUSD", REOPEN, 100.0) == pytest.approx(1.2)
