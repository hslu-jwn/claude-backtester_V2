"""Strategy 5 (gap fade) as the `Strategy` the engine runs.

Spec: docs/strategy-gap-fade.md. On the 1m candle that closes at the cash open (09:30 ET)
the strategy compares its close with the previous cash close and, if the gap is in the
traded ATR bucket, fades it: target = the previous cash close, stop = the mirror level.
The daily cash-session ATR and the previous cash close are built incrementally from the
1m candles (same definitions as `analytics/open_gap.py`: a regular day has a candle closing
at `cash_close`; the ATR is the Wilder ATR over regular days). A trade still open at
`exit_time` is closed by `exits()` at that candle, or at the first later candle.
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
from backtester.strategy.gap_fade.config import GapFadeConfig
from backtester.strategy.session_stats import SessionStats, TimedExit

if TYPE_CHECKING:
    from backtester.engine.trade import TradeResult

# warm-up in calendar days: trading days are 5 of 7 days, plus a margin for holidays
CALENDAR_PER_TRADING_DAY = 1.5
WARMUP_MARGIN_DAYS = 7


def _opposite(direction: Direction) -> Direction:
    return Direction.BEARISH if direction is Direction.BULLISH else Direction.BULLISH


class GapFade(Strategy):
    base_timeframe = Timeframe.M1
    timeframes = (Timeframe.M1,)
    uses_session_break_even = False  # a day trade: no break-even at the next session

    def __init__(
        self,
        symbol: str,
        config: GapFadeConfig | None = None,
        detectors: DetectorSettings | None = None,  # unused: no shared detector is needed
    ):
        self.symbol = symbol
        self.config = config = config or GapFadeConfig()
        self._tz = ZoneInfo(config.zone)
        self._stats = SessionStats(config.cash_open, config.cash_close, config.atr_period)
        self._exit = TimedExit()
        self.min_warmup_days = math.ceil((config.atr_period + 1) * CALENDAR_PER_TRADING_DAY) + (
            WARMUP_MARGIN_DAYS
        )

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        cfg = self.config
        candle = views[self.base_timeframe].current
        local = now.astimezone(self._tz)
        t = local.time()
        self._exit.check(local, cfg.exit_time)
        if cfg.cash_open < t <= cfg.cash_close:
            self._stats.take_in(local.date(), t, candle)
            return []
        if t != cfg.cash_open:
            return []
        self._stats.finish()
        return self._entry(candle.close, local.date())

    # --- entry and exit -----------------------------------------------------------------

    def _entry(self, open_price: float, today: date) -> list[Order]:
        cfg = self.config
        stats = self._stats
        atr, prev_close = stats.atr, stats.prev_close
        if not stats.prev_regular or prev_close is None or atr is None or atr <= 0:
            return []
        gap = open_price - prev_close
        if not cfg.min_gap_atr <= abs(gap) / atr < cfg.max_gap_atr:
            return []
        with_gap = Direction.BULLISH if gap > 0 else Direction.BEARISH
        direction = with_gap if cfg.mode == "follow" else _opposite(with_gap)
        sign = 1 if direction is Direction.BULLISH else -1
        # fade: target = the previous close; follow: the same distance on the other side
        target = prev_close if cfg.mode == "fade" else open_price + sign * abs(gap)
        ref = self._exit.open(today)
        return [
            Order(
                direction,
                open_price,
                open_price - sign * cfg.stop_gap_mult * abs(gap),
                target,
                reason=f"gap {cfg.mode} {gap / atr:+.2f} ATR",
                ref=ref,
            )
        ]

    def exits(self) -> list[object]:
        return self._exit.take()

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        self._exit.forget(ref)  # never filled (cost filter)

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        self._exit.forget(ref)  # stopped out or target hit before the time exit
