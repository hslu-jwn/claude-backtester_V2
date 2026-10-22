"""Fixes for the review findings of the live bot (docs/review/live.md #1-#16, #18-#20).

Same fake world as test_bot.py (fake MT5, hand-built M1 bars). Nothing here touches a terminal,
places a real order or reads a credential. Each test is named after its finding.
"""

from __future__ import annotations

import dataclasses
import json
import math
from datetime import UTC, datetime, timedelta

import pytest
from fake_bot_mt5 import Deal2
from test_bot import (
    BROKER,
    DAY,
    SYM,
    World,
    history_rows,
    ny,
    quote_at,
    row,
    started,
    today_rows,
    truncate,
)
from test_demo_orders import POSITION, demo_terminal
from test_loop_safety import cycle, labels, make, request_file
from test_lost_order import lose_answers
from test_status import SECRETS, Notes

from backtester.core.errors import LookaheadError
from backtester.data.cache import cache_path, read_cached_day
from backtester.live import bot as bot_module
from backtester.live import orders
from backtester.live.bot import Bot, BotConfig
from backtester.live.orders import OrderLog
from backtester.live.test_orders import run_test
from backtester.risk.prop_rules import GuardConfig
from backtester.ui import live_model

M1 = 1  # FakeMt5.TIMEFRAME_M1


@pytest.fixture(autouse=True)
def fast_confirm(monkeypatch):
    monkeypatch.setattr(orders, "CONFIRM_INTERVAL_S", 0.0)


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def position_net(world, ticket) -> float:
    return sum(
        d.profit + d.commission + d.swap + d.fee
        for d in world.fake.deals.values()
        if d.position_id == ticket
    )


# --- #1 clock skew: a bar still forming on the server is never admitted ---------------------------


def test_1_a_bar_still_forming_on_the_server_is_not_admitted(world):
    bot = started(world)
    full = history_rows() + today_rows()
    t940 = int(ny(DAY, 9, 40).timestamp())
    forming = [row(ny(DAY, 9, 40), 100, 101, 100, 101) if r[0] == t940 else r for r in full]
    world.fake.set_rates(BROKER, M1, forming)
    quote_at(world, ny(DAY, 9, 40) + timedelta(seconds=59))  # server: 14:40:59
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))  # the PC clock is 4 s ahead
    bot.cycle()
    assert world.opens() == []
    assert bot.symbols[SYM].candles[-1].ts == ny(DAY, 9, 39)  # the forming bar is not kept
    world.fake.set_rates(BROKER, M1, full)  # the bar's final OHLC
    quote_at(world, ny(DAY, 9, 41) + timedelta(seconds=1))
    world.at(ny(DAY, 9, 41) + timedelta(seconds=12))
    bot.cycle()
    assert len(world.opens()) == 1
    last = bot.symbols[SYM].candles[-1]
    assert last.ts == ny(DAY, 9, 40) and last.close == 103


# --- #2 LookaheadError is never swallowed ----------------------------------------------------------


def _lookahead(*a, **k):
    raise LookaheadError("a candle that has not closed")


def test_2_lookahead_in_the_strategy_ends_the_cycle(world):
    bot = started(world)
    bot.symbols[SYM].strategy.on_candle = _lookahead
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    with pytest.raises(LookaheadError):
        bot.cycle()


def test_2_lookahead_in_a_cycle_step_ends_the_cycle(world, monkeypatch):
    bot = started(world)
    monkeypatch.setattr(bot, "_reconcile", _lookahead)
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    with pytest.raises(LookaheadError):
        bot.cycle()


def test_2_lookahead_at_entry_ends_the_cycle(world, monkeypatch):
    bot = started(world)
    monkeypatch.setattr(bot_module, "lots_for_risk", _lookahead)
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    with pytest.raises(LookaheadError):
        bot.cycle()


