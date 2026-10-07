"""Chart page: TradingView-like candlesticks from the M1 cache. Spec: ROADMAP.md › 1.1.

Pick symbol (every symbol of `SymbolSources` with cached days, each read from its own
source's cache, `data/sources.py`), timeframe and a date range (UTC days, both
inclusive, limited to cached days). A range touching a day that was never downloaded shows
the `MissingCacheError` instead of a chart, so gaps in the cache are never silent.
Zooming or panning updates the x-axis labels and fits the price axis to the visible candles.

Replay (ROADMAP.md › 1.2): "Replay" first shows the full chart and asks for a start candle
(click one, or press ▶ to start at the first candle of the last day). From then on only the
candles of `Replay.view(cursor)` are drawn, a `SeriesView`, so the chart shows exactly what
the engine sees; the price axis and the x-axis labels also come only from those candles.
Replay steps on the shown timeframe (M5: 5 minutes per step, H1: one hour). The replay
state stores `now` (the close time of the cursor candle), so switching timeframe keeps the
replay time: the chart then shows the candles of that timeframe closed at `now`.
It also keeps the visible TIME span around the cursor (the "replay span", minutes left and
right of `now`): switching M5 -> M1 shows the same hours with smaller candles. The span
starts at `replay_visible` / `replay_right_space` candles of the timeframe replay was
started on and follows the user's zoom/pan; each replay step keeps it.

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
Overlays that load their own data (`OverlayType.needs_sources`) get the page's sources.

Later steps add: the session view (3.5).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from functools import lru_cache

import pandas as pd
from dash import Dash, Input, Output, Patch, State, ctx, dcc, html, no_update

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries, SeriesView
from backtester.data.adapters.cache_adapter import (
    MissingCacheError,
    candles_from_frame,
    latest_run,
)
from backtester.data.resample import supported
from backtester.data.sources import SymbolSources, warmup_start
from backtester.engine.replay import Replay
from backtester.ui import (
    bos_overlay,  # noqa: F401  (registers the BOS + trend overlay)
    bpr_overlay,  # noqa: F401  (registers the BPR overlay)
    fvg_overlay,  # noqa: F401  (registers the FVG overlay)
    ob_overlay,  # noqa: F401  (registers the Order block overlay)
    session_zone_overlay,  # noqa: F401  (registers the Session zones overlay)
    sweep_overlay,  # noqa: F401  (registers the Liquidity sweep overlay)
    swing_overlay,  # noqa: F401  (registers the Swings overlay)
    trades_overlay,  # noqa: F401  (registers the Trades overlay)
)
from backtester.ui.chart_figure import (
    DEFAULT_CONFIG,
    ChartConfig,
    build_candle_figure,
    frame_from_candles,
    time_ticks,
    y_range,
)
from backtester.ui.overlays import (
    DEFAULT_SETTINGS,
    OVERLAYS,
    OverlayContext,
    OverlaySettings,
    OverlayType,
    OverlayUnavailable,
    overlay_options,
    overlay_summary,
    overlay_traces,
)

TIMEFRAMES = [tf.name for tf in Timeframe if supported(tf)]
DEFAULT_TIMEFRAME = Timeframe.M5.name
REPLAY_OFF = {"on": False, "picking": False, "playing": False, "start": None, "now": None}


def load_chart(
    sources: SymbolSources,
    symbol: str | None,
    timeframe: str | None,
    start_date: str | None,
    end_date: str | None,
    config: ChartConfig = DEFAULT_CONFIG,
    show_sessions: bool = True,
    overlay_keys: Sequence[str] = (),
    registry: dict[str, OverlayType] = OVERLAYS,
    settings: OverlaySettings = DEFAULT_SETTINGS,
):
    """Figure, message and stored candle data for the chosen inputs.

    Returns (figure or None, message, store data or None). `start_date`/`end_date` are
    ISO days, both inclusive. `overlay_keys` are the overlay types to draw (all their events).
    """
    frame, message = _load_frame(sources, symbol, timeframe, start_date, end_date, config)
    if frame is None:
        return None, message, None
    traces, notes = [], []
    if overlay_keys:
        replay, _ = load_replay(sources, symbol, timeframe, start_date, end_date, config)
        traces, notes = chart_overlays(
            replay, overlay_keys, len(replay) - 1, 0, config, registry, settings, sources
        )
    figure = build_candle_figure(
        frame, symbol, Timeframe[timeframe], config, show_sessions=show_sessions, overlays=traces
    )
    return figure, _with_notes(message, notes), _axis_store(frame)


def chart_overlays(
    replay: Replay,
    keys: Sequence[str],
    cursor: int,
    first_x: int,
    config: ChartConfig = DEFAULT_CONFIG,
    registry: dict[str, OverlayType] = OVERLAYS,
    settings: OverlaySettings = DEFAULT_SETTINGS,
    sources: SymbolSources | None = None,
):
    """(traces, messages) of the selected overlays for candles first_x..cursor of `replay`.
    `sources` are passed to overlays that load their own data (e.g. the Trades overlay)."""
    if not keys:
        return [], []
    ctx = OverlayContext(
        replay.symbol,
        cursor,
        first_x,
        config,
        replay.timeframe,
        replay.overall_timeframe,
    )
    return overlay_traces(
        lambda o: _cached_events(replay, o, settings, sources), keys, ctx, registry
    )


@lru_cache(maxsize=32)
def _cached_events(
    replay: Replay,
    overlay: OverlayType,
    settings: OverlaySettings,
    sources: SymbolSources | None = None,
):
    """Events of one overlay over the whole replay range, computed once per range and
    settings."""
    if overlay.needs_sources:
        if sources is None:
            raise OverlayUnavailable("needs the chart's data sources")
        return tuple(overlay.detect(replay, settings, sources))
    return tuple(overlay.detect(replay, settings))


def _with_notes(message: str, notes: Sequence[str]) -> str:
    return " · ".join([message, *notes])


def _load_frame(sources, symbol, timeframe, start_date, end_date, config):
    """(candle frame or None, message) for the chosen inputs."""
    if not (symbol and timeframe and start_date and end_date):
        return None, "Pick a symbol, timeframe and date range."
    start, end = date.fromisoformat(start_date[:10]), date.fromisoformat(end_date[:10])
    if end < start:
        return None, "The end date is before the start date."
    try:
        frame = sources.adapter(symbol).fetch_frame(
            symbol, Timeframe[timeframe], _midnight(start), _midnight(end + timedelta(days=1))
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


def _axis_store(frame: pd.DataFrame, x0: int = 0, timeframe: Timeframe | None = None) -> dict:
    """What the zoom callback needs: open times and lows/highs of the drawn candles, which
    start at x = x0. During replay these are only candles up to the cursor, and the store
    also has the cursor's x and the timeframe (to turn a zoom into a replay span)."""
    replay = {} if timeframe is None else {"cursor_x": x0 + len(frame) - 1, "tf": timeframe.value}
    return {
        **replay,
        "x0": x0,
        "ts": frame["ts"].dt.strftime("%Y-%m-%dT%H:%M:%SZ").tolist(),
        "low": frame["low"].tolist(),
        "high": frame["high"].tolist(),
    }


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


