"""Live page `/live`: the demo bot at a glance. Spec: docs/live-trading.md › App layout and Live page.

Reads `results/live/status.json` (written by the bot every minute and on every event), today's
`orders.jsonl` and the day folders' `trades.csv` every few seconds; nothing is computed here but
display values (`ui/live_model.py` holds the tested helpers). Times: session window and "running
since" in New York time (ET), signals and the log in UTC, each labelled.

Buttons: **Start** launches `python -m backtester.live.bot` with the settings of this page as a
detached process (it keeps running when the web server stops) and refuses while a fresh heartbeat
shows a running bot; **Pause** toggles the `PAUSE` file (no new entries, open trades keep being
managed); **Stop** creates `STOP` (stop, close nothing); **Close all & stop** creates `EMERGENCY`
(close the bot's positions, then stop) after a confirm dialog. The page never touches MT5 or the
login (the Connection section only moves `trading_panel`, which does).

Settings (risk %, daily stop %, symbols) are editable only while the bot is not running.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import plotly.graph_objects as go
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update

from backtester.live.status import STATUS_NAME, heartbeat_age_s, read_status
from backtester.paths import RESULTS_DIR
from backtester.ui import live_model as lm
from backtester.ui import trading_panel

LIVE_DIR = RESULTS_DIR / "live"
LOG_LINES = 50
REFRESH_MS = 3000
BOT_LOG = "bot_stdout.log"
PAUSE_NAME = "PAUSE"
DASH = lm.DASH
STATE_BADGE = {  # bot state -> (label, css)
    "running": ("Running", "ok"), "paused": ("Paused", "warn"),
    "stale": ("Stopped", "bad"), "stopped": ("Stopped", "idle"), "none": ("Stopped", "idle"),
}  # fmt: skip
Spawn = Callable[[list[str], Path], object]  # (command, stdout log file)


# --- actions ---------------------------------------------------------------------------------


def request_stop(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "STOP").touch()


def request_emergency(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "EMERGENCY").touch()


def is_paused(out_dir: Path) -> bool:
    return (out_dir / PAUSE_NAME).exists()


def toggle_pause(out_dir: Path) -> bool:
    """Create or delete the PAUSE file. Returns True when the bot is now asked to pause."""
    path = out_dir / PAUSE_NAME
    if path.exists():
        path.unlink(missing_ok=True)
        return False
    out_dir.mkdir(parents=True, exist_ok=True)
    path.touch()
    return True


def _spawn_detached(command: list[str], log_file: Path) -> object:
    kwargs: dict = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
            | subprocess.CREATE_NO_WINDOW
        )
    else:
        kwargs["start_new_session"] = True
    with log_file.open("ab") as out:
        return subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT, **kwargs
        )


def start_bot(
    out_dir: Path, now: datetime, spawn: Spawn = _spawn_detached, settings: dict | None = None
) -> str:
    """Start the bot unless a fresh heartbeat shows it running. `settings` (validated, see
    `live_model.validate_settings`) become its command line. Returns a message."""
    if lm.bot_state(read_status(out_dir / STATUS_NAME), now) in ("running", "paused"):
        return "The bot is already running (fresh heartbeat); not started again."
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("STOP", "EMERGENCY", PAUSE_NAME):  # leftovers must not affect the new run
        (out_dir / name).unlink(missing_ok=True)
    try:
        spawn(lm.start_command(settings), out_dir / BOT_LOG)
    except OSError as e:
        return f"Could not start the bot: {type(e).__name__}."
    return "Bot started; the first heartbeat appears within a minute."


# --- view model ------------------------------------------------------------------------------


def _log_line(entry: dict) -> str:
    when = str(entry.get("time", ""))[11:19]
    request = entry.get("request") or {}
    detail = " ".join(f"{k}={v}" for k, v in request.items()) if isinstance(request, dict) else ""
    return f"{when} {entry.get('label', '')} {detail}".strip()


def _read_log(out_dir: Path, now: datetime) -> list[str]:
    path = out_dir / now.strftime("%Y-%m-%d") / "orders.jsonl"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict):
            out.append(_log_line(entry))
    return out[-LOG_LINES:]


def live_view(out_dir: Path, now: datetime) -> dict:
    status = read_status(out_dir / STATUS_NAME)
    state = lm.bot_state(status, now)
    if state == "running" and is_paused(out_dir):
        state = "paused"  # the file is the newest word; the heartbeat catches up
    return {
        "status": status,
        "age": heartbeat_age_s(status, now),
        "state": state,
        "log": _read_log(out_dir, now),
    }


def guard_bar(status: dict) -> dict:
    """Today's loss against the own daily stop (fraction of the stop, 0 .. 1)."""
    return lm.today_bar(status)


