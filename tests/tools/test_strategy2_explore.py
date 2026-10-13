"""The exit variants of the strategy-2 exploration tool (tools/strategy2_explore.py)."""

from __future__ import annotations

from dataclasses import replace

from backtester.core.models import Direction
from backtester.strategy.base import Order
from backtester.tools.strategy2_explore import EXITS, ReplayOrders, pick

LONG = Order(
    Direction.BULLISH, 100.0, 98.0, 103.0, take_profit_2=105.0, tp1_share=1 / 3,
    break_even_after_tp1=True, take_profit_3=108.0, tp2_share=1 / 3,
)  # fmt: skip


def test_fixed_r_targets_use_the_risk_of_the_order():
    o = EXITS["2R only"](LONG)  # risk 2 -> 104
    assert (o.take_profit, o.take_profit_2, o.take_profit_3, o.tp1_share) == (
        104.0,
        None,
        None,
        1.0,
    )
    short = replace(LONG, direction=Direction.BEARISH, entry=100.0, stop_loss=102.0)
    assert EXITS["1.5R only"](short).take_profit == 97.0


def test_single_tp_and_two_parts():
    assert EXITS["TP1 only"](LONG).take_profit == 103.0
    assert EXITS["TP2 only"](LONG).take_profit == 105.0
    two = EXITS["2 parts + BE"](LONG)
    assert (two.take_profit, two.take_profit_2, two.take_profit_3, two.tp1_share) == (
        103.0, 105.0, None, 0.5,
    )  # fmt: skip
    assert two.break_even_after_tp1
    assert not EXITS["3 parts, no BE"](LONG).break_even_after_tp1
    assert EXITS["3 parts + BE (today)"](LONG) == LONG


def test_tp2_only_falls_back_to_the_last_tp_there_is():
    one = replace(LONG, take_profit_2=None, take_profit_3=None, tp1_share=1.0)
    assert EXITS["TP2 only"](one).take_profit == 103.0


class E:
    def __init__(self, at, window, open_offset, setup_start, symbol="NAS100", day=1):
        self.at, self.window, self.open_offset, self.setup_start = (
            at,
            window,
            open_offset,
            setup_start,
        )
        self.symbol, self.date = symbol, day


def test_pick_cuts_the_window_and_takes_the_first_entry_per_window():
    es = [
        E(1, "am", -40, -50),  # before a 30 min window
        E(2, "am", 10, -20),  # first inside
        E(3, "am", 20, 5),  # second in the same window: not taken
        E(4, "pm", 200, 100),  # after a 120 min window
        E(5, "pm", 50, 40),
    ]
    assert [e.at for e in pick(es, 30, 120)] == [2, 5]
    assert [e.at for e in pick(es, 30, 120, kinds=("pm",))] == [5]
    assert [e.at for e in pick(es, 30, 120, first_only=False)] == [2, 3, 5]
    assert [e.at for e in pick(es, 60, 300)] == [1, 4]


def test_replay_orders_returns_the_order_at_its_close_time():
    s = ReplayOrders({10: [LONG]})
    assert s.on_candle(10, {}) == [LONG] and s.on_candle(11, {}) == []
