"""Pause file results/live/PAUSE (ROADMAP 7.3): no new entries, everything else keeps running."""

from __future__ import annotations

from datetime import timedelta

import pytest
from test_bot import DAY, World, ny
from test_status import Notes, make, status_of

from backtester.live import orders
from backtester.live.bot import BotConfig
from backtester.live.telegram import format_event


@pytest.fixture(autouse=True)
def fast_confirm(monkeypatch):
    monkeypatch.setattr(orders, "CONFIRM_INTERVAL_S", 0.0)


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def cycle(world, bot, hh, mm):
    world.at(ny(DAY, hh, mm) + timedelta(seconds=3))
    return bot.cycle()


def pause(world, on=True):
    world.out.mkdir(parents=True, exist_ok=True)
    f = world.out / "PAUSE"
    if on:
        f.write_text("")
    else:
        f.unlink()


def test_pause_file_is_a_config_property(tmp_path):
    assert BotConfig(out_dir=tmp_path).pause_file == tmp_path / "PAUSE"


def test_entry_is_skipped_while_paused(world):
    bot = make(world)
    pause(world)
    assert cycle(world, bot, 9, 41) == "continue"
    assert world.opens() == []
    s = status_of(world)
    assert s["paused"] is True
    assert [(x["status"], x["reason"]) for x in s["signals"]] == [("skipped", "paused")]
    assert world.csv("paper.csv")[0]["reason"] == "paused"


def test_open_trade_still_exits_while_paused(world):
    bot = make(world)
    cycle(world, bot, 9, 41)
    assert len(world.opens()) == 1
    pause(world)
    cycle(world, bot, 9, 45)
    cycle(world, bot, 15, 55)
    assert world.fake.positions == {} and len(world.closes()) == 1
    assert len(world.csv("trades.csv")) == 1


def test_server_side_stop_is_still_reported_while_paused(world):
    bot = make(world)
    cycle(world, bot, 9, 41)
    (ticket,) = world.fake.positions
    pause(world)
    world.fake.stop_out(ticket, 97.5, world.fake.DEAL_REASON_SL)
    cycle(world, bot, 9, 43)
    assert world.csv("trades.csv")[0]["exit_reason"] == "stop_loss"


def test_deleting_the_file_resumes_and_both_changes_are_noted_once(world):
    notes = Notes()
    bot = make(world, notifier=notes)
    pause(world)
    cycle(world, bot, 9, 38)
    cycle(world, bot, 9, 39)  # still paused: no second note
    pause(world, on=False)
    cycle(world, bot, 9, 40)
    cycle(world, bot, 9, 41)
    assert len(world.opens()) == 1
    kinds = [k for k, _ in notes.events]
    assert kinds.count("paused") == 1 and kinds.count("unpaused") == 1
    assert status_of(world)["paused"] is False


def test_stop_file_still_works_while_paused(world):
    bot = make(world)
    pause(world)
    cycle(world, bot, 9, 39)
    (world.out / "STOP").write_text("")
    assert cycle(world, bot, 9, 40) == "stop"


def test_emergency_file_still_works_while_paused(world):
    bot = make(world)
    cycle(world, bot, 9, 41)
    pause(world)
    (world.out / "EMERGENCY").write_text("")
    assert cycle(world, bot, 9, 42) == "stop"
    assert world.fake.positions == {}


def test_daily_guard_still_runs_while_paused(world):
    bot = make(world)
    cycle(world, bot, 9, 41)
    pause(world)
    world.fake.equity = 97_800.0
    cycle(world, bot, 9, 42)
    assert bot.blocked and world.fake.positions == {}


def test_telegram_texts_for_pause_events():
    assert "no new entries" in format_event("paused", {}).lower()
    assert "resum" in format_event("unpaused", {}).lower()
