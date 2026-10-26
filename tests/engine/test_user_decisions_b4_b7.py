"""Hand-built regressions for ARCHITECTURE.md: B4-B7 (user, 2026-10-22)."""

from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
from conftest import DEFAULT_START, build_candles, build_series

from backtester.analytics.entry_screen import (
    M1Data,
    ScreenTrade,
    exit_after_bars,
    exit_bracket,
    random_exit_runs,
)
from backtester.analytics.random_fills import RandomFillsConfig, market_fills, max_slippage_r
from backtester.analytics.records import TradeRecord
from backtester.core.models import Direction, Timeframe
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig, SymbolCosts
from backtester.engine.trade import ExitReason
from backtester.strategy.base import Order, Strategy

# touch fills (the rule before 2026-10-23): these tests check the cost arithmetic of a touch
TOUCH = {"tp_penetration": 0.0, "short_tp_on_ask": False}

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
ENTRY = (100.0, 100.0, 100.0, 100.0)
COSTS = SymbolCosts(0.2, 0.0, 1, slippage=0.1)


class Scripted(Strategy):
    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)
    uses_session_break_even = False

    def __init__(self, order, signal=False):
        self.order, self.signal, self.cursor = order, signal, -1

    def on_candle(self, now, views):
        self.cursor = views[Timeframe.M5].cursor
        return [self.order] if self.cursor == int(self.order.limit_fill) else []

    def pending_limit_orders(self):
        return [self.order] if self.order.limit_fill and self.cursor == 0 else []

    def exits(self):
        return ["entry"] if self.signal and self.cursor == 1 else []


def run(candles, sign=1, *, costs=COSTS, tp=None, tp2=None, limit=False, signal=False):
    order = Order(
        LONG if sign > 0 else SHORT,
        100.0,
        100.0 - sign * 2,
        tp,
        take_profit_2=tp2,
        tp1_share=0.5,
        break_even_after_tp1=True,
        limit_fill=limit,
        ref="entry",
    )
    config = EngineConfig(costs=CostConfig(**TOUCH, symbols={"TEST": costs}))
    return run_backtest(Scripted(order, signal), [build_series(candles)], config)[0]


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("signal", [False, True])
def test_b4_market_entry_and_close_exit_are_slipped_against_trader(sign, signal):
    t = run([ENTRY, ENTRY], sign, signal=signal)
    assert t.entry_fill == pytest.approx(100 + (0.2 if sign > 0 else 0) + sign * 0.1)
    assert t.exit_fill == pytest.approx(100 + (0.2 if sign < 0 else 0) - sign * 0.1)
    assert t.r_net == pytest.approx(-0.2)  # (spread .2 + two slips .1) / risk 2
    assert t.r_gross == 0


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("gap", [False, True])
def test_b4_stop_and_gap_stop_are_slipped_and_sl_wins_over_tp(sign, gap):
    opening = 100 - sign * 3 if gap else 100
    t = run([ENTRY, (opening, 110, 90, 100)], sign, tp=100 + sign * 4)
    chart_exit = opening if gap else 100 - sign * 2
    assert t.exit_reason is ExitReason.STOP_LOSS
    assert t.exit_price == chart_exit
    assert t.exit_fill == pytest.approx(chart_exit + (0.2 if sign < 0 else 0) - sign * 0.1)
    assert t.r_net == pytest.approx((-1.5 if gap else -1) - 0.2)


@pytest.mark.parametrize("sign", [1, -1])
def test_b4_tp_is_not_slipped(sign):
    target = 100 + sign * 4
    candle = (100, 105, 99, 104) if sign > 0 else (100, 101, 95, 96)
    t = run([ENTRY, candle], sign, tp=target)
    assert t.exit_reason is ExitReason.TAKE_PROFIT
    assert t.exit_fill == pytest.approx(target + (0.2 if sign < 0 else 0))
    assert t.r_net == pytest.approx(1.85)  # spread .2 + entry slip .1, no TP slip