def replay_figure(
    view: SeriesView,
    config: ChartConfig = DEFAULT_CONFIG,
    show_sessions: bool = True,
    overlays: Sequence = (),
    span: dict | None = None,
):
    """(figure, axis store) drawn only from `view`: its last `replay_window` candles, at
    their absolute positions, with the cursor near the right edge. `overlays` are traces
    built for candles `replay_first_x(view.cursor)`..cursor. `span` is the replay span
    (minutes left/right of the cursor's close, see `default_span`), shown in candles of
    this view's timeframe."""
    candles = view.last(config.replay_window)
    first_x = replay_first_x(view.cursor, config)
    frame = frame_from_candles(candles)
    span = span or default_span(view.timeframe, config)
    left, right = span_candles(span, view.timeframe, config)
    x_range = (view.cursor - left + 0.5, view.cursor + right + 0.5)
    figure = build_candle_figure(
        frame, view.symbol, view.timeframe, config, first_x, x_range, show_sessions, overlays
    )
    return figure, _axis_store(frame, first_x, view.timeframe)


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


def zoomed_span(relayout: dict | None, store: dict | None) -> dict | None:
    """Replay span after a zoom/pan during replay (None: no x change, or not in replay)."""
    if not relayout or not store or "cursor_x" not in store:
        return None
    if "xaxis.range[0]" in relayout:
        x0, x1 = relayout["xaxis.range[0]"], relayout["xaxis.range[1]"]
    elif "xaxis.range" in relayout:
        x0, x1 = relayout["xaxis.range"]
    else:
        return None
    cursor, minutes = store["cursor_x"], store["tf"]
    return {"left": (cursor + 0.5 - x0) * minutes, "right": (x1 - cursor - 0.5) * minutes}


def replay_first_x(cursor: int, config: ChartConfig = DEFAULT_CONFIG) -> int:
    """First candle drawn during replay: at most `replay_window` candles up to the cursor."""
    return max(0, cursor + 1 - config.replay_window)


