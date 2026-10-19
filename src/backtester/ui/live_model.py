"""Pure helpers of the /live page and the top bar (ROADMAP 7.3): no Dash, no MT5.

Everything the page shows is derived here from `results/live/status.json` (a dict, fields may be
missing: the page then shows "–") and the bot's `trades.csv` files, so it is unit-tested without a
browser. Spec: docs/live-trading.md › App layout and Live page.

Times: everything on the page is shown in Swiss time ("CH", Europe/Zurich, DST-aware; user,
2026-10-17); status.json and the logs stay in UTC.
"""

from __future__ import annotations

import csv
import math
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from backtester.live.bot import FORWARD_SYMBOLS, BotConfig
from backtester.live.status import STALE_S, heartbeat_age_s, is_fresh
from backtester.risk.prop_rules import GuardConfig

SWISS = ZoneInfo("Europe/Zurich")
DASH = "–"

# Limits of the editable settings (user, 2026-10-17: "risk > 0 and <= 2, daily stop > 0 and <= 5").
MAX_RISK_PERCENT = 2.0
MAX_DAILY_STOP_PERCENT = 5.0
DEFAULT_RISK = BotConfig.risk_percent
_GUARD = GuardConfig()  # slots dataclass: read defaults from an instance
DEFAULT_DAILY_STOP = _GUARD.daily_stop_percent
DEFAULT_SYMBOLS = FORWARD_SYMBOLS
WARN_FRACTION = 0.5  # a loss bar turns amber from this share of its limit

LIVE_PATH = "/live"
BOT_MODULE = "backtester.live.bot"
STAGES = (
    "waiting_session", "range_forming", "range_set", "waiting_breakout",
    "volume_passed", "entered", "done",
)  # fmt: skip
STAGE_LABELS = {
    "waiting_session": "Waiting for the session",
    "range_forming": "Opening range forming",
    "range_set": "Range set",
    "waiting_breakout": "Waiting for the breakout",
    "volume_passed": "Volume filter passed",
    "entered": "Entered",
    "done": "Done for today",
}
RANGES = {"day": 1, "week": 7, "all": None}  # window in days
_DAY_FOLDER = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# --- time ----------------------------------------------------------------------------------------


def _parse_utc(text) -> datetime | None:
    try:
        when = datetime.fromisoformat(str(text))
    except ValueError:
        return None
    return when.astimezone(UTC) if when.tzinfo is not None else None