# --- rendering -------------------------------------------------------------------------------


def usd(value, signed: bool = False) -> str:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return DASH
    sign = "+" if signed and x >= 0 else "-" if x < 0 else ""
    return f"{sign}${abs(x):,.0f}"


def _num(status: dict, key: str):
    value = status.get(key)
    return value if isinstance(value, int | float) else None


def _pnl_class(x) -> str:
    return "lv-pos" if x is not None and x > 0 else "lv-neg" if x is not None and x < 0 else ""


def _bar(fraction: float, level: str, mark: float | None = None) -> html.Div:
    children = [
        html.Div(className=f"lv-fill lv-{level}", style={"width": f"{fraction * 100:.1f}%"})
    ]
    if mark is not None:
        children.append(html.Div(className="lv-mark", style={"left": f"{mark * 100:.1f}%"}))
    return html.Div(children, className="lv-bar")


def _table(head: list[str], rows: list[list], empty: str) -> html.Div:
    if not rows:
        return html.Div(empty, className="lv-empty")
    return html.Table(
        [
            html.Thead(html.Tr([html.Th(h) for h in head])),
            html.Tbody([html.Tr([html.Td(c) for c in row]) for row in rows]),
        ],
        className="lv-table",
    )


def _card(title: str, body, right=None, extra: str = "") -> html.Div:
    head = html.Div(
        [html.Span(title, className="lv-card-title"), right if right is not None else None],
        className="lv-card-head",
    )
    body = html.Div(body) if isinstance(body, list) else body  # no nested lists in Dash children
    return html.Div([head, body], className=f"lv-card {extra}".strip())


def render_head(view: dict, now: datetime) -> html.Div:
    status, state = view["status"] or {}, view["state"]
    label, css = STATE_BADGE[state]
    symbols = status.get("symbols") or []
    meta = [
        status.get("account_mode") or DASH,
        ", ".join(symbols) or DASH,
        f"{lm.window_text(status.get('session'))} · {lm.countdown_text(status.get('session'), now)}",
    ]
    if state in ("running", "paused"):
        meta.append(f"running since {lm.clock_et(status.get('started_at'))}")
    parts = [
        html.Div(
            [
                html.Span(label, className=f"lv-state lv-{css}"),
                html.Span(status.get("strategy") or "Live demo bot", className="lv-strategy"),
            ],
            className="lv-head-title",
        ),
        html.Div([html.Span(m, className="lv-meta") for m in meta], className="lv-metas"),
    ]
    if state == "none":
        parts.append(html.Div("Bot not started yet (no status file).", className="lv-note"))
    elif state == "stale":
        age = view["age"]
        gap = f" for {age / 60:.0f} min" if age is not None else ""
        parts.append(
            html.Div(f"No heartbeat{gap}: the bot is not running.", className="lv-note lv-stale")
        )
    if status.get("last_error"):
        parts.append(html.Div(f"Last error: {status['last_error']}", className="lv-error"))
    return html.Div(parts)


