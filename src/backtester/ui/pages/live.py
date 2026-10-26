"""Live page `/live`: the demo bot at a glance. Spec: docs/live-trading.md › App layout and Live page.

Reads `results/live/status.json` (written by the bot every minute and on every event), today's
`orders.jsonl` and the day folders' `trades.csv` every few seconds; nothing is computed here but
display values (`ui/live_model.py` holds the tested helpers). Times: all in Swiss time (CH, user
2026-10-17), labelled.

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

from backtester.live.lock import LOCK_NAME, lock_holder, pid_alive
from backtester.live.status import STATUS_NAME, heartbeat_age_s, read_status
from backtester.paths import RESULTS_DIR
from backtester.ui import layout as ui
from backtester.ui import live_model as lm
from backtester.ui import trade_focus, trading_panel
from backtester.ui.theme import color as theme_color

LIVE_DIR = RESULTS_DIR / "live"
LOG_LINES = 50
REFRESH_MS = 3000
BOT_LOG = "bot_stdout.log"
PAUSE_NAME = "PAUSE"
DASH = lm.DASH
STEP_MARK = {"done": "✓", "failed": "✕"}  # funnel row state -> mark
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


# Windows: the bot is started by a short-lived launcher, so it has no living parent (a restart
# of the app that kills its process tree, taskkill /T, does not reach it), and with
# CREATE_BREAKAWAY_FROM_JOB, so it is not in the app's job object (a terminal / IDE / service
# host that kills the job when the app is restarted would take the bot with it). Without
# DETACHED_PROCESS: the venv's python.exe is a launcher, and its real Python would open a new
# (empty) console window without one; a hidden console it is.
_LAUNCHER = """
import subprocess, sys
log, cmd = sys.argv[1], sys.argv[2:]
flags = 0x00000200 | 0x08000000 | 0x01000000  # new group | no window | breakaway
with open(log, 'ab') as out:
    for f in (flags, flags & ~0x01000000):  # a job may forbid breakaway
        try:
            subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=out,
                             stderr=subprocess.STDOUT, creationflags=f)
            break
        except OSError:
            if f == flags & ~0x01000000:
                raise
