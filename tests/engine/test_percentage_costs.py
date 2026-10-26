"""Percentage commission, percentage swap and Binance funding in R (rule set by the user,
2026-10-15; risk-management.md > Costs). Lots and contract size cancel:

    commission_R = pct x (entry + sum(share x exit fill)) / SL distance
    swap_R       = nights x pct_year / 365 x entry / SL distance
    funding_R    = - sign x sum(share x rates while open) x entry / SL distance
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from conftest import build_series

import backtester.engine.costs as costs_module
from backtester.analytics.records import TradeRecord
from backtester.core.models import Direction, Timeframe
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import (
    DEFAULT_SYMBOL_COSTS,
    CostConfig,
    FundingSeries,
    SymbolCosts,
    funding_from_rows,
)
from backtester.runner import TRADE_COLUMNS
from backtester.strategy.base import Order, Strategy
from backtester.ui.pages.results import cost_totals

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
M5 = timedelta(minutes=5)
FLAT = (100.0, 100.1, 99.9, 100.0)  # entry 100, SL 98 (risk 2), never hit


def utc(*args) -> datetime:
    return datetime(*args, tzinfo=UTC)


def sym(**kw) -> SymbolCosts:
    return SymbolCosts(spread=0.0, commission_per_lot=0.0, contract_size=100, **kw)


def config(symbol: SymbolCosts, **kw) -> CostConfig:
    return CostConfig(spread_enabled=False, symbols={"TEST": symbol}, **kw)


class Scripted(Strategy):
    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)

    def __init__(self, direction):
        self.direction = direction

    def on_candle(self, now, views):
        base = views[Timeframe.M5]
        if base.cursor != 0:
            return []
        sl = 98.0 if self.direction is LONG else 102.0
        return [Order(self.direction, base.current.close, sl, None)]


def run(start, n, cost, direction=LONG):
    """One trade entered at the close of the first candle (start + 5 min), held to the end."""
    series = build_series([FLAT] * n, start=start)
    [t] = run_backtest(Scripted(direction), [series], EngineConfig(costs=cost))
    return t


# --- percentage commission --------------------------------------------------------------


def test_percentage_commission_is_pct_of_entry_plus_exit_notional_in_r():
    c = config(sym(commission_pct_per_side=0.0005))
    assert c.commission_r("TEST", 2.0, 100.0, [(1.0, 100.0)]) == pytest.approx(0.0005 * 200 / 2)
    # the same trade at twice the price costs twice as much R (same SL distance)
    assert c.commission_r("TEST", 2.0, 200.0, [(1.0, 200.0)]) == pytest.approx(0.0005 * 400 / 2)


def test_percentage_commission_uses_each_part_at_its_own_exit_fill():
    c = config(sym(commission_pct_per_side=0.0005))
    got = c.commission_r("TEST", 4.0, 100.0, [(0.5, 110.0), (0.5, 120.0)])
    assert got == pytest.approx(0.0005 * (100 + 115) / 4)


def test_percentage_commission_without_exits_assumes_the_exit_at_the_entry():
    c = config(sym(commission_pct_per_side=0.0005))
    assert c.commission_r("TEST", 2.0, 100.0) == pytest.approx(0.05)
    assert c.commission_price("TEST", 100.0) == pytest.approx(0.1)  # round turn in price units
    assert c.break_even_offset("TEST", None, 100.0) == pytest.approx(0.1 / (1 - 0.0005))


def test_percentage_commission_needs_a_price_and_can_be_switched_off():
    c = config(sym(commission_pct_per_side=0.0005))
    with pytest.raises(ValueError, match="entry price"):
        c.commission_r("TEST", 2.0)
    assert replace(c, commission_enabled=False).commission_r("TEST", 2.0) == 0.0


def test_fixed_and_percentage_commission_add_up():
    c = CostConfig(symbols={"T": SymbolCosts(0.0, 4.0, 100, commission_pct_per_side=0.0005)})
    assert c.commission_r("T", 2.0, 100.0, [(1.0, 100.0)]) == pytest.approx(4 / 200 + 0.05)


def test_cost_filter_sees_the_percentage_commission():
    c = config(sym(commission_pct_per_side=0.0005), max_cost_r=0.04)
    assert c.too_expensive("TEST", 2.0, None, 100.0)  # 0.05 R > 0.04
    assert not c.too_expensive("TEST", 2.0, None, 50.0)  # 0.025 R


# --- percentage swap --------------------------------------------------------------------


def test_percentage_swap_per_night_long_and_short():
    # 0.365 per year = 0.001 per night of the notional 100 -> 0.1 per unit, SL distance 2
    cost = config(sym(swap_long_pct_year=-0.365, swap_short_pct_year=0.365))
    start = utc(2026, 1, 5, 20, 0)  # Monday: the 22:00 UTC rollover is one night
    assert run(start, 36, cost, LONG).swap_r == pytest.approx(-0.05)
    assert run(start, 36, cost, SHORT).swap_r == pytest.approx(0.05)
    assert run(start, 12, cost, LONG).swap_r == 0  # closes before the rollover


def test_percentage_swap_counts_three_nights_on_the_triple_weekday():
    cost = config(sym(swap_long_pct_year=-0.365))
    wednesday = utc(2026, 1, 7, 20, 0)
    t = run(wednesday, 36, cost)
    assert t.swap_r == pytest.approx(-0.15)
    assert t.r_net == pytest.approx(t.r_gross - 0.15)


def test_percentage_swap_adds_to_the_dollar_swap():
    cost = config(sym(swap_long_per_lot=-10.0, swap_long_pct_year=-0.365))
    t = run(utc(2026, 1, 5, 20, 0), 36, cost)
    assert t.swap_r == pytest.approx(-10.0 / 200 - 0.05)


# --- funding ----------------------------------------------------------------------------

FUNDING = funding_from_rows(
    [
        (utc(2026, 1, 5, 8), 0.0001),
        (utc(2026, 1, 5, 16), 0.0002),
        (utc(2026, 1, 6, 0), -0.0004),
    ]
)


def funding_config(**kw) -> CostConfig:
    return config(sym(funding=True), funding={"TEST": FUNDING}, **kw)


def test_funding_series_counts_timestamps_after_entry_up_to_and_including_exit():
    assert FUNDING.rate_sum(utc(2026, 1, 5, 8), utc(2026, 1, 5, 16)) == pytest.approx(0.0002)
    assert FUNDING.rate_sum(utc(2026, 1, 5, 7, 59), utc(2026, 1, 5, 8)) == pytest.approx(0.0001)
    assert FUNDING.rate_sum(utc(2026, 1, 5, 8, 1), utc(2026, 1, 5, 15, 59)) == 0.0
    assert FUNDING.rate_sum(utc(2026, 1, 5, 0), utc(2026, 1, 6, 0)) == pytest.approx(-0.0001)
    assert FundingSeries((), ()).rate_sum(utc(2026, 1, 1), utc(2026, 1, 9)) == 0.0


def test_funding_sign_longs_pay_positive_rates_shorts_receive():
    c = funding_config()
    exits = [(1.0, utc(2026, 1, 5, 17))]  # only the 16:00 timestamp (0.0002) is inside
    entry_time = utc(2026, 1, 5, 12)
    # notional 100, SL distance 2: 0.0002 x 100 / 2 = 0.01 R
    assert c.funding_r("TEST", LONG, 2.0, entry_time, exits, 100.0) == pytest.approx(-0.01)
    assert c.funding_r("TEST", SHORT, 2.0, entry_time, exits, 100.0) == pytest.approx(0.01)


def test_negative_rate_means_longs_receive_and_shorts_pay():
    c = funding_config()
    exits = [(1.0, utc(2026, 1, 6, 1))]
    got = c.funding_r("TEST", LONG, 2.0, utc(2026, 1, 5, 17), exits, 100.0)
    assert got == pytest.approx(0.0004 * 100 / 2)


def test_each_part_pays_the_timestamps_up_to_its_own_exit():
    c = funding_config()
    exits = [(0.5, utc(2026, 1, 5, 12)), (0.5, utc(2026, 1, 5, 17))]
    got = c.funding_r("TEST", LONG, 2.0, utc(2026, 1, 5, 7), exits, 100.0)
    # first part: 08:00 (0.0001); second part: 08:00 + 16:00 (0.0003)
    assert got == pytest.approx(-(0.5 * 0.0001 + 0.5 * 0.0003) * 100 / 2)


def test_funding_only_for_symbols_with_funding_and_can_be_switched_off():
    exits = [(1.0, utc(2026, 1, 5, 17))]
    no_flag = config(sym(), funding={"TEST": FUNDING})
    assert no_flag.funding_r("TEST", LONG, 2.0, utc(2026, 1, 5, 12), exits, 100.0) == 0.0
    off = funding_config(funding_enabled=False)
    assert off.funding_r("TEST", LONG, 2.0, utc(2026, 1, 5, 12), exits, 100.0) == 0.0
    assert funding_config().funding_r("OTHER", LONG, 2.0, utc(2026, 1, 5, 12), exits, 100.0) == 0.0


def test_funding_in_a_backtest_enters_net_r_and_the_trade():
    # entry at 12:05, held 5 h -> exit 17:05 (end of data): the 16:00 timestamp is inside
    t = run(utc(2026, 1, 5, 12, 0), 60, funding_config())
    assert t.funding_r == pytest.approx(-0.01)
    assert t.r_net == pytest.approx(t.r_gross - 0.01)
    short = run(utc(2026, 1, 5, 12, 0), 60, funding_config(), SHORT)
    assert short.funding_r == pytest.approx(0.01)


def test_a_funding_timestamp_exactly_at_the_entry_is_not_paid():
    # entry at 15:55 + 5 min = 16:00 -> the 16:00 timestamp is not inside
    t = run(utc(2026, 1, 5, 15, 55), 12, funding_config())
    assert t.funding_r == 0.0


def test_funding_is_read_from_the_cache_file_and_a_missing_file_is_named(tmp_path, monkeypatch):
    monkeypatch.setattr(costs_module, "FUNDING_DIR", tmp_path)
    costs_module.load_funding.cache_clear()
    c = config(sym(funding=True))
    with pytest.raises(FileNotFoundError, match="TEST"):
        c.funding_series("TEST")
    (tmp_path / "TEST.csv").write_text(
        "calc_time,funding_interval_hours,last_funding_rate\n"
        "2026-01-05 16:00:00,8,0.0002\n2026-01-05 08:00:00,8,0.0001\n",
        encoding="utf-8",
    )
    series = c.funding_series("TEST")
    assert series.rate_sum(utc(2026, 1, 5, 0), utc(2026, 1, 5, 23)) == pytest.approx(0.0003)
    costs_module.load_funding.cache_clear()


# --- the defaults -----------------------------------------------------------------------


def test_fixed_dollar_symbols_are_unchanged():
    c = CostConfig()
    # GBPUSD $5 / (0.002 x 100,000), GBPJPY $5 / (0.2 x 100,000 / 150): the old numbers
    assert c.commission_r("GBPUSD", 0.002, 1.25, [(1.0, 1.26)]) == pytest.approx(0.025)
    assert c.commission_r("GBPJPY", 0.2, 190.0, [(1.0, 191.0)]) == pytest.approx(0.0375)
    assert c.commission_r("NAS100", 50.0, 20000.0, [(1.0, 20050.0)]) == 0.0
    assert c.spread_r("NAS100", 50.0) == pytest.approx(0.02)
    for name in ("GBPUSD", "GBPJPY", "NAS100", "US500", "EURUSD", "GER40"):
        d = DEFAULT_SYMBOL_COSTS[name]
        assert d.commission_pct_per_side == d.swap_long_pct_year == d.swap_short_pct_year == 0.0
        assert not d.funding
    assert DEFAULT_SYMBOL_COSTS["GBPUSD"].commission_per_lot == 5.0
    assert DEFAULT_SYMBOL_COSTS["NAS100"].swap_long_per_lot == -6.912


def test_xauusd_and_xagusd_commission_is_ftmos_0_0014_percent_round_turn():
    c = CostConfig()
    for name in ("XAUUSD", "XAGUSD"):
        d = DEFAULT_SYMBOL_COSTS[name]
        assert d.commission_per_lot == 0.0  # was $6 per lot until 2026-10-15
        assert d.commission_pct_per_side == pytest.approx(0.000007)
    # XAUUSD entry 2000, exit 2005, SL 2.5: 0.000007 x 4005 / 2.5
    assert c.commission_r("XAUUSD", 2.5, 2000.0, [(1.0, 2005.0)]) == pytest.approx(0.011214)
    assert DEFAULT_SYMBOL_COSTS["XAUUSD"].swap_long_per_lot == -61.27  # swap unchanged


def test_ftmo_crypto_is_a_percentage_commission_and_a_percentage_swap():
    for name in ("BTCUSD", "ETHUSD"):
        d = DEFAULT_SYMBOL_COSTS[name]
        assert d.commission_pct_per_side == pytest.approx(0.000325)
        assert d.swap_long_pct_year == d.swap_short_pct_year == pytest.approx(-0.30)
        assert d.swap_long_per_lot == d.swap_short_per_lot == 0.0 and not d.funding
    c = CostConfig()
    # BTCUSD 100,000 -> 101,000, SL 1,000: 0.000325 x 201,000 / 1,000
    got = c.commission_r("BTCUSD", 1000.0, 100_000.0, [(1.0, 101_000.0)])
    assert got == pytest.approx(0.065325)
    # one night: 0.3 / 365 x 100,000 / 1,000
    swap = c.swap_r(
        "BTCUSD", LONG, 1000.0, utc(2026, 1, 5, 20), [(1.0, utc(2026, 1, 5, 23))], 100_000.0
    )
    assert swap == pytest.approx(-0.3 / 365 * 100)


def test_binance_symbols_pay_taker_fee_and_funding_without_spread():
    for name in ("BTCUSDT", "ETHUSDT"):
        d = DEFAULT_SYMBOL_COSTS[name]
        assert d.commission_pct_per_side == 0.0005 and d.commission_per_lot == 0.0
        assert d.spread == 0.0 and d.funding
        assert d.swap_long_per_lot == d.swap_short_per_lot == 0.0
        assert d.swap_long_pct_year == d.swap_short_pct_year == 0.0


# --- shown in the results ---------------------------------------------------------------

ROW = {
    "id": "1", "symbol": "X", "direction": "long", "entry_time": "2026-01-05T12:00:00+00:00",
    "entry_candle": "2026-01-05T11:55:00+00:00", "entry": "1", "initial_stop": "0.9",
    "exit_time": "2026-01-05T13:00:00+00:00", "exit_price": "1.1", "exit_reason": "take_profit",
    "r_gross": "1", "r_net": "0.9", "spread_r": "0", "commission_r": "0",
}  # fmt: skip


def test_funding_r_is_written_next_to_swap_r_and_read_back():
    assert TRADE_COLUMNS.index("funding_r") == TRADE_COLUMNS.index("swap_r") + 1
    assert TradeRecord.from_row({**ROW, "funding_r": "-0.012"}).funding_r == -0.012
    assert TradeRecord.from_row(ROW).funding_r == 0.0  # old result folder


def test_cost_totals_are_signed_by_their_effect_on_net_r():
    a = TradeRecord.from_row(
        {**ROW, "spread_r": "0.1", "commission_r": "0.02", "swap_r": "-0.03", "funding_r": "-0.01"}
    )
    b = TradeRecord.from_row(
        {**ROW, "spread_r": "0.2", "commission_r": "0.03", "swap_r": "0.05", "funding_r": "0.04"}
    )
    got = cost_totals([a, b])
    assert got == pytest.approx(
        {"spread": -0.3, "commission": -0.05, "swap": 0.02, "funding": 0.03}
    )
