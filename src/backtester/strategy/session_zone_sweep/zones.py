"""Session high/low zones on 30m, their role (support / resistance), breaks and flips.

Spec: strategy-session-zones.md › Session zones, › Zone flips.
- A candle belongs to the session it CLOSES in (rule set by the user): the 30m candle
  closing at the New York open is New York's first candle, not London's last.
- Per session: the single most extreme CONFIRMED swing high and low (shared swing
  detector). A swing belongs to the session of its extreme-wick candle and counts only if
  a candle of that same session confirms it: a swing confirmed by the next session's first
  candle doesn't count, but a swing whose extreme is that first candle counts for the next
  session (rule set by the user). A higher wick that is no confirmed swing is never used.
- High zone: highest wick (the swing price) to the lowest body top of its turn candles in
  that session (a turn candle of the previous session doesn't count, rule set by the
  user); low zone mirrored. No confirmed swing on one side -> no zone on that side.
- Valid only during the next session (London->NY, NY->Tokyo, Tokyo->London); Friday NY
  carries into Monday Tokyo (`friday_ny_carries_to_monday_tokyo`).
- Role from the close of the forming session's last candle (rule set by the user): zone
  below that close = support, above = resistance; the active session's first candle can
  already break it. Inside the zone: the first close outside (never a doji) sets the role
  and is no break.
- Break: a close beyond the whole zone on the far side (support: below its bottom). A wick
  never counts, nor does a doji (rule set by the user). The 1st break flips the role, the
  2nd flips it back, the `zone_kill_breaks`-th (default 3) kills the zone for the rest of
  its session. With `zone_kill` off no number of breaks kills a zone (it keeps flipping).
- Candles closing on the weekend before Tokyo's start (Sunday open) are ignored: no
  swings, no breaks, and the role of a Friday NY zone comes from Friday's last close (rule
  set by the user). The candle closing at Tokyo's start is Tokyo's first.

Described for support (the bullish case), resistance mirrored. The tracker is incremental
like a detector: `update(view)` once per closed 30m candle, in order. A session's zones are
emitted once it is known to be over: at the close of a candle after which the next candle
would close in a later session, or (after a data gap, e.g. the weekend) at the first
candle of a later session, before that candle is checked.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from backtester.core.models import Candle
from backtester.core.series import SeriesView
from backtester.detectors.base import Detector, Event
from backtester.detectors.swings import SwingDetector, SwingKind, SwingPoint, is_doji
from backtester.sessions import Session, SessionInstance, next_session_start, session_of
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig

_FRIDAY = 4


class Role(Enum):
    SUPPORT = "support"  # zone below price, used from above (the bullish case)
    RESISTANCE = "resistance"

    @property
    def sign(self) -> int:
        return 1 if self is Role.SUPPORT else -1

    @property
    def flipped(self) -> Role:
        return Role.RESISTANCE if self is Role.SUPPORT else Role.SUPPORT


@dataclass(frozen=True, slots=True)
class SessionZone(Event):
    """A session zone, emitted when the session it formed in is over. Its identity: the
    role, break and expiry events refer to it."""

    side: SwingKind  # HIGH: the session's high zone
    top: float
    bottom: float
    swing: SwingPoint
    formed_in: SessionInstance
    active_in: SessionInstance  # the only session the zone is used in
    start_index: int  # first turn candle in `formed_in` (left edge when drawn)

    def far(self, role: Role) -> float:
        """The edge a break closes beyond (support: the bottom)."""
        return self.bottom if role is Role.SUPPORT else self.top


@dataclass(frozen=True, slots=True)
class ZoneRoleSet(Event):
    """The zone's first role: at its session's start, or by the first close outside it."""

    zone: SessionZone
    role: Role
    close: float  # the close that decided it


@dataclass(frozen=True, slots=True)
class ZoneBreak(Event):
    zone: SessionZone
    number: int  # 1st, 2nd, ... break of this zone
    role: Role  # role after the flip (meaningless once killed)
    killed: bool
    close: float


@dataclass(frozen=True, slots=True)
class ZoneExpired(Event):
    """The zone's active session is over (killed zones don't expire, they're gone)."""

    zone: SessionZone
    last_index: int  # last candle of the active session (right edge when drawn)


SessionZoneEvent = SessionZone | ZoneRoleSet | ZoneBreak | ZoneExpired


@dataclass
class _Candidate:
    swing: SwingPoint
    top: float
    bottom: float
    start_index: int


@dataclass
class _Live:
    zone: SessionZone
    role: Role | None  # None: price was inside the zone, no close outside yet
    breaks: int = 0


def _sign(kind: SwingKind) -> int:
    return 1 if kind is SwingKind.HIGH else -1


def zone_edges(kind: SwingKind, price: float, turn: Sequence[Candle]) -> tuple[float, float]:
    """(top, bottom) of a zone at a swing: the extreme wick to the innermost body edge of
    the turn candles that count (high: the lowest body top)."""
    sign = _sign(kind)
    edges = [max(c.open, c.close) if sign > 0 else min(c.open, c.close) for c in turn]
    inner = sign * min(sign * e for e in edges)
    return (price, inner) if sign > 0 else (inner, price)


