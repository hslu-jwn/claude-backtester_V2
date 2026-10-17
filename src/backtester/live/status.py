"""`results/live/status.json`: the bot's state for the /live page and Telegram's /status.

The bot writes it once per minute and on every event (atomic: temp file + rename, so a reader
never sees half a file). It holds no secrets: no login, password, server, token or chat id.
Spec: docs/live-trading.md › Monitoring, App layout and Live page.

Keys added for the /live page (ROADMAP 7.3), next to the older ones (running, connected, balance,
equity, guard, positions, signals, ...):
  "paused":       bool, the PAUSE file exists (no new entries, open trades still managed)
  "risk_percent": float, risk per trade in % of the balance
  "strategy":     short name of the strategy (STRATEGY_NAME)
  "session":      {"name", "open_utc", "close_utc" (ISO, UTC), "is_open"}: the current session
                  window if open, else the next one (weekends skipped, holidays not known)
  "setups":       {symbol: {"stage", "detail", "time"}}; stage is one of STAGES, "time" is when
                  the symbol entered that stage
"""

from __future__ import annotations

import contextlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from backtester.strategy.opening_range.config import SYMBOL_CLASS, SessionSpec

STATUS_NAME = "status.json"
STALE_S = 120.0  # a heartbeat older than this means the bot is not running
STRATEGY_NAME = "Opening-range breakout"
STAGES = (
    "waiting_session", "range_forming", "range_set", "waiting_breakout",
    "volume_passed", "entered", "done",
)  # fmt: skip
MAX_SKIP_DAYS = 8  # days searched for the next session (weekends, long breaks)


