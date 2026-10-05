"""Chart page: TradingView-like candlesticks from the Dukascopy cache. Spec: ROADMAP.md › 1.1.

Pick symbol (only symbols with cached days), timeframe and a date range (UTC days, both
inclusive, limited to cached days). A range touching a day that was never downloaded shows
the `MissingCacheError` instead of a chart, so gaps in the cache are never silent.
Zooming or panning updates the x-axis labels and fits the price axis to the visible candles.

Later steps add: replay (1.2), session lines (1.3), zones, confluences and position boxes.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd
from dash import Dash, Input, Output, Patch, State, dcc, html, no_update

from backtester.core.models import Timeframe
from backtester.data.adapters.cache_adapter import (
    CacheAdapter,
    MissingCacheError,
    available_symbols,
    cached_days,
    latest_run,
)
from backtester.data.resample import supported
from backtester.ui.chart_figure import (
    DEFAULT_CONFIG,
    ChartConfig,
    build_candle_figure,
    time_ticks,
    y_range,
)

TIMEFRAMES = [tf.name for tf in Timeframe if supported(tf)]
DEFAULT_TIMEFRAME = Timeframe.M5.name


def load_chart(
    cache_dir: Path,
    symbol: str | None,
    timeframe: str | None,
    start_date: str | None,
    end_date: str | None,
    config: ChartConfig = DEFAULT_CONFIG,
):
    """Figure, message and stored candle data for the chosen inputs.

    Returns (figure or None, message, store data or None). `start_date`/`end_date` are
    ISO days, both inclusive.
    """
    if not (symbol and timeframe and start_date and end_date):
        return None, "Pick a symbol, timeframe and date range.", None
    start, end = date.fromisoformat(start_date[:10]), date.fromisoformat(end_date[:10])
    if end < start:
        return None, "The end date is before the start date.", None
    try:
        frame = CacheAdapter(cache_dir).fetch_frame(
            symbol, Timeframe[timeframe], _midnight(start), _midnight(end + timedelta(days=1))
        )
    except MissingCacheError as e:
        return None, str(e), None
    if frame.empty:
        return None, f"No {symbol} candles from {start} to {end} (market closed?).", None
    if len(frame) > config.max_candles:
        return (
            None,
            (
                f"{len(frame):,} {timeframe} candles is more than the limit of "
                f"{config.max_candles:,}. Pick a shorter range or a higher timeframe."
            ),
            None,
        )
    store = {
        "ts": frame["ts"].dt.strftime("%Y-%m-%dT%H:%M:%SZ").tolist(),
        "low": frame["low"].tolist(),
        "high": frame["high"].tolist(),
    }
    message = f"{len(frame):,} {timeframe} candles, {start} to {end} (UTC)."
    return build_candle_figure(frame, symbol, Timeframe[timeframe], config), message, store


def visible_axes(relayout: dict | None, store: dict | None, config: ChartConfig = DEFAULT_CONFIG):
    """New x-axis labels and price range after a zoom/pan, or None if nothing to change."""
    if not relayout or not store:
        return None
    n = len(store["ts"])
    if relayout.get("xaxis.autorange"):
        x0, x1 = 0.0, n - 1.0
    elif "xaxis.range[0]" in relayout:
        x0, x1 = relayout["xaxis.range[0]"], relayout["xaxis.range[1]"]
    elif "xaxis.range" in relayout:
        x0, x1 = relayout["xaxis.range"]
    else:
        return None
    lo, hi = max(round(x0), 0), min(round(x1), n - 1)
    if hi < lo:
        return None
    ts = pd.to_datetime(pd.Series(store["ts"]), utc=True)
    tickvals, ticktext = time_ticks(ts, lo, hi, config.max_ticks)
    prices = pd.DataFrame({"low": store["low"], "high": store["high"]})
    return tickvals, ticktext, y_range(prices, lo, hi, config.y_padding)


def layout(cache_dir: Path) -> html.Div:
    symbols = available_symbols(cache_dir)
    label = {"color": "#d1d4dc", "marginRight": "6px"}
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
                ],
                style={"display": "flex", "alignItems": "center", "gap": "8px", "padding": "8px"},
            ),
            html.Div(id="chart-message", style={"color": "#d1d4dc", "padding": "0 8px"}),
            dcc.Store(id="chart-candles"),
            dcc.Graph(
                id="chart-graph",
                style={"height": "calc(100vh - 110px)", "display": "none"},
                config={"scrollZoom": True, "displaylogo": False},
            ),
        ],
        style={"backgroundColor": ChartConfig.background, "minHeight": "100vh"},
    )


def register_callbacks(app: Dash, cache_dir: Path, config: ChartConfig = DEFAULT_CONFIG) -> None:
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
        days = cached_days(symbol, cache_dir) if symbol else []
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
        State("chart-graph", "style"),
    )
    def _draw(symbol, timeframe, start_date, end_date, style):
        figure, message, store = load_chart(
            cache_dir, symbol, timeframe, start_date, end_date, config
        )
        style = {**(style or {}), "display": "block" if figure else "none"}
        return figure or {}, style, message, store

    @app.callback(
        Output("chart-graph", "figure", allow_duplicate=True),
        Input("chart-graph", "relayoutData"),
        State("chart-candles", "data"),
        prevent_initial_call=True,
    )
    def _fit_visible(relayout, store):
        axes = visible_axes(relayout, store, config)
        if axes is None:
            return no_update
        tickvals, ticktext, yrange = axes
        patch = Patch()
        patch["layout"]["xaxis"]["tickvals"] = tickvals
        patch["layout"]["xaxis"]["ticktext"] = ticktext
        if yrange:
            patch["layout"]["yaxis"]["range"] = yrange
        return patch


def _midnight(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=UTC)
