"""DEMO LOCK and the scripted demo test orders (ROADMAP 7.1), with a fake MetaTrader5."""

from __future__ import annotations

import json

import pytest
from fake_mt5 import FakeMt5, Position

from backtester.core.models import Direction
from backtester.live.orders import (
    MAGIC,
    DemoLockError,
    OrderLog,
    close_own_positions,
    close_volume,
    market_order,
    modify_sl,
    send,
)
from backtester.live.test_orders import run_from_panel, run_test
from backtester.live.trading_settings import TradingSettings

SERVER_TIME = 1_791_000_000


def demo_terminal(trade_mode=FakeMt5.ACCOUNT_TRADE_MODE_DEMO, **specs) -> FakeMt5:
    fake = FakeMt5(trade_mode=trade_mode)
    fake.initialize()
    fake.add_symbol("XAUUSD", trade_stops_level=10, **specs)
    fake.set_tick("XAUUSD", 4000.00, 4000.20, SERVER_TIME)
    return fake


# --- DEMO LOCK ---------------------------------------------------------------------------

POSITION = Position(5, "XAUUSD", 0, 0.02, 4000.2, 3990.0, 4010.0, MAGIC, "", SERVER_TIME)


@pytest.mark.parametrize(
    "mode", [FakeMt5.ACCOUNT_TRADE_MODE_REAL, FakeMt5.ACCOUNT_TRADE_MODE_CONTEST]
)
@pytest.mark.parametrize(
    "call",
    [
        lambda m, log: market_order(m, "XAUUSD", Direction.BULLISH, 0.02, 3990, 4010, log),
        lambda m, log: market_order(m, "XAUUSD", Direction.BEARISH, 0.02, 4010, 3990, log),
        lambda m, log: modify_sl(m, POSITION, 4000.2, log),
        lambda m, log: close_volume(m, POSITION, 0.01, log),
        lambda m, log: close_own_positions(m, "XAUUSD", log),
        lambda m, log: send(m, {"action": m.TRADE_ACTION_DEAL}, log, "raw"),
    ],
)
def test_every_order_function_refuses_a_non_demo_account(mode, call):
    fake = demo_terminal(trade_mode=mode)
    fake.positions[POSITION.ticket] = POSITION
    log = OrderLog()
    with pytest.raises(DemoLockError, match="not a demo account"):
        call(fake, log)
    assert fake.requests == [] and log.entries == []


def test_order_functions_refuse_without_an_account():
    fake = demo_terminal()
    fake.shutdown()
    with pytest.raises(DemoLockError, match="no account"):
        market_order(fake, "XAUUSD", Direction.BULLISH, 0.02, 3990, 4010, OrderLog())
    assert fake.requests == []


def test_the_panel_test_is_refused_on_a_real_account():
    fake = FakeMt5(trade_mode=FakeMt5.ACCOUNT_TRADE_MODE_REAL)
    fake.add_symbol("XAUUSD")
    lines = run_from_panel(TradingSettings(), None, "XAUUSD", fake, OrderLog())
    assert lines[0].startswith("Refused: not a demo account")
    assert fake.requests == []


# --- the scripted test -------------------------------------------------------------------


def test_scripted_run_on_demo(tmp_path):
    fake = demo_terminal()
    log = OrderLog(tmp_path / "log.jsonl")
    lines = run_test(fake, "XAUUSD", "XAUUSD", log)
    labels = [e["label"] for e in log.entries]
    assert labels == [
        "open buy",
        "SL to break-even",  # rejected: the bid is below the entry right after a buy
        "SL halfway",
        "close half",
        "close rest",
        "open sell",
        "SL to break-even",
        "SL halfway",
        "close half",
        "close rest",
    ]
    assert [e["retcode"] for e in log.entries] == [
        10009,
        10016,
        10009,
        10009,
        10009,
        10009,
        10016,
        10009,
        10009,
        10009,
    ]
    opening = log.entries[0]["request"]
    assert opening["volume"] == 0.02 and opening["magic"] == MAGIC
    # SL / TP 0.3% of the price away (more than 3 x the stops level of 10 points)
    assert (opening["sl"], opening["tp"]) == (3988.2, 4012.2)
    assert log.entries[3]["request"]["volume"] == 0.01
    assert fake.positions == {}
    text = "\n".join(lines)
    assert "filled 4000.2 vs ask 4000.2 (slippage +0 points), filling FOK" in text
    assert "invalid stops" in text and "(expected right after the entry)" in text
    assert "0.01 lots left, at 4000.0" in text
    assert "End check: nothing open" in text
    assert "Rejections: SL to break-even 10016 invalid stops" in text
    written = [json.loads(line) for line in (tmp_path / "log.jsonl").read_text().splitlines()]
    assert len(written) == 10 and written[0]["result"]["retcode"] == 10009


