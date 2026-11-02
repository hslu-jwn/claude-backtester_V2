from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.analytics.robustness import (
    RobustnessConfig,
    load_slippage_p90,
    stressed_net,
    stressed_net_p90,
    trade_robustness,
)
from backtester.analytics.scorecard import ScorecardConfig, scorecard

NOW = datetime(2020, 1, 1, tzinfo=UTC)
COSTS = SimpleNamespace(slippage=lambda symbol, entry: 1.0)


def trade(**changes):
    values = {
        "symbol": "TEST",
        "entry": 100.0,
        "initial_stop": 90.0,
        "r_net": 0.8,
        "r_gross": 1.0,
        "exit_reason": "stop_loss",
        "parts": [],
        "limit_fill": False,
        "entry_time": NOW,
        "exit_time": NOW + timedelta(hours=1),
        "planned_r": None,
    }
    values.update(changes)
    return SimpleNamespace(**values)


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({}, 0.4),
        ({"exit_reason": "take_profit"}, 0.6),
        ({"exit_reason": "take_profit", "limit_fill": True}, 0.8),
        (
            {
                "parts": [
                    {"reason": "take_profit", "share": 0.5},
                    {"reason": "stop_loss", "share": 0.5},
                ]
            },
            0.5,
        ),
        ({"initial_stop": 110.0, "direction": "short"}, 0.4),
    ],
)
def test_market_fills(changes, expected):
    assert stressed_net_p90([trade(**changes)], {"TEST": 3.0}, COSTS) == pytest.approx(expected)


def test_floor_fallback_mixed_and_zero_risk():
    t = trade()
    assert stressed_net_p90([t], {"TEST": 0.5}, COSTS) == t.r_net
    other = trade(symbol="OTHER")
    assert stressed_net_p90([other], {"TEST": 3}, COSTS) == stressed_net([other], 1.5)
    assert stressed_net_p90([t, other], {"TEST": 3}, COSTS) == pytest.approx(
        0.4 + stressed_net([other], 1.5)
    )
    with pytest.raises(ValueError):
        stressed_net_p90([trade(initial_stop=100)], {"TEST": 3}, COSTS)


def test_modes_and_reporting(monkeypatch):
    monkeypatch.setattr("backtester.analytics.robustness.load_slippage_p90", lambda: {"TEST": 3})
    with pytest.raises(ValueError):
        RobustnessConfig(cost_stress_mode="x")
    with pytest.raises(ValueError):
        ScorecardConfig(cost_stress_mode="x")
    trades = [trade(), trade(symbol="OTHER")]
    row = trade_robustness(trades, costs=COSTS)
    assert row["cost_stress_mode"] == "p90"
    assert row["stressed_unmeasured_symbols"] == ["OTHER"]
    assert row["net_r_stressed"] == pytest.approx(1.1)
    factor = trade_robustness(trades, RobustnessConfig(cost_stress_mode="factor"))
    assert factor["stressed_unmeasured_symbols"] == []
    assert factor["net_r_stressed"] == stressed_net(trades, 1.5)
    assert scorecard(trades, ScorecardConfig(cost_stress_mode="factor"))[
        "net_r_stressed"
    ] == stressed_net(trades, 1.5)
    assert scorecard(trades, costs=COSTS)["net_r_stressed"] == pytest.approx(1.1)


def test_packaged_table():
    table = load_slippage_p90()
    assert len(table) == 23
    assert {"GER40", "XAUUSD", "NATGAS"} <= table.keys()