def test_2_lookahead_ends_the_run(world, monkeypatch):
    world.at(ny(DAY, 9, 38))
    bot = world.bot()
    monkeypatch.setattr(bot, "_reconcile", _lookahead)
    stop_later = ny(DAY, 9, 45)  # without the fix the loop would go on: end it by a STOP file
    world.clock.on_sleep = lambda c: request_file(world, "STOP") if c.t >= stop_later else None
    with pytest.raises(LookaheadError):
        bot.run()


# --- #3 a failed position query is not "flat" -----------------------------------------------------


def failing_positions(world, when):
    """positions_get answers None (a failed call) for the queries `when(symbol, ticket)` picks."""
    real = world.fake.positions_get
    state = {"on": True}

    def get(symbol=None, ticket=None):
        if state["on"] and when(symbol, ticket):
            world.fake.error = (-10004, "No IPC connection")
            return None
        return real(symbol=symbol, ticket=ticket)

    world.fake.positions_get = get
    return state


def test_3_emergency_keeps_flattening_while_the_position_query_fails(world):
    bot = make(world)
    cycle(world, bot, 9, 41)
    state = failing_positions(world, lambda s, t: s is None and t is None)
    request_file(world, "EMERGENCY")
    assert cycle(world, bot, 9, 42) == "continue"
    assert len(world.fake.positions) == 1 and bot.flatten is not None
    state["on"] = False
    world.fake.error = (1, "Success")
    assert cycle(world, bot, 9, 43) == "stop"
    assert world.fake.positions == {}


def test_3_a_failed_ticket_query_keeps_the_session_exit_pending(world):
    bot = make(world)
    cycle(world, bot, 9, 41)
    (ticket,) = world.fake.positions
    state = failing_positions(world, lambda s, t: t is not None)
    cycle(world, bot, 15, 55)
    assert list(world.fake.positions) == [ticket] and bot.pending_exits
    state["on"] = False
    world.fake.error = (1, "Success")
    cycle(world, bot, 15, 56)
    assert world.fake.positions == {} and len(world.csv("trades.csv")) == 1


# --- #4 an unconfirmed close keeps the trade -------------------------------------------------------


def test_4_an_unconfirmed_close_keeps_the_trade_and_retries(world, monkeypatch):
    bot = make(world)
    cycle(world, bot, 9, 41)
    (ticket,) = world.fake.positions
    real = world.fake.order_send
    state = {"on": True}

    def send(request):
        if state["on"] and "position" in request:  # accepted, but nothing closed
            world.fake.requests.append(dict(request))
            return world.fake._result(world.fake.TRADE_RETCODE_DONE, request)
        return real(request)

    world.fake.order_send = send
    monkeypatch.setattr(orders, "CONFIRM_TIMEOUT_S", 0.0)
    cycle(world, bot, 15, 55)
    assert ticket in bot.by_ticket and world.csv("trades.csv") == []
    state["on"] = False
    cycle(world, bot, 15, 56)
    assert world.fake.positions == {} and len(world.csv("trades.csv")) == 1


# --- #5 an accepted order whose position is not visible is not abandoned ---------------------------


def hide_fills(world, deals_too=False):
    """Opens execute, but their position (and deal) is not visible until put back."""
    real = world.fake.order_send
    hidden = {"positions": {}, "deals": {}}

    def send(request):
        result = real(request)
        if "position" not in request and result.retcode == world.fake.TRADE_RETCODE_DONE:
            hidden["positions"][result.order] = world.fake.positions.pop(result.order)
            if deals_too:
                hidden["deals"][result.order] = world.fake.deals.pop(result.order)
        return result

    world.fake.order_send = send
    return hidden


def test_5_an_accepted_order_is_tracked_from_its_deal(world, monkeypatch):
    monkeypatch.setattr(orders, "CONFIRM_TIMEOUT_S", 0.0)
    bot = make(world, adopt_recheck_cycles=1)
    hidden = hide_fills(world)
    cycle(world, bot, 9, 41)
    (ticket,) = hidden["positions"]
    for minute in (42, 43, 44):
        cycle(world, bot, 9, minute)
    assert labels(world, "skip") == []
    assert ticket in bot.by_ticket
    world.fake.positions.update(hidden["positions"])
    cycle(world, bot, 15, 55)
    assert world.fake.positions == {} and len(world.csv("trades.csv")) == 1


