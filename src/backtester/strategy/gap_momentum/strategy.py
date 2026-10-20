"""Strategy 7 (gap momentum) as the `Strategy` the engine runs.

Spec: docs/strategy-gap-momentum.md. On the 1m candle that closes at the session open (09:30 ET
for indices, 05:00 ET for fx) the strategy compares its close with the previous session's high /
low: beyond it by `entry_z` x sd (sd of the last `vol_days` daily log returns) it trades with the
gap, stop `stop_atr` x daily ATR, no target, a signal exit at `exit_time` (`TimedExit`). The
session statistics are built incrementally (`SessionStats`). Bullish is described, bearish is
mirrored through `Direction`.
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
from backtester.strategy.gap_momentum.config import GapMomentumConfig
from backtester.strategy.session_stats import SessionStats, TimedExit

if TYPE_CHECKING:
    from backtester.engine.trade import TradeResult

# warm-up in calendar days: trading days are 5 of 7 days, plus a margin for holidays
CALENDAR_PER_TRADING_DAY = 1.5
WARMUP_MARGIN_DAYS = 7


def _opposite(direction: Direction) -> Direction:
    return Direction.BEARISH if direction is Direction.BULLISH else Direction.BULLISH


class GapMomentum(Strategy):
    base_timeframe = Timeframe.M1
    timeframes = (Timeframe.M1,)
    uses_session_break_even = False  # a day trade: no break-even at the next session

    def __init__(
        self,
        symbol: str,
        config: GapMomentumConfig | None = None,
        detectors: DetectorSettings | None = None,  # unused: no shared detector is needed
    ):
        self.symbol = symbol
        self.config = config = config or GapMomentumConfig()
        self._tz = ZoneInfo(config.zone)
        self._stats = SessionStats(
            config.session_open,
            config.session_close,
            config.atr_period,
            config.vol_days,
            config.close_tolerance_min,
        )
        self._exit = TimedExit()
        history = max(config.vol_days + 1, config.atr_period + 1)  # sessions needed
        self.min_warmup_days = math.ceil(history * CALENDAR_PER_TRADING_DAY) + WARMUP_MARGIN_DAYS

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        cfg = self.config
        candle = views[self.base_timeframe].current
        local = now.astimezone(self._tz)
        t = local.time()
        self._exit.check(local, cfg.exit_time_resolved)
        if cfg.session_open < t <= cfg.session_close:
            self._stats.take_in(local.date(), t, candle)
            return []
        if t != cfg.session_open:
            return []
        self._stats.finish()
        return self._entry(candle.close, local.date())

    def _gap_direction(self, open_price: float, sd: float) -> Direction | None:
        """The side of the gap beyond the previous session's range, or None."""
        stats, z = self._stats, self.config.entry_z
        if open_price > stats.prev_high * (1 + z * sd):
            return Direction.BULLISH
        if open_price < stats.prev_low * (1 - z * sd):
            return Direction.BEARISH
        return None

    def _entry(self, open_price: float, today: date) -> list[Order]:
        cfg, stats = self.config, self._stats
        sd, atr = stats.vol_sd(), stats.atr
        if not stats.prev_regular or sd is None or atr is None or atr <= 0:
            return []
        with_gap = self._gap_direction(open_price, sd)
        if with_gap is None:
            return []
        direction = with_gap if cfg.side == "momentum" else _opposite(with_gap)
        sign = 1 if direction is Direction.BULLISH else -1
        stop_distance = cfg.stop_atr * atr
        target = open_price + sign * cfg.target_r * stop_distance if cfg.target_r > 0 else None
        return [
            Order(
                direction,
                open_price,
                open_price - sign * stop_distance,
                target,
                reason=f"gap {cfg.side} {'up' if with_gap is Direction.BULLISH else 'down'}",
                ref=self._exit.open(today),
            )
        ]

    def exits(self) -> list[object]:
        return self._exit.take()

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        self._exit.forget(ref)  # never filled (cost filter)

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        self._exit.forget(ref)  # stopped out or target hit before the time exit
