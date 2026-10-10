"""Swing high / low detector.

Spec: confluences.md › Swing high / low.
- High: green followed by red; price = highest wick of the two.
- Low: red followed by green; price = lowest wick of the two.
- Only the two candles at the turn count (the last green and the first red for a high).
- Doji/thin candles (body <= the symbol's doji threshold) are skipped: they don't break the
  pattern and their wicks don't count, so a swing can span more than 2 candles.
- Confirmed at the close of the turning candle (the red one for a high).

The turning candle of one swing is also the first candle of the next one: green, red, green
gives a high (confirmed by the red) and a low (confirmed by the second green).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType

from backtester.core.models import Candle
from backtester.core.series import SeriesView
from backtester.detectors.base import Detector, Event

# Gold is the reference pair: its user-defined doji threshold (0.065) is this share of its
# median 5m candle range (4.255, XAUUSD 2026-09-01..07). Other pairs default to the same
# share of their own median 5m range (spec: confluences.md › Swing high / low).
DOJI_REFERENCE_SYMBOL = "XAUUSD"
DOJI_RANGE_SHARE = 0.065 / 4.255

# Median 5m candle range (high - low) the other pairs' defaults come from, measured with
# `python -m backtester.data.check` (histdata.com): GBP pairs 2026-09-02..30, indices
# over 2020-01-02..2026-09-30 (user's choice, 2026-10-10).
MEDIAN_M5_RANGE = MappingProxyType(
    {"GBPUSD": 0.00028, "GBPJPY": 0.066, "NAS100": 11.57, "US500": 2.51}
)


class SwingKind(Enum):
    HIGH = "high"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class SwingConfig:
    # max |close - open| of a doji/thin candle, per symbol, in bid price units. Gold's is
    # set by the user; the others are the same share of their median 5m range. Pairs not
    # listed have no threshold: swings aren't computed for them.
    doji_max_body: Mapping[str, float] = field(
        default_factory=lambda: MappingProxyType(
            {
                DOJI_REFERENCE_SYMBOL: 0.065,
                **{s: equivalent_doji_body(r) for s, r in MEDIAN_M5_RANGE.items()},
            }
        )
    )

    def __post_init__(self) -> None:
        for symbol, value in self.doji_max_body.items():
            if value < 0:
                raise ValueError(f"doji_max_body for {symbol} must be >= 0")

    def doji_threshold(self, symbol: str) -> float:
        if symbol not in self.doji_max_body:
            raise KeyError(
                f"no doji threshold for {symbol}: set SwingConfig.doji_max_body "
                f"(default: {DOJI_RANGE_SHARE:.4f} x its median 5m candle range)"
            )
        return self.doji_max_body[symbol]


def equivalent_doji_body(median_m5_range: float) -> float:
    """Doji threshold for a pair whose median 5m candle range is `median_m5_range`, the
    same share of a typical candle as gold's 0.065."""
    return DOJI_RANGE_SHARE * median_m5_range


@dataclass(frozen=True, slots=True)
class SwingPoint(Event):
    kind: SwingKind
    price: float
    index: int  # candle holding the extreme wick (one of the two turn candles)
    ts: datetime  # open time of that candle
    first_index: int  # first turn candle (the green one for a high); last = confirmed_index


def is_doji(candle: Candle, max_body: float) -> bool:
    return candle.body <= max_body


def _extreme(kind: SwingKind, a: tuple[int, Candle], b: tuple[int, Candle]):
    """(index, candle, price) of the more extreme wick; on a tie the earlier candle."""
    sign = 1 if kind is SwingKind.HIGH else -1

    def wick(c: Candle) -> float:
        return c.high if kind is SwingKind.HIGH else c.low

    (ia, ca), (ib, cb) = a, b
    return (ib, cb, wick(cb)) if sign * wick(cb) > sign * wick(ca) else (ia, ca, wick(ca))


class SwingDetector(Detector[SwingPoint]):
    """Incremental: `update(view)` once per closed candle, in order."""

    def __init__(self, doji_max_body: float):
        if doji_max_body < 0:
            raise ValueError("doji_max_body must be >= 0")
        self.doji_max_body = doji_max_body
        self._next = 0  # cursor expected next
        self._last: tuple[int, Candle] | None = None  # last non-doji candle

    @classmethod
    def for_symbol(cls, symbol: str, config: SwingConfig | None = None) -> SwingDetector:
        return cls((config or SwingConfig()).doji_threshold(symbol))

    def update(self, view: SeriesView) -> list[SwingPoint]:
        if view.cursor != self._next:
            raise ValueError(
                f"SwingDetector.update must be called once per candle in order: "
                f"expected cursor {self._next}, got {view.cursor}"
            )
        self._next += 1
        candle = view.current
        if is_doji(candle, self.doji_max_body):
            return []
        prev, self._last = self._last, (view.cursor, candle)
        if prev is None or prev[1].is_green == candle.is_green:
            return []
        kind = SwingKind.HIGH if prev[1].is_green else SwingKind.LOW
        index, extreme, price = _extreme(kind, prev, self._last)
        return [
            SwingPoint(
                confirmed_index=view.cursor,
                confirmed_at=candle.ts + view.timeframe.duration,
                kind=kind,
                price=price,
                index=index,
                ts=extreme.ts,
                first_index=prev[0],
            )
        ]
