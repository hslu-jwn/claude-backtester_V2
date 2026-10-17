"""The live demo bot (ROADMAP 7.2): the opening-range strategy on the FTMO demo account.

    python -m backtester.live.bot            # starts MT5 itself, trades until stopped
    python -m backtester.live.bot --risk 0.25 --daily-stop 2 --symbols US30 US500

Stop it by creating the file `results/live/STOP` (stop, close nothing) or
`results/live/EMERGENCY` (close all positions with our MAGIC, then stop); `results/live/PAUSE`
blocks new entries while it exists (open trades keep being managed); Ctrl+C also stops it
(positions keep their server-side SL). Spec: docs/live-trading.md.

How it works
- One loop, once per closed minute: new closed M1 bars only (`Mt5Adapter`, bars closing after
  "now" are dropped), appended per symbol and fed to the strategy exactly like the backtest
  engine: base candle close time = `now`; first positions closed by the server are reported to
  `on_trade_closed`, then `on_candle`, then `exits()`, then the new orders.
- The strategy is the same code as in the backtest. On start (and after a restart) it replays
  the history through the same path, so its state (ATR, volume history, today's session) is the
  state it would have had. An order from a past bar is never sent (stale after
  `stale_signal_s`); if the position of that signal is still open (same comment) it is picked up
  again, so a restart neither duplicates nor forgets a trade.
- Lots from the sizer (`risk/sizer.py`), the daily guard (`risk/prop_rules.py`) is checked once
  per cycle and before every order. Every fill is read from the deal, never from `order_send`'s
  result (FTMO answers with deal 0 / price 0.0).
- Logs in `results/live/<date>/`: `orders.jsonl` (every signal skip, order, retcode, guard and
  connection event, via `OrderLog`), `paper.csv` (each signal with its simulated fill next to
  the real one) and `trades.csv` (closed trades: R net from the deals' money / the money at
  risk; `sim_r` = simulated R from the signal price and the bar's spread at entry, exit at the
  SL price or the exit bar's close, no exit spread).
- A lost connection is retried with backoff; missed bars are fetched afterwards, missed
  entries are not traded late.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType

from backtester.cli import utf8_output
from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.data.adapters.mt5_adapter import Mt5Adapter, Mt5Error, ServerClock, load_mt5
from backtester.data.mt5_download import DEFAULT_CLOCK, DEFAULT_NAMES
from backtester.engine.trade import ExitReason, TradeResult
from backtester.live.connection import ConnectionFailed, connect, scrub
from backtester.live.credentials import CredentialStoreError, load_credentials
from backtester.live.orders import (
    MAGIC,
    RETCODE_DONE,
    DemoLockError,
    OrderLog,
    close_volume,
    confirm_close,
    confirm_open,
    market_order,
    own_positions,
    require_demo,
    retcode_text,
)
from backtester.live.status import STATUS_NAME, build_status, summary_text, write_status
from backtester.live.telegram import Notifier, TelegramClient, load_telegram
from backtester.live.trading_settings import TradingSettings, load_trading_settings
from backtester.paths import RESULTS_DIR
from backtester.risk.prop_rules import GuardConfig, GuardStatus, evaluate, prague_day_start
from backtester.risk.sizer import lots_for_risk, spec_from_symbol_info
from backtester.strategy.opening_range.config import EntryMode, OpeningRangeConfig
from backtester.strategy.opening_range.strategy import OpeningRange

CONTINUE, STOP = "continue", "stop"
ERROR_KINDS = ("error", "disconnected", "connect_failed", "close_failed", "refused")
FORWARD_SYMBOLS = ("US30", "US500", "NAS100", "US2000")
PAPER_COLUMNS = [
    "time_utc", "symbol", "side", "signal_entry", "sim_fill", "sl", "spread", "lots", "status",
    "reason", "real_fill", "slippage", "ticket", "comment",
]  # fmt: skip
TRADE_COLUMNS = [
    "symbol", "side", "ticket", "lots", "entry_time", "exit_time", "entry_fill", "exit_price",
    "sl", "exit_reason", "sim_exit", "sim_r", "r_gross", "r_net", "money", "risk_money",
]  # fmt: skip


def forward_strategy_config() -> OpeningRangeConfig:
    """The candidate of the forward test (docs/strategy-opening-range.md, live-trading.md)."""
    return OpeningRangeConfig(
        entry_mode=EntryMode.BAND, band_atr=0.25, target_r=0.0, min_rel_volume=1.5
    )


@dataclass(frozen=True)
class BotConfig:
    symbols: tuple[str, ...] = FORWARD_SYMBOLS
    strategy: OpeningRangeConfig = field(default_factory=forward_strategy_config)
    risk_percent: float = 0.25  # of the balance per trade (adjustable per strategy)
    initial_balance: float | None = None  # override; None: the account's first balance deal
    guard: GuardConfig = field(default_factory=GuardConfig)
    comment_prefix: str = "orb"  # + the signal bar's close time: stable across restarts
    out_dir: Path = RESULTS_DIR / "live"
    poll_delay_s: float = 2.0  # wait after the minute boundary before asking for the new bar
    bar_retries: int = 5  # extra tries while an expected bar is not there yet
    bar_retry_s: float = 1.0
    stale_signal_s: float = 90.0  # an order from a bar older than this is not sent
    reconnect_first_s: float = 5.0
    reconnect_factor: float = 2.0
    reconnect_max_s: float = 300.0
    verbose: bool = True

    @property
    def stop_file(self) -> Path:
        return self.out_dir / "STOP"

    @property
    def emergency_file(self) -> Path:
        return self.out_dir / "EMERGENCY"

    @property
    def pause_file(self) -> Path:
        return self.out_dir / "PAUSE"

    @property
    def status_file(self) -> Path:
        return self.out_dir / STATUS_NAME


class InitialBalanceError(RuntimeError):
    """The account's initial balance can't be found and no override is given."""


class BotDisconnected(RuntimeError):
    """The terminal or the account is gone; the loop reconnects."""


@dataclass
class _Symbol:
    name: str  # our name (strategy, adapter)
    broker: str
    strategy: OpeningRange
    candles: list[Candle] = field(default_factory=list)


@dataclass
class _Trade:
    ticket: int
    symbol: str
    broker: str
    ref: object
    direction: Direction
    lots: float
    sl: float
    signal_entry: float
    sim_fill: float
    real_fill: float
    entry_time: datetime
    candle_ts: datetime
    open_commission: float
    risk_money: float
    comment: str


class Bot:
    def __init__(
        self,
        config: BotConfig,
        mt5: ModuleType,
        settings: TradingSettings,
        credentials=None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        sleep: Callable[[float], None] = time.sleep,
        notifier=None,  # Telegram: anything with `event(kind, fields)`; never blocks (telegram.py)
    ):
        self.config, self.mt5, self.settings, self.credentials = config, mt5, settings, credentials
        self.now, self.sleep = now, sleep
        clock = settings.server_clock or DEFAULT_CLOCK
        names = {s: DEFAULT_NAMES.get(s, s) for s in config.symbols}
        names.update({s: n for s, n in settings.symbols.items() if s in names and n != s})
        self.clock: ServerClock = clock
        self.adapter = Mt5Adapter(mt5, clock, names, now=now)
        self.symbols = {
            s: _Symbol(s, names[s], OpeningRange(s, config.strategy)) for s in config.symbols
        }
        self.by_ticket: dict[int, _Trade] = {}
        self.by_ref: dict[tuple[str, object], _Trade] = {}
        self.pending_exits: list[tuple[str, object, float]] = []
        self._logs: dict[str, OrderLog] = {}
        self._day_key: datetime | None = None
        self._day_balance = 0.0
        self.status: GuardStatus | None = None
        self.blocked = ""  # reason; empty: trading allowed
        self.notifier = notifier
        self.initial_balance: float | None = None  # FTMO max loss is measured from it
        # state for status.json (live/status.py)
        self.running = False
        self.connected = False
        self.account_mode = ""
        self.started_at: datetime | None = None
        self.last_error = ""
        self.signals: list[dict] = []
        self.day_trades: list[tuple[datetime, float]] = []  # (closed at, R net)
        self.last_status: dict | None = None
        self.paused = False  # the PAUSE file exists: no new entries (docs/live-trading.md)
        self.setup_since: dict[str, tuple[str, str]] = {}  # symbol -> (stage, since), status.json

    # --- logs -------------------------------------------------------------------------------

    def _day_dir(self) -> Path:
        return self.config.out_dir / self.now().strftime("%Y-%m-%d")

    def log(self) -> OrderLog:
        folder = self._day_dir()
        key = str(folder)
        if key not in self._logs:
            self._logs[key] = OrderLog(folder / "orders.jsonl")
        return self._logs[key]

    def note(self, kind: str, **fields) -> None:
        """A line in the decision log (and on screen)."""
        plain = {k: v.isoformat() if isinstance(v, datetime) else v for k, v in fields.items()}
        self.log().add(kind, plain, None, 0.0)
        if self.config.verbose:
            text = " ".join(f"{k}={v}" for k, v in fields.items())
            print(f"{self.now():%H:%M:%S} {kind} {text}", flush=True)
        safe = {
            k: scrub(v, self.credentials) if isinstance(v, str) else v for k, v in plain.items()
        }
        if kind in ERROR_KINDS:
            detail = safe.get("what") or safe.get("error") or safe.get("retcode") or ""
            self.last_error = f"{kind}: {detail}"
        if kind == "disconnected":
            self.connected = False
        if kind in ("stopped", "refused"):
            self.running = False
        self._tell(kind, safe)
        self.publish()

    def _tell(self, kind: str, fields: dict) -> None:
        """Hand an event to Telegram; whatever goes wrong there never reaches the trading."""
        if self.notifier is not None:
            with contextlib.suppress(Exception):
                self.notifier.event(kind, fields)

    def publish(self) -> None:
        """Write status.json (heartbeat); a failed write must not stop trading."""
        with contextlib.suppress(Exception):
            self.last_status = build_status(self, self.now())
            write_status(self.config.status_file, self.last_status)

    def status_text(self) -> str:
        return summary_text(self.last_status)

    @property
    def day_r(self) -> float:
        return sum(
            r for when, r in self.day_trades if self._day_key is None or when >= self._day_key
        )

    def open_positions(self) -> list[dict]:
        out = []
        for t in list(self.by_ticket.values()):
            sign = 1 if t.direction is Direction.BULLISH else -1
            risk = abs(t.signal_entry - t.sl)
            tick = self.mt5.symbol_info_tick(t.broker)
            price = (tick.bid if sign > 0 else tick.ask) if tick else None
            floating = sign * (price - t.real_fill) / risk if price is not None and risk else 0.0
            out.append({
                "symbol": t.symbol, "side": "buy" if sign > 0 else "sell", "lots": t.lots,
                "entry": t.real_fill, "sl": t.sl, "ticket": t.ticket,
                "floating_r": round(floating, 3), "since": t.entry_time.isoformat(),
            })  # fmt: skip
        return out

    def _set_signal(self, sym: _Symbol, bar_now: datetime, status: str, reason: str = "") -> None:
        key = bar_now.isoformat()
        for s in reversed(self.signals):
            if s["time"] == key and s["symbol"] == sym.name:
                s["status"], s["reason"] = status, reason
                return
        self.signals.append(
            {"time": key, "symbol": sym.name, "side": "", "status": status, "reason": reason}
        )

    def _append(self, name: str, columns: list[str], values: dict) -> None:
        path = self._day_dir() / name
        path.parent.mkdir(parents=True, exist_ok=True)
        new = not path.exists()
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, columns)
            if new:
                writer.writeheader()
            writer.writerow(values)

    # --- connection -------------------------------------------------------------------------

    def connect(self) -> None:
        """Connect (retry with backoff), then require a DEMO account. A REAL account raises
        `DemoLockError` before anything is sent."""
        wait = self.config.reconnect_first_s
        while True:
            try:
                connect(self.mt5, self.credentials, self.settings.terminal_path)
                break
            except ConnectionFailed as e:
                self.note("connect_failed", error=scrub(str(e), self.credentials), retry_s=wait)
                self.sleep(wait)
                wait = min(wait * self.config.reconnect_factor, self.config.reconnect_max_s)
        require_demo(self.mt5)
        self.connected, self.running, self.account_mode = True, True, "DEMO"
        self.started_at = self.started_at or self.now()
        self.note("connected")

    def _check_connected(self) -> None:
        terminal, account = self.mt5.terminal_info(), self.mt5.account_info()
        if terminal is None or account is None or not terminal.connected:
            raise BotDisconnected("terminal or account not available")

    def resolve_initial_balance(self) -> float:
        """Override, else the account's first balance deal (whole history). Raises
        `InitialBalanceError` when neither exists."""
        if self.config.initial_balance:
            self.initial_balance = float(self.config.initial_balance)
            return self.initial_balance
        now = self.now()
        deals = self.mt5.history_deals_get(
            self.clock.to_server(datetime(2000, 1, 1, tzinfo=UTC)),
            self.clock.to_server(now + timedelta(days=1)),
        )
        balance = sorted(
            (d for d in (deals or ()) if getattr(d, "type", None) == self.mt5.DEAL_TYPE_BALANCE),
            key=lambda d: getattr(d, "time", 0),
        )
        if not balance or not getattr(balance[0], "profit", 0) > 0:
            raise InitialBalanceError(
                "initial balance not found in the account's deal history; "
                "pass it with --balance <amount>"
            )
        self.initial_balance = float(balance[0].profit)
        return self.initial_balance

    # --- start: history and resume ----------------------------------------------------------

    def start(self) -> None:
        """Warm up every symbol: load the history and replay it through the strategy."""
        now = self._floor(self.now())
        for sym in self.symbols.values():
            self.mt5.symbol_select(sym.broker, True)
            if self.mt5.symbol_info(sym.broker) is None:
                raise Mt5Error(f"{sym.broker}: unknown symbol on this server")
            begin = now - timedelta(days=sym.strategy.min_warmup_days)
            candles = self._candles(sym, begin, now)
            if not candles:
                self.note("no_history", symbol=sym.name)
                continue
            self._feed_new(sym, candles)
            self.note("warm_up", symbol=sym.name, bars=len(sym.candles), last=sym.candles[-1].ts)

    @staticmethod
    def _floor(t: datetime) -> datetime:
        return t.replace(second=0, microsecond=0)

    def _candles(self, sym: _Symbol, begin: datetime, end: datetime) -> list[Candle]:
        if end <= begin:
            return []
        return self.adapter.fetch(sym.name, Timeframe.M1, begin, end)

    # --- the loop ---------------------------------------------------------------------------

    def run(self) -> int:
        """Connect, warm up, then one `cycle` per minute until stopped. Returns the exit code."""
        try:
            self.connect()
            self.resolve_initial_balance()
            if self.config.stop_file.exists():
                self.config.stop_file.unlink()
                self.note("old_stop_file_removed")
            self.start()
            while True:
                try:
                    if self.cycle() == STOP:
                        break
                except (BotDisconnected, Mt5Error, ConnectionFailed, OSError) as e:
                    self.note("disconnected", error=scrub(str(e), self.credentials))
                    self.mt5.shutdown()
                    self.connect()
                    continue
                self.sleep(self._seconds_to_next_minute())
            self.note("stopped")
            return 0
        except (DemoLockError, InitialBalanceError) as e:
            self.note("refused", error=str(e))
            return 1
        except KeyboardInterrupt:
            self.note("stopped", by="keyboard")
            return 0
        finally:
            self.mt5.shutdown()

    def _seconds_to_next_minute(self) -> float:
        t = self.now()
        return 60.0 - (t.second + t.microsecond / 1e6) + self.config.poll_delay_s

    def cycle(self) -> str:
        """Everything for one closed minute. Returns `CONTINUE` or `STOP`."""
        cfg = self.config
        if cfg.stop_file.exists():
            cfg.stop_file.unlink()
            self.note("stop_file", closed="nothing")
            return STOP
        self._check_connected()
        if cfg.emergency_file.exists():
            cfg.emergency_file.unlink()
            self.note("emergency_file")
            self._close_all("emergency")
            return STOP
        self._check_pause()
        if self._guard() == STOP:
            return STOP
        self._reconcile()
        self._retry_exits()
        for sym in self.symbols.values():
            self._feed_new(sym, self._fetch_new(sym))
        self.publish()
        return CONTINUE

    def _check_pause(self) -> None:
        """The PAUSE file blocks new entries only; each change is noted once."""
        paused = self.config.pause_file.exists()
        if paused != self.paused:
            self.paused = paused
            self.note("paused" if paused else "unpaused")

    # --- the daily guard --------------------------------------------------------------------

    def _guard(self) -> str:
        now = self.now()
        account = self.mt5.account_info()
        day = prague_day_start(now, self.config.guard.zone)
        if day != self._day_key:
            self._day_key = day
            self._day_balance = self._balance_at(day, account, now)
            if self.blocked:
                self.note("guard_reset", balance=self._day_balance)
            self.blocked = ""
        status = evaluate(
            self.config.guard, self._day_balance, account.equity, self.initial_balance
        )
        self.status = status
        if status.breach:
            self.note("guard_breach", reason=status.reason, day_pl=round(status.day_pl, 2))
            self._close_all("ftmo limit")
            return STOP
        if status.stop_trading and not self.blocked:
            self.blocked = status.reason
            self.note("guard_stop", reason=status.reason, day_pl=round(status.day_pl, 2))
            self._close_all("daily stop")
        return CONTINUE

    def _balance_at(self, day_start: datetime, account, now: datetime) -> float:
        """Balance at the day's start = balance now - the net of today's trade deals."""
        deals = self.mt5.history_deals_get(
            self.clock.to_server(day_start), self.clock.to_server(now + timedelta(days=1))
        )
        kinds = (self.mt5.DEAL_TYPE_BUY, self.mt5.DEAL_TYPE_SELL)
        net = sum(
            getattr(d, "profit", 0.0)
            + getattr(d, "commission", 0.0)
            + getattr(d, "swap", 0.0)
            + getattr(d, "fee", 0.0)
            for d in (deals or ())
            if getattr(d, "type", None) in kinds
        )
        return account.balance - net

    # --- bars and the strategy --------------------------------------------------------------

    def _fetch_new(self, sym: _Symbol) -> list[Candle]:
        end = self._floor(self.now())
        expected = end - timedelta(minutes=1)
        last = sym.candles[-1].ts if sym.candles else None
        start = last + timedelta(minutes=1) if last else end - timedelta(minutes=1)
        flowing = last is not None and last >= expected - timedelta(minutes=1)
        for attempt in range(self.config.bar_retries + 1):
            new = [c for c in self._candles(sym, start, end) if last is None or c.ts > last]
            if not flowing or (new and new[-1].ts >= expected) or end <= start:
                return new
            if attempt < self.config.bar_retries:
                self.sleep(self.config.bar_retry_s)
        return new

    def _feed_new(self, sym: _Symbol, new: list[Candle]) -> None:
        if not new:
            return
        first = len(sym.candles)
        sym.candles.extend(new)
        series = CandleSeries(sym.name, Timeframe.M1, sym.candles)
        for i in range(first, len(sym.candles)):
            view = series.view(i)
            candle = view.current
            bar_now = candle.ts + Timeframe.M1.duration
            orders = sym.strategy.on_candle(bar_now, {Timeframe.M1: view})
            for ref in sym.strategy.exits():
                self._exit(sym, ref, candle)
            for order in orders:
                self._enter(sym, order, candle, bar_now)

    # --- entries ----------------------------------------------------------------------------

    def _skip(self, sym: _Symbol, order, bar_now: datetime, reason: str, **extra) -> None:
        sym.strategy.on_order_skipped(order.ref, bar_now)
        self._set_signal(sym, bar_now, "skipped", reason)
        self.note("skip", symbol=sym.name, reason=reason, **extra)
        self._paper(sym, order, bar_now, None, "skipped", reason, 0.0, 0.0, "", extra)

    def _paper(self, sym, order, bar_now, candle_spread, status, reason, lots, real, ticket, extra):
        spread = extra.get("spread", 0.0) if candle_spread is None else candle_spread
        long = order.direction is Direction.BULLISH
        sim = order.entry + spread if long else order.entry
        self._append(
            "paper.csv",
            PAPER_COLUMNS,
            {
                "time_utc": bar_now.isoformat(),
                "symbol": sym.name,
                "side": "buy" if long else "sell",
                "signal_entry": order.entry,
                "sim_fill": sim,
                "sl": order.stop_loss,
                "spread": spread,
                "lots": lots,
                "status": status,
                "reason": reason,
                "real_fill": real or "",
                "slippage": (real - sim) * (1 if long else -1) if real else "",
                "ticket": ticket,
                "comment": self._comment(bar_now),
            },
        )

    def _comment(self, bar_now: datetime) -> str:
        return f"{self.config.comment_prefix} {bar_now:%m%d%H%M}"

    def _enter(self, sym: _Symbol, order, candle: Candle, bar_now: datetime) -> None:
        comment = self._comment(bar_now)
        existing = [p for p in own_positions(self.mt5, sym.broker) if p.comment == comment]
        if existing:  # a restart: the trade is already open, pick it up (no second order)
            self._register_existing(sym, order, existing[0], candle, bar_now, comment)
            return
        age = (self.now() - bar_now).total_seconds()
        if age > self.config.stale_signal_s:
            if bar_now >= prague_day_start(self.now(), self.config.guard.zone):
                self._skip(sym, order, bar_now, f"stale signal ({age:.0f} s old)")
            else:
                sym.strategy.on_order_skipped(order.ref, bar_now)
            return
        long = order.direction is Direction.BULLISH
        self.signals.append({
            "time": bar_now.isoformat(), "symbol": sym.name, "side": "buy" if long else "sell",
            "status": "signal", "reason": "",
        })  # fmt: skip
        self._tell("signal", {"symbol": sym.name, "side": "buy" if long else "sell",
                              "entry": order.entry, "sl": order.stop_loss})  # fmt: skip
        if self.paused:
            self._skip(sym, order, bar_now, "paused")
            return
        if self.blocked:
            self._skip(sym, order, bar_now, f"daily stop active: {self.blocked}")
            return
        if self._guard() == STOP:
            self._skip(sym, order, bar_now, "FTMO limit reached")
            return
        if self.blocked:
            self._skip(sym, order, bar_now, f"daily stop active: {self.blocked}")
            return
        info = self.mt5.symbol_info(sym.broker)
        account = self.mt5.account_info()
        sized = lots_for_risk(
            account.balance,
            self.config.risk_percent,
            abs(order.entry - order.stop_loss),
            spec_from_symbol_info(info),
        )
        if sized.lots is None:
            self._skip(sym, order, bar_now, sized.reason, spread=candle.spread)
            return
        sl = round(order.stop_loss, info.digits)
        tp = round(order.take_profit, info.digits) if order.take_profit else 0.0
        result, *_ = market_order(
            self.mt5, sym.broker, order.direction, sized.lots, sl, tp, self.log(), comment
        )
        if result is None or result.retcode != RETCODE_DONE:
            code = retcode_text(result.retcode) if result is not None else "no result"
            self._skip(sym, order, bar_now, f"order rejected: {code}", spread=candle.spread)
            return
        fill = confirm_open(self.mt5, result)
        position = fill.position
        if position is None:  # not visible in time: look for it by its comment
            found = [p for p in own_positions(self.mt5, sym.broker) if p.comment == comment]
            position = found[0] if found else None
        if position is None:
            self.note("error", symbol=sym.name, what="order accepted but no position found")
            sym.strategy.on_order_skipped(order.ref, bar_now)
            return
        long = order.direction is Direction.BULLISH
        real = fill.price or position.price_open
        value = spec_from_symbol_info(info).value_per_unit
        trade = _Trade(
            position.ticket, sym.name, sym.broker, order.ref, order.direction, sized.lots, sl,
            order.entry, order.entry + candle.spread if long else order.entry, real, bar_now,
            candle.ts, fill.commission, sized.lots * abs(order.entry - sl) * value, comment,
        )  # fmt: skip
        self._track(trade)
        self._set_signal(sym, bar_now, "filled")
        self.note(
            "order", symbol=sym.name, side="buy" if long else "sell", lots=sized.lots, sl=sl,
            fill=real, ticket=position.ticket, confirmed=fill.confirmed,
        )  # fmt: skip
        self._paper(sym, order, bar_now, candle.spread, "filled", sized.reason, sized.lots, real,
                    position.ticket, {})  # fmt: skip

    def _register_existing(self, sym, order, position, candle, bar_now, comment) -> None:
        if position.ticket in self.by_ticket:
            return
        info = self.mt5.symbol_info(sym.broker)
        value = spec_from_symbol_info(info).value_per_unit
        long = order.direction is Direction.BULLISH
        sl = position.sl or order.stop_loss
        trade = _Trade(
            position.ticket, sym.name, sym.broker, order.ref, order.direction, position.volume,
            sl, order.entry, order.entry + candle.spread if long else order.entry,
            position.price_open, bar_now, candle.ts, 0.0,
            position.volume * abs(order.entry - sl) * value, comment,
        )  # fmt: skip
        self._track(trade)
        self.note("resumed", symbol=sym.name, ticket=position.ticket, comment=comment)

    def _track(self, trade: _Trade) -> None:
        self.by_ticket[trade.ticket] = trade
        self.by_ref[(trade.symbol, trade.ref)] = trade

    # --- exits and closed trades ------------------------------------------------------------

    def _exit(self, sym: _Symbol, ref: object, candle: Candle) -> None:
        trade = self.by_ref.get((sym.name, ref))
        if trade is None:
            return
        found = self.mt5.positions_get(ticket=trade.ticket)
        if not found:
            return  # closed by the server; `_reconcile` reports it
        if not self._close(found[0], "session exit", ExitReason.SIGNAL, candle.close):
            self.pending_exits.append((sym.name, ref, candle.close))

    def _retry_exits(self) -> None:
        pending, self.pending_exits = self.pending_exits, []
        for name, ref, sim_exit in pending:
            trade = self.by_ref.get((name, ref))
            found = self.mt5.positions_get(ticket=trade.ticket) if trade else ()
            if found and not self._close(
                found[0], "session exit retry", ExitReason.SIGNAL, sim_exit
            ):
                self.pending_exits.append((name, ref, sim_exit))

    def _close(self, position, label: str, reason: ExitReason, sim_exit: float | None) -> bool:
        result, _, _ = close_volume(self.mt5, position, position.volume, self.log(), label)
        if result is None or result.retcode != RETCODE_DONE:
            code = retcode_text(result.retcode) if result is not None else "no result"
            self.note("close_failed", ticket=position.ticket, retcode=code)
            return False
        fill = confirm_close(self.mt5, result, position, position.volume)
        trade = self.by_ticket.get(position.ticket)
        if trade is not None:
            price = fill.price if fill.price else sim_exit
            self._finish(trade, price, fill.net, reason, sim_exit, self.now())
        return True

    def _close_all(self, label: str) -> None:
        """Close every position with our MAGIC (any symbol); the user's own are left alone."""
        for position in [p for p in (self.mt5.positions_get() or ()) if p.magic == MAGIC]:
            self._close(position, f"close all: {label}", ExitReason.SIGNAL, None)

    def _reconcile(self) -> None:
        """Trades whose position is gone (SL / TP hit on the server): report them."""
        for trade in list(self.by_ticket.values()):
            if self.mt5.positions_get(ticket=trade.ticket):
                continue
            deals = self.mt5.history_deals_get(position=trade.ticket) or ()
            out = [d for d in deals if getattr(d, "entry", None) == self.mt5.DEAL_ENTRY_OUT]
            if not out:
                self.note("closed_no_deal_yet", ticket=trade.ticket)
                continue
            volume = sum(d.volume for d in out)
            price = sum(d.price * d.volume for d in out) / volume
            money = (
                sum(
                    getattr(d, "profit", 0.0)
                    + getattr(d, "commission", 0.0)
                    + getattr(d, "swap", 0.0)
                    + getattr(d, "fee", 0.0)
                    for d in deals
                )
                - trade.open_commission
            )  # the open deal's commission is added in `_finish`
            reason = {
                self.mt5.DEAL_REASON_SL: ExitReason.STOP_LOSS,
                self.mt5.DEAL_REASON_TP: ExitReason.TAKE_PROFIT,
            }.get(getattr(out[-1], "reason", None), ExitReason.SIGNAL)
            sim_exit = trade.sl if reason is ExitReason.STOP_LOSS else price
            self._finish(trade, price, money, reason, sim_exit, self.now())

    def _finish(
        self,
        trade: _Trade,
        exit_price: float,
        close_money: float,
        reason: ExitReason,
        sim_exit: float | None,
        when: datetime,
    ) -> None:
        """Record a closed trade (R net from the deals' money), tell the strategy."""
        self.by_ticket.pop(trade.ticket, None)
        self.by_ref.pop((trade.symbol, trade.ref), None)
        sign = 1 if trade.direction is Direction.BULLISH else -1
        risk_dist = abs(trade.signal_entry - trade.sl)
        money = trade.open_commission + close_money
        r_net = money / trade.risk_money if trade.risk_money else 0.0
        r_gross = sign * (exit_price - trade.real_fill) / risk_dist
        sim_r = sign * (sim_exit - trade.sim_fill) / risk_dist if sim_exit is not None else ""
        result = TradeResult(
            symbol=trade.symbol, direction=trade.direction, entry_time=trade.entry_time,
            entry_candle=trade.candle_ts, entry=trade.signal_entry, entry_fill=trade.real_fill,
            initial_stop=trade.sl, take_profit=None, exit_time=when, exit_candle=when,
            exit_price=exit_price, exit_fill=exit_price, exit_reason=reason, r_gross=r_gross,
            r_net=r_net, spread_r=0.0, commission_r=0.0, break_even_time=None,
            break_even_stop=None, mae_r=0.0, mfe_r=0.0,
        )  # fmt: skip
        self.symbols[trade.symbol].strategy.on_trade_closed(trade.ref, result)
        self.day_trades.append((when, r_net))
        self._append(
            "trades.csv",
            TRADE_COLUMNS,
            {
                "symbol": trade.symbol,
                "side": "buy" if sign > 0 else "sell",
                "ticket": trade.ticket,
                "lots": trade.lots,
                "entry_time": trade.entry_time.isoformat(),
                "exit_time": when.isoformat(),
                "entry_fill": trade.real_fill,
                "exit_price": exit_price,
                "sl": trade.sl,
                "exit_reason": reason.value,
                "sim_exit": "" if sim_exit is None else sim_exit,
                "sim_r": sim_r,
                "r_gross": r_gross,
                "r_net": r_net,
                "money": money,
                "risk_money": trade.risk_money,
            },
        )
        self.note(
            "trade_closed", symbol=trade.symbol, ticket=trade.ticket, reason=reason.value,
            r_net=round(r_net, 3),
        )  # fmt: skip


