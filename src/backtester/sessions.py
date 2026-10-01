"""Trading session clock: Tokyo, London, New York.

Spec: strategy-session-zones.md › Sessions.
- Starts given in New York time (ET): New York 08:00, London 03:00, Tokyo 20:00.
  Each session follows its own city's DST (America/New_York, Europe/London, Asia/Tokyo),
  so start times in ET shift during the weeks when DST dates differ.
- A session ends when the next one starts.
- Candles before a session start belong to the previous session.
- Sunday-open candles before Tokyo's start are ignored (form no zones).
All inputs and outputs are UTC datetimes; conversion uses zoneinfo, never fixed offsets.

TODO: implement `session_of(ts) -> SessionInstance | None` and `next_session_start(ts)`.
Test DST transition weeks explicitly (March and October/November).
"""

from __future__ import annotations

from enum import Enum


class Session(Enum):
    TOKYO = "tokyo"
    LONDON = "london"
    NEW_YORK = "new_york"
