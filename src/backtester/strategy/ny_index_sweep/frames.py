"""The detectors of one timeframe for strategy 2, fed with that timeframe's closed candles.

Spec: strategy-ny-indices.md › General. Per timeframe (1m, 5m, 15m, 1h, 4h New York):
structure (swings, real BoS, trend), the zones (FVG, OB first version, breaker, BPR) and,
on the timeframes TP levels come from, the untouched swing highs / lows and the zones never
tapped since they formed (› Take Profit). `update(view)` processes every candle of the
timeframe closed since the last call, in order (no lookahead: views only hold closed
candles); what happened in that call is in `breaks`, `new_zones`, `closed`.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right, insort
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.detectors.atr import Atr
from backtester.detectors.bos import BosDetector, BreakOfStructure
from backtester.detectors.bpr import BprConfig, BprDetector
from backtester.detectors.breaker import BreakerDetector
from backtester.detectors.fvg import FvgConfig, FvgDetector
from backtester.detectors.order_block import OrderBlockConfig, OrderBlockDetector
from backtester.detectors.swings import SwingDetector, SwingKind, SwingPoint
from backtester.detectors.zone import ZoneBox, ZoneTransition

NEW_YORK = ZoneInfo("America/New_York")
RECENT = timedelta(days=3)  # zones kept for "inside the BoS move" (moves are hours long)


def candle_open(tf: Timeframe, t: datetime) -> datetime:
    """Open time (UTC) of the `tf` candle containing time `t`: UTC-aligned, except 4h,
    which is New York-aligned (closes 02:00, 06:00, ... ET; data/resample.py)."""
    if tf is Timeframe.H4:
        local = t.astimezone(NEW_YORK).replace(tzinfo=None) - timedelta(hours=2)
        start = local.replace(hour=local.hour - local.hour % 4, minute=0, second=0, microsecond=0)
        return (start + timedelta(hours=2)).replace(tzinfo=NEW_YORK).astimezone(UTC)
    minutes = tf.value
    epoch_minutes = int(t.timestamp() // 60)
    return datetime.fromtimestamp((epoch_minutes - epoch_minutes % minutes) * 60, UTC)


def wick(direction: Direction, candle: Candle) -> float:
    """The wick on the side a `direction` setup sweeps / retraces into (bullish: the low)."""
    return candle.low if direction is Direction.BULLISH else candle.high


def beyond(direction: Direction, price: float, level: float) -> bool:
    """`price` is strictly past `level` against `direction` (bullish: below it)."""
    return price < level if direction is Direction.BULLISH else price > level


@dataclass(frozen=True, slots=True)
class Zone:
    """A zone with the timeframe it lives on and its first candle's open time."""

    box: ZoneBox
    tf: Timeframe
    start_ts: datetime


