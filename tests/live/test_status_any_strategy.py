"""status.json for every bot strategy (audit 2026-11-02, R1): the fill-probe run of 2026-10-27..31
never wrote its status because `build_status` asked every strategy for opening-range-only parts
(sessions, setup_state); `publish` hid the error, so the Live page showed "not running"."""

from __future__ import annotations

import json

import pytest
from test_bot import DAY, World, ny
from test_status import SECRETS

from backtester.live import orders
from backtester.live import status as status_module
from backtester.live.bot import Bot
from backtester.live.status import STRATEGY_NAME
from backtester.strategy.fill_probe.config import FillProbeConfig


@pytest.fixture(autouse=True)
def fast_confirm(monkeypatch):
    monkeypatch.setattr(orders, "CONFIRM_INTERVAL_S", 0.0)


def started(world: World, **kw) -> Bot:
    world.at(ny(DAY, 9, 38))
    bot = Bot(
        world.config(**kw),
        world.fake,
        world.settings,
        credentials=SECRETS,
        now=world.clock,
        sleep=world.clock.sleep,
    )
    bot.connect()
    bot.start()
    return bot


def status_of(world: World) -> dict:
    return json.loads((world.out / "status.json").read_text(encoding="utf-8"))


def test_fill_probe_bot_writes_its_status(tmp_path):
    world = World(tmp_path)
    started(world, strategy_name="fill_probe", strategy=FillProbeConfig(), comment_prefix="fp")
    s = status_of(world)
    assert s["running"] is True and s["connected"] is True
    assert s["heartbeat"] == ny(DAY, 9, 38).isoformat()
    assert s["strategy"] == "fill_probe"
    assert s["session"] is None and s["setups"] == {}


def test_opening_range_status_keeps_its_name_session_and_setups(tmp_path):
    world = World(tmp_path)
    started(world)
    s = status_of(world)
    assert s["strategy"] == STRATEGY_NAME
    assert s["session"] is not None and set(s["setups"]) == {*world.config().symbols}


def test_a_failed_status_is_reported_once_and_never_stops_the_bot(tmp_path, monkeypatch, capsys):
    world = World(tmp_path)
    bot = started(world)
    capsys.readouterr()

    def broken(_bot, _now):
        raise AttributeError("no sessions")

    monkeypatch.setattr("backtester.live.bot.build_status", broken)
    bot.publish()
    bot.publish()
    err = capsys.readouterr().err
    assert err.count("status") == 1 and "AttributeError: no sessions" in err

    monkeypatch.setattr("backtester.live.bot.build_status", status_module.build_status)
    bot.publish()  # works again: a later, different failure is reported again
    monkeypatch.setattr("backtester.live.bot.build_status", broken)
    bot.publish()
    assert capsys.readouterr().err.count("status") == 1
