"""What the chart page sends to the browser (Lightweight Charts, `ui/assets/chart.js`).
Spec: ROADMAP.md › 4.0a (parts 2-4), CLAUDE.md › Invariant #1. No Plotly, no Dash.

Everything is cut at a **cursor** (the latest closed candle shown; the last candle outside
replay), so the browser never gets anything that isn't known at the cursor:

- `candles(start, stop)`: candles start..stop-1 as columns (open times in UTC seconds,
  OHLC, spread). Their position on the chart is their index in the replay (x).
- `sessions(start, stop)`: session start lines on those candles, (x, color, label).
- `full(keys, cursor)`: the drawings of the overlay types `keys` at the cursor (each
  overlay's `draw` on its events confirmed by then, with every sub-entry; the browser
  shows / hides overlays and sub-entries itself), their badges and the messages.
  Drawings and badges are grouped by overlay type.
- `delta(keys, frm, to)`: from the browser's cursor `frm` to `to` (any distance, either
  direction): the new candles (or how many to drop), their session lines, the drawings
  that appeared and the ids of those that disappeared, and the badges at `to`. Applying
  it to the payload at `frm` gives the payload at `to`.

A box, line or hover area that runs to the cursor (an active zone, an open trade) is sent
with `x1` null, "live": the browser draws it to its latest candle. So a replay step only
sends the drawings that changed: a zone confirmed or invalidated by the new candle comes
back with its fixed end, a new zone is added. A drawing's id is a hash of its JSON, so the
same drawing has the same id in every payload.

Speed: an overlay's drawings are kept per group of events (`OverlayType.group`, e.g. a
zone and its transitions). One step forward only draws again the groups with an event
confirmed on the new candle and the live ones; the rest is taken from the step before.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, OrderedDict
from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass, replace
from datetime import datetime

import pandas as pd

from backtester.detectors.base import Event
from backtester.engine.replay import Replay
from backtester.ui.chart_config import DEFAULT_CONFIG, SESSION_LABELS, ChartConfig
from backtester.ui.chart_config import session_line_positions as _session_positions
from backtester.ui.drawing import Badge, Box, Drawing, Hover, Label, Line, Marker
from backtester.ui.overlays import (
    OVERLAYS,
    OverlayContext,
    OverlayType,
    OverlayUnavailable,
    visible_events,
)

LIVE = math.inf  # x1 of a drawing that runs to the cursor (sent as null)
_CACHE_SIZE = 64  # drawings per (overlay, cursor) kept for replay steps back and forth


def rgba(hex_color: str, opacity: float) -> str:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{opacity})"


def _epoch(t: datetime) -> int:
    return int(t.timestamp())


def encode(overlay: str, d: Drawing) -> dict:
    """JSON for one drawing of `overlay`, with its id. Defaults are left out."""
    if isinstance(d, Box):
        out = {"k": "b", "x0": d.x0, "x1": d.x1, "y0": d.bottom, "y1": d.top}
        if d.fill is not None:
            out["f"] = rgba(d.fill, d.fill_opacity)
        if d.edge is not None:
            out["e"] = d.edge if d.edge_opacity is None else rgba(d.edge, d.edge_opacity)
            out["ew"] = d.edge_width
            if d.edge_dash != "solid":
                out["ed"] = d.edge_dash
    elif isinstance(d, Line):
        out = {"k": "l", "x0": d.x0, "x1": d.x1, "y0": d.y0, "y1": d.y1, "c": d.color}
        out["w"] = d.width
        if d.dash != "solid":
            out["d"] = d.dash
    elif isinstance(d, Marker):
        out = {"k": "m", "x": d.x, "y": d.y, "s": d.shape, "c": d.color, "z": d.size}
        if d.outline:
            out["ow"] = d.outline
        if d.hover is not None:
            out["h"] = d.hover
    elif isinstance(d, Label):
        out = {"k": "t", "x": d.x, "y": d.y, "s": d.text, "c": d.color, "z": d.size}
        out["a"] = d.anchor
    elif isinstance(d, Hover):
        out = {"k": "h", "x0": d.x0, "x1": d.x1, "y": d.y, "s": d.text}
    else:
        raise TypeError(f"not a chart drawing: {d!r}")
    if out.get("x1") == LIVE:
        out["x1"] = None
    out["o"] = overlay
    if d.part is not None:
        out["p"] = d.part
    out["id"] = hashlib.blake2b(
        json.dumps(out, sort_keys=True, separators=(",", ":")).encode(), digest_size=6
    ).hexdigest()
    return out


def encode_badge(b: Badge) -> dict:
    return {"t": b.text, "bg": b.background, "c": b.color, "z": b.size, "r": b.row}


def _live(d: Drawing, cursor: int) -> Drawing:
    """`d` with an end at the cursor marked live."""
    return replace(d, x1=LIVE) if getattr(d, "x1", None) == cursor else d


class ChartData:
    """Payloads for one loaded chart (`replay` = the shown candles and their clocks).
    `events_for(overlay)` returns an overlay's events over the whole range (the page
    caches them per range and settings); it may raise `OverlayUnavailable`."""

    def __init__(
        self,
        replay: Replay,
        events_for: Callable[[OverlayType], Sequence[Event]],
        config: ChartConfig = DEFAULT_CONFIG,
        registry: dict[str, OverlayType] = OVERLAYS,
    ):
        self.replay = replay
        self.events_for = events_for
        self.config = config
        self.registry = registry
        self._all = list(replay.view(len(replay) - 1))  # server side only, cut per payload
        self._drawn: OrderedDict[tuple[str, int], _Drawn] = OrderedDict()
        self._indexes: dict[str, _Index | str] = {}

    def __len__(self) -> int:
        return len(self._all)

    # --- candles and session lines ------------------------------------------------------

    def candles(self, start: int, stop: int) -> dict:
        """Candles start..stop-1 as columns; x of the first one = `start`."""
        part = self._all[max(start, 0) : stop]
        return {
            "x0": max(start, 0),
            "t": [_epoch(c.ts) for c in part],
            "o": [c.open for c in part],
            "h": [c.high for c in part],
            "l": [c.low for c in part],
            "c": [c.close for c in part],
            "s": [None if c.spread is None or math.isnan(c.spread) else c.spread for c in part],
        }

    def sessions(self, start: int, stop: int) -> list[list]:
        """Session start lines (x, color, label) on candles start..stop-1. One candle before
        `start` is looked at too, so a session starting in the gap before candle `start`
        gets its line there."""
        cfg, timeframe = self.config, self.replay.timeframe
        if stop <= start or timeframe.value > cfg.session_max_timeframe.value:
            return []
        lo = max(start - 1, 0)
        ts = pd.Series(pd.to_datetime([c.ts for c in self._all[lo:stop]], utc=True))
        return [
            [int(x), cfg.session_color(s), SESSION_LABELS[s]]
            for x, s in _session_positions(ts, timeframe, lo)
            if x >= start
        ]

    # --- drawings -----------------------------------------------------------------------

    def _context(self, cursor: int) -> OverlayContext:
        r = self.replay
        return OverlayContext(r.symbol, cursor, 0, self.config, r.timeframe, r.overall_timeframe)

    def _index(self, key: str) -> _Index | str:
        """The overlay's events grouped (see `OverlayType.group`), or its message if it
        can't be drawn on this range."""
        found = self._indexes.get(key)
        if found is None:
            overlay = self.registry[key]
            try:
                events = self.events_for(overlay)
            except OverlayUnavailable as e:
                found = f"{overlay.label}: {e}"
            else:
                found = _Index(events, overlay.group)
            self._indexes[key] = found
        return found

    def _draw_groups(self, key: str, groups, index: _Index, cursor: int, out: dict, live: set):
        """Draw `groups` at `cursor` into `out` / `live` (a group with no drawing is left out)."""
        overlay = self.registry[key]
        ctx = replace(self._context(cursor), parts=frozenset(p for p, _ in overlay.parts))
        for g in groups:
            seen = [e for e in index.groups[g] if e.confirmed_index <= cursor]
            drawings = tuple(_live(d, cursor) for d in overlay.draw(seen, ctx)) if seen else ()
            out.pop(g, None)
            live.discard(g)
            if drawings:
                out[g] = drawings
                if any(getattr(d, "x1", None) == LIVE for d in drawings):
                    live.add(g)

    def drawn(self, key: str, cursor: int) -> _Drawn:
        """Overlay `key` at `cursor`: drawings per group, badges, message. From the state at
        cursor - 1 when that is cached: only groups with an event on this candle and groups
        that were live (their end or hover may move) are drawn again."""
        cached = self._drawn.get((key, cursor))
        if cached is not None:
            self._drawn.move_to_end((key, cursor))
            return cached
        index = self._index(key)
        if isinstance(index, str):
            result = _Drawn({}, set(), [], index, None)
        else:
            overlay = self.registry[key]
            prev = self._drawn.get((key, cursor - 1))
            if prev is not None:
                groups, live = dict(prev.groups), set(prev.live)
                changed = {*index.new_at.get(cursor, ()), *prev.live}
            else:
                groups, live, changed = {}, set(), None
            todo = index.groups if changed is None else changed
            self._draw_groups(key, todo, index, cursor, groups, live)
            badges = []
            if overlay.status is not None:
                badges = overlay.status(visible_events(index.events, cursor), self._context(cursor))
            result = _Drawn(groups, live, badges, None, changed)
        self._drawn[(key, cursor)] = result
        if len(self._drawn) > _CACHE_SIZE:
            self._drawn.popitem(last=False)
        return result

    def _keys(self, keys: Sequence[str]) -> list[str]:
        """`keys` that are registered, in registry (drawing) order."""
        return [k for k in self.registry if k in keys]

    def full(self, keys: Sequence[str], cursor: int) -> dict:
        """Drawings, badges and messages of overlay types `keys` at `cursor`."""
        types, badges, messages = {}, {}, []
        for key in self._keys(keys):
            state = self.drawn(key, cursor)
            types[key] = [encode(key, d) for ds in state.groups.values() for d in ds]
            badges[key] = [encode_badge(x) for x in state.badges]
            if state.message:
                messages.append(state.message)
        return {"cursor": cursor, "types": types, "badges": badges, "messages": messages}

    def delta(self, keys: Sequence[str], frm: int, to: int) -> dict:
        """From the payload at `frm` to the one at `to` (see the module docstring)."""
        keys = self._keys(keys)
        out: dict = {"from": frm, "to": to, "types": keys}
        if to > frm:
            out["candles"] = self.candles(frm + 1, to + 1)
            out["sessions"] = self.sessions(frm + 1, to + 1)
        elif to < frm:
            out["drop"] = frm - to
        added, removed, badges = [], [], {}
        for key in keys:
            before, after = self.drawn(key, frm), self.drawn(key, to)
            if to == frm + 1 and after.changed is not None:
                groups = after.changed  # one step forward: only these were drawn again
            elif to == frm - 1 and before.changed is not None:
                groups = before.changed  # one step back: the same groups in reverse
            else:
                groups = before.groups.keys() | after.groups.keys()
            old = Counter(d for g in groups for d in before.groups.get(g, ()))
            new = Counter(d for g in groups for d in after.groups.get(g, ()))
            added += [encode(key, d) for d in (new - old).elements()]
            removed += [encode(key, d)["id"] for d in (old - new).elements()]
            badges[key] = [encode_badge(x) for x in after.badges]
        out.update(add=added, remove=removed, badges=badges)
        return out


class _Index:
    """One overlay's events over the whole range, grouped for drawing."""

    def __init__(self, events: Sequence[Event], group: Callable[[Event], Hashable] | None):
        self.events = events
        self.groups: dict[Hashable, list[Event]] = {}  # in event (confirmation) order
        self.new_at: dict[int, list[Hashable]] = {}  # groups with an event confirmed there
        for i, e in enumerate(events):
            g = i if group is None else group(e)
            self.groups.setdefault(g, []).append(e)
            self.new_at.setdefault(e.confirmed_index, []).append(g)


@dataclass(frozen=True)
class _Drawn:
    """One overlay at one cursor."""

    groups: dict[Hashable, tuple[Drawing, ...]]  # drawings per group, live ends marked
    live: set[Hashable]  # groups with a drawing that runs to the cursor
    badges: list[Badge]
    message: str | None
    changed: set[Hashable] | None  # groups drawn again since cursor - 1 (None: all)
