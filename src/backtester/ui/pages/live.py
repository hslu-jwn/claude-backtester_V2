"""Live page `/live`: the demo bot at a glance. Spec: docs/live-trading.md › Monitoring.

Reads `results/live/status.json` (written by the bot every minute and on every event) and
today's `orders.jsonl` every few seconds; nothing is computed here. Shows connection and
account, day P/L, the daily-guard bar (own stop and the FTMO limit), open positions, today's
signals and skips with reasons and the last 50 log lines. A heartbeat older than 2 minutes is
shown in red.

Buttons: **Start** launches `python -m backtester.live.bot` as a detached process (it keeps
running when the web server stops) and refuses while a fresh heartbeat shows a running bot;
**Stop** creates `STOP` (stop, close nothing); **Emergency stop** creates `EMERGENCY` (close the
bot's positions, then stop) after a confirm dialog. The page never touches MT5 or the login.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from dash import Dash, Input, Output, dcc, html, no_update

from backtester.live.status import STALE_S, STATUS_NAME, heartbeat_age_s, is_fresh, read_status
from backtester.paths import RESULTS_DIR

LIVE_DIR = RESULTS_DIR / "live"
LOG_LINES = 50
REFRESH_MS = 3000
BOT_LOG = "bot_stdout.log"
Spawn = Callable[[list[str], Path], object]  # (command, stdout log file)


# --- actions ---------------------------------------------------------------------------------


def request_stop(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "STOP").touch()


def request_emergency(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "EMERGENCY").touch()


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


def start_bot(out_dir: Path, now: datetime, spawn: Spawn = _spawn_detached) -> str:
    """Start the bot unless a fresh heartbeat shows it running. Returns a message."""
    if is_fresh(read_status(out_dir / STATUS_NAME), now):
        return "The bot is already running (fresh heartbeat); not started again."
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("STOP", "EMERGENCY"):  # leftovers from an earlier stop must not stop the new run
        (out_dir / name).unlink(missing_ok=True)
    try:
        spawn([sys.executable, "-m", "backtester.live.bot"], out_dir / BOT_LOG)
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
    age = heartbeat_age_s(status, now)
    if status is None:
        state = "none"
    elif age is None or age > STALE_S:
        state = "stale"
    elif not status.get("running"):
        state = "stopped"
    else:
        state = "running"
    return {"status": status, "age": age, "state": state, "log": _read_log(out_dir, now)}


def guard_bar(status: dict) -> dict:
    """Today's loss against the own daily stop and the FTMO daily limit (scale 0 .. limit)."""
    guard = status.get("guard") or {}
    stop = float(guard.get("daily_stop_percent", 2.0))
    limit = float(guard.get("ftmo_daily_percent", 5.0))
    loss = max(0.0, -float(status.get("day_pl_percent", 0.0)))
    level = "ok"
    if guard.get("state") == "breach" or loss >= limit:
        level = "breach"
    elif guard.get("state") == "stopped" or loss >= stop:
        level = "stopped"
    return {
        "loss_percent": loss,
        "stop_percent": stop,
        "limit_percent": limit,
        "stop_at": stop / limit * 100,
        "fill_width": min(100.0, round(loss / limit * 100, 1)),
        "level": level,
    }


# --- rendering -------------------------------------------------------------------------------


def _kv(label: str, value) -> html.Div:
    return html.Div(
        [html.Span(label, className="lv-k"), html.Span(value, className="lv-v")], className="lv-kv"
    )


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


def _heartbeat(view: dict) -> html.Div:
    state, age = view["state"], view["age"]
    if state == "none":
        return html.Div("Bot not started yet (no status file).", className="lv-badge lv-idle")
    if state == "stale":
        text = (
            "No heartbeat" + (f" for {age / 60:.0f} min" if age is not None else "")
            + ": the bot is not running."
        )  # fmt: skip
        return html.Div(text, className="lv-badge lv-stale")
    if state == "stopped":
        return html.Div("Bot stopped.", className="lv-badge lv-idle")
    return html.Div(f"Running, heartbeat {age:.0f} s ago.", className="lv-badge lv-ok")


