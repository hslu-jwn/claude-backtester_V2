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
from math import isfinite
from types import MappingProxyType

from backtester.core.models import Candle
from backtester.core.series import SeriesView
from backtester.detectors.base import Detector, Event

# Gold is the reference pair: its user-defined doji threshold (0.065) is this share of its
# median 5m candle range (4.255, XAUUSD 2026-09-01..07). Other pairs default to the same
# share of their own median 5m range (spec: confluences.md › Swing high / low).
DOJI_REFERENCE_SYMBOL = "XAUUSD"
DOJI_RANGE_SHARE = 0.065 / 4.255
DEFAULT_DOJI_RELATIVE_TOLERANCE = 1e-9

# Median 5m candle range (high - low) the other pairs' defaults come from, measured with
# `tools.check.history_median_m5_range` (bid, flat zero-volume minutes dropped, read through
# DEFAULT_SOURCES: MT5 day by day, else histdata / Binance). GBP pairs 2026-09-02..30 and
# NAS100 / US500 2020-01-02..2026-09-30 (user's choice, 2026-10-10); every other symbol over
# its full cached history, measured 2026-10-20 (user's choice; periods in confluences.md).
MEDIAN_M5_RANGE = MappingProxyType(
    {
        "GBPUSD": 0.00028, "GBPJPY": 0.066, "NAS100": 11.57, "US500": 2.51,
        "EURUSD": 0.00034, "USDJPY": 0.035, "AUDUSD": 0.00032, "USDCAD": 0.00034,
        "USDCHF": 0.00029, "NZDUSD": 0.00031, "EURJPY": 0.050, "EURGBP": 0.00024,
        "XAGUSD": 0.024, "GER40": 9.0, "UK100": 4.29, "JP225": 20.0, "EU50": 3.0,
        "USOIL": 0.079, "UKOIL": 0.081, "DXY": 0.060,
        "US30": 17.0, "US2000": 1.40, "NATGAS": 0.0060, "BTCUSD": 52.5, "ETHUSD": 3.5,
        "BTCUSDT": 74.8, "ETHUSDT": 4.48,
    }
)  # fmt: skip


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
    # 0 = off (the fixed amounts above). > 0 (user, 2026-10-12): a doji is a body of at most
    # this share of the candle's own range, on every timeframe and symbol (e.g. 0.1)
    doji_range_share: float = 0.0
    # Spec: confluences.md › Swing high / low (B9, user 2026-10-22).
    # Inclusive comparison slack as a share of max(abs(open), abs(close)); 0 = strict.
    doji_relative_tolerance: float = DEFAULT_DOJI_RELATIVE_TOLERANCE

    def __post_init__(self) -> None:
        if not isfinite(self.doji_relative_tolerance) or self.doji_relative_tolerance < 0:
            raise ValueError("doji_relative_tolerance must be finite and >= 0")
        if not 0 <= self.doji_range_share <= 1:
            raise ValueError("doji_range_share must be between 0 and 1")
        for symbol, value in self.doji_max_body.items():
            if value < 0:
                raise ValueError(f"doji_max_body for {symbol} must be >= 0")

    def doji_threshold(self, symbol: str) -> float:
        if self.doji_range_share > 0:
            return RangeShare(self.doji_range_share, self.doji_relative_tolerance)
        if symbol not in self.doji_max_body:
            raise KeyError(
                f"no doji threshold for {symbol}: set SwingConfig.doji_max_body "
                f"(default: {DOJI_RANGE_SHARE:.4f} x its median 5m candle range)"
            )
        return DojiThreshold(self.doji_max_body[symbol], self.doji_relative_tolerance)


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


class DojiThreshold(float):
    """Price threshold carrying its comparison tolerance through shared consumers.

    Spec: confluences.md › Swing high / low. Retains the float threshold interface.
    """

    def __new__(cls, value: float, relative_tolerance: float = DEFAULT_DOJI_RELATIVE_TOLERANCE):
        threshold = super().__new__(cls, value)
        threshold.relative_tolerance = relative_tolerance
        return threshold


class RangeShare(DojiThreshold):
    """A doji threshold that is a share of the candle's own range, not a price amount. A
    float subclass so it travels through every `doji_max_body: float` unchanged."""

    __slots__ = ()


def is_doji(candle: Candle, max_body: float) -> bool:
    """Inclusive threshold with price-relative slack (spec: confluences.md › Swing high / low)."""
    threshold = max_body
    if isinstance(max_body, RangeShare):
        threshold = max_body * (candle.high - candle.low)
    body = candle.body
    if body <= threshold:
        return True
    relative = getattr(max_body, "relative_tolerance", DEFAULT_DOJI_RELATIVE_TOLERANCE)
    return body - threshold <= relative * max(abs(candle.open), abs(candle.close))


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

    def update(self, view: SeriesView, *, ignore: bool = False) -> list[SwingPoint]:
        """Consume one closed candle; ignored candles advance order without altering swings.

        Spec: strategy-session-zones.md › Session zones (ignored weekend candles).
        The caller owns the session policy; this detector remains timeframe-agnostic.
        """
        if view.cursor != self._next:
            raise ValueError(
                f"SwingDetector.update must be called once per candle in order: "
                f"expected cursor {self._next}, got {view.cursor}"
            )
        self._next += 1
        if ignore:
            return []
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
