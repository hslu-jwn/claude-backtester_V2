"""FTMO currency conversion adjustment (rule set by the user, 2026-10-27;
docs/review/ftmo-fees-2026-10-27.md): 0.7 % of the realised profit or loss of a trade whose
profit currency differs from the account currency (USD). In R:

    conversion_R = - adjustment x sum(share x |gross R of the part|)     (inside r_net)
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from conftest import build_series

from backtester.analytics.records import TradeRecord
from backtester.core.models import Direction, Timeframe
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import (
    DEFAULT_SYMBOL_COSTS,
    FTMO_PCT_COMMISSION_SIDE,
    CostConfig,
    SymbolCosts,
)
from backtester.runner import TRADE_COLUMNS
from backtester.strategy.base import Order, Strategy
from backtester.ui.pages.results import cost_totals

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
M5 = timedelta(minutes=5)


def sym(currency="JPY", **kw) -> SymbolCosts:
    return SymbolCosts(
        spread=0.0, commission_per_lot=0.0, contract_size=100, profit_currency=currency, **kw
    )


def config(currency="JPY", **kw) -> CostConfig:
    return CostConfig(spread_enabled=False, symbols={"TEST": sym(currency)}, **kw)


class Scripted(Strategy):
    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)

    def __init__(self, direction, tp=None, tp2=None, share=1.0):
        self.direction, self.tp, self.tp2, self.share = direction, tp, tp2, share

    def on_candle(self, now, views):
        base = views[Timeframe.M5]
        if base.cursor != 0:
            return []
        sl = 98.0 if self.direction is LONG else 102.0
        return [
            Order(
                self.direction, base.current.close, sl, self.tp,
                take_profit_2=self.tp2, tp1_share=self.share,
            )
        ]  # fmt: skip


def run(candles, cost, direction=LONG, **kw):
    series = build_series(candles)
    [t] = run_backtest(
        Scripted(direction, **kw),
        [series],
        EngineConfig(costs=cost, break_even_at_next_session=False),
    )
    return t


FLAT = (100.0, 100.1, 99.9, 100.0)  # entry 100, SL 98 (risk 2)
WIN = (100.0, 103.1, 99.9, 103.0)  # TP 103 reached: +1.5 R
LOSS = (100.0, 100.1, 97.9, 98.0)  # stop 98 hit: -1 R


# --- config -----------------------------------------------------------------------------


def test_defaults_are_on_at_0_7_percent_in_usd():
    c = CostConfig()
    assert c.conversion_adjustment == 0.007 and c.account_currency == "USD"


@pytest.mark.parametrize("bad", [-0.001, 1.0, 1.5, float("nan"), float("inf")])
def test_adjustment_is_validated(bad):
    with pytest.raises(ValueError, match="conversion_adjustment"):
        CostConfig(conversion_adjustment=bad)


def test_adjustment_zero_is_allowed():
    assert CostConfig(conversion_adjustment=0).conversion_adjustment == 0


# --- per-symbol profit currency ---------------------------------------------------------


@pytest.mark.parametrize(
    ("symbol", "currency"),
    [
        ("USDJPY", "JPY"), ("EURGBP", "GBP"), ("EURAUD", "AUD"), ("GBPJPY", "JPY"),
        ("USDCAD", "CAD"), ("USDCHF", "CHF"), ("AUDJPY", "JPY"), ("CHFJPY", "JPY"),
        ("GER40", "EUR"), ("EU50", "EUR"), ("UK100", "GBP"), ("JP225", "JPY"),
        ("AUS200", "AUD"), ("HK50", "HKD"),
        ("EURUSD", "USD"), ("GBPUSD", "USD"), ("AUDUSD", "USD"), ("NZDUSD", "USD"),
        ("XAUUSD", "USD"), ("XAGUSD", "USD"), ("NAS100", "USD"), ("US500", "USD"),
        ("US30", "USD"), ("US2000", "USD"), ("USOIL", "USD"), ("UKOIL", "USD"),
        ("NATGAS", "USD"), ("DXY", "USD"), ("BTCUSD", "USD"), ("ETHUSD", "USD"),
        ("BTCUSDT", "USD"), ("ETHUSDT", "USD"),
    ],
)  # fmt: skip
def test_default_profit_currency(symbol, currency):
    assert DEFAULT_SYMBOL_COSTS[symbol].profit_currency == currency


def test_every_default_symbol_has_a_currency_and_the_default_is_usd():
    assert SymbolCosts(0.0, 0.0, 1).profit_currency == "USD"
    assert all(c.profit_currency for c in DEFAULT_SYMBOL_COSTS.values())


def test_natgas_and_dxy_commission_is_the_ftmo_percentage():
    assert FTMO_PCT_COMMISSION_SIDE == pytest.approx(0.000007)
    for symbol in ("NATGAS", "DXY"):
        assert DEFAULT_SYMBOL_COSTS[symbol].commission_pct_per_side == FTMO_PCT_COMMISSION_SIDE
        assert DEFAULT_SYMBOL_COSTS[symbol].commission_per_lot == 0.0
    # metals and crypto unchanged, indices / oil stay free
    assert DEFAULT_SYMBOL_COSTS["XAUUSD"].commission_pct_per_side == pytest.approx(0.000007)
    assert DEFAULT_SYMBOL_COSTS["BTCUSD"].commission_pct_per_side == pytest.approx(0.000325)
    for symbol in ("USOIL", "UKOIL", "NAS100", "GER40", "HK50"):
        assert DEFAULT_SYMBOL_COSTS[symbol].commission_pct_per_side == 0.0


# --- conversion_r -----------------------------------------------------------------------


def test_conversion_r_is_a_cost_on_profit_and_on_loss():
    c = config()
    assert c.conversion_r("TEST", [(1.0, 1.5)]) == pytest.approx(-0.007 * 1.5)
    assert c.conversion_r("TEST", [(1.0, -1.0)]) == pytest.approx(-0.007 * 1.0)


def test_conversion_r_sums_the_parts_by_share():
    c = config()
    got = c.conversion_r("TEST", [(0.5, 1.2), (0.5, -0.4)])
    assert got == pytest.approx(-0.007 * (0.5 * 1.2 + 0.5 * 0.4))  # not |0.5*1.2 - 0.5*0.4|


def test_usd_symbol_and_zero_adjustment_and_unknown_symbol_pay_nothing():
    assert config("USD").conversion_r("TEST", [(1.0, 1.5)]) == 0.0
    assert config(conversion_adjustment=0).conversion_r("TEST", [(1.0, 1.5)]) == 0.0
    assert config().conversion_r("OTHER", [(1.0, 1.5)]) == 0.0


def test_a_different_account_currency_flips_which_symbols_pay():
    c = config("USD", account_currency="EUR")
    assert c.conversion_r("TEST", [(1.0, 1.0)]) == pytest.approx(-0.007)
    assert config("EUR", account_currency="EUR").conversion_r("TEST", [(1.0, 1.0)]) == 0.0


def test_zero_gross_pays_nothing():
    assert config().conversion_r("TEST", [(1.0, 0.0)]) == 0.0


# --- in a backtest ----------------------------------------------------------------------


def test_win_in_a_backtest_lowers_net_by_0_7_percent_of_gross():
    t = run([FLAT, WIN], config(), tp=103.0)
    assert t.r_gross == pytest.approx(1.5)
    assert t.conversion_r == pytest.approx(-0.0105)
    assert t.r_net == pytest.approx(1.5 - 0.0105)


def test_loss_in_a_backtest_is_increased_by_0_7_percent():
    t = run([FLAT, LOSS], config(), tp=110.0)
    assert t.r_gross == pytest.approx(-1.0)
    assert t.conversion_r == pytest.approx(-0.007)
    assert t.r_net == pytest.approx(-1.0 - 0.007)


def test_short_trade_uses_the_absolute_gross():
    t = run([FLAT, (100.0, 100.1, 96.9, 97.0)], config(), SHORT, tp=97.0)
    assert t.r_gross == pytest.approx(1.5)
    assert t.conversion_r == pytest.approx(-0.0105)


def test_usd_symbol_is_unaffected_and_zero_reproduces_old_numbers():
    base = run([FLAT, WIN], config("USD"), tp=103.0)
    off = run([FLAT, WIN], config(conversion_adjustment=0), tp=103.0)
    assert base.conversion_r == 0.0 and off.conversion_r == 0.0
    assert base.r_net == off.r_net == pytest.approx(1.5)


def test_conversion_is_charged_on_top_of_the_other_costs():
    cost = CostConfig(
        spread_enabled=False,
        symbols={"TEST": sym(commission_pct_per_side=0.0005)},
    )
    t = run([FLAT, WIN], cost, tp=103.0)
    assert t.commission_r > 0
    assert t.r_net == pytest.approx(1.5 - t.commission_r - 0.0105)


def test_partial_closes_sum_to_the_whole():
    # TP1 102.4 (1.2 R) closes half, the rest runs to TP2 104 (2 R): gross 0.5*1.2 + 0.5*2
    candles = [FLAT, (100.2, 102.5, 100.1, 102.2), (102.2, 104.1, 101.0, 103.9)]
    t = run(candles, config(), tp=102.4, tp2=104.0, share=0.5)
    assert t.r_gross == pytest.approx(1.6)
    assert t.conversion_r == pytest.approx(-0.007 * (0.5 * 1.2 + 0.5 * 2.0))
    assert t.r_net == pytest.approx(1.6 - 0.007 * 1.6)


# --- trades CSV and records -------------------------------------------------------------

ROW = {
    "id": "1", "symbol": "X", "direction": "long", "entry_time": "2026-01-05T12:00:00+00:00",
    "entry_candle": "2026-01-05T11:55:00+00:00", "entry": "1", "initial_stop": "0.9",
    "exit_time": "2026-01-05T13:00:00+00:00", "exit_price": "1.1", "exit_reason": "take_profit",
    "r_gross": "1", "r_net": "0.9", "spread_r": "0", "commission_r": "0",
}  # fmt: skip


def test_conversion_r_column_follows_funding_r_and_round_trips():
    assert TRADE_COLUMNS.index("conversion_r") == TRADE_COLUMNS.index("funding_r") + 1
    assert TradeRecord.from_row({**ROW, "conversion_r": "-0.0105"}).conversion_r == -0.0105


def test_old_csv_without_the_column_loads_as_zero():
    assert TradeRecord.from_row(ROW).conversion_r == 0.0
    assert TradeRecord.from_row({**ROW, "conversion_r": ""}).conversion_r == 0.0


def test_cost_totals_include_conversion_signed_like_net_r():
    a = TradeRecord.from_row({**ROW, "conversion_r": "-0.01"})
    b = TradeRecord.from_row({**ROW, "conversion_r": "-0.02"})
    assert cost_totals([a, b])["conversion"] == pytest.approx(-0.03)
