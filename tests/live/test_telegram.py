"""Telegram for the live bot (ROADMAP 7.2 monitoring): a fake HTTP client, no network.

The token never appears in logs, errors or stored messages; only the saved chat id is obeyed;
/emergency needs a confirm within 60 s; sending never blocks or crashes the caller.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest
from fake_keyring import FakeKeyring

from backtester.live.credentials import CredentialStoreError
from backtester.live.telegram import (
    EMERGENCY_CONFIRM_S,
    Notifier,
    TelegramClient,
    TelegramConfig,
    TelegramError,
    format_event,
    load_telegram,
    save_telegram,
)

TOKEN = "123456:SECRET-token-ABC"
CHAT = "4242"


class FakeHttp:
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []
        self.updates: list[dict] = []
        self.fail: Exception | None = None

    def __call__(self, url, payload, timeout):
        self.calls.append((url, payload))
        if self.fail:
            raise self.fail
        if url.endswith("/getUpdates"):
            out, self.updates = self.updates, []
            return {"ok": True, "result": out}
        return {"ok": True, "result": {}}

    def sent(self) -> list[str]:
        return [p["text"] for u, p in self.calls if u.endswith("/sendMessage")]


def update(uid, chat, text):
    return {"update_id": uid, "message": {"chat": {"id": int(chat)}, "text": text}}


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


@pytest.fixture
def rig(tmp_path):
    http, clock = FakeHttp(), Clock()
    client = TelegramClient(TelegramConfig(TOKEN, CHAT), http=http)
    stop, emergency = tmp_path / "STOP", tmp_path / "EMERGENCY"
    n = Notifier(
        client, stop, emergency, status_text=lambda: "status-line", now=clock, threaded=False
    )
    n.pump(force_poll=True)  # the first poll only primes: it drops commands sent before the start
    return SimpleNamespace(n=n, http=http, clock=clock, stop=stop, emergency=emergency)


# --- storage -----------------------------------------------------------------------------


def test_config_roundtrip_and_hidden_repr():
    store = FakeKeyring()
    save_telegram(TelegramConfig(TOKEN, CHAT), store)
    assert load_telegram(store) == TelegramConfig(TOKEN, CHAT)
    assert TOKEN not in repr(TelegramConfig(TOKEN, CHAT))
    assert TOKEN not in str(TelegramConfig(TOKEN, CHAT))


def test_nothing_saved_and_incomplete_are_handled():
    assert load_telegram(FakeKeyring()) is None
    with pytest.raises(CredentialStoreError):
        save_telegram(TelegramConfig("", CHAT), FakeKeyring())
    with pytest.raises(CredentialStoreError):
        save_telegram(TelegramConfig(TOKEN, "not-a-number"), FakeKeyring())


def test_store_failure_does_not_leak_the_token():
    with pytest.raises(CredentialStoreError) as e:
        save_telegram(TelegramConfig(TOKEN, CHAT), FakeKeyring(fail=True))
    assert TOKEN not in str(e.value)


# --- client ------------------------------------------------------------------------------


def test_send_posts_to_the_chat():
    http = FakeHttp()
    TelegramClient(TelegramConfig(TOKEN, CHAT), http=http).send("hello")
    url, payload = http.calls[0]
    assert url.endswith("/sendMessage") and payload == {"chat_id": CHAT, "text": "hello"}


def test_http_error_text_is_scrubbed():
    http = FakeHttp()
    http.fail = OSError(f"failed https://api.telegram.org/bot{TOKEN}/sendMessage")
    client = TelegramClient(TelegramConfig(TOKEN, CHAT), http=http)
    with pytest.raises(TelegramError) as e:
        client.send("x")
    assert TOKEN not in str(e.value) and "SECRET" not in repr(e.value)


def test_api_not_ok_raises_without_token():
    client = TelegramClient(TelegramConfig(TOKEN, CHAT), http=lambda u, p, t: {"ok": False})
    with pytest.raises(TelegramError) as e:
        client.send("x")
    assert TOKEN not in str(e.value)


# --- formatting --------------------------------------------------------------------------


def test_event_messages():
    assert "started" in format_event("connected", {}).lower()
    assert "stopped" in format_event("stopped", {}).lower()
    fill = format_event(
        "order",
        {"symbol": "US500", "side": "buy", "lots": 45.4, "sl": 97.5, "fill": 103.2, "ticket": 7},
    )
    assert all(s in fill for s in ("US500", "buy", "45.4", "103.2", "97.5"))
    assert "+0.8" in format_event("trade_closed", {"symbol": "US500", "r_net": 0.8, "reason": "x"})
    assert "-1.0" in format_event("trade_closed", {"symbol": "US500", "r_net": -1.0, "reason": "x"})
    skip = format_event("skip", {"symbol": "US500", "reason": "daily stop active"})
    assert "US500" in skip and "daily stop active" in skip
    assert "Daily stop" in format_event("guard_stop", {"reason": "r", "day_pl": -2100})
    assert "FTMO" in format_event("guard_breach", {"reason": "r", "day_pl": -5100})
    assert "boom" in format_event("error", {"what": "boom"})
    assert "lost" in format_event("disconnected", {"error": "x"}).lower()


def test_signal_message():
    text = format_event("signal", {"symbol": "US500", "side": "buy", "entry": 103.0, "sl": 97.5})
    assert "Signal" in text and "US500" in text and "103" in text


def test_unlisted_events_are_not_sent():
    assert format_event("warm_up", {"symbol": "US500"}) is None
    assert format_event("no_such_kind", {}) is None


# --- notifier: sending ------------------------------------------------------------------


def test_notify_queues_and_pump_sends(rig):
    rig.n.notify("one")
    rig.n.notify("two")
    assert rig.http.sent() == []  # nothing sent from the caller's thread
    rig.n.pump()
    assert rig.http.sent() == ["one", "two"]


def test_failed_send_never_raises_and_is_logged_without_token(rig, caplog):
    rig.http.fail = OSError(f"https://api.telegram.org/bot{TOKEN}/sendMessage timed out")
    rig.n.notify("x")
    with caplog.at_level(logging.DEBUG):
        rig.n.pump()
    assert rig.n.errors and TOKEN not in " ".join(rig.n.errors)
    assert TOKEN not in caplog.text and "SECRET" not in caplog.text


def test_full_queue_drops_instead_of_blocking(rig):
    for i in range(rig.n.QUEUE_MAX + 50):
        rig.n.notify(str(i))
    assert rig.n.dropped == 50


def test_event_sends_only_listed_kinds(rig):
    rig.n.event("warm_up", {"symbol": "x"})
    rig.n.event("skip", {"symbol": "US500", "reason": "stale"})
    rig.n.pump()
    assert len(rig.http.sent()) == 1 and "stale" in rig.http.sent()[0]


def test_threaded_notifier_sends_in_background_and_stops():
    http = FakeHttp()
    n = Notifier(
        TelegramClient(TelegramConfig(TOKEN, CHAT), http=http), None, None, poll_every_s=0.05
    )
    n.start()
    n.notify("bg")
    n.stop(timeout=3)
    assert "bg" in http.sent()


# --- notifier: commands -------------------------------------------------------------------


def test_status_command_replies_to_the_saved_chat(rig):
    rig.http.updates = [update(2, CHAT, "/status")]
    rig.n.pump(force_poll=True)
    assert "status-line" in rig.http.sent()


def test_stop_command_creates_the_stop_file(rig):
    rig.http.updates = [update(5, CHAT, "/stop")]
    rig.n.pump(force_poll=True)
    assert rig.stop.exists()


def test_commands_from_other_chats_are_ignored(rig):
    rig.http.updates = [
        update(6, "999", "/stop"),
        update(7, "999", "/emergency confirm"),
        update(8, "999", "/status"),
    ]
    rig.n.pump(force_poll=True)
    assert not rig.stop.exists() and not rig.emergency.exists() and rig.http.sent() == []


def test_old_commands_before_start_are_dropped(tmp_path):
    http = FakeHttp()
    http.updates = [update(1, CHAT, "/stop")]
    stop = tmp_path / "STOP"
    n = Notifier(TelegramClient(TelegramConfig(TOKEN, CHAT), http=http), stop, None, threaded=False)
    n.pump(force_poll=True)
    assert not stop.exists()


def test_emergency_needs_confirm(rig):
    rig.http.updates = [update(10, CHAT, "/emergency")]
    rig.n.pump(force_poll=True)
    assert not rig.emergency.exists()
    assert any("/emergency confirm" in s for s in rig.http.sent())
    rig.clock.t += 10
    rig.http.updates = [update(11, CHAT, "/emergency confirm")]
    rig.n.pump(force_poll=True)
    assert rig.emergency.exists()


def test_confirm_without_request_or_too_late_does_nothing(rig):
    rig.http.updates = [update(10, CHAT, "/emergency confirm")]
    rig.n.pump(force_poll=True)
    assert not rig.emergency.exists()
    rig.http.updates = [update(11, CHAT, "/emergency")]
    rig.n.pump(force_poll=True)
    rig.clock.t += EMERGENCY_CONFIRM_S + 1
    rig.http.updates = [update(12, CHAT, "/emergency confirm")]
    rig.n.pump(force_poll=True)
    assert not rig.emergency.exists()


def test_poll_errors_are_swallowed(rig):
    rig.http.fail = OSError("down")
    rig.n.pump(force_poll=True)
    assert rig.n.errors
