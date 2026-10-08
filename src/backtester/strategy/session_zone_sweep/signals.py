"""Feeds the entry-sequence setups from the 5m and 30m detectors and emits entry signals.

Spec: strategy-session-zones.md › Entry sequence, › Invalidation & reset, › Zone flips.
Per closed 5m candle (`update(now, v5, v30)`):
1. 5m detectors: structure (BOS / with-trend breaks, 5m trend), FVG, OB, BPR, ATR. An FVG
   is usable only if it points with the 5m trend after its candle 3 closed (no trend =
   not used); OBs and BPRs have no trend rule. With `use_equilibrium`: the equilibrium of
   every 5m break's move (see `equilibrium_zone`), validated like a zone.
2. Every 30m candle closed by now: session zones (`SessionZoneTracker`), then each live
   zone's setup (sweep, 30m reaction, flips). A setup that just got its 30m reaction
   looks back at the 5m breaks during that 30m candle.
3. This candle's 5m breaks advance / cancel the other setups; confluences confirmed by
   this candle trigger entries.
One setup per live zone, in the direction of the zone's role (support = long). A zone's
setup only sees 30m candles of the session the zone is active in. At most one entry per
direction per candle: if several setups trigger on the same candle, the first live zone's
signal is used and all of them restart.

Equilibrium entry (strategy-session-zones.md › Entry sequence step 4, confluences.md › Equilibrium):
the leg runs from the break's leg extreme (long: the BOS leg's low) to the move's end, the
first 5m swing high confirmed after the break candle. From that candle on, the leg's lower
half (0.5 level down to the low) is validated like a zone (zone.py): a wick below 0.5 taps
it, a green close back above 0.5 confirms it, a close below the low invalidates it. Only
the setup whose BOS made the leg may use it.

For the results file (journal.py) every `update` also leaves what it saw on this candle:
`session_zone_events` (zones formed, roles, breaks, expiries), `zone_transitions` (taps,
confirmations, invalidations of the confluences and equilibria) and `links`: each
confluence a setup at step 4 could use (open, or confirmed now and accepted), read before
a triggered setup restarts.
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
from backtester.detectors.swings import SwingKind, SwingPoint
from backtester.detectors.zone import ZoneBook, ZoneBox, ZoneKind, ZoneState, ZoneTransition
from backtester.sessions import Session, session_of
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.setup import (
    EntrySignal,
    Setup,
    Step,
    StructureBreak,
    StructureTracker,
)
from backtester.strategy.session_zone_sweep.zones import (
    Role,
    SessionZone,
    SessionZoneEvent,
    SessionZoneTracker,
    ZoneBreak,
    ZoneExpired,
    ZoneRoleSet,
)

ROLE_DIRECTION = {Role.SUPPORT: Direction.BULLISH, Role.RESISTANCE: Direction.BEARISH}
# the swing that ends a break's move (a bullish move ends at a swing high)
MOVE_END = {Direction.BULLISH: SwingKind.HIGH, Direction.BEARISH: SwingKind.LOW}


def equilibrium_zone(b: StructureBreak, end: SwingPoint) -> ZoneBox:
    """The discount half of `b`'s move (long: 0.5 level down to the leg's low), existing
    from the candle that confirmed the move's end swing `end`."""
    mid = (b.leg_extreme + end.price) / 2
    top, bottom = (mid, b.leg_extreme) if b.direction is Direction.BULLISH else (b.leg_extreme, mid)
    return ZoneBox(
        ZoneKind.EQUILIBRIUM,
        b.direction,
        top,
        bottom,
        b.leg_index,
        end.confirmed_index,
        end.confirmed_at,
    )


@dataclass
class LiveZone:
    zone: SessionZone
    role: Role | None = None
    setup: Setup | None = None  # None while the role is unknown


@dataclass(frozen=True, slots=True)
class SetupLink:
    """`confluence` is part of `zone`'s setup at the current candle. `accepted`: it was
    confirmed by this candle and the setup took it (an entry signal)."""

    zone: SessionZone
    direction: Direction
    confluence: ZoneBox
    accepted: bool


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
        self._eq_waiting: list[StructureBreak] = []  # breaks whose move hasn't ended yet
        self._eq_book = ZoneBook(doji)
        self._equilibrium: dict[tuple[int, Direction], ZoneBox] = {}  # by break, still open
        self.state = SignalState()
        self.session_zone_events: list[SessionZoneEvent] = []
        self.zone_transitions: list[ZoneTransition] = []
        self.links: list[SetupLink] = []

    def update(self, now: datetime, v5: SeriesView, v30: SeriesView | None) -> list[EntrySignal]:
        self.session_zone_events, self.zone_transitions = [], []
        breaks, confirmed = self._update_5m(v5)
        touched = self._update_zones(now, v30)
        for live in self._live.values():
            if live.setup is not None and live.setup not in touched:
                live.setup.on_breaks(breaks)
        self.state = SignalState(list(self._live.values()), self._atr.current)
        self.links = self._links(v5, confirmed)
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
                self.zone_transitions.append(e)
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
        if self.config.use_equilibrium:
            confirmed += self._update_equilibria(v5, breaks)
        return breaks, confirmed

    def _update_equilibria(self, v5: SeriesView, breaks: list[StructureBreak]) -> list[ZoneBox]:
        """Validate the open equilibria with this candle, then add those whose move ended
        with it. Returns the ones this candle confirmed."""
        transitions = self._eq_book.on_candle(v5)
        self.zone_transitions += transitions
        confirmed = [t.zone for t in transitions if t.state is ZoneState.CONFIRMED]
        still = {*self._eq_book.open_zones, *confirmed}
        self._equilibrium = {k: z for k, z in self._equilibrium.items() if z in still}
        waiting = []
        for b in self._eq_waiting:
            kind = MOVE_END[b.direction]
            end = next((s for s in self.structure.new_swings if s.kind is kind), None)
            if end is None:
                waiting.append(b)
                continue
            zone = equilibrium_zone(b, end)
            self._eq_book.add(zone)
            self._equilibrium[(b.index, b.direction)] = zone
        self._eq_waiting = waiting + breaks  # a move ends after its break candle
        return confirmed

    def equilibrium_of(self, b: StructureBreak) -> ZoneBox | None:
        """The open (or just confirmed) equilibrium of break `b`'s move."""
        return self._equilibrium.get((b.index, b.direction))

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
        events = self._zones.update(view)
        self.session_zone_events += events
        for e in events:
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

    def _links(self, v5: SeriesView, confirmed: list[ZoneBox]) -> list[SetupLink]:
        """The confluences each setup at step 4 could use at this candle."""
        out = []
        for live in self._live.values():
            setup = live.setup
            if setup is None or setup.step is not Step.CONFLUENCE or not self._trades_in(live.zone):
                continue
            own = self.equilibrium_of(setup.bos)
            open_ = [z for z in self._usable if z.direction is setup.direction]
            if own is not None and own not in confirmed:
                open_.append(own)
            for z in open_:
                if z.created_index >= setup.bos.leg_index:
                    out.append(SetupLink(live.zone, setup.direction, z, False))
            for z in confirmed:
                if setup.accepts(z, v5.cursor) and (z.kind is not ZoneKind.EQUILIBRIUM or z == own):
                    out.append(SetupLink(live.zone, setup.direction, z, True))
        return out

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
            usable = [
                z
                for z in confirmed
                if setup.accepts(z, v5.cursor)
                and (z.kind is not ZoneKind.EQUILIBRIUM or z == self.equilibrium_of(setup.bos))
            ]
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