def render_cards(view: dict) -> html.Div:
    status = view["status"] or {}
    balance, equity = _num(status, "balance"), _num(status, "equity")
    floating = None if balance is None or equity is None else equity - balance
    pl, pl_money, day_r = (
        _num(status, "day_pl_percent"),
        _num(status, "day_pl"),
        _num(status, "day_r"),
    )
    today = lm.today_bar(status)
    age = view["age"]
    stale = lm.heartbeat_stale(age) or view["state"] in ("stopped", "none")
    link = status.get("connected")
    cards = [
        _card(
            "Balance",
            [
                html.Div(usd(balance), className="lv-big"),
                html.Div(f"start {usd(_num(status, 'initial_balance'))}", className="lv-sub"),
            ],
        ),
        _card(
            "Equity",
            [
                html.Div(usd(equity), className="lv-big"),
                html.Div(
                    f"{usd(floating, signed=True)} floating",
                    className=f"lv-sub {_pnl_class(floating)}",
                ),
            ],
        ),
        _card(
            "Today",
            [
                html.Div(
                    DASH if pl is None else f"{pl:+.2f} %", className=f"lv-big {_pnl_class(pl)}"
                ),
                _bar(today["fraction"], today["level"]),
                html.Div(
                    f"{usd(pl_money, signed=True)} · {DASH if day_r is None else f'{day_r:+.1f} R'}",
                    className="lv-sub",
                ),
            ],
            right=html.Span(f"daily stop -{today['stop']:g} %", className="lv-sub"),
        ),
        _card("FTMO limits", [_limit_row(b) for b in lm.ftmo_bars(status)]),
        _card(
            "Heartbeat",
            [
                html.Div(
                    lm.heartbeat_text(age),
                    className="lv-big lv-small" + (" lv-stale" if view["status"] and stale else ""),
                ),
                html.Div(
                    DASH if link is None else ("MT5 connected" if link else "MT5 not connected"),
                    className="lv-sub",
                ),
            ],
        ),
    ]
    return html.Div(cards, className="lv-cards")


def _limit_row(b: dict) -> html.Div:
    used = DASH if b["used"] is None else f"{b['used']:.2f} %"
    return html.Div(
        [
            html.Div(
                [
                    html.Span(b["label"], className="lv-sub"),
                    html.Span(f"{used} of {b['limit']:g} %", className="lv-mono"),
                ],
                className="lv-limit-head",
            ),
            _bar(b["fraction"], b["level"]),
        ],
        className="lv-limit",
    )


def render_setup(view: dict) -> html.Div:
    status = view["status"] or {}
    setups = status.get("setups") if isinstance(status.get("setups"), dict) else {}
    symbols = list(status.get("symbols") or setups)
    if not symbols:
        return html.Div("No symbols yet.", className="lv-empty")
    blocks = []
    for symbol in symbols:
        rows = lm.funnel_rows(setups.get(symbol))
        steps = [
            html.Div(
                [
                    html.Span("✓" if r["state"] == "done" else "", className="lv-dot"),
                    html.Div(
                        [
                            html.Div(r["label"], className="lv-step-label"),
                            html.Div(r["detail"], className="lv-sub") if r["detail"] else None,
                        ]
                    ),
                ],
                className=f"lv-step lv-step-{r['state']}",
            )
            for r in rows
        ]
        blocks.append(
            html.Div([html.Div(symbol, className="lv-symbol"), *steps], className="lv-funnel")
        )
    return html.Div(blocks, className="lv-funnels")


def render_positions(view: dict) -> html.Div:
    return _table(
        ["Symbol", "Side", "Lots", "Entry", "SL", "Floating R"],
        [
            [
                p.get("symbol", DASH),
                p.get("side", DASH),
                p.get("lots", DASH),
                p.get("entry", DASH),
                p.get("sl", DASH),
                html.Span(
                    f"{p['floating_r']:+.2f}"
                    if isinstance(p.get("floating_r"), int | float)
                    else DASH,
                    className=_pnl_class(
                        p.get("floating_r")
                        if isinstance(p.get("floating_r"), int | float)
                        else None
                    ),
                ),
            ]
            for p in (view["status"] or {}).get("positions") or []
        ],
        "none",
    )


