"""Fixed spread scaled with the price level (rule set by the user, 2026-10-16).
Spec: risk-management.md › Costs › Spread scaled with the price level.

    spread used = SymbolCosts.spread x (fill price / SymbolCosts.reference_price)
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backtester.engine.costs import (
    DEFAULT_SYMBOL_COSTS,
    CostConfig,
    SymbolCosts,
)
from backtester.engine.spread_table import SpreadTable

AT = datetime(2015, 6, 1, 14, 0, tzinfo=UTC)
SILVER = DEFAULT_SYMBOL_COSTS["XAGUSD"]


def test_every_default_symbol_with_a_spread_has_a_reference_price():
    # Binance symbols have no spread; the rest are measured in FTMO data
    for name, costs in DEFAULT_SYMBOL_COSTS.items():
        if costs.spread > 0:
            assert costs.reference_price and costs.reference_price > 0, name


def test_half_the_reference_price_pays_half_the_spread():
    cfg = CostConfig(spread_table=None)
    ref = SILVER.reference_price
    assert cfg.spread("XAGUSD", AT, price=ref / 2) == pytest.approx(SILVER.spread / 2)


def test_at_the_reference_price_the_old_spread_exactly():
    cfg = CostConfig(spread_table=None)
    assert cfg.spread("XAGUSD", AT, price=SILVER.reference_price) == pytest.approx(SILVER.spread)


def test_switch_off_gives_the_old_values_exactly():
    cfg = CostConfig(spread_price_scaling=False, spread_table=None)
    assert cfg.spread("XAGUSD", AT, price=15.0) == SILVER.spread
    assert cfg.spread_r("XAGUSD", 0.5, AT, price=15.0) == SILVER.spread / 0.5


def test_default_is_on():
    assert CostConfig().spread_price_scaling is True


def test_no_price_given_means_no_scaling():
    assert CostConfig(spread_table=None).spread("XAGUSD", AT) == SILVER.spread
    assert CostConfig(spread_table=None).spread("XAGUSD", AT, price=0.0) == SILVER.spread


def test_symbol_without_reference_price_is_not_scaled():
    cfg = CostConfig(
        symbols={"ZZZ": SymbolCosts(spread=0.3, commission_per_lot=0, contract_size=1)}
    )
    assert cfg.for_symbol("ZZZ").reference_price is None
    assert cfg.spread("ZZZ", AT, price=1234.0) == 0.3


def test_spread_off_stays_zero():
    assert CostConfig(spread_enabled=False).spread("XAGUSD", AT, price=15.0) == 0.0


def test_spread_table_is_not_scaled():
    class Table(SpreadTable):
        def __init__(self):
            pass

        def spread_at(self, symbol, at):
            return 0.07

    cfg = CostConfig(spread_table=Table())
    assert cfg.spread("XAGUSD", AT, price=15.0) == 0.07


def test_spread_table_without_value_falls_back_to_scaled_fixed():
    class Empty(SpreadTable):
        def __init__(self):
            pass

        def spread_at(self, symbol, at):
            return None

    cfg = CostConfig(spread_table=Empty())
    assert cfg.spread("XAGUSD", AT, price=SILVER.reference_price / 2) == pytest.approx(
        SILVER.spread / 2
    )


def test_spread_r_uses_the_scaled_spread():
    cfg = CostConfig(spread_table=None)
    price = SILVER.reference_price / 4
    assert cfg.spread_r("XAGUSD", 0.1, AT, price=price) == pytest.approx(SILVER.spread / 4 / 0.1)


def test_break_even_offset_uses_the_scaled_spread():
    cfg = CostConfig(commission_enabled=False, spread_table=None)
    price = SILVER.reference_price / 2
    assert cfg.break_even_offset("XAGUSD", AT, price) == pytest.approx(
        (SILVER.spread + 2 * SILVER.slippage) / 2
    )


def test_cost_filter_uses_the_scaled_spread():
    # at the reference price the spread costs 0.049 / 0.1 = 0.49 R: filtered at 0.3 R;
    # at a quarter of it 0.1225 R: filled
    cfg = CostConfig(max_cost_r=0.3, commission_enabled=False, spread_table=None)
    ref = SILVER.reference_price
    assert cfg.too_expensive("XAGUSD", 0.1, AT, entry=ref)
    assert not cfg.too_expensive("XAGUSD", 0.1, AT, entry=ref / 4)
    old = CostConfig(
        max_cost_r=0.3, commission_enabled=False, spread_price_scaling=False, spread_table=None
    )
    assert old.too_expensive("XAGUSD", 0.1, AT, entry=ref / 4)


def test_gbpusd_at_reference_price_is_unchanged():
    gbp = DEFAULT_SYMBOL_COSTS["GBPUSD"]
    cfg = CostConfig(spread_table=None)
    assert cfg.spread("GBPUSD", AT, price=gbp.reference_price) == pytest.approx(gbp.spread)
    assert cfg.spread("GBPUSD", AT) == gbp.spread
