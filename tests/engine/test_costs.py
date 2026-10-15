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


# --- ROADMAP 11.8 / 11.9: FTMO costs of the new symbols (read from the terminal 2026-10-15) ----

NEW_FTMO = [  # symbol, spread, swap long, swap short, triple weekday (0 = Monday)
    ("EURUSD", 0.00002, -8.53, 0.21, 2),
    ("USDJPY", 0.003, 1.0813, -11.0347, 2),
    ("XAGUSD", 0.049, -68.05, 0.30, 2),
    ("GER40", 1.53, -5.0571, -0.0511, 4),
    ("JP225", 10.0, -0.5683, -0.1894, 4),
    ("USOIL", 0.075, 4.966, -22.54, 4),
    ("US30", 2.28, -11.7596, 0.5936, 4),
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
    assert DEFAULT_SYMBOL_COSTS["NAS100"].spread == 1.0
