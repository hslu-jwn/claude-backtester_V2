"""Strategy 10 (timed hold) as the `Strategy` the engine runs.

Spec: docs/strategy-timed-hold.md. Enter at the close of the 1m candle closing at `entry_time`
on a qualifying day, hold a fixed direction, stop = stop_atr x daily ATR, no take profit, time
exit at `exit_time` (`TimedExit`). The ATR sessions run on their own clock (`atr_zone`) and only
finished sessions count.
"""

from __future__ import annotations

import math
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
    uses_session_break_even = False  # a day trade: no break-even at the next session

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
        self.min_warmup_days = math.ceil((config.atr_period + 1) * CALENDAR_PER_TRADING_DAY) + (
            WARMUP_MARGIN_DAYS
        )

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        cfg = self.config
        candle = views[self.base_timeframe].current
        local = now.astimezone(self._tz)
        self._exit.check(local, cfg.exit_time)
        a = now.astimezone(self._atr_tz)
        # a later ATR date ends the session in progress, so it counts at this candle's entry
        if self._atr_day is not None and a.date() > self._atr_day:
            self._stats.finish()
        orders: list[Order] = []
        if local.time() == cfg.entry_time and self._days.qualifies(local.date()):
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
        else:  # vs the close of the last finished regular ATR session
            prev = self._stats.prev_close
            if prev is None or price == prev or abs(price - prev) < cfg.min_move_atr * atr:
                return []
            up = (price > prev) == (cfg.direction == "with_day")
            direction = Direction.BULLISH if up else Direction.BEARISH
        sign = 1 if direction is Direction.BULLISH else -1
        return [
            Order(
                direction,
                price,
                price - sign * cfg.stop_atr * atr,
                None,
                reason=f"timed hold {cfg.direction} {cfg.stop_atr} ATR",
                ref=self._exit.open(today),
            )
        ]

    def exits(self) -> list[object]:
        return self._exit.take()

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        self._exit.forget(ref)  # never filled (cost filter)

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        self._exit.forget(ref)  # stopped out before the time exit
