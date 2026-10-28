"""Signal-close London-fix reversal on M1, using only completed SeriesViews.

Spec: strategy-london-fix.md > Entries, ATR and exits. The existing engine
processes stops before Strategy.exits(); both deadlines use that close-exit hook.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from math import isfinite
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from backtester.core.models import Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.detectors.atr import Atr
from backtester.detectors.settings import DetectorSettings
from backtester.strategy.base import Order, Strategy
from backtester.strategy.london_fix.config import SYMBOLS, LondonFixConfig, clock_time

if TYPE_CHECKING:
    from backtester.engine.trade import TradeResult


def _month_end(today: date) -> bool:
    """Spec: strategy-london-fix.md > Assumptions (last weekday, reporting only)."""
    following = today + timedelta(days=1)
    while following.weekday() >= 5:
        following += timedelta(days=1)
    return following.month != today.month


class LondonFix(Strategy):
    base_timeframe = Timeframe.M1
    timeframes = (Timeframe.M1,)
    uses_session_break_even = False

    def __init__(
        self,
        symbol: str,
        config: LondonFixConfig | None = None,
        detectors: DetectorSettings | None = None,
    ):
        self.symbol = symbol
        self.config = config = config or LondonFixConfig()
        self._tz = ZoneInfo("Europe/London")
        self._entry_time = clock_time(config.entry_time_london)
        self._force_time = clock_time(config.force_close_london)
        self._sides = dict(zip(SYMBOLS, config.side_map, strict=True))
        self._atr = Atr(config.atr_period)
        self._last_close: datetime | None = None
        self._entry_day: date | None = None
        self._ref: object | None = None
        self._deadline: datetime | None = None
        self._exit_queued = False

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        view = views.get(Timeframe.M1)
        if view is None:
            return []
        candle = view.current
        # Stale/misaligned callbacks must never substitute another candle for the fix.
        if candle.ts + Timeframe.M1.duration != now:
            return []
        if self._last_close is not None and now <= self._last_close:
            return []
        self._last_close = now
        atr = self._atr.update(view)
        local = now.astimezone(self._tz)
        if self._ref is not None:
            if self._deadline is not None and now >= self._deadline:
                self._exit_queued = True
            return []  # keep blocking until the engine confirms the trade is closed
        side = self._sides.get(self.symbol)
        if (
            side is None
            or local.weekday() >= 5
            or local.time() != self._entry_time
            or self._entry_day == local.date()
            or atr is None
            or not isfinite(atr)
            or atr <= 0
        ):
            return []
        distance = self.config.stop_atr_multiplier * atr
        if not isfinite(distance) or distance <= 0:
            return []
        self._entry_day = local.date()
        self._ref = (self.symbol, self._entry_day)
        force = datetime.combine(self._entry_day, self._force_time, self._tz).astimezone(UTC)
        self._deadline = min(now + timedelta(minutes=self.config.holding_minutes), force)
        return [
            Order(
                direction=Direction.BULLISH if side > 0 else Direction.BEARISH,
                entry=candle.close,
                stop_loss=candle.close - side * distance,
                take_profit=None,
                tags=frozenset({"month_end"}) if _month_end(self._entry_day) else frozenset(),
                reason="London fix reversal",
                ref=self._ref,
            )
        ]

    def exits(self) -> list[object]:
        if not self._exit_queued:
            return []
        self._exit_queued = False
        return [self._ref] if self._ref is not None else []

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        self._forget(ref)

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        self._forget(ref)

    def _forget(self, ref: object) -> None:
        if ref == self._ref:
            self._ref = self._deadline = None
            self._exit_queued = False
