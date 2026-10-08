"""Confluence overlays on the chart ("all confluences" mode). Spec: ROADMAP.md › Phase 2.

The chart starts empty. The "Overlays" switch turns overlays on and a checkbox panel
(opened like a dropdown) picks which types are drawn, in roadmap order (`order`); each
type's sub-entries stay indented right under it and can only be ticked while it is. Every detector plugs in by registering an `OverlayType`:

- `detect(replay, settings)` runs the detector over the whole loaded range, feeding it
  `replay.view(cursor)` once per candle, in order (`run_detector`). Detectors never see a
  `CandleSeries`. `settings` are the chart's detector switches (`OverlaySettings`, e.g. the
  strong-move filter); overlays that have none ignore them.
- `draw(events, ctx)` turns events into neutral drawing objects (`ui/drawing.py`: boxes,
  lines, markers, labels, hover areas), e.g. a small marker on the **confirming candle**
  (x = `event.confirmed_index`) and a hover text with its state (zones: hover over the
  zone itself, no marker). `ui/plotly_render.py` turns them into Plotly traces.
- `parts` (optional) are sub-entries listed under the overlay in the panel (e.g.
  "↳ ★ confirmations" under FVG); the selected ones reach `draw` as `ctx.parts`.
- `status(events, ctx)` (optional) returns badges (`drawing.Badge`) for a state that depends on
  every event up to the cursor, not only the drawn ones (e.g. the current trend, which can
  come from a BOS before the replay window). It gets all events confirmed at or before the
  cursor.

Events are computed once per loaded range and settings and then filtered by `visible_events`: during
replay only events whose confirming candle is at or before the cursor are drawn. Because
every detector has a no-lookahead test (appending candles never changes past events), this
shows exactly what an incremental run up to the cursor would have emitted.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace

from backtester.core.models import Timeframe
from backtester.detectors.base import Detector, Event
from backtester.engine.replay import Replay
from backtester.ui.chart_figure import DEFAULT_CONFIG, ChartConfig, price_digits
from backtester.ui.drawing import Badge, Drawing


@dataclass(frozen=True)
class OverlaySettings:
    """Detector switches on the chart page (the settings page replaces them in Phase 4)."""

    fvg_strong_move_filter: bool = False  # spec › Strong-move filter (FVG default off)
    ob_strong_move_filter: bool = True  # spec › Strong-move filter (OB default on)


DEFAULT_SETTINGS = OverlaySettings()


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
    parts: frozenset[str] = frozenset()  # the overlay's selected sub-entries (drawing only)

    @property
    def digits(self) -> int:
        return price_digits(self.symbol)


@dataclass(frozen=True)
class OverlayType:
    key: str  # panel value, e.g. "swings"
    label: str  # panel text, e.g. "Swings"
    detect: Callable[[Replay, OverlaySettings], Sequence[Event]]
    draw: Callable[[Sequence[Event], OverlayContext], list[Drawing]]
    status: Callable[[Sequence[Event], OverlayContext], list[Badge]] | None = None
    # optional sub-entries listed under it in the panel, (part key, label), e.g.
    # ("confirmed", "★ confirmations"); `draw` gets the selected ones in `ctx.parts`
    parts: tuple[tuple[str, str], ...] = field(default=())
    order: str = "99"  # position in the panel: the roadmap step (e.g. "2.5" for FVG)
    # True: `detect(replay, settings, sources)` also gets the chart's `SymbolSources`, for
    # overlays that load their own candles (e.g. the Trades overlay's 5m backtest)
    needs_sources: bool = False

    @property
    def step(self) -> tuple[int, ...]:
        """`order` as numbers, so "2.11" comes after "2.9"."""
        return tuple(int(p) for p in self.order.split("."))

    def part_value(self, part: str) -> str:
        """Panel value of a sub-entry, e.g. "fvg.confirmed"."""
        return f"{self.key}.{part}"


OVERLAYS: dict[str, OverlayType] = {}  # in panel order (`order`)


def register(overlay: OverlayType, registry: dict[str, OverlayType] = OVERLAYS) -> OverlayType:
    """Add `overlay`, keeping the registry sorted by `order` (import order doesn't matter)."""
    if overlay.key in registry:
        raise ValueError(f"overlay {overlay.key!r} registered twice")
    entries = sorted([*registry.values(), overlay], key=lambda o: o.step)
    registry.clear()
    registry.update((o.key, o) for o in entries)
    return overlay


def overlay_options(
    selected: Sequence[str] = (), enabled: bool = True, registry: dict[str, OverlayType] = OVERLAYS
) -> list[dict]:
    """Checkbox options: one per overlay type, its sub-entries indented right below it.
    Everything is disabled while the Overlays switch is off; a sub-entry also while its
    overlay isn't ticked."""
    options = []
    for o in registry.values():
        options.append({"label": o.label, "value": o.key, "disabled": not enabled})
        options += [
            {
                "label": f" ↳ {label}",
                "value": o.part_value(part),
                "disabled": not enabled or o.key not in selected,
            }
            for part, label in o.parts
        ]
    return options


def overlay_summary(selected: Sequence[str], registry: dict[str, OverlayType] = OVERLAYS) -> str:
    """Text on the closed panel: the ticked overlay types, in panel order."""
    labels = [o.label for o in registry.values() if o.key in selected]
    return f"Overlay types: {', '.join(labels)}" if labels else "Overlay types"


def run_detector(detector: Detector, replay: Replay) -> list[Event]:
    """All events of `detector`, fed one closed candle at a time through `SeriesView`s."""
    events: list[Event] = []
    for cursor in range(len(replay)):
        events.extend(detector.update(replay.view(cursor)))
    return events


def visible_events(events: Sequence[Event], cursor: int, first_x: int = 0) -> list[Event]:
    """Events confirmed by a candle in first_x..cursor (nothing confirmed after the cursor)."""
    return [e for e in events if first_x <= e.confirmed_index <= cursor]


def overlay_drawings(
    events_for: Callable[[OverlayType], Sequence[Event]],
    keys: Sequence[str],
    ctx: OverlayContext,
    registry: dict[str, OverlayType] = OVERLAYS,
) -> tuple[list[Drawing], list[str]]:
    """(drawings and badges, messages) for the selected overlay types, in registry order.

    `events_for(overlay)` returns that overlay's events over the loaded range (the chart
    page caches them). Unknown keys (e.g. a type removed since the browser saved the
    choice) are ignored; an `OverlayUnavailable` becomes a message. A sub-entry only
    draws with its overlay selected; `draw` gets the selected ones in `ctx.parts`.
    """
    drawings: list[Drawing] = []
    messages: list[str] = []
    for key, overlay in registry.items():
        if key not in keys:
            continue
        try:
            events = events_for(overlay)
        except OverlayUnavailable as e:
            messages.append(f"{overlay.label}: {e}")
            continue
        parts = frozenset(p for p, _ in overlay.parts if overlay.part_value(p) in keys)
        drawn = replace(ctx, parts=parts)
        drawings.extend(overlay.draw(visible_events(events, ctx.cursor, ctx.first_x), drawn))
        if overlay.status is not None:
            drawings.extend(overlay.status(visible_events(events, ctx.cursor), ctx))
    return drawings, messages