def replay_chart(
    replay: Replay,
    state: dict,
    config: ChartConfig = DEFAULT_CONFIG,
    show_sessions: bool = True,
    overlay_keys: Sequence[str] = (),
    registry: dict[str, OverlayType] = OVERLAYS,
    span: dict | None = None,
    settings: OverlaySettings = DEFAULT_SETTINGS,
    sources: SymbolSources | None = None,
):
    """(figure or None, message, axis store or None) at the replay time `state["now"]`,
    showing the replay `span`. Overlays show only events confirmed at or before the cursor."""
    now = datetime.fromisoformat(state["now"])
    cursor = replay.cursor_at(now)
    if cursor is None:
        return None, f"Replay at {now:%Y-%m-%d %H:%M} UTC: no candle closed yet. Press ▶.", None
    view = replay.view(cursor)
    traces, notes = chart_overlays(
        replay,
        overlay_keys,
        cursor,
        replay_first_x(cursor, config),
        config,
        registry,
        settings,
        sources,
    )
    figure, store = replay_figure(view, config, show_sessions, traces, span)
    message = (
        f"Replay · candle {cursor + 1:,} of {len(replay):,} · "
        f"{view.current.ts:%Y-%m-%d %H:%M} {replay.timeframe.name} candle, closed at "
        f"{replay.close_time(cursor):%H:%M} UTC"
    )
    return figure, _with_notes(message, notes), store


def visible_axes(relayout: dict | None, store: dict | None, config: ChartConfig = DEFAULT_CONFIG):
    """New x-axis labels and price range after a zoom/pan, or None if nothing to change."""
    if not relayout or not store:
        return None
    n, first = len(store["ts"]), store.get("x0", 0)
    if relayout.get("xaxis.autorange"):
        x0, x1 = first, first + n - 1.0
    elif "xaxis.range[0]" in relayout:
        x0, x1 = relayout["xaxis.range[0]"], relayout["xaxis.range[1]"]
    elif "xaxis.range" in relayout:
        x0, x1 = relayout["xaxis.range"]
    else:
        return None
    lo, hi = max(round(x0) - first, 0), min(round(x1) - first, n - 1)
    if hi < lo:
        return None
    ts = pd.to_datetime(pd.Series(store["ts"]), utc=True)
    tickvals, ticktext = time_ticks(ts, lo, hi, config.max_ticks)
    prices = pd.DataFrame({"low": store["low"], "high": store["high"]})
    tickvals = [first + p for p in tickvals]
    return tickvals, ticktext, y_range(prices, lo, hi, config.y_padding)


