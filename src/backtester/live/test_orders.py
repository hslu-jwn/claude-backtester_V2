"""Scripted order test on the demo account. Spec: ROADMAP.md › 7.1.

    python -m backtester.live.test_orders XAUUSD

(also the button in Settings (gear) -> Trading). Demo accounts only (DEMO LOCK, `orders.py`).
For a buy, then the same as a sell:

1. market order 2 x the minimum lot with SL and TP: fill price vs the quote it was sent
   at (slippage), SL / TP on the position;
2. SL to break-even (the entry price), as the strategy does; right after the entry the
   price is usually not far enough from it (the SL would be on the wrong side of the
   price or inside the stops level), so a rejection there is reported and the SL is then
   moved halfway to the entry instead, to test the modify itself;
3. close half (like TP1), check the volume left;
4. close the rest.

Every request and result (retcode, fill, execution time) is logged to
`results/live/test_orders/<time>_<SYMBOL>.jsonl` and summed up in the report. At the end
(also after an error) every position the test opened (MAGIC) is closed and the symbol's
positions and orders are checked. The user's own positions are never touched.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

from backtester.cli import utf8_output
from backtester.core.models import Direction
from backtester.live.connection import account_mode, scrub, session
from backtester.live.credentials import Credentials, CredentialStoreError, load_credentials
from backtester.live.orders import (
    MAGIC,
    RETCODE_DONE,
    RETCODE_INVALID_STOPS,
    RETCODE_MARKET_CLOSED,
    DemoLockError,
    OrderLog,
    close_own_positions,
    close_volume,
    confirm_close,
    confirm_open,
    market_order,
    modify_sl,
    own_orders,
    own_positions,
    require_demo,
    retcode_text,
)
from backtester.live.trading_settings import TradingSettings, load_trading_settings
from backtester.paths import RESULTS_DIR

LOG_DIR = RESULTS_DIR / "live" / "test_orders"
SL_TP_SHARE = 0.003  # SL / TP distance: 0.3% of the price, at least 3 x the stops level


class TestAborted(RuntimeError):
    __test__ = False  # not a pytest test class


def _round_step(value: float, step: float) -> float:
    return round(round(value / step) * step, 8)


def _side_name(side: Direction) -> str:
    return "buy" if side is Direction.BULLISH else "sell"


def _step_line(name: str, result, ms: float, extra: str = "") -> str:
    code = retcode_text(result.retcode) if result is not None else "no result"
    comment = f" ({result.comment})" if result is not None and result.comment else ""
    return f"  {name}: {code}{comment}, {ms:.0f} ms{'; ' + extra if extra else ''}"


def run_side(mt5: ModuleType, name: str, side: Direction, log: OrderLog) -> list[str]:
    info = mt5.symbol_info(name)
    point, digits = info.point, info.digits
    sign = 1 if side is Direction.BULLISH else -1
    volume = _round_step(2 * info.volume_min, info.volume_step)
    half = _round_step(volume / 2, info.volume_step)
    tick = mt5.symbol_info_tick(name)
    quote = tick.ask if side is Direction.BULLISH else tick.bid
    distance = max(3 * info.trade_stops_level * point, SL_TP_SHARE * quote)
    distance = _round_step(distance, info.trade_tick_size)
    sl, tp = round(quote - sign * distance, digits), round(quote + sign * distance, digits)
    lines = [f"{_side_name(side).capitalize()} {volume:g} lots, SL {sl} / TP {tp}:"]

    # 1. open
    result, ms, mode, sent_at = market_order(mt5, name, side, volume, sl, tp, log, "bt test")
    if result is None or result.retcode != RETCODE_DONE:
        lines.append(_step_line("1 open", result, ms))
        if result is not None and result.retcode == RETCODE_MARKET_CLOSED:
            raise TestAborted("market closed: no test possible now")
        return lines
    fill = confirm_open(mt5, result)
    if not fill.confirmed:
        lines.append("  ! the fill is not confirmed (no deal / position visible)")
    slippage = sign * (fill.price - sent_at) / point
    lines.append(
        _step_line(
            "1 open",
            result,
            ms,
            f"filled {fill.price} vs {'ask' if sign > 0 else 'bid'} {sent_at} "
            f"(slippage {slippage:+.0f} points), filling {_filling_name(mt5, mode)}",
        )
    )
    position = fill.position
    if position is None:
        lines.append("  ! the position can't be found after the fill")
        return lines
    if (position.sl, position.tp) != (sl, tp):
        lines.append(f"  ! SL / TP on the position: {position.sl} / {position.tp}")

    # 2. break-even
    result, ms = modify_sl(mt5, position, position.price_open, log, "SL to break-even")
    if result is not None and result.retcode == RETCODE_DONE:
        lines.append(_step_line("2 SL to break-even", result, ms))
    else:
        tick = mt5.symbol_info_tick(name)
        now = tick.bid if sign > 0 else tick.ask
        lines.append(
            _step_line(
                "2 SL to break-even",
                result,
                ms,
                f"entry {position.price_open}, {'bid' if sign > 0 else 'ask'} now {now}, "
                f"stops level {info.trade_stops_level} points"
                + (
                    " (expected right after the entry)"
                    if result is not None and result.retcode == RETCODE_INVALID_STOPS
                    else ""
                ),
            )
        )
        halfway = round(position.price_open - sign * distance / 2, digits)
        result, ms = modify_sl(mt5, position, halfway, log, "SL halfway")
        lines.append(_step_line(f"2b SL to {halfway} (halfway)", result, ms))
    position = mt5.positions_get(ticket=position.ticket)[0]
    lines.append(f"  SL on the position now {position.sl}")

    # 3. close half
    result, ms, mode = close_volume(mt5, position, half, log, "close half")
    done = confirm_close(mt5, result, position, half)
    left = [done.position] if done.position is not None else []
    left_volume = done.position.volume if left else 0.0
    check = "" if done.confirmed and abs(left_volume - (volume - half)) < 1e-9 else " !"
    price = f", at {done.price}" if result is not None else ""
    lines.append(_step_line("3 close half", result, ms, f"{left_volume:g} lots left{check}{price}"))

    # 4. close the rest
    if left:
        result, ms, mode = close_volume(mt5, left[0], left[0].volume, log, "close rest")
        gone = confirm_close(mt5, result, left[0], left[0].volume).position is None
        lines.append(
            _step_line("4 close rest", result, ms, "position closed" if gone else "! still open")
        )
    return lines


def _filling_name(mt5: ModuleType, mode) -> str:
    for name in ("ORDER_FILLING_FOK", "ORDER_FILLING_IOC", "ORDER_FILLING_RETURN"):
        if getattr(mt5, name) == mode:
            return name.removeprefix("ORDER_FILLING_")
    return str(mode)


def run_test(mt5: ModuleType, symbol: str, name: str, log: OrderLog) -> list[str]:
    """The whole test on a connected terminal; returns the report lines."""
    try:
        require_demo(mt5)
    except DemoLockError as e:
        return [str(e).capitalize()]  # "Refused: …"
    account, terminal = mt5.account_info(), mt5.terminal_info()
    mt5.symbol_select(name, True)
    info = mt5.symbol_info(name)
    if info is None:
        return [f"{symbol}: {name} is not a symbol on this server"]
    margin = {
        mt5.ACCOUNT_MARGIN_MODE_RETAIL_HEDGING: "hedging",
        mt5.ACCOUNT_MARGIN_MODE_RETAIL_NETTING: "netting",
    }.get(account.margin_mode, str(account.margin_mode))
    lines = [
        f"Demo test orders {symbol} ({name}), {datetime.now(UTC):%Y-%m-%d %H:%M:%S} UTC",
        (
            f"Account {account_mode(mt5, account.trade_mode)}, {margin}; volume min / step "
            f"{info.volume_min:g} / {info.volume_step:g}; stops level "
            f"{info.trade_stops_level} points, freeze level {info.trade_freeze_level}; "
            f"filling flags {info.filling_mode}"
        ),
    ]
    if not terminal.trade_allowed:
        return [*lines, "Algo Trading is off in the terminal: press the Algo Trading button."]
    others = [p for p in (mt5.positions_get(symbol=name) or ()) if p.magic != MAGIC]
    if others:
        lines.append(f"({len(others)} position(s) of your own on {name}: left alone)")
    # the bot's positions and orders open before the test are not the test's: never closed,
    # not counted in the end check (review live #12)
    before = {p.ticket for p in own_positions(mt5, name)}
    orders_before = {o.ticket for o in own_orders(mt5, name)}
    if before:
        lines.append(f"({len(before)} bot position(s) on {name} open before the test: left alone)")
    try:
        for side in (Direction.BULLISH, Direction.BEARISH):
            lines += run_side(mt5, name, side, log)
    except TestAborted as e:
        lines.append(f"Stopped: {e}")
    except Exception as e:  # noqa: BLE001 - reported, then cleaned up below
        lines.append(f"Stopped by an error: {type(e).__name__}: {e}")
    finally:
        closed = close_own_positions(mt5, name, log, keep=before)
        if closed:
            lines.append(f"Cleanup: closed {closed} position(s) the test had left open")
    positions = [p for p in own_positions(mt5, name) if p.ticket not in before]
    orders = [o for o in own_orders(mt5, name) if o.ticket not in orders_before]
    lines.append(
        "End check: nothing open"
        if not positions and not orders
        else f"End check: ! {len(positions)} position(s), {len(orders)} order(s) still open"
    )
    rejected = [e for e in log.entries if e["retcode"] not in (RETCODE_DONE, None)]
    if rejected:
        lines.append(
            "Rejections: "
            + ", ".join(f"{e['label']} {retcode_text(e['retcode'])}" for e in rejected)
        )
    times = [e["ms"] for e in log.entries]
    if times:
        lines.append(
            f"Execution times: {len(times)} requests, median {sorted(times)[len(times) // 2]:.0f} "
            f"ms, max {max(times):.0f} ms"
        )
    return lines


def log_path(symbol: str) -> Path:
    return LOG_DIR / f"{datetime.now(UTC):%Y%m%d-%H%M%S}_{symbol}.jsonl"


def run_from_panel(
    settings: TradingSettings,
    credentials: Credentials | None,
    symbol: str,
    mt5: ModuleType | None = None,
    log: OrderLog | None = None,
) -> list[str]:
    """The test as the Trading panel runs it: connect, test, disconnect."""
    log = log or OrderLog(log_path(symbol))
    name = settings.symbols.get(symbol, symbol)
    try:
        with session(settings, credentials, mt5) as connected:
            lines = run_test(connected, symbol, name, log)
    except Exception as e:  # noqa: BLE001 - shown in the panel
        return [f"Can't run the test: {scrub(str(e), credentials)}"]
    if log.path is not None and log.entries:
        lines.append(f"Log: {log.path}")
    return lines


def main(argv: list[str] | None = None) -> int:
    utf8_output()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("symbol", help="our name, e.g. XAUUSD (mapped to the server's name)")
    args = p.parse_args(argv)
    settings = load_trading_settings()
    try:
        credentials = load_credentials(settings.platform)
    except CredentialStoreError as e:
        print(f"Credential store: {e}; using the terminal's logged-in account.")
        credentials = None
    lines = run_from_panel(settings, credentials, args.symbol.upper())
    print("\n".join(lines))
    return 0 if not any(line.startswith(("Refused", "Can't")) for line in lines) else 1


if __name__ == "__main__":
    raise SystemExit(main())