def render(view: dict) -> html.Div:
    status = view["status"]
    parts = [_heartbeat(view)]
    if status is None:
        return html.Div(parts, className="lv-body")
    bar = guard_bar(status)
    guard = status.get("guard") or {}
    link = "connected" if status.get("connected") else "NOT connected"
    parts += [
        html.Div(
            [
                _kv("Connection", link),
                _kv("Account", status.get("account_mode") or "?"),
                _kv("Balance", f"{status.get('balance', 0):,.2f}"),
                _kv("Equity", f"{status.get('equity', 0):,.2f}"),
                _kv("Initial balance", f"{status.get('initial_balance') or 0:,.2f}"),
                _kv(
                    "Day P/L",
                    f"{status.get('day_pl', 0):+,.2f} ({status.get('day_pl_percent', 0):+.1f} %, "
                    f"{status.get('day_r', 0):+.1f} R)",
                ),
                _kv("Symbols", ", ".join(status.get("symbols") or [])),
            ],
            className="lv-grid",
        ),
        html.Div("Daily guard", className="lv-h"),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            className=f"lv-fill lv-{bar['level']}",
                            style={"width": f"{bar['fill_width']}%"},
                        ),
                        html.Div(className="lv-mark", style={"left": f"{bar['stop_at']}%"}),
                    ],
                    className="lv-bar",
                ),
                html.Div(
                    f"loss today {bar['loss_percent']:.1f} %; own stop -{bar['stop_percent']:g} %"
                    f" (mark), FTMO daily limit -{bar['limit_percent']:g} % (end)."
                    + (f" {guard.get('reason')}" if guard.get("reason") else ""),
                    className="lv-help",
                ),
            ]
        ),
        html.Div("Open positions", className="lv-h"),
        _table(
            ["Symbol", "Side", "Lots", "Entry", "SL", "Floating R"],
            [
                [p["symbol"], p["side"], p["lots"], p["entry"], p["sl"], f"{p['floating_r']:+.2f}"]
                for p in status.get("positions") or []
            ],
            "none",
        ),
        html.Div("Today's signals and skips", className="lv-h"),
        _table(
            ["Time (UTC)", "Symbol", "Side", "Result", "Reason"],
            [
                [s["time"][11:16], s["symbol"], s.get("side", ""), s["status"], s.get("reason", "")]
                for s in status.get("signals") or []
            ],
            "none yet",
        ),
    ]
    if status.get("last_error"):
        parts.append(html.Div(f"Last error: {status['last_error']}", className="lv-error"))
    parts += [
        html.Div(f"Last {LOG_LINES} log lines", className="lv-h"),
        html.Pre("\n".join(view["log"]) or "(empty)", className="lv-log"),
    ]
    return html.Div(parts, className="lv-body")


def layout() -> html.Div:
    return html.Div(
        [
            dcc.Interval(id="lv-interval", interval=REFRESH_MS),
            html.Div(
                [
                    dcc.Link("← Chart", href="/", className="rs-back"),
                    html.Div("Live demo bot", className="lv-title"),
                ],
                className="lv-top",
            ),
            html.Div(
                [
                    html.Button("Start", id="lv-start", className="lv-btn lv-go", n_clicks=0),
                    html.Button("Stop", id="lv-stop", className="lv-btn", n_clicks=0),
                    dcc.ConfirmDialogProvider(
                        html.Button("Emergency stop", className="lv-btn lv-danger"),
                        id="lv-emergency",
                        message=(
                            "Emergency stop: close ALL positions opened by the bot and stop it. "
                            "Continue?"
                        ),
                    ),
                    html.Span(id="lv-msg", className="lv-msg"),
                ],
                className="lv-actions",
            ),
            html.Div(id="lv-view", children=render(live_view(LIVE_DIR, datetime.now(UTC)))),
        ],
        className="lv-page",
    )


def register_callbacks(app: Dash, out_dir: Path = LIVE_DIR) -> None:
    @app.callback(Output("lv-view", "children"), Input("lv-interval", "n_intervals"))
    def _refresh(_):
        return render(live_view(out_dir, datetime.now(UTC)))

    @app.callback(
        Output("lv-msg", "children"),
        Input("lv-start", "n_clicks"),
        Input("lv-stop", "n_clicks"),
        Input("lv-emergency", "submit_n_clicks"),
        prevent_initial_call=True,
    )
    def _buttons(start, stop, emergency):
        from dash import ctx

        which = ctx.triggered_id
        if which == "lv-start" and start:
            return start_bot(out_dir, datetime.now(UTC))
        if which == "lv-stop" and stop:
            request_stop(out_dir)
            return "STOP requested: the bot stops at its next cycle (nothing is closed)."
        if which == "lv-emergency" and emergency:
            request_emergency(out_dir)
            return "EMERGENCY requested: the bot closes its positions at its next cycle."
        return no_update