def render_signals(view: dict) -> html.Div:
    return _table(
        ["Time (UTC)", "Symbol", "Side", "Result", "Reason"],
        [
            [
                str(s.get("time", ""))[11:16],
                s.get("symbol", ""),
                s.get("side", ""),
                s.get("status", ""),
                s.get("reason", ""),
            ]
            for s in (view["status"] or {}).get("signals") or []
        ],
        "none yet",
    )


def render(view: dict, now: datetime | None = None) -> dict:
    """All the dynamic pieces of the page by name (one Dash output each)."""
    now = now or datetime.now(UTC)
    return {
        "head": render_head(view, now),
        "cards": render_cards(view),
        "setup": render_setup(view),
        "positions": render_positions(view),
        "signals": render_signals(view),
        "log": "\n".join(view["log"]) or "(empty)",
    }


def trades_figure(strip: dict) -> go.Figure:
    """Bars in % of the balance (green / red) and the balance line in USD (right axis)."""
    fig = go.Figure()
    n = len(strip["pct"])
    if n:
        x = list(range(1, n + 1))
        fig.add_bar(
            x=x, y=strip["pct"], hovertext=strip["labels"], name="trade %", hovertemplate="%{hovertext}<br>%{y:+.2f} %<extra></extra>",
            marker_color=["#2ebd85" if v >= 0 else "#f6465d" for v in strip["pct"]],
        )  # fmt: skip
        fig.add_scatter(
            x=x, y=strip["balance"], yaxis="y2", name="balance", mode="lines",
            line={"color": "#4f8cff", "width": 2}, hovertemplate="$%{y:,.0f}<extra></extra>",
        )  # fmt: skip
    else:
        fig.add_annotation(text="No trades yet", showarrow=False, font={"color": "#7d8aa5"})
    axis = {"gridcolor": "#1d2a40", "zerolinecolor": "#33415c", "color": "#7d8aa5"}
    fig.update_layout(
        height=260, margin={"l": 40, "r": 56, "t": 8, "b": 28}, showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "ui-monospace, Consolas, monospace", "size": 11, "color": "#7d8aa5"},
        xaxis={**axis, "title": "trade", "dtick": 1 if n <= 20 else None},
        yaxis={**axis, "ticksuffix": " %"},
        yaxis2={"overlaying": "y", "side": "right", "color": "#4f8cff", "showgrid": False,
                "tickprefix": "$", "tickformat": ",.0f"},
    )  # fmt: skip
    return fig


def settings_state(view: dict) -> dict:
    """What the settings controls do for a view: disabled while the bot runs, and the values the
    running bot uses (None: leave the inputs alone)."""
    status, running = view["status"] or {}, view["state"] in ("running", "paused")
    if not running:
        return {"disabled": False, "risk": None, "stop": None, "symbols": None}
    guard = status.get("guard") or {}
    return {
        "disabled": True,
        "risk": status.get("risk_percent"),
        "stop": guard.get("daily_stop_percent"),
        "symbols": status.get("symbols") or None,
    }


def symbol_options(chosen: list[str] | None, disabled: bool) -> list[dict]:
    names = list(lm.DEFAULT_SYMBOLS) + [s for s in chosen or [] if s not in lm.DEFAULT_SYMBOLS]
    return [{"label": s, "value": s, "disabled": disabled} for s in names]


def button_state(view: dict) -> dict:
    running = view["state"] in ("running", "paused")
    return {
        "start_disabled": running,
        "pause_label": "Resume" if view["state"] == "paused" else "Pause",
        "pause_disabled": not running,
        "stop_disabled": view["state"] in ("none", "stopped"),
    }