def test_5_an_accepted_order_is_rechecked_until_it_shows_up(world, monkeypatch):
    monkeypatch.setattr(orders, "CONFIRM_TIMEOUT_S", 0.0)
    bot = make(world, adopt_recheck_cycles=1)
    hidden = hide_fills(world, deals_too=True)
    cycle(world, bot, 9, 41)
    for minute in (42, 43, 44):
        cycle(world, bot, 9, minute)
    assert labels(world, "skip") == [] and len(bot.unclear) == 1  # never given up
    world.fake.positions.update(hidden["positions"])
    world.fake.deals.update(hidden["deals"])
    cycle(world, bot, 9, 45)
    (ticket,) = world.fake.positions
    assert ticket in bot.by_ticket and bot.unclear == []
    cycle(world, bot, 15, 55)
    assert world.fake.positions == {} and len(world.csv("trades.csv")) == 1


# --- #6 a failing bar does not skip the rest of the batch ------------------------------------------


def test_6_a_failing_bar_does_not_skip_the_session_exit_in_the_same_batch(world):
    bot = make(world)
    cycle(world, bot, 9, 41)
    strategy = bot.symbols[SYM].strategy
    real = strategy.on_candle
    calls = {"n": 0}

    def flaky(now, views):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("first bar of the batch broke")
        return real(now, views)

    strategy.on_candle = flaky
    cycle(world, bot, 15, 55)  # one batch: 09:41 .. the bar closing 15:55
    assert labels(world, "error")
    assert world.fake.positions == {} and len(world.csv("trades.csv")) == 1
    count = len(bot.symbols[SYM].candles)
    cycle(world, bot, 15, 56)
    assert len(bot.symbols[SYM].candles) == count + 1  # nothing fetched or fed twice


# --- #7 sizing from the executable quote, stops on the tick grid and outside the stops level -------


def test_7_lots_are_sized_from_the_executable_price(world):
    bot = make(world)
    world.set_tick(105.0, 105.2)  # the ask ran away from the signal price 103
    cycle(world, bot, 9, 41)
    (request,) = world.opens()
    assert request["volume"] == pytest.approx(32.4)  # 250 / (105.2 - 97.5) = 32.47 -> 32.4
    assert request["volume"] * (105.2 - 97.5) <= 250.0


def test_7_the_stop_is_rounded_to_the_tick_size(world):
    world.fake.add_symbol(
        BROKER, digits=2, point=0.01, trade_tick_size=0.4, trade_tick_value=0.4,
        volume_min=0.1, volume_step=0.1, volume_max=500.0, trade_stops_level=0,
    )  # fmt: skip
    bot = make(world)
    cycle(world, bot, 9, 41)
    (request,) = world.opens()
    assert request["sl"] == 97.6  # 97.5 on a 0.4 grid
    assert request["volume"] == pytest.approx(44.6)  # 250 / (103.2 - 97.6) = 44.64


@pytest.mark.parametrize(
    "stops_level, bid, ask",
    [(600, 103.0, 103.2), (0, 97.0, 97.2)],  # 6.0 > 5.5 to the bid; bid below the SL
)
def test_7_a_stop_the_broker_would_refuse_is_skipped(world, stops_level, bid, ask):
    world.fake.symbols[BROKER] = world.fake.symbols[BROKER]._replace(trade_stops_level=stops_level)
    bot = make(world)
    world.set_tick(bid, ask)
    cycle(world, bot, 9, 41)
    assert world.opens() == []
    (skip,) = labels(world, "skip")
    assert "stop" in skip["request"]["reason"].lower()


# --- #8 session exit by the clock when no bar comes -----------------------------------------------


