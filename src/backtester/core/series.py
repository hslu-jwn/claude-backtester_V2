"""Candle storage and the lookahead-safe view handed to detectors and strategies.

`CandleSeries` holds the full history and is owned ONLY by the engine.
Everything else (detectors, strategies, risk, charts during replay) receives a
`SeriesView`, which physically cannot return a candle after its cursor.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from itertools import pairwise

from backtester.core.errors import LookaheadError
from backtester.core.models import Candle, Timeframe


class CandleSeries:
    """Full, time-ordered history for one symbol + timeframe. Engine-private."""

    def __init__(self, symbol: str, timeframe: Timeframe, candles: Sequence[Candle]):
        for prev, cur in pairwise(candles):
            if cur.ts <= prev.ts:
                raise ValueError(f"Candles not strictly increasing: {prev.ts} -> {cur.ts}")
        self.symbol = symbol
        self.timeframe = timeframe
        self._candles: tuple[Candle, ...] = tuple(candles)

    def __len__(self) -> int:
        return len(self._candles)

    def view(self, cursor: int) -> SeriesView:
        """A view where candle `cursor` is the most recent CLOSED candle."""
        if not 0 <= cursor < len(self._candles):
            raise IndexError(f"cursor {cursor} out of range 0..{len(self._candles) - 1}")
        return SeriesView(self, cursor)


class SeriesView:
    """Read-only window onto candles[0 .. cursor] (inclusive).

    Indexing:
      view[i]   absolute index i, must be <= cursor
      view[-1]  the current (latest closed) candle, -2 the one before, etc.
      view.last(n) the n most recent candles, oldest first
    Any access past the cursor raises LookaheadError.
    """

    __slots__ = ("_cursor", "_series")

    def __init__(self, series: CandleSeries, cursor: int):
        self._series = series
        self._cursor = cursor

    @property
    def cursor(self) -> int:
        return self._cursor

    @property
    def symbol(self) -> str:
        return self._series.symbol

    @property
    def timeframe(self) -> Timeframe:
        return self._series.timeframe

    def __len__(self) -> int:
        return self._cursor + 1

    def __getitem__(self, idx: int) -> Candle:
        if isinstance(idx, slice):
            raise TypeError("Use view.last(n) or view.window(start, stop) instead of slicing")
        if idx < 0:
            idx = self._cursor + 1 + idx
            if idx < 0:
                raise IndexError("index before start of history")
        if idx > self._cursor:
            raise LookaheadError(f"index {idx} is in the future (cursor={self._cursor})")
        return self._series._candles[idx]

    def __iter__(self) -> Iterator[Candle]:
        return iter(self._series._candles[: self._cursor + 1])

    @property
    def current(self) -> Candle:
        return self[-1]

    def last(self, n: int) -> tuple[Candle, ...]:
        start = max(0, self._cursor + 1 - n)
        return self._series._candles[start : self._cursor + 1]

    def at(self, cursor: int) -> SeriesView:
        """An earlier view of the same series (candles 0..cursor). Never a later one."""
        if cursor > self._cursor:
            raise LookaheadError(f"view at {cursor} is in the future (cursor={self._cursor})")
        if cursor < 0:
            raise IndexError("cursor before start of history")
        return SeriesView(self._series, cursor)

    def window(self, start: int, stop: int) -> tuple[Candle, ...]:
        """Absolute indices [start, stop). `stop` may not exceed cursor + 1."""
        if stop < 0:
            raise IndexError("window stop before start of history")
        if stop > self._cursor + 1:
            raise LookaheadError(f"window stop {stop} is in the future (cursor={self._cursor})")
        return self._series._candles[max(0, start) : stop]
