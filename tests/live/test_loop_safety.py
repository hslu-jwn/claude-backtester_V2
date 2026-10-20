"""Loop safety net, emergency order and close-until-flat (ROADMAP 13.1, 13.2, 13.3).

Same world as test_bot.py (fake MT5, hand-built bars). Nothing here touches a terminal.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from test_bot import BROKER, DAY, World, ny
from test_status import Notes

from backtester.live import bot as bot_module
from backtester.live import orders
from backtester.live.bot import Bot, BotConfig
from backtester.live.orders import DemoLockError
from backtester.live.telegram import format_event
from backtester.risk.prop_rules import GuardConfig


@pytest.fixture(autouse=True)
def fast_confirm(monkeypatch):
    monkeypatch.setattr(orders, "CONFIRM_INTERVAL_S", 0.0)


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def make(world: World, notifier=None, **kw) -> Bot:
    world.at(ny(DAY, 9, 38))
    bot = Bot(
        world.config(**kw), world.fake, world.settings,
        now=world.clock, sleep=world.clock.sleep, notifier=notifier,
    )  # fmt: skip
    bot.connect()
    bot.start()
    return bot


def cycle(world, bot, hh, mm):
    world.at(ny(DAY, hh, mm) + timedelta(seconds=3))
    return bot.cycle()


def labels(world, label):
    return [d for d in world.decisions() if d["label"] == label]


def block_closes(world, blocked=True):
    """order_send returns None (a lost answer) for every close request while `blocked`."""
    real = world.fake.order_send
    state = {"on": blocked}

    def send(request):
        if state["on"] and "position" in request:
            world.fake.requests.append(dict(request))
            return None
        return real(request)

    world.fake.order_send = send
    return state


def request_file(world, name):
    world.out.mkdir(parents=True, exist_ok=True)
    (world.out / name).write_text("")


# --- 13.1 loop safety net ------------------------------------------------------------------


def test_new_tunables_have_defaults():
    cfg = BotConfig()
    assert cfg.error_repeat_s == 300.0 and cfg.error_persist_cycles == 5
    assert cfg.close_attempts == 3 and cfg.close_retry_first_s == 1.0
    assert cfg.close_retry_factor == 2.0 and cfg.close_retry_max_s == 10.0
    assert cfg.adopt_recheck_cycles == 3


def test_a_missing_tick_at_entry_is_reported_and_the_loop_goes_on(world):
    notes = Notes()
    bot = make(world, notifier=notes)
    world.fake.ticks.pop(BROKER)  # symbol_info_tick() -> None: market_order raises
    assert cycle(world, bot, 9, 41) == "continue"
    assert world.fake.positions == {}
    assert [e for e in notes.events if e[0] == "error"]
    assert [d for d in labels(world, "skip") if "error" in d["request"]["reason"]]


def test_a_sizer_error_at_entry_is_reported_and_the_loop_goes_on(world, monkeypatch):
    notes = Notes()
    bot = make(world, notifier=notes)

    def boom(*a, **k):
        raise ValueError("risk must be positive")

    monkeypatch.setattr(bot_module, "lots_for_risk", boom)
    assert cycle(world, bot, 9, 41) == "continue"
    assert world.opens() == []
    (event,) = [f for k, f in notes.events if k == "error"]
    assert "ValueError" in event["what"]


def test_a_failed_session_exit_is_kept_and_retried_next_cycle(world):
    bot = make(world)
    cycle(world, bot, 9, 41)
    (ticket,) = world.fake.positions
    tick = world.fake.ticks.pop(BROKER)
    assert cycle(world, bot, 15, 55) == "continue"  # the exit raises inside: no crash
    assert list(world.fake.positions) == [ticket]
    world.fake.ticks[BROKER] = tick
    cycle(world, bot, 15, 56)
    assert world.fake.positions == {} and len(world.closes()) == 1
    assert len(world.csv("trades.csv")) == 1


def test_a_failing_guard_does_not_block_the_exit_of_an_open_position(world, monkeypatch):
    bot = make(world)
    cycle(world, bot, 9, 41)

    def boom():
        raise AttributeError("'NoneType' object has no attribute 'equity'")

    monkeypatch.setattr(bot, "_guard", boom)
    assert cycle(world, bot, 15, 55) == "continue"
    assert world.fake.positions == {}  # session exit still happened


def test_run_survives_persistent_errors_reports_rate_limited_and_still_exits(world, monkeypatch):
    notes = Notes()
    world.at(ny(DAY, 9, 38))
    bot = Bot(
        world.config(error_repeat_s=100_000.0, error_persist_cycles=5), world.fake,
        world.settings, now=world.clock, sleep=world.clock.sleep, notifier=notes,
    )  # fmt: skip

    def boom():
        raise RuntimeError("reconcile broke")

    monkeypatch.setattr(bot, "_reconcile", boom)

    def hook(clock):
        if clock.t >= ny(DAY, 16, 0):
            request_file(world, "STOP")

    world.clock.on_sleep = hook
    assert bot.run() == 0
    assert world.fake.positions == {} and len(world.closes()) == 1  # 15:55 exit happened
    assert len(labels(world, "error")) == 1  # identical errors: one report
    assert len(labels(world, "error_persistent")) == 1
    assert [k for k, _ in notes.events].count("error_persistent") == 1


def test_identical_errors_are_reported_again_after_the_window(world, monkeypatch):
    bot = make(world, error_repeat_s=600.0)

    def boom():
        raise RuntimeError("same")

    monkeypatch.setattr(bot, "_reconcile", boom)
    for minute in (50, 51, 52):
        cycle(world, bot, 9, minute)
    assert len(labels(world, "error")) == 1
    cycle(world, bot, 10, 5)
    again = labels(world, "error")
    assert len(again) == 2 and again[1]["request"]["repeats"] == 2


def test_the_streak_ends_with_a_clean_cycle(world, monkeypatch):
    bot = make(world, error_persist_cycles=3)
    calls = {"n": 0}
    real = bot._reconcile

    def flaky():
        calls["n"] += 1
        if calls["n"] in (1, 2, 4, 5):
            raise RuntimeError("x")
        real()

    monkeypatch.setattr(bot, "_reconcile", flaky)
    for minute in range(50, 55):
        cycle(world, bot, 9, minute)
    assert labels(world, "error_persistent") == []  # 2 + clean + 2: never 3 in a row


def test_a_demo_lock_error_still_ends_the_run(world, monkeypatch):
    world.at(ny(DAY, 9, 38))
    bot = world.bot()

    def lock():
        raise DemoLockError("refused: not a demo account")

    monkeypatch.setattr(bot, "_reconcile", lock)
    assert bot.run() == 1


def test_telegram_texts_for_the_new_events():
    assert "reconcile" in format_event("error_persistent", {"what": "reconcile", "cycles": 5})
    assert format_event("close_all_incomplete", {"left": 2, "label": "emergency"})


# --- 13.2 emergency before stop --------------------------------------------------------------


def test_emergency_wins_over_stop_in_the_same_cycle(world):
    bot = make(world)
    cycle(world, bot, 9, 41)
    assert len(world.fake.positions) == 1
    request_file(world, "STOP")
    request_file(world, "EMERGENCY")
    assert cycle(world, bot, 9, 42) == "stop"
    assert world.fake.positions == {} and len(world.closes()) == 1
    assert not (world.out / "STOP").exists() and not (world.out / "EMERGENCY").exists()


# --- 13.3 close until flat -------------------------------------------------------------------


def test_emergency_retries_inside_the_cycle_with_backoff(world):
    bot = make(world)
    cycle(world, bot, 9, 41)
    state = block_closes(world)
    before = len(world.clock.sleeps)
    world.clock.on_sleep = lambda c: state.update(on=len(world.clock.sleeps) - before < 2)
    request_file(world, "EMERGENCY")
    assert cycle(world, bot, 9, 42) == "stop"  # third attempt works
    assert world.fake.positions == {}
    assert world.clock.sleeps[before:] == [1.0, 2.0]


def test_emergency_does_not_stop_while_a_position_is_left_and_retries_each_cycle(world):
    notes = Notes()
    bot = make(world, notifier=notes)
    cycle(world, bot, 9, 41)
    state = block_closes(world)
    request_file(world, "EMERGENCY")
    assert cycle(world, bot, 9, 42) == "continue"  # three attempts failed
    assert len(world.fake.positions) == 1
    assert any(k == "close_all_incomplete" for k, _ in notes.events)
    assert cycle(world, bot, 9, 43) == "continue"
    assert len(world.opens()) == 1  # no new entry while closing everything
    state["on"] = False
    assert cycle(world, bot, 9, 44) == "stop"
    assert world.fake.positions == {}


def test_failed_closes_are_rate_limited_in_the_log(world):
    bot = make(world, error_repeat_s=100_000.0)
    cycle(world, bot, 9, 41)
    block_closes(world)
    request_file(world, "EMERGENCY")
    cycle(world, bot, 9, 42)
    cycle(world, bot, 9, 43)
    assert len(labels(world, "close_failed")) == 1


def test_ftmo_breach_keeps_closing_until_flat_then_stops(world):
    bot = make(world)
    cycle(world, bot, 9, 41)
    state = block_closes(world)
    world.fake.equity = 94_000.0
    assert cycle(world, bot, 9, 42) == "continue"
    assert len(world.fake.positions) == 1
    state["on"] = False
    assert cycle(world, bot, 9, 43) == "stop"
    assert world.fake.positions == {}


def test_daily_stop_retries_the_close_each_cycle_and_blocks_entries(world):
    bot = make(world, guard=GuardConfig())
    cycle(world, bot, 9, 41)
    state = block_closes(world)
    world.fake.equity = 97_800.0
    assert cycle(world, bot, 9, 42) == "continue"
    assert bot.blocked and len(world.fake.positions) == 1
    state["on"] = False
    assert cycle(world, bot, 9, 43) == "continue"
    assert world.fake.positions == {}
    assert cycle(world, bot, 9, 44) == "continue"  # flat: no further closes