def layout(sources: SymbolSources, config: ChartConfig = DEFAULT_CONFIG) -> html.Div:
    symbols = sources.available_symbols()
    label = {"color": config.text_color, "marginRight": "6px"}
    row = {"display": "flex", "alignItems": "center", "gap": "8px", "padding": "8px"}
    return html.Div(
        [
            html.Div(
                [
                    html.Span("Symbol", style=label),
                    dcc.Dropdown(
                        id="chart-symbol",
                        options=symbols,
                        value=symbols[0] if symbols else None,
                        clearable=False,
                        placeholder="No symbols in the cache",
                        style={"width": "140px"},
                    ),
                    html.Span("Timeframe", style=label),
                    dcc.Dropdown(
                        id="chart-timeframe",
                        options=TIMEFRAMES,
                        value=DEFAULT_TIMEFRAME,
                        clearable=False,
                        style={"width": "100px"},
                    ),
                    html.Span("Days (UTC)", style=label),
                    dcc.DatePickerRange(
                        id="chart-dates", display_format="YYYY-MM-DD", first_day_of_week=1
                    ),
                    dcc.Checklist(
                        id="chart-sessions",
                        options=[{"label": "Sessions", "value": "on"}],
                        value=["on"],
                        persistence=True,
                        style={"color": config.text_color},
                        inputStyle={"marginRight": "4px"},
                    ),
                    dcc.Checklist(
                        id="chart-overlays",
                        options=[{"label": "Overlays", "value": "on"}],
                        value=[],
                        persistence=True,
                        style={"color": config.text_color},
                        inputStyle={"marginRight": "4px"},
                    ),
                    html.Details(
                        [
                            html.Summary(
                                "Overlay types" if OVERLAYS else "No overlay types yet",
                                id="chart-overlay-summary",
                                style={"cursor": "pointer", "color": config.text_color},
                            ),
                            dcc.Checklist(
                                id="chart-overlay-types",
                                options=overlay_options(enabled=False),
                                value=[],
                                persistence=True,
                                style={
                                    "position": "absolute",
                                    "zIndex": 10,
                                    "top": "100%",
                                    "left": 0,
                                    "minWidth": "220px",
                                    "padding": "6px 10px",
                                    "background": config.background,
                                    "border": f"1px solid {config.spike_color}",
                                    "borderRadius": "4px",
                                    "color": config.text_color,
                                },
                                labelStyle={"display": "block", "whiteSpace": "nowrap"},
                                inputStyle={"marginRight": "6px"},
                            ),
                        ],
                        style={
                            "position": "relative",
                            "minWidth": "220px",
                            "padding": "4px 8px",
                            "border": f"1px solid {config.spike_color}",
                            "borderRadius": "4px",
                        },
                    ),
                    dcc.Checklist(
                        id="chart-filters",
                        options=[
                            {"label": "FVG strong-move filter", "value": "fvg"},
                            {"label": "OB strong-move filter", "value": "ob"},
                        ],
                        value=["ob"],
                        persistence=True,
                        style={"color": config.text_color},
                        inputStyle={"marginRight": "4px"},
                    ),
                    html.Button("Replay", id="chart-replay-toggle", title="Replay on/off"),
                    html.Div(
                        [
                            html.Button("Pick start", id="chart-replay-pick"),
                            html.Button("⏮", id="chart-replay-start", title="Back to start"),
                            html.Button("◀", id="chart-replay-back", title="One candle back"),
                            html.Button("▶", id="chart-replay-forward", title="One candle"),
                            html.Button("Play", id="chart-replay-play"),
                            dcc.Dropdown(
                                id="chart-replay-speed",
                                options=[
                                    {"label": f"{s}/s", "value": s} for s in config.replay_speeds
                                ],
                                value=config.replay_default_speed,
                                clearable=False,
                                style={"width": "80px"},
                            ),
                        ],
                        id="chart-replay-controls",
                        style={**row, "display": "none", "padding": "0"},
                    ),
                ],
                style=row,
            ),
            html.Div(id="chart-message", style={"color": config.text_color, "padding": "0 8px"}),
            dcc.Store(id="chart-candles"),
            dcc.Store(id="chart-replay", data=REPLAY_OFF),
            dcc.Store(id="chart-replay-span"),
            dcc.Interval(
                id="chart-replay-timer",
                interval=1000 // config.replay_default_speed,
                disabled=True,
            ),
            dcc.Graph(
                id="chart-graph",
                style={"height": "calc(100vh - 110px)", "display": "none"},
                config={"scrollZoom": True, "displaylogo": False},
            ),
        ],
        style={"backgroundColor": config.background, "minHeight": "100vh"},
    )


