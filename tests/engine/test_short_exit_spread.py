"""Review B8 (the user, 2026-11-11): a short pays the ask when it closes, so its spread is the one
of the candle that manages it, not the entry's. Longs pay the spread once, at the entry.
Spec: risk-management.md › Costs › Short stop on ask. Winter: New York = UTC - 5."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from conftest import build_series

from backtester.core.models import Direction, Timeframe
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig, SymbolCosts
from backtester.engine.spread_table import SpreadTable
from backtester.engine.trade import ExitReason
from backtester.strategy.base import Order, Strategy

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
FLAT = (100.0, 100.1, 99.9, 100.0)
START = datetime(2026, 1, 5, 13, 55, tzinfo=UTC)  # first close 14:00 UTC = 09:00 New York
N = 98  # last candle 22:00-22:05 UTC = 17:00 New York (the wide rollover hour)
QUIET, WIDE = 0.1, 1.0


class Scripted(Strategy):
    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)

    def __init__(self, direction):
        self.direction = direction

    def on_candle(self, now, views):
        if views[Timeframe.M5].cursor != 0:
            return []
        sl = 98.0 if self.direction is LONG else 102.0
        return [Order(self.direction, views[Timeframe.M5].current.close, sl, None)]


def costs() -> CostConfig:
    hours = {h: QUIET for h in range(24)} | {17: WIDE}
    return CostConfig(
        commission_enabled=False,
        swap_enabled=False,
        spread_table=SpreadTable({"TEST": {2026: hours}}),
        symbols={"TEST": SymbolCosts(spread=QUIET, commission_per_lot=0.0, contract_size=100)},
    )


def run(direction, rows):
    [t] = run_backtest(Scripted(direction), [build_series(rows, start=START)], EngineConfig(costs=costs()))
    return t


def test_short_closed_in_the_wide_hour_pays_the_wide_spread():
    t = run(SHORT, [FLAT] * N)
    assert t.exit_reason is ExitReason.END_OF_DATA
    assert t.exit_fill == pytest.approx(100.0 + WIDE)
    assert t.spread_r == pytest.approx(WIDE / 2.0)
    assert t.r_net == pytest.approx(t.r_gross - WIDE / 2.0)


def test_long_still_pays_the_entry_spread_once():
    t = run(LONG, [FLAT] * N)
    assert t.entry_fill == pytest.approx(100.0 + QUIET)
    assert t.r_net == pytest.approx(t.r_gross - QUIET / 2.0)


def test_short_stop_is_triggered_by_the_wide_ask():
    rows = [FLAT] * (N - 1) + [(100.0, 101.5, 99.9, 100.0)]  # bid 101.5 + 1.0 spread > SL 102
    t = run(SHORT, rows)
    assert t.exit_reason is ExitReason.STOP_LOSS
    assert t.exit_fill == pytest.approx(102.0)


def test_short_stop_not_triggered_in_a_quiet_hour():
    rows = [FLAT] * 10 + [(100.0, 101.5, 99.9, 100.0)] + [FLAT] * (N - 11)
    assert run(SHORT, rows).exit_reason is ExitReason.END_OF_DATA
