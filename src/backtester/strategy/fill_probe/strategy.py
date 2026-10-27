"""Fill probe: a TEST TOOL for the FTMO demo bot, not a researched strategy.

It sends many varied market orders (alternating long / short, every `interval_minutes`)
so slippage, spreads and commissions of real fills can be measured. Profit does not
matter: never research it, never trade it for profit.

Spec: docs/strategy-fill-probe.md. Only the `SeriesView` handed in is read (no lookahead).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from backtester.core.models import Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.detectors.atr import Atr
from backtester.detectors.settings import DetectorSettings
from backtester.strategy.base import Order, Strategy
from backtester.strategy.fill_probe.config import FillProbeConfig

if TYPE_CHECKING:
    from backtester.engine.trade import TradeResult

CONFLUENCE = "probe"
WARMUP_DAYS = 1


class FillProbe(Strategy):
    base_timeframe = Timeframe.M1
    timeframes = (Timeframe.M1,)
    uses_session_break_even = False
    min_warmup_days = WARMUP_DAYS

    def __init__(
        self,
        symbol: str,
        config: FillProbeConfig | None = None,
        detectors: DetectorSettings | None = None,  # unused: no shared detector is needed
    ):
        self.symbol = symbol
        self.config = config or FillProbeConfig()
        self._atr = Atr(self.config.atr_period)
        self._sent = 0  # orders sent (also the skipped ones): decides the next direction
        self._open: object | None = None  # ref of the open or pending trade
        self._entry_time: datetime | None = None
        self._now: datetime | None = None
        self._fed = 0  # candles fed to the ATR

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        view = views[self.base_timeframe]
        self._now = now
        if view is None:
            return []
        atr = self._update_atr(view)
        candle = view.current
        if candle.ts + self.base_timeframe.duration != now:  # market closed: no fresh candle
            return []
        if now.minute % self.config.interval_minutes != 0 or self._open is not None:
            return []
        if atr is None or atr <= 0:
            return []
        return [self._order(now, candle.close, atr)]

    def _update_atr(self, view: SeriesView) -> float | None:
        """Feed every candle up to the cursor once (also after a gap in the calls)."""
        for i in range(self._fed, view.cursor + 1):
            self._atr.update(view.at(i))
        self._fed = max(self._fed, view.cursor + 1)
        return self._atr.current

    def _order(self, now: datetime, entry: float, atr: float) -> Order:
        cfg = self.config
        direction = Direction.BULLISH if self._sent % 2 == 0 else Direction.BEARISH
        sign = 1 if direction is Direction.BULLISH else -1
        self._sent += 1
        stop = entry - sign * cfg.stop_atr * atr
        take_profit = entry + sign * cfg.target_r * abs(entry - stop) if cfg.target_r > 0 else None
        ref = ("fill_probe", self._sent)
        self._open, self._entry_time = ref, now
        side = "long" if sign > 0 else "short"
        return Order(
            direction,
            entry,
            stop,
            take_profit,
            reason=f"fill probe {side} #{self._sent}",
            confluence=CONFLUENCE,
            ref=ref,
        )

    def exits(self) -> list[object]:
        if self._open is None or self._entry_time is None or self._now is None:
            return []
        held = (self._now - self._entry_time).total_seconds() / 60
        return [self._open] if held >= self.config.max_hold_minutes else []

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        self._free(ref)

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        self._free(ref)

    def _free(self, ref: object) -> None:
        if ref == self._open:
            self._open = self._entry_time = None
