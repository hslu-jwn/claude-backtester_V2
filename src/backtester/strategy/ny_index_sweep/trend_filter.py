"""Strategy 2's trend filter: the direction of the last SMA-band cross on one timeframe.

Spec: strategy-ny-indices.md › Backtest options › Trend filter. The cross rule is strategy 4's
`sma` signal (`SmaBandCross`); stops play no part, the trend is simply the last cross. Fed with
the filter timeframe's view on every base candle; it processes each candle closed since the
last call, in order, so it only ever knows closed candles.
"""

from __future__ import annotations

from backtester.core.models import Direction
from backtester.core.series import SeriesView
from backtester.detectors.atr import Atr
from backtester.strategy.ny_index_sweep.config import TrendFilterConfig
from backtester.strategy.trend_following.indicators import SmaBandCross


class TrendFilter:
    def __init__(self, config: TrendFilterConfig):
        self._atr = Atr(config.atr_period)
        self._cross = SmaBandCross(config.sma_period, config.band_atr)
        self._cursor = -1
        self.direction: Direction | None = None  # None until the first cross

    def update(self, view: SeriesView | None) -> None:
        if view is None:
            return
        for cursor in range(self._cursor + 1, view.cursor + 1):
            step = view.at(cursor)
            atr = self._atr.update(step)
            event = self._cross.update(step.current.close, atr)
            if event is not None:
                self.direction = event
        self._cursor = max(self._cursor, view.cursor)
