"""Shared drawing of zone overlays (FVG, OB, BPR, later breaker). Spec: ROADMAP.md › 2.5,
2.6, 2.8; confluences.md › Validation.

Per zone: a filled box from its first candle to the candle that confirmed or invalidated
it, or to the cursor while it is still active or tapped (no length limit). One color per
zone type, whatever the direction (FVG green, OB yellow, BPR purple, rule set by the user); invalidated
zones stay drawn, fainter. Where boxes overlap, the fills stack and the overlap is darker
(e.g. overlapping FVGs = an imbalance, rule set by the user; see `ui/plotly_render.py`).

No marker on the zone's confirming candle (user's choice) and none for a tap: hovering
over the box shows the hover text (a hover area along the middle of the box). The panel
sub-entries "↳ ★ confirmations" and "↳ ✕ invalidations" add ★ / ✕ where it was
confirmed / invalidated (drawing only: the box ends there either way).

The state is rebuilt from the transitions confirmed at or before the cursor, so replay
shows each zone as it was known then.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from backtester.detectors.base import Event
from backtester.detectors.zone import ZoneBox, ZoneState, ZoneTransition
from backtester.ui.drawing import Box, Drawing, Hover, Marker
from backtester.ui.overlays import OverlayContext

# the panel sub-entries every zone overlay has
ZONE_PARTS = (
    (ZoneState.CONFIRMED.value, "★ confirmations"),
    (ZoneState.INVALIDATED.value, "✕ invalidations"),
)
TRANSITION_SYMBOL = {ZoneState.CONFIRMED: "star", ZoneState.INVALIDATED: "x"}


@dataclass(frozen=True)
class ZoneStyle:
    name: str  # e.g. "FVG": trace names "FVG box", "FVG" (hover), "FVG state"
    color: str  # "#rrggbb"
    fill_opacity: float
    invalidated_opacity: float


def zone_history(events: Sequence[Event]) -> list[tuple[Event, list[ZoneTransition]]]:
    """Each zone event (any event with a `zone` that isn't a transition) with its
    transitions among `events`, in order."""
    transitions: dict[ZoneBox, list[ZoneTransition]] = {}
    for e in events:
        if isinstance(e, ZoneTransition):
            transitions.setdefault(e.zone, []).append(e)
    return [(e, transitions.get(e.zone, [])) for e in events if not isinstance(e, ZoneTransition)]


def state_at(history: Sequence[ZoneTransition]) -> ZoneState:
    return history[-1].state if history else ZoneState.ACTIVE


def box_end(history: Sequence[ZoneTransition], cursor: int) -> int:
    """Last candle the box is drawn over: the confirming/invalidating candle, else the
    cursor."""
    return history[-1].confirmed_index if history and history[-1].state.finished else cursor


def draw_zones(
    events: Sequence[Event],
    ctx: OverlayContext,
    style: ZoneStyle,
    hover_text: Callable[[Event, Sequence[ZoneTransition], OverlayContext], str],
) -> list[Drawing]:
    cfg = ctx.config
    history = zone_history(events)
    if not history:
        return []
    shown = {ZoneState(p) for p in ctx.parts}
    groups: dict[bool, list[Box]] = {False: [], True: []}  # by invalidated
    hovers, marks = [], []
    for event, steps in history:
        zone: ZoneBox = event.zone
        x0, x1 = zone.start_index, box_end(steps, ctx.cursor)
        invalidated = state_at(steps) is ZoneState.INVALIDATED
        groups[invalidated].append(
            Box(
                x0,
                x1,
                zone.bottom,
                zone.top,
                f"{style.name} box" + (" (invalidated)" if invalidated else ""),
                fill=style.color,
                fill_opacity=style.invalidated_opacity if invalidated else style.fill_opacity,
                edge=style.color,
                edge_opacity=0.5 if invalidated else 1.0,
            )
        )
        text = hover_text(event, steps, ctx)
        hovers.append(Hover(x0, x1, (zone.top + zone.bottom) / 2, text, style.name))
        for t in steps:
            if t.state not in shown:
                continue
            marks.append(
                Marker(
                    t.confirmed_index,
                    zone.far if t.state is ZoneState.INVALIDATED else zone.near,
                    f"{style.name} state",
                    TRANSITION_SYMBOL[t.state],
                    style.color,
                    cfg.marker_size - 2,
                    hover=(
                        f"{zone.direction.value.capitalize()} {style.name} {t.state.value}\n"
                        f"candle closed {t.confirmed_at:%Y-%m-%d %H:%M} UTC, "
                        f"close {t.close:.{ctx.digits}f}"
                    ),
                    outline=1,
                )
            )
    return [*groups[False], *groups[True], *hovers, *marks]


def steps_text(history: Sequence[ZoneTransition]) -> str:
    """'state: …' plus one line per transition, for the hover text."""
    steps = "".join(
        f"\n{t.state.value}: candle closed {t.confirmed_at:%m-%d %H:%M} UTC" for t in history
    )
    return f"state: {state_at(history).value}{steps}"
