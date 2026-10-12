"""Settings ⚙ → Trading (ROADMAP 7.1): the panel logic with a fake keyring and MT5."""

from __future__ import annotations

import json

from fake_keyring import FakeKeyring
from fake_mt5 import FakeMt5

from backtester.live.credentials import Credentials, load_credentials
from backtester.ui import trading_panel
from backtester.ui.trading_panel import PASSWORD_NONE, PASSWORD_SAVED, Deps, trading_action

FORM = {
    "platform": "MT5",
    "login": "51234567",
    "password": "s3cr3t-Pa55",
    "server": "Broker-Demo7",
    "path": "",
    "symbols": {"XAUUSD": "XAUUSD.x", "GBPUSD": "", "GBPJPY": "GBPJPY"},
}


def deps(tmp_path, store=None, mt5=None):
    store = store if store is not None else FakeKeyring()
    return Deps(
        settings_path=tmp_path / "trading.json",
        backend=lambda: store,
        mt5=(lambda: mt5) if mt5 else None,
        appdata=tmp_path,
    )


def test_load_with_nothing_saved(tmp_path):
    out = trading_action("load", {}, deps(tmp_path))
    assert out["fields"]["login"] == "" and out["fields"]["server"] == ""
    assert out["fields"]["symbols"] == {
        s: s for s in ("XAUUSD", "GBPUSD", "GBPJPY", "NAS100", "US500")
    }
    assert out["password_placeholder"] == PASSWORD_NONE
    assert "not measured yet" in out["clock"]


def test_save_puts_secrets_only_in_the_credential_store(tmp_path):
    store = FakeKeyring()
    out = trading_action("save", FORM, deps(tmp_path, store))
    assert out["status"].startswith("Saved")
    assert load_credentials("MT5", store) == Credentials("51234567", "s3cr3t-Pa55", "Broker-Demo7")
    text = (tmp_path / "trading.json").read_text(encoding="utf-8")
    for secret in ("51234567", "s3cr3t", "Broker-Demo7"):
        assert secret not in text
    assert json.loads(text)["symbols"] == {
        "XAUUSD": "XAUUSD.x",
        "GBPUSD": "GBPUSD",
        "GBPJPY": "GBPJPY",
        "NAS100": "NAS100",
        "US500": "US500",
    }

    loaded = trading_action("load", {}, deps(tmp_path, store))
    assert loaded["fields"]["login"] == "51234567"
    assert loaded["fields"]["server"] == "Broker-Demo7"
    assert "password" not in loaded["fields"]  # never sent back
    assert loaded["password_placeholder"] == PASSWORD_SAVED


def test_empty_password_keeps_the_saved_one(tmp_path):
    store = FakeKeyring()
    trading_action("save", FORM, deps(tmp_path, store))
    trading_action(
        "save", {**FORM, "password": "", "server": "Broker-Demo8"}, deps(tmp_path, store)
    )
    assert load_credentials("MT5", store) == Credentials("51234567", "s3cr3t-Pa55", "Broker-Demo8")


def test_save_refuses_incomplete_forms(tmp_path):
    out = trading_action("save", {**FORM, "login": "abc"}, deps(tmp_path))
    assert out["status"] == "Not saved: the login is the account number (digits only)."
    out = trading_action("save", {**FORM, "password": ""}, deps(tmp_path))
    assert out["status"] == "Not saved: enter the password."
    assert not (tmp_path / "trading.json").exists()


def test_test_connection_uses_the_form_without_saving(tmp_path):
    store, fake = FakeKeyring(), FakeMt5()
    out = trading_action("test", FORM, deps(tmp_path, store, fake))
    assert out["result"][0] == "Connected: yes" and "Type: DEMO" in out["result"]
    assert fake.init_kwargs["login"] == 51234567
    assert store.store == {}


def test_failed_connection_shows_mt5s_error_without_secrets(tmp_path):
    fake = FakeMt5(login_ok=False)
    fake.initialize = lambda *a, **k: (
        setattr(fake, "error", (-6, "Authorization failed: s3cr3t-Pa55 51234567")) or False
    )
    out = trading_action("test", FORM, deps(tmp_path, mt5=fake))
    text = json.dumps(out)
    assert out["result"][0] == "Connected: no"
    assert "s3cr3t" not in text and "51234567" not in text


def test_credential_store_unavailable(tmp_path):
    out = trading_action("load", {}, deps(tmp_path, FakeKeyring(fail=True)))
    assert out["status"].startswith("Credential store:")


def test_layout_has_a_masked_password_field():
    layout = trading_panel.layout()

    def find(node, id_):
        if getattr(node, "id", None) == id_:
            return node
        children = getattr(node, "children", None)
        for child in children if isinstance(children, list) else [children]:
            if child is not None and not isinstance(child, str):
                hit = find(child, id_)
                if hit is not None:
                    return hit
        return None

    assert find(layout, "tr-password").type == "password"
    assert find(layout, "tr-server").list == "tr-servers"