def layout(out_dir: Path = LIVE_DIR, now: datetime | None = None) -> html.Div:
    now = now or datetime.now(UTC)
    view = live_view(out_dir, now)
    pieces = render(view, now)
    settings = settings_state(view)
    connected = bool((view["status"] or {}).get("connected")) and view["state"] != "stale"
    buttons = button_state(view)
    chosen = settings["symbols"] or list(lm.DEFAULT_SYMBOLS)
    return html.Div(
        [
            dcc.Interval(id="lv-interval", interval=REFRESH_MS),
            html.Div(
                [
                    html.Div(pieces["head"], id="lv-head", className="lv-head-info"),
                    html.Div(
                        [
                            html.Button(
                                "Start",
                                id="lv-start",
                                className="lv-btn lv-go",
                                n_clicks=0,
                                disabled=buttons["start_disabled"],
                            ),
                            html.Button(
                                buttons["pause_label"],
                                id="lv-pause",
                                className="lv-btn",
                                n_clicks=0,
                                disabled=buttons["pause_disabled"],
                            ),
                            html.Button(
                                "Stop",
                                id="lv-stop",
                                className="lv-btn",
                                n_clicks=0,
                                disabled=buttons["stop_disabled"],
                            ),
                            dcc.ConfirmDialogProvider(
                                html.Button("Close all & stop", className="lv-btn lv-danger"),
                                id="lv-emergency",
                                message=(
                                    "Close ALL positions opened by the bot and stop it. Continue?"
                                ),
                            ),
                        ],
                        className="lv-actions",
                    ),
                ],
                className="lv-card lv-header",
            ),
            html.Div(id="lv-msg", className="lv-msg"),
            html.Div(pieces["cards"], id="lv-cards"),
            html.Div(
                [
                    _card("Setup in progress", html.Div(pieces["setup"], id="lv-setup")),
                    _card(
                        "Recent trades",
                        [
                            dcc.Graph(
                                id="lv-trades",
                                figure=trades_figure(lm.trade_strip([], None, "day", now)),
                                config={"displayModeBar": False},
                            ),
                        ],
                        right=dcc.RadioItems(
                            id="lv-range",
                            options=[
                                {"label": "Day", "value": "day"},
                                {"label": "Week", "value": "week"},
                                {"label": "All", "value": "all"},
                            ],
                            value="day",
                            className="lv-seg",
                            inline=True,
                        ),
                    ),
                ],
                className="lv-two",
            ),
            _card("Open positions", html.Div(pieces["positions"], id="lv-positions")),
            _card("Today's signals and skips", html.Div(pieces["signals"], id="lv-signals")),
            _card(
                "Event log",
                html.Pre(pieces["log"], id="lv-log", className="lv-log"),
                right=html.Span(f"last {LOG_LINES}, times in UTC", className="lv-sub"),
            ),
            _card(
                "Settings",
                [
                    html.Div(
                        [
                            _field(
                                "Risk per trade (%)",
                                dcc.Input(
                                    id="lv-risk",
                                    type="number",
                                    value=lm.DEFAULT_RISK,
                                    min=0,
                                    max=lm.MAX_RISK_PERCENT,
                                    step=0.05,
                                    className="lv-input",
                                    disabled=settings["disabled"],
                                ),
                            ),
                            _field(
                                "Daily stop (%)",
                                dcc.Input(
                                    id="lv-daily-stop",
                                    type="number",
                                    value=lm.DEFAULT_DAILY_STOP,
                                    min=0,
                                    max=lm.MAX_DAILY_STOP_PERCENT,
                                    step=0.1,
                                    className="lv-input",
                                    disabled=settings["disabled"],
                                ),
                            ),
                            _field(
                                "Symbols",
                                dcc.Checklist(
                                    id="lv-symbols",
                                    options=symbol_options(chosen, settings["disabled"]),
                                    value=chosen,
                                    inline=True,
                                    className="lv-checks",
                                ),
                            ),
                        ],
                        className="lv-fields",
                    ),
                    html.Div(
                        f"Editable only while the bot is not running; Start passes them to the bot. "
                        f"Risk 0 to {lm.MAX_RISK_PERCENT:g} %, daily stop 0 to "
                        f"{lm.MAX_DAILY_STOP_PERCENT:g} %, at least one symbol.",
                        className="lv-sub",
                    ),
                ],
            ),
            trading_panel.layout(open_=not connected),
        ],
        className="lv-page",
    )


