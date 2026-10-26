"""Credentials, trading settings and the connection test (ROADMAP 7.1), with fakes."""

from __future__ import annotations

import json
import sys

import pytest
from fake_keyring import FakeKeyring
from fake_mt5 import FakeMt5

from backtester.data.adapters.mt5_adapter import ServerClock
from backtester.live.connection import (
    ConnectionFailed,
    check_connection,
    connect,
    known_servers,
    report_lines,
    scrub,
)
from backtester.live.credentials import (
    SERVICE,
    Credentials,
    CredentialStoreError,
    delete_credentials,
    load_credentials,
    save_credentials,
)
from backtester.live.trading_settings import (
    TradingSettings,
    load_trading_settings,
    save_trading_settings,
)

SECRET = Credentials("51234567", "s3cr3t-Pa55", "Broker-Demo7")


def test_credentials_never_print_their_values():
    for text in (repr(SECRET), str(SECRET), f"{SECRET}", repr([SECRET])):
        assert "51234567" not in text and "s3cr3t" not in text and "Broker-Demo7" not in text


def test_credentials_round_trip_through_the_store():
    store = FakeKeyring()
    assert load_credentials("MT5", store) is None
    save_credentials(SECRET, "MT5", store)
    assert list(store.store) == [(SERVICE, "MT5")]
    assert load_credentials("MT5", store) == SECRET
    delete_credentials("MT5", store)
    assert load_credentials("MT5", store) is None


def test_credential_store_errors_hide_the_values():
    with pytest.raises(CredentialStoreError, match="all needed"):
        save_credentials(Credentials("1", "", "x"), "MT5", FakeKeyring())
    with pytest.raises(CredentialStoreError) as e:
        save_credentials(SECRET, "MT5", FakeKeyring(fail=True))
    assert "s3cr3t" not in str(e.value)


def test_trading_settings_file_has_no_secrets(tmp_path):
    path = tmp_path / "trading.json"
    settings = TradingSettings(
        terminal_path="C:/MT5/terminal64.exe",
        symbols={"XAUUSD": "XAUUSD.x"},
        server_clock=ServerClock("America/New_York", 7),
    )
    save_trading_settings(settings, path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert set(data) == {
        "platform",
        "terminal_path",
        "symbols",
        "server_clock",
        "server_clock_note",
    }
    assert load_trading_settings(path) == settings
    assert load_trading_settings(path).symbols["GBPUSD"] == "GBPUSD"  # unmapped: same name
    assert load_trading_settings(tmp_path / "none.json") == TradingSettings()


def test_connect_passes_the_login_and_scrubs_errors():
    fake = FakeMt5()
    connect(fake, SECRET, "C:/MT5/terminal64.exe")
    assert fake.init_kwargs["path"] == "C:/MT5/terminal64.exe"
    assert fake.init_kwargs["login"] == 51234567 and fake.init_kwargs["server"] == "Broker-Demo7"

    failing = FakeMt5(login_ok=False)
    failing.initialize = lambda *a, **k: (
        setattr(failing, "error", (-6, "Authorization failed for 51234567 on Broker-Demo7"))
        or False
    )
    with pytest.raises(ConnectionFailed) as e:
        connect(failing, SECRET)
    assert "51234567" not in str(e.value) and "Broker-Demo7" not in str(e.value)
    assert "Authorization failed" in str(e.value)


def test_connect_without_saved_login_attaches_to_the_terminal():
    fake = FakeMt5()
    connect(fake, None)
    assert "login" not in fake.init_kwargs


def test_connection_report_lines():
    fake = FakeMt5()
    report = check_connection(TradingSettings(), SECRET, fake)
    lines = report_lines(report)
    assert lines[:4] == [
        "Connected: yes",
        "Account: Test Trader",
        "Server: Broker-Demo",
        "Type: DEMO",
    ]
    assert "Balance: 100,000.00" in lines and "Leverage: 1:100" in lines
    assert "Algo trading allowed: yes" in lines
    assert not fake.initialized  # shut down afterwards
    assert "login" not in report


def test_connection_report_tells_to_press_algo_trading_and_warns_on_real():
    fake = FakeMt5(trade_mode=FakeMt5.ACCOUNT_TRADE_MODE_REAL)
    fake.algo_allowed = False
    lines = report_lines(check_connection(TradingSettings(), SECRET, fake))
    assert "Type: REAL" in lines and "Algo trading allowed: no" in lines
    assert any("Algo Trading button" in line for line in lines)
    assert any("DEMO LOCK" in line for line in lines)


def test_connection_failure_is_a_report_not_an_exception():
    report = check_connection(TradingSettings(), SECRET, FakeMt5(login_ok=False))
    assert report_lines(report) == [
        "Connected: no",
        "MT5: Terminal: Authorization failed (MT5 error -6)",
    ]
    bad_login = check_connection(
        TradingSettings(), Credentials("abc", "pw-long-1", "Server-X"), FakeMt5()
    )
    assert bad_login["error"] == "the MT5 login is a number"


def test_scrub_longest_first():
    creds = Credentials("123", "pw123", "srv")
    assert scrub("x pw123 y 123 srv", creds) == "x <hidden> y <hidden> <hidden>"
    assert scrub("nothing", None) == "nothing"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows paths in origin.txt")
def test_known_servers_from_the_terminal_folders(tmp_path):
    terminal = tmp_path / "MetaQuotes" / "Terminal" / "ABC123"
    for name in ("Broker-Demo", "Broker-Live2", "Custom", "Default", "signals"):
        (terminal / "bases" / name).mkdir(parents=True)
    (terminal / "origin.txt").write_text("C:\\Program Files\\MetaTrader 5", encoding="utf-16")
    other = tmp_path / "MetaQuotes" / "Terminal" / "DEF456"
    (other / "bases" / "Other-Server").mkdir(parents=True)
    (other / "origin.txt").write_text("D:\\Other MT5", encoding="utf-16")
    assert known_servers("", tmp_path) == ["Broker-Demo", "Broker-Live2", "Other-Server"]
    assert known_servers("C:\\Program Files\\MetaTrader 5\\terminal64.exe", tmp_path) == [
        "Broker-Demo",
        "Broker-Live2",
    ]
    assert known_servers("", tmp_path / "nowhere") == []


def test_trading_symbols_are_all_the_backtest_symbols():
    """One symbol list: the MT5 settings cover every symbol the data layer knows (incl. the
    two indices NAS100 / US500)."""
    from backtester.data.sources import PRICE_DIGITS
    from backtester.live.trading_settings import SYMBOLS, TradingSettings

    assert set(SYMBOLS) == set(PRICE_DIGITS)
    assert {"XAUUSD", "GBPUSD", "GBPJPY", "NAS100", "US500"} <= set(
        SYMBOLS
    )  # + ROADMAP 11.8 / 11.9
    assert dict(TradingSettings().symbols) == {s: s for s in SYMBOLS}