def _number(value) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def fmt_duration(seconds: float) -> str:
    minutes = int(max(0.0, seconds) // 60)
    if minutes < 1:
        return "<1 min"
    hours, mins = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days:
        return f"{days} d {hours} h" if hours else f"{days} d"
    if hours:
        return f"{hours} h {mins} min" if mins else f"{hours} h"
    return f"{mins} min"


def clock_ch(text) -> str:
    when = _parse_utc(text)
    return f"{when.astimezone(SWISS):%H:%M} CH" if when else DASH


def hm_ch(text, seconds: bool = False) -> str:
    """Swiss clock time for table cells ("" when the time is missing or naive)."""
    when = _parse_utc(text)
    return (
        f"{when.astimezone(SWISS):%H:%M:%S}"
        if when and seconds
        else (f"{when.astimezone(SWISS):%H:%M}" if when else "")
    )


def window_text(session: dict | None) -> str:
    """ "US open 15:30–22:00 CH"."""
    s = session or {}
    start, end = _parse_utc(s.get("open_utc")), _parse_utc(s.get("close_utc"))
    if start is None or end is None:
        return DASH
    span = f"{start.astimezone(SWISS):%H:%M}–{end.astimezone(SWISS):%H:%M} CH"
    return f"{s['name']} {span}" if s.get("name") else span


def countdown_text(session: dict | None, now: datetime) -> str:
    """ "US open in 2 h 14 min" before the window, "open, 47 min left" inside it."""
    s = session or {}
    start, end = _parse_utc(s.get("open_utc")), _parse_utc(s.get("close_utc"))
    if start is not None and end is not None:  # the times decide: the status may be a minute old
        if start <= now < end:
            return f"open, {fmt_duration((end - now).total_seconds())} left"
        if now < start:
            wait = fmt_duration((start - now).total_seconds())
            return f"{s['name']} in {wait}" if s.get("name") else f"opens in {wait}"
        return "closed"
    if "is_open" in s:
        return "open" if s["is_open"] else "closed"
    return DASH


def heartbeat_text(age: float | None) -> str:
    if age is None:
        return DASH
    age = max(0.0, age)
    if age < 60:
        return f"checked {int(age)} s ago"
    return f"checked {int(age // 60)} min ago"


def heartbeat_stale(age: float | None) -> bool:
    return age is None or age > STALE_S


# --- bars ----------------------------------------------------------------------------------------


def _level(fraction: float) -> str:
    return "breach" if fraction >= 1 else "warn" if fraction >= WARN_FRACTION else "ok"


def today_bar(status: dict) -> dict:
    """Today's loss against the own daily stop (fraction 0 .. 1 of the stop)."""
    guard = status.get("guard") or {}
    stop = _number(guard.get("daily_stop_percent")) or DEFAULT_DAILY_STOP
    pl = _number(status.get("day_pl_percent")) or 0.0
    loss = max(0.0, -pl)
    fraction = min(1.0, loss / stop)
    level = "ok"
    if guard.get("state") == "breach":
        level = "breach"
    elif guard.get("state") == "stopped" or fraction >= 1:
        level = "stopped"
    return {"loss": loss, "stop": stop, "fraction": fraction, "level": level}


def ftmo_bars(status: dict) -> list[dict]:
    """[daily, max]: loss used against FTMO's 5 % daily and 10 % max limits.

    `used` is None when the numbers are missing (the page shows "–")."""
    guard = status.get("guard") or {}
    daily_limit = _number(guard.get("ftmo_daily_percent")) or _GUARD.ftmo_daily_loss_percent
    max_limit = _number(guard.get("ftmo_max_percent")) or _GUARD.ftmo_max_loss_percent
    pl = _number(status.get("day_pl_percent"))
    equity = _number(status.get("equity"))
    initial = _number(status.get("initial_balance"))
    daily_used = None if pl is None else max(0.0, -pl)
    max_used = None
    if equity is not None and initial:
        max_used = max(0.0, (initial - equity) / initial * 100)
    out = []
    for label, used, limit in (
        ("Daily loss", daily_used, daily_limit),
        ("Max loss", max_used, max_limit),
    ):
        fraction = 0.0 if used is None else min(1.0, used / limit)
        out.append({
            "label": label, "used": used, "limit": limit, "fraction": fraction,
            "left": None if used is None else max(0.0, limit - used), "level": _level(fraction),
        })  # fmt: skip
    return out


# --- state and top bar ---------------------------------------------------------------------------


def bot_state(status: dict | None, now: datetime) -> str:
    """none (no file) / stale (heartbeat too old) / stopped / paused / running."""
    if status is None:
        return "none"
    age = heartbeat_age_s(status, now)
    if age is None or age > STALE_S:
        return "stale"
    if not status.get("running"):
        return "stopped"
    return "paused" if status.get("paused") else "running"


def nav_view(status: dict | None, now: datetime) -> dict:
    """The top bar: is the Live button red, and the status text on the right."""
    state = bot_state(status, now)
    if state not in ("running", "paused"):
        return {"live": False, "text": "Bot not running", "level": "idle"}
    connected = bool((status or {}).get("connected"))
    text = f"MT5 {'connected' if connected else 'not connected'} · bot {state}"
    return {"live": True, "text": text, "level": "ok" if connected else "warn"}


def landing_path(pathname: str | None, landed: bool, status: dict | None, now: datetime):
    """ "/live" when the app is opened (first load of a browser session) on "/" while the bot
    runs, else None (stay)."""
    if landed or pathname != "/":
        return None
    return LIVE_PATH if is_fresh(status, now) else None


# --- setup funnel --------------------------------------------------------------------------------


def funnel_rows(setup: dict | None) -> list[dict]:
    """The stages of a setup: earlier ones done, the current one highlighted, later ones todo."""
    setup = setup or {}
    at = STAGES.index(setup["stage"]) if setup.get("stage") in STAGES else None
    rows = []
    for i, key in enumerate(STAGES):
        if at is None:
            state = "todo"
        elif key == "done" and at == i:
            state = "done"  # finished: everything ticked
        else:
            state = "done" if i < at else "current" if i == at else "todo"
        detail = str(setup.get("detail") or "") if at == i else ""
        rows.append({"key": key, "label": STAGE_LABELS[key], "state": state, "detail": detail})
    return rows


# --- trades --------------------------------------------------------------------------------------


def read_trades(out_dir: Path) -> list[dict]:
    """All closed trades of the bot (`<out_dir>/<YYYY-MM-DD>/trades.csv`), oldest exit first.
    Rows without a readable money value are skipped; a broken file is ignored."""
    try:
        folders = sorted(p for p in Path(out_dir).iterdir() if _DAY_FOLDER.match(p.name))
    except OSError:
        return []
    trades = []
    for folder in folders:
        try:
            with (folder / "trades.csv").open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
        except (OSError, UnicodeDecodeError, csv.Error):
            continue
        for row in rows:
            money = _number(row.get("money"))
            if money is None:
                continue
            trades.append({
                "symbol": row.get("symbol", ""), "exit_time": row.get("exit_time", ""),
                "money": money, "r_net": _number(row.get("r_net")) or 0.0,
                # what the chart needs to draw the order (ROADMAP 7.6); the bot records no TP
                "side": row.get("side", ""), "entry_time": row.get("entry_time", ""),
                "entry_fill": row.get("entry_fill", ""), "sl": row.get("sl", ""),
                "exit_price": row.get("exit_price", ""),
            })  # fmt: skip
    trades.sort(key=lambda t: t["exit_time"])
    return trades


def _window_cutoff(range_key: str, now: datetime):
    days = RANGES.get(range_key)
    return days, None if days is None else now.astimezone(UTC) - timedelta(days=days)


def _in_window(trade: dict, days, cutoff, now: datetime) -> bool:
    if cutoff is None:
        return True
    when = _parse_utc(trade["exit_time"])
    if when is None:
        return False
    return when.date() == now.astimezone(UTC).date() if days == 1 else when >= cutoff


def window_trades(trades: list[dict], range_key: str, now: datetime) -> list[dict]:
    """The trades of a window ("day" = today UTC, "week", "all"), oldest exit first: the ones
    `trade_strip` draws (the Live page's bars and its closed-trades table)."""
    days, cutoff = _window_cutoff(range_key, now)
    ordered = sorted(trades, key=lambda t: t["exit_time"])
    return [t for t in ordered if _in_window(t, days, cutoff, now)]


def trade_strip(trades: list[dict], initial_balance, range_key: str, now: datetime) -> dict:
    """Bars in % of the balance before each trade and the balance line in USD for a window.

    Earlier trades still count toward the balance. Without a usable initial balance the percent
    is 0 and the line is the cumulative P/L."""
    base = _number(initial_balance)
    days, cutoff = _window_cutoff(range_key, now)
    balance = base if base and base > 0 else 0.0
    out = {"pct": [], "balance": [], "labels": [], "total": 0.0}
    for t in sorted(trades, key=lambda t: t["exit_time"]):
        before = balance
        balance += t["money"]
        if not _in_window(t, days, cutoff, now):
            continue
        out["pct"].append(t["money"] / before * 100 if base and base > 0 and before > 0 else 0.0)
        out["balance"].append(balance)
        out["labels"].append(f"{t['symbol']} {_stamp(t['exit_time'])}")
        out["total"] += t["money"]
    return out


def _stamp(exit_time: str) -> str:
    when = _parse_utc(exit_time)
    return f"{when.astimezone(SWISS):%Y-%m-%d %H:%M} CH" if when else exit_time


# --- settings ------------------------------------------------------------------------------------


def validate_settings(risk, daily_stop, symbols) -> tuple[dict | None, str]:
    """(clean settings, "") or (None, the reason)."""
    r = _number(risk)
    if r is None or not 0 < r <= MAX_RISK_PERCENT:
        return None, f"Risk per trade must be above 0 and at most {MAX_RISK_PERCENT:g} %."
    d = _number(daily_stop)
    if d is None or not 0 < d <= MAX_DAILY_STOP_PERCENT:
        return None, f"Daily stop must be above 0 and at most {MAX_DAILY_STOP_PERCENT:g} %."
    chosen = [str(s) for s in symbols or []]
    if not chosen:
        return None, "Choose at least one symbol."
    return {"risk": r, "daily_stop": d, "symbols": chosen}, ""


def start_command(settings: dict | None) -> list[str]:
    """`python -m backtester.live.bot [--symbols ... --risk X --daily-stop Y]`."""
    cmd = [sys.executable, "-m", BOT_MODULE]
    if settings:
        cmd += ["--symbols", *settings["symbols"], "--risk", f"{settings['risk']:g}"]
        cmd += ["--daily-stop", f"{settings['daily_stop']:g}"]
    return cmd
