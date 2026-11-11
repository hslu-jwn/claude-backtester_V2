"""Per-symbol cost defaults. Spec: risk-management.md › Costs."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backtester.core.models import Direction
from backtester.engine.costs import DEFAULT_SYMBOL_COSTS, CostConfig, SymbolCosts


@pytest.mark.parametrize("direction, expected", [(Direction.BULLISH, -0.3), (Direction.BEARISH, 0.15)])
@pytest.mark.parametrize("entry, multiplier", [(50.0, 0.5), (100.0, 1.0), (200.0, 2.0)])
def test_per_lot_swap_scales_with_entry_price(direction, expected, entry, multiplier):
    # Three nights: -12 USD (long) / +6 USD (short), divided by 2 * 20 USD risk; the credit
    # needs swap_credit (off by default since review B5, 2026-11-11).
    config = CostConfig(swap_credit=True, symbols={"TEST": SymbolCosts(
        0, 0, 20, swap_long_per_lot=-4, swap_short_per_lot=2, reference_price=100,
    )})
    assert config.swap_r_nights("TEST", direction, 2, 3, entry) == pytest.approx(expected * multiplier)


def test_swap_price_scaling_can_be_disabled_independently_of_spread():
    config = CostConfig(swap_price_scaling=False, symbols={"TEST": SymbolCosts(
        0, 0, 20, swap_long_per_lot=-4, reference_price=100,
    )})
    assert config.swap_r_nights("TEST", Direction.BULLISH, 2, 3, 50) == pytest.approx(-0.3)


@pytest.mark.parametrize("reference, entry", [(None, 50.0), (100.0, 0.0), (100.0, -1.0)])
def test_per_lot_swap_without_reference_or_positive_entry_is_unchanged(reference, entry):
    config = CostConfig(symbols={"TEST": SymbolCosts(
        0, 0, 20, swap_long_per_lot=-4, reference_price=reference,
    )})
    assert config.swap_r_nights("TEST", Direction.BULLISH, 2, 3, entry) == pytest.approx(-0.3)


@pytest.mark.parametrize("scaling", [False, True])
@pytest.mark.parametrize("rate, fixed_r", [(0, 0), (-4, -0.3)])
def test_percentage_swap_is_not_price_scaled_again(scaling, rate, fixed_r):
    config = CostConfig(swap_price_scaling=scaling, symbols={"TEST": SymbolCosts(
        0, 0, 20, swap_long_per_lot=rate, swap_long_pct_year=-0.365, reference_price=100,
    )})
    # Percentage component: 3 * -0.365 / 365 * 50 / 2 = -0.075 R, with either switch value.
    expected = fixed_r * (0.5 if scaling else 1) - 0.075
    assert config.swap_r_nights("TEST", Direction.BULLISH, 2, 3, 50) == pytest.approx(expected)


def test_swap_r_scales_share_weighted_triple_nights_using_entry():
    config = CostConfig(spread_price_scaling=False, symbols={"TEST": SymbolCosts(
        0, 0, 20, swap_long_per_lot=-4, reference_price=100,
    )})
    entry_time = datetime(2026, 1, 7, 20, tzinfo=UTC)  # Wednesday, triple rollover at 22 UTC
    exits = [(0.5, datetime(2026, 1, 7, 21, tzinfo=UTC)),
             (0.5, datetime(2026, 1, 7, 22, tzinfo=UTC))]
    assert config.swap_r("TEST", Direction.BULLISH, 2, entry_time, exits, 50) == pytest.approx(-0.075)


@pytest.mark.parametrize(
    ("symbol", "spread", "slippage"),
    [
        ("NAS100", 1.9, 1.0),
        ("US500", 0.61, 0.25),
        ("XAUUSD", 0.41, 0.10),
        ("GBPUSD", 0.000059, 0.00002),  # 0.2 pip
        ("GBPJPY", 0.023, 0.003),  # 0.3 pip
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
def test_indices_break_even_is_spread_plus_two_slips_without_commission(symbol):
    config = CostConfig()
    assert config.commission_r(symbol, risk=20.0) == 0
    costs = DEFAULT_SYMBOL_COSTS[symbol]
    assert config.break_even_offset(symbol) == costs.spread + 2 * costs.slippage


# --- ROADMAP 11.8 / 11.9: FTMO costs of the new symbols (read from the terminal 2026-10-15) ----

NEW_FTMO = [  # symbol, spread, swap long, swap short, triple weekday (0 = Monday)
    ("EURUSD", 0.00002, -8.53, 0.21, 2),
    ("USDJPY", 0.0043, 1.0813, -11.0347, 2),
    ("XAGUSD", 0.049, -68.05, 0.30, 2),
    ("GER40", 2.3, -5.0571, -0.0511, 4),
    ("JP225", 11.0, -0.5683, -0.1894, 4),
    ("USOIL", 0.080, 4.966, -22.54, 4),
    ("US30", 2.5, -11.7596, 0.5936, 4),
    ("NATGAS", 0.06, -5.84, 1.27, 4),
]


@pytest.mark.parametrize(("symbol", "spread", "long", "short", "triple"), NEW_FTMO)
def test_new_ftmo_symbols_spread_and_swap(symbol, spread, long, short, triple):
    costs = DEFAULT_SYMBOL_COSTS[symbol]
    assert costs.spread == pytest.approx(spread)
    assert costs.swap_long_per_lot == pytest.approx(long, abs=1e-4)
    assert costs.swap_short_per_lot == pytest.approx(short, abs=1e-4)
    assert costs.swap_triple_weekday == triple


def test_quote_currency_conversion_and_contract_sizes():
    assert DEFAULT_SYMBOL_COSTS["USDJPY"].quote_to_usd == pytest.approx(0.00632, rel=1e-3)
    assert DEFAULT_SYMBOL_COSTS["GER40"].quote_to_usd == pytest.approx(1.1211, rel=1e-3)
    assert DEFAULT_SYMBOL_COSTS["JP225"].contract_size == 10
    assert DEFAULT_SYMBOL_COSTS["XAGUSD"].contract_size == 5000
    assert DEFAULT_SYMBOL_COSTS["EURUSD"].contract_size == 100_000


def test_commission_of_the_new_symbols():
    assert DEFAULT_SYMBOL_COSTS["EURUSD"].commission_per_lot == 5.0
    for symbol in ("GER40", "US30", "USOIL", "DXY", "NATGAS"):
        assert DEFAULT_SYMBOL_COSTS[symbol].commission_per_lot == 0.0


def test_binance_costs_are_percentage_fees_and_funding():
    # details in test_percentage_costs.py (0.05 % taker per side of the notional, funding)
    for symbol in ("BTCUSDT", "ETHUSDT"):
        costs = DEFAULT_SYMBOL_COSTS[symbol]
        assert costs.spread == 0.0 and costs.contract_size == 1 and costs.funding
        assert costs.commission_pct_per_side == pytest.approx(0.0005)


def test_existing_five_symbols_are_unchanged():
    assert DEFAULT_SYMBOL_COSTS["XAUUSD"].swap_long_per_lot == -61.27
    assert DEFAULT_SYMBOL_COSTS["GBPJPY"].quote_to_usd == pytest.approx(1 / 150.0)
    assert DEFAULT_SYMBOL_COSTS["NAS100"].spread == 1.9



# --- review B9 (the user, 2026-11-11): USD-base pairs convert the fixed commission at the price --


@pytest.mark.parametrize("symbol, price", [("USDCHF", 0.95), ("USDJPY", 110.0), ("USDCAD", 1.30)])
def test_usd_base_commission_uses_one_over_the_price(symbol, price):
    cfg = CostConfig()
    per_lot = cfg.for_symbol(symbol).commission_per_lot
    expected = per_lot * price / 100_000  # a lot is 100,000 USD: USD -> quote units at the price
    assert cfg.commission_price(symbol, price) == pytest.approx(expected)
    assert cfg.commission_r(symbol, 2 * expected, entry=price) == pytest.approx(0.5)


def test_non_usd_base_commission_keeps_the_fixed_rate():
    cfg = CostConfig()
    k = cfg.for_symbol("GBPUSD")
    assert cfg.commission_price("GBPUSD", 1.25) == pytest.approx(k.commission_per_lot / 100_000)
