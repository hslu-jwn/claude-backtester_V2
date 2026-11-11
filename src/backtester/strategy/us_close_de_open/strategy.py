"""US close signal, European open execution.

Spec: strategy-us_close_de_open.md › Definitions / Assumptions / Decisions U1-U2.
"""

from __future__ import annotations

import csv
import math
from bisect import bisect_left
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from backtester.core.market import MarketView, ReferenceInput
from backtester.core.models import Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.detectors.settings import DetectorSettings
from backtester.strategy.base import MarketAwareStrategy, Order
from backtester.strategy.session_stats import SessionStats, TimedExit
from backtester.strategy.timed_hold.day_filter import DEFAULT_DIR
from backtester.strategy.timed_hold.strategy import CALENDAR_PER_TRADING_DAY, WARMUP_MARGIN_DAYS
from backtester.strategy.us_close_de_open.config import UsCloseDeOpenConfig

if TYPE_CHECKING:
    from backtester.engine.trade import TradeResult

# Numerical equality tolerance in percentage points (Assumption 3).
RETURN_TOLERANCE = 1e-9


class UsCloseDeOpen(MarketAwareStrategy):
    """Spec: strategy-us_close_de_open.md › Definitions (M1, one trade per day)."""

    base_timeframe = Timeframe.M1
    timeframes = (Timeframe.M1,)
    uses_session_break_even = False

    def __init__(
        self,
        symbol: str,
        config: UsCloseDeOpenConfig | None = None,
        detectors: DetectorSettings | None = None,
    ):
        self.symbol = symbol
        self.config = cfg = config or UsCloseDeOpenConfig()
        self.references = (
            ReferenceInput(cfg.ref_symbol, "signal", (Timeframe.M1,),
                           max_age=timedelta(days=7), required=False),
        )
        self._tz = ZoneInfo(cfg.zone)
        self._atr_tz = ZoneInfo(cfg.atr_zone)
        self._ref_tz = ZoneInfo(cfg.ref_zone)
        self._stats = SessionStats(cfg.atr_open, cfg.atr_close, cfg.atr_period,
                                   close_tolerance_min=cfg.atr_close_tolerance_min)
        self._atr_day: date | None = None
        self._entry_day: date | None = None
        self._exit = TimedExit()
        self._excluded: set[date] = set()
        if cfg.skip_nyse_short_days:
            folder = Path(cfg.calendar_dir) if cfg.calendar_dir else DEFAULT_DIR
            with (folder / "nyse_holidays.csv").open(newline="", encoding="utf-8") as handle:
                self._excluded = {
                    date.fromisoformat(row["date"]) for row in csv.DictReader(handle)
                    if row["type"].strip() in ("closed", "early_close_13:00")
                }
        self.min_warmup_days = (
            math.ceil((cfg.atr_period + 1) * CALENDAR_PER_TRADING_DAY) + WARMUP_MARGIN_DAYS
        )

    def on_market_candle(
        self, now: datetime, primary_views: dict[Timeframe, SeriesView | None], market: MarketView
    ) -> list[Order]:
        """Feed ATR every minute; read references only at entry. Spec: Definitions / U2."""
        cfg = self.config
        view = primary_views[self.base_timeframe]
        if view is None:
            return []
        candle = view.current
        local, atr_local = now.astimezone(self._tz), now.astimezone(self._atr_tz)
        self._exit.check(local, cfg.exit_time)
        if self._atr_day is not None and atr_local.date() > self._atr_day:
            self._stats.finish()
            self._atr_day = None
        orders = []
        if (local.time() == cfg.entry_time and local.weekday() < 5
                and self._entry_day != local.date()):
            today = local.date()
            signal_day = today - timedelta(days=1)
            while signal_day.weekday() >= 5:
                signal_day -= timedelta(days=1)
            atr = self._stats.atr
            if (today not in self._excluded and signal_day not in self._excluded
                    and atr is not None and atr > 0):
                direction = self._direction(signal_day, market)
                if direction is not None:
                    sign = 1 if direction is Direction.BULLISH else -1
                    self._entry_day = today
                    orders.append(Order(
                        direction, candle.close, candle.close - sign * cfg.stop_atr * atr, None,
                        reason=f"US close / European open {cfg.direction} {cfg.stop_atr} ATR",
                        ref=self._exit.open(today),
                    ))
        # As in timed_hold, the entry uses finished sessions before taking in this candle.
        if cfg.atr_open < atr_local.time() <= cfg.atr_close:
            self._stats.take_in(atr_local.date(), atr_local.time(), candle)
            self._atr_day = atr_local.date()
        return orders

    def _direction(self, signal_day: date, market: MarketView) -> Direction | None:
        """Exact previous-weekday endpoints, no availability gate. Spec: Definitions / G5 / U2."""
        cfg = self.config
        if cfg.direction in ("long", "short"):
            return Direction.BULLISH if cfg.direction == "long" else Direction.BEARISH
        view = market.views.get(cfg.ref_symbol, {}).get(Timeframe.M1)
        if view is None:
            return None
        start = self._close(view, signal_day, cfg.ref_from)
        end = self._close(view, signal_day, cfg.ref_to)
        if start is None or end is None:
            return None
        change = 100 * (end / start - 1)
        if change >= cfg.min_ref_return_pct - RETURN_TOLERANCE:
            return Direction.BULLISH
        if change <= -cfg.min_ref_return_pct + RETURN_TOLERANCE:
            return Direction.BEARISH
        return None

    def _close(self, view: SeriesView, day: date, clock: time) -> float | None:
        """Binary search only the bounded view. Spec: Definitions › Signal (G2, G5)."""
        timestamp = (
            datetime.combine(day, clock, self._ref_tz).astimezone(UTC) - Timeframe.M1.duration
        )
        index = bisect_left(view, timestamp, key=lambda candle: candle.ts)
        if index < len(view) and view[index].ts == timestamp:
            return view[index].close
        return None

    def exits(self) -> list[object]:
        return self._exit.take()

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        self._exit.forget(ref)

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        self._exit.forget(ref)
