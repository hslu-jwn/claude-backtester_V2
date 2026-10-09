"""Per-session record of strategy 1 for the results file and the session view.

Spec: ROADMAP.md › 3.4, strategy-session-zones.md › Session inspection view. Per session
(the session a zone is active in, `SessionZone.active_in`):

- **Session zones** active in it (formed in the previous session): box, where they formed
  (open time of their first 30m turn candle), their first role and when it was set, every
  break (flip / kill) and when they ended (`expired` at the session's end, `killed`, or
  `run_end` if the data stopped first).
- **Setup confluences**: every FVG / OB / BPR / equilibrium that was part of a setup in
  that session, i.e. one a setup at step 4 (after its BOS) could have used, also when the
  setup never triggered or was cancelled (`SetupLink`, signals.py). Drawn from the candle
  it formed (`start_time`, open time of its first 5m candle) to `end_time`: when it was
  confirmed (`confirmed`), invalidated (`invalidated`) or the session ended
  (`session_end`); `run_end` if the data stopped first. `setup_confirmed`: a setup took
  its confirmation (an entry signal); `traded`: that signal became an order.

No lookahead: everything is recorded at the close of the candle that caused it, from the
views the strategy got; nothing is revised later except the end of a record that was
still open. A session's record is final once the session is over.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from backtester.core.models import Direction
from backtester.core.series import SeriesView
from backtester.detectors.zone import ZoneBox, ZoneState, ZoneTransition
from backtester.sessions import SessionInstance
from backtester.strategy.session_zone_sweep.signals import SetupLink
from backtester.strategy.session_zone_sweep.zones import (
    SessionZone,
    SessionZoneEvent,
    ZoneBreak,
    ZoneExpired,
    ZoneRoleSet,
)


@dataclass
class ZoneRecord:
    zone: SessionZone
    start_time: datetime  # open time of the zone's first 30m turn candle
    role: str | None = None  # first role
    role_set_at: datetime | None = None
    breaks: list[dict] = field(default_factory=list)
    end_time: datetime | None = None
    end: str | None = None  # expired / killed / run_end


@dataclass
class ConfluenceRecord:
    box: ZoneBox
    start_time: datetime  # open time of the zone's first 5m candle
    linked_at: datetime  # first candle a setup could use it
    setup_zones: set[str] = field(default_factory=set)  # sides of the zones whose setup it was in
    setup_confirmed: bool = False
    traded: bool = False
    end_time: datetime | None = None
    end: str | None = None  # confirmed / invalidated / session_end / run_end


class SessionJournal:
    def __init__(self):
        self._zones: dict[SessionZone, ZoneRecord] = {}
        self._confluences: dict[tuple[SessionInstance, ZoneBox], ConfluenceRecord] = {}
        # the records not ended yet (an end is final), so a candle only looks at those and
        # the time per candle doesn't grow with the history (ROADMAP 6.3 speed)
        self._open: dict[tuple[SessionInstance, ZoneBox], ConfluenceRecord] = {}
        self._sessions: set[SessionInstance] = set()

    def on_candle(
        self,
        now: datetime,
        v5: SeriesView,
        v30: SeriesView | None,
        zone_events: list[SessionZoneEvent],
        transitions: list[ZoneTransition],
        links: list[SetupLink],
    ) -> None:
        """Record what the setup side saw at the close of 5m candle `v5.current` (`now`)."""
        for e in zone_events:
            self._on_zone_event(e, v30)
        for link in links:
            self._on_link(link, now, v5)
        for t in transitions:
            if t.state.finished:
                self._finish(t)
        for key, record in list(self._open.items()):
            if key[0].end <= now:
                record.end_time, record.end = key[0].end, "session_end"
                del self._open[key]

    def on_signal(self, session: SessionInstance, confluence: ZoneBox, traded: bool) -> None:
        """A setup of `session` triggered on `confluence`; `traded`: it became an order."""
        record = self._confluences.get((session, confluence))
        if record is not None:
            record.traded = record.traded or traded

    def _on_zone_event(self, e: SessionZoneEvent, v30: SeriesView | None) -> None:
        if isinstance(e, SessionZone):
            self._sessions.add(e.active_in)
            self._zones[e] = ZoneRecord(e, v30[e.start_index].ts)
            return
        record = self._zones[e.zone]
        if isinstance(e, ZoneRoleSet):
            record.role, record.role_set_at = e.role.value, e.confirmed_at
        elif isinstance(e, ZoneBreak):
            record.breaks.append(
                {
                    "time": e.confirmed_at,
                    "number": e.number,
                    "role": None if e.killed else e.role.value,
                    "killed": e.killed,
                }
            )
            if e.killed:
                record.end_time, record.end = e.confirmed_at, "killed"
        elif isinstance(e, ZoneExpired) and record.end is None:
            record.end_time, record.end = e.zone.active_in.end, "expired"

    def _on_link(self, link: SetupLink, now: datetime, v5: SeriesView) -> None:
        session = link.zone.active_in
        key = (session, link.confluence)
        record = self._confluences.get(key)
        if record is None:
            box = link.confluence
            record = self._confluences[key] = ConfluenceRecord(box, v5[box.start_index].ts, now)
            self._open[key] = record
        record.setup_zones.add(link.zone.side.value)
        if link.accepted:
            record.setup_confirmed = True

    def _finish(self, t: ZoneTransition) -> None:
        end = "confirmed" if t.state is ZoneState.CONFIRMED else "invalidated"
        for key, record in list(self._open.items()):
            if key[1] == t.zone:
                record.end_time, record.end = t.confirmed_at, end
                del self._open[key]

    def records(self, run_end: datetime | None = None) -> list[dict]:
        """One JSON-ready dict per session that had zones, oldest first. Records still open
        end at `run_end` (`run_end` reason)."""
        out = []
        for session in sorted(self._sessions, key=lambda s: s.start):
            zones = [r for r in self._zones.values() if r.zone.active_in == session]
            confluences = [r for (s, _), r in self._confluences.items() if s == session]
            out.append(
                {
                    "session": session.session.value,
                    "trading_date": session.trading_date.isoformat(),
                    "start": _iso(session.start),
                    "end": _iso(session.end),
                    "zones": [_zone_dict(r, run_end) for r in zones],
                    "confluences": [
                        _confluence_dict(r, run_end) for r in sorted(confluences, key=_record_order)
                    ],
                }
            )
        return out


def _record_order(r: ConfluenceRecord) -> tuple:
    """Confluences by creation, then linking; ties (e.g. an FVG and a BPR from the same
    candle) by kind and edges, so the file is the same on every run (the setups collect
    them in sets, whose order changes between Python processes)."""
    box = r.box
    return (box.created_at, r.linked_at, box.kind.value, box.start_index, box.bottom, box.top)


def _iso(t: datetime | None) -> str | None:
    return None if t is None else t.isoformat()


def _zone_dict(r: ZoneRecord, run_end: datetime | None) -> dict:
    z = r.zone
    ended = r.end is not None
    return {
        "side": z.side.value,
        "top": z.top,
        "bottom": z.bottom,
        "start_time": _iso(r.start_time),
        "formed_in": z.formed_in.session.value,
        "formed_trading_date": z.formed_in.trading_date.isoformat(),
        "swing_time": _iso(z.swing.ts),
        "swing_price": z.swing.price,
        "role": r.role,
        "role_set_at": _iso(r.role_set_at),
        "breaks": [{**b, "time": _iso(b["time"])} for b in r.breaks],
        "end_time": _iso(r.end_time if ended else run_end),
        "end": r.end if ended else "run_end",
    }


def _confluence_dict(r: ConfluenceRecord, run_end: datetime | None) -> dict:
    b = r.box
    ended = r.end is not None
    return {
        "kind": b.kind.value,
        "direction": "long" if b.direction is Direction.BULLISH else "short",
        "top": b.top,
        "bottom": b.bottom,
        "start_time": _iso(r.start_time),
        "created_at": _iso(b.created_at),
        "linked_at": _iso(r.linked_at),
        "setup_zones": sorted(r.setup_zones),
        "setup_confirmed": r.setup_confirmed,
        "traded": r.traded,
        "end_time": _iso(r.end_time if ended else run_end),
        "end": r.end if ended else "run_end",
    }
