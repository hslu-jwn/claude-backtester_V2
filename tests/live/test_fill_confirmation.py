"""Fills are confirmed from the deal and the position, never from `order_send`'s result
(FTMO answers 10009 with deal 0 and price 0.0; the deal shows up a few ms later)."""

from __future__ import annotations

import pytest
from fake_bot_mt5 import FakeBotMt5

from backtester.core.models import Direction
from backtester.live import orders
from backtester.live.orders import (
    OrderLog,
    close_volume,
    confirm_close,
    confirm_open,
    market_order,
)
from backtester.live.test_orders import run_test

T = 1_791_000_000


def terminal(delay=0) -> FakeBotMt5:
    fake = FakeBotMt5(delay_polls=delay)
    fake.initialize()
    fake.add_symbol("XAUUSD", trade_stops_level=10)
    fake.set_tick("XAUUSD", 4000.00, 4000.20, T)
    return fake


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    monkeypatch.setattr(orders, "CONFIRM_INTERVAL_S", 0.0)


def test_open_result_has_no_fill_but_the_deal_does_after_a_wait():
    fake = terminal(delay=3)
    result, _, _, _ = market_order(fake, "XAUUSD", Direction.BULLISH, 0.02, 3990, 4010, OrderLog())
    assert (result.retcode, result.deal, result.price) == (10009, 0, 0.0)
    fill = confirm_open(fake, result)
    assert fill.confirmed and fill.price == 4000.2 and fill.volume == 0.02
    assert fill.position.ticket == result.order


def test_open_not_visible_within_the_timeout_is_not_confirmed():
    fake = terminal(delay=10_000)
    result, *_ = market_order(fake, "XAUUSD", Direction.BULLISH, 0.02, 3990, 4010, OrderLog())
    clock = iter(range(100)).__next__
    fill = confirm_open(fake, result, timeout=3, sleep=lambda s: None, clock=clock)
    assert not fill.confirmed and fill.price == 0.0


def test_partial_close_waits_for_the_reduced_volume():
    fake = terminal()
    result, *_ = market_order(fake, "XAUUSD", Direction.BULLISH, 0.02, 3990, 4010, OrderLog())
    position = confirm_open(fake, result).position
    fake.delay_polls = 4
    closed, _, _ = close_volume(fake, position, 0.01, OrderLog())
    fill = confirm_close(fake, closed, position, 0.01)
    assert fill.confirmed and fill.position.volume == 0.01 and fill.price == 4000.0
    fake.delay_polls = 4
    closed, _, _ = close_volume(fake, fill.position, 0.01, OrderLog())
    last = confirm_close(fake, closed, fill.position, 0.01)
    assert last.confirmed and last.position is None


def test_a_rejected_order_is_never_confirmed():
    fake = terminal()
    fake.reject[(fake.TRADE_ACTION_DEAL, None)] = fake.TRADE_RETCODE_MARKET_CLOSED
    result, *_ = market_order(fake, "XAUUSD", Direction.BULLISH, 0.02, 3990, 4010, OrderLog())
    assert not confirm_open(fake, result).confirmed


def test_the_scripted_test_survives_a_late_deal():
    fake = terminal(delay=3)
    lines = run_test(fake, "XAUUSD", "XAUUSD", OrderLog())
    text = "\n".join(lines)
    assert "filled 4000.2" in text and "0.01 lots left" in text
    assert "10014" not in text and "! still open" not in text
    assert "End check: nothing open" in text and fake.positions == {}