"""


def _spawn_detached(command: list[str], log_file: Path) -> object:
    if sys.platform == "win32":
        launch = [sys.executable, "-c", _LAUNCHER, str(log_file), *command]
        base = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        try:
            return _popen_quiet(launch, base | subprocess.CREATE_BREAKAWAY_FROM_JOB)
        except OSError:  # the app's job forbids breakaway: still better than not starting
            return _popen_quiet(launch, base)
    with log_file.open("ab") as out:
        return subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
            start_new_session=True,
        )  # fmt: skip


def _popen_quiet(command: list[str], flags: int) -> object:
    return subprocess.Popen(
        command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=flags,
    )  # fmt: skip


def start_bot(
    out_dir: Path,
    now: datetime,
    spawn: Spawn = _spawn_detached,
    settings: dict | None = None,
    alive: Callable[[int], bool] = pid_alive,
) -> str:
    """Start the bot unless a fresh heartbeat shows it running. `settings` (validated, see
    `live_model.validate_settings`) become its command line. Returns a message."""
    if lm.bot_state(read_status(out_dir / STATUS_NAME), now) in ("running", "paused"):
        return "The bot is already running (fresh heartbeat); not started again."
    holder = lock_holder(out_dir / LOCK_NAME, alive)
    if holder is not None:  # no heartbeat yet (starting, or stuck connecting) but a bot holds it
        return "The bot is already running (lock file held); not started again."
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
    when = lm.hm_ch(entry.get("time", ""), seconds=True)
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


def live_view(out_dir: Path, now: datetime, stale_minutes=lm.DISPLAY_STALE_MINUTES) -> dict:
    status = read_status(out_dir / STATUS_NAME)
    state = lm.bot_state(status, now)
    if state == "running" and is_paused(out_dir):
        state = "paused"  # the file is the newest word; the heartbeat catches up
    return {
        "status": status,
        "age": heartbeat_age_s(status, now),
        "state": state,
        "display_stale": lm.display_stale(status, now, stale_minutes),
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


def _fold(title: str, body, extra: str = "", open_: bool = False) -> html.Details:
    """A card the user folds by its title (the clickable summary); closed unless `open_`
    (ROADMAP 7.7: what concerns the day is open by default)."""
    body = html.Div(body) if isinstance(body, list) else body  # no nested lists in Dash children
    return html.Details(
        [html.Summary(title, className="lv-summary"), html.Div(body, className="lv-fold-body")],
        className=f"lv-card lv-fold {extra}".strip(),
        open=open_,
    )


def _range_picker(id_: str) -> dcc.RadioItems:
    """Day / Week / All window of a trades card, Day first."""
    return dcc.RadioItems(
        id=id_,
        options=[{"label": k.title(), "value": k} for k in lm.RANGES],
        value="day",
        className="lv-seg lv-fold-right",
        inline=True,
    )


def render_head(view: dict, now: datetime) -> html.Div:
    status, state = view["status"] or {}, view["state"]
    label, css = STATE_BADGE[state]
    if _historical(view):
        label, css = "Stopped", "idle"
    symbols = status.get("symbols") or []
    meta = [
        status.get("account_mode") or DASH,
        ", ".join(symbols) or DASH,
        f"{lm.window_text(status.get('session'))} · {lm.countdown_text(status.get('session'), now)}",
    ]
    if _historical(view):
        meta[-1] = lm.last_session_text(status)
    if state in ("running", "paused") and not _historical(view):
        meta.append(f"running since {lm.clock_ch(status.get('started_at'))}")
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
        parts.append(ui.info("Bot not started yet (no status file)."))
    elif state == "stale":
        age = view["age"]
        gap = f" for {age / 60:.0f} min" if age is not None else ""
        parts.append(ui.info(f"No heartbeat{gap}: the bot is not running."))
    if status.get("last_error"):
        parts.append(html.Div(f"Last error: {status['last_error']}", className="lv-error"))
    return html.Div(parts)


def _historical(view: dict) -> bool:
    age = view["age"]
    return view["status"] is not None and view.get(
        "display_stale",
        age is None or age > lm.DISPLAY_STALE_MINUTES * 60 or view["state"] == "stopped",
    )


def _last_session(view: dict):
    return html.Div(lm.last_session_text(view["status"]), className="lv-sub")


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
    stale = _historical(view)
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
                    className="lv-big lv-small"
                    + (" lv-stale" if view["status"] and lm.heartbeat_stale(age) else ""),
                ),
                html.Div(
                    DASH if link is None else ("MT5 connected" if link else "MT5 not connected"),
                    className="lv-sub",
                ),
            ],
        ),
    ]
    if stale:
        for card in cards[2:4]:
            card.className += " lv-last-session"
            card.children.append(_last_session(view))
        cards[-1].children[1].children[-1].children = lm.last_seen_text(status, age)
    return html.Div(cards, className="lv-cards" + (" lv-last-state" if stale else ""))


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
    blocks = [_last_session(view)] if _historical(view) else []
    if not symbols:
        blocks.append(html.Div("No symbols yet.", className="lv-empty"))
    for symbol in symbols:
        rows = lm.funnel_rows(setups.get(symbol))
        steps = [
            html.Div(
                [
                    html.Span(STEP_MARK.get(r["state"], ""), className="lv-dot"),
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
    return html.Div(
        blocks, className="lv-funnels" + (" lv-last-session" if _historical(view) else "")
    )


def chart_link(row: dict):
    """ "Chart →" link that opens a live trade / position on the chart with its order (entry and
    SL; the bot records no TP), or a dash when the row is no order."""
    href = trade_focus.live_link(row)
    return dcc.Link("Chart →", href=href, className="lv-link") if href else DASH


def render_closed(trades: list[dict]) -> html.Div:
    """The closed trades of the chosen window, newest first, each with its chart link."""
    return _table(
        ["Entry (CH)", "Symbol", "Side", "R", "Chart"],
        [
            [
                lm.hm_ch(t.get("entry_time", "")) or DASH,
                t.get("symbol", ""),
                t.get("side", ""),
                f"{t.get('r_net', 0.0):+.2f}",
                chart_link(t),
            ]
            for t in reversed(trades)
        ],
        "none yet",
    )


def render_positions(view: dict) -> html.Div:
    return _table(
        ["Symbol", "Side", "Lots", "Entry", "SL", "Floating R", "Chart"],
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
                chart_link(p),
            ]
            for p in (view["status"] or {}).get("positions") or []
        ],
        "none",
    )


def render_signals(view: dict) -> html.Div:
    return _table(
        ["Time (CH)", "Symbol", "Side", "Result", "Reason"],
        [
            [
                lm.hm_ch(s.get("time", "")),
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


def trades_figure(strip: dict, trades: list[dict] | None = None) -> go.Figure:
    """Bars in % of the balance (green / red) and the balance line in USD (right axis). `trades`
    (the strip's trades, same order): a click on a bar opens that trade on the chart."""
    fig = go.Figure()
    n = len(strip["pct"])
    if n:
        x = list(range(1, n + 1))
        fig.add_bar(
            x=x, y=strip["pct"], hovertext=strip["labels"], name="trade %", hovertemplate="%{hovertext}<br>%{y:+.2f} %<extra></extra>",
            marker_color=["#2ebd85" if v >= 0 else "#f6465d" for v in strip["pct"]],
            customdata=[trade_focus.live_link(t) for t in trades or []] or None,
        )  # fmt: skip
        fig.add_scatter(
            x=x, y=strip["balance"], yaxis="y2", name="balance", mode="lines",
            line={"color": "#4f8cff", "width": 2}, hovertemplate="$%{y:,.0f}<extra></extra>",
        )  # fmt: skip
    else:
        fig.add_annotation(
            text="No trades yet", showarrow=False, font={"color": theme_color("muted")}
        )
    axis = {
        "gridcolor": theme_color("line"),
        "zerolinecolor": theme_color("line"),
        "color": theme_color("muted"),
    }
    fig.update_layout(
        height=400, margin={"l": 40, "r": 56, "t": 8, "b": 28}, showlegend=False,
        paper_bgcolor=theme_color("panel"), plot_bgcolor=theme_color("panel"),
        font={"family": "ui-monospace, Consolas, monospace", "size": 11, "color": theme_color("muted")},
        xaxis={**axis, "title": "trade", "dtick": 1 if n <= 20 else None},
        yaxis={**axis, "ticksuffix": " %"},
        yaxis2={"overlaying": "y", "side": "right", "color": theme_color("muted"), "showgrid": False,
                "tickprefix": "$", "tickformat": ",.0f"},
    )  # fmt: skip
    if not n:  # no data: hide the axes plotly would draw with a made-up range
        fig.update_layout(xaxis_visible=False, yaxis_visible=False)
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
        "emergency_disabled": view["state"] in ("none", "stopped"),
    }