def test_break_even_accepted_when_the_price_moved():
    fake = demo_terminal()
    original = fake.order_send

    def move_price_after_open(request):
        result = original(request)
        if request["action"] == fake.TRADE_ACTION_DEAL and "position" not in request:
            fake.set_tick("XAUUSD", 4005.00, 4005.20, SERVER_TIME + 1)  # buy in profit
        return result

    fake.order_send = move_price_after_open
    log = OrderLog()
    lines = run_test(fake, "XAUUSD", "XAUUSD", log)
    assert log.entries[1]["label"] == "SL to break-even" and log.entries[1]["retcode"] == 10009
    assert any("SL on the position now 4000.2" in line for line in lines)


def test_filling_mode_falls_back_and_logs_both_tries():
    fake = demo_terminal()
    fake.allowed_fillings = {fake.ORDER_FILLING_IOC}  # the symbol says FOK and IOC
    log = OrderLog()
    lines = run_test(fake, "XAUUSD", "XAUUSD", log)
    assert [e["retcode"] for e in log.entries[:2]] == [10030, 10009]
    assert log.entries[1]["request"]["type_filling"] == fake.ORDER_FILLING_IOC
    assert any("filling IOC" in line for line in lines)
    assert fake.positions == {}


def test_market_closed_stops_the_test():
    fake = demo_terminal()
    fake.reject[(fake.TRADE_ACTION_DEAL, None)] = fake.TRADE_RETCODE_MARKET_CLOSED
    lines = run_test(fake, "XAUUSD", "XAUUSD", OrderLog())
    assert "Stopped: market closed: no test possible now" in lines
    assert lines[-3] == "End check: nothing open" or "End check: nothing open" in lines


def test_an_error_midway_still_closes_everything():
    fake = demo_terminal()
    original = fake.order_send

    def broken_modify(request):
        if request["action"] == fake.TRADE_ACTION_SLTP:
            raise RuntimeError("terminal hiccup")
        return original(request)

    fake.order_send = broken_modify
    lines = run_test(fake, "XAUUSD", "XAUUSD", OrderLog())
    assert "Stopped by an error: RuntimeError: terminal hiccup" in lines
    assert "Cleanup: closed 1 position(s) the test had left open" in lines
    assert "End check: nothing open" in lines and fake.positions == {}


def test_the_users_own_positions_are_left_alone():
    fake = demo_terminal()
    own = POSITION._replace(ticket=1, magic=0)
    fake.positions[1] = own
    lines = run_test(fake, "XAUUSD", "XAUUSD", OrderLog())
    assert fake.positions == {1: own}
    assert "(1 position(s) of your own on XAUUSD: left alone)" in lines


def test_algo_trading_off_sends_nothing():
    fake = demo_terminal()
    fake.algo_allowed = False
    lines = run_test(fake, "XAUUSD", "XAUUSD", OrderLog())
    assert "press the Algo Trading button" in lines[-1] and fake.requests == []


def test_panel_runs_the_test_through_a_session(tmp_path):
    fake = FakeMt5()
    fake.add_symbol("XAUUSD.r", trade_stops_level=10)
    fake.set_tick("XAUUSD.r", 4000.00, 4000.20, SERVER_TIME)
    settings = TradingSettings(symbols={"XAUUSD": "XAUUSD.r"})
    lines = run_from_panel(settings, None, "XAUUSD", fake, OrderLog(tmp_path / "l.jsonl"))
    assert lines[0].startswith("Demo test orders XAUUSD (XAUUSD.r)")
    assert lines[-1] == f"Log: {tmp_path / 'l.jsonl'}"
    assert not fake.initialized  # disconnected afterwards
