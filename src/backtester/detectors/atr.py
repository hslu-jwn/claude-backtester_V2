"""ATR and the strong-move filter.

Spec: confluences.md › Strong-move filter.
ATR as on TradingView: true range smoothed with Wilder's RMA, seeded with the simple
average of the first n true ranges. A candle is a strong move if its range >= k * the ATR
of the n candles BEFORE it, so a big candle doesn't raise its own threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from backtester.core.models import Candle
from backtester.core.series import SeriesView


@dataclass(frozen=True, slots=True)
class StrongMoveConfig:
    atr_period: int = 14  # n: ATR over the n candles before (TBD: lookback to sweep)
    atr_mult: float = 2.0  # k: strong move = range >= k x ATR

    def __post_init__(self) -> None:
        if self.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if self.atr_mult <= 0:
            raise ValueError("atr_mult must be > 0")


def true_range(candle: Candle, prev_close: float | None) -> float:
    """max(high - low, |high - prev close|, |low - prev close|); high - low if no previous."""
    if not all(isfinite(price) for price in (candle.open, candle.high, candle.low, candle.close)):
        raise ValueError("ATR input prices must be finite")
    if prev_close is not None and not isfinite(prev_close):
        raise ValueError("ATR previous close must be finite")
    if prev_close is None:
        tr = candle.range
    else:
        tr = max(candle.range, abs(candle.high - prev_close), abs(candle.low - prev_close))
    if not isfinite(tr):
        raise ValueError("ATR true range must be finite")
    return tr


def is_strong_move(candle: Candle, atr: float | None, k: float) -> bool:
    """range >= k * atr. Without an ATR (warm-up) nothing is a strong move."""
    return atr is not None and candle.range >= k * atr


class Atr:
    """Incremental Wilder ATR(n). `update(view)` once per closed candle, in order.

    `at(i)` is the ATR known at the close of candle i (it includes candle i), or None
    while fewer than n candles exist. Values are never rewritten.
    """

    def __init__(self, period: int = 14):
        if period < 1:
            raise ValueError("period must be >= 1")
        self.period = period
        self._values: list[float | None] = []
        self._prev_close: float | None = None
        self._tr_sum = 0.0  # sum of true ranges during warm-up

    def update(self, view: SeriesView) -> float | None:
        if view.cursor != len(self._values):
            raise ValueError(
                f"Atr.update must be called once per candle in order: "
                f"expected cursor {len(self._values)}, got {view.cursor}"
            )
        candle = view.current
        tr = true_range(candle, self._prev_close)
        self._prev_close = candle.close
        n = self.period
        count = len(self._values) + 1
        if count < n:
            self._tr_sum += tr
            value = None
        elif count == n:
            value = (self._tr_sum + tr) / n
        else:
            prev = self._values[-1]
            assert prev is not None
            value = (prev * (n - 1) + tr) / n
        self._values.append(value)
        return value

    def at(self, index: int) -> float | None:
        """ATR at the close of candle `index`; only candles already processed."""
        if not 0 <= index < len(self._values):
            raise IndexError(f"ATR not known for candle {index} (processed {len(self._values)})")
        return self._values[index]

    @property
    def current(self) -> float | None:
        return self._values[-1] if self._values else None


class StrongMoveFilter:
    """Feeds an ATR and answers "was candle i a strong move?".

    Each detector that uses the filter (FVG, OB) owns one and calls `update(view)` once per
    closed candle before asking `is_strong`.
    """

    def __init__(self, config: StrongMoveConfig | None = None, *, atr: Atr | None = None):
        self.config = config = config or StrongMoveConfig()
        self.atr = atr if atr is not None else Atr(config.atr_period)
        self._strong: list[bool] = []

    def update(self, view: SeriesView) -> bool:
        """Process `view.current`; return whether it is a strong move."""
        # A sibling filter may already have fed the shared ATR this same closed view.
        self.atr.update(view)
        prior_atr = self.atr.at(view.cursor - 1) if view.cursor else None
        strong = is_strong_move(view.current, prior_atr, self.config.atr_mult)
        self._strong.append(strong)
        return strong

    def is_strong(self, index: int) -> bool:
        """Whether candle `index` (already processed) was a strong move."""
        if not 0 <= index < len(self._strong):
            raise IndexError(f"candle {index} not processed yet (processed {len(self._strong)})")
        return self._strong[index]

    def threshold_at(self, index: int) -> float | None:
        """Range candle `index` needed to be strong: k * ATR at the previous close."""
        self.is_strong(index)  # raises if candle `index` is not processed yet
        prior = self.atr.at(index - 1) if index > 0 else None
        return None if prior is None else self.config.atr_mult * prior