@pytest.mark.parametrize("sign", [1, -1])
def test_b4_limit_entry_is_not_slipped_but_stop_is(sign):
    candle = (100, 101, 97, 99) if sign > 0 else (100, 103, 99, 101)
    t = run([ENTRY, candle], sign, limit=True)
    assert t.entry_fill == pytest.approx(100 + (0.2 if sign > 0 else 0))
    assert t.r_net == pytest.approx(-1.15)


@pytest.mark.parametrize("sign", [1, -1])
def test_b4_slippage_follows_entry_price_scaling_independently_of_spread_switch(sign):
    costs = replace(COSTS, spread=0, reference_price=200)
    t = run([ENTRY, ENTRY], sign, costs=costs)
    assert t.entry_fill == pytest.approx(100 + sign * 0.05)
    assert t.exit_fill == pytest.approx(100 - sign * 0.05)
    assert t.r_net == pytest.approx(-0.05)


@pytest.mark.parametrize(
    "reason", [ExitReason.SIGNAL, ExitReason.END_OF_DATA, "signal", "end_of_data"]
)
def test_b4_random_fills_include_market_exit_draw(reason):
    t = SimpleNamespace(entry=100, initial_stop=98, exit_reason=reason)
    assert max_slippage_r(t, 0.1) == pytest.approx([0.1, 0.1])
    t.parts = ({"share": 0.4, "reason": "take_profit"}, {"share": 0.6, "reason": reason})
    assert max_slippage_r(t, 0.1) == pytest.approx([0.1, 0.06])


def test_b4_random_fills_do_not_draw_for_engine_limit_entry():
    t = run([ENTRY, ENTRY], limit=True)
    assert max_slippage_r(t, 0.1) == pytest.approx([0.1])  # market exit only
    assert market_fills(t, RandomFillsConfig()) == 1


@pytest.mark.parametrize("encoded", [True, "True", "true"])
def test_b4_limit_entry_kind_survives_trade_csv_round_trip(encoded):
    from backtester.runner import trade_rows

    t = run([ENTRY, ENTRY], limit=True)
    result = SimpleNamespace(trades=[t], runs={"TEST": SimpleNamespace(sessions=[])})
    row = trade_rows(result)[0]
    assert row["limit_fill"] is True
    row["limit_fill"] = encoded
    record = TradeRecord.from_row(row)
    assert max_slippage_r(record, 0.1) == pytest.approx([0.1])


@pytest.mark.parametrize("encoded", [False, "False", "false", None])
def test_b4_market_or_legacy_csv_records_keep_entry_draw(encoded):
    from backtester.runner import trade_rows

    t = run([ENTRY, ENTRY])
    result = SimpleNamespace(trades=[t], runs={"TEST": SimpleNamespace(sessions=[])})
    row = trade_rows(result)[0]
    if encoded is None:
        row.pop("limit_fill", None)
    else:
        row["limit_fill"] = encoded
    assert max_slippage_r(TradeRecord.from_row(row), 0.1) == pytest.approx([0.1, 0.1])


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("distance", [0.2, 0.5])
def test_b5_be_at_or_beyond_tp1_keeps_original_stop(sign, distance):
    # Spread alone makes BE 100.5 / 99.5, including exact equality with TP1.
    costs = replace(COSTS, spread=0.5, slippage=0)
    target = 100 + sign * distance
    first = (100, 100.6, 99.9, 100.1) if sign > 0 else (100, 100.1, 99.4, 99.9)
    stop = (100, 101, 97, 99) if sign > 0 else (100, 103, 99, 101)
    t = run([ENTRY, first, stop], sign, costs=costs, tp=target, tp2=100 + sign * 4)
    assert t.break_even_time is None and t.break_even_stop is None
    assert [p.reason for p in t.parts] == [ExitReason.TAKE_PROFIT, ExitReason.STOP_LOSS]
    assert t.parts[-1].price == 100 - sign * 2


