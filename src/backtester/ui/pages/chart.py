"""Chart page: TradingView-like candlesticks from the M1 cache. Spec: ROADMAP.md › 1.1, 4.0a.

The chart is TradingView Lightweight Charts in the browser (`ui/assets/chart.js`, created
once and kept). The server only sends data (`ui/chart_data.py`), through stores:
`chart-base` = candles up to the cursor and session lines (a new symbol, timeframe, range
or replay mode); `chart-ovl` = the drawings of the overlay types the browser asked for in
`chart-need` (types it doesn't have yet for this range and filter setting); `chart-delta`
= one replay step from the browser's cursor (`chart-view`, written by the browser) to the
next. Showing / hiding overlays, sub-entries and session lines happens in the browser.

Pick symbol (every symbol of `SymbolSources` with cached days, each read from its own
source's cache, `data/sources.py`), timeframe and a date range (UTC days, both
inclusive, limited to cached days). A range touching a day that was never downloaded shows
the `MissingCacheError` instead of a chart, so gaps in the cache are never silent.
Zooming or panning is the library's; the price axis fits the visible candles.

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

Overlays (ROADMAP.md › Phase 2): the chart starts empty. The "Overlays" switch turns the
detector overlays on and the "Overlay types" panel next to it (opens like a dropdown) picks
which types are drawn: one checkbox per registered `OverlayType` in roadmap order, see
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

Trades (ROADMAP.md › 3.3b): the "Trades" overlay runs strategy 1 and the engine on the
shown symbol and range (with warm-up) and draws position boxes, see `ui/trades_overlay.py`.
It and the backtest use the settings panel's current settings (ROADMAP.md › 4.1,
`ui/settings_panel.py`, store `settings-current`); the browser re-requests the overlays
when their key changes.
Overlays that load their own data (`OverlayType.needs_sources`) get the page's sources.

Focus on one trade (ROADMAP.md › 3.6, from the results page's trade list):
`/?symbol=…&from=…&to=…&t0=…&t1=…` selects the symbol and the UTC days from..to, turns on
the Trades overlay with its confluences and, once the candles are drawn, scrolls the chart
to the trade (t0 = entry candle, t1 = exit time). Applied once; the store `chart-focus` is
then marked done, so later changes of symbol or days are the user's again.

Timeframe switch (ROADMAP.md › 4.0b part 1), outside replay: the time at the centre of
the view stays at the centre and the number of visible candles stays the same (the browser
reports its view in `chart-viewport`; `chart.js` re-centres after the new candles). The
days the new view needs are added to the shown range (`dates_for_view`), so a switch up
shows as many candles as before. In replay the replay time is kept (as before).

Screenshot (ROADMAP.md › 4.0b part 3): the camera button (top right) saves a PNG of the
chart as shown, with a stamp (symbol, timeframe, first → last visible candle in UTC, the
replay time, the overlays that are on, the settings preset) and the same data in the file
name; "▾" also offers copying it to the clipboard. All in the browser (`chart.js` `shot`).

Later steps add: the session view (3.5).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache
from urllib.parse import parse_qs
from uuid import uuid4

from dash import ClientsideFunction, Dash, Input, Output, State, ctx, dcc, html, no_update

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.data.adapters.cache_adapter import (
    MissingCacheError,
    candles_from_frame,
    latest_run,
)
from backtester.data.resample import CALENDAR, DEFAULT_BOUNDARY, DayBoundary, supported
from backtester.data.sources import SymbolSources, cached_block, warmup_start
from backtester.engine.replay import Replay
from backtester.runner import BackgroundRun, RunSettings, start_run
from backtester.ui import (
    bos_overlay,  # noqa: F401  (registers the BOS + trend overlay)
    bpr_overlay,  # noqa: F401  (registers the BPR overlay)
    fvg_overlay,  # noqa: F401  (registers the FVG overlay)
    ob_overlay,  # noqa: F401  (registers the Order block overlay)
    session_zone_overlay,  # noqa: F401  (registers the Session zones overlay)
    settings_panel,
    sweep_overlay,  # noqa: F401  (registers the Liquidity sweep overlay)
    swing_overlay,  # noqa: F401  (registers the Swings overlay)
    trades_overlay,  # noqa: F401  (registers the Trades overlay)
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
    try:
        frame = sources.adapter(symbol).fetch_frame(
            symbol,
            Timeframe[timeframe],
            _midnight(start),
            _midnight(end + timedelta(days=1)),
            config.day_boundary,
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
def _cached_replay(sources, symbol, timeframe, start_date, end_date, config):
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
    return _cached_replay(sources, symbol, timeframe, start_date, end_date, config)


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
    D / W candles also depend on the day boundary."""
    key = f"{symbol}|{timeframe}|{start_date}|{end_date}"
    if timeframe in CALENDAR_NAMES and config.day_boundary is not DEFAULT_BOUNDARY:
        key += f"|{config.day_boundary.name}"
    return key


