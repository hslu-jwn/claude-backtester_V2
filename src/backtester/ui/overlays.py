"""Confluence overlays on the chart ("all confluences" mode). Spec: ROADMAP.md › Phase 2.

The chart starts empty. The "Overlays" switch turns overlays on and a multi-select dropdown
picks which types are drawn. Every detector plugs in by registering an `OverlayType`:

- `detect(replay)` runs the detector over the whole loaded range, feeding it
  `replay.view(cursor)` once per candle, in order (`run_detector`). Detectors never see a
  `CandleSeries`.
- `draw(events, ctx)` turns events into Plotly traces: a small marker on the
  **confirming candle** (x = `event.confirmed_index`) and a hover text with its state.
- `status(events, ctx)` (optional) returns layout annotations for a state that depends on
  every event up to the cursor, not only the drawn ones (e.g. the current trend, which can
  come from a BOS before the replay window). It gets all events confirmed at or before the
  cursor.

Events are computed once per loaded range and then filtered by `visible_events`: during
replay only events whose confirming candle is at or before the cursor are drawn. Because
every detector has a no-lookahead test (appending candles never changes past events), this
shows exactly what an incremental run up to the cursor would have emitted.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from plotly.basedatatypes import BaseTraceType
from plotly.graph_objs.layout import Annotation

from backtester.core.models import Timeframe
from backtester.detectors.base import Detector, Event
from backtester.engine.replay import Replay
from backtester.ui.chart_figure import DEFAULT_CONFIG, ChartConfig, price_digits


class OverlayUnavailable(Exception):
    """An overlay can't be computed for this data (e.g. a setting the spec leaves open for
    the symbol). The message is shown on the chart page instead of the overlay."""


@dataclass(frozen=True)
class OverlayContext:
    """What a `draw` function needs besides the events."""

    symbol: str
    cursor: int  # latest closed candle shown (absolute index = x on the chart)
    first_x: int  # first candle drawn
    config: ChartConfig = DEFAULT_CONFIG
    timeframe: Timeframe = Timeframe.M5  # shown timeframe
    overall_timeframe: Timeframe | None = None  # the replay's overall-trend series, if any

    @property
    def digits(self) -> int:
        return price_digits(self.symbol)


@dataclass(frozen=True)
class OverlayType:
    key: str  # dropdown value, e.g. "swings"
    label: str  # dropdown text, e.g. "Swings"
    detect: Callable[[Replay], Sequence[Event]]
    draw: Callable[[Sequence[Event], OverlayContext], list[BaseTraceType]]
    status: Callable[[Sequence[Event], OverlayContext], list[Annotation]] | None = None


OVERLAYS: dict[str, OverlayType] = {}  # in dropdown order


def register(overlay: OverlayType) -> OverlayType:
    if overlay.key in OVERLAYS:
        raise ValueError(f"overlay {overlay.key!r} registered twice")
    OVERLAYS[overlay.key] = overlay
    return overlay


def dropdown_options(registry: dict[str, OverlayType] = OVERLAYS) -> list[dict]:
    return [{"label": o.label, "value": o.key} for o in registry.values()]


def run_detector(detector: Detector, replay: Replay) -> list[Event]:
    """All events of `detector`, fed one closed candle at a time through `SeriesView`s."""
    events: list[Event] = []
    for cursor in range(len(replay)):
        events.extend(detector.update(replay.view(cursor)))
    return events


def visible_events(events: Sequence[Event], cursor: int, first_x: int = 0) -> list[Event]:
    """Events confirmed by a candle in first_x..cursor (nothing confirmed after the cursor)."""
    return [e for e in events if first_x <= e.confirmed_index <= cursor]


def overlay_traces(
    events_for: Callable[[OverlayType], Sequence[Event]],
    keys: Sequence[str],
    ctx: OverlayContext,
    registry: dict[str, OverlayType] = OVERLAYS,
) -> tuple[list[BaseTraceType | Annotation], list[str]]:
    """(traces and annotations, messages) for the selected overlay types, in registry order.

    `events_for(overlay)` returns that overlay's events over the loaded range (the chart
    page caches them). Unknown keys (e.g. a type removed since the browser saved the
    choice) are ignored; an `OverlayUnavailable` becomes a message.
    """
    traces: list[BaseTraceType | Annotation] = []
    messages: list[str] = []
    for key, overlay in registry.items():
        if key not in keys:
            continue
        try:
            events = events_for(overlay)
        except OverlayUnavailable as e:
            messages.append(f"{overlay.label}: {e}")
            continue
        traces.extend(overlay.draw(visible_events(events, ctx.cursor, ctx.first_x), ctx))
        if overlay.status is not None:
            traces.extend(overlay.status(visible_events(events, ctx.cursor), ctx))
    return traces, messages