def _field(label: str, control) -> html.Div:
    return html.Div([html.Div(label, className="lv-sub"), control], className="lv-field")


def register_callbacks(app: Dash, out_dir: Path = LIVE_DIR) -> None:
    trading_panel.register_callbacks(app)

    @app.callback(
        Output("lv-head", "children"),
        Output("lv-cards", "children"),
        Output("lv-setup", "children"),
        Output("lv-positions", "children"),
        Output("lv-signals", "children"),
        Output("lv-log", "children"),
        Output("lv-start", "disabled"),
        Output("lv-pause", "children"),
        Output("lv-pause", "disabled"),
        Output("lv-stop", "disabled"),
        Output("lv-risk", "disabled"),
        Output("lv-daily-stop", "disabled"),
        Output("lv-symbols", "options"),
        Output("lv-risk", "value"),
        Output("lv-daily-stop", "value"),
        Output("lv-symbols", "value"),
        Input("lv-interval", "n_intervals"),
        State("lv-symbols", "value"),
    )
    def _refresh(_, chosen):
        now = datetime.now(UTC)
        view = live_view(out_dir, now)
        p, b, s = render(view, now), button_state(view), settings_state(view)
        keep = s["symbols"] or chosen
        return (
            p["head"], p["cards"], p["setup"], p["positions"], p["signals"], p["log"],
            b["start_disabled"], b["pause_label"], b["pause_disabled"], b["stop_disabled"],
            s["disabled"], s["disabled"], symbol_options(keep, s["disabled"]),
            no_update if s["risk"] is None else s["risk"],
            no_update if s["stop"] is None else s["stop"],
            no_update if s["symbols"] is None else s["symbols"],
        )  # fmt: skip

    @app.callback(
        Output("lv-trades", "figure"),
        Input("lv-interval", "n_intervals"),
        Input("lv-range", "value"),
    )
    def _trades(_, range_key):
        now = datetime.now(UTC)
        status = read_status(out_dir / STATUS_NAME) or {}
        strip = lm.trade_strip(
            lm.read_trades(out_dir), status.get("initial_balance"), range_key, now
        )
        return trades_figure(strip)

    @app.callback(
        Output("lv-msg", "children"),
        Input("lv-start", "n_clicks"),
        Input("lv-pause", "n_clicks"),
        Input("lv-stop", "n_clicks"),
        Input("lv-emergency", "submit_n_clicks"),
        State("lv-risk", "value"),
        State("lv-daily-stop", "value"),
        State("lv-symbols", "value"),
        prevent_initial_call=True,
    )
    def _buttons(start, pause, stop, emergency, risk, daily_stop, symbols):
        which = ctx.triggered_id
        now = datetime.now(UTC)
        if which == "lv-start" and start:
            clean, error = lm.validate_settings(risk, daily_stop, symbols)
            if clean is None:
                return f"Not started: {error}"
            return start_bot(out_dir, now, settings=clean)
        if which == "lv-pause" and pause:
            if lm.bot_state(read_status(out_dir / STATUS_NAME), now) not in ("running", "paused"):
                return "The bot is not running; nothing to pause."
            if toggle_pause(out_dir):
                return "PAUSE requested: no new entries; open trades keep being managed."
            return "Resumed: new entries are allowed again."
        if which == "lv-stop" and stop:
            request_stop(out_dir)
            return "STOP requested: the bot stops at its next cycle (nothing is closed)."
        if which == "lv-emergency" and emergency:
            request_emergency(out_dir)
            return (
                "CLOSE ALL requested: the bot closes its positions at its next cycle, then stops."
            )
        return no_update
