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
from datetime import date, datetime, time
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.detectors.settings import DetectorSettings
from backtester.strategy.base import Order, Strategy
from backtester.strategy.gap_fade.config import GapFadeConfig

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
        # the cash session in progress (candles closing in (cash_open, cash_close])
        self._day: date | None = None
        self._high = self._low = self._last_close = 0.0
        self._has_close = False  # the candle closing at cash_close exists
        # state of the sessions finished so far
        self._prev_regular = False  # the previous session was regular
        self._prev_close: float | None = None  # the close of the last regular session
        self._atr: float | None = None
        self._trs: list[float] = []  # true ranges until the ATR has `atr_period` days
        self._ref: int | None = None  # ref of the open trade's order
        self._ref_date: date | None = None
        self._next_ref = 0
        self._to_close: list[object] = []
        self.min_warmup_days = math.ceil((config.atr_period + 1) * CALENDAR_PER_TRADING_DAY) + (
            WARMUP_MARGIN_DAYS
        )

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        cfg = self.config
        candle = views[self.base_timeframe].current
        local = now.astimezone(self._tz)
        t = local.time()
        self._check_exit(local)
        if cfg.cash_open < t <= cfg.cash_close:
            self._take_in(local.date(), t, candle)
            return []
        if t != cfg.cash_open:
            return []
        self._finish_session()
        return self._entry(candle.close, local.date())

    # --- the cash session ---------------------------------------------------------------

    def _take_in(self, day: date, t: time, candle: Candle) -> None:
        if day != self._day:
            self._finish_session()
            self._day = day
            self._high, self._low, self._has_close = candle.high, candle.low, False
        else:
            self._high = max(self._high, candle.high)
            self._low = min(self._low, candle.low)
        self._last_close = candle.close
        if t == self.config.cash_close:
            self._has_close = True

    def _finish_session(self) -> None:
        """Close the session in progress: a regular one feeds the ATR and the previous close."""
        if self._day is None:
            return
        self._prev_regular = self._has_close
        if self._has_close:
            tr = self._high - self._low
            if self._prev_close is not None:
                tr = max(tr, abs(self._high - self._prev_close), abs(self._low - self._prev_close))
            self._prev_close = self._last_close
            period = self.config.atr_period
            if self._atr is None:
                self._trs.append(tr)
                if len(self._trs) == period:
                    self._atr = sum(self._trs) / period
            else:
                self._atr = (self._atr * (period - 1) + tr) / period
        self._day = None

    # --- entry and exit -----------------------------------------------------------------

    def _entry(self, open_price: float, today: date) -> list[Order]:
        cfg = self.config
        atr, prev_close = self._atr, self._prev_close
        if not self._prev_regular or prev_close is None or atr is None or atr <= 0:
            return []
        gap = open_price - prev_close
        if not cfg.min_gap_atr <= abs(gap) / atr < cfg.max_gap_atr:
            return []
        with_gap = Direction.BULLISH if gap > 0 else Direction.BEARISH
        direction = with_gap if cfg.mode == "follow" else _opposite(with_gap)
        sign = 1 if direction is Direction.BULLISH else -1
        # fade: target = the previous close; follow: the same distance on the other side
        target = prev_close if cfg.mode == "fade" else open_price + sign * abs(gap)
        self._ref, self._ref_date = self._next_ref, today
        self._next_ref += 1
        return [
            Order(
                direction,
                open_price,
                open_price - sign * cfg.stop_gap_mult * abs(gap),
                target,
                reason=f"gap {cfg.mode} {gap / atr:+.2f} ATR",
                ref=self._ref,
            )
        ]

    def _check_exit(self, local: datetime) -> None:
        """Queue the open trade for `exits` at `exit_time`, or at the first later candle."""
        if self._ref is None or self._ref_date is None:
            return
        if local.date() > self._ref_date or local.time() >= self.config.exit_time:
            self._to_close.append(self._ref)
            self._ref = self._ref_date = None

    def exits(self) -> list[object]:
        out, self._to_close = self._to_close, []
        return out

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        if ref == self._ref:  # never filled (cost filter)
            self._ref = self._ref_date = None

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        if ref == self._ref:  # stopped out or target hit before the time exit
            self._ref = self._ref_date = None
