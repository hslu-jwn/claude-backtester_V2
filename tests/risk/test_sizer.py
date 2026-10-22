"""Position sizing: lots = risk % x balance / (SL distance x value of 1.0 price move per lot)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from backtester.risk.sizer import SymbolSpec, lots_for_risk, spec_from_symbol_info

INDEX = SymbolSpec(tick_size=0.01, tick_value=0.01, volume_min=0.1, volume_step=0.1, volume_max=500)
GOLD = SymbolSpec(tick_size=0.01, tick_value=1.0, volume_min=0.01, volume_step=0.01, volume_max=50)
EURUSD = SymbolSpec(
    tick_size=0.00001, tick_value=1.0, volume_min=0.01, volume_step=0.01, volume_max=100
)


def test_index_example():
    # 250 USD risk / (5.5 points x 1 USD per point) = 45.45 -> step 0.1 -> 45.4
    s = lots_for_risk(100_000, 0.25, 5.5, INDEX)
    assert s.lots == 45.4 and s.reason == ""
    assert s.risk_money == pytest.approx(45.4 * 5.5)


def test_gold_example():
    # 250 / (5.0 x 100) = 0.5 lots exactly
    assert lots_for_risk(100_000, 0.25, 5.0, GOLD).lots == 0.5


def test_fx_example_rounds_down():
    # 250 / (0.0017 x 100000) = 1.4705 -> 1.47
    assert lots_for_risk(100_000, 0.25, 0.0017, EURUSD).lots == 1.47


def test_exact_multiple_is_not_lost_to_float_error():
    # 0.29 / 0.01 = 28.999999999999996: still 0.29 lots
    spec = SymbolSpec(0.01, 1.0, 0.01, 0.01, 100)
    s = lots_for_risk(10_000, 1.0, 100 / 0.29 / 100, spec)  # risk 100 USD
    assert s.lots == pytest.approx(0.29)


def test_below_the_minimum_is_skipped_with_a_reason():
    s = lots_for_risk(1_000, 0.25, 5.0, GOLD)  # 2.5 / 500 = 0.005
    assert s.lots is None and "below the minimum lot 0.01" in s.reason


def test_capped_at_the_maximum():
    s = lots_for_risk(10_000_000, 1.0, 1.0, GOLD)
    assert s.lots == 50 and "capped" in s.reason


@pytest.mark.parametrize(
    "args",
    [(0, 0.25, 5.0), (-1, 0.25, 5.0), (1000, 0, 5.0), (1000, 0.25, 0), (1000, 0.25, -1)],
)
def test_bad_inputs_raise(args):
    with pytest.raises(ValueError):
        lots_for_risk(*args, GOLD)


def test_bad_spec_raises():
    with pytest.raises(ValueError):
        SymbolSpec(0.0, 1.0, 0.01, 0.01, 1)
    with pytest.raises(ValueError):
        SymbolSpec(0.01, 1.0, 0.0, 0.01, 1)
    with pytest.raises(ValueError):
        SymbolSpec(0.01, 1.0, 0.01, 0.01, 0.001)  # volume_min > volume_max
    with pytest.raises(ValueError):
        SymbolSpec(0.01, 1.0, 0.01, 2.0, 1.0)  # volume_step > volume_max


def test_capped_volume_rounded_down_to_step():
    # Step/min 0.3, max 1.0: raw = 5.0 lots -> capped at max 1.0, rounded down to step 0.9
    spec = SymbolSpec(
        tick_size=0.01, tick_value=1.0, volume_min=0.3, volume_step=0.3, volume_max=1.0
    )
    s = lots_for_risk(10_000, 1.0, 0.20, spec)  # 100 / (0.20 * 100) = 5.0 raw lots
    assert s.lots == 0.9 and "capped" in s.reason

    # Capped volume rounded down to step falls below volume_min:
    spec_under = SymbolSpec(
        tick_size=0.01, tick_value=1.0, volume_min=0.8, volume_step=0.5, volume_max=0.9
    )
    s_under = lots_for_risk(
        10_000, 1.0, 0.20, spec_under
    )  # raw 5.0 -> capped 0.9 -> step 0.5 < min 0.8
    assert s_under.lots is None and "below the minimum" in s_under.reason


@pytest.mark.parametrize("field", ["volume_min", "volume_step", "volume_max"])
@pytest.mark.parametrize("value", [0.0, -1.0, float("nan"), float("inf"), float("-inf")])
def test_invalid_volume_spec_is_rejected(field, value):
    values = {
        "tick_size": 0.01,
        "tick_value": 1.0,
        "volume_min": 0.01,
        "volume_step": 0.01,
        "volume_max": 1.0,
    }
    values[field] = value
    with pytest.raises(ValueError):
        SymbolSpec(**values)


def test_spec_from_symbol_info():
    info = SimpleNamespace(
        trade_tick_size=0.01, trade_tick_value=0.01, volume_min=0.1, volume_step=0.1, volume_max=9
    )
    assert spec_from_symbol_info(info) == SymbolSpec(0.01, 0.01, 0.1, 0.1, 9)
    assert spec_from_symbol_info(info).value_per_unit == pytest.approx(1.0)
