"""`results/live/status.json`: the bot's state for the /live page and Telegram's /status.

The bot writes it once per minute and on every event (atomic: temp file + rename, so a reader
never sees half a file). It holds no secrets: no login, password, server, token or chat id.
Spec: docs/live-trading.md › Monitoring.
"""

from __future__ import annotations

import contextlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

STATUS_NAME = "status.json"
STALE_S = 120.0  # a heartbeat older than this means the bot is not running


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
    }
