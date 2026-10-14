"""Signal exits (`Strategy.exits`) and orders without a take profit (ROADMAP 10.1).
Spec: strategy-trend-following.md › Position; CLAUDE.md › Invariant #1."""

from __future__ import annotations

import pytest
from conftest import DEFAULT_START, build_series

from backtester.analytics.metrics import summarize
from backtester.analytics.records import TradeRecord
from backtester.core.models import Direction, Timeframe
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.base import Order, Strategy

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
NO_COSTS = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))
SPREAD_ONLY = EngineConfig(costs=CostConfig(spread_enabled=True, commission_enabled=False))
ENTRY = (100.0, 100.5, 99.5, 100.0)  # close 100
QUIET = (100.0, 100.6, 99.6, 100.2)


class Scripted(Strategy):
    """At cursor k: open each (direction, SL) of opens[k] without a TP (ref = the
    cursor and index); close the refs listed in closes[k]."""

    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)

    def __init__(self, opens, closes=None):
        self.opens, self.closes = opens, closes or {}
        self.events: list[tuple] = []
        self._cursor = -1

    def on_candle(self, now, views):
        view = views[Timeframe.M5]
        self._cursor = view.cursor
        self.events.append(("candle", view.cursor))
        return [
            Order(d, view.current.close, sl, None, ref=(view.cursor, i))
            for i, (d, sl) in enumerate(self.opens.get(view.cursor, []))
        ]

    def exits(self):
        self.events.append(("exits", self._cursor))
        return list(self.closes.get(self._cursor, []))

    def on_trade_closed(self, ref, result):
        self.events.append(("closed", self._cursor, ref, result.exit_reason))


def run(ohlc, opens, closes=None, config=NO_COSTS, symbol="TEST"):
    strategy = Scripted(opens, closes)
    trades = run_backtest(strategy, [build_series(ohlc, symbol=symbol)], config)
    return trades, strategy


# --- orders without a take profit -------------------------------------------------------


def test_no_tp_trade_closed_by_sl():
    [t] = run([ENTRY, QUIET, (100.2, 100.3, 97.9, 98.5)], {0: [(LONG, 98.0)]})[0]
    assert t.exit_reason is ExitReason.STOP_LOSS and t.r_gross == pytest.approx(-1.0)
    assert t.take_profit is None and t.planned_r is None and t.targets == []


def test_no_tp_trade_ignores_any_rise_and_ends_at_end_of_data():
    rally = (100.0, 130.0, 100.0, 125.0)
    [t] = run([ENTRY, rally, (125.0, 140.0, 120.0, 130.0)], {0: [(LONG, 98.0)]})[0]
    assert t.exit_reason is ExitReason.END_OF_DATA
    assert t.exit_price == 130.0 and t.r_gross == pytest.approx(15.0)


def test_no_tp_short_is_mirrored():
    [t] = run([ENTRY, (100.0, 100.2, 80.0, 82.0)], {0: [(SHORT, 102.0)]})[0]
    assert t.exit_reason is ExitReason.END_OF_DATA and t.r_gross == pytest.approx(9.0)


def test_no_tp_order_still_needs_its_sl_beyond_entry():
    with pytest.raises(ValueError, match="SL"):
        run([ENTRY, QUIET], {0: [(LONG, 101.0)]})


def test_no_tp_trade_in_metrics_and_records():
    [t] = run([ENTRY, QUIET, (100.2, 100.3, 97.9, 98.5)], {0: [(LONG, 98.0)]})[0]
    assert summarize([t])["avg_rr"] is None  # no planned R without a target
    row = {
        "id": 1, "symbol": "TEST", "direction": "long", "entry_time": t.entry_time.isoformat(),
        "entry_candle": t.entry_candle.isoformat(), "entry": 100.0, "initial_stop": 98.0,
        "take_profit": "", "planned_rr": "", "exit_time": t.exit_time.isoformat(),
        "exit_price": 98.0, "exit_reason": "stop_loss", "r_gross": -1.0, "r_net": -1.0,
    }  # fmt: skip
    rec = TradeRecord.from_row(row)
    assert rec.take_profit is None and rec.planned_r is None


# --- signal exits -----------------------------------------------------------------------


