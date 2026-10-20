"""A lost or unclear order_send result (ROADMAP 13.5): look the position up by its comment
(own MAGIC only) before calling the order rejected; adopt what is found into management."""

from __future__ import annotations

import pytest
from fake_mt5 import Position
from test_bot import BROKER, World
from test_loop_safety import cycle, labels, make
from test_status import Notes

from backtester.live import bot as bot_module
from backtester.live import orders
from backtester.live.orders import MAGIC
from backtester.live.telegram import format_event


@pytest.fixture(autouse=True)
def fast_confirm(monkeypatch):
    monkeypatch.setattr(orders, "CONFIRM_INTERVAL_S", 0.0)


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def lose_answers(world, mode="none", execute=True):
    """order_send of an open: executed on the server (`execute`), but the bot gets no result
    (`mode` "none") or a 'processing error' result ("error")."""
    real = world.fake.order_send
    state = {"on": True, "held": []}

    def send(request):
        if not state["on"] or "position" in request:
            return real(request)
        if execute:
            result = real(request)
        else:
            world.fake.requests.append(dict(request))
            state["held"].append(dict(request))
            result = None
        if mode == "none":
            return None
        return result._replace(retcode=10011, deal=0, order=0)

    world.fake.order_send = send
    state["real"] = real
    return state


def test_an_open_with_no_result_is_adopted_and_exited_at_1555(world):
    notes = Notes()
    bot = make(world, notifier=notes)
    lose_answers(world, "none")
    cycle(world, bot, 9, 41)
    (ticket,) = world.fake.positions
    assert ticket in bot.by_ticket
    assert [d for d in labels(world, "skip")] == []
    assert any(k == "order_adopted" for k, _ in notes.events)
    assert world.csv("paper.csv")[0]["status"] == "filled"
    cycle(world, bot, 15, 55)
    assert world.fake.positions == {} and len(world.closes()) == 1
    assert len(world.csv("trades.csv")) == 1


def test_an_unclear_retcode_with_an_executed_order_is_adopted_too(world):
    bot = make(world)
    lose_answers(world, "error")
    cycle(world, bot, 9, 41)
    (ticket,) = world.fake.positions
    assert bot.by_ticket[ticket].sl == 97.5  # the SL known from the position / the order
    cycle(world, bot, 15, 55)
    assert world.fake.positions == {}


def test_a_clear_rejection_without_a_position_is_still_a_skip(world):
    bot = make(world)
    world.fake.reject[(world.fake.TRADE_ACTION_DEAL, None)] = world.fake.TRADE_RETCODE_MARKET_CLOSED
    cycle(world, bot, 9, 41)
    assert bot.unclear == []
    assert "order rejected" in labels(world, "skip")[0]["request"]["reason"]


def test_a_position_that_shows_up_later_is_adopted_on_a_later_cycle(world):
    bot = make(world)
    state = lose_answers(world, "none", execute=False)
    cycle(world, bot, 9, 41)
    assert world.fake.positions == {} and len(bot.unclear) == 1
    assert labels(world, "skip") == []  # not judged yet
    state["real"](state["held"][0])  # the server executed it after all
    cycle(world, bot, 9, 42)
    (ticket,) = world.fake.positions
    assert ticket in bot.by_ticket and bot.unclear == []
    cycle(world, bot, 15, 55)
    assert world.fake.positions == {} and len(world.csv("trades.csv")) == 1


def test_an_order_that_never_appears_is_skipped_after_the_rechecks(world):
    notes = Notes()
    bot = make(world, notifier=notes, adopt_recheck_cycles=2)
    lose_answers(world, "none", execute=False)
    cycle(world, bot, 9, 41)
    cycle(world, bot, 9, 42)
    assert len(bot.unclear) == 1
    cycle(world, bot, 9, 43)
    assert bot.unclear == []
    (skip,) = labels(world, "skip")
    assert "unclear" in skip["request"]["reason"]
    assert world.csv("paper.csv")[0]["status"] == "skipped"
    assert any(k == "order_unclear" for k, _ in notes.events)


def test_a_position_of_the_user_with_the_same_comment_is_not_adopted(world):
    bot = make(world)
    state = lose_answers(world, "none", execute=False)
    cycle(world, bot, 9, 41)
    comment = state["held"][0]["comment"]
    world.fake.positions[7] = Position(7, BROKER, 0, 1.0, 100.0, 0.0, 0.0, MAGIC + 1, comment, 0)
    cycle(world, bot, 9, 42)
    assert bot.by_ticket == {}


def test_an_error_after_the_order_was_sent_still_adopts_the_position(world, monkeypatch):
    bot = make(world)

    def boom(*a, **k):
        raise RuntimeError("terminal hiccup")

    monkeypatch.setattr(bot_module, "confirm_open", boom)
    cycle(world, bot, 9, 41)
    (ticket,) = world.fake.positions
    assert ticket in bot.by_ticket
    assert labels(world, "error")
    cycle(world, bot, 15, 55)
    assert world.fake.positions == {}


def test_telegram_texts_for_unclear_orders():
    assert format_event("order_adopted", {"symbol": "US500", "ticket": 5})
    assert format_event("order_unclear", {"symbol": "US500", "retcode": "no result"})


def test_recheck_budget_is_a_config_value(world):
    assert make(world, adopt_recheck_cycles=7).config.adopt_recheck_cycles == 7
