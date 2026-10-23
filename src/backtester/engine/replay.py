"""Stepping through time candle by candle, without lookahead. Spec: ROADMAP.md › 1.2.

`Replay` owns the full `CandleSeries` and hands out only `SeriesView`s, so whatever is built
from it (the chart replay now, the backtest loop in 3.1) sees exactly the candles that have
closed at the cursor. The cursor is an index into the stepped ("base") timeframe; `now` is
the close time of that candle.

Higher timeframes come only from `HigherTimeframeClock`: a higher-timeframe candle is
visible once it has fully closed at `now`, never while it is still forming. Around the
daily break or a weekend this can make it appear one step "late": the 21:00 H1 candle of
gold shows up at the close of the first M5 candle after the break, because there is no
21:55 M5 candle whose close is 22:00. That is correct, not a bug.

The `overall` series is the overall-trend timeframe (confluences.md › Trend, default 4H),
usually with history from before the base range so the trend is known at its start. It
can be any timeframe, also the base one, and is read the same way: only its candles
closed at `now`.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from backtester.core.models import Timeframe
from backtester.core.mtf import HigherTimeframeClock
from backtester.core.series import CandleSeries, SeriesView


class Replay:
    def __init__(
        self,
        base: CandleSeries,
        higher: Sequence[CandleSeries] = (),
        overall: CandleSeries | None = None,
    ):
        if len(base) == 0:
            raise ValueError("Replay needs at least one candle")
        self._base = base
        self._duration = base.timeframe.duration
        self._base_clock = HigherTimeframeClock(base)  # close time -> base cursor
        self._clocks: dict[Timeframe, HigherTimeframeClock] = {}
        for series in higher:
            if series.timeframe.value <= base.timeframe.value:
                raise ValueError(
                    f"{series.timeframe.name} is not higher than {base.timeframe.name}"
                )
            if series.symbol != base.symbol:
                raise ValueError(f"{series.symbol} series in a {base.symbol} replay")
            self._clocks[series.timeframe] = HigherTimeframeClock(series)
        if overall is not None and overall.symbol != base.symbol:
            raise ValueError(f"{overall.symbol} overall series in a {base.symbol} replay")
        self._overall = overall
        self._overall_clock = HigherTimeframeClock(overall) if overall else None

    def __len__(self) -> int:
        return len(self._base)

    @property
    def symbol(self) -> str:
        return self._base.symbol

    @property
    def timeframe(self) -> Timeframe:
        return self._base.timeframe

    def view(self, cursor: int) -> SeriesView:
        """Base candles 0..cursor; candle `cursor` is the latest closed one."""
        return self._base.view(cursor)

    def close_time(self, cursor: int) -> datetime:
        """`now` at `cursor`: the close time of base candle `cursor`."""
        if not 0 <= cursor < len(self._base):
            raise IndexError(f"cursor {cursor} out of range 0..{len(self._base) - 1}")
        return self._base._candles[cursor].ts + self._duration

    def cursor_at(self, now: datetime) -> int | None:
        """Cursor of the latest base candle closed at or before `now` (None: none yet)."""
        view = self._base_clock.view_at(now)
        return None if view is None else view.cursor

    def higher_view(self, cursor: int, timeframe: Timeframe) -> SeriesView | None:
        """Closed `timeframe` candles at the cursor's close time (None: none closed yet)."""
        if timeframe not in self._clocks:
            raise KeyError(f"no {timeframe.name} series in this replay")
        return self._clocks[timeframe].view_at(self.close_time(cursor))

    def higher_view_at(self, now: datetime, timeframe: Timeframe) -> SeriesView | None:
        """Closed HTF candles at the base close time already computed by the engine.

        Spec: ARCHITECTURE.md, closed-only higher-timeframe alignment.
        """
        if timeframe not in self._clocks:
            raise KeyError(f"no {timeframe.name} series in this replay")
        return self._clocks[timeframe].view_at(now)

    @property
    def overall_timeframe(self) -> Timeframe | None:
        return self._overall.timeframe if self._overall else None

    def overall_view(self, cursor: int) -> SeriesView | None:
        """Closed overall-trend candles at the cursor's close time (None: none closed yet)."""
        if self._overall_clock is None:
            raise KeyError("no overall-trend series in this replay")
        return self._overall_clock.view_at(self.close_time(cursor))
