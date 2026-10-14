"""Per-symbol cost defaults. Spec: risk-management.md › Costs."""

from __future__ import annotations

import pytest

from backtester.engine.costs import DEFAULT_SYMBOL_COSTS, CostConfig


@pytest.mark.parametrize(
    ("symbol", "spread", "slippage"),
    [
        ("NAS100", 1.0, 1.0),
        ("US500", 0.5, 0.25),
        ("XAUUSD", 0.25, 0.10),
        ("GBPUSD", 0.00003, 0.00002),  # 0.2 pip
        ("GBPJPY", 0.010, 0.003),  # 0.3 pip
    ],
)
def test_spread_and_slippage_defaults(symbol, spread, slippage):
    costs = DEFAULT_SYMBOL_COSTS[symbol]
    assert costs.spread == spread and costs.slippage == pytest.approx(slippage)


@pytest.mark.parametrize(
    ("symbol", "long", "short", "triple"),
    [
        ("XAUUSD", -61.27, -4.20, 2),
        ("GBPUSD", -5.77, -4.48, 2),
        ("GBPJPY", 2.04, -13.85, 2),
        ("NAS100", -6.912, 0.339, 4),
        ("US500", -1.2218, -0.4575, 4),
    ],
)
def test_swap_defaults_are_ftmo_rates_of_2026_10_14(symbol, long, short, triple):
    # rule set by the user 2026-10-14: FTMO's MT5 rates are the default (ROADMAP 10.4 table)
    costs = DEFAULT_SYMBOL_COSTS[symbol]
    assert costs.swap_long_per_lot == pytest.approx(long)
    assert costs.swap_short_per_lot == pytest.approx(short)
    assert costs.swap_triple_weekday == triple


@pytest.mark.parametrize("symbol", ["NAS100", "US500"])
def test_indices_have_no_commission_so_break_even_is_the_spread(symbol):
    config = CostConfig()
    assert config.commission_r(symbol, risk=20.0) == 0
    assert config.break_even_offset(symbol) == DEFAULT_SYMBOL_COSTS[symbol].spread
