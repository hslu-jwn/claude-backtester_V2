"""Multi-timeframe alignment without lookahead.

The engine steps on the lowest ("base") timeframe. A higher-timeframe candle is
visible only once it has fully CLOSED at the current base-candle close time.
Example: stepping on M5, the H1 candle that opened at 10:00 becomes visible at
the close of the 10:55 M5 candle (i.e. at 11:00), never earlier.
"""

from __future__ import annotations

from bisect import bisect_right
from datetime import datetime

from backtester.core.series import CandleSeries, SeriesView


class HigherTimeframeClock:
    def __init__(self, series: CandleSeries):
        self._series = series
        dur = series.timeframe.duration
        # close time of every HTF candle, in order
        self._close_times: list[datetime] = [c.ts + dur for c in series._candles]
        self._view: SeriesView | None = None

    def view_at(self, now: datetime) -> SeriesView | None:
        """Most recent HTF view whose last candle closed at or before `now`.

        `now` must be the CLOSE time of the current base-timeframe candle.
        Returns None if no HTF candle has closed yet.
        """
        idx = bisect_right(self._close_times, now) - 1
        if idx < 0:
            return None
        # Reuse a snapshot only while its cursor is unchanged. Never advance a
        # previously returned view: detectors and chart replay may retain it.
        if self._view is None or self._view.cursor != idx:
            self._view = self._series.view(idx)
        return self._view
