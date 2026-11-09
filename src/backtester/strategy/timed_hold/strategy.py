"""Strategy 10 (timed hold) as the `Strategy` the engine runs.

Spec: docs/strategy-timed-hold.md. Enter at the close of the 1m candle closing at `entry_time`
on a qualifying day, hold a fixed direction, stop = stop_atr x daily ATR, no take profit, time
exit at `exit_time`, optionally after `hold_days` trading days. The ATR sessions run on their own clock (`atr_zone`) and only
finished sessions count.
"""

from __future__ import annotations

import math
from collections import deque
from datetime import date, datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from backtester.core.models import Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.detectors.settings import DetectorSettings
from backtester.strategy.base import Order, Strategy
from backtester.strategy.session_stats import SessionStats, TimedExit
from backtester.strategy.timed_hold.config import TimedHoldConfig
from backtester.strategy.timed_hold.day_filter import DayFilter

if TYPE_CHECKING:
    from backtester.engine.trade import TradeResult

# warm-up in calendar days: trading days are 5 of 7 days, plus a margin for holidays
CALENDAR_PER_TRADING_DAY = 1.5
WARMUP_MARGIN_DAYS = 7


class TimedHold(Strategy):
    base_timeframe = Timeframe.M1
    timeframes = (Timeframe.M1,)
    uses_session_break_even = False  # no break-even at the next session, including multi-day holds

    def __init__(
        self,
        symbol: str,
        config: TimedHoldConfig | None = None,
        detectors: DetectorSettings | None = None,  # unused: no shared detector is needed
    ):
        self.symbol = symbol
        self.config = config = config or TimedHoldConfig()
        self._tz, self._atr_tz = ZoneInfo(config.zone), ZoneInfo(config.atr_zone)
        self._stats = SessionStats(
            config.atr_open, config.atr_close, config.atr_period,
            close_tolerance_min=config.atr_close_tolerance_min,
        )  # fmt: skip
        self._atr_day: date | None = None  # ATR-clock date of the last candle taken in
        self._exit = TimedExit()
        self._days = DayFilter(config)
        self._multi_ref: object | None = None
        self._exit_day: date | None = None
        self._closes: deque[float] = deque(maxlen=max(config.rsi_period + 1, config.sma_filter_days))
        self._rsi_changes = 0
        self._gain = self._loss = 0.0  # seed sums, then Wilder averages
        warmup = config.atr_period + 1
        if config.direction == "rsi":
            warmup = max(warmup, config.rsi_period + 1, config.sma_filter_days)
        self.min_warmup_days = math.ceil(warmup * CALENDAR_PER_TRADING_DAY) + (
            WARMUP_MARGIN_DAYS
        )

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        cfg = self.config
        candle = views[self.base_timeframe].current
        local = now.astimezone(self._tz)
        if cfg.hold_days == 0:
            self._exit.check(local, cfg.exit_time)
        elif self._exit_day is not None and (
            local.date() > self._exit_day
            or (local.date() == self._exit_day and local.time() >= cfg.exit_time)
        ):
            # TimedExit is shared: gate its check here by our strategy's calendar target.
            self._exit.check(local, cfg.exit_time)
        a = now.astimezone(self._atr_tz)
        # a later ATR date ends the session in progress, so it counts at this candle's entry
        if self._atr_day is not None and a.date() > self._atr_day:
            self._stats.finish()
            if cfg.direction == "rsi" and self._stats.prev_regular:
                self._remember_close(self._stats.prev_close)
            self._atr_day = None
        orders: list[Order] = []
        if (self._multi_ref is None and local.time() == cfg.entry_time
                and self._days.qualifies(local.date())):
            orders = self._entry(candle.close, local.date())
        weekend = cfg.atr_skip_weekend and a.weekday() >= 5
        if cfg.atr_open < a.time() <= cfg.atr_close and not weekend:
            self._stats.take_in(a.date(), a.time(), candle)
            self._atr_day = a.date()
        return orders

    def _entry(self, price: float, today: date) -> list[Order]:
        cfg = self.config
        atr = self._stats.atr
        if atr is None or atr <= 0:
            return []
        if cfg.direction in ("long", "short"):
            direction = Direction.BULLISH if cfg.direction == "long" else Direction.BEARISH
        elif cfg.direction == "rsi":
            direction = self._rsi_direction(price)
            if direction is None:
                return []
        else:  # vs the close of the last finished regular ATR session
            prev = self._stats.prev_close
            if prev is None or price == prev or abs(price - prev) < cfg.min_move_atr * atr:
                return []
            up = (price > prev) == (cfg.direction == "with_day")
            direction = Direction.BULLISH if up else Direction.BEARISH
        sign = 1 if direction is Direction.BULLISH else -1
        ref = self._exit.open(today)
        if cfg.hold_days:
            self._multi_ref = ref
            self._exit_day = self._days.after_trading_days(today, cfg.hold_days)
        return [
            Order(
                direction,
                price,
                price - sign * cfg.stop_atr * atr,
                None,
                reason=f"timed hold {cfg.direction} {cfg.stop_atr} ATR",
                ref=ref,
            )
        ]

    def _averages_with(self, price: float) -> tuple[float, float] | None:
        """Preview one close without advancing Wilder state. Spec: Hypothesis 10."""
        if not self._closes:
            return None
        change = price - self._closes[-1]
        gain, loss = max(change, 0.0), max(-change, 0.0)
        period = self.config.rsi_period
        if self._rsi_changes < period:
            if self._rsi_changes + 1 < period:
                return None
            return (self._gain + gain) / period, (self._loss + loss) / period
        return ((self._gain * (period - 1) + gain) / period,
                (self._loss * (period - 1) + loss) / period)

    def _remember_close(self, price: float) -> None:
        """Commit each finished regular ATR-session close once. Spec: Hypothesis 10."""
        if self._closes:
            averages = self._averages_with(price)
            if averages is None:
                change = price - self._closes[-1]
                self._gain += max(change, 0.0)
                self._loss += max(-change, 0.0)
            else:
                self._gain, self._loss = averages
            self._rsi_changes = min(self._rsi_changes + 1, self.config.rsi_period)
        self._closes.append(price)

    def _rsi(self, price: float) -> float | None:
        """Wilder RSI including today's known signal close. Spec: Hypothesis 10."""
        averages = self._averages_with(price)
        if averages is None:
            return None
        gain, loss = averages
        if gain + loss == 0:
            return None
        return 100 * gain / (gain + loss)

    def _rsi_direction(self, price: float) -> Direction | None:
        cfg = self.config
        rsi = self._rsi(price)
        if rsi is None or (cfg.sma_filter_days and len(self._closes) + 1 < cfg.sma_filter_days):
            return None
        sma = None
        if cfg.sma_filter_days:
            previous = list(self._closes)[-(cfg.sma_filter_days - 1):] if cfg.sma_filter_days > 1 else []
            sma = (sum(previous) + price) / cfg.sma_filter_days
        for direction, threshold in ((Direction.BULLISH, cfg.rsi_long_below),
                                     (Direction.BEARISH, cfg.rsi_short_above)):
            sign = 1 if direction is Direction.BULLISH else -1
            if (threshold > 0 and sign * (rsi - threshold) < 0
                    and (sma is None or sign * (price - sma) > 0)):
                return direction
        return None

    def exits(self) -> list[object]:
        return self._exit.take()

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        self._forget(ref)  # never filled (cost filter)

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        self._forget(ref)

    def _forget(self, ref: object) -> None:
        self._exit.forget(ref)
        if ref == self._multi_ref:
            self._multi_ref = self._exit_day = None
