"""A sell whose SL is not above the ask at the fill is refused, as the broker refuses it
(live/bot.py `_stops_refused`; rule set by the user, 2026-11-03).
Spec: risk-management.md › Costs › Stop inside the spread.
"""

from __future__ import annotations

from test_cost_filter import LONG, SHORT, run

from backtester.engine.costs import CostConfig

# test_cost_filter: entry 100.0 (bid), spread 0.2 -> ask 100.2


def test_default_is_on():
    assert CostConfig().refuse_stop_in_spread is True


def test_short_with_sl_inside_the_spread_is_refused_and_the_strategy_told():
    strategy, trades = run([(SHORT, 100.1), (SHORT, 100.5)])
    assert [t.initial_stop for t in trades] == [100.5]
    assert [ref for ref, _ in strategy.skipped] == [0]


def test_short_with_sl_at_the_ask_is_refused():
    strategy, trades = run([(SHORT, 100.2)])
    assert trades == [] and [ref for ref, _ in strategy.skipped] == [0]


def test_long_closes_at_the_bid_so_a_tight_sl_is_still_filled():
    strategy, trades = run([(LONG, 99.9)])  # 0.1 below the bid: the broker accepts it
    assert len(trades) == 1 and strategy.skipped == []


def test_no_spread_nothing_to_refuse():
    _, trades = run([(SHORT, 100.1)], spread_enabled=False)
    assert len(trades) == 1


def test_switch_off_reproduces_old_results():
    strategy, trades = run([(SHORT, 100.1)], refuse_stop_in_spread=False)
    assert len(trades) == 1 and strategy.skipped == []
