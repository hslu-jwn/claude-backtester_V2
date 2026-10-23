"""Random-fills test (kind C). Spec: risk-management.md > Monte Carlo report, C."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from backtester.analytics.random_fills import RandomFillsConfig, max_slippage_r, random_fills
from backtester.engine.costs import SymbolCosts
from backtester.engine.trade import ExitReason

COSTS = {"X": SymbolCosts(0.0, 0.0, 1, slippage=0.1), "Z": SymbolCosts(0.0, 0.0, 1, slippage=0.0)}


def trade(reason=ExitReason.STOP_LOSS, r_net=-1.0, entry=100.0, stop=98.0, symbol="X"):
    return SimpleNamespace(
        symbol=symbol, entry=entry, initial_stop=stop, exit_reason=reason, r_net=r_net
    )


def test_zero_slippage_setting_leaves_the_result_unchanged():
    res = random_fills(
        [trade(symbol="Z"), trade(ExitReason.TAKE_PROFIT, 1.0, symbol="Z")], costs=COSTS
    )
    assert set(res.run_net_r) == {0.0}
    assert res.p5 == res.p50 == res.p95 == res.base_net_r == 0.0


def test_r_conversion_on_a_hand_example():
    # slippage 0.1, factor 2, stop distance 2 -> each fill at most 0.1 R
    cfg = RandomFillsConfig()
    assert max_slippage_r(trade(), 0.1, cfg) == pytest.approx([0.1, 0.1])  # entry + stop
    assert max_slippage_r(trade(ExitReason.TAKE_PROFIT), 0.1, cfg) == pytest.approx([0.1])


def test_runs_stay_between_base_and_the_maximum_and_centre_on_half():
    res = random_fills([trade()], RandomFillsConfig(runs=4000), COSTS)
    assert all(-1.2 <= r <= -1.0 for r in res.run_net_r)
    assert sum(res.run_net_r) / 4000 == pytest.approx(-1.1, abs=0.005)  # mean 2 x 0.05 R
    assert res.p5 < res.p50 < res.p95


def test_factor_scales_the_slippage():
    r1 = random_fills([trade()], RandomFillsConfig(runs=3000, factor=1.0), COSTS)
    r2 = random_fills([trade()], RandomFillsConfig(runs=3000, factor=2.0), COSTS)
    c1 = r1.base_net_r - sum(r1.run_net_r) / 3000
    c2 = r2.base_net_r - sum(r2.run_net_r) / 3000
    assert c2 == pytest.approx(2 * c1, rel=0.02)
    assert random_fills([trade()], RandomFillsConfig(factor=0.0), COSTS).p50 == -1.0


def test_take_profit_gets_only_entry_slippage():
    res = random_fills([trade(ExitReason.TAKE_PROFIT, 1.0)], RandomFillsConfig(runs=500), COSTS)
    assert all(0.9 <= r <= 1.0 for r in res.run_net_r) and min(res.run_net_r) < 1.0


def test_time_exit_gets_exit_slippage_by_default_but_can_be_configured():
    t = trade(ExitReason.SIGNAL, 0.5)
    assert len(max_slippage_r(t, 0.1)) == 2
    cfg = RandomFillsConfig(slipped_exit_reasons=frozenset({"stop_loss"}))
    assert len(max_slippage_r(t, 0.1, cfg)) == 1


def test_string_exit_reason_like_trades_csv_is_supported():
    assert len(max_slippage_r(trade("stop_loss"), 0.1)) == 2
    assert len(max_slippage_r(trade("take_profit"), 0.1)) == 1


def test_deterministic_and_seed_dependent():
    ts = [trade(), trade(ExitReason.TAKE_PROFIT, 1.0)]
    assert random_fills(ts, costs=COSTS) == random_fills(ts, costs=COSTS)
    other = random_fills(ts, RandomFillsConfig(seed=1), COSTS)
    assert other.run_net_r != random_fills(ts, costs=COSTS).run_net_r


def test_errors():
    with pytest.raises(KeyError):
        random_fills([trade(symbol="NOPE")], costs=COSTS)
    with pytest.raises(ValueError):
        random_fills([trade(stop=100.0)], costs=COSTS)
    with pytest.raises(ValueError):
        RandomFillsConfig(runs=0)
    with pytest.raises(ValueError):
        RandomFillsConfig(factor=-1)
    assert RandomFillsConfig().factor == 2.0 and RandomFillsConfig().runs == 1000
