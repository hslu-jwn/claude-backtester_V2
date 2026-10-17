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
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

from backtester.core.models import Direction

CONFIRM_TIMEOUT_S = 5.0  # how long to wait for the deal / position after order_send
CONFIRM_INTERVAL_S = 0.05  # poll interval while waiting
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


# --- confirming a fill (FTMO returns retcode 10009 with deal 0 and price 0.0; the deal and the
# --- updated position show up a few ms later, so nothing is read from the result itself) -----


@dataclass(frozen=True)
class Fill:
    """What the terminal really did, read from the deal and the position."""

    confirmed: bool
    price: float = 0.0
    volume: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    profit: float = 0.0
    fee: float = 0.0
    deal_ticket: int = 0
    position_id: int = 0
    position: object | None = None  # the position as it is now (None: gone)

    @property
    def net(self) -> float:
        return self.profit + self.commission + self.swap + self.fee


def _own_deal(mt5: ModuleType, result, position_id: int):
    """The deal that belongs to `result` (its order), or None while it isn't visible."""
    deals = mt5.history_deals_get(position=position_id) or ()
    mine = [d for d in deals if getattr(d, "order", None) == result.order]
    if result.deal:
        mine = [d for d in mine if d.ticket == result.deal] or mine
    return mine[-1] if mine else None


def _confirm(mt5, result, position_id, expect_left, timeout, interval, sleep, clock) -> Fill:
    """Poll until the deal exists and the position matches: open (`expect_left` None: it
    exists), or `expect_left` lots left (0.0: gone)."""
    if result is None or result.retcode not in (RETCODE_DONE, RETCODE_DONE_PARTIAL):
        return Fill(False, position_id=position_id)
    deadline = clock() + timeout
    while True:
        deal = _own_deal(mt5, result, position_id)
        found = mt5.positions_get(ticket=position_id) or ()
        position = found[0] if found else None
        if expect_left is None:
            state_ok = position is not None
        elif expect_left <= 0:
            state_ok = position is None
        else:
            state_ok = position is not None and abs(position.volume - expect_left) < 1e-9
        if deal is not None and state_ok:
            return Fill(
                True,
                deal.price,
                deal.volume,
                getattr(deal, "commission", 0.0),
                getattr(deal, "swap", 0.0),
                getattr(deal, "profit", 0.0),
                getattr(deal, "fee", 0.0),
                deal.ticket,
                position_id,
                position,
            )
        if clock() >= deadline:
            price = deal.price if deal is not None else 0.0
            return Fill(False, price, position_id=position_id, position=position)
        sleep(interval)


def confirm_open(
    mt5: ModuleType,
    result,
    timeout: float | None = None,
    interval: float | None = None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> Fill:
    """Wait for the deal of an accepted market open (the position id is the order ticket)."""
    if result is None:
        return Fill(False)
    return _confirm(
        mt5,
        result,
        result.order,
        None,
        CONFIRM_TIMEOUT_S if timeout is None else timeout,
        CONFIRM_INTERVAL_S if interval is None else interval,
        sleep,
        clock,
    )


def confirm_close(
    mt5: ModuleType,
    result,
    position,
    volume: float,
    timeout: float | None = None,
    interval: float | None = None,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> Fill:
    """Wait for the deal of a (partial) close and for the position to show the reduced volume
    (or to be gone). Do not take the next step before this returns `confirmed`."""
    left = round(position.volume - volume, 8)
    return _confirm(
        mt5,
        result,
        position.ticket,
        max(left, 0.0),
        CONFIRM_TIMEOUT_S if timeout is None else timeout,
        CONFIRM_INTERVAL_S if interval is None else interval,
        sleep,
        clock,
    )
