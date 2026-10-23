"""Chart page: TradingView-like candlesticks from the M1 cache. Spec: ROADMAP.md › 1.1, 4.0a.

The chart is TradingView Lightweight Charts in the browser (`ui/assets/chart.js`, created
once and kept). The server only sends data (`ui/chart_data.py`), through stores:
`chart-base` = candles up to the cursor and session lines (a new symbol, timeframe, range
or replay mode); `chart-ovl` = the drawings of the overlay types the browser asked for in
`chart-need` (types it doesn't have yet for this range and filter setting); `chart-delta`
= one replay step from the browser's cursor (`chart-view`, written by the browser) to the
next. Showing / hiding overlays, sub-entries and session lines happens in the browser.

Pick symbol (every symbol of `SymbolSources` with cached days, each read from its own
source's cache, `data/sources.py`) and timeframe. The shown days (store `chart-dates`
{start, end}, UTC days, both inclusive, limited to cached days) start as the last month of
the symbol and grow while scrolling (user, 2026-10-19): when the view comes near the left or
right edge of the loaded candles the browser asks for more (`chart-more`), `extend_dates` adds
a chunk of days there (never across a hole in the cache, at most `max_candles`, not in
replay) and the chart reloads around the same time and zoom, overlays included. "Go to", a
timeframe switch and a trade focus load their days too. A range touching a day that was never
imported shows the `MissingCacheError` instead of a chart, so gaps in the cache are never
silent. Zooming or panning is the library's; the price axis fits the visible candles.
A thin bar at the top of the chart pane shows loads (staged) and backtests (percent).

Replay (ROADMAP.md › 1.2): "Replay" first shows the full chart and asks for a start candle
(click one, or press ▶ to start at the first candle of the last day). From then on only the
candles of `Replay.view(cursor)` are sent, a `SeriesView`, so the chart shows exactly what
the engine sees; each step sends only the next candle and what changed with it.
Replay steps on the shown timeframe (M5: 5 minutes per step, H1: one hour). The replay
state stores `now` (the close time of the cursor candle), so switching timeframe keeps the
replay time: the chart then shows the candles of that timeframe closed at `now`.
It also keeps the visible TIME span around the cursor (the "replay span", minutes left and
right of `now`): switching M5 -> M1 shows the same hours with smaller candles. The span
starts at `replay_visible` / `replay_right_space` candles of the timeframe replay was
started on and follows the user's zoom/pan (the browser reports it); each step keeps it.

Session lines (ROADMAP.md › 1.3): the "Sessions" switch shows or hides all session start
lines (Tokyo, London, NY), in the normal chart and in replay; the choice is kept in the browser.

Overlays (ROADMAP.md › Phase 2): the chart starts empty. In the ⚙ Settings popover's "Chart
Overlays" section the "Show overlays" switch turns the detector overlays on and the list under
it picks which types are drawn: one checkbox per registered `OverlayType` in roadmap order, see
`ui/overlays.py`. A checkbox panel rather than a dropdown, so ticked entries stay in place
and sub-entries stay right under their type. Events are computed once per
loaded range by feeding the detector `SeriesView`s; during replay only events confirmed at
or before the cursor are drawn. Both choices are kept in the browser. The "FVG strong-move
filter" (default off) and "OB strong-move filter" (default on) switches
(confluences.md › Strong-move filter) are passed to those detectors; events are cached
per setting, so switching back is instant (the FVG switch also applies to BPRs, which are
built from FVGs). Zone overlays (FVG, Order block, BPR) have indented
sub-entries "↳ ★ confirmations" / "↳ ✕ invalidations" that show their ★ / ✕ markers
(drawing only); they can only be ticked while their type is.

Trades (ROADMAP.md › 3.3b): the "Trades" overlay runs the selected strategy and the engine
on the shown symbol and range (with warm-up) and draws position boxes, see
`ui/trades_overlay.py` (confluences: strategy 1 only).
It and the backtest use the settings panel's current settings (ROADMAP.md › 4.1,
`ui/settings_panel.py`, store `settings-current`); the browser re-requests the overlays
when their key changes.
Overlays that load their own data (`OverlayType.needs_sources`) get the page's sources.

Focus on one trade (ROADMAP.md › 3.6, 7.6): a trade of a backtest (results page, the side
panel's "Trades in view") or a live trade (Live page) opens as an ORDER, see `ui/trade_focus.py`:
`/?symbol=…&tf=…&dir=…&entry=…&ep=…&sl=…&tp=…&exit=…&xp=…` selects the symbol and the timeframe
(the strategy's own, from the run's settings), loads the trade's days and scrolls the chart to
the trade; only that order is drawn (entry, SL, TP zones, labelled), nothing is run and no
overlay is switched on. The order (store `chart-order`, drawn from `chart-order-draw`) stays until
another symbol is picked or the ✕ on its chip (bottom bar) is pressed. A trade on a day that is not
cached shows a note on the chip. Links of the older form (`symbol, from, to, t0, t1`, no order) turn
on the Trades overlay as before. Applied once; the store `chart-focus` is then marked done, so
later changes of symbol or days are the user's again.

Timeframe switch (ROADMAP.md › 4.0b part 1), outside replay: the time at the centre of
the view stays at the centre and the number of visible candles stays the same (the browser
reports its view in `chart-viewport`; `chart.js` re-centres after the new candles). The
days the new view needs are added to the shown range (`dates_for_view`), so a switch up
shows as many candles as before. In replay the replay time is kept (as before).

Screenshot (ROADMAP.md › 4.0b part 3): the camera button (top right) saves a PNG of the
chart as shown, with a stamp (symbol, timeframe, first → last visible candle in UTC, the
replay time, the overlays that are on, the settings preset) and the same data in the file
name; "▾" also offers copying it to the clipboard. All in the browser (`chart.js` `shot`).

Go to (ROADMAP.md › 4.0b part 4): the "Go to" field in the bottom bar (Alt+G) takes a UTC
time; its days are loaded if they aren't shown (`goto_dates`) and the browser centres on
the candle containing it (`chart.js` `goto`). In replay only times up to the replay time.

Box zoom (ROADMAP.md › 4.0b part 5): the zoom button, then drag a rectangle: the chart
shows that time and price range; "reset zoom" or a double-click on the chart goes back,
a double-click on the price axis auto-scales. All in the browser (`chart.js`).

Later steps add: the session view (3.5).
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache
from pathlib import Path

from dash import ALL, ClientsideFunction, Dash, Input, Output, State, ctx, dcc, html, no_update

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.data.adapters.cache_adapter import (
    MissingCacheError,
    candles_from_frame,
    latest_run,
)
from backtester.data.resample import CALENDAR, DEFAULT_BOUNDARY, DayBoundary, H4Alignment, supported
from backtester.data.sources import SymbolSources, cached_block, warmup_start
from backtester.detectors.sweep import SweepConfig
from backtester.detectors.swings import SwingConfig
from backtester.engine.replay import Replay
from backtester.runner import RESULTS_DIR, RunSettings, start_run
from backtester.settings import from_json
from backtester.strategy.registry import REGISTRY
from backtester.ui import (
    backtest_job,
    bos_overlay,  # noqa: F401  (registers the BOS + trend overlay)
    bot_overlay,
    bpr_overlay,  # noqa: F401  (registers the BPR overlay)
    breaker_overlay,  # noqa: F401  (registers the Breaker block overlay)
    chart_side,
    equilibrium_overlay,  # noqa: F401  (registers the Equilibrium overlay)
    fvg_overlay,  # noqa: F401  (registers the FVG overlay)
    ob_overlay,  # noqa: F401  (registers the Order block overlay)
    session_zone_overlay,  # noqa: F401  (registers the Session zones overlay)
    settings_panel,
    sweep_overlay,  # noqa: F401  (registers the Liquidity sweep overlay)
    swing_overlay,  # noqa: F401  (registers the Swings overlay)
    trade_focus,
    trades_overlay,  # noqa: F401  (registers the Trades overlay)
    update_button,
)
from backtester.ui.chart_config import DEFAULT_CONFIG, ChartConfig, price_digits
from backtester.ui.chart_data import ChartData
from backtester.ui.overlays import (
    DEFAULT_SETTINGS,
    OVERLAYS,
    OverlaySettings,
    OverlayType,
    OverlayUnavailable,
    overlay_options,
    overlay_summary,
)

TIMEFRAMES = [tf.name for tf in Timeframe if supported(tf)]
CALENDAR_NAMES = {tf.name for tf in CALENDAR}
DEFAULT_TIMEFRAME = Timeframe.M5.name
REPLAY_OFF = {"on": False, "picking": False, "playing": False, "start": None, "now": None}


@lru_cache(maxsize=32)
def _cached_events(
    replay: Replay,
    overlay: OverlayType,
    settings: OverlaySettings,
    sources: SymbolSources | None = None,
):
    """Events of one overlay over the whole replay range, computed once per range and
    settings. Only overlays that use the strategy settings get them (so the others stay
    cached when they change)."""
    if not overlay.strategy_settings and settings.strategy:
        return _cached_events(replay, overlay, replace(settings, strategy=""), sources)
    if overlay.needs_sources:
        if sources is None:
            raise OverlayUnavailable("needs the chart's data sources")
        return tuple(overlay.detect(replay, settings, sources))
    return tuple(overlay.detect(replay, settings))


def _load_frame(sources, symbol, timeframe, start_date, end_date, config):
    """(candle frame or None, message) for the chosen inputs."""
    if not (symbol and timeframe and start_date and end_date):
        return None, "Pick a symbol, timeframe and date range."
    start, end = date.fromisoformat(start_date[:10]), date.fromisoformat(end_date[:10])
    if end < start:
        return None, "The end date is before the start date."
    tf = Timeframe[timeframe]
    weekdays = sum(1 for d in sources.cached_days(symbol) if start <= d <= end and d.weekday() < 5)
    estimate = weekdays * 1440 // tf.value
    if estimate > config.max_candles * config.early_refuse_factor:
        return None, (
            f"About {estimate:,} {timeframe} candles is far more than the limit of "
            f"{config.max_candles:,}. Pick a shorter range or a higher timeframe "
            "(e.g. 4h or D for years)."
        )
    try:
        frame = sources.adapter(symbol).fetch_frame(
            symbol,
            Timeframe[timeframe],
            _midnight(start),
            _midnight(end + timedelta(days=1)),
            config.day_boundary,
            config.h4_alignment,
        )
    except MissingCacheError as e:
        return None, str(e)
    if frame.empty:
        return None, f"No {symbol} candles from {start} to {end} (market closed?)."
    if len(frame) > config.max_candles:
        return None, (
            f"{len(frame):,} {timeframe} candles is more than the limit of "
            f"{config.max_candles:,}. Pick a shorter range or a higher timeframe."
        )
    return frame, f"{len(frame):,} {timeframe} candles, {start} to {end} (UTC)."


@lru_cache(maxsize=8)
def _cached_replay(sources, symbol, timeframe, start_date, end_date, config, live_stamp=()):
    """`live_stamp` (the live folder's files and times) only keys the cache: today's live day
    is rewritten every minute and must be read again."""
    frame, message = _load_frame(sources, symbol, timeframe, start_date, end_date, config)
    if frame is None:
        return None, message
    series = CandleSeries(symbol, Timeframe[timeframe], candles_from_frame(frame))
    overall = _overall_series(sources, symbol, start_date, end_date, config)
    higher = _higher_series(sources, symbol, series.timeframe, start_date, end_date, config)
    return Replay(series, higher, overall=overall), message


def _higher_series(sources, symbol, timeframe, start_date, end_date, config) -> list:
    """The chart range on `config.higher_timeframes` above the shown one (e.g. 30m for
    session zones on the 5m chart), read by overlays only through the replay's clocks."""
    start, end = date.fromisoformat(start_date[:10]), date.fromisoformat(end_date[:10])
    out = []
    for tf in config.higher_timeframes:
        if tf.value <= timeframe.value:
            continue
        frame = sources.adapter(symbol).fetch_frame(
            symbol, tf, _midnight(start), _midnight(end + timedelta(days=1))
        )
        if len(frame):
            out.append(CandleSeries(symbol, tf, candles_from_frame(frame)))
    return out


def _overall_series(sources, symbol, start_date, end_date, config) -> CandleSeries | None:
    """Overall-trend candles (confluences.md › Trend) from up to
    `overall_trend_warmup_days` before the chart range to its end, using only cached days
    with no missing day in between, so the trend is already known at the range's start."""
    start, end = date.fromisoformat(start_date[:10]), date.fromisoformat(end_date[:10])
    cached = set(sources.cached_days(symbol))
    first = warmup_start(cached, start, config.overall_trend_warmup_days)
    timeframe = config.trend.overall_timeframe
    frame = sources.adapter(symbol).fetch_frame(
        symbol, timeframe, _midnight(first), _midnight(end + timedelta(days=1))
    )
    return CandleSeries(symbol, timeframe, candles_from_frame(frame)) if len(frame) else None


def estimated_candles(first: date, last: date, timeframe: Timeframe) -> int:
    """Upper estimate of the candles in the UTC days first..last (every minute traded)."""
    return ((last - first).days + 1) * 1440 // timeframe.value


def dates_for_view(
    cached: Sequence[date],
    start: date,
    end: date,
    view: dict,
    timeframe: Timeframe,
    config: ChartConfig = DEFAULT_CONFIG,
) -> tuple[date, date] | None:
    """Chart days after switching to `timeframe` (ROADMAP 4.0b part 1), or None to keep
    start..end. `view` = what the browser shows: the centre time (UTC seconds) and the
    number of visible candles. The new view needs that many candles of `timeframe` around
    the centre, plus `switch_warmup_candles` on the left for the overlays; the days are
    added to the shown ones, within the run of cached days around the centre. If that is
    more than `max_candles` (a switch down), only the days the view needs are kept."""
    center = datetime.fromtimestamp(view["center"], UTC)
    cached_set = set(cached)
    if center.date() not in cached_set:
        return None
    block_first, block_last = cached_block(cached_set, center.date())
    half = view["count"] / 2
    left = (half + config.switch_warmup_candles) * timeframe.duration
    need_first = max((center - left).date(), block_first)
    need_last = min((center + half * timeframe.duration).date(), block_last)
    first, last = min(start, need_first), max(end, need_last)
    if not (block_first <= start and end <= block_last):  # shown days in another block
        first, last = need_first, need_last
    if estimated_candles(first, last, timeframe) > config.max_candles:
        first, last = need_first, need_last
    return None if (first, last) == (start, end) else (first, last)


def extend_dates(
    cached: Sequence[date],
    start: date,
    end: date,
    side: str,
    timeframe: Timeframe,
    view: dict | None = None,
    config: ChartConfig = DEFAULT_CONFIG,
) -> tuple[date, date] | None:
    """Days to show after the view came near the "left" or "right" edge of the loaded days
    start..end (user, 2026-10-19), or None when there is nothing more to load. Adds a chunk of
    `config.extend_candles` (estimated) candles of days on that side, within the run of cached
    days around the shown ones (a hole in the cache stops it). Above `max_candles` the
    opposite end is dropped, but never below what `view` (centre time and candle count, as in
    `dates_for_view`) still shows; if that is not enough the new chunk is cut instead."""
    cached_set = set(cached)
    if start not in cached_set or end not in cached_set:
        return None
    block_first, block_last = cached_block(cached_set, start)
    chunk = max(1, -(-config.extend_candles * timeframe.value // 1440))
    first, last = start, end
    if side == "left":
        first = max(start - timedelta(days=chunk), block_first)
    else:
        last = min(end + timedelta(days=chunk), block_last)
    if (first, last) == (start, end):
        return None
    allowed = config.max_candles * timeframe.value // 1440  # days that fit under the limit

    def excess() -> int:
        return (last - first).days + 1 - allowed

    if excess() > 0:
        keep_first, keep_last = last, first  # the far end may move up to the view's days
        if view:
            half = timedelta(seconds=view["count"] / 2 * timeframe.duration.total_seconds())
            centre = datetime.fromtimestamp(view["center"], UTC)
            keep_first, keep_last = (centre - half).date(), (centre + half).date()
        if side == "left":
            last = max(last - timedelta(days=excess()), min(keep_last, end))
            first += timedelta(days=max(excess(), 0))
        else:
            first = min(first + timedelta(days=excess()), max(keep_first, start))
            last -= timedelta(days=max(excess(), 0))
        if (side == "left" and first >= start) or (side == "right" and last <= end):
            return None  # no room left for the chunk
    return first, last


_GOTO = re.compile(
    r"^\s*(\d{4}-\d{2}-\d{2})(?:[ T]+(\d{1,2}):(\d{2}))?\s*(?:UTC|Z)?\s*$", re.IGNORECASE
)


def parse_goto(text: str | None) -> datetime | None:
    """A UTC time typed into "Go to": "2026-09-12 12:15", "2026-09-12T12:15" or a day
    ("2026-09-12" = 00:00). None if it isn't one."""
    m = _GOTO.match(text or "")
    if not m:
        return None
    try:
        day = date.fromisoformat(m.group(1))
        hour, minute = int(m.group(2) or 0), int(m.group(3) or 0)
        return datetime(day.year, day.month, day.day, hour, minute, tzinfo=UTC)
    except ValueError:
        return None


def goto_dates(
    cached: Sequence[date],
    start: date,
    end: date,
    at: datetime,
    timeframe: Timeframe,
    config: ChartConfig = DEFAULT_CONFIG,
) -> tuple[date, date] | str | None:
    """Days to show for "Go to `at`" (ROADMAP 4.0b part 4): None = the shown days contain
    it; else as many days as shown now, centred on its day, within the run of cached days
    around it and the candle limit; a message if its day isn't cached."""
    day = at.date()
    if start <= day <= end:
        return None
    cached_set = set(cached)
    if day not in cached_set:
        return f"Go to: {day} is not in the cache."
    block_first, block_last = cached_block(cached_set, day)
    span = (end - start).days
    while span > 0 and estimated_candles(day, day + timedelta(days=span), timeframe) > (
        config.max_candles
    ):
        span //= 2
    first = max(day - timedelta(days=span // 2), block_first)
    last = min(first + timedelta(days=span), block_last)
    first = max(min(first, last - timedelta(days=span)), block_first)
    return first, last


def goto_outputs(
    at: datetime,
    symbol: str,
    timeframe: str,
    start: str,
    end: str,
    replay_state: dict | None,
    n: int,
    cached: Sequence[date],
    config: ChartConfig = DEFAULT_CONFIG,
) -> tuple:
    """Outputs (goto command, start date, end date, message) of a go to `at` (UTC): the
    command for the browser plus the days to load if they aren't shown, or a message.
    Used by the "Go to" field and by a click on a trade in the side panel."""
    goto = {"t": int(at.timestamp()), "symbol": symbol, "n": n}
    in_replay = bool(replay_state and replay_state.get("on"))
    if in_replay and replay_state.get("now") and at > datetime.fromisoformat(replay_state["now"]):
        return no_update, no_update, no_update, "Go to: that is after the replay time."
    found = goto_dates(
        cached,
        date.fromisoformat(start[:10]),
        date.fromisoformat(end[:10]),
        at,
        Timeframe[timeframe],
        config,
    )
    if isinstance(found, str):
        return no_update, no_update, no_update, found
    if found is None or in_replay:
        return goto, no_update, no_update, no_update
    return goto, found[0].isoformat(), found[1].isoformat(), no_update


def _packed(outputs: tuple) -> tuple:
    """(goto, start, end, message) of `goto_outputs` as (goto, dates store, message)."""
    goto, start, end, message = outputs
    dates = no_update if start is no_update else {"start": start, "end": end}
    return goto, dates, message


def load_replay(
    sources: SymbolSources,
    symbol: str | None,
    timeframe: str | None,
    start_date: str | None,
    end_date: str | None,
    config: ChartConfig = DEFAULT_CONFIG,
) -> tuple[Replay | None, str]:
    """(Replay over the chosen candles or None, message). Kept in memory for the next steps
    (restart the app to see days downloaded while it runs)."""
    stamp = sources.fallback_stamp(symbol) if symbol in sources.fallback_dirs else ()
    return _cached_replay(sources, symbol, timeframe, start_date, end_date, config, stamp)


def default_start(replay: Replay) -> int:
    """Cursor of the first candle of the last UTC day in the replay."""
    last = replay.close_time(len(replay) - 1) - replay.timeframe.duration
    before = replay.cursor_at(datetime.combine(last.date(), datetime.min.time(), UTC))
    return 0 if before is None else before + 1


def replay_step(action: str, state: dict, replay: Replay | None, clicked_x=None) -> dict:
    """Next replay state after a button, timer tick, candle click or data change.

    Actions: toggle, pick, click, start (back to the start candle), back, forward, play
    (play/pause), tick (autoplay step), data (symbol/timeframe/dates changed).
    """
    if action == "toggle":
        if state["on"] or replay is None:
            return dict(REPLAY_OFF)
        now = _iso(replay.close_time(default_start(replay)))
        return {"on": True, "picking": True, "playing": False, "start": now, "now": now}
    if not state["on"] or replay is None:
        return state
    now = datetime.fromisoformat(state["now"])
    if action == "data":
        if replay.close_time(0) <= now <= replay.close_time(len(replay) - 1):
            return state
        start = _iso(replay.close_time(default_start(replay)))
        return {**state, "picking": True, "playing": False, "start": start, "now": start}
    if action == "pick":
        return {**state, "picking": True, "playing": False}
    if action == "click":
        if clicked_x is None or not 0 <= clicked_x < len(replay):
            return state
        at = _iso(replay.close_time(int(clicked_x)))
        return {**state, "picking": False, "playing": False, "start": at, "now": at}
    if action == "start":
        return {**state, "picking": False, "playing": False, "now": state["start"]}
    if action == "play":
        return {**state, "picking": False, "playing": not state["playing"]}
    if action == "tick" and not state["playing"]:
        return state

    cursor = replay.cursor_at(now)
    if action == "back":
        to = 0 if cursor is None else max(cursor - 1, 0)
        return {**state, "picking": False, "playing": False, "now": _iso(replay.close_time(to))}
    if action in ("forward", "tick"):
        to = 0 if cursor is None else cursor + 1
        if to >= len(replay):
            return {**state, "picking": False, "playing": False}
        playing = action == "tick" and to < len(replay) - 1
        return {**state, "picking": False, "playing": playing, "now": _iso(replay.close_time(to))}
    raise ValueError(f"unknown replay action {action!r}")


def default_span(timeframe: Timeframe, config: ChartConfig = DEFAULT_CONFIG) -> dict:
    """Replay span when replay starts: `replay_visible` candles left of the cursor and
    `replay_right_space` empty slots right of it, in minutes of `timeframe`."""
    minutes = timeframe.value
    return {"left": config.replay_visible * minutes, "right": config.replay_right_space * minutes}


def span_candles(span: dict, timeframe: Timeframe, config: ChartConfig = DEFAULT_CONFIG):
    """(candles left, slots right) of the cursor that show the `span` minutes on `timeframe`.
    Left stays within `replay_min_visible`..`replay_window` candles, right is at least 1."""
    minutes = timeframe.value
    left = min(max(span["left"] / minutes, config.replay_min_visible), config.replay_window)
    return left, max(span["right"] / minutes, 1.0)


# --- Lightweight Charts payloads (ROADMAP 4.0a) -----------------------------------------


def chart_key(symbol, timeframe, start_date, end_date, config: ChartConfig = DEFAULT_CONFIG):
    """Identifies the loaded candles: payloads for another key are ignored by the browser.
    D / W candles also depend on the day boundary, 4h candles on their alignment."""
    key = f"{symbol}|{timeframe}|{start_date}|{end_date}"
    if timeframe in CALENDAR_NAMES and config.day_boundary is not DEFAULT_BOUNDARY:
        key += f"|{config.day_boundary.name}"
    if timeframe == Timeframe.H4.name and config.h4_alignment is not H4Alignment.UTC:
        key += f"|{config.h4_alignment.name}"
    return key


def with_boundary(config: ChartConfig, boundary: str | None, h4: str | None = None) -> ChartConfig:
    """The chart config with the day boundary and the 4h alignment chosen in the chart
    settings."""
    if boundary in DayBoundary.__members__:
        config = replace(config, day_boundary=DayBoundary[boundary])
    if h4 in H4Alignment.__members__:
        config = replace(config, h4_alignment=H4Alignment[h4])
    return config


# Temporary tweaker (user, 2026-10-12): liquidity sweep rules tried on the chart. Values of
# the Sweep section of the chart settings: the equal-high tolerance in ATR ("none": one of the last N).
SWEEP_TOLERANCES = (
    ("none", "One of the last N (current)"),
    ("0", "Most extreme of last N (0)"),
    ("0.1", "Same height: 0.1 ATR"),
    ("0.25", "Same height: 0.25 ATR"),
    ("0.5", "Same height: 0.5 ATR"),
    ("1", "Same height: 1 ATR"),
    ("2", "Same height: 2 ATR"),
)


# breakout filter choices: value -> (label, SweepConfig fields)
SWEEP_CANCELS = {
    "off": ("No breakout filter (current)", {}),
    "c2": ("2 closes beyond: no sweep", {"two_closes_cancel": True}),
    "c3": ("3 closes beyond: no sweep", {"two_closes_cancel": True, "cancel_closes": 3}),
    "w2": (
        "1 wick + 1 close beyond: no sweep",
        {"two_closes_cancel": True, "cancel_wick_first": True},
    ),
    "w3": (
        "2 wicks + 1 close beyond: no sweep",
        {"two_closes_cancel": True, "cancel_wick_first": True, "cancel_closes": 3},
    ),
}


def sweep_config(tweak: dict | None) -> SweepConfig:
    """The sweep rules chosen in the Sweep section of the chart settings ({"n", "tol", "cancel", "top"})."""
    tweak = tweak or {}
    tol = tweak.get("tol", "none")
    return SweepConfig(
        lookback_swings=int(tweak.get("n", SweepConfig().lookback_swings)),
        equal_tolerance_atr=None if tol == "none" else float(tol),
        bos_before_top=bool(tweak.get("top")),
        **SWEEP_CANCELS.get(tweak.get("cancel", "off"), SWEEP_CANCELS["off"])[1],
    )


def overlay_settings(
    filters: Sequence[str] | None, strategy: str = "", sweep_tweak: dict | None = None
) -> OverlaySettings:
    """The chart's detector switches + the strategy settings (canonical JSON, "" = spec
    defaults; `settings_panel.store_json`) + the sweep rules being tried."""
    filters = filters or []
    return OverlaySettings(
        fvg_strong_move_filter="fvg" in filters,
        ob_strong_move_filter="ob" in filters,
        strategy=strategy,
        doji_max_body=changed_doji(strategy),
        doji_range_share=from_json(strategy).detectors.swings.doji_range_share if strategy else 0.0,
        sweep=sweep_config(sweep_tweak),
    )


def changed_doji(strategy: str) -> tuple[tuple[str, float], ...]:
    """The doji thresholds of the strategy settings that differ from the spec's."""
    if not strategy:
        return ()
    spec = SwingConfig().doji_max_body
    chosen = from_json(strategy).detectors.swings.doji_max_body
    return tuple(sorted((s, v) for s, v in chosen.items() if spec.get(s) != v))


@lru_cache(maxsize=16)
def chart_data(
    replay: Replay,
    settings: OverlaySettings = DEFAULT_SETTINGS,
    sources: SymbolSources | None = None,
    config: ChartConfig = DEFAULT_CONFIG,
) -> ChartData:
    """Payload builder for one loaded range and detector setting (kept for replay steps)."""
    return ChartData(
        replay,
        lambda o: _cached_events(replay, o, settings, sources),
        config,
        feed_switch=sources.feed_switch(replay.symbol) if sources is not None else None,
    )


def replay_message(replay: Replay, cursor: int) -> str:
    current = replay.view(cursor).current
    return (
        f"Replay · candle {cursor + 1:,} of {len(replay):,} · "
        f"{current.ts:%Y-%m-%d %H:%M} {replay.timeframe.name} candle, closed at "
        f"{replay.close_time(cursor):%H:%M} UTC"
    )


def base_payload(
    sources: SymbolSources,
    symbol: str | None,
    timeframe: str | None,
    start_date: str | None,
    end_date: str | None,
    replay_state: dict = REPLAY_OFF,
    span: dict | None = None,
    config: ChartConfig = DEFAULT_CONFIG,
) -> tuple[dict | None, str]:
    """(candles up to the cursor + session lines, message). The cursor is the last candle,
    or in replay (start picked) the candle closed at the replay time `now`."""
    replay, message = load_replay(sources, symbol, timeframe, start_date, end_date, config)
    if replay is None:
        return None, message
    in_replay = replay_state["on"] and not replay_state["picking"]
    cursor = len(replay) - 1
    if in_replay:
        now = datetime.fromisoformat(replay_state["now"])
        cursor = replay.cursor_at(now)
        if cursor is None:
            return None, f"Replay at {now:%Y-%m-%d %H:%M} UTC: no candle closed yet. Press ▶."
        message = replay_message(replay, cursor)
    elif replay_state["on"]:
        now = datetime.fromisoformat(replay_state["now"])
        message = (
            "Replay: click the candle to start at, or press ▶ to start after the "
            f"candle closing at {now:%Y-%m-%d %H:%M} UTC."
        )
    data = chart_data(replay, DEFAULT_SETTINGS, sources, config)
    tf = Timeframe[timeframe]
    payload = {
        "key": chart_key(symbol, timeframe, start_date, end_date, config),
        "symbol": symbol,
        "tf": tf.name,
        "tfmin": tf.value,
        "digits": price_digits(symbol),
        "cursor": cursor,
        "replay": bool(replay_state["on"]),
        "picking": bool(replay_state["on"] and replay_state["picking"]),
        "candles": data.candles(0, cursor + 1),
        "sessions": data.sessions(0, cursor + 1),
        "span": None,
        "range": None,
    }
    if in_replay:  # the replay span (minutes left / right of the cursor) on this timeframe
        span = span or default_span(tf, config)
        left, right = span_candles(span, tf, config)
        payload["span"] = span
        payload["range"] = {"from": cursor - left + 0.5, "to": cursor + right + 0.5}
    return payload, message


def overlay_payload(
    sources: SymbolSources,
    request: dict,
    symbol,
    timeframe,
    start_date,
    end_date,
    filters,
    config: ChartConfig = DEFAULT_CONFIG,
    strategy: str = "",
    sweep_tweak: dict | None = None,
) -> dict | None:
    """Full drawings of the requested overlay types at the browser's cursor, or None if
    the request is for other candles than the ones selected now."""
    if not request or request["key"] != chart_key(symbol, timeframe, start_date, end_date, config):
        return None
    replay, _ = load_replay(sources, symbol, timeframe, start_date, end_date, config)
    if replay is None or not 0 <= request["cursor"] < len(replay):
        return None
    data = chart_data(replay, overlay_settings(filters, strategy, sweep_tweak), sources, config)
    return {
        **data.full(request["types"], request["cursor"]),
        "key": request["key"],
        "filters": request["filters"],
        "requested": request["types"],
        "order": list(OVERLAYS),
    }


def order_draw_payload(
    sources: SymbolSources,
    order: dict | None,
    symbol: str | None,
    timeframe: str | None,
    start_date: str | None,
    end_date: str | None,
    replay_state: dict | None = None,
    config: ChartConfig = DEFAULT_CONFIG,
    run_trades: Sequence | None = None,
) -> dict | None:
    """{"key", "items"}: the drawings on the candles of this chart (`key` = the base payload's,
    so the browser draws them only on those candles). With a focused `order` of this symbol: that
    order, labelled. Without one: the `run_trades` (the newest run's, any strategy) of the symbol
    that are on the loaded candles, light and capped at `MAX_RUN_ORDERS`; no strategy is run.
    None: nothing to draw, another symbol, replay on, or no candles."""
    if not symbol or not timeframe or (replay_state and replay_state.get("on")):
        return None
    if order and order.get("symbol") != symbol:
        order = None
    if not order and not [t for t in run_trades or () if t.symbol == symbol]:
        return None
    replay, _ = load_replay(sources, symbol, timeframe, start_date, end_date, config)
    if replay is None:
        return None
    opens = [c.ts for c in replay.view(len(replay) - 1)]
    tf, digits = Timeframe[timeframe], price_digits(symbol)
    if order:
        items = trade_focus.order_payload(order, opens, tf, digits, config)
    else:
        items, drawn = [], 0
        for t in run_trades:
            if t.symbol != symbol or drawn >= trade_focus.MAX_RUN_ORDERS:
                continue
            found = trade_focus.order_payload(
                trade_focus.trade_order(t), opens, tf, digits, config, light=True
            )
            drawn += bool(found)
            items += found
    return {"key": chart_key(symbol, timeframe, start_date, end_date, config), "items": items}


def replay_delta(
    sources: SymbolSources,
    view: dict | None,
    replay: Replay,
    cursor: int,
    key: str,
    filters,
    config: ChartConfig = DEFAULT_CONFIG,
    strategy: str = "",
    sweep_tweak: dict | None = None,
) -> dict | None:
    """Delta from what the browser shows (`view`: key, cursor, loaded types) to `cursor`."""
    if not view or view.get("key") != key or view.get("cursor") is None:
        return None
    frm = view["cursor"]
    if not 0 <= frm < len(replay):
        return None
    data = chart_data(replay, overlay_settings(filters, strategy, sweep_tweak), sources, config)
    return {**data.delta(view.get("types") or [], frm, cursor), "key": key}


# --- backtest from the toolbar (ROADMAP 4.0, 7.6; the run is shown on /backtest) ---------

BACKTEST_PATH = "/backtest"


def start_backtest(
    sources: SymbolSources,
    symbols,
    start_date,
    end_date,
    start=start_run,
    settings: RunSettings | None = None,
    preset: str | None = None,
):
    """Outputs of the backtest callback after "Run": (status text, page). The run goes on in
    a background thread (ui/backtest_job.py) with `settings` (the settings panel's current
    ones) and the app opens the Backtest page, which shows it; one backtest at a time."""
    if not symbols or not start_date or not end_date:
        return "Pick one or more symbols and the days.", no_update
    first, last = date.fromisoformat(start_date[:10]), date.fromisoformat(end_date[:10])
    try:
        # no live fallback in backtests: today's partial day is for the chart only (7.8)
        no_live = replace(sources, fallback_dirs={}) if sources is not None else None
        backtest_job.start(symbols, first, last, settings, no_live, preset, starter=start)
    except backtest_job.JobRunning:
        return "A backtest is already running. Open it with Backtest in the top bar.", no_update
    return "", BACKTEST_PATH


def chart_settings(config: ChartConfig = DEFAULT_CONFIG) -> dict:
    """Colors and sizes the browser chart needs."""
    return {
        "background": config.background,
        "text_color": config.text_color,
        "axis_border": config.axis_color,
        "show_grid": config.show_grid,
        "grid_color": config.grid_color,
        "spike_color": config.spike_color,
        "up_body": config.up_body,
        "down_body": config.down_body,
        "edge_color": config.edge_color,
        "wick_color": config.wick_color,
        "y_padding": config.y_padding,
        "session_line_width": config.session_line_width,
        "session_line_dash": config.session_line_dash,
        "replay_min_visible": config.replay_min_visible,
        "replay_window": config.replay_window,
        "extend_candles": config.extend_candles,
        "extend_margin_screens": config.extend_margin_screens,
        "extend_margin_min": config.extend_margin_min,
        "progress_sent": config.progress_sent,
        "progress_received": config.progress_received,
    }


STRATEGIES = [{"label": spec.label, "value": name} for name, spec in REGISTRY.items()]


def timeframe_label(name: str) -> str:
    """TradingView's button text: 1m, 5m, 1h, 4h, D."""
    minutes = Timeframe[name].value
    if minutes < 60:
        return f"{minutes}m"
    if minutes < 1440:
        return f"{minutes // 60}h"
    return "D" if minutes == 1440 else "W"


def _months_back(d: date, months: int) -> date:
    year, month = divmod(d.year * 12 + d.month - 1 - months, 12)
    month += 1
    last_day = (date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1)).day
    return date(year, month, min(d.day, last_day))


def quick_range(days: Sequence[date], key: str) -> tuple[date, date] | None:
    """(first, last) day of a quick range ending on the last cached day, limited to the run of
    consecutive cached days it ends in (a range over a missing day can't be shown)."""
    if not days:
        return None
    first, last = latest_run(days)
    starts = {
        "1M": _months_back(last, 1) + timedelta(days=1),
        "3M": _months_back(last, 3) + timedelta(days=1),
        "6M": _months_back(last, 6) + timedelta(days=1),
        "YTD": date(last.year, 1, 1),
        "1Y": last - timedelta(days=364),
        "All": first,
    }
    return max(starts[key], first), last


def _icon_button(id_: str, icon: str, title: str, pop: str | None = None, **kwargs):
    attrs = {"data-pop": pop} if pop else {}
    return html.Button(
        html.Span(className=f"tb-icon icon-{icon}"),
        id=id_,
        title=title,
        className="tb-btn",
        n_clicks=0,
        **attrs,
        **kwargs,
    )


def _popover(id_: str, title: str, children) -> html.Div:
    return html.Div(
        [html.Div(title, className="tb-pop-title"), *children], id=id_, className="tb-pop"
    )


def _switch(id_: str, label: str, value: list) -> dcc.Checklist:
    return dcc.Checklist(
        id=id_,
        options=[{"label": label, "value": "on"}],
        value=value,
        persistence=True,
        className="tb-check",
    )


TRADES_OVERLAY = ("trades", "trades.confluences")  # turned on by an old-form trade focus


def focus_from_query(search: str | None) -> dict | None:
    """The trade focus from the URL query (see the module docstring), or None."""
    return trade_focus.focus_from_query(search)


def focus_selection(focus: dict | None, overlay_types: list | None):
    """(symbol, overlays switch, overlay types) for a pending old-form focus (no order), else
    None: an order focus switches no overlay on."""
    if not focus or focus.get("done") or focus.get("order"):
        return None
    types = list(overlay_types or [])
    return focus["symbol"], ["on"], types + [t for t in TRADES_OVERLAY if t not in types]


def order_focus_pending(focus: dict | None) -> bool:
    """A focus with an order that the browser has not scrolled to yet."""
    return bool(focus and focus.get("order") and not focus.get("done"))


def focus_outputs(
    focus: dict | None,
    overlay_types: list | None,
    cached: Sequence[date],
    config: ChartConfig = DEFAULT_CONFIG,
    timeframes: Sequence[str] = TIMEFRAMES,
) -> tuple:
    """Outputs (symbol, timeframe, overlays switch, overlay types, chart-dates, order) of a
    pending trade focus; `no_update` for what it leaves alone, all of it without one. An order
    focus sets symbol, timeframe and days and the order (with a `note` if the trade's day is not
    cached: then the newest candles are shown); an old-form focus turns on the Trades overlay."""
    if not focus or focus.get("done"):
        return (no_update,) * 6
    order = focus.get("order")
    if order is None:
        symbol, switch, types = focus_selection(focus, overlay_types)
        return symbol, no_update, switch, types, no_update, None
    timeframe = focus.get("tf") if focus.get("tf") in timeframes else None
    found = trade_focus.focus_dates(cached, focus, config)
    note = None
    if found is None:
        note = "not in the cache"
        found = trade_focus.latest_dates(cached, timeframe or DEFAULT_TIMEFRAME, config)
    dates = {"start": found[0], "end": found[1]} if found else None
    return (
        focus["symbol"],
        timeframe or no_update,
        no_update,
        no_update,
        dates,
        {**order, "note": note} if note else order,
    )


def side_trade_focus(trade, folder: Path, n: int | None = None) -> dict:
    """The focus for a trade of the run `folder` (chart side panel, results page): its order on
    the run's timeframe. `n` (the click count) makes a second click on the same trade a change."""
    focus = trade_focus.focus_from_order(
        trade_focus.trade_order(trade), trade_focus.run_timeframe(folder, trade.symbol)
    )
    return focus if n is None else {**focus, "n": n}


def initial_dates(days: Sequence[date], symbol: str | None = None, focus: dict | None = None):
    """(start, end) ISO days shown when the symbol changes: the last month of cached days (the
    "1M" quick range; with years cached, all of them would be too many 5m candles), or a
    pending old-form trade focus's days for its symbol. None without cached days. More days are
    loaded by scrolling (`extend_dates`) and "Go to". (An order focus sets its days itself,
    `focus_outputs`.)"""
    if not days:
        return None
    first, last = quick_range(days, "1M")
    if focus and not focus.get("done") and not focus.get("order") and focus["symbol"] == symbol:
        return focus["from"], focus["to"]
    return first.isoformat(), last.isoformat()


def dates_of(data: dict | None) -> tuple[str | None, str | None]:
    """(start, end) ISO days of the `chart-dates` store ({"start", "end"}), None where unset."""
    data = data or {}
    return data.get("start"), data.get("end")


def overlay_controls() -> list:
    """The overlay switches in the Settings popover (user, 2026-10-19; before: the side panel's
    Overlays card, same ids): the master switch and one switch per overlay type."""
    return [
        dcc.Checklist(
            id="chart-overlays",
            options=[{"label": "Show overlays", "value": "on"}],
            value=[],
            persistence=True,
            className="ch-switches ch-master",
        ),
        dcc.Checklist(
            id="chart-overlay-types",
            options=overlay_options(enabled=False),
            value=[],
            persistence=True,
            className="ch-switches ch-types",
        ),
        html.Div(
            "Overlay types" if OVERLAYS else "No overlay types yet",
            id="chart-overlay-summary",
            className="ch-note",
        ),
    ]


def layout(
    sources: SymbolSources,
    config: ChartConfig = DEFAULT_CONFIG,
    focus: dict | None = None,
    results_dir: Path = RESULTS_DIR,
) -> html.Div:
    symbols = [s for s in sources.available_symbols() if s not in config.hidden_symbols]
    settings = _popover(
        "pop-settings",
        "Settings",
        [
            html.Details(
                [
                    html.Summary("Chart Settings"),
                    _switch("chart-sessions", "Session lines", ["on"]),
                    html.Div("Daily / weekly candles", className="tb-pop-sub"),
                    dcc.Dropdown(
                        id="chart-day-boundary",
                        options=[
                            {"label": f"Day from {b.value}", "value": b.name} for b in DayBoundary
                        ],
                        value=DEFAULT_BOUNDARY.name,
                        clearable=False,
                        searchable=False,
                        persistence=True,
                    ),
                    html.Div("4h candles", className="tb-pop-sub"),
                    dcc.Dropdown(
                        id="chart-h4-alignment",
                        options=[{"label": a.value, "value": a.name} for a in H4Alignment],
                        value=H4Alignment.UTC.name,
                        clearable=False,
                        searchable=False,
                        persistence=True,
                    ),
                    html.Div("Detector settings", className="tb-pop-sub"),
                    dcc.Checklist(
                        id="chart-filters",
                        options=[
                            {"label": "FVG strong-move filter", "value": "fvg"},
                            {"label": "OB strong-move filter", "value": "ob"},
                        ],
                        value=["ob"],
                        persistence=True,
                        className="tb-check",
                    ),
                    html.Div("Liquidity sweep (temporary)", className="tb-pop-sub tb-group"),
                    html.Div("Same-height high counts as the level", className="tb-pop-sub"),
                    dcc.Dropdown(
                        id="chart-sweep-tol",
                        options=[{"label": label, "value": v} for v, label in SWEEP_TOLERANCES],
                        value="none",
                        clearable=False,
                        searchable=False,
                        persistence=True,
                    ),
                    html.Div("Breakout filter", className="tb-pop-sub"),
                    dcc.Dropdown(
                        id="chart-sweep-cancel",
                        options=[
                            {"label": label, "value": k} for k, (label, _) in SWEEP_CANCELS.items()
                        ],
                        value="off",
                        clearable=False,
                        searchable=False,
                        persistence=True,
                    ),
                    html.Div("Highs / lows that count (last N swings)", className="tb-pop-sub"),
                    dcc.Dropdown(
                        id="chart-sweep-n",
                        options=[{"label": f"Last {n} swings", "value": n} for n in range(1, 6)],
                        value=SweepConfig().lookback_swings,
                        clearable=False,
                        searchable=False,
                        persistence=True,
                    ),
                    dcc.Checklist(
                        id="chart-sweep-top",
                        options=[
                            {"label": "BOS must break structure from before the top", "value": "on"}
                        ],
                        value=[],
                        persistence=True,
                        className="tb-check",
                    ),
                    html.Div(
                        "Tolerance in ATR of the shown timeframe. Applies to the Liquidity sweep "
                        "and Equilibrium overlays. Defaults = the current rules.",
                        className="tb-pop-note",
                    ),
                ],
                className="tb-details",
            ),
            html.Details(
                [html.Summary("Chart Overlays"), *overlay_controls()],
                className="tb-details tb-group",
            ),
        ],
    )
    strategy = _popover(
        "pop-strategy",
        "Strategy",
        [
            dcc.Dropdown(
                id="chart-strategy",
                options=STRATEGIES,
                value=STRATEGIES[0]["value"],
                clearable=False,
                searchable=False,
            ),
            html.Div(
                [html.Button("Settings…", className="tb-run", **{"data-modal": "st-modal"})],
                className="tb-pop-row",
            ),
            html.Div("Used by the Trades overlay and the backtest.", className="tb-pop-note"),
        ],
    )
    backtest = _popover(
        "pop-backtest",
        "Backtest",
        [
            html.Div("Symbols", className="tb-pop-sub"),
            dcc.Dropdown(id="bt-symbols", options=symbols, value=symbols[:1], multi=True),
            html.Div("Days (UTC)", className="tb-pop-sub"),
            dcc.DatePickerRange(id="bt-dates", display_format="YYYY-MM-DD", first_day_of_week=1),
            html.Div("Settings preset", className="tb-pop-sub"),
            dcc.Dropdown(
                id="bt-preset",
                options=settings_panel.preset_options([settings_panel.DEFAULT_PRESET]),
                value=settings_panel.DEFAULT_PRESET,
                clearable=False,
                searchable=False,
            ),
            html.Div(id="bt-preset-note", className="tb-pop-note"),
            html.Div(
                [html.Button("Run", id="bt-run", className="tb-run", n_clicks=0)],
                className="tb-pop-row",
            ),
            html.Div(id="bt-status", className="tb-pop-note"),
        ],
    )
    toolbar = html.Div(
        [
            dcc.Dropdown(
                id="chart-symbol",
                options=symbols,
                value=symbols[0] if symbols else None,
                clearable=False,
                searchable=True,
                persistence=True,
                placeholder="No symbols in the cache",
                className="tb-symbol",
            ),
            html.Div(className="tb-sep"),
            dcc.RadioItems(
                id="chart-timeframe",
                options=[{"label": timeframe_label(tf), "value": tf} for tf in TIMEFRAMES],
                value=DEFAULT_TIMEFRAME,
                persistence=True,
                className="tb-timeframes",
            ),
            html.Div(className="tb-sep"),
            html.Div(
                [
                    _icon_button("tb-settings", "settings", "Chart settings", "pop-settings"),
                    settings,
                ],
                className="tb-anchor",
            ),
            html.Div(
                [_icon_button("tb-strategy", "strategy", "Strategy", "pop-strategy"), strategy],
                className="tb-anchor",
            ),
            _icon_button("chart-replay-toggle", "replay", "Bar replay (on / off)"),
            html.Div(
                [_icon_button("tb-backtest", "backtest", "Backtest", "pop-backtest"), backtest],
                className="tb-anchor",
            ),
            html.Div(className="tb-sep"),
            _icon_button("tb-zoom", "zoom", "Zoom: drag a rectangle on the chart"),
            _icon_button("tb-zoom-reset", "zoom-reset", "Reset zoom (or double-click the chart)"),
            html.Div(className="tb-sep"),
            *update_button.layout(),
            html.Div(className="tb-spacer"),
            html.Div(
                [
                    _icon_button("shot-save", "camera", "Save a picture of the chart (PNG)"),
                    html.Button(
                        "▾",
                        title="Picture options",
                        className="tb-btn tb-caret",
                        n_clicks=0,
                        **{"data-pop": "pop-shot"},
                    ),
                    _popover(
                        "pop-shot",
                        "Picture of the chart",
                        [
                            html.Button(
                                "Download PNG",
                                id="shot-menu-save",
                                className="tb-menu-item",
                                n_clicks=0,
                            ),
                            html.Button(
                                "Copy to clipboard",
                                id="shot-copy",
                                className="tb-menu-item",
                                n_clicks=0,
                            ),
                            html.Div(id="shot-status", className="tb-pop-note"),
                        ],
                    ),
                ],
                className="tb-anchor tb-shot",
            ),
        ],
        className="tb-bar tb-top",
    )
    replay_bar = html.Div(
        [
            html.Button("Select bar", id="chart-replay-pick", title="Click a candle to start at"),
            html.Button("⏮", id="chart-replay-start", title="Back to the start candle"),
            html.Button("◀", id="chart-replay-back", title="One candle back"),
            html.Button("▶", id="chart-replay-play", title="Play / pause"),
            html.Button("▶|", id="chart-replay-forward", title="One candle forward"),
            dcc.Dropdown(
                id="chart-replay-speed",
                options=[{"label": f"{s}/s", "value": s} for s in config.replay_speeds],
                value=config.replay_default_speed,
                clearable=False,
                searchable=False,
                className="tb-speed",
            ),
            html.Button("✕", id="chart-replay-exit", title="Exit replay"),
        ],
        id="chart-replay-controls",
        className="tb-replay",
        style={"display": "none"},
    )
    bottom = html.Div(
        [
            html.Span(
                className="tb-icon icon-goto tb-cal-icon",
                title="Go to a UTC date / time (Alt+G), e.g. 2026-09-12 12:15",
            ),
            dcc.Input(
                id="chart-goto-input",
                type="text",
                placeholder="Go to 2026-09-12 12:15",
                debounce=True,
                className="tb-goto",
            ),
            html.Div(
                [html.Span(id="chart-message"), html.Span(id="chart-notes")],
                className="tb-message",
            ),
            html.Span(
                [
                    html.Span(id="chart-order-text"),
                    html.Button(
                        "✕",
                        id="chart-order-clear",
                        title="Remove the trade from the chart",
                        n_clicks=0,
                    ),
                ],
                id="chart-order-chip",
                className="tb-chip",
                style={"display": "none"},
            ),
            html.Span("UTC", className="tb-utc"),
        ],
        className="tb-bar tb-bottom",
    )
    return html.Div(
        [
            toolbar,
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(id="chart-lwc"),
                                    html.Div(
                                        [
                                            html.Div(id="chart-bar-fill", className="ch-bar-fill"),
                                            html.Span(id="chart-bar-pct", className="ch-bar-pct"),
                                        ],
                                        id="chart-bar",
                                        className="ch-bar",
                                    ),
                                    replay_bar,
                                ],
                                className="tb-chart",
                            ),
                            bottom,
                        ],
                        className="ch-chartcol",
                    ),
                    chart_side.panel(chart_side.run_summary(results_dir)),
                    # Slim right-edge strip like TradingView's widget bar: always there.
                    html.Div(
                        _icon_button("side-toggle", "panel", "Show / hide the side panel"),
                        id="ch-strip",
                        className="ch-strip",
                    ),
                ],
                id="ch-main",
                className=chart_side.main_class(False),
            ),
            dcc.Store(id="chart-range"),
            dcc.Store(id="chart-dates"),
            dcc.Store(id="chart-more"),
            dcc.Store(id="st-reset-click"),
            dcc.Store(id="st-apply"),
            dcc.Store(id="side-collapsed", storage_type="local"),
            dcc.Store(id="chart-config", data=chart_settings(config)),
            dcc.Store(id="chart-sweep-tweak"),
            dcc.Store(id="chart-base"),
            dcc.Store(id="chart-base-done"),
            dcc.Store(id="chart-need"),
            dcc.Store(id="chart-ovl"),
            dcc.Store(id="chart-delta"),
            dcc.Store(id="chart-view"),
            dcc.Store(id="chart-click"),
            dcc.Store(id="chart-resync"),
            dcc.Store(id="chart-replay", data=REPLAY_OFF),
            dcc.Store(id="chart-replay-mode", data={"on": False, "picking": False}),
            dcc.Store(id="chart-replay-span"),
            dcc.Store(id="chart-focus", data=focus),
            dcc.Store(id="chart-order"),
            dcc.Store(id="chart-bot-seen", storage_type="local", data=[]),
            dcc.Store(id="chart-order-draw"),
            dcc.Store(id="chart-order-done"),
            dcc.Store(id="chart-viewport"),
            dcc.Store(id="chart-goto"),
            dcc.Store(id="settings-current", storage_type="local"),
            settings_panel.layout(),
            dcc.Interval(
                id="chart-replay-timer",
                interval=1000 // config.replay_default_speed,
                disabled=True,
            ),
        ],
        className="tb-page ch-page",
    )


