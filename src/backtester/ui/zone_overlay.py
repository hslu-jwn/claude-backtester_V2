"""Shared drawing of zone overlays (FVG, OB, later breaker and BPR). Spec: ROADMAP.md › 2.5,
2.6; confluences.md › Validation.

Per zone: a filled box from its first candle to the candle that confirmed or invalidated
it, or to the cursor while it is still active or tapped (no length limit). One color per
zone type, whatever the direction (FVG green, OB yellow, rule set by the user); invalidated
zones stay drawn, fainter. Where boxes overlap, the fills stack and the overlap is darker
(e.g. overlapping FVGs = an imbalance, rule set by the user). Plotly fills all boxes of one
trace as one shape, so overlapping boxes would NOT stack inside a trace: boxes are spread
over as few traces ("lanes") as needed so that no two boxes of one trace overlap.

No marker on the zone's confirming candle (user's choice) and none for a tap: hovering
over the box shows the hover text, from invisible points along the middle of the box, one
every `ChartConfig.zone_hover_step` candles over the first and last `zone_hover_ends`
candles (where it formed and where price is now; the middle of a very long box has none,
which keeps the figure small). The panel sub-entries "↳ ★ confirmations" and
"↳ ✕ invalidations" add ★ / ✕ where it was confirmed / invalidated (drawing only: the box
ends there either way).

The state is rebuilt from the transitions confirmed at or before the cursor, so replay
shows each zone as it was known then.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import plotly.graph_objects as go

from backtester.detectors.base import Event
from backtester.detectors.zone import ZoneBox, ZoneState, ZoneTransition
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


def hover_xs(x0: int, x1: int, step: int, ends: int) -> list[int]:
    """Candles of a box from x0 to x1 that get a hover point: every `step` candles within
    `ends` candles of either end, and x1."""
    xs = {x for x in range(x0, x1 + 1, step) if x - x0 < ends or x1 - x < ends}
    return sorted({*xs, x1})


Box = tuple[float, float, float, float]  # x0, x1, bottom, top


def _overlap(a: Box, b: Box) -> bool:
    return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]


def stack_lanes(boxes: Sequence[Box]) -> list[int]:
    """A lane per box such that no two boxes of one lane overlap (greedy, by start)."""
    lanes: list[list[Box]] = []  # boxes per lane that may still overlap later ones
    out = [0] * len(boxes)
    for i in sorted(range(len(boxes)), key=lambda i: boxes[i][0]):
        box = boxes[i]
        for lane, active in enumerate(lanes):
            active[:] = [b for b in active if b[1] > box[0]]
            if not any(_overlap(box, b) for b in active):
                break
        else:
            lanes.append([])
            lane = len(lanes) - 1
        lanes[lane].append(box)
        out[i] = lane
    return out


def rgba(hex_color: str, opacity: float) -> str:
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{opacity})"


def draw_zones(
    events: Sequence[Event],
    ctx: OverlayContext,
    style: ZoneStyle,
    hover_text: Callable[[Event, Sequence[ZoneTransition], OverlayContext], str],
) -> list[go.Scatter]:
    cfg = ctx.config
    history = zone_history(events)
    if not history:
        return []
    shown = {ZoneState(p) for p in ctx.parts}
    groups: dict[bool, list[Box]] = {False: [], True: []}  # by invalidated
    hover_x, hover_y, hover_text_ = [], [], []
    marks_x, marks_y, marks_symbol, marks_text = [], [], [], []
    for event, steps in history:
        zone: ZoneBox = event.zone
        x0, x1 = zone.start_index, box_end(steps, ctx.cursor)
        groups[state_at(steps) is ZoneState.INVALIDATED].append((x0, x1, zone.bottom, zone.top))
        text = hover_text(event, steps, ctx)
        hx = hover_xs(x0, x1, cfg.zone_hover_step, cfg.zone_hover_ends)
        hover_x += hx
        hover_y += [(zone.top + zone.bottom) / 2] * len(hx)
        hover_text_ += [text] * len(hx)
        for t in steps:
            if t.state not in shown:
                continue
            marks_x.append(t.confirmed_index)
            marks_y.append(zone.far if t.state is ZoneState.INVALIDATED else zone.near)
            marks_symbol.append(TRANSITION_SYMBOL[t.state])
            marks_text.append(
                f"{zone.direction.value.capitalize()} {style.name} {t.state.value}<br>"
                f"candle closed {t.confirmed_at:%Y-%m-%d %H:%M} UTC, close {t.close:.{ctx.digits}f}"
            )
    traces = []
    for invalidated, boxes in groups.items():
        lanes = stack_lanes(boxes)
        for lane in range(max(lanes, default=-1) + 1):
            xs, ys = [], []
            for (x0, x1, bottom, top), box_lane in zip(boxes, lanes, strict=True):
                if box_lane == lane:
                    xs += [x0, x1, x1, x0, x0, None]
                    ys += [bottom, bottom, top, top, bottom, None]
            traces.append(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="lines",
                    fill="toself",
                    fillcolor=rgba(
                        style.color,
                        style.invalidated_opacity if invalidated else style.fill_opacity,
                    ),
                    line={"color": rgba(style.color, 0.5 if invalidated else 1.0), "width": 1},
                    hoverinfo="skip",
                    name=f"{style.name} box" + (" (invalidated)" if invalidated else ""),
                )
            )
    traces.append(
        go.Scatter(
            x=hover_x,
            y=hover_y,
            mode="markers",
            marker={"size": cfg.marker_size, "opacity": 0},  # invisible, only for hover
            text=hover_text_,
            hovertemplate="%{text}<extra></extra>",
            name=style.name,
        )
    )
    if marks_x:
        traces.append(
            go.Scatter(
                x=marks_x,
                y=marks_y,
                mode="markers",
                marker={
                    "symbol": marks_symbol,
                    "color": style.color,
                    "size": cfg.marker_size - 2,
                    "line": {"color": style.color, "width": 1},
                },
                text=marks_text,
                hovertemplate="%{text}<extra></extra>",
                name=f"{style.name} state",
            )
        )
    return traces


def steps_text(history: Sequence[ZoneTransition]) -> str:
    """'state: …' plus one line per transition, for the hover text."""
    steps = "".join(
        f"<br>{t.state.value}: candle closed {t.confirmed_at:%m-%d %H:%M} UTC" for t in history
    )
    return f"state: {state_at(history).value}{steps}"
