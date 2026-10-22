"""Strategy 3 (no-wick candle in the trend) as the `Strategy` the engine runs.

Spec: strategy-no-wick.md. Per closed candle of the entry timeframe:
1. The structure (swings, BOS, trend) of the entry timeframe and, with TrendSource.HIGHER,
   of the next higher one is brought up to the candles closed by now.
2. Pending limit orders (entry modes body_end / middle) are checked against this candle:
   traded through -> filled at their level; too old -> dropped.
3. This candle is a signal when it has the trend's colour and no wick on the side the
   stop is on (uptrend: green, no lower wick). Then the SL goes beyond the last confirmed
   swing, the TP at `rr` x risk. `close` enters now, the other modes place a limit order.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.detectors.bos import BosDetector
from backtester.detectors.settings import DetectorSettings
from backtester.detectors.swings import SwingDetector, SwingKind, SwingPoint
from backtester.strategy.base import Order, Strategy
from backtester.strategy.no_wick.config import (
    HIGHER_TIMEFRAME,
    EntryMode,
    NoWickConfig,
    TrendSource,
)

STOP_SWING = {Direction.BULLISH: SwingKind.LOW, Direction.BEARISH: SwingKind.HIGH}


class Structure:
    """Swings, BOS and trend of one timeframe, fed with every closed candle in order."""

    def __init__(self, doji_max_body: float):
        self.bos = BosDetector(SwingDetector(doji_max_body))
        self._cursor = -1

    @property
    def trend(self) -> Direction | None:
        return self.bos.trend

    def update(self, view: SeriesView | None) -> None:
        if view is None:
            return
        for cursor in range(self._cursor + 1, view.cursor + 1):
            self.bos.update(view.at(cursor))
        self._cursor = view.cursor

    def last_swing(self, kind: SwingKind) -> SwingPoint | None:
        return next((s for s in reversed(self.bos.swings) if s.kind is kind), None)


@dataclass(slots=True)
class Pending:
    order: Order  # its entry is the limit level
    left: int  # candles it may still be filled in


def wick_share(direction: Direction, candle: Candle) -> float:
    """The wick on the stop side (bullish: lower) as a share of the candle's range."""
    span = candle.high - candle.low
    if direction is Direction.BULLISH:
        return (min(candle.open, candle.close) - candle.low) / span
    return (candle.high - max(candle.open, candle.close)) / span


class NoWick(Strategy):
    uses_session_break_even = False  # plain 1:1, no break-even move

    def __init__(
        self,
        symbol: str,
        config: NoWickConfig | None = None,
        detectors: DetectorSettings | None = None,
    ):
        self.symbol = symbol
        self.config = config = config or NoWickConfig()
        self.detectors = detectors = detectors or DetectorSettings()
        tf = config.timeframe
        self.base_timeframe = tf
        same = config.trend_source is TrendSource.SAME
        self.timeframes = (tf,) if same else (tf, HIGHER_TIMEFRAME[tf])
        self._trend_tf = self.timeframes[-1]
        doji = detectors.swings.doji_threshold(symbol)
        self._structures = {t: Structure(doji) for t in self.timeframes}
        self._pending: list[Pending] = []

    def pending_limit_orders(self) -> list[Order]:
        """Limits already placed at this close. Spec: strategy-no-wick.md › Entry."""
        return [p.order for p in self._pending]

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        for tf, structure in self._structures.items():
            structure.update(views[tf])
        candle = views[self.base_timeframe].current
        orders = self._fill_pending(candle)
        signal = self._signal(candle)
        if signal is None:
            return orders
        if self.config.entry_mode is EntryMode.CLOSE:
            orders.append(signal)
        else:
            self._pending.append(Pending(signal, self.config.order_expiry_candles))
        return orders

    def _fill_pending(self, candle: Candle) -> list[Order]:
        filled, waiting = [], []
        for p in self._pending:
            level = p.order.entry
            long = p.order.direction is Direction.BULLISH
            if candle.low <= level if long else candle.high >= level:
                order = p.order
                if not candle.low <= level <= candle.high:  # gapped through the level
                    order = replace(order, entry=candle.open)  # a limit fills at the open
                    sign = 1 if long else -1
                    if sign * (order.entry - order.stop_loss) <= 0:
                        continue  # gapped through the stop as well: dropped
                filled.append(order)
            elif p.left > 1:
                p.left -= 1
                waiting.append(p)
        self._pending = waiting
        return filled

    def _signal(self, candle: Candle) -> Order | None:
        direction = self._structures[self._trend_tf].trend
        if direction is None or candle.high <= candle.low:
            return None
        bullish = direction is Direction.BULLISH
        if (candle.close > candle.open) != bullish or candle.close == candle.open:
            return None  # the candle must have the trend's colour
        if wick_share(direction, candle) > self.config.max_wick_share:
            return None
        mode = self.config.entry_mode
        if mode is EntryMode.CLOSE:
            entry = candle.close
        elif mode is EntryMode.BODY_END:
            entry = candle.open
        else:
            entry = (candle.high + candle.low) / 2
        swing = self._structures[self.base_timeframe].last_swing(STOP_SWING[direction])
        sign = 1 if bullish else -1
        if swing is None or sign * (entry - swing.price) <= 0:
            return None
        stop = swing.price - sign * self.config.sl_buffer * abs(entry - swing.price)
        return Order(
            direction,
            entry,
            stop,
            entry + sign * self.config.rr * abs(entry - stop),
            reason=f"no-wick {mode.value}",
            limit_fill=mode is not EntryMode.CLOSE,
        )