def register_callbacks(
    app: Dash,
    sources: SymbolSources,
    config: ChartConfig = DEFAULT_CONFIG,
    results_dir: Path = RESULTS_DIR,
) -> None:
    settings_panel.register_callbacks(app)
    update_button.register_callbacks(app)

    @app.callback(
        Output("chart-dates", "data"),
        Input("chart-symbol", "value"),
        State("chart-focus", "data"),
    )
    def _initial_dates(symbol, focus):
        """A new symbol starts on its last month (or an old-form trade focus's days); an order
        focus sets its own days (`_focus`)."""
        if order_focus_pending(focus):
            return no_update
        found = initial_dates(sources.cached_days(symbol) if symbol else [], symbol, focus)
        return {"start": found[0], "end": found[1]} if found else None

    @app.callback(
        Output("chart-dates", "data", allow_duplicate=True),
        Input("chart-timeframe", "value"),
        State("chart-viewport", "data"),
        State("chart-symbol", "value"),
        State("chart-dates", "data"),
        State("chart-replay", "data"),
        State("chart-focus", "data"),
        prevent_initial_call=True,
    )
    def _timeframe_days(timeframe, view, symbol, dates, replay_state, focus):
        """Keep the view on a timeframe switch: load the days it needs (outside replay)."""
        if order_focus_pending(focus):
            return no_update  # the trade focus loads its own days with the timeframe
        start, end = dates_of(dates)
        if not (view and timeframe and start and end) or view.get("symbol") != symbol:
            return no_update
        if replay_state and replay_state.get("on"):
            return no_update
        found = dates_for_view(
            sources.cached_days(symbol),
            date.fromisoformat(start[:10]),
            date.fromisoformat(end[:10]),
            view,
            Timeframe[timeframe],
            config,
        )
        if found is None:
            return no_update
        return {"start": found[0].isoformat(), "end": found[1].isoformat()}

    @app.callback(
        Output("chart-dates", "data", allow_duplicate=True),
        Input("chart-more", "data"),
        State("chart-symbol", "value"),
        State("chart-timeframe", "value"),
        State("chart-dates", "data"),
        State("chart-replay", "data"),
        State("chart-day-boundary", "value"),
        State("chart-h4-alignment", "value"),
        prevent_initial_call=True,
    )
    def _more(request, symbol, timeframe, dates, replay_state, boundary, h4):
        """The view came near an edge of the loaded candles: load the next days there."""
        start, end = dates_of(dates)
        if not (request and symbol and timeframe and start and end):
            return no_update
        if replay_state and replay_state.get("on"):
            return no_update
        cfg = with_boundary(config, boundary, h4)
        if request.get("key") != chart_key(symbol, timeframe, start, end, cfg):
            return no_update  # asked for other candles than the ones shown now
        found = extend_dates(
            sources.cached_days(symbol),
            date.fromisoformat(start[:10]),
            date.fromisoformat(end[:10]),
            request.get("side"),
            Timeframe[timeframe],
            request.get("view"),
            cfg,
        )
        if found is None:
            return no_update
        return {"start": found[0].isoformat(), "end": found[1].isoformat()}

    @app.callback(
        Output("chart-goto", "data"),
        Output("chart-dates", "data", allow_duplicate=True),
        Output("chart-message", "children", allow_duplicate=True),
        Input("chart-goto-input", "n_submit"),
        State("chart-goto-input", "value"),
        State("chart-symbol", "value"),
        State("chart-timeframe", "value"),
        State("chart-dates", "data"),
        State("chart-replay", "data"),
        prevent_initial_call=True,
    )
    def _goto(n_submit, text, symbol, timeframe, dates, replay_state):
        """Go to a UTC time: load its days if needed; the browser centres on it."""
        at = parse_goto(text)
        start, end = dates_of(dates)
        if not n_submit or not (symbol and timeframe and start and end):
            return no_update, no_update, no_update
        if at is None:
            message = f"Go to: {text!r} is not a UTC time like 2026-09-12 12:15."
            return no_update, no_update, message
        found = goto_outputs(
            at, symbol, timeframe, start, end, replay_state, n_submit,
            sources.cached_days(symbol), config,
        )  # fmt: skip
        return _packed(found)

    @app.callback(
        Output("chart-focus", "data", allow_duplicate=True),
        Output("chart-message", "children", allow_duplicate=True),
        Input({"type": "side-trade", "index": ALL}, "n_clicks"),
        State("chart-replay", "data"),
        prevent_initial_call=True,
    )
    def _focus_trade(_clicks, replay_state):
        """A click on a trade in "Trades in view": open its order on the run's timeframe."""
        trig = ctx.triggered[0] if ctx.triggered else None
        folder = chart_side.newest_run(results_dir)
        if not trig or not trig["value"] or folder is None:
            return (no_update,) * 2
        if replay_state and replay_state.get("on"):
            return no_update, "Leave the replay to open a trade."
        by_id = {t.id: t for t in chart_side.run_trades(folder)}
        trade = by_id.get(ctx.triggered_id["index"])
        if trade is None:
            return (no_update,) * 2
        return side_trade_focus(trade, folder, trig["value"]), no_update

    @app.callback(
        Output("side-trades", "children"),
        Input("chart-range", "data"),
        Input("chart-symbol", "value"),
        Input("chart-replay", "data"),
    )
    def _side_trades(rng, symbol, replay_state):
        """Trades of the newest run whose entry is inside the visible range."""
        if replay_state and replay_state.get("on"):
            return html.Div("Trades in view are hidden during replay.", className="side-empty")
        folder = chart_side.newest_run(results_dir)
        if folder is None:
            return chart_side.trades_body([], has_run=False)
        times = chart_side.view_times(rng)
        if times is None or not rng or rng.get("symbol") != symbol:
            return chart_side.trades_body([])
        found = chart_side.trades_in_view(chart_side.run_trades(folder), symbol, *times)
        return chart_side.trades_body(found)

    @app.callback(
        Output("side-collapsed", "data"),
        Input("side-toggle", "n_clicks"),
        State("side-collapsed", "data"),
        prevent_initial_call=True,
    )
    def _side_toggle(clicks, collapsed):
        return chart_side.collapsed_after(clicks, collapsed)

    @app.callback(
        Output("ch-main", "className"),
        Output("side-toggle", "className"),
        Input("side-collapsed", "data"),
    )
    def _side_apply(collapsed):
        return chart_side.main_class(collapsed), "tb-btn" if collapsed else "tb-btn active"

    app.clientside_callback(
        ClientsideFunction("chart", "goto"),
        Output("chart-goto", "data", allow_duplicate=True),
        Input("chart-goto", "data"),
        Input("chart-base-done", "data"),
        prevent_initial_call=True,
    )

    @app.callback(
        Output("chart-symbol", "value"),
        Output("chart-timeframe", "value"),
        Output("chart-overlays", "value"),
        Output("chart-overlay-types", "value"),
        Output("chart-dates", "data", allow_duplicate=True),
        Output("chart-order", "data"),
        Input("chart-focus", "data"),
        State("chart-overlay-types", "value"),
        prevent_initial_call="initial_duplicate",
    )
    def _focus(focus, overlay_types):
        """A trade focus: symbol, timeframe, days and the order (or, old form, the Trades
        overlay)."""
        symbol = focus.get("symbol") if focus else None
        cached = sources.cached_days(symbol) if symbol else []
        return focus_outputs(focus, overlay_types, cached, config)

    @app.callback(
        Output("chart-overlays", "value", allow_duplicate=True),
        Output("chart-overlay-types", "value", allow_duplicate=True),
        Output("chart-bot-seen", "data"),
        Input("chart-symbol", "value"),
        State("chart-overlay-types", "value"),
        State("chart-overlays", "value"),
        State("chart-bot-seen", "data"),
        prevent_initial_call="initial_duplicate",
    )
    def _bot_overlay_default(symbol, types, master, seen):
        """Bot trades on by default: switched on once for each symbol the bot trades (the
        user's later choice stays)."""
        chosen = bot_overlay.default_selection(
            symbol, types or [], master or [], seen or [], bot_overlay.bot_symbols()
        )
        return no_update if chosen is None else chosen

    @app.callback(
        Output("chart-order", "data", allow_duplicate=True),
        Input("chart-order-clear", "n_clicks"),
        Input("chart-symbol", "value"),
        State("chart-order", "data"),
        prevent_initial_call=True,
    )
    def _clear_order(clicks, symbol, order):
        """The order stays until another symbol is picked or its ✕ is pressed."""
        if not order:
            return no_update
        if ctx.triggered_id == "chart-order-clear":
            return None if clicks else no_update
        return None if order.get("symbol") != symbol else no_update

    @app.callback(
        Output("chart-order-text", "children"),
        Output("chart-order-chip", "style"),
        Input("chart-order", "data"),
    )
    def _order_chip(order):
        shown = {"display": "inline-flex"} if order else {"display": "none"}
        return (trade_focus.chip_text(order, order.get("note")) if order else ""), shown

    @app.callback(
        Output("chart-order-draw", "data"),
        Input("chart-base-done", "data"),
        Input("chart-order", "data"),
        State("chart-symbol", "value"),
        State("chart-timeframe", "value"),
        State("chart-dates", "data"),
        State("chart-replay", "data"),
        State("chart-day-boundary", "value"),
        State("chart-h4-alignment", "value"),
    )
    def _order_draw(_done, order, symbol, timeframe, dates, replay_state, boundary, h4):
        """The order as drawings on the loaded candles (not during replay: it would show the
        future)."""
        start, end = dates_of(dates)
        cfg = with_boundary(config, boundary, h4)
        folder = chart_side.newest_run(results_dir)
        trades = chart_side.run_trades(folder) if folder is not None else ()
        return order_draw_payload(
            sources, order, symbol, timeframe, start, end, replay_state, cfg, trades
        )

    app.clientside_callback(
        ClientsideFunction("chart", "order"),
        Output("chart-order-done", "data"),
        Input("chart-order-draw", "data"),
    )
    app.clientside_callback(
        ClientsideFunction("chart", "focus"),
        Output("chart-focus", "data"),
        Input("chart-base-done", "data"),
        State("chart-focus", "data"),
    )

    @app.callback(
        Output("chart-base", "data"),
        Output("chart-message", "children"),
        Input("chart-symbol", "value"),
        Input("chart-timeframe", "value"),
        Input("chart-dates", "data"),
        Input("chart-replay-mode", "data"),
        Input("chart-resync", "data"),
        Input("chart-day-boundary", "value"),
        Input("chart-h4-alignment", "value"),
        State("chart-replay", "data"),
        State("chart-replay-span", "data"),
    )
    def _base(symbol, timeframe, dates, _mode, _resync, boundary, h4, replay_state, span):
        start_date, end_date = dates_of(dates)
        cfg = with_boundary(config, boundary, h4)
        return base_payload(
            sources, symbol, timeframe, start_date, end_date, replay_state, span, cfg
        )

    @app.callback(
        Output("chart-ovl", "data"),
        Input("chart-need", "data"),
        State("chart-symbol", "value"),
        State("chart-timeframe", "value"),
        State("chart-dates", "data"),
        State("chart-filters", "value"),
        State("settings-current", "data"),
        State("chart-day-boundary", "value"),
        State("chart-h4-alignment", "value"),
        State("chart-sweep-tweak", "data"),
        prevent_initial_call=True,
    )
    def _overlays(request, symbol, timeframe, dates, filters, store, boundary, h4, sweep_tweak):
        start_date, end_date = dates_of(dates)
        strategy = settings_panel.store_json(store)
        cfg = with_boundary(config, boundary, h4)
        payload = overlay_payload(
            sources, request, symbol, timeframe, start_date, end_date, filters, cfg, strategy,
            sweep_tweak,
        )  # fmt: skip
        return payload if payload is not None else no_update

    app.clientside_callback(  # the loading bar (chart.js): a new base is on its way
        ClientsideFunction("chart", "loading"),
        Output("chart-bar", "title"),
        Input("chart-symbol", "value"),
        Input("chart-timeframe", "value"),
        Input("chart-dates", "data"),
        Input("chart-replay-mode", "data"),
        Input("chart-day-boundary", "value"),
        Input("chart-h4-alignment", "value"),
    )
    app.clientside_callback(
        ClientsideFunction("chart", "base"),
        Output("chart-base-done", "data"),
        Input("chart-base", "data"),
        State("chart-config", "data"),
    )
    app.clientside_callback(
        ClientsideFunction("chart", "select"),
        Output("chart-need", "data"),
        Input("chart-overlays", "value"),
        Input("chart-overlay-types", "value"),
        Input("chart-filters", "value"),
        Input("chart-sessions", "value"),
        Input("chart-base-done", "data"),
        Input("settings-current", "data"),
        Input("chart-sweep-tweak", "data"),
    )
    app.clientside_callback(
        ClientsideFunction("chart", "overlays"),
        Output("chart-need", "data", allow_duplicate=True),
        Input("chart-ovl", "data"),
        prevent_initial_call=True,
    )
    app.clientside_callback(
        ClientsideFunction("chart", "shot"),
        Output("shot-status", "children"),
        Input("shot-save", "n_clicks"),
        Input("shot-menu-save", "n_clicks"),
        Input("shot-copy", "n_clicks"),
        State("chart-overlays", "value"),
        State("chart-overlay-types", "value"),
        State("chart-overlay-types", "options"),
        State("settings-current", "data"),
        State("bt-preset-note", "children"),
        prevent_initial_call=True,
    )
    app.clientside_callback(
        ClientsideFunction("chart", "delta"),
        Output("chart-resync", "data"),
        Input("chart-delta", "data"),
        prevent_initial_call=True,
    )

    @app.callback(
        Output("chart-replay", "data"),
        Output("chart-replay-mode", "data"),
        Output("chart-replay-span", "data", allow_duplicate=True),
        Output("chart-delta", "data"),
        Output("chart-message", "children", allow_duplicate=True),
        Output("chart-replay-timer", "disabled"),
        Output("chart-replay-play", "children"),
        Output("chart-replay-controls", "style"),
        Output("chart-replay-toggle", "className"),
        Input("chart-replay-toggle", "n_clicks"),
        Input("chart-replay-exit", "n_clicks"),
        Input("chart-replay-pick", "n_clicks"),
        Input("chart-replay-start", "n_clicks"),
        Input("chart-replay-back", "n_clicks"),
        Input("chart-replay-forward", "n_clicks"),
        Input("chart-replay-play", "n_clicks"),
        Input("chart-replay-timer", "n_intervals"),
        Input("chart-click", "data"),
        Input("chart-symbol", "value"),
        Input("chart-timeframe", "value"),
        Input("chart-dates", "data"),
        State("chart-replay", "data"),
        State("chart-replay-controls", "style"),
        State("chart-view", "data"),
        State("chart-filters", "value"),
        State("settings-current", "data"),
        State("chart-day-boundary", "value"),
        State("chart-h4-alignment", "value"),
        State("chart-sweep-tweak", "data"),
        prevent_initial_call=True,
    )
    def _replay_control(*args):
        symbol, timeframe, dates, state, controls_style, view, filters = args[-11:-4]
        start_date, end_date = dates_of(dates)
        strategy = settings_panel.store_json(args[-4])
        cfg = with_boundary(config, args[-3], args[-2])
        sweep_tweak = args[-1]
        action = _REPLAY_ACTIONS.get(ctx.triggered_id, "data")
        replay, _ = load_replay(sources, symbol, timeframe, start_date, end_date, cfg)
        clicked = ctx.triggered[0]["value"] if action == "click" else None
        clicked_x = clicked.get("x") if isinstance(clicked, dict) else None
        new = replay_step(action, state, replay, clicked_x)
        # replay switched on: the span starts at the default of the shown timeframe
        started = action == "toggle" and new["on"]
        mode = {"on": new["on"], "picking": new["picking"]}
        mode_changed = mode != {"on": state["on"], "picking": state["picking"]}
        delta, message = no_update, no_update
        stepping = new["on"] and not new["picking"] and not mode_changed and action != "data"
        if stepping and replay is not None and new["now"] != state["now"]:
            cursor = replay.cursor_at(datetime.fromisoformat(new["now"]))
            key = chart_key(symbol, timeframe, start_date, end_date, cfg)
            found = replay_delta(
                sources, view, replay, cursor, key, filters, cfg, strategy, sweep_tweak
            )
            if found is not None:
                delta, message = found, replay_message(replay, cursor)
        # only what changed, so a replay step re-renders nothing but the chart and message
        playing = new["playing"] != state["playing"]
        on = new["on"] != state["on"]
        return (
            new if new != state else no_update,
            mode if mode_changed else no_update,
            default_span(Timeframe[timeframe], config) if started else no_update,
            delta,
            message,
            not new["playing"] if playing else no_update,
            ("❚❚" if new["playing"] else "▶") if playing else no_update,
            {**controls_style, "display": "flex" if new["on"] else "none"} if on else no_update,
            ("tb-btn active" if new["on"] else "tb-btn") if on else no_update,
        )

    @app.callback(
        Output("chart-sweep-tweak", "data"),
        Input("chart-sweep-tol", "value"),
        Input("chart-sweep-cancel", "value"),
        Input("chart-sweep-n", "value"),
        Input("chart-sweep-top", "value"),
    )
    def _sweep_tweak(tol, cancel, n, top):
        return {"tol": tol, "cancel": cancel, "n": n, "top": bool(top)}

    @app.callback(
        Output("chart-overlay-types", "options"),
        Output("chart-overlay-summary", "children"),
        Input("chart-overlays", "value"),
        Input("chart-overlay-types", "value"),
    )
    def _overlay_panel(overlays_switch, overlay_types):
        selected = overlay_types or []
        if not OVERLAYS:
            return [], "No overlay types yet"
        return overlay_options(selected, bool(overlays_switch)), overlay_summary(selected)

    @app.callback(Output("chart-replay-timer", "interval"), Input("chart-replay-speed", "value"))
    def _speed(speed):
        return 1000 // speed

    @app.callback(
        Output("bt-symbols", "value"),
        Output("bt-dates", "start_date"),
        Output("bt-dates", "end_date"),
        Output("bt-dates", "min_date_allowed"),
        Output("bt-dates", "max_date_allowed"),
        Input("chart-symbol", "value"),
        Input("chart-dates", "data"),
    )
    def _backtest_defaults(symbol, dates):
        """The backtest starts out with the chart's symbol and days."""
        days = sources.cached_days(symbol) if symbol else []
        start, end = dates_of(dates)
        low, high = (days[0].isoformat(), days[-1].isoformat()) if days else (None, None)
        return [symbol] if symbol else [], start, end, low, high

    @app.callback(
        Output("bt-status", "children"),
        Output("url", "pathname"),
        Input("bt-run", "n_clicks"),
        State("bt-symbols", "value"),
        State("bt-dates", "start_date"),
        State("bt-dates", "end_date"),
        State("settings-current", "data"),
        prevent_initial_call=True,
    )
    def _backtest(run, symbols, start, end, store):
        if not run:  # fired when the page is built (n_clicks 0), not a click
            return no_update, no_update
        settings = settings_panel.store_settings(store)
        preset = settings_panel.preset_label(store)
        return start_backtest(sources, symbols, start, end, settings=settings, preset=preset)


_REPLAY_ACTIONS = {
    "chart-replay-toggle": "toggle",
    "chart-replay-exit": "toggle",
    "chart-replay-pick": "pick",
    "chart-replay-start": "start",
    "chart-replay-back": "back",
    "chart-replay-forward": "forward",
    "chart-replay-play": "play",
    "chart-replay-timer": "tick",
    "chart-click": "click",
}


def selected_overlays(switch: list | None, types: list | None) -> list[str]:
    """Overlay types to draw: none while the switch is off (the chart starts empty)."""
    return list(types or []) if switch else []


def _iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _midnight(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=UTC)
