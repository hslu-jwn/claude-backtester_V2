"""Settings ⚙ → Trading: the Telegram fields (token masked, chat id, Save, Send test message)."""

from __future__ import annotations

import json

from fake_keyring import FakeKeyring

from backtester.live.telegram import load_telegram
from backtester.ui import trading_panel
from backtester.ui.trading_panel import Deps, telegram_action

TOKEN = "123456:SECRET-token-ABC"
FORM = {"token": TOKEN, "chat_id": "4242"}


def deps(store=None, http=None):
    store = store if store is not None else FakeKeyring()
    return Deps(backend=lambda: store, telegram_http=http), store


def test_save_goes_to_the_keyring_only():
    d, store = deps()
    out = telegram_action("save", FORM, d)
    assert "Saved" in out["status"]
    saved = load_telegram(store)
    assert saved.token == TOKEN and saved.chat_id == "4242"
    assert TOKEN not in json.dumps(out)  # nothing goes back to the browser


def test_load_shows_the_chat_id_but_never_the_token():
    d, _ = deps()
    telegram_action("save", FORM, d)
    out = telegram_action("load", {}, d)
    assert out["chat_id"] == "4242" and out["token_placeholder"] != "bot token"
    assert TOKEN not in json.dumps(out)


def test_empty_token_keeps_the_saved_one():
    d, store = deps()
    telegram_action("save", FORM, d)
    telegram_action("save", {"token": "", "chat_id": "777"}, d)
    saved = load_telegram(store)
    assert saved.token == TOKEN and saved.chat_id == "777"


def test_bad_input_is_rejected_without_leaking():
    d, store = deps()
    assert "Not saved" in telegram_action("save", {"token": TOKEN, "chat_id": "abc"}, d)["status"]
    assert "Not saved" in telegram_action("save", {"token": "", "chat_id": "42"}, d)["status"]
    assert load_telegram(store) is None


def test_broken_store_is_reported():
    d, _ = deps(FakeKeyring(fail=True))
    out = telegram_action("save", FORM, d)
    assert "Not saved" in out["status"] and TOKEN not in out["status"]


def test_test_message_uses_the_typed_values_and_reports_success():
    calls = []

    def http(url, payload, timeout):
        calls.append((url, payload))
        return {"ok": True, "result": {}}

    d, _ = deps(http=http)
    out = telegram_action("test", FORM, d)
    assert "sent" in out["status"].lower()
    assert calls[0][1]["chat_id"] == "4242" and "test" in calls[0][1]["text"].lower()
    assert TOKEN not in out["status"]


def test_test_message_with_saved_token():
    calls = []
    d, _ = deps(http=lambda u, p, t: calls.append(u) or {"ok": True})
    telegram_action("save", FORM, d)
    out = telegram_action("test", {"token": "", "chat_id": ""}, d)
    assert "sent" in out["status"].lower() and TOKEN in calls[0]


def test_test_message_failure_hides_the_token():
    def http(url, payload, timeout):
        raise OSError(f"cannot reach {url}")

    d, _ = deps(http=http)
    out = telegram_action("test", FORM, d)
    assert "failed" in out["status"].lower() and TOKEN not in out["status"]


def test_nothing_to_send_to():
    d, _ = deps(http=lambda *a: {"ok": True})
    assert "enter" in telegram_action("test", {"token": "", "chat_id": ""}, d)["status"].lower()


def test_layout_has_the_fields():
    text = json.dumps(trading_panel.layout(), default=lambda o: o.to_plotly_json())
    for i in ("tr-tg-token", "tr-tg-chat", "tr-tg-save", "tr-tg-test"):
        assert i in text
    assert '"type": "password"' in text
