"""results/live/status.json (ROADMAP 7.2 monitoring): what the bot writes for the /live page."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from test_bot import DAY, SYM, World, ny

from backtester.live import orders
from backtester.live.bot import Bot
from backtester.live.credentials import Credentials
from backtester.live.status import (
    STALE_S,
    heartbeat_age_s,
    read_status,
    summary_text,
    write_status,
)

SECRETS = Credentials("51234567", "pw-s3cr3t-XYZ", "Broker-Demo7")


@pytest.fixture(autouse=True)
def fast_confirm(monkeypatch):
    monkeypatch.setattr(orders, "CONFIRM_INTERVAL_S", 0.0)


class Notes:
    """A notifier that records events (the Bot only needs `.event` and `.notify`)."""

    def __init__(self):
        self.events, self.texts = [], []

    def event(self, kind, fields):
        self.events.append((kind, fields))

    def notify(self, text):
        self.texts.append(text)


def make(world: World, **kw) -> Bot:
    world.at(ny(DAY, 9, 38))
    bot = Bot(
        world.config(),
        world.fake,
        world.settings,
        credentials=SECRETS,
        now=world.clock,
        sleep=world.clock.sleep,
        **kw,
    )
    bot.connect()
    bot.start()
    return bot


def status_of(world: World) -> dict:
    return json.loads((world.out / "status.json").read_text(encoding="utf-8"))


@pytest.fixture
def world(tmp_path):
    return World(tmp_path)


def minute(world, bot, hh, mm):
    world.at(ny(DAY, hh, mm) + timedelta(seconds=3))
    return bot.cycle()


def test_status_has_the_fields_after_start(world):
    make(world)
    s = status_of(world)
    assert s["connected"] is True and s["account_mode"] == "DEMO" and s["running"] is True
    assert s["balance"] == pytest.approx(100_000.0) and s["equity"] == pytest.approx(100_000.0)
    assert s["guard"]["state"] == "ok"
    assert s["guard"]["daily_stop_percent"] == 2.0 and s["guard"]["ftmo_daily_percent"] == 5.0
    assert s["positions"] == [] and s["signals"] == [] and s["last_error"] == ""
    assert s["heartbeat"].endswith("+00:00")
    assert {"day_pl", "day_pl_percent", "day_r", "date", "symbols"} <= set(s)


def test_each_cycle_refreshes_the_heartbeat(world):
    bot = make(world)
    first = status_of(world)["heartbeat"]
    minute(world, bot, 9, 39)
    assert status_of(world)["heartbeat"] > first


def test_fill_gives_an_open_position_and_a_signal(world):
    bot = make(world)
    minute(world, bot, 9, 41)
    s = status_of(world)
    (pos,) = s["positions"]
    assert pos["symbol"] == SYM and pos["side"] == "buy" and pos["sl"] == 97.5
    assert pos["entry"] == pytest.approx(103.2) and "floating_r" in pos
    assert [(x["symbol"], x["status"]) for x in s["signals"]] == [(SYM, "filled")]


def test_floating_r_follows_the_price(world):
    bot = make(world)
    minute(world, bot, 9, 41)
    world.set_tick(104.3, 104.5)  # long closes at the bid: +1.1 over risk 103.0 - 97.5 = 5.5
    minute(world, bot, 9, 42)
    assert status_of(world)["positions"][0]["floating_r"] == pytest.approx(0.2, abs=0.01)


def test_skip_is_listed_with_its_reason(world):
    world.fake.equity = 97_900.0  # daily stop
    bot = make(world)
    minute(world, bot, 9, 41)
    s = status_of(world)
    assert s["guard"]["state"] == "stopped" and s["guard"]["reason"]
    assert s["signals"][0]["status"] == "skipped" and "daily stop" in s["signals"][0]["reason"]
    assert s["day_pl_percent"] == pytest.approx(-2.1)


def test_closed_trade_counts_in_day_r(world):
    bot = make(world)
    minute(world, bot, 9, 41)
    world.at(ny(DAY, 15, 55) + timedelta(seconds=3))
    bot.cycle()
    s = status_of(world)
    (trade,) = world.csv("trades.csv")
    assert s["positions"] == [] and s["day_r"] == pytest.approx(float(trade["r_net"]), abs=1e-3)


def test_errors_are_kept_and_scrubbed(world):
    bot = make(world)
    bot.note("error", symbol=SYM, what=f"boom {SECRETS.password}")
    s = status_of(world)
    assert "boom" in s["last_error"]
    assert SECRETS.password not in json.dumps(s)


def test_no_secret_anywhere_in_the_status_file(world):
    bot = make(world)
    minute(world, bot, 9, 41)
    text = (world.out / "status.json").read_text(encoding="utf-8")
    for secret in SECRETS.secrets():
        assert secret not in text
    assert "token" not in text.lower() and "password" not in text.lower()


def test_stop_marks_not_running(world):
    bot = make(world)
    world.out.mkdir(parents=True, exist_ok=True)
    (world.out / "STOP").write_text("")
    assert bot.cycle() == "stop"
    bot.note("stopped")
    s = status_of(world)
    assert s["running"] is False


def test_events_go_to_the_notifier(world):
    notes = Notes()
    bot = make(world, notifier=notes)
    minute(world, bot, 9, 41)
    kinds = [k for k, _ in notes.events]
    assert {"connected", "signal", "order"} <= set(kinds)


def test_a_broken_notifier_does_not_stop_the_bot(world):
    class Broken:
        def event(self, kind, fields):
            raise RuntimeError("telegram is down")

        notify = event

    bot = make(world, notifier=Broken())
    assert minute(world, bot, 9, 41) == "continue"
    assert len(world.opens()) == 1


def test_write_is_atomic_and_leaves_no_temp_file(tmp_path):
    path = tmp_path / "live" / "status.json"
    write_status(path, {"a": 1})
    write_status(path, {"a": 2})
    assert json.loads(path.read_text()) == {"a": 2}
    assert [p.name for p in path.parent.iterdir()] == ["status.json"]


def test_read_status_handles_missing_and_broken_files(tmp_path):
    assert read_status(tmp_path / "none.json") is None
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert read_status(bad) is None


def test_heartbeat_age_and_staleness():
    now = datetime(2026, 1, 12, 15, 0, tzinfo=UTC)
    fresh = {"heartbeat": (now - timedelta(seconds=30)).isoformat()}
    stale = {"heartbeat": (now - timedelta(seconds=STALE_S + 5)).isoformat()}
    assert heartbeat_age_s(fresh, now) == pytest.approx(30)
    assert heartbeat_age_s(stale, now) > STALE_S
    assert heartbeat_age_s(None, now) is None and heartbeat_age_s({}, now) is None
    assert heartbeat_age_s({"heartbeat": "garbage"}, now) is None


def test_summary_text_is_short_and_plain():
    text = summary_text(
        {
            "running": True,
            "connected": True,
            "account_mode": "DEMO",
            "equity": 99_000.0,
            "day_pl_percent": -1.0,
            "day_r": -2.5,
            "positions": [{}],
            "guard": {"state": "ok"},
            "last_error": "",
        }
    )
    assert "DEMO" in text and "-1.0" in text and "-2.5" in text and "open 1" in text
    assert "no status" in summary_text(None)
