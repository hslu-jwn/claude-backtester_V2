"""Scoped detector sharing for one symbol/timeframe's closed views.

Spec: confluences.md > Swings, BOS, Strong-move filter, FVG, OB, Breaker, BPR.
Only the most recently processed view is cached. Consumers keep their own zone books
and their original event order; standalone detectors retain strict once-per-candle calls.
"""

from backtester.core.series import SeriesView
from backtester.detectors.atr import Atr, StrongMoveConfig, StrongMoveFilter
from backtester.detectors.bos import BosDetector
from backtester.detectors.bpr import BprConfig, BprDetector
from backtester.detectors.breaker import BreakerDetector
from backtester.detectors.fvg import FvgConfig, FvgDetector
from backtester.detectors.order_block import OrderBlockConfig, OrderBlockDetector
from backtester.detectors.swings import SwingDetector


class _SharedUpdate:
    _last_view: SeriesView | None = None

    def update(self, view: SeriesView):
        previous = self._last_view
        if previous is not None and previous.cursor == view.cursor:
            if (
                previous.symbol != view.symbol
                or previous.timeframe is not view.timeframe
                or previous.current is not view.current
            ):
                raise ValueError("shared detectors require the same closed candle view")
            return self._last_events
        events = super().update(view)
        self._last_view, self._last_events = view, events
        return events


class _SharedAtr(_SharedUpdate, Atr):
    pass


class _SharedFilter(_SharedUpdate, StrongMoveFilter):
    pass


class _SharedSwings(_SharedUpdate, SwingDetector):
    pass


class _SharedBos(_SharedUpdate, BosDetector):
    pass


class _SharedFvg(_SharedUpdate, FvgDetector):
    pass


class DetectorPool:
    """One pool per timeframe feed; unequal ATR/filter configurations stay separate."""

    def __init__(self, doji_max_body: float):
        self.doji_max_body = doji_max_body
        self.swings = _SharedSwings(doji_max_body)
        self.bos = _SharedBos(self.swings)
        self._atrs: dict[int, Atr] = {}
        self._filters: dict[StrongMoveConfig, StrongMoveFilter] = {}
        self._fvgs: dict[FvgConfig, FvgDetector] = {}

    def atr(self, period: int) -> Atr:
        if period not in self._atrs:
            self._atrs[period] = _SharedAtr(period)
        return self._atrs[period]

    def strong_move(self, config: StrongMoveConfig) -> StrongMoveFilter:
        if config not in self._filters:
            self._filters[config] = _SharedFilter(config, atr=self.atr(config.atr_period))
        return self._filters[config]

    def fvg(self, config: FvgConfig) -> FvgDetector:
        if config not in self._fvgs:
            self._fvgs[config] = _SharedFvg(
                self.doji_max_body, config, strong_move=self.strong_move(config.strong_move)
            )
        return self._fvgs[config]

    def order_block(self, config: OrderBlockConfig) -> OrderBlockDetector:
        return OrderBlockDetector(
            self.doji_max_body,
            config,
            bos=self.bos,
            strong_move=self.strong_move(config.strong_move),
        )

    def breaker(self) -> BreakerDetector:
        return BreakerDetector(self.doji_max_body, bos=self.bos)

    def bpr(self, config: BprConfig) -> BprDetector:
        return BprDetector(self.doji_max_body, config, fvg=self.fvg(config.fvg))
