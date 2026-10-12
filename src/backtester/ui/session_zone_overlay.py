"""Session zone overlay (strategy 1). Spec: ROADMAP.md › 2.9, 2.10,
strategy-session-zones.md › Session zones on the chart (provisional, for testing).

Drawn always while the overlay is on: a box with a dotted edge from the swing's first turn
candle to the end of the session the zone is active in, ending at the candle that kills it
(3rd break), or at the cursor while that session is still running. Only the part in the
session where the zone is used is filled; the part in the session it formed in is an
outline (rule set by the user). Color = the session the zone is ACTIVE in (Tokyo yellow,
London blue, New York red, like the session lines), so a London zone used in New York is
red. Flips are not marked; hovering over the box shows the zone, its sessions, the role at
the cursor and its breaks.

The zones are built on 30m candles and shown on the 30m chart and below, down to
`ChartConfig.session_zone_min_timeframe` (5m). On a lower chart the tracker reads 30m
candles only through the replay's clock (`Replay.higher_view`): a 30m candle counts from
the close of the chart candle that ends with it, never earlier. A zone appears once the
session it formed in is over (the strategy only knows it then).

Every candle belongs to the session it closes in, on its own timeframe (rule set by the
user): the fill starts with the chart candle that closes at the session start (30m: the
12:30 candle for a 13:00 open; 5m: the 12:55 one; 5m candles closing before 13:00 are
still London's) and the box ends with the last chart candle closing before the session's
end.
"""

from __future__ import annotations

from bisect import bisect_left
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from backtester.core.series import SeriesView
from backtester.detectors.base import Event
from backtester.engine.replay import Replay
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.zones import (
    SessionZone,
    SessionZoneEvent,
    SessionZoneTracker,
    ZoneBreak,
    ZoneExpired,
    ZoneRoleSet,
)
from backtester.ui.chart_config import DEFAULT_CONFIG, SESSION_LABELS
from backtester.ui.drawing import Box, Drawing, Hover
from backtester.ui.overlays import (
    DEFAULT_SETTINGS,
    OverlayContext,
    OverlaySettings,
    OverlayType,
    OverlayUnavailable,
    register,
)


@dataclass(frozen=True, slots=True)
class ChartZoneEvent(Event):
    """A tracker event placed on the shown chart: `confirmed_index` is the chart candle at
    whose close it is known; `x` the chart candle where it draws (SessionZone: the box's
    first candle, or with `activates` the first candle of the session it is used in, where
    the fill starts; a kill or expiry: its last candle)."""

    event: SessionZoneEvent
    x: int
    activates: bool = False

    @property
    def zone(self) -> SessionZone:
        e = self.event
        return e if isinstance(e, SessionZone) else e.zone


def detect_session_zones(
    replay: Replay, settings: OverlaySettings = DEFAULT_SETTINGS, config=DEFAULT_CONFIG
) -> list[ChartZoneEvent]:
    strategy = SessionZoneSweepConfig()
    zone_tf, shown = strategy.zone_timeframe, replay.timeframe
    if not config.session_zone_min_timeframe.value <= shown.value <= zone_tf.value:
        raise OverlayUnavailable(
            f"built on {zone_tf.name} candles, shown on {config.session_zone_min_timeframe.name}"
            f" to {zone_tf.name} charts"
        )
    try:
        tracker = SessionZoneTracker.for_symbol(replay.symbol, strategy, settings.swing_config)
    except KeyError as e:
        raise OverlayUnavailable(e.args[0]) from e

    def zone_view(cursor: int) -> SeriesView | None:
        if shown is zone_tf:
            return replay.view(cursor)
        try:
            return replay.higher_view(cursor, zone_tf)
        except KeyError as e:
            raise OverlayUnavailable(f"no {zone_tf.name} candles for this range") from e

    chart_ts: list[datetime] = []  # open times of the chart candles closed so far
    out: list[ChartZoneEvent] = []
    expiring: list[ZoneExpired] = []  # active session over on 30m, maybe not on the chart
    waiting: list[SessionZone] = []  # formed, their active session not started on the chart
    fed = -1  # last zone-timeframe candle given to the tracker
    for cursor in range(len(replay)):
        chart_ts.append(replay.view(cursor).current.ts)
        now = replay.close_time(cursor)
        view = zone_view(cursor)
        if view is not None:
            for i in range(fed + 1, view.cursor + 1):
                for e in tracker.update(view.at(i)):
                    if isinstance(e, ZoneExpired):
                        expiring.append(e)
                        continue
                    if isinstance(e, SessionZone):
                        waiting.append(e)
                    out.append(_place(e, cursor, now, view, chart_ts))
            fed = view.cursor
        for z in [z for z in waiting if now >= z.active_in.start]:
            out.append(ChartZoneEvent(cursor, now, z, cursor, activates=True))  # closes in it
            waiting.remove(z)
        for e in list(expiring):
            end = e.zone.active_in.end
            if now >= end:  # after a gap: this candle is already in a later session
                out.append(ChartZoneEvent(cursor, now, e, cursor - 1))
            elif now + shown.duration >= end:  # the session's last chart candle
                out.append(ChartZoneEvent(cursor, now, e, cursor))
            else:
                continue
            expiring.remove(e)
    return out