def test_8_session_exit_happens_without_new_bars(world):
    bot = make(world)
    cycle(world, bot, 9, 41)
    full = truncate(world, ny(DAY, 12, 59))  # the feed stops
    cycle(world, bot, 13, 0)
    cycle(world, bot, 15, 55)
    assert len(world.fake.positions) == 1  # not before the grace period
    cycle(world, bot, 16, 30)
    assert world.fake.positions == {} and len(world.closes()) == 1
    (trade,) = world.csv("trades.csv")
    assert trade["exit_reason"] == "signal"
    world.fake.set_rates(BROKER, M1, full)  # the bars come later: no second close
    cycle(world, bot, 16, 31)
    assert len(world.closes()) == 1 and len(world.csv("trades.csv")) == 1


def test_8_grace_is_a_config_value():
    assert BotConfig().exit_fallback_s == 60.0


# --- #9 a failed deal-history read does not reset the day baseline --------------------------------


def test_9_failed_history_read_blocks_entries_and_is_retried(tmp_path):
    w = World(tmp_path, balance=97_000.0)
    w.fake.deals[901] = Deal2(  # today's closed loss: the day started at 100,000
        901, 901, 55, BROKER, 1, 1.0, 97.0, 1, 4, -3_000.0, 0.0, 0.0, 0.0, 0
    )
    bot = make(w)
    real = w.fake.history_deals_get
    state = {"on": True}

    def deals(*args, ticket=None, position=None, **kw):
        if state["on"] and ticket is None and position is None:
            w.fake.error = (-10004, "No IPC connection")
            return None
        return real(*args, ticket=ticket, position=position, **kw)

    w.fake.history_deals_get = deals
    cycle(w, bot, 9, 41)
    assert w.opens() == [] and labels(w, "error")
    state["on"] = False
    w.fake.error = (1, "Success")
    cycle(w, bot, 9, 42)
    assert bot._day_balance == pytest.approx(100_000.0) and bot.blocked


# --- #10 the daily-stop latch survives a restart ----------------------------------------------------


def test_10_restart_keeps_the_daily_stop_of_the_day(world):
    first = started(world)
    world.fake.equity = 97_900.0
    world.at(ny(DAY, 9, 39) + timedelta(seconds=3))
    first.cycle()
    assert first.blocked
    world.fake.equity = 99_000.0  # recovers to -1 %
    second = started(world, t=ny(DAY, 9, 40))
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    second.cycle()
    assert world.opens() == [] and second.blocked


def test_10_the_latch_is_for_that_day_and_account_only(world):
    first = started(world)
    world.fake.equity = 97_900.0
    world.at(ny(DAY, 9, 39) + timedelta(seconds=3))
    first.cycle()
    world.fake.equity = 99_000.0
    real = world.fake.account_info
    world.fake.account_info = lambda: real()._replace(login=999)  # another account
    second = started(world, t=ny(DAY, 9, 40))
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    second.cycle()
    assert len(world.opens()) == 1 and not second.blocked
    world.fake.account_info = real
    third = started(world, t=ny(DAY, 9, 40))
    world.at(ny(DAY + timedelta(days=1), 3, 0))  # the next Prague day
    third.cycle()
    assert not third.blocked


# --- #11 control files are read before the start-up replay ----------------------------------------


def test_11_pause_present_at_start_blocks_the_replayed_entry(world):
    request_file(world, "PAUSE")
    bot = started(world, t=ny(DAY, 9, 41) + timedelta(seconds=3))
    assert world.opens() == [] and bot.paused
    assert [d["request"]["reason"] for d in labels(world, "skip")] == ["paused"]


def test_11_emergency_present_at_start_blocks_the_replayed_entry(world):
    request_file(world, "EMERGENCY")
    bot = started(world, t=ny(DAY, 9, 41) + timedelta(seconds=3))
    assert world.opens() == []
    assert bot.cycle() == "stop"


# --- #12 the demo test cleans up only what it opened ----------------------------------------------


