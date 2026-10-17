"""status.json: strategy, risk, pause, session window and the setup per symbol (ROADMAP 7.3)."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

import pytest
from test_bot import DAY, SYM, World, ny
from test_status import make, minute, status_of

from backtester.live import orders
from backtester.live.status import STRATEGY_NAME, session_window
from backtester.strategy.opening_range.config import SessionSpec

NY_SPEC = SessionSpec("America/New_York", time(9, 30), time(15, 55))


@pytest.fixture(autouse=True)
def fast_confirm(monkeypatch):
    monkeypatch.setattr(orders, "CONFIRM_INTERVAL_S", 0.0)


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def utc(y, m, d, hh, mm) -> datetime:
    return datetime(y, m, d, hh, mm, tzinfo=UTC)


# --- session_window ----------------------------------------------------------------------------


def test_inside_the_window():
    s = session_window(utc(2026, 1, 14, 15, 0), "New York", NY_SPEC)  # 10:00 New York, Wednesday
    assert s == {
        "name": "New York",
        "open_utc": utc(2026, 1, 14, 14, 30).isoformat(),
        "close_utc": utc(2026, 1, 14, 20, 55).isoformat(),
        "is_open": True,
    }


def test_exactly_at_open_and_close_is_open():
    assert session_window(utc(2026, 1, 14, 14, 30), "NY", NY_SPEC)["is_open"] is True
    assert session_window(utc(2026, 1, 14, 20, 55), "NY", NY_SPEC)["is_open"] is True
    assert session_window(utc(2026, 1, 14, 20, 56), "NY", NY_SPEC)["is_open"] is False


def test_before_the_open_gives_todays_window_not_open():
    s = session_window(utc(2026, 1, 14, 13, 0), "NY", NY_SPEC)
    assert s["is_open"] is False and s["open_utc"] == utc(2026, 1, 14, 14, 30).isoformat()


def test_after_the_close_gives_the_next_day():
    s = session_window(utc(2026, 1, 14, 21, 30), "NY", NY_SPEC)
    assert s["is_open"] is False and s["open_utc"] == utc(2026, 1, 15, 14, 30).isoformat()


def test_friday_after_close_and_weekend_give_monday():
    for now in (utc(2026, 1, 16, 21, 30), utc(2026, 1, 17, 12, 0), utc(2026, 1, 18, 23, 0)):
        s = session_window(now, "NY", NY_SPEC)
        assert s["open_utc"] == utc(2026, 1, 19, 14, 30).isoformat() and not s["is_open"]


def test_dst_switch_in_march_and_november():
    # US DST 2026 starts Sunday 8 March: Friday close 15:55 EST, Monday open 09:30 EDT
    s = session_window(utc(2026, 3, 6, 21, 0), "NY", NY_SPEC)
    assert s["open_utc"] == utc(2026, 3, 9, 13, 30).isoformat()
    assert s["close_utc"] == utc(2026, 3, 9, 19, 55).isoformat()
    # it ends Sunday 1 November: Friday still EDT, Monday EST
    s = session_window(utc(2026, 10, 30, 21, 0), "NY", NY_SPEC)
    assert s["open_utc"] == utc(2026, 11, 2, 14, 30).isoformat()


def test_window_is_in_utc():
    s = session_window(utc(2026, 1, 14, 15, 0), "NY", NY_SPEC)
    assert datetime.fromisoformat(s["open_utc"]).utcoffset() == timedelta(0)


# --- the new status fields ---------------------------------------------------------------------


def test_new_top_level_fields(world):
    make(world)
    s = status_of(world)
    assert s["paused"] is False and s["risk_percent"] == 0.25
    assert s["strategy"] == STRATEGY_NAME == "Opening-range breakout"
    assert s["session"]["name"] == "New York"
    assert s["session"]["open_utc"] == ny(DAY, 9, 30).isoformat()
    assert s["session"]["close_utc"] == ny(DAY, 15, 55).isoformat()
    assert s["session"]["is_open"] is True  # 09:38 New York


def test_setup_stages_over_the_day(world):
    bot = make(world)  # 09:38, warmed up with the bars up to 09:37
    minute(world, bot, 9, 39)
    st = status_of(world)["setups"][SYM]
    assert st["stage"] == "waiting_breakout"
    assert st["detail"] == "range 97.5-102.5"
    assert datetime.fromisoformat(st["time"]).tzinfo is not None
    minute(world, bot, 9, 41)  # the breakout fills
    st = status_of(world)["setups"][SYM]
    assert st["stage"] == "entered" and "buy" in st["detail"]
    world.at(ny(DAY, 15, 55) + timedelta(seconds=3))
    bot.cycle()
    assert status_of(world)["setups"][SYM]["stage"] == "done"
    world.at(ny(DAY, 16, 30))
    bot.cycle()
    assert status_of(world)["setups"][SYM]["stage"] == "done"


def test_waiting_session_before_the_open(world):
    world.at(ny(DAY, 8, 0))
    bot = world.bot()
    bot.connect()
    bot.start()
    assert status_of(world)["setups"][SYM]["stage"] == "waiting_session"
    assert status_of(world)["session"]["is_open"] is False


def test_stage_time_changes_only_with_the_stage(world):
    bot = make(world)
    minute(world, bot, 9, 39)
    first = status_of(world)["setups"][SYM]["time"]
    minute(world, bot, 9, 40)
    assert status_of(world)["setups"][SYM]["time"] == first


def test_no_secret_in_the_status_with_the_new_fields(world):
    bot = make(world)
    minute(world, bot, 9, 41)
    text = (world.out / "status.json").read_text(encoding="utf-8").lower()
    assert "password" not in text and "token" not in text