def write_status(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")
        os.replace(tmp, path)
    finally:
        with contextlib.suppress(OSError):
            tmp.unlink()


def read_status(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def heartbeat_age_s(status: dict | None, now: datetime | None = None) -> float | None:
    """Seconds since the last heartbeat, or None when there is none."""
    try:
        beat = datetime.fromisoformat(str((status or {}).get("heartbeat")))
    except ValueError:
        return None
    if beat.tzinfo is None:
        return None
    return ((now or datetime.now(UTC)) - beat).total_seconds()


def is_fresh(status: dict | None, now: datetime | None = None) -> bool:
    age = heartbeat_age_s(status, now)
    return age is not None and age <= STALE_S and bool((status or {}).get("running"))


def summary_text(status: dict | None) -> str:
    """The short status for Telegram's /status."""
    if not status:
        return "no status yet"
    guard = status.get("guard") or {}
    state = "running" if status.get("running") else "not running"
    link = "connected" if status.get("connected") else "not connected"
    text = (
        f"{state}, {link} ({status.get('account_mode') or '?'}). "
        f"Equity {status.get('equity', 0):,.0f}, day {status.get('day_pl_percent', 0):+.1f} % "
        f"({status.get('day_r', 0):+.1f} R), open {len(status.get('positions') or [])}, "
        f"guard {guard.get('state', '?')}."
    )
    if status.get("last_error"):
        text += f" Last error: {status['last_error']}"
    return text


def session_window(now: datetime, name: str, spec: SessionSpec) -> dict:
    """The session window of `spec` that holds `now`, else the next one (Saturdays and Sundays
    skipped; exchange holidays are not known). Times in UTC, computed in the session zone."""
    tz = ZoneInfo(spec.zone)
    day = now.astimezone(tz).date()
    for _ in range(MAX_SKIP_DAYS):
        if day.weekday() < 5:
            open_at = datetime.combine(day, spec.open_time, tzinfo=tz)
            close_at = datetime.combine(day, spec.exit_time, tzinfo=tz)
            if now <= close_at:
                break
        day += timedelta(days=1)
    return {
        "name": name,
        "open_utc": open_at.astimezone(UTC).isoformat(),
        "close_utc": close_at.astimezone(UTC).isoformat(),
        "is_open": open_at <= now <= close_at,
    }


def _session(cfg, now: datetime) -> dict | None:
    sessions = cfg.strategy.sessions.get(SYMBOL_CLASS.get(cfg.symbols[0], ""), {})
    for key, spec in sessions.items():
        return session_window(now, key.replace("_", " ").title(), spec)
    return None


def _fmt(x: float) -> str:
    return f"{x:.10g}"


def _detail(bot, symbol: str, stage: str, state) -> str:
    cfg = bot.config.strategy
    if stage == "waiting_session":
        return "waiting for the session open"
    if stage == "range_forming":
        return "waiting for the range to form"
    if stage in ("range_set", "waiting_breakout"):
        return f"range {_fmt(state.down)}-{_fmt(state.up)}"
    if stage == "volume_passed":
        return f"rel volume {state.rel_volume or 0:.1f} >= {cfg.min_rel_volume:.1f}, order pending"
    if stage == "entered":
        t = next((p for p in bot.open_positions() if p["symbol"] == symbol), None)
        return f"{t['side']} {t['lots']:g} lots at {_fmt(t['entry'])}" if t else "in a trade"
    if state.traded:
        return "traded today"
    if state.rel_volume is not None and state.rel_volume < cfg.min_rel_volume:
        return f"rel volume {state.rel_volume:.1f} < {cfg.min_rel_volume:.1f}, skipped"
    return "no trade today"


def build_setups(bot, now: datetime) -> dict:
    """Stage of every symbol (see STAGES), from the strategy read-only `setup_state`."""
    out = {}
    held = {t.symbol for t in bot.by_ticket.values()}
    for name, sym in bot.symbols.items():
        state = sym.strategy.setup_state(now)
        stage = state.phase
        if name in held:
            stage = "entered"
        elif stage == "ordered":
            stage = "volume_passed"
        detail = _detail(bot, name, stage, state)
        before = bot.setup_since.get(name)
        if before is None or before[0] != stage:
            bot.setup_since[name] = (stage, now.isoformat())
        out[name] = {"stage": stage, "detail": detail, "time": bot.setup_since[name][1]}
    return out


def build_status(bot, now: datetime) -> dict:
    """The status of a running `Bot` (duck-typed; see live/bot.py)."""
    cfg = bot.config
    guard_cfg, guard = cfg.guard, bot.status
    account = None
    try:
        account = bot.mt5.account_info() if bot.connected else None
    except Exception:  # noqa: BLE001 - a dead terminal must not stop the status
        account = None
    state = "ok"
    if guard is not None and guard.breach:
        state = "breach"
    elif bot.blocked:
        state = "stopped"
    today = now.strftime("%Y-%m-%d")
    return {
        "running": bot.running,
        "connected": bot.connected,
        "account_mode": bot.account_mode,
        "heartbeat": now.isoformat(),
        "started_at": bot.started_at.isoformat() if bot.started_at else "",
        "date": today,
        "symbols": list(cfg.symbols),
        "balance": getattr(account, "balance", 0.0),
        "equity": getattr(account, "equity", 0.0),
        "day_pl": guard.day_pl if guard else 0.0,
        "day_pl_percent": guard.day_pl_percent if guard else 0.0,
        "day_r": bot.day_r,
        "initial_balance": bot.initial_balance,
        "guard": {
            "state": state,
            "reason": (guard.reason if guard else "") or bot.blocked,
            "daily_stop_percent": guard_cfg.daily_stop_percent,
            "ftmo_daily_percent": guard_cfg.ftmo_daily_loss_percent,
            "ftmo_max_percent": guard_cfg.ftmo_max_loss_percent,
            "initial_balance": bot.initial_balance,
        },
        "positions": bot.open_positions(),
        "signals": [s for s in bot.signals if s["time"].startswith(today)],
        "last_error": bot.last_error,
        "paused": bot.paused,
        "risk_percent": cfg.risk_percent,
        "strategy": STRATEGY_NAME,
        "session": _session(cfg, now),
        "setups": build_setups(bot, now),
    }