class SessionZoneTracker(Detector[SessionZoneEvent]):
    """Incremental: `update(view)` once per closed `zone_timeframe` candle, in order."""

    def __init__(self, doji_max_body: float, config: SessionZoneSweepConfig | None = None):
        self.config = config or SessionZoneSweepConfig()
        self.doji_max_body = doji_max_body
        self._swings = SwingDetector(doji_max_body)
        self._next = 0
        self._forming: SessionInstance | None = None
        self._best: dict[SwingKind, _Candidate] = {}
        self._live: list[_Live] = []
        self._last: tuple[int, float] | None = None  # (index, close) of last candle in a session

    @classmethod
    def for_symbol(
        cls, symbol: str, config: SessionZoneSweepConfig | None = None
    ) -> SessionZoneTracker:
        config = config or SessionZoneSweepConfig()
        return cls(config.swings.doji_threshold(symbol), config)

    def update(self, view: SeriesView) -> list[SessionZoneEvent]:
        if view.timeframe is not self.config.zone_timeframe:
            raise ValueError(
                f"session zones are built on {self.config.zone_timeframe.name}, "
                f"got {view.timeframe.name} candles"
            )
        if view.cursor != self._next:
            raise ValueError(
                f"SessionZoneTracker.update must be called once per candle in order: "
                f"expected cursor {self._next}, got {view.cursor}"
            )
        self._next += 1
        candle = view.current
        closed_at = candle.ts + view.timeframe.duration
        swings = self._swings.update(view)  # every candle, so its state stays continuous
        session = session_of(closed_at, self.config.sessions)
        if session is None:
            return []  # closes on the weekend, before Tokyo's start: ignored
        out: list[SessionZoneEvent] = []
        if self._forming is not None and session != self._forming:
            out += self._end_session(view.cursor, closed_at)  # gap: no candle reached its end
        out += self._expire(lambda z: z.active_in.end <= closed_at, view.cursor, closed_at)
        if self._forming is None:
            self._forming = session
        for swing in swings:
            self._consider(swing, session, view)
        for live in self._live:
            out += self._check(live, candle, view.cursor, closed_at)
        self._live = [live for live in self._live if not self._killed(live)]
        self._last = (view.cursor, candle.close)
        if closed_at + view.timeframe.duration >= session.end:  # the next one closes later
            out += self._end_session(view.cursor, closed_at)
        return out

    def _consider(self, swing: SwingPoint, session: SessionInstance, view: SeriesView) -> None:
        """Keep `swing` if it is the most extreme of its kind in `session` so far."""
        duration = view.timeframe.duration
        if not session.contains(swing.ts + duration):
            return  # its extreme is in the previous session, confirmed too late there
        turn = [
            i
            for i in (swing.first_index, swing.confirmed_index)
            if session.contains(view[i].ts + duration)
        ]
        top, bottom = zone_edges(swing.kind, swing.price, [view[i] for i in turn])
        best, sign = self._best.get(swing.kind), _sign(swing.kind)
        if best is None or sign * swing.price > sign * best.swing.price:
            self._best[swing.kind] = _Candidate(swing, top, bottom, turn[0])

    def _check(self, live: _Live, candle: Candle, cursor: int, closed_at: datetime):
        if is_doji(candle, self.doji_max_body):
            return []
        zone, close = live.zone, candle.close
        if live.role is None:
            if zone.bottom <= close <= zone.top:
                return []
            live.role = Role.SUPPORT if close > zone.top else Role.RESISTANCE
            return [ZoneRoleSet(cursor, closed_at, zone, live.role, close)]
        role = live.role
        if role.sign * close >= role.sign * zone.far(role):
            return []
        live.breaks += 1
        live.role = role.flipped
        killed = self._killed(live)
        return [ZoneBreak(cursor, closed_at, zone, live.breaks, live.role, killed, close)]

    def _killed(self, live: _Live) -> bool:
        return self.config.zone_kill and live.breaks >= self.config.zone_kill_breaks

    def _expire(self, done, cursor: int, closed_at: datetime) -> list[ZoneExpired]:
        expired = [live for live in self._live if done(live.zone)]
        self._live = [live for live in self._live if not done(live.zone)]
        last_index = self._last[0] if self._last else cursor
        return [ZoneExpired(cursor, closed_at, live.zone, last_index) for live in expired]

    def _end_session(self, cursor: int, closed_at: datetime) -> list[SessionZoneEvent]:
        """The forming session is over: zones active in it expire, its own zones form."""
        formed, best = self._forming, self._best
        self._forming, self._best = None, {}
        out: list[SessionZoneEvent] = list(
            self._expire(lambda z: z.active_in.end <= formed.end, cursor, closed_at)
        )
        friday_ny = formed.session is Session.NEW_YORK and formed.trading_date.weekday() == _FRIDAY
        if friday_ny and not self.config.friday_ny_carries_to_monday_tokyo:
            return out
        active_in = next_session_start(formed.start, self.config.sessions)
        close = self._last[1]  # the forming session's last close
        for side in (SwingKind.HIGH, SwingKind.LOW):
            if side not in best:
                continue  # no confirmed swing on this side -> no zone
            c = best[side]
            zone = SessionZone(
                cursor, closed_at, side, c.top, c.bottom, c.swing, formed, active_in, c.start_index
            )
            out.append(zone)
            role = None
            if close > zone.top:
                role = Role.SUPPORT
            elif close < zone.bottom:
                role = Role.RESISTANCE
            if role is not None:
                out.append(ZoneRoleSet(cursor, closed_at, zone, role, close))
            self._live.append(_Live(zone, role))
        return out