def test_signal_exit_closes_at_the_candle_close():
    trades, _ = run(
        [ENTRY, QUIET, (100.2, 103.2, 100.1, 103.0), QUIET],
        {0: [(LONG, 98.0)]},
        {2: [(0, 0)]},
    )
    [t] = trades
    assert t.exit_reason is ExitReason.SIGNAL and t.exit_price == 103.0
    assert t.r_gross == pytest.approx(1.5)
    assert t.exit_candle == DEFAULT_START + 2 * Timeframe.M5.duration


def test_signal_exit_costs_long_bid_short_ask():
    ohlc = [ENTRY, QUIET, (100.2, 100.3, 98.9, 99.0)]  # XAUUSD spread 0.25, risk 2 -> 0.125 R
    [long] = run(ohlc, {0: [(LONG, 98.0)]}, {2: [(0, 0)]}, SPREAD_ONLY, "XAUUSD")[0]
    [short] = run(ohlc, {0: [(SHORT, 102.0)]}, {2: [(0, 0)]}, SPREAD_ONLY, "XAUUSD")[0]
    assert long.exit_fill == 99.0 and long.r_gross == pytest.approx(-0.5)
    assert long.r_net == pytest.approx(-0.625)  # in at ask 100.25, out at bid 99
    assert short.exit_fill == 99.25 and short.r_gross == pytest.approx(0.5)
    assert short.r_net == pytest.approx(0.375)  # in at bid 100, out at ask 99.25


def test_closed_callback_runs_before_the_new_order_is_filled_and_reverse_works():
    trades, strategy = run(
        [ENTRY, QUIET, (100.2, 103.2, 100.1, 103.0), (103.0, 103.5, 101.0, 102.0)],
        {0: [(LONG, 98.0)], 2: [(SHORT, 106.0)]},
        {2: [(0, 0)]},
    )
    assert [t.direction for t in trades] == [LONG, SHORT]
    first, second = trades
    assert first.exit_reason is ExitReason.SIGNAL and first.exit_price == 103.0
    assert second.entry == 103.0 and second.entry_time == first.exit_time  # same close
    assert second.exit_reason is ExitReason.END_OF_DATA
    closed = [e for e in strategy.events if e[0] == "closed"]
    assert closed == [("closed", 2, (0, 0), ExitReason.SIGNAL)]
    # order inside candle 2: on_candle, then exits, then the closed callback
    inside = [e[0] for e in strategy.events if e[1] == 2]
    assert inside == ["candle", "exits", "closed"]


def test_ref_that_is_not_open_is_ignored():
    trades, _ = run([ENTRY, QUIET, QUIET], {0: [(LONG, 98.0)]}, {1: [(9, 9), "nope"]})
    [t] = trades
    assert t.exit_reason is ExitReason.END_OF_DATA


def test_sl_in_the_candle_comes_first_then_the_signal_exit_is_ignored():
    trades, strategy = run(
        [ENTRY, (100.0, 100.2, 97.0, 99.0)],
        {0: [(LONG, 98.0)]},
        {1: [(0, 0)]},
    )
    [t] = trades
    assert t.exit_reason is ExitReason.STOP_LOSS and t.exit_price == 98.0
    assert [e for e in strategy.events if e[0] == "closed"] == [
        ("closed", 0, (0, 0), ExitReason.STOP_LOSS)  # reported before candle 1's on_candle
    ]
    assert ("exits", 1) in strategy.events and ("candle", 1) in strategy.events


def test_stop_out_then_new_entry_in_the_same_candle_at_its_close():
    trades, _ = run(
        [ENTRY, (100.0, 100.2, 96.0, 96.5)],
        {0: [(LONG, 98.0)], 1: [(SHORT, 99.0)]},
    )
    first, second = trades
    assert first.exit_reason is ExitReason.STOP_LOSS
    assert second.direction is SHORT and second.entry == 96.5


def test_only_the_named_trade_is_closed():
    trades, _ = run(
        [ENTRY, QUIET, (100.2, 101.2, 100.1, 101.0)],
        {0: [(LONG, 98.0), (LONG, 97.0)]},
        {2: [(0, 1)]},
    )
    by_reason = {t.initial_stop: t.exit_reason for t in trades}
    assert by_reason == {97.0: ExitReason.SIGNAL, 98.0: ExitReason.END_OF_DATA}


def test_default_strategy_has_no_exits():
    class Plain(Strategy):
        base_timeframe = Timeframe.M5
        timeframes = (Timeframe.M5,)

        def on_candle(self, now, views):
            return []

    assert Plain().exits() == []
