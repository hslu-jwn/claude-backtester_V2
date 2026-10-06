"""Trading session clock: Tokyo, London, New York.

Spec: strategy-session-zones.md › Sessions.
- Each session starts at a fixed local time in its own city: Tokyo 09:00 Asia/Tokyo,
  London 08:00 Europe/London, New York 08:00 America/New_York. In New York time that is
  Tokyo 20:00 (19:00 in US winter, Japan has no DST), London 03:00 (04:00 in the weeks when
  US and European DST dates differ), New York 08:00.
- Sessions run Monday to Friday by their own city's date, so Monday's Tokyo session starts
  on Sunday evening in New York.
- A session ends when the next one starts (Friday New York ends at Monday Tokyo).
- A candle belongs to the session it CLOSES in (rule set by the user): pass its close
  time to `session_of`. The 30m candle closing at the New York open is New York's first.
- Times on the weekend before Tokyo's start are in no session: `session_of` returns None
  (candles closing there, i.e. the Sunday open, are ignored).
All inputs and outputs are UTC datetimes; conversion uses zoneinfo, never fixed offsets.
Holidays are not handled here: a session on a closed day simply has no candles.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import Enum
from zoneinfo import ZoneInfo


class Session(Enum):
    TOKYO = "tokyo"
    LONDON = "london"
    NEW_YORK = "new_york"


@dataclass(frozen=True)
class SessionStart:
    local_time: time
    zone: str  # IANA zone of the session's city


@dataclass(frozen=True)
class SessionConfig:
    tokyo: SessionStart = SessionStart(time(9, 0), "Asia/Tokyo")
    london: SessionStart = SessionStart(time(8, 0), "Europe/London")
    new_york: SessionStart = SessionStart(time(8, 0), "America/New_York")
    weekend_zone: str = "America/New_York"  # whose Saturday/Sunday counts as the weekend

    def start(self, session: Session) -> SessionStart:
        return getattr(self, session.value)


DEFAULT_SESSIONS = SessionConfig()
_TRADING_WEEKDAYS = range(5)  # Monday..Friday in the session's own city
_FRIDAY = 4


@dataclass(frozen=True)
class SessionInstance:
    """One session on one day. `start`/`end` are UTC; `trading_date` is the local date in
    the session's own city (Monday's Tokyo session has trading_date Monday)."""

    session: Session
    trading_date: date
    start: datetime
    end: datetime

    def contains(self, ts: datetime) -> bool:
        return self.start <= ts < self.end


def _starts_on(d: date, config: SessionConfig) -> list[tuple[datetime, Session, date]]:
    if d.weekday() not in _TRADING_WEEKDAYS:
        return []
    return [(_utc(d, config.start(session)), session, d) for session in Session]


def _utc(d: date, start: SessionStart) -> datetime:
    return datetime.combine(d, start.local_time, ZoneInfo(start.zone)).astimezone(UTC)


def session_starts(
    start: datetime, end: datetime, config: SessionConfig = DEFAULT_SESSIONS
) -> list[SessionInstance]:
    """All sessions starting in [start, end) (UTC), oldest first, each with its end."""
    _check_utc(start)
    _check_utc(end)
    # Local dates differ from UTC dates by less than a day; a weekend plus padding covers
    # the start of the session that ends the last one in range.
    first, last = start.date() - timedelta(days=1), end.date() + timedelta(days=4)
    raw = sorted(
        s
        for i in range((last - first).days + 1)
        for s in _starts_on(first + timedelta(days=i), config)
    )
    return [
        SessionInstance(session, d, ts, raw[i + 1][0])
        for i, (ts, session, d) in enumerate(raw[:-1])
        if start <= ts < end
    ]


def session_of(ts: datetime, config: SessionConfig = DEFAULT_SESSIONS) -> SessionInstance | None:
    """The session running at `ts` (UTC), or None on the weekend before Tokyo's start. A
    candle belongs to the session of its CLOSE time."""
    _check_utc(ts)
    candidates = session_starts(ts - timedelta(days=4), ts + timedelta(seconds=1), config)
    if not candidates:
        return None
    current = candidates[-1]
    weekend_date = ts.astimezone(ZoneInfo(config.weekend_zone)).date()
    if current.trading_date.weekday() == _FRIDAY and weekend_date > current.trading_date:
        return None  # past Friday in New York: weekend / Sunday open before Tokyo
    return current


def next_session_start(ts: datetime, config: SessionConfig = DEFAULT_SESSIONS) -> SessionInstance:
    """The first session starting strictly after `ts` (UTC)."""
    _check_utc(ts)
    return session_starts(ts + timedelta(microseconds=1), ts + timedelta(days=4), config)[0]


def _check_utc(ts: datetime) -> None:
    if ts.tzinfo is None or ts.utcoffset() != timedelta(0):
        raise ValueError(f"expected a UTC datetime, got {ts!r}")