def layout(out_dir: Path = LIVE_DIR, now: datetime | None = None) -> html.Div:
    now = now or datetime.now(UTC)
    view = live_view(out_dir, now)
    pieces = render(view, now)
    settings = settings_state(view)
    buttons = button_state(view)
    chosen = settings["symbols"] or list(lm.DEFAULT_SYMBOLS)
    header = html.Div(
        [
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
                                html.Button(
                                    "Close all & stop",
                                    id="lv-emergency-btn",
                                    className="lv-btn lv-danger",
                                    disabled=buttons["emergency_disabled"],
                                ),
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
            html.Div(pieces["cards"], id="lv-cards"),
        ],
        id="lv-key-strip",
        className="ui-key-strip lv-strip",
    )
    main = _card(
        "Recent trades",
        [
            _range_picker("lv-range"),
            ui.info("Click a bar to open the trade on the chart."),
            dcc.Graph(
                id="lv-trades",
                figure=trades_figure(lm.trade_strip([], None, "day", now)),
                config={"displayModeBar": False, "responsive": True},
            ),
        ],
    )
    settings_panel = html.Div(
        [
            html.Div(
                [
                    _field(
                        "Mark status stale after (minutes)",
                        dcc.Input(
                            id="lv-stale-minutes",
                            type="number",
                            min=1,
                            step=1,
                            value=lm.DISPLAY_STALE_MINUTES,
                            persistence=True,
                            persistence_type="local",
                            className="lv-input",
                        ),
                    ),
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
            ui.info(
                f"Editable only while the bot is not running; Start passes them to the bot. "
                f"Risk 0 to {lm.MAX_RISK_PERCENT:g} %, daily stop 0 to "
                f"{lm.MAX_DAILY_STOP_PERCENT:g} %, at least one symbol.",
            ),
        ]
    )
    panels = [
        ("positions", "Open positions", html.Div(pieces["positions"], id="lv-positions")),
        (
            "closed",
            "Closed trades",
            html.Div(
                [_range_picker("lv-closed-range"), html.Div(render_closed([]), id="lv-closed")]
            ),
        ),
        ("signals", "Signals & skips", html.Div(pieces["signals"], id="lv-signals")),
        (
            "log",
            "Event log",
            html.Div(
                [
                    ui.info(f"last {LOG_LINES}, times in Swiss time"),
                    html.Pre(pieces["log"], id="lv-log", className="lv-log"),
                ]
            ),
        ),
        ("settings", "Settings", settings_panel),
    ]
    tabs = html.Div(
        [
            ui.tabs_below(
                [dcc.Tab(label=label, value=name) for name, label, _ in panels],
                id="lv-tabs",
                value="positions",
            ),
            *[
                html.Div(
                    body,
                    id=f"lv-tab-{name}",
                    style={} if name == "positions" else {"display": "none"},
                    className="lv-tab-content",
                )
                for name, _, body in panels
            ],
        ]
    )
    return html.Div(
        [
            dcc.Interval(id="lv-interval", interval=REFRESH_MS),
            ui.page(
                header,
                [html.Div(id="lv-msg", className="lv-msg"), main],
                side=_card("Setup in progress", html.Div(pieces["setup"], id="lv-setup")),
                tabs=tabs,
            ),
            html.Div(trading_panel.layout(), id="connection"),
        ],
        className="lv-page",
    )


def _field(label: str, control) -> html.Div:
    return html.Div([html.Div(label, className="lv-sub"), control], className="lv-field")


def register_callbacks(app: Dash, out_dir: Path = LIVE_DIR) -> None:
    trading_panel.register_callbacks(app)

    @app.callback(
        [
            Output(f"lv-tab-{name}", "style")
            for name in ("positions", "closed", "signals", "log", "settings")
        ],
        Input("lv-tabs", "value"),
    )
    def _tabs(selected):
        # All callback targets stay mounted, including settings used by Start.
        return [
            {} if selected == name else {"display": "none"}
            for name in ("positions", "closed", "signals", "log", "settings")
        ]

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
        Output("lv-emergency-btn", "disabled"),
        Output("lv-risk", "disabled"),
        Output("lv-daily-stop", "disabled"),
        Output("lv-symbols", "options"),
        Output("lv-risk", "value"),
        Output("lv-daily-stop", "value"),
        Output("lv-symbols", "value"),
        Input("lv-interval", "n_intervals"),
        Input("lv-stale-minutes", "value"),
        State("lv-symbols", "value"),
    )
    def _refresh(_, stale_minutes, chosen):
        now = datetime.now(UTC)
        view = live_view(out_dir, now, stale_minutes)
        p, b, s = render(view, now), button_state(view), settings_state(view)
        keep = s["symbols"] or chosen
        return (
            p["head"], p["cards"], p["setup"], p["positions"], p["signals"], p["log"],
            b["start_disabled"], b["pause_label"], b["pause_disabled"], b["stop_disabled"],
            b["emergency_disabled"],
            s["disabled"], s["disabled"], symbol_options(keep, s["disabled"]),
            no_update if s["risk"] is None else s["risk"],
            no_update if s["stop"] is None else s["stop"],
            no_update if s["symbols"] is None else s["symbols"],
        )  # fmt: skip

    @app.callback(
        Output("lv-trades", "figure"),
        Output("lv-closed", "children"),
        Input("lv-interval", "n_intervals"),
        Input("lv-range", "value"),
        Input("lv-closed-range", "value"),
    )
    def _trades(_, range_key, closed_key):
        now = datetime.now(UTC)
        status = read_status(out_dir / STATUS_NAME) or {}
        trades = lm.read_trades(out_dir)
        strip = lm.trade_strip(trades, status.get("initial_balance"), range_key, now)
        shown = lm.window_trades(trades, range_key, now)
        closed = lm.window_trades(trades, closed_key or "day", now)
        return trades_figure(strip, shown), render_closed(closed)

    app.clientside_callback(  # a click on a bar: open that trade on the chart
        "function (click) { const p = click && click.points && click.points[0];"
        " if (p && typeof p.customdata === 'string') window.location.assign(p.customdata);"
        " return window.dash_clientside.no_update; }",
        Output("lv-trades", "className"),
        Input("lv-trades", "clickData"),
        prevent_initial_call=True,
    )

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