def test_12_cleanup_leaves_bot_positions_that_were_open_before():
    fake = demo_terminal()
    bot_position = POSITION._replace(ticket=1, comment="orb 01121441")
    fake.positions[1] = bot_position
    original = fake.order_send

    def broken_modify(request):
        if request["action"] == fake.TRADE_ACTION_SLTP:
            raise RuntimeError("terminal hiccup")
        return original(request)

    fake.order_send = broken_modify
    lines = run_test(fake, "XAUUSD", "XAUUSD", OrderLog())
    assert fake.positions == {1: bot_position}
    assert "Cleanup: closed 1 position(s) the test had left open" in lines
    assert "End check: nothing open" in lines


# --- #13 credentials are scrubbed before anything is written ---------------------------------------


def test_13_event_fields_are_scrubbed_before_the_log_and_the_screen(world, capsys):
    world.at(ny(DAY, 9, 38))
    bot = Bot(
        world.config(verbose=True), world.fake, world.settings, credentials=SECRETS,
        now=world.clock, sleep=world.clock.sleep,
    )  # fmt: skip
    bot.note("error", what=f"boom {SECRETS.password}", server=SECRETS.server)
    logged = json.dumps(bot.log().entries) + bot.log().path.read_text(encoding="utf-8")
    printed = capsys.readouterr().out
    for secret in SECRETS.secrets():
        assert secret not in logged and secret not in printed
    assert "boom" in logged and "boom" in printed


# --- #14 a failing journal never silences errors or stops the bot ----------------------------------


def test_14_a_failing_journal_still_notifies_and_the_bot_trades(world, tmp_path):
    notes = Notes()
    bot = make(world, notifier=notes)
    blocker = tmp_path / "blocker"
    blocker.write_text("")  # a file where the day folder should be: every write fails
    bot._day_dir = lambda: blocker
    bot.note("error", what="boom")  # must not raise
    assert ("error", {"what": "boom"}) in notes.events
    assert any(k == "error" and "journal" in f.get("what", "") for k, f in notes.events)
    assert cycle(world, bot, 9, 41) == "continue"
    assert len(world.opens()) == 1 and len(bot.by_ticket) == 1


# --- #15 a partial fill is tracked with the filled volume -----------------------------------------


def test_15_partial_fill_registers_the_filled_volume(world):
    bot = make(world)
    real = world.fake.order_send

    def partial(request):
        if "position" in request:
            return real(request)
        result = real({**request, "volume": round(request["volume"] / 2, 1)})
        return result._replace(retcode=orders.RETCODE_DONE_PARTIAL)

    world.fake.order_send = partial
    cycle(world, bot, 9, 41)
    (position,) = world.fake.positions.values()
    trade = bot.by_ticket[position.ticket]
    assert trade.lots == position.volume
    assert trade.risk_money == pytest.approx(position.volume * 5.5 * 1.0)
    assert float(world.csv("paper.csv")[0]["lots"]) == position.volume


# --- #16 the net of a trade counts every deal of its position -------------------------------------


def test_16_explicit_close_counts_the_entry_fee_and_commission(world):
    world.fake.commission_per_lot = 0.1
    bot = make(world)
    cycle(world, bot, 9, 41)
    (ticket,) = world.fake.positions
    world.fake.deals[ticket] = world.fake.deals[ticket]._replace(fee=-5.0)
    world.set_tick(104.0, 104.2)
    cycle(world, bot, 15, 55)
    (trade,) = world.csv("trades.csv")
    assert float(trade["money"]) == pytest.approx(position_net(world, ticket))


def test_16_an_adopted_trade_keeps_its_entry_commission(world):
    world.fake.commission_per_lot = 0.1
    first = started(world)
    world.at(ny(DAY, 9, 41) + timedelta(seconds=3))
    first.cycle()
    (ticket,) = world.fake.positions
    second = started(world, t=ny(DAY, 10, 20))
    second.cycle()
    world.set_tick(104.0, 104.2)
    world.at(ny(DAY, 15, 55) + timedelta(seconds=3))
    second.cycle()
    (trade,) = world.csv("trades.csv")
    assert float(trade["money"]) == pytest.approx(position_net(world, ticket))


