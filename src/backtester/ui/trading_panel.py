"""Settings ⚙ → Trading: the account connection (a modal). Spec: ROADMAP.md › 7.1.

Platform (MT5 now), login, password (masked), server (the servers the terminal knows as
suggestions, any name can be typed), optional terminal path, the broker's symbol names,
"Save", "Test connection" and the demo test orders.

Login, password and server are saved only in the Windows Credential Manager
(`live/credentials.py`); the rest in `results/trading.json` (`live/trading_settings.py`).
The password is never sent back to the browser: the field stays empty and says when one is
saved; leaving it empty on Save / Test keeps the saved one.

`trading_action` holds the logic (tested without Dash); `register_callbacks` wires it.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from types import ModuleType

from dash import Dash, Input, Output, State, ctx, dcc, html, no_update

from backtester.live.connection import check_connection, known_servers, report_lines, scrub
from backtester.live.credentials import (
    Credentials,
    CredentialStoreError,
    keyring_backend,
    load_credentials,
    save_credentials,
)
from backtester.live.trading_settings import (
    PLATFORMS,
    SYMBOLS,
    TRADING_FILE,
    TradingSettings,
    load_trading_settings,
    save_trading_settings,
)

PASSWORD_SAVED = "saved, leave empty to keep it"
PASSWORD_NONE = "password"


@dataclass(frozen=True)
class Deps:
    """Where the panel stores and connects (tests replace them)."""

    settings_path: Path = TRADING_FILE
    backend: Callable[[], object] = keyring_backend
    mt5: Callable[[], ModuleType] | None = None  # None: the real MetaTrader5
    appdata: str | Path | None = None
    run_test_orders: Callable | None = None  # set by part D


def _clock_text(settings: TradingSettings) -> str:
    if settings.server_clock is None:
        return "Server time: not measured yet (python -m backtester.data.mt5_info)."
    note = f" ({settings.server_clock_note})" if settings.server_clock_note else ""
    return f"Server time = {settings.server_clock.label}{note}."


def _form_credentials(form: Mapping, saved: Credentials | None) -> Credentials:
    login = str(form.get("login") or "").strip()
    server = str(form.get("server") or "").strip()
    password = form.get("password") or (saved.password if saved else "")
    if not login.isdigit():
        raise CredentialStoreError("the login is the account number (digits only)")
    if not server:
        raise CredentialStoreError("enter the server")
    if not password:
        raise CredentialStoreError("enter the password")
    return Credentials(login, password, server)


def _form_settings(form: Mapping, base: TradingSettings) -> TradingSettings:
    symbols = {s: str((form.get("symbols") or {}).get(s) or "").strip() for s in SYMBOLS}
    return replace(
        base.with_symbols(symbols),
        platform=form.get("platform") or base.platform,
        terminal_path=str(form.get("path") or "").strip(),
    )


def trading_action(trigger: str, form: Mapping, deps: Deps | None = None) -> dict:
    """trigger: "load" (the panel opened), "save", "test" or "orders" (demo test orders,
    `form["test_symbol"]`). Returns {"fields": form values to show or None, "servers",
    "password_placeholder", "clock", "status", "result": lines}."""
    deps = deps or Deps()
    settings = load_trading_settings(deps.settings_path)
    out = {"fields": None, "servers": [], "result": [], "status": ""}
    saved = None
    try:
        backend = deps.backend()
        saved = load_credentials(settings.platform, backend)
    except CredentialStoreError as e:
        backend, out["status"] = None, f"Credential store: {e}."

    if trigger == "load":
        out["fields"] = {
            "platform": settings.platform,
            "login": saved.login if saved else "",
            "server": saved.server if saved else "",
            "path": settings.terminal_path,
            "symbols": dict(settings.symbols),
        }
    elif trigger == "save":
        try:
            credentials = _form_credentials(form, saved)
            if backend is None:
                raise CredentialStoreError("the credential store is not available")
            save_credentials(credentials, settings.platform, backend)
            settings = _form_settings(form, settings)
            save_trading_settings(settings, deps.settings_path)
            saved = credentials
            out["status"] = (
                "Saved: login, password and server in the Windows Credential Manager; "
                "terminal path and symbol names in results/trading.json."
            )
        except (CredentialStoreError, ValueError) as e:
            out["status"] = f"Not saved: {scrub(str(e), saved)}."
    elif trigger in ("test", "orders"):
        try:
            credentials = _form_credentials(form, saved)
        except CredentialStoreError as e:
            out["status"] = f"Can't connect: {e}."
            credentials = None
        if credentials is not None:
            settings = _form_settings(form, settings)
            mt5 = deps.mt5() if deps.mt5 else None
            if trigger == "test":
                report = check_connection(settings, credentials, mt5)
                out["result"] = report_lines(report)
                out["status"] = "Connection tested (not saved)."
            elif deps.run_test_orders is None:
                out["status"] = "Demo test orders are not available."
            else:
                symbol = form.get("test_symbol") or SYMBOLS[0]
                out["result"] = deps.run_test_orders(settings, credentials, symbol, mt5)
                out["status"] = f"Demo test orders on {symbol} finished."
    out["servers"] = known_servers(settings.terminal_path, deps.appdata)
    out["password_placeholder"] = PASSWORD_SAVED if saved else PASSWORD_NONE
    out["clock"] = _clock_text(settings)
    return out


# --- layout ------------------------------------------------------------------------------


def _row(label: str, control, help_: str = "") -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Div(label, className="st-label"),
                    html.Div(help_, className="st-help") if help_ else None,
                ],
                className="st-text",
            ),
            html.Div(control, className="st-control"),
            html.Div(),
        ],
        className="st-row",
    )


def _input(id_: str, **kwargs) -> dcc.Input:
    return dcc.Input(id=id_, type="text", className="st-input", **kwargs)


def layout() -> html.Div:
    fields = html.Div(
        [
            html.Div("Account", className="st-section"),
            _row(
                "Platform",
                dcc.Dropdown(
                    id="tr-platform",
                    options=list(PLATFORMS),
                    value=PLATFORMS[0],
                    clearable=False,
                    searchable=False,
                    className="st-dd",
                ),
                "MetaTrader 5 now; others later.",
            ),
            _row("Login", _input("tr-login", autoComplete="off"), "The account number."),
            _row(
                "Password",
                dcc.Input(
                    id="tr-password",
                    type="password",
                    className="st-input",
                    placeholder=PASSWORD_NONE,
                    autoComplete="new-password",
                ),
                "Never shown again after saving.",
            ),
            _row(
                "Server",
                _input("tr-server", list="tr-servers", autoComplete="off"),
                "Pick one the terminal knows or type the name.",
            ),
            html.Datalist(id="tr-servers"),
            _row(
                "Terminal path",
                _input("tr-path", placeholder="optional: …\\terminal64.exe"),
                "Empty: the installed / running MetaTrader 5.",
            ),
            html.Div("Symbols on the server", className="st-section"),
            html.Div(
                "The broker's name for each symbol (e.g. with a suffix). "
                "python -m backtester.data.mt5_info finds them.",
                className="st-help st-section-help",
            ),
            *[_row(symbol, _input(f"tr-sym-{symbol}")) for symbol in SYMBOLS],
            html.Div(id="tr-clock", className="st-help"),
            html.Div("Demo test orders", className="st-section"),
            html.Div(
                "Demo accounts only (DEMO LOCK): buy and sell 2 x the minimum lot with SL "
                "and TP, move the SL, close half, close the rest. Nothing stays open.",
                className="st-help st-section-help",
            ),
            html.Div(
                [
                    dcc.Dropdown(
                        id="tr-test-symbol",
                        options=list(SYMBOLS),
                        value=SYMBOLS[0],
                        clearable=False,
                        searchable=False,
                        className="tr-test-symbol",
                    ),
                    html.Button("Run demo test orders", id="tr-orders", className="st-btn"),
                ],
                className="tr-actions",
            ),
            dcc.Loading(html.Pre(id="tr-result", className="tr-result"), type="dot"),
        ],
        className="st-fields",
    )
    return html.Div(
        html.Div(
            [
                html.Div(
                    [
                        html.Div("Settings · Trading", className="st-title"),
                        html.Button("✕", className="st-close", **{"data-modal-close": "tr-modal"}),
                    ],
                    className="st-head",
                ),
                html.Div(
                    [
                        dcc.RadioItems(
                            id="tr-nav", options=["Trading"], value="Trading", className="st-nav"
                        ),
                        fields,
                    ],
                    className="st-main",
                ),
                html.Div(
                    [
                        html.Div(id="tr-status", className="st-status"),
                        html.Button("Test connection", id="tr-test", className="st-btn"),
                        html.Button("Save", id="tr-save", className="st-btn st-primary"),
                        html.Button(
                            "Close", className="st-btn", **{"data-modal-close": "tr-modal"}
                        ),
                    ],
                    className="st-foot",
                ),
            ],
            className="st-dialog",
        ),
        id="tr-modal",
        className="st-backdrop",
    )


def register_callbacks(app: Dash, deps: Deps | None = None) -> None:
    deps = deps or Deps()
    triggers = {"tr-open": "load", "tr-save": "save", "tr-test": "test", "tr-orders": "orders"}
    symbol_ids = [f"tr-sym-{s}" for s in SYMBOLS]

    @app.callback(
        Output("tr-platform", "value"),
        Output("tr-login", "value"),
        Output("tr-password", "value"),
        Output("tr-password", "placeholder"),
        Output("tr-server", "value"),
        Output("tr-servers", "children"),
        Output("tr-path", "value"),
        *[Output(i, "value") for i in symbol_ids],
        Output("tr-clock", "children"),
        Output("tr-status", "children"),
        Output("tr-result", "children"),
        *[Input(i, "n_clicks") for i in triggers],
        State("tr-platform", "value"),
        State("tr-login", "value"),
        State("tr-password", "value"),
        State("tr-server", "value"),
        State("tr-path", "value"),
        *[State(i, "value") for i in symbol_ids],
        State("tr-test-symbol", "value"),
        prevent_initial_call=True,
    )
    def _trading(*args):
        n = len(triggers)
        platform, login, password, server, path, *rest = args[n:]
        symbols, test_symbol = rest[: len(SYMBOLS)], rest[len(SYMBOLS)]
        form = {
            "platform": platform,
            "login": login,
            "password": password,
            "server": server,
            "path": path,
            "symbols": dict(zip(SYMBOLS, symbols, strict=True)),
            "test_symbol": test_symbol,
        }
        trigger = triggers.get(ctx.triggered_id, "load")
        out = trading_action(trigger, form, deps)
        f = out["fields"] or {
            "platform": platform,
            "login": login,
            "server": server,
            "path": path,
            "symbols": form["symbols"],
        }
        return (
            f["platform"],
            f["login"],
            # the password never goes back to the browser; Test keeps what was typed
            "" if trigger in ("load", "save") else no_update,
            out["password_placeholder"],
            f["server"],
            [html.Option(value=s) for s in out["servers"]],
            f["path"],
            *[f["symbols"].get(s, s) for s in SYMBOLS],
            out["clock"],
            out["status"],
            "\n".join(out["result"]),
        )