class Frame:
    def __init__(
        self,
        tf: Timeframe,
        doji_max_body: float,
        fvg: FvgConfig,
        ob: OrderBlockConfig,
        tp_levels: bool = False,
        atr_period: int | None = None,
    ):
        self.tf = tf
        self.structure = BosDetector(SwingDetector(doji_max_body))
        self._zone_detectors = (
            FvgDetector(doji_max_body, fvg),
            OrderBlockDetector(doji_max_body, ob),
            BreakerDetector(doji_max_body),
            BprDetector(doji_max_body, BprConfig(fvg)),
        )
        self._atr = Atr(atr_period) if atr_period else None
        self.tp_levels = tp_levels
        self.view: SeriesView | None = None
        self._cursor = -1
        self._trend_times: list[datetime] = []  # close time of each BoS
        self._trends: list[Direction] = []  # the trend from then on
        self.recent: list[Zone] = []  # zones formed in the last RECENT
        self.untapped: dict[ZoneBox, Zone] = {}  # tp_levels: never tapped since formed
        # tp_levels: swings no later wick reached, sorted by how soon a wick reaches them
        self._highs: list[tuple[float, int, SwingPoint]] = []  # (price, n, swing) ascending
        self._lows: list[tuple[float, int, SwingPoint]] = []  # (-price, n, swing) ascending
        self._n = 0
        # what the last update saw
        self.closed = False
        self.breaks: list[BreakOfStructure] = []
        self.new_zones: list[Zone] = []
        self.new_swings: list[SwingPoint] = []

    @property
    def current(self) -> Candle | None:
        """The candle that closed in the last update (None if none did)."""
        return self.view.current if self.closed else None

    def update(self, view: SeriesView | None) -> None:
        self.closed, self.breaks, self.new_zones, self.new_swings = False, [], [], []
        if view is None or view.cursor == self._cursor:
            return
        for cursor in range(self._cursor + 1, view.cursor + 1):
            self._step(view.at(cursor))
        self._cursor = view.cursor
        self.view = view
        self.closed = True
        cut = view.current.ts - RECENT
        if self.recent and self.recent[0].box.created_at < cut:
            self.recent = [z for z in self.recent if z.box.created_at >= cut]

    def _step(self, view: SeriesView) -> None:
        before = len(self.structure.swings)
        breaks = self.structure.update(view)
        swings = self.structure.swings[before:]
        candle = view.current
        closed_at = candle.ts + view.timeframe.duration
        for b in breaks:
            self._trend_times.append(closed_at)
            self._trends.append(b.direction)
        self.breaks += breaks
        self.new_swings += swings
        if self._atr is not None:
            self._atr.update(view)
        for detector in self._zone_detectors:
            for e in detector.update(view):
                if isinstance(e, ZoneTransition):
                    self.untapped.pop(e.zone, None)
                    continue
                zone = Zone(e.zone, self.tf, view[e.zone.start_index].ts)
                self.recent.append(zone)
                self.new_zones.append(zone)
                if self.tp_levels:
                    self.untapped[e.zone] = zone
        if self.tp_levels:
            del self._highs[: bisect_right(self._highs, (candle.high, float("inf")))]
            del self._lows[: bisect_right(self._lows, (-candle.low, float("inf")))]
            for sw in swings:  # reached only by later candles
                self._n += 1
                if sw.kind is SwingKind.HIGH:
                    insort(self._highs, (sw.price, self._n, sw))
                else:
                    insort(self._lows, (-sw.price, self._n, sw))

    def trend_at(self, t: datetime) -> Direction | None:
        """The trend (direction of the last BoS) from the candles closed at or before `t`."""
        i = bisect_right(self._trend_times, t)
        return self._trends[i - 1] if i else None

    def untouched(self, direction: Direction, beyond_price: float) -> list[SwingPoint]:
        """tp_levels: untouched swing highs above `beyond_price` (bullish), nearest first;
        bearish: untouched swing lows below it."""
        if direction is Direction.BULLISH:
            return [s for _, _, s in self._highs[bisect_left(self._highs, (beyond_price, 0)) :]]
        return [s for _, _, s in self._lows[bisect_left(self._lows, (-beyond_price, 0)) :]]

    def last_swings(self, kind: SwingKind, n: int, confirmed_by: datetime) -> list[SwingPoint]:
        """The last `n` swings of `kind` confirmed by candles closed at or before
        `confirmed_by`."""
        out = []
        for s in reversed(self.structure.swings):
            if s.kind is not kind or s.confirmed_at > confirmed_by:
                continue
            out.append(s)
            if len(out) == n:
                break
        return out

    def atr(self) -> float | None:
        return self._atr.at(self._cursor) if self._atr is not None and self._cursor >= 0 else None

    def index_at(self, t: datetime) -> int:
        """Index of the candle containing time `t` (the last one opening at or before it)."""
        view = self.view
        i = view.cursor
        while i > 0 and view[i].ts > t:
            i -= 1
        return i

    def invalidated(self, zone: Zone, until: datetime | None = None) -> bool:
        """A candle of the zone's timeframe after the one that formed it closed beyond its
        far edge (zone.py: a close below a bullish zone's bottom), up to `until`."""
        view, box = self.view, zone.box
        far, direction = box.far, box.direction
        for i in range(box.created_index + 1, view.cursor + 1):
            candle = view[i]
            if until is not None and candle.ts + self.tf.duration > until:
                break
            if beyond(direction, candle.close, far):
                return True
        return False
