"""Connecting to the MT5 terminal and the "Test connection" report. Spec: ROADMAP.md › 7.1.

`session()` connects with the saved login (Windows Credential Manager) and the saved
terminal path, and always shuts the connection down afterwards. Without a saved login it
attaches to whatever account the running terminal is logged in to. The `MetaTrader5`
module is process-wide, so one lock serializes every session (the app's callbacks run in
threads).

Error texts are scrubbed of login, password and server before they are shown or raised.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType

from backtester.data.adapters.mt5_adapter import load_mt5
from backtester.live.credentials import Credentials
from backtester.live.trading_settings import TradingSettings

LOCK = threading.RLock()
TIMEOUT_MS = 60_000
NOT_SERVERS = {"Custom", "Default", "signals"}  # other folders in a terminal's bases/
HIDDEN = "<hidden>"


class ConnectionFailed(RuntimeError):
    pass


def scrub(text: str, credentials: Credentials | None) -> str:
    """`text` with the login, password and server replaced by <hidden>."""
    for secret in sorted(credentials.secrets() if credentials else (), key=len, reverse=True):
        text = text.replace(secret, HIDDEN)
    return text


def connect(
    mt5: ModuleType,
    credentials: Credentials | None,
    terminal_path: str = "",
    timeout_ms: int = TIMEOUT_MS,
) -> None:
    """Initialize the terminal and log in. Raises `ConnectionFailed` with MT5's error."""
    kwargs: dict = {"timeout": timeout_ms}
    if credentials is not None:
        if not credentials.login.strip().isdigit():
            raise ConnectionFailed("the MT5 login is a number")
        kwargs.update(
            login=int(credentials.login),
            password=credentials.password,
            server=credentials.server,
        )
    args = (terminal_path,) if terminal_path else ()
    ok = mt5.initialize(*args, **kwargs)
    if not ok:
        code, text = mt5.last_error()
        mt5.shutdown()
        raise ConnectionFailed(scrub(f"{text} (MT5 error {code})", credentials))


@contextmanager
def session(
    settings: TradingSettings,
    credentials: Credentials | None,
    mt5: ModuleType | None = None,
) -> Iterator[ModuleType]:
    with LOCK:
        mt5 = mt5 or load_mt5()
        connect(mt5, credentials, settings.terminal_path)
        try:
            yield mt5
        finally:
            mt5.shutdown()


def account_mode(mt5: ModuleType, trade_mode: int) -> str:
    names = {
        mt5.ACCOUNT_TRADE_MODE_DEMO: "DEMO",
        mt5.ACCOUNT_TRADE_MODE_CONTEST: "CONTEST",
        mt5.ACCOUNT_TRADE_MODE_REAL: "REAL",
    }
    return names.get(trade_mode, f"unknown ({trade_mode})")


def account_report(mt5: ModuleType) -> dict:
    """What "Test connection" shows, from a connected terminal (no login number)."""
    account, terminal = mt5.account_info(), mt5.terminal_info()
    if account is None or terminal is None:
        code, text = mt5.last_error()
        return {"connected": False, "error": f"{text} (MT5 error {code})"}
    return {
        "connected": True,
        "error": None,
        "name": account.name,
        "server": account.server,
        "mode": account_mode(mt5, account.trade_mode),
        "currency": account.currency,
        "balance": account.balance,
        "equity": account.equity,
        "leverage": account.leverage,
        "algo_allowed": bool(terminal.trade_allowed),  # the terminal's Algo Trading button
        "account_algo_allowed": bool(account.trade_expert),  # the broker allows EAs
    }


def check_connection(
    settings: TradingSettings, credentials: Credentials | None, mt5: ModuleType | None = None
) -> dict:
    """`account_report`, or {"connected": False, "error": …}; never raises."""
    try:
        with session(settings, credentials, mt5) as connected:
            return account_report(connected)
    except Exception as e:  # noqa: BLE001 - shown in the panel, scrubbed
        return {"connected": False, "error": scrub(str(e), credentials)}


def report_lines(report: dict) -> list[str]:
    if not report["connected"]:
        return ["Connected: no", f"MT5: {report['error']}"]
    lines = [
        "Connected: yes",
        f"Account: {report['name']}",
        f"Server: {report['server']}",
        f"Type: {report['mode']}",
        f"Currency: {report['currency']}",
        f"Balance: {report['balance']:,.2f}",
        f"Equity: {report['equity']:,.2f}",
        f"Leverage: 1:{report['leverage']}",
        f"Algo trading allowed: {'yes' if report['algo_allowed'] else 'no'}",
    ]
    if not report["algo_allowed"]:
        lines.append(
            "→ Press the Algo Trading button in the MT5 toolbar (it turns green), "
            "otherwise orders from Python are rejected."
        )
    if not report["account_algo_allowed"]:
        lines.append("→ The server does not allow automated trading on this account.")
    if report["mode"] != "DEMO":
        lines.append("→ Not a demo account: every order function refuses (DEMO LOCK).")
    return lines


def terminal_data_dirs(terminal_path: str = "", appdata: str | Path | None = None) -> list[Path]:
    """Data folders of the installed terminals (`%APPDATA%/MetaQuotes/Terminal/<id>`), only
    the one belonging to `terminal_path` if given (its origin.txt), plus the terminal's
    own folder (portable mode)."""
    root = Path(appdata or os.environ.get("APPDATA", "")) / "MetaQuotes" / "Terminal"
    found: list[Path] = []
    wanted = Path(terminal_path).parent if terminal_path else None
    if root.is_dir():
        for folder in sorted(root.iterdir()):
            origin = folder / "origin.txt"
            if not origin.is_file():
                continue
            if wanted is not None:
                installed = _read_origin(origin)
                if Path(installed).resolve() != wanted.resolve():
                    continue
            found.append(folder)
    if wanted is not None and (wanted / "bases").is_dir():
        found.append(wanted)
    return found


def _read_origin(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-16", "utf-8"):
        try:
            return raw.decode(encoding).strip().strip("﻿")
        except UnicodeDecodeError:
            continue
    return ""


def known_servers(terminal_path: str = "", appdata: str | Path | None = None) -> list[str]:
    """Servers the terminal has connected to before (folders in its bases/), sorted."""
    names: set[str] = set()
    for folder in terminal_data_dirs(terminal_path, appdata):
        bases = folder / "bases"
        if bases.is_dir():
            names |= {p.name for p in bases.iterdir() if p.is_dir() and p.name not in NOT_SERVERS}
    return sorted(names)