def register_callbacks(
    app: Dash, sources: SymbolSources, config: ChartConfig = DEFAULT_CONFIG
) -> None:
    @app.callback(
        Output("chart-dates", "min_date_allowed"),
        Output("chart-dates", "max_date_allowed"),
        Output("chart-dates", "disabled_days"),
        Output("chart-dates", "start_date"),
        Output("chart-dates", "end_date"),
        Output("chart-dates", "initial_visible_month"),
        Input("chart-symbol", "value"),
    )
    def _date_limits(symbol):
        days = sources.cached_days(symbol) if symbol else []
        if not days:
            return None, None, [], None, None, None
        cached = set(days)
        span = (days[-1] - days[0]).days
        holes = [days[0] + timedelta(days=i) for i in range(span + 1)]
        first, last = latest_run(days)
        return (
            days[0].isoformat(),
            days[-1].isoformat(),
            [d.isoformat() for d in holes if d not in cached],
            first.isoformat(),
            last.isoformat(),
            first.isoformat(),
        )

    @app.callback(
        Output("chart-graph", "figure"),
        Output("chart-graph", "style"),
        Output("chart-message", "children"),
        Output("chart-candles", "data"),
        Input("chart-symbol", "value"),
        Input("chart-timeframe", "value"),
        Input("chart-dates", "start_date"),
        Input("chart-dates", "end_date"),
        Input("chart-replay", "data"),
        Input("chart-sessions", "value"),
        Input("chart-overlays", "value"),
        Input("chart-overlay-types", "value"),
        Input("chart-filters", "value"),
        State("chart-graph", "style"),
        State("chart-replay-span", "data"),
    )
    def _draw(
        symbol,
        timeframe,
        start_date,
        end_date,
        replay_state,
        sessions_switch,
        overlays_switch,
        overlay_types,
        filters,
        style,
        span,
    ):
        args = (sources, symbol, timeframe, start_date, end_date, config)
        show_sessions = bool(sessions_switch)
        keys = selected_overlays(overlays_switch, overlay_types)
        settings = OverlaySettings(
            fvg_strong_move_filter="fvg" in (filters or []),
            ob_strong_move_filter="ob" in (filters or []),
        )
        if replay_state["on"] and not replay_state["picking"]:
            replay, message = load_replay(*args)
            figure, message, store = (
                replay_chart(
                    replay,
                    replay_state,
                    config,
                    show_sessions,
                    keys,
                    span=span,
                    settings=settings,
                    sources=sources,
                )
                if replay
                else (None, message, None)
            )
        else:
            figure, message, store = load_chart(
                *args, show_sessions=show_sessions, overlay_keys=keys, settings=settings
            )
            if replay_state["on"] and figure:
                now = datetime.fromisoformat(replay_state["now"])
                message = (
                    "Replay: click the candle to start at, or press ▶ to start after the "
                    f"candle closing at {now:%Y-%m-%d %H:%M} UTC."
                )
        style = {**(style or {}), "display": "block" if figure else "none"}
        return figure or {}, style, message, store

    @app.callback(
        Output("chart-replay", "data"),
        Output("chart-replay-span", "data", allow_duplicate=True),
        Output("chart-replay-timer", "disabled"),
        Output("chart-replay-play", "children"),
        Output("chart-replay-controls", "style"),
        Output("chart-replay-toggle", "style"),
        Input("chart-replay-toggle", "n_clicks"),
        Input("chart-replay-pick", "n_clicks"),
        Input("chart-replay-start", "n_clicks"),
        Input("chart-replay-back", "n_clicks"),
        Input("chart-replay-forward", "n_clicks"),
        Input("chart-replay-play", "n_clicks"),
        Input("chart-replay-timer", "n_intervals"),
        Input("chart-graph", "clickData"),
        Input("chart-symbol", "value"),
        Input("chart-timeframe", "value"),
        Input("chart-dates", "start_date"),
        Input("chart-dates", "end_date"),
        State("chart-replay", "data"),
        State("chart-replay-controls", "style"),
        prevent_initial_call=True,
    )
    def _replay_control(*args):
        symbol, timeframe, start_date, end_date, state, controls_style = args[-6:]
        action = _REPLAY_ACTIONS.get(ctx.triggered_id, "data")
        replay, _ = load_replay(sources, symbol, timeframe, start_date, end_date, config)
        clicked = ctx.triggered[0]["value"] if action == "click" else None
        clicked_x = clicked["points"][0]["x"] if clicked and clicked.get("points") else None
        new = replay_step(action, state, replay, clicked_x)
        # replay switched on: the span starts at the default of the shown timeframe
        started = action == "toggle" and new["on"]
        return (
            new if new != state else no_update,
            default_span(Timeframe[timeframe], config) if started else no_update,
            not new["playing"],
            "Pause" if new["playing"] else "Play",
            {**controls_style, "display": "flex" if new["on"] else "none"},
            {"fontWeight": "bold", "background": config.accent_color, "color": "white"}
            if new["on"]
            else {},
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
        Output("chart-graph", "figure", allow_duplicate=True),
        Output("chart-replay-span", "data", allow_duplicate=True),
        Input("chart-graph", "relayoutData"),
        State("chart-candles", "data"),
        prevent_initial_call=True,
    )
    def _fit_visible(relayout, store):
        span = zoomed_span(relayout, store) or no_update
        axes = visible_axes(relayout, store, config)
        if axes is None:
            return no_update, span
        tickvals, ticktext, yrange = axes
        patch = Patch()
        patch["layout"]["xaxis"]["tickvals"] = tickvals
        patch["layout"]["xaxis"]["ticktext"] = ticktext
        if yrange:
            patch["layout"]["yaxis"]["range"] = yrange
        return patch, span


_REPLAY_ACTIONS = {
    "chart-replay-toggle": "toggle",
    "chart-replay-pick": "pick",
    "chart-replay-start": "start",
    "chart-replay-back": "back",
    "chart-replay-forward": "forward",
    "chart-replay-play": "play",
    "chart-replay-timer": "tick",
    "chart-graph": "click",
}


def selected_overlays(switch: list | None, types: list | None) -> list[str]:
    """Overlay types to draw: none while the switch is off (the chart starts empty)."""
    return list(types or []) if switch else []


def _iso(t: datetime) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def _midnight(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=UTC)