def _place(
    e: SessionZoneEvent, cursor: int, now: datetime, view: SeriesView, chart_ts: list[datetime]
) -> ChartZoneEvent:
    """`e` on the chart, from the chart candles up to `cursor` only."""

    def first_from(ts: datetime) -> int:  # first chart candle opening at or after ts
        return bisect_left(chart_ts, ts)

    def last_in(index: int) -> int:  # last chart candle within zone-timeframe candle `index`
        return first_from(view[index].ts + view.timeframe.duration) - 1

    if isinstance(e, SessionZone):
        return ChartZoneEvent(cursor, now, e, first_from(view[e.start_index].ts))
    if isinstance(e, ZoneBreak):
        return ChartZoneEvent(cursor, now, e, last_in(e.confirmed_index))
    return ChartZoneEvent(cursor, now, e, cursor)


def zone_steps(events: Sequence[ChartZoneEvent]) -> list[tuple[ChartZoneEvent, list]]:
    """Each zone with its later events (fill start, role, breaks, expiry) among `events`,
    in order."""

    def formed(e: ChartZoneEvent) -> bool:
        return isinstance(e.event, SessionZone) and not e.activates

    steps: dict[SessionZone, list[ChartZoneEvent]] = {}
    for e in events:
        if not formed(e):
            steps.setdefault(e.zone, []).append(e)
    return [(z, steps.get(z.zone, [])) for z in events if formed(z)]


def box_end(steps: Sequence[ChartZoneEvent], cursor: int) -> int:
    """The killing candle, else the active session's last candle, else the cursor."""
    for e in steps:
        if isinstance(e.event, ZoneBreak) and e.event.killed or isinstance(e.event, ZoneExpired):
            return e.x
    return cursor


def _session(instance) -> str:
    return f"{SESSION_LABELS[instance.session]} {instance.trading_date:%a %m-%d}"


def hover_text(zone: SessionZone, steps: Sequence[ChartZoneEvent], ctx: OverlayContext) -> str:
    digits, swing = ctx.digits, zone.swing
    size = zone.top - zone.bottom
    lines = [
        (
            f"{_session(zone.active_in)} session zone ({zone.side.value}) "
            f"{zone.bottom:.{digits}f} – {zone.top:.{digits}f} (size {size:.{digits}f})"
        ),
        (
            f"formed in {_session(zone.formed_in)}: swing {swing.kind.value} "
            f"{swing.price:.{digits}f} (confirmed {swing.confirmed_at:%Y-%m-%d %H:%M} UTC)"
        ),
        f"exists from: 30m candle closed {zone.confirmed_at:%Y-%m-%d %H:%M} UTC",
    ]
    role = "not set yet (price inside the zone)"
    for step in steps:
        e = step.event
        when = f"30m candle closed {e.confirmed_at:%m-%d %H:%M} UTC"
        if isinstance(e, ZoneRoleSet):
            role = e.role.value
            lines.append(f"{e.role.value}: {when}, close {e.close:.{digits}f}")
        elif isinstance(e, ZoneBreak):
            role = "killed" if e.killed else e.role.value
            after = "killed" if e.killed else f"now {e.role.value}"
            lines.append(f"break {e.number}: {when}, close {e.close:.{digits}f}, {after}")
        elif isinstance(e, ZoneExpired):
            role = f"expired ({role})"
            lines.append(f"expired: end of {_session(zone.active_in)}")
    lines.insert(3, f"role: {role}")
    return "\n".join(lines)


def draw_session_zones(events: Sequence[ChartZoneEvent], ctx: OverlayContext) -> list[Drawing]:
    cfg = ctx.config
    outlines: dict[str, list[Box]] = {}  # by color: the whole box
    fills: dict[str, list[Box]] = {}  # by color: the part in the session it is used in
    hovers = []
    for placed, steps in zone_steps(events):
        zone = placed.zone
        x0, x1 = placed.x, box_end(steps, ctx.cursor)
        color = cfg.session_color(zone.active_in.session)
        outlines.setdefault(color, []).append(
            Box(
                x0,
                x1,
                zone.bottom,
                zone.top,
                "Session zone box",
                edge=color,
                edge_dash=cfg.session_zone_line_dash,
            )
        )
        active_x = next((s.x for s in steps if s.activates), None)
        if active_x is not None and active_x <= x1:
            fills.setdefault(color, []).append(
                Box(
                    active_x,
                    x1,
                    zone.bottom,
                    zone.top,
                    "Session zone fill",
                    fill=color,
                    fill_opacity=cfg.session_zone_fill_opacity,
                )
            )
        middle = (zone.top + zone.bottom) / 2
        hovers.append(Hover(x0, x1, middle, hover_text(zone, steps, ctx), "Session zone"))
    return [
        *(b for boxes in fills.values() for b in boxes),
        *(b for boxes in outlines.values() for b in boxes),
        *hovers,
    ]


SESSION_ZONES = register(
    OverlayType(
        "session_zones",
        "Session zones",
        detect_session_zones,
        draw_session_zones,
        order="2.9",
        group=lambda e: e.zone,  # a zone with its later events
    )
)