# --- #18 risk settings are validated before the start ----------------------------------------------


@pytest.mark.parametrize("risk", [0.0, -0.25, math.nan, math.inf, 2.5])
def test_18_bad_risk_is_refused(risk):
    with pytest.raises(ValueError, match="risk"):
        BotConfig(risk_percent=risk)


@pytest.mark.parametrize("stop", [math.inf, 6.0])
def test_18_bad_daily_stop_is_refused(stop):
    with pytest.raises(ValueError, match="daily stop"):
        BotConfig(guard=GuardConfig(daily_stop_percent=stop))


@pytest.mark.parametrize("balance", [0.0, -1.0, math.nan, math.inf])
def test_18_bad_balance_override_is_refused(balance):
    with pytest.raises(ValueError, match="balance"):
        BotConfig(initial_balance=balance)


def test_18_limits_are_the_ui_limits():
    assert live_model.MAX_RISK_PERCENT == bot_module.MAX_RISK_PERCENT
    assert live_model.MAX_DAILY_STOP_PERCENT == bot_module.MAX_DAILY_STOP_PERCENT


@pytest.mark.parametrize(
    "argv", [["--risk", "nan"], ["--risk", "0"], ["--daily-stop", "inf"], ["--balance", "-5"]]
)
def test_18_cli_refuses_before_anything_starts(monkeypatch, argv):
    def never(*a, **k):
        raise AssertionError("must not get this far")

    monkeypatch.setattr(bot_module, "load_trading_settings", never)
    monkeypatch.setattr(bot_module, "load_credentials", never)
    assert bot_module.main(argv) == 2


# --- #19 an incomplete cached day is repaired after the catch-up -----------------------------------


def test_19_a_day_cached_from_stale_history_is_rewritten_after_the_catch_up(world):
    bot = started(world)
    nxt = DAY + timedelta(days=1)
    midnight = datetime(nxt.year, nxt.month, nxt.day, tzinfo=UTC)
    new = [row(midnight + timedelta(minutes=i), 100, 100, 100, 100) for i in range(10)]
    full = history_rows() + today_rows() + new
    stale = [r for r in full if r[0] <= int(ny(DAY, 9, 50).timestamp())]
    world.fake.set_rates(BROKER, M1, stale)
    cycle_at = midnight + timedelta(minutes=5, seconds=3)
    world.at(cycle_at)
    bot.cycle()
    path = cache_path(world.out.parent / "cache_mt5", SYM, DAY)
    assert len(read_cached_day(path)) < len(today_rows())  # written short at midnight
    world.fake.set_rates(BROKER, M1, full)
    world.at(cycle_at + timedelta(minutes=1))
    bot.cycle()
    day_candles = [c for c in bot.symbols[SYM].candles if c.ts.date() == DAY]
    assert len(read_cached_day(path)) == len(day_candles) == len(today_rows())


# --- #20 a failing adoption query keeps the unresolved orders --------------------------------------


def test_20_a_failing_lookup_keeps_every_unresolved_order(world, monkeypatch):
    bot = make(world)
    state = lose_answers(world, "none", execute=False)
    cycle(world, bot, 9, 41)
    (item,) = bot.unclear
    bot.unclear.append(dataclasses.replace(item, comment="orb other"))

    def boom(*a, **k):
        raise RuntimeError("terminal hiccup")

    monkeypatch.setattr(bot_module, "own_positions", boom)
    cycle(world, bot, 9, 42)
    assert len(bot.unclear) == 2 and labels(world, "error")
    monkeypatch.setattr(bot_module, "own_positions", orders.own_positions)
    state["real"](state["held"][0])  # the server executed the first one after all
    cycle(world, bot, 9, 43)
    assert len(bot.by_ticket) == 1 and len(bot.unclear) == 1
