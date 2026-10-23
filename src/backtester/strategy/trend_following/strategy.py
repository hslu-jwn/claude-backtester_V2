"""Strategy 4 (trend following, Kaufman style) as the `Strategy` the engine runs.

Spec: strategy-trend-following.md. Per closed candle of the one strategy timeframe:
1. The indicators (channel / SMA / KAMA, ATR) take the candle in.
2. The signal rule gives at most one event, a direction. Nothing is decided before the
   indicator has its full history (warm-up) or while the ATR is unknown.
3. An event with the open position's direction changes nothing. Without a position it
   opens one at the close; against the position it closes it at this close (`exits`,
   ExitReason.SIGNAL) and opens the reverse one at the same close.
4. Every position has a stop 3 x ATR from the entry (1R), no target, no trailing.

The strategy knows its position only through its own orders and `on_trade_closed`: the
engine reports a stop-out before the next `on_candle`, so an event in the stop candle
finds the strategy flat and enters at that candle's close.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import TYPE_CHECKING

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.detectors.atr import Atr
from backtester.detectors.settings import DetectorSettings
from backtester.strategy.base import Order, Strategy
from backtester.strategy.trend_following.config import Signal, TrendFollowingConfig
from backtester.strategy.trend_following.indicators import (
    DunniganSwings,
    Kama,
    Momentum,
    RollingChannel,
    SmaBandCross,
)

if TYPE_CHECKING:
    from backtester.engine.trade import TradeResult

# warm-up in calendar days from candles: candles exist on trading days only (5 of 7 days),
# plus a margin for holidays and thin weeks
CALENDAR_PER_TRADING_DAY = 1.5
WARMUP_MARGIN_DAYS = 3
# Dunnigan swings need a few swings of history before a swing top / bottom exists; the signal
# itself waits for the first real swing, so this only sizes the data loaded before the run
DUNNIGAN_WARMUP_CANDLES = 10


class TrendFollowing(Strategy):
    uses_session_break_even = False  # no break-even, no trailing: the stop never moves

    def __init__(
        self,
        symbol: str,
        config: TrendFollowingConfig | None = None,
        detectors: DetectorSettings | None = None,  # unused: no shared detector is needed
    ):
        self.symbol = symbol
        self.config = config = config or TrendFollowingConfig()
        self.base_timeframe = config.timeframe
        self.timeframes = (config.timeframe,)
        self._atr = Atr(config.atr_period)
        self._channel = RollingChannel(config.breakout_period)
        self._sma_cross = SmaBandCross(config.sma_period, config.sma_band_atr)
        self._momentum = Momentum(config.momentum_period)
        self._dunnigan = DunniganSwings()
        self._kama = Kama(
            config.kama_er_period,
            config.kama_fast,
            config.kama_slow,
            config.kama_filter,
            config.kama_filter_period,
        )
        self._position: Direction | None = None
        self._ref: int | None = None  # ref of the open position's order
        self._next_ref = 0
        self._to_close: list[object] = []
        self.min_warmup_days = self._warmup_days()

    @property
    def warmup_candles(self) -> int:
        """Closed candles needed before the first order is possible (candles counted
        from 0: the first order can come at the candle with this index)."""
        c = self.config
        # SMA(N) exists at N - 1, the cross needs the one before; with a band the ATR and
        # the one before it must exist too (ATR exists at atr_period - 1)
        sma = max(c.sma_period, c.atr_period) if c.sma_band_atr > 0 else c.sma_period
        signal = {
            Signal.BREAKOUT: c.breakout_period,
            Signal.SMA: sma,
            Signal.MOMENTUM: c.momentum_period,
            Signal.DUNNIGAN: DUNNIGAN_WARMUP_CANDLES,
            Signal.KAMA: c.kama_er_period + c.kama_filter_period,
        }[c.signal]
        return max(signal, c.atr_period - 1)

    def _warmup_days(self) -> int:
        """Calendar days of history before the first run day so the indicators are warm."""
        per_day = self.base_timeframe.duration.total_seconds() / 86400
        days = self.warmup_candles * per_day * CALENDAR_PER_TRADING_DAY
        return math.ceil(days) + WARMUP_MARGIN_DAYS

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        view = views[self.base_timeframe]
        candle = view.current
        atr = self._atr.update(view)
        event = self._event(candle, atr)  # the indicators take every candle in, in order
        if event is None or atr is None or atr <= 0 or event is self._position:
            return []
        if self._position is not None:
            self._to_close.append(self._ref)  # stop and reverse: closed by `exits`
        sign = 1 if event is Direction.BULLISH else -1
        self._position, self._ref = event, self._next_ref
        self._next_ref += 1
        stop = candle.close - sign * self.config.stop_atr_mult * atr
        return [
            Order(
                event,
                candle.close,
                stop,
                None,
                reason=f"trend {self.config.signal.value}",
                ref=self._ref,
            )
        ]

    def exits(self) -> list[object]:
        out, self._to_close = self._to_close, []
        return out

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        if ref == self._ref:  # never filled (cost filter): flat, the next event tries again
            self._position = self._ref = None

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        if ref == self._ref:  # the position the strategy still holds (a stop-out)
            self._position = self._ref = None

    # --- signals -----------------------------------------------------------------------

    def _event(self, candle: Candle, atr: float | None) -> Direction | None:
        signal = self.config.signal
        if signal is Signal.SMA:
            return self._sma_cross.update(candle.close, atr)
        if signal is Signal.KAMA:
            self._kama.update(candle.close)
            return self._kama.signal
        if signal is Signal.MOMENTUM:
            return self._momentum.update(candle.close)
        if signal is Signal.DUNNIGAN:
            return self._dunnigan.update(candle)
        channel = self._channel.update(candle)
        if channel is None:  # breakout
            return None
        for direction, level in ((Direction.BULLISH, channel[0]), (Direction.BEARISH, channel[1])):
            sign = 1 if direction is Direction.BULLISH else -1
            if sign * (candle.close - level) > 0:
                return direction
        return None