@pytest.mark.parametrize("sign", [1, -1])
def test_b6_percentage_commission_uses_entry_fill(sign):
    costs = replace(COSTS, commission_per_lot=0.04, commission_pct_per_side=0.001)
    t = run([ENTRY, ENTRY], sign, costs=costs)
    expected_entry = 100 + (0.2 if sign > 0 else 0) + sign * 0.1
    expected_exit = 100 + (0.2 if sign < 0 else 0) - sign * 0.1
    assert t.commission_r == pytest.approx((0.04 + 0.001 * (expected_entry + expected_exit)) / 2)


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("limit", [False, True])
def test_b6_be_remainder_nets_exactly_zero_with_percentage_and_fixed_commission(sign, limit):
    costs = replace(COSTS, commission_per_lot=0.04, commission_pct_per_side=0.001)
    first = (100, 103, 99.9, 102.5) if sign > 0 else (100, 100.1, 97, 97.5)
    second = (102, 103, 99, 100) if sign > 0 else (98, 101, 97, 100)
    candles = [ENTRY, *([ENTRY] if limit else []), first, second]
    t = run(candles, sign, costs=costs, tp=100 + sign * 2, tp2=100 + sign * 6, limit=limit)
    rest = t.parts[-1]
    assert rest.reason is ExitReason.BREAK_EVEN
    commission = (0.04 + 0.001 * (t.entry_fill + rest.fill)) / 2
    assert rest.r_fills - commission == pytest.approx(0, abs=1e-12)
    expected_fill = ((sign + 0.001) * t.entry_fill + 0.04) / (sign - 0.001)
    expected_stop = expected_fill - (0.2 if sign < 0 else 0) + sign * 0.1
    assert t.break_even_stop == pytest.approx(expected_stop)


@pytest.mark.parametrize("sign", [1, -1])
def test_b7_gap_stop_excursions_stop_at_open_and_ignore_future_candles(sign):
    gap = (97, 110, 96, 105) if sign > 0 else (103, 104, 90, 95)
    prefix = [ENTRY, (100, 101, 99, 100), gap]
    t = run(prefix, sign)
    future = run([*prefix, (100, 1000, 1, 100)], sign)
    assert (t.mae_r, t.mfe_r) == pytest.approx((-1.5, 0.5))
    assert future == t


@pytest.mark.parametrize("sign", [1, -1])
def test_b7_stop_exactly_at_open_does_not_count_later_extremes(sign):
    gap = (98, 110, 90, 105) if sign > 0 else (102, 110, 90, 95)
    t = run([ENTRY, gap], sign)
    assert (t.mae_r, t.mfe_r) == pytest.approx((-1, 0))


@pytest.mark.parametrize("sign", [1, -1])
def test_b7_whole_tp_exit_at_open_does_not_count_later_extremes(sign):
    gap = (105, 110, 99, 106) if sign > 0 else (95, 101, 90, 94)
    t = run([ENTRY, gap], sign, tp=100 + sign * 4)
    assert t.exit_reason is ExitReason.TAKE_PROFIT
    assert t.exit_price == 100 + sign * 4  # TP retains its planned limit price
    assert (t.mae_r, t.mfe_r) == pytest.approx((0, 2.5))


@pytest.mark.parametrize("sign", [1, -1])
def test_b7_partial_tp_at_open_still_tracks_candle_while_remainder_is_open(sign):
    candle = (103, 105, 99, 104) if sign > 0 else (97, 101, 95, 96)
    costs = replace(COSTS, spread=0, slippage=0)
    t = run([ENTRY, candle], sign, costs=costs, tp=100 + sign * 2, tp2=100 + sign * 6)
    assert (t.mae_r, t.mfe_r) == pytest.approx((-0.5, 2.5))


@pytest.mark.parametrize("sign", [1, -1])
def test_b7_be_gap_keeps_excursions_from_before_the_gap(sign):
    first = (100, 103, 99.9, 102.5) if sign > 0 else (100, 100.1, 97, 97.5)
    gap = (100, 120, 80, 100)
    t = run([ENTRY, first, gap], sign, tp=100 + sign * 2, tp2=100 + sign * 6)
    assert t.exit_reason is ExitReason.BREAK_EVEN
    assert t.exit_price == 100
    assert (t.mae_r, t.mfe_r) == pytest.approx((-0.05, 1.5))


