"""The account's initial balance for the FTMO 10 % max-loss check (user, 2026-10-17).

Read at start from the first balance deal of the account; `BotConfig.initial_balance`
(`--balance`) overrides it; with neither the bot refuses to start.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest
from fake_bot_mt5 import Deal2
from test_bot import DAY, World, ny

from backtester.live import orders


@pytest.fixture(autouse=True)
def fast_confirm(monkeypatch):
    monkeypatch.setattr(orders, "CONFIRM_INTERVAL_S", 0.0)


def balance_deal(world: World, ticket: int, amount: float, when: int) -> None:
    world.fake.deals[ticket] = Deal2(
        ticket, 0, 0, "", world.fake.DEAL_TYPE_BALANCE, 0.0, 0.0, 0, 0, amount, 0.0, 0.0, 0.0, when
    )


def fresh(tmp_path, balance_deals=((900, 100_000.0, 1000),)) -> World:
    w = World(tmp_path)
    del w.fake.deals[900]  # World's default first deal
    for ticket, amount, when in balance_deals:
        balance_deal(w, ticket, amount, when)
    w.at(ny(DAY, 9, 38))
    return w


def status_of(world: World) -> dict:
    return json.loads((world.out / "status.json").read_text(encoding="utf-8"))


def test_first_balance_deal_is_the_initial_balance(tmp_path):
    # the later deposit (id 5, time 5000) comes first in the dict but is not the first in time
    w = fresh(tmp_path, ((5, 25_000.0, 5000), (900, 100_000.0, 1000)))
    bot = w.bot()
    bot.connect()
    bot.resolve_initial_balance()
    assert bot.initial_balance == 100_000.0
    bot.publish()
    s = status_of(w)
    assert s["initial_balance"] == 100_000.0 and s["guard"]["initial_balance"] == 100_000.0


def test_override_wins(tmp_path):
    w = fresh(tmp_path)
    bot = w.bot(initial_balance=50_000.0)
    bot.connect()
    bot.resolve_initial_balance()
    assert bot.initial_balance == 50_000.0


def test_missing_balance_deal_refuses_to_start(tmp_path):
    w = fresh(tmp_path, balance_deals=())
    bot = w.bot()
    assert bot.run() == 1
    assert w.fake.requests == []
    refused = [d for d in w.decisions() if d["label"] == "refused"]
    assert refused and "initial balance" in refused[0]["request"]["error"].lower()
    assert "--balance" in refused[0]["request"]["error"]


def test_missing_balance_deal_is_fine_with_the_override(tmp_path):
    w = fresh(tmp_path, balance_deals=())
    bot = w.bot(initial_balance=100_000.0)
    bot.connect()
    bot.resolve_initial_balance()
    assert bot.initial_balance == 100_000.0


def test_max_loss_uses_the_read_balance(tmp_path):
    # started with 110,000: the FTMO floor is 99,000; equity 98,900 breaches it although the
    # day's loss is only 1.1 %
    w = fresh(tmp_path, ((900, 110_000.0, 1000),))
    bot = w.bot()
    bot.connect()
    bot.resolve_initial_balance()
    bot.start()
    w.fake.equity = 98_900.0
    w.at(ny(DAY, 9, 39) + timedelta(seconds=3))
    assert bot.cycle() == "stop"
    assert any("max loss" in str(d["request"]) for d in w.decisions())
