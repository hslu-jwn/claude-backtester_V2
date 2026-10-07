"""Feeds the entry-sequence setups from the 5m and 30m detectors and emits entry signals.

Spec: strategy-session-zones.md › Entry sequence, › Invalidation & reset, › Zone flips.
Per closed 5m candle (`update(now, v5, v30)`):
1. 5m detectors: structure (BOS / with-trend breaks, 5m trend), FVG, OB, BPR, ATR. An FVG
   is usable only if it points with the 5m trend after its candle 3 closed (no trend =
   not used); OBs and BPRs have no trend rule.
2. Every 30m candle closed by now: session zones (`SessionZoneTracker`), then each live
   zone's setup (sweep, 30m reaction, flips). A setup that just got its 30m reaction
   looks back at the 5m breaks during that 30m candle.
3. This candle's 5m breaks advance / cancel the other setups; confluences confirmed by
   this candle trigger entries.
One setup per live zone, in the direction of the zone's role (support = long). A zone's
setup only sees 30m candles of the session the zone is active in. At most one entry per
direction per candle: if several setups trigger on the same candle, the first live zone's
signal is used and all of them restart.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from backtester.core.models import Direction
from backtester.core.series import SeriesView
from backtester.detectors.atr import Atr
from backtester.detectors.bpr import BalancedPriceRange, BprConfig, BprDetector
from backtester.detectors.fvg import FairValueGap, FvgDetector
from backtester.detectors.order_block import OrderBlock, OrderBlockDetector
from backtester.detectors.zone import ZoneBox, ZoneState, ZoneTransition
from backtester.sessions import Session, session_of
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.setup import (
    EntrySignal,
    Setup,
    StructureBreak,
    StructureTracker,
)
from backtester.strategy.session_zone_sweep.zones import (
    Role,
    SessionZone,
    SessionZoneTracker,
    ZoneBreak,
    ZoneExpired,
    ZoneRoleSet,
)

ROLE_DIRECTION = {Role.SUPPORT: Direction.BULLISH, Role.RESISTANCE: Direction.BEARISH}


@dataclass
class LiveZone:
    zone: SessionZone
    role: Role | None = None
    setup: Setup | None = None  # None while the role is unknown


@dataclass
class SignalState:
    """What the signal side knows at the current candle (read by SL / TP)."""

    live_zones: list[LiveZone] = field(default_factory=list)
    atr: float | None = None  # 5m ATR at the current close


class SetupTracker:
    def __init__(self, symbol: str, config: SessionZoneSweepConfig | None = None):
        self.config = config = config or SessionZoneSweepConfig()
        doji = config.swings.doji_threshold(symbol)
        self.doji_max_body = doji
        self.structure = StructureTracker(doji)
        self._fvg = FvgDetector(doji, config.fvg)
        self._ob = OrderBlockDetector(doji, config.order_block)
        self._bpr = BprDetector(doji, BprConfig(config.fvg))
        self._atr = Atr(config.strong_move.atr_period)
        self._zones = SessionZoneTracker(doji, config)
        self._zone_cursor = -1
        self._live: dict[SessionZone, LiveZone] = {}
        self._usable: set[ZoneBox] = set()  # open confluences a setup may use
        self._recent: list[StructureBreak] = []  # 5m breaks of the last 30m
        self.state = SignalState()

    def update(self, now: datetime, v5: SeriesView, v30: SeriesView | None) -> list[EntrySignal]:
        breaks, confirmed = self._update_5m(v5)
        touched = self._update_zones(now, v30)
        for live in self._live.values():
            if live.setup is not None and live.setup not in touched:
                live.setup.on_breaks(breaks)
        self.state = SignalState(list(self._live.values()), self._atr.current)
        return self._entries(v5, now, confirmed)

    def _update_5m(self, v5: SeriesView) -> tuple[list[StructureBreak], list[ZoneBox]]:
        breaks = self.structure.update(v5)
        self._atr.update(v5)
        now = v5.current.ts + v5.timeframe.duration
        horizon = now - self.config.zone_timeframe.duration
        self._recent = [b for b in self._recent if b.at > horizon] + breaks
        kinds = self.config.confluence_kinds
        confirmed = []
        for e in [*self._fvg.update(v5), *self._ob.update(v5), *self._bpr.update(v5)]:
            if isinstance(e, ZoneTransition):
                if e.state is ZoneState.CONFIRMED and e.zone in self._usable:
                    confirmed.append(e.zone)
                if e.state.finished:
                    self._usable.discard(e.zone)
            elif e.zone.kind not in kinds:
                continue
            elif isinstance(e, FairValueGap):
                if self.structure.trend is e.direction:  # trend after candle 3
                    self._usable.add(e.zone)
            elif isinstance(e, OrderBlock | BalancedPriceRange):
                self._usable.add(e.zone)
        return breaks, confirmed

    def _update_zones(self, now: datetime, v30: SeriesView | None) -> set[Setup]:
        """Process every 30m candle closed since the last call. Returns the setups that
        already saw this 5m candle's breaks (through the 30m reaction look-back)."""
        touched: set[Setup] = set()
        if v30 is None:
            return touched
        for cursor in range(self._zone_cursor + 1, v30.cursor + 1):
            view = v30.at(cursor)
            touched |= self._on_30m(view)
        self._zone_cursor = v30.cursor
        return touched

    def _on_30m(self, view: SeriesView) -> set[Setup]:
        candle = view.current
        closed_at = candle.ts + view.timeframe.duration
        flipped: set[SessionZone] = set()
        with_trend = self.config.entry_bos_with_trend
        for e in self._zones.update(view):
            if isinstance(e, SessionZone):
                self._live[e] = LiveZone(e)
            elif isinstance(e, ZoneRoleSet):
                live = self._live[e.zone]
                live.role = e.role
                live.setup = Setup(e.zone, ROLE_DIRECTION[e.role], with_trend)
            elif isinstance(e, ZoneBreak):
                if e.killed:
                    self._live.pop(e.zone, None)
                    continue
                live = self._live[e.zone]
                live.role = e.role
                live.setup = Setup(e.zone, ROLE_DIRECTION[e.role], with_trend)
                flipped.add(e.zone)
                is_reaction = candle.is_red if e.role is Role.RESISTANCE else candle.is_green
                if is_reaction:
                    live.setup.start_from_flip(candle)
            elif isinstance(e, ZoneExpired):
                self._live.pop(e.zone, None)
        touched = set()
        session = session_of(closed_at, self.config.sessions)
        for zone, live in self._live.items():
            setup = live.setup
            if setup is None or session != zone.active_in or not self._trades_in(zone):
                continue
            if zone in flipped:
                reacted = setup.reaction_open == candle.ts
            else:
                reacted = setup.on_30m(candle, closed_at, self.doji_max_body)
            if reacted:
                setup.on_breaks(b for b in self._recent if b.at <= closed_at)
                touched.add(setup)
        return touched

    def _trades_in(self, zone: SessionZone) -> bool:
        return not (self.config.skip_tokyo and zone.active_in.session is Session.TOKYO)

    def _entries(
        self, v5: SeriesView, now: datetime, confirmed: list[ZoneBox]
    ) -> list[EntrySignal]:
        if not confirmed:
            return []
        signals: dict[Direction, EntrySignal] = {}
        for live in self._live.values():
            setup = live.setup
            if setup is None or not self._trades_in(live.zone):
                continue
            usable = [z for z in confirmed if setup.accepts(z, v5.cursor)]
            if not usable:
                continue
            # several at once: the most recent one (on a tie, the one nearest the close)
            sign = 1 if setup.direction is Direction.BULLISH else -1
            confluence = max(usable, key=lambda z: (z.created_index, sign * z.near))
            signals.setdefault(
                setup.direction,
                EntrySignal(
                    setup.direction,
                    live.zone,
                    confluence,
                    setup.bos,
                    setup.reaction_open,
                    v5.cursor,
                    now,
                    v5.current.close,
                ),
            )
            setup.reset(not_before=now)
        return list(signals.values())