@pytest.mark.parametrize("sign", [1, -1])
def test_b7_tp_gap_does_not_override_sl_first_in_a_candle_with_both_levels(sign):
    candle = (105, 110, 90, 100) if sign > 0 else (95, 110, 90, 100)
    t = run([ENTRY, candle], sign, tp=100 + sign * 4)
    assert t.exit_reason is ExitReason.STOP_LOSS
    assert t.exit_price == 100 - sign * 2
    assert (t.mae_r, t.mfe_r) == pytest.approx((-5, 5))


@pytest.mark.parametrize("scaling", [False, True])
@pytest.mark.parametrize("spread_enabled", [False, True])
def test_b4_slippage_scaling_switch_and_spread_switch_are_independent(scaling, spread_enabled):
    cfg = CostConfig(
        **TOUCH,
        symbols={"TEST": replace(COSTS, reference_price=200)},
        spread_price_scaling=scaling,
        spread_enabled=spread_enabled,
    )
    assert cfg.slippage("TEST", 100) == pytest.approx(0.05 if scaling else 0.1)
    assert cfg.slippage("TEST") == pytest.approx(0.1)


@pytest.mark.parametrize("threshold, count", [(0.2001, 0), (0.2003, 1)])
def test_b6_cost_filter_estimates_commission_on_actual_entry_fill(threshold, count):
    # Spread .2 / risk 2 + .001 * (100.3 + 100.3) / risk 2 = .2003R.
    costs = CostConfig(
        **TOUCH,
        symbols={"TEST": replace(COSTS, commission_pct_per_side=0.001)},
        max_cost_r=threshold,
    )
    order = Order(LONG, 100, 98, None)
    trades = run_backtest(Scripted(order), [build_series([ENTRY])], EngineConfig(costs=costs))
    assert len(trades) == count


@pytest.mark.parametrize("pct", [1, 2])
def test_b6_unsolvable_percentage_be_is_rejected(pct):
    costs = replace(COSTS, commission_pct_per_side=pct)
    with pytest.raises(ValueError, match="commission_pct_per_side"):
        run([ENTRY], costs=costs)


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("kind", ["time", "end_of_data", "target", "stop", "gap"])
def test_b4_b6_entry_screening_obeys_the_same_market_fill_costs(sign, kind):
    costs = CostConfig(**TOUCH, symbols={"TEST": replace(COSTS, commission_pct_per_side=0.001)})
    candle = ENTRY
    price = 100
    if kind == "target":
        candle = (100, 103, 99, 102) if sign > 0 else (100, 101, 97, 98)
        price = 100 + sign * 2
    elif kind == "stop":
        candle = (100, 101, 97, 99) if sign > 0 else (100, 103, 99, 101)
        price = 100 - sign * 2
    elif kind == "gap":
        price = 100 - sign * 3
        candle = (price, price, price, price)
    data = M1Data.from_candles(build_candles([candle], Timeframe.M1))
    trade = ScreenTrade(
        "TEST",
        LONG if sign > 0 else SHORT,
        DEFAULT_START,
        100,
        100 - sign * 2,
        DEFAULT_START + Timeframe.M1.duration,
        0,
    )
    result = (
        exit_after_bars(data, trade, 1, 1, costs)
        if kind == "time"
        else exit_bracket(data, trade, costs)
    )
    entry_fill = 100 + (0.2 if sign > 0 else 0) + sign * 0.1
    exit_fill = price + (0.2 if sign < 0 else 0) - (0 if kind == "target" else sign * 0.1)
    net = (sign * (exit_fill - entry_fill) - 0.001 * (entry_fill + exit_fill)) / 2
    assert result.r_net == pytest.approx(net)
    if kind != "target":
        random = random_exit_runs(data, trade, np.array([60, 120]), costs)
        assert random.net == pytest.approx([net, net])
