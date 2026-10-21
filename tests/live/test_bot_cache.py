"""Bot data for the chart (ROADMAP 7.8): finished days into the MT5 cache, today's bars into the
live cache, the background cache update. Fake MT5 world of test_bot.py, tmp cache folders."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta

import pytest
from test_bot import BROKER, DAY, World, history_rows, ny, today_rows
from test_status import Notes

from backtester.data.cache import (
    COLUMNS,
    LIVE_CACHE_DIR,
    MT5_CACHE_DIR,
    cache_path,
    read_cached_day,
)
from backtester.live import bot as bot_module
from backtester.live import orders
from backtester.live.bot import Bot, BotConfig
from backtester.live.detached import spawn_detached

SYM = "US500"


@pytest.fixture(autouse=True)
def fast_confirm(monkeypatch):
    monkeypatch.setattr(orders, "CONFIRM_INTERVAL_S", 0.0)


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def mt5_file(world, day):
    return cache_path(world.out.parent / "cache_mt5", SYM, day)


def live_file(world, day):
    return cache_path(world.out.parent / "cache_live", SYM, day)


def started(world, spawn=None, **kw) -> Bot:
    world.at(ny(DAY, 9, 38))
    extra = {} if spawn is None else {"spawn": spawn}
    bot = Bot(
        world.config(**kw), world.fake, world.settings,
        now=world.clock, sleep=world.clock.sleep, **extra,
    )  # fmt: skip
    bot.connect()
    bot.start()
    return bot


def cycle(world, bot, t):
    world.at(t + timedelta(seconds=3))
    return bot.cycle()


def utc_days(bot):
    return {c.ts.date() for c in bot.symbols[SYM].candles}


def events(world, kind):
    return [d for d in world.decisions() if d["label"] == kind]


def test_defaults():
    cfg = BotConfig()
    assert cfg.mt5_cache_dir == MT5_CACHE_DIR and cfg.live_cache_dir == LIVE_CACHE_DIR
    assert cfg.update_cache_at_start is True
    assert cfg.update_log_name == "update_stdout.log"


def test_complete_days_written_first_and_today_not(world):
    bot = started(world)
    days = utc_days(bot)
    first = min(days)
    expected = days - {first, DAY}
    assert len(expected) >= 10
    for day in expected:
        frame = read_cached_day(mt5_file(world, day))
        assert list(frame.columns) == COLUMNS and len(frame) > 0
        assert set(frame["ts"].dt.date) == {day}
    assert not mt5_file(world, first).exists()  # cut by the warm-up start
    assert not mt5_file(world, DAY).exists()
    (note,) = events(world, "cache_days")
    assert (
        note["request"]["symbol"] == SYM and note["request"]["written"] == (DAY - first).days - 1
    )  # + empty hole days


def test_existing_day_file_is_not_overwritten(world):
    day = sorted(utc_days(started(world)))[1]
    path = mt5_file(world, day)
    path.write_bytes(b"sentinel")
    started(world)  # a second start (restart) sees the file and leaves it
    assert path.read_bytes() == b"sentinel"


def test_todays_bars_go_to_live_cache_and_are_rewritten(world):
    bot = started(world)
    before = read_cached_day(live_file(world, DAY))
    assert len(before) > 0 and set(before["ts"].dt.date) == {DAY}
    assert list(before.columns) == COLUMNS
    cycle(world, bot, ny(DAY, 9, 41))
    after = read_cached_day(live_file(world, DAY))
    assert len(after) > len(before)
    assert after["ts"].iloc[-1] == bot.symbols[SYM].candles[-1].ts


def test_day_change_moves_yesterday_to_the_mt5_cache(world):
    bot = started(world)
    assert not mt5_file(world, DAY).exists()
    nxt = DAY + timedelta(days=1)
    start = datetime(nxt.year, nxt.month, nxt.day, 0, 0, tzinfo=UTC)
    new = [(int((start + timedelta(minutes=i)).timestamp()), 100, 100, 100, 100, 20)
           for i in range(5)]  # fmt: skip
    rows = history_rows() + today_rows() + new
    world.fake.set_rates(BROKER, world.fake.TIMEFRAME_M1, rows)
    cycle(world, bot, start + timedelta(minutes=5))
    today_candles = [c for c in bot.symbols[SYM].candles if c.ts.date() == DAY]
    assert len(read_cached_day(mt5_file(world, DAY))) == len(today_candles) > 0
    assert len(read_cached_day(live_file(world, nxt))) == 5


def test_no_candles_nothing_written(world):
    world.fake.set_rates(BROKER, world.fake.TIMEFRAME_M1, [])
    bot = started(world)
    cycle(world, bot, ny(DAY, 9, 41))
    assert not (world.out.parent / "cache_mt5").exists()
    assert not (world.out.parent / "cache_live").exists()


def test_no_new_candles_no_rewrite(world):
    bot = started(world)
    path = live_file(world, DAY)
    path.write_bytes(b"marker")
    world.at(ny(DAY, 9, 38) + timedelta(seconds=5))  # same minute: nothing new
    bot.cycle()
    assert path.read_bytes() == b"marker"


def test_write_error_does_not_stop_the_cycle(world, monkeypatch):
    bot = started(world)

    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(bot_module, "write_atomic", boom)
    assert cycle(world, bot, ny(DAY, 9, 41)) == "continue"
    assert len(world.opens()) == 1  # the 09:40 breakout was still traded
    assert any("cache US500" in e["request"]["what"] for e in events(world, "error"))
    monkeypatch.undo()
    cycle(world, bot, ny(DAY, 9, 42))  # recovers: the live file is written again
    assert live_file(world, DAY).exists()


def test_update_spawned_once_at_start(world):
    calls = []
    bot = started(
        world, spawn=lambda cmd, log: calls.append((cmd, log)), update_cache_at_start=True
    )
    cycle(world, bot, ny(DAY, 9, 41))
    assert calls == [
        ([sys.executable, "-m", "backtester.tools.update_data"], world.out / "update_stdout.log")
    ]
    assert events(world, "update_started")


def test_update_can_be_switched_off(world):
    calls = []
    started(world, spawn=lambda cmd, log: calls.append(cmd), update_cache_at_start=False)
    assert calls == []


def test_update_spawn_failure_is_only_noted(world):
    def fail(cmd, log):
        raise OSError("no process")

    bot = started(world, spawn=fail, update_cache_at_start=True)
    assert events(world, "update_failed")
    assert cycle(world, bot, ny(DAY, 9, 41)) == "continue"
    assert len(world.opens()) == 1


def test_notifier_gets_the_cache_event_without_trouble(world):
    notes = Notes()
    world.at(ny(DAY, 9, 38))
    bot = Bot(
        world.config(), world.fake, world.settings,
        now=world.clock, sleep=world.clock.sleep, notifier=notes,
    )  # fmt: skip
    bot.connect()
    bot.start()
    assert any(kind == "cache_days" for kind, _ in notes.events)


def test_spawn_detached_creates_the_log_folder(tmp_path, monkeypatch):
    seen = {}

    def fake_popen(cmd, **kw):
        seen["cmd"] = cmd
        return object()

    monkeypatch.setattr("backtester.live.detached.subprocess.Popen", fake_popen)
    spawn_detached(["echo", "x"], tmp_path / "a" / "log.txt")
    assert (tmp_path / "a").is_dir() and "echo" in seen["cmd"]


def test_days_without_candles_get_an_empty_file(world):
    bot = started(world)
    days = utc_days(bot)
    first = min(days)
    holes = [
        first + timedelta(days=i)
        for i in range(1, (DAY - first).days)
        if first + timedelta(days=i) not in days
    ]
    assert holes  # the fake history has weekends
    for day in holes:
        frame = read_cached_day(mt5_file(world, day))
        assert len(frame) == 0 and list(frame.columns) == COLUMNS
    assert not mt5_file(world, first).exists() and not mt5_file(world, DAY).exists()


def test_existing_hole_file_is_untouched(world):
    bot = started(world)
    days = utc_days(bot)
    first = min(days)
    hole = next(
        first + timedelta(days=i) for i in range(1, 30) if first + timedelta(days=i) not in days
    )
    mt5_file(world, hole).write_bytes(b"sentinel")
    started(world)
    assert mt5_file(world, hole).read_bytes() == b"sentinel"