def main(argv: list[str] | None = None) -> int:
    utf8_output()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--symbols", nargs="+", default=list(FORWARD_SYMBOLS))
    p.add_argument("--risk", type=float, default=BotConfig.risk_percent, help="percent per trade")
    p.add_argument("--daily-stop", type=float, default=GuardConfig().daily_stop_percent)
    p.add_argument("--balance", type=float, default=None,
                   help="initial balance override (default: the account's first balance deal)")  # fmt: skip
    args = p.parse_args(argv)
    settings = load_trading_settings()
    try:
        credentials = load_credentials(settings.platform)
    except CredentialStoreError as e:
        print(f"Credential store: {e}; using the terminal's logged-in account.")
        credentials = None
    config = BotConfig(
        symbols=tuple(s.upper() for s in args.symbols),
        risk_percent=args.risk,
        guard=GuardConfig(daily_stop_percent=args.daily_stop),
        initial_balance=args.balance,
    )
    config.out_dir.mkdir(parents=True, exist_ok=True)
    notifier = _telegram_notifier(config)
    bot = Bot(config, load_mt5(), settings, credentials, notifier=notifier)
    if notifier is not None:
        notifier.status_text = bot.status_text
        notifier.start()
    try:
        return bot.run()
    finally:
        if notifier is not None:
            notifier.stop()  # sends the last texts ("stopped")


def _telegram_notifier(config: BotConfig) -> Notifier | None:
    """Telegram from the Windows Credential Manager; none saved (or no keyring): no messages."""
    try:
        saved = load_telegram()
    except CredentialStoreError:
        return None
    if saved is None:
        return None
    return Notifier(TelegramClient(saved), config.stop_file, config.emergency_file)


if __name__ == "__main__":
    raise SystemExit(main())