def with_boundary(config: ChartConfig, boundary: str | None) -> ChartConfig:
    """The chart config with the day boundary chosen in the chart settings."""
    if not boundary or boundary not in DayBoundary.__members__:
        return config
    return replace(config, day_boundary=DayBoundary[boundary])


def overlay_settings(filters: Sequence[str] | None, strategy: str = "") -> OverlaySettings:
    """The chart's detector switches + the strategy settings (canonical JSON, "" = spec
    defaults; `settings_panel.store_json`)."""
    filters = filters or []
    return OverlaySettings(
        fvg_strong_move_filter="fvg" in filters,
        ob_strong_move_filter="ob" in filters,
        strategy=strategy,
    )


@lru_cache(maxsize=16)
def chart_data(
    replay: Replay,
    settings: OverlaySettings = DEFAULT_SETTINGS,
    sources: SymbolSources | None = None,
    config: ChartConfig = DEFAULT_CONFIG,
) -> ChartData:
    """Payload builder for one loaded range and detector setting (kept for replay steps)."""
    return ChartData(replay, lambda o: _cached_events(replay, o, settings, sources), config)


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
) -> dict | None:
    """Full drawings of the requested overlay types at the browser's cursor, or None if
    the request is for other candles than the ones selected now."""
    if not request or request["key"] != chart_key(symbol, timeframe, start_date, end_date, config):
        return None
    replay, _ = load_replay(sources, symbol, timeframe, start_date, end_date, config)
    if replay is None or not 0 <= request["cursor"] < len(replay):
        return None
    data = chart_data(replay, overlay_settings(filters, strategy), sources, config)
    return {
        **data.full(request["types"], request["cursor"]),
        "key": request["key"],
        "filters": request["filters"],
        "requested": request["types"],
        "order": list(OVERLAYS),
    }


def replay_delta(
    sources: SymbolSources,
    view: dict | None,
    replay: Replay,
    cursor: int,
    key: str,
    filters,
    config: ChartConfig = DEFAULT_CONFIG,
    strategy: str = "",
) -> dict | None:
    """Delta from what the browser shows (`view`: key, cursor, loaded types) to `cursor`."""
    if not view or view.get("key") != key or view.get("cursor") is None:
        return None
    frm = view["cursor"]
    if not 0 <= frm < len(replay):
        return None
    data = chart_data(replay, overlay_settings(filters, strategy), sources, config)
    return {**data.delta(view.get("types") or [], frm, cursor), "key": key}


# --- backtest from the toolbar (ROADMAP 4.0, runner.start_run) ---------------------------

_RUNS: dict[str, BackgroundRun] = {}  # running backtests by job id (this server process)


def start_backtest(
    sources: SymbolSources,
    symbols,
    start_date,
    end_date,
    start=start_run,
    settings: RunSettings | None = None,
    preset: str | None = None,
):
    """Outputs of the backtest callback after "Run": (job, timer disabled, status, bar
    style, page). The run goes on in a background thread with `settings` (the settings
    panel's current ones); `poll_backtest` follows it."""
    if not symbols or not start_date or not end_date:
        return no_update, True, "Pick one or more symbols and the days.", {"width": "0%"}, no_update
    job = uuid4().hex
    first, last = date.fromisoformat(start_date[:10]), date.fromisoformat(end_date[:10])
    _RUNS[job] = start(
        list(symbols), first, last, settings=settings, sources=sources, preset=preset
    )
    return {"id": job}, False, f"Running {', '.join(symbols)} …", {"width": "0%"}, no_update


