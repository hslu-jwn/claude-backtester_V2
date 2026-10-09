"""Order functions, demo accounts only. Spec: ROADMAP.md › 7.1.

**DEMO LOCK:** every function here first checks `account_info().trade_mode` and refuses
(`DemoLockError`, before anything is sent) unless the account is a DEMO account. There is
no override yet.

Orders carry `MAGIC`, so the backtester's positions can be told from the user's own.
Every request and its result (retcode, fill, execution time) goes to an `OrderLog`.
The filling mode is the first one the symbol allows (FOK, IOC, then RETURN); a request
rejected for its filling mode is sent again with the next one, and both are logged.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

from backtester.core.models import Direction

MAGIC = 7_100_001  # marks the backtester's orders and positions
DEVIATION_POINTS = 20  # accepted slippage for market orders, in points
RETCODE_DONE = 10009
RETCODE_DONE_PARTIAL = 10010
RETCODE_INVALID_STOPS = 10016
RETCODE_MARKET_CLOSED = 10018
RETCODE_INVALID_FILL = 10030
RETCODES = {
    10004: "requote",
    10006: "rejected",
    10007: "canceled",
    10008: "placed",
    10009: "done",
    10010: "done partially",
    10011: "processing error",
    10013: "invalid request",
    10014: "invalid volume",
    10015: "invalid price",
    10016: "invalid stops",
    10017: "trade disabled",
    10018: "market closed",
    10019: "no money",
    10020: "prices changed",
    10021: "no quotes",
    10024: "too many requests",
    10025: "no changes",
    10026: "autotrading disabled by server",
    10027: "autotrading disabled by client (Algo Trading button)",
    10029: "order or position frozen",
    10030: "unsupported filling mode",
    10031: "no connection",
    10035: "invalid order",
    10036: "position already closed",
    10038: "close volume exceeds the position",
    10040: "position limit reached",
    10044: "only position closing allowed",
}
FILLING_BITS = ((1, "ORDER_FILLING_FOK"), (2, "ORDER_FILLING_IOC"))


class DemoLockError(RuntimeError):
    """The account is not a demo account (or no account): orders are refused."""


def require_demo(mt5: ModuleType) -> None:
    account = mt5.account_info()
    if account is None:
        raise DemoLockError("refused: no account (not connected)")
    if account.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
        raise DemoLockError(
            "refused: not a demo account (DEMO LOCK, ROADMAP 7.1); no order was sent"
        )


def retcode_text(code: int) -> str:
    return f"{code} {RETCODES.get(code, 'unknown')}"


def _plain(value):
    """MT5's named tuples (also nested) as JSON values."""
    if hasattr(value, "_asdict"):
        return {k: _plain(v) for k, v in value._asdict().items()}
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_plain(v) for v in value]
    return value


@dataclass
class OrderLog:
    """Every request and result; also appended to `path` (JSON lines) when given."""

    path: Path | None = None
    entries: list[dict] = field(default_factory=list)

    def add(self, label: str, request: dict, result, ms: float) -> dict:
        entry = {
            "time": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "label": label,
            "request": _plain(request),
            "retcode": getattr(result, "retcode", None),
            "result": _plain(result),
            "ms": round(ms, 1),
        }
        self.entries.append(entry)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        return entry


def send(mt5: ModuleType, request: dict, log: OrderLog, label: str):
    """`order_send` behind the demo lock, timed and logged. Returns (result, ms)."""
    require_demo(mt5)
    start = time.perf_counter()
    result = mt5.order_send(request)
    ms = (time.perf_counter() - start) * 1000
    log.add(label, request, result, ms)
    return result, ms


def filling_modes(mt5: ModuleType, symbol_info) -> list[int]:
    """The filling modes to try, in order: those the symbol allows, then RETURN."""
    modes = [getattr(mt5, name) for bit, name in FILLING_BITS if symbol_info.filling_mode & bit]
    return [*modes, mt5.ORDER_FILLING_RETURN]


def _deal(mt5, request: dict, log: OrderLog, label: str):
    """A TRADE_ACTION_DEAL request, retried with the next filling mode if rejected for
    it. Returns (result, ms of the accepted / last try, filling mode used)."""
    info = mt5.symbol_info(request["symbol"])
    result = ms = mode = None
    for mode in filling_modes(mt5, info):
        result, ms = send(mt5, {**request, "type_filling": mode}, log, label)
        if result is None or result.retcode != RETCODE_INVALID_FILL:
            break
    return result, ms, mode


def market_order(
    mt5: ModuleType,
    symbol: str,
    side: Direction,
    volume: float,
    sl: float,
    tp: float,
    log: OrderLog,
    comment: str = "backtester",
):
    """Market buy (BULLISH) or sell (BEARISH) with SL and TP. Returns (result, ms,
    filling mode, the quote it was sent at)."""
    require_demo(mt5)
    tick = mt5.symbol_info_tick(symbol)
    buy = side is Direction.BULLISH
    price = tick.ask if buy else tick.bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY if buy else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": DEVIATION_POINTS,
        "magic": MAGIC,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
    }
    result, ms, mode = _deal(mt5, request, log, f"open {'buy' if buy else 'sell'}")
    return result, ms, mode, price


def modify_sl(mt5: ModuleType, position, sl: float, log: OrderLog, label: str = "modify SL"):
    """Move the SL of an open position (TP unchanged). Returns (result, ms)."""
    require_demo(mt5)
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": position.symbol,
        "position": position.ticket,
        "sl": sl,
        "tp": position.tp,
        "magic": MAGIC,
    }
    return send(mt5, request, log, label)


def close_volume(mt5: ModuleType, position, volume: float, log: OrderLog, label: str = "close"):
    """Close `volume` of an open position (all of it or part). Returns (result, ms,
    filling mode)."""
    require_demo(mt5)
    tick = mt5.symbol_info_tick(position.symbol)
    long = position.type == mt5.POSITION_TYPE_BUY
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": position.symbol,
        "position": position.ticket,
        "volume": volume,
        "type": mt5.ORDER_TYPE_SELL if long else mt5.ORDER_TYPE_BUY,
        "price": tick.bid if long else tick.ask,
        "deviation": DEVIATION_POINTS,
        "magic": MAGIC,
        "comment": "backtester close",
        "type_time": mt5.ORDER_TIME_GTC,
    }
    return _deal(mt5, request, log, label)


def own_positions(mt5: ModuleType, symbol: str) -> list:
    return [p for p in (mt5.positions_get(symbol=symbol) or ()) if p.magic == MAGIC]


def own_orders(mt5: ModuleType, symbol: str) -> list:
    return [o for o in (mt5.orders_get(symbol=symbol) or ()) if o.magic == MAGIC]


def close_own_positions(mt5: ModuleType, symbol: str, log: OrderLog) -> int:
    """Close every position of `symbol` the backtester opened (MAGIC). Returns how many
    were closed. The user's own positions are never touched."""
    require_demo(mt5)
    closed = 0
    for position in own_positions(mt5, symbol):
        result, _, _ = close_volume(mt5, position, position.volume, log, "cleanup close")
        closed += result is not None and result.retcode == RETCODE_DONE
    return closed
