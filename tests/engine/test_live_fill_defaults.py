"""Approved raises only, at reference price. Spec: risk-management.md > Costs.

Freeze every symbol, including sub-threshold proposals, rejected decreases, and symbols
absent from the proposal. The ignored proposal file is not needed to run these tests.
"""

import pytest

from backtester.engine.costs import DEFAULT_SYMBOL_COSTS, CostConfig


@pytest.mark.parametrize(
    ("symbol", "spread", "slippage", "reference_price"),
    [
        ('XAUUSD', 0.41, 0.1, 4342.74),
        ('GBPUSD', 5.9e-05, 2e-05, 1.348),
        ('GBPJPY', 0.023, 0.003, 209.75),
        ('NAS100', 1.9, 1.0, 29580.48),
        ('US500', 0.61, 0.25, 7696.45),
        ('EURUSD', 2e-05, 1e-05, 1.15405),
        ('AUDUSD', 3.2e-05, 1e-05, 0.71185),
        ('NZDUSD', 3e-05, 1.5e-05, 0.57601),
        ('EURGBP', 4e-05, 2e-05, 0.85688),
        ('USDJPY', 0.0043, 0.0015, 158.058),
        ('USDCAD', 5.1e-05, 1.5e-05, 1.39191),
        ('USDCHF', 5e-05, 2.5e-05, 0.81828),
        ('EURJPY', 0.011, 0.0045, 179.43),
        ('XAGUSD', 0.049, 0.0245, 64.58),
        ('GER40', 2.3, 0.765, 25563.64),
        ('UK100', 2.6, 0.725, 10720.5),
        ('JP225', 11.0, 5.0, 66072.5),
        ('EU50', 1.06, 0.53, 6316.47),
        ('USOIL', 0.08, 0.0375, 92.499),
        ('UKOIL', 0.073, 0.0345, 102.245),
        ('DXY', 0.018, 0.009, 99.673),
        ('US30', 2.5, 1.14, 52172.25),
        ('US2000', 0.93, 0.465, 2890.78),
        ('NATGAS', 0.06, 0.03, 2.876),
        ('AUDJPY', 0.009, 0.0045, 110.57),
        ('CADJPY', 0.007, 0.0035, 111.527),
        ('NZDJPY', 0.009, 0.0045, 89.395),
        ('CHFJPY', 0.015, 0.0075, 190.36),
        ('EURAUD', 9.5e-05, 3e-05, 1.61278),
        ('GBPAUD', 0.00011, 5.5e-05, 1.8914),
        ('AUS200', 1.0, 0.5, 8755.7),
        ('HK50', 6.24, 3.12, 24605.0),
        ('BTCUSD', 1.0, 2.5, 79679.87),
        ('ETHUSD', 0.66, 0.3, 2498.33),
        ('BTCUSDT', 0.0, 0.0, None),
        ('ETHUSDT', 0.0, 0.0, None),
    ],
)
def test_live_fill_defaults_2026_11_09(symbol, spread, slippage, reference_price):
    costs = DEFAULT_SYMBOL_COSTS[symbol]
    assert costs.spread == spread
    assert costs.slippage == slippage
    assert costs.reference_price == reference_price
    config = CostConfig(spread_table=None)
    assert config.spread(symbol, price=reference_price or 0.0) == pytest.approx(spread)
    assert config.slippage(symbol, reference_price or 0.0) == pytest.approx(slippage)