def poll_backtest(job: dict | None):
    """Progress of the running backtest; when it is done, open its results page."""
    run = _RUNS.get(job["id"]) if job else None
    if run is None:
        return no_update, True, no_update, no_update, no_update
    if not run.finished:
        share = run.done / run.total if run.total else 0.0
        status = f"{run.done:,} of {run.total:,} candles" if run.total else "Loading candles …"
        return no_update, False, status, {"width": f"{share:.0%}"}, no_update
    del _RUNS[job["id"]]
    if run.error is not None:
        return None, True, f"Failed: {run.error}", {"width": "0%"}, no_update
    name = run.folder.name
    return None, True, f"Done: results/{name}", {"width": "100%"}, f"/results/{name}"


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
    }


QUICK_RANGES = ("1M", "3M", "6M", "YTD", "1Y", "All")
STRATEGIES = [{"label": "Strategy 1 · Session zone sweep", "value": "session_zone_sweep"}]


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


TRADES_OVERLAY = ("trades", "trades.confluences")  # turned on by a trade focus


def focus_from_query(search: str | None) -> dict | None:
    """The trade focus from the URL query (see the module docstring), or None."""
    query = {k: v[0] for k, v in parse_qs((search or "").lstrip("?")).items()}
    try:
        focus = {
            "symbol": query["symbol"],
            "from": date.fromisoformat(query["from"]).isoformat(),
            "to": date.fromisoformat(query["to"]).isoformat(),
            "t0": datetime.fromisoformat(query["t0"]).isoformat(),
            "t1": datetime.fromisoformat(query["t1"]).isoformat(),
        }
    except (KeyError, ValueError):
        return None
    return focus if focus["from"] <= focus["to"] else None


def focus_selection(focus: dict | None, overlay_types: list | None):
    """(symbol, overlays switch, overlay types) for a pending focus, else None."""
    if not focus or focus.get("done"):
        return None
    types = list(overlay_types or [])
    return focus["symbol"], ["on"], types + [t for t in TRADES_OVERLAY if t not in types]


def date_limits(days: Sequence[date], symbol: str | None = None, focus: dict | None = None):
    """Date picker limits and the range shown when the symbol changes: the latest run of
    consecutive cached days, or a pending trade focus's days for its symbol."""
    if not days:
        return None, None, [], None, None, None
    cached = set(days)
    span = (days[-1] - days[0]).days
    holes = [days[0] + timedelta(days=i) for i in range(span + 1)]
    first, last = latest_run(days)
    start, end = first.isoformat(), last.isoformat()
    if focus and not focus.get("done") and focus["symbol"] == symbol:
        start, end = focus["from"], focus["to"]
    return (
        days[0].isoformat(),
        days[-1].isoformat(),
        [d.isoformat() for d in holes if d not in cached],
        start,
        end,
        start,
    )


def layout(
    sources: SymbolSources, config: ChartConfig = DEFAULT_CONFIG, focus: dict | None = None
) -> html.Div:
    symbols = sources.available_symbols()
    settings = _popover(
        "pop-settings",
        "Chart settings",
        [
            _switch("chart-sessions", "Session lines", ["on"]),
            _switch("chart-overlays", "Overlays", []),
            html.Div(
                "Overlay types" if OVERLAYS else "No overlay types yet",
                id="chart-overlay-summary",
                className="tb-pop-sub",
            ),
            dcc.Checklist(
                id="chart-overlay-types",
                options=overlay_options(enabled=False),
                value=[],
                persistence=True,
                className="tb-check tb-types",
            ),
            html.Div("Daily / weekly candles", className="tb-pop-sub"),
            dcc.Dropdown(
                id="chart-day-boundary",
                options=[{"label": f"Day from {b.value}", "value": b.name} for b in DayBoundary],
                value=DEFAULT_BOUNDARY.name,
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
            html.Div(html.Div(id="bt-bar", className="tb-progress-bar"), className="tb-progress"),
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
            *[
                html.Button(k, id=f"range-{k}", className="tb-range", n_clicks=0)
                for k in QUICK_RANGES
            ],
            html.Div(className="tb-sep"),
            html.Span(className="tb-icon icon-calendar tb-cal-icon"),
            dcc.DatePickerRange(
                id="chart-dates",
                display_format="YYYY-MM-DD",
                first_day_of_week=1,
                className="tb-dates",
            ),
            html.Div(
                [html.Span(id="chart-message"), html.Span(id="chart-notes")],
                className="tb-message",
            ),
            html.Span("UTC", className="tb-utc"),
        ],
        className="tb-bar tb-bottom",
    )
    return html.Div(
        [
            toolbar,
            html.Div([html.Div(id="chart-lwc"), replay_bar], className="tb-chart"),
            bottom,
            dcc.Store(id="chart-config", data=chart_settings(config)),
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
            dcc.Store(id="bt-job"),
            dcc.Store(id="chart-focus", data=focus),
            dcc.Store(id="chart-viewport"),
            dcc.Store(id="settings-current", storage_type="local"),
            settings_panel.layout(),
            dcc.Interval(
                id="chart-replay-timer",
                interval=1000 // config.replay_default_speed,
                disabled=True,
            ),
            dcc.Interval(id="bt-timer", interval=500, disabled=True),
        ],
        className="tb-page",
    )


def register_callbacks(
    app: Dash, sources: SymbolSources, config: ChartConfig = DEFAULT_CONFIG
) -> None:
    settings_panel.register_callbacks(app)

    @app.callback(
        Output("chart-dates", "min_date_allowed"),
        Output("chart-dates", "max_date_allowed"),
        Output("chart-dates", "disabled_days"),
        Output("chart-dates", "start_date"),
        Output("chart-dates", "end_date"),
        Output("chart-dates", "initial_visible_month"),
        Input("chart-symbol", "value"),
        State("chart-focus", "data"),
    )
    def _date_limits(symbol, focus):
        return date_limits(sources.cached_days(symbol) if symbol else [], symbol, focus)

    @app.callback(
        Output("chart-dates", "start_date", allow_duplicate=True),
        Output("chart-dates", "end_date", allow_duplicate=True),
        Input("chart-timeframe", "value"),
        State("chart-viewport", "data"),
        State("chart-symbol", "value"),
        State("chart-dates", "start_date"),
        State("chart-dates", "end_date"),
        State("chart-replay", "data"),
        prevent_initial_call=True,
    )
    def _timeframe_days(timeframe, view, symbol, start, end, replay_state):
        """Keep the view on a timeframe switch: load the days it needs (outside replay)."""
        if not (view and timeframe and start and end) or view.get("symbol") != symbol:
            return no_update, no_update
        if replay_state and replay_state.get("on"):
            return no_update, no_update
        found = dates_for_view(
            sources.cached_days(symbol),
            date.fromisoformat(start[:10]),
            date.fromisoformat(end[:10]),
            view,
            Timeframe[timeframe],
            config,
        )
        if found is None:
            return no_update, no_update
        return found[0].isoformat(), found[1].isoformat()

    @app.callback(
        Output("chart-symbol", "value"),
        Output("chart-overlays", "value"),
        Output("chart-overlay-types", "value"),
        Input("chart-focus", "data"),
        State("chart-overlay-types", "value"),
    )
    def _focus(focus, overlay_types):
        found = focus_selection(focus, overlay_types)
        return found if found is not None else (no_update, no_update, no_update)

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
        Input("chart-dates", "start_date"),
        Input("chart-dates", "end_date"),
        Input("chart-replay-mode", "data"),
        Input("chart-resync", "data"),
        Input("chart-day-boundary", "value"),
        State("chart-replay", "data"),
        State("chart-replay-span", "data"),
    )
    def _base(symbol, timeframe, start_date, end_date, _mode, _resync, boundary, replay_state,
              span):  # fmt: skip
        cfg = with_boundary(config, boundary)
        return base_payload(
            sources, symbol, timeframe, start_date, end_date, replay_state, span, cfg
        )

    @app.callback(
        Output("chart-ovl", "data"),
        Input("chart-need", "data"),
        State("chart-symbol", "value"),
        State("chart-timeframe", "value"),
        State("chart-dates", "start_date"),
        State("chart-dates", "end_date"),
        State("chart-filters", "value"),
        State("settings-current", "data"),
        State("chart-day-boundary", "value"),
        prevent_initial_call=True,
    )
    def _overlays(request, symbol, timeframe, start_date, end_date, filters, store, boundary):
        strategy = settings_panel.store_json(store)
        cfg = with_boundary(config, boundary)
        payload = overlay_payload(
            sources, request, symbol, timeframe, start_date, end_date, filters, cfg, strategy
        )
        return payload if payload is not None else no_update

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
        Input("chart-dates", "start_date"),
        Input("chart-dates", "end_date"),
        State("chart-replay", "data"),
        State("chart-replay-controls", "style"),
        State("chart-view", "data"),
        State("chart-filters", "value"),
        State("settings-current", "data"),
        State("chart-day-boundary", "value"),
        prevent_initial_call=True,
    )
    def _replay_control(*args):
        symbol, timeframe, start_date, end_date, state, controls_style, view, filters = args[-10:-2]
        strategy = settings_panel.store_json(args[-2])
        cfg = with_boundary(config, args[-1])
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
            found = replay_delta(sources, view, replay, cursor, key, filters, cfg, strategy)
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
        Output("chart-dates", "start_date", allow_duplicate=True),
        Output("chart-dates", "end_date", allow_duplicate=True),
        *[Input(f"range-{k}", "n_clicks") for k in QUICK_RANGES],
        State("chart-symbol", "value"),
        prevent_initial_call=True,
    )
    def _quick_range(*args):
        symbol = args[-1]
        key = str(ctx.triggered_id).removeprefix("range-")
        found = quick_range(sources.cached_days(symbol) if symbol else [], key)
        if found is None:
            return no_update, no_update
        return found[0].isoformat(), found[1].isoformat()

    @app.callback(
        Output("bt-symbols", "value"),
        Output("bt-dates", "start_date"),
        Output("bt-dates", "end_date"),
        Output("bt-dates", "min_date_allowed"),
        Output("bt-dates", "max_date_allowed"),
        Input("chart-symbol", "value"),
        Input("chart-dates", "start_date"),
        Input("chart-dates", "end_date"),
        State("chart-dates", "min_date_allowed"),
        State("chart-dates", "max_date_allowed"),
    )
    def _backtest_defaults(symbol, start, end, low, high):
        """The backtest starts out with the chart's symbol and days."""
        symbols = [symbol] if symbol else []
        return symbols, start, end, low, high

    @app.callback(
        Output("bt-job", "data"),
        Output("bt-timer", "disabled"),
        Output("bt-status", "children"),
        Output("bt-bar", "style"),
        Output("url", "pathname"),
        Input("bt-run", "n_clicks"),
        Input("bt-timer", "n_intervals"),
        State("bt-symbols", "value"),
        State("bt-dates", "start_date"),
        State("bt-dates", "end_date"),
        State("bt-job", "data"),
        State("settings-current", "data"),
        prevent_initial_call=True,
    )
    def _backtest(_run, _tick, symbols, start, end, job, store):
        if ctx.triggered_id == "bt-run":
            if not _run:  # fired when the page is built (n_clicks 0), not a click
                return (no_update,) * 5
            settings = settings_panel.store_settings(store)
            preset = settings_panel.preset_label(store)
            return start_backtest(sources, symbols, start, end, settings=settings, preset=preset)
        return poll_backtest(job)


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
