"""Results page of one backtest run: `/results/<run id>`. Spec: ROADMAP.md › 3.6.

TradingView Strategy Tester look (light theme, same style as the chart's toolbar):
- Top bar: "← Chart", the run selector (every run folder in results/, newest first) and
  the symbol filter (All / one symbol), which applies to every tab.
- Header: run name, symbols, date range, settings preset, run date.
- Tabs: **Overview** (stat cards, equity curve in R over time, gross and net, with the net
  drawdown shaded in a pane below; Lightweight Charts, `assets/results.js`),
  **Performance summary** (all / long / short table, per year and per quarter for all
  symbols and each (ROADMAP 6.3), splits by symbol, session,
  long / short, confluence type, TP outcome and tag, R distribution histogram) and
  **List of trades** (sortable; clicking a trade opens the chart on its symbol and days
  with the Trades overlay and its confluences on, scrolled to the trade).

Every number comes from the run's files: trades.csv read back as `TradeRecord`s and
computed with `analytics/metrics.py`, the same functions that wrote summary.json (so the
symbol filter and runs written before a metric existed work too). Nothing is computed here.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dash_table, dcc, html, no_update
from dash.dash_table.Format import Format, Scheme, Sign

from backtester.analytics.metrics import (
    SPLITS,
    by_period,
    by_quarter,
    by_year,
    equity_curve,
    r_histogram,
    split,
    summarize,
)
from backtester.analytics.records import TradeRecord, read_trades
from backtester.runner import RESULTS_DIR
from backtester.ui.chart_config import price_digits

_RUN_ID = re.compile(r"^[A-Za-z0-9_.-]+$")
ALL = "__all__"  # symbol filter value for every symbol
TABS = (
    ("overview", "Overview"),
    ("performance", "Performance summary"),
    ("trades", "List of trades"),
)
HISTOGRAM_BIN_R = 0.25
UP, DOWN, MUTED, ACCENT = "#089981", "#f23645", "#787b86", "#2962ff"  # TradingView colors


def run_folder(run_id: str, results_dir: Path = RESULTS_DIR) -> Path | None:
    """The run's folder, or None for a name that isn't a run folder (no paths outside)."""
    if not _RUN_ID.match(run_id or "") or run_id in (".", ".."):
        return None
    folder = Path(results_dir) / run_id
    return folder if (folder / "summary.json").is_file() else None


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


_RUN_ID = re.compile(r"\d{8}-\d{6}")


def list_runs(results_dir: Path = RESULTS_DIR) -> list[dict]:
    """Run selector options, newest first (run ids start with their UTC start time)."""
    folder = Path(results_dir)
    if not folder.is_dir():
        return []
    found = sorted((p for p in folder.iterdir() if (p / "summary.json").is_file()), reverse=True)
    # timestamped runs first (newest first), study folders after them in name order
    runs = [p for p in found if _RUN_ID.match(p.name)] + [
        p for p in found if not _RUN_ID.match(p.name)
    ]
    options = []
    for p in runs:
        s = _read_json(p / "summary.json")
        symbols = ", ".join(s.get("symbols", []))
        options.append(
            {"label": f"{p.name} · {symbols} · {s.get('start')} → {s.get('end')}", "value": p.name}
        )
    return options


def run_date(run_id: str, summary: dict) -> str:
    """When the run was made: summary.json's `created`, else the time in the run id."""
    if summary.get("created"):
        return datetime.fromisoformat(summary["created"]).strftime("%Y-%m-%d %H:%M UTC")
    try:
        started = datetime.strptime(run_id[:15] + "+0000", "%Y%m%d-%H%M%S%z")
        return started.strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return "—"


# --- formatting ------------------------------------------------------------------------


def fmt_r(value: float | None, sign: bool = True) -> str:
    if value is None:
        return "—"
    return f"{value:+.2f} R" if sign else f"{value:.2f} R"


def fmt_pct(value: float | None) -> str:
    return "—" if value is None else f"{value:.1%}"


def fmt_num(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}"


def tone(value: float | None) -> str:
    """CSS class for a result: green above 0, red below."""
    if value is None or abs(value) < 1e-9:
        return ""
    return "rs-up" if value > 0 else "rs-down"


NAMES = {
    "tokyo": "Tokyo",
    "london": "London",
    "new_york": "New York",
    "none": "no session",
    "fvg": "FVG",
    "order_block": "Order block",
    "bpr": "BPR",
    "breaker": "Breaker",
    "equilibrium": "Equilibrium",
    "long": "Long",
    "short": "Short",
}


def name(key: str) -> str:
    """Display name of a split group or a value from trades.csv."""
    return NAMES.get(key, key)


def session_name(label: str) -> str:
    """ "new_york 2026-09-02" -> "New York 2026-09-02"."""
    session, _, day = label.partition(" ")
    return f"{name(session)} {day}".strip() if label else ""


def filtered(trades: list[TradeRecord], symbol: str | None) -> list[TradeRecord]:
    return trades if symbol in (None, ALL) else [t for t in trades if t.symbol == symbol]


# --- Overview --------------------------------------------------------------------------


def _card(label: str, value: str, sub: str = "", cls: str = "") -> html.Div:
    return html.Div(
        [
            html.Div(label, className="rs-card-label"),
            html.Div(value, className=f"rs-card-value {cls}"),
            html.Div(sub, className="rs-card-sub"),
        ],
        className="rs-card",
    )


def stat_cards(s: dict) -> list[html.Div]:
    """The overview cards for one summary (analytics/metrics.py `summarize`)."""
    return [
        _card(
            "Net R",
            fmt_r(s["net_r_net"]),
            f"gross {fmt_r(s['net_r_gross'])}",
            tone(s["net_r_net"]),
        ),
        _card(
            "Total trades",
            str(s["trades"]),
            f"{s['wins']} wins · {s['losses']} losses · {s['break_even']} break-even",
        ),
        _card("Win rate", fmt_pct(s["win_rate"]), "by net R"),
        _card("Avg R:R (planned)", fmt_num(s["avg_rr"]), "if every TP is hit"),
        _card(
            "Avg realized R",
            fmt_r(s["avg_r_net"]),
            f"gross {fmt_r(s['avg_r_gross'])}",
            tone(s["avg_r_net"]),
        ),
        _card(
            "Avg win / avg loss",
            f"{fmt_r(s['avg_win_r'])} / {fmt_r(s['avg_loss_r'])}",
            "net R",
        ),
        _card("Profit factor", fmt_num(s["profit_factor"]), "net R won / net R lost"),
        _card("Expectancy", fmt_r(s["expectancy_r"]), "net R per trade", tone(s["expectancy_r"])),
        _card(
            "Max drawdown",
            fmt_r(s["max_drawdown_r_net"], sign=False),
            f"gross {fmt_r(s['max_drawdown_r_gross'], sign=False)}",
            "rs-down" if s["max_drawdown_r_net"] > 0 else "",
        ),
        _card(
            "Longest losing streak",
            f"{s['longest_losing_streak']} trades",
            f"longest winning streak {s['longest_winning_streak']}",
        ),
    ]


def _epoch(t: datetime) -> int:
    return int(t.timestamp())


def equity_payload(trades: list[TradeRecord]) -> dict:
    """Equity curve for the browser (`assets/results.js`): UTC seconds, R values."""
    curve = equity_curve(trades)
    return {
        "t": [_epoch(p["time"]) for p in curve],
        "gross": [round(p["gross"], 4) for p in curve],
        "net": [round(p["net"], 4) for p in curve],
        "dd": [round(p["drawdown"], 4) for p in curve],
        "colors": {"gross": MUTED, "net": ACCENT, "dd": DOWN},
    }


def overview(trades: list[TradeRecord]) -> html.Div:
    if not trades:
        return html.Div("No trades.", className="rs-empty")
    return html.Div(
        [
            html.Div(stat_cards(summarize(trades)), className="rs-cards"),
            html.Div(
                [
                    html.Div("Equity curve (R)", className="rs-section-title"),
                    html.Div(
                        [
                            html.Span("Net", className="rs-key rs-key-net"),
                            html.Span("Gross", className="rs-key rs-key-gross"),
                            html.Span("Drawdown (net)", className="rs-key rs-key-dd"),
                        ],
                        className="rs-keys",
                    ),
                ],
                className="rs-section-head",
            ),
            html.Div(id="rs-equity", className="rs-equity"),
        ]
    )


# --- Performance summary ---------------------------------------------------------------

SUMMARY_ROWS = (
    ("Net R (net)", "net_r_net", fmt_r),
    ("Net R (gross)", "net_r_gross", fmt_r),
    ("Total trades", "trades", str),
    ("Wins / losses / break-even", None, None),
    ("Win rate", "win_rate", fmt_pct),
    ("Avg R:R (planned)", "avg_rr", fmt_num),
    ("Avg realized R (net)", "avg_r_net", fmt_r),
    ("Avg realized R (gross)", "avg_r_gross", fmt_r),
    ("Avg win", "avg_win_r", fmt_r),
    ("Avg loss", "avg_loss_r", fmt_r),
    ("Profit factor", "profit_factor", fmt_num),
    ("Expectancy", "expectancy_r", fmt_r),
    ("Max drawdown (net)", "max_drawdown_r_net", lambda v: fmt_r(v, sign=False)),
    ("Max drawdown (gross)", "max_drawdown_r_gross", lambda v: fmt_r(v, sign=False)),
    ("Longest losing streak", "longest_losing_streak", str),
    ("Longest winning streak", "longest_winning_streak", str),
)


COST_ROWS = (
    ("Cost: spread", "spread"),
    ("Cost: commission", "commission"),
    ("Cost: swap", "swap"),
    ("Cost: funding", "funding"),
)


def cost_totals(trades: list[TradeRecord]) -> dict[str, float]:
    """Costs in R summed over the trades, signed like their effect on net R (cost < 0)."""
    return {
        "spread": -sum(t.spread_r for t in trades),
        "commission": -sum(t.commission_r for t in trades),
        "swap": sum(t.swap_r for t in trades),
        "funding": sum(t.funding_r for t in trades),
    }


def summary_table(trades: list[TradeRecord]) -> html.Table:
    """TradingView's performance summary: one row per metric, columns All / Long / Short."""
    columns = [
        ("All", summarize(trades)),
        ("Long", summarize([t for t in trades if t.direction == "long"])),
        ("Short", summarize([t for t in trades if t.direction == "short"])),
    ]

    def cell(s: dict, key, fmt) -> html.Td:
        if key is None:
            return html.Td(f"{s['wins']} / {s['losses']} / {s['break_even']}")
        value = s[key]
        cls = tone(value) if fmt is fmt_r and "drawdown" not in key else ""
        return html.Td(fmt(value), className=cls)

    subsets = [
        trades,
        [t for t in trades if t.direction == "long"],
        [t for t in trades if t.direction == "short"],
    ]
    totals = [cost_totals(sub) for sub in subsets]
    cost_rows = [
        html.Tr([html.Td(label)] + [html.Td(fmt_r(c[key]), className=tone(c[key])) for c in totals])
        for label, key in COST_ROWS
    ]
    return html.Table(
        [
            html.Thead(html.Tr([html.Th("")] + [html.Th(title) for title, _ in columns])),
            html.Tbody(
                [
                    html.Tr([html.Td(label)] + [cell(s, key, fmt) for _, s in columns])
                    for label, key, fmt in SUMMARY_ROWS
                ]
                + cost_rows
            ),
        ],
        className="rs-table rs-summary",
    )


SPLIT_COLUMNS = ("Trades", "Win rate", "Net R", "Avg R", "Profit factor", "Max DD")


def split_table(title: str, groups: dict[str, dict]) -> html.Div:
    rows = [
        html.Tr(
            [
                html.Td(name(group)),
                html.Td(str(s["trades"])),
                html.Td(fmt_pct(s["win_rate"])),
                html.Td(fmt_r(s["net_r_net"]), className=tone(s["net_r_net"])),
                html.Td(fmt_r(s["avg_r_net"]), className=tone(s["avg_r_net"])),
                html.Td(fmt_num(s["profit_factor"])),
                html.Td(fmt_r(s["max_drawdown_r_net"], sign=False)),
            ]
        )
        for group, s in groups.items()
    ]
    return html.Div(
        [
            html.Div(title, className="rs-section-title"),
            html.Table(
                [
                    html.Thead(html.Tr([html.Th("")] + [html.Th(c) for c in SPLIT_COLUMNS])),
                    html.Tbody(rows),
                ],
                className="rs-table rs-split",
            ),
        ],
        className="rs-split-box",
    )


def histogram_figure(trades: list[TradeRecord]) -> go.Figure:
    bins = r_histogram((t.r_net for t in trades), HISTOGRAM_BIN_R)
    colors = [UP if b["lo"] >= 0 else DOWN for b in bins]
    fig = go.Figure(
        go.Bar(
            x=[b["lo"] + HISTOGRAM_BIN_R / 2 for b in bins],
            y=[b["count"] for b in bins],
            width=HISTOGRAM_BIN_R * 0.9,
            marker_color=colors,
            customdata=[[b["lo"], b["hi"]] for b in bins],
            hovertemplate="%{customdata[0]:+.2f} R to %{customdata[1]:+.2f} R: "
            "%{y} trades<extra></extra>",
        )
    )
    fig.update_layout(
        height=260,
        margin={"l": 40, "r": 10, "t": 10, "b": 36},
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"family": "-apple-system, Trebuchet MS, Roboto, sans-serif", "size": 12},
        xaxis={"title": "net R per trade", "gridcolor": "#f0f3fa", "zeroline": False},
        yaxis={"title": "trades", "gridcolor": "#f0f3fa", "rangemode": "tozero"},
        bargap=0,
    )
    return fig


PERIOD_COLUMNS = ("Trades", "Win rate", "Net R", "Max DD")


def period_table(title: str, periods: dict[str, dict]) -> html.Div:
    """Per year / quarter (ROADMAP 6.3): trades, win rate, net R and max drawdown, for all
    symbols together and (several symbols) for each."""
    groups = list(next(iter(periods.values())))  # "all", then the symbols
    if len(groups) == 2:  # one symbol: "all" is the same
        groups = groups[:1]
    head1 = [html.Th("")] + [
        html.Th("All symbols" if g == "all" else g, colSpan=len(PERIOD_COLUMNS),
                className="rs-group")
        for g in groups
    ]  # fmt: skip
    head2 = [html.Th("")] + [
        html.Th(c, className="rs-group-start" if i == 0 else "")
        for _ in groups
        for i, c in enumerate(PERIOD_COLUMNS)
    ]

    def cells(s: dict) -> list[html.Td]:
        return [
            html.Td(str(s["trades"]), className="rs-group-start"),
            html.Td(fmt_pct(s["win_rate"])),
            html.Td(fmt_r(s["net_r_net"]), className=tone(s["net_r_net"])),
            html.Td(fmt_r(s["max_drawdown_r_net"], sign=False)),
        ]

    rows = [
        html.Tr([html.Td(period)] + [c for g in groups for c in cells(row[g])])
        for period, row in periods.items()
    ]
    return html.Div(
        [
            html.Div(title, className="rs-section-title"),
            html.Table(
                [html.Thead([html.Tr(head1), html.Tr(head2)]), html.Tbody(rows)],
                className="rs-table rs-periods",
            ),
        ]
    )


def performance(trades: list[TradeRecord]) -> html.Div:
    if not trades:
        return html.Div("No trades.", className="rs-empty")
    return html.Div(
        [
            html.Div("Performance summary", className="rs-section-title"),
            summary_table(trades),
            period_table(
                "Per year (net R; max drawdown within the year)", by_period(trades, by_year)
            ),
            html.Details(
                [
                    html.Summary("Per quarter", className="rs-section-title rs-summary-toggle"),
                    period_table("", by_period(trades, by_quarter)),
                ],
                open=len({by_year(t) for t in trades}) <= 2,
            ),
            html.Div(
                [split_table(title, split(trades, key)) for title, key in SPLITS.items()],
                className="rs-splits",
            ),
            html.Div(
                f"R distribution (net R, {HISTOGRAM_BIN_R} R bins)", className="rs-section-title"
            ),
            dcc.Graph(
                figure=histogram_figure(trades),
                config={"displayModeBar": False},
                className="rs-histogram",
            ),
        ]
    )


# --- List of trades --------------------------------------------------------------------

EXIT_LABELS = {
    "take_profit": "TP",
    "stop_loss": "SL",
    "break_even": "Break-even",
    "end_of_data": "End of data",
    "signal": "Signal",
}


def trade_table_rows(trades: list[TradeRecord]) -> list[dict]:
    rows = []
    for t in trades:
        digits = price_digits(t.symbol)
        rows.append(
            {
                "id": t.id,
                "time": f"{t.entry_time:%Y-%m-%d %H:%M}",
                "symbol": t.symbol,
                "direction": "Long" if t.direction == "long" else "Short",
                "entry": round(t.entry, digits),
                "sl": round(t.initial_stop, digits),
                "tp1": None if t.take_profit is None else round(t.take_profit, digits),
                "tp2": None if t.take_profit_2 is None else round(t.take_profit_2, digits),
                "r_gross": round(t.r_gross, 3),
                "r_net": round(t.r_net, 3),
                "exit": EXIT_LABELS.get(t.exit_reason, t.exit_reason),
                "confluence": name(t.confluence),
                "session": session_name(t.session),
            }
        )
    return rows


def _r_format() -> Format:
    return Format(precision=2, scheme=Scheme.fixed, sign=Sign.positive)


TRADE_COLUMNS = [
    {"name": "#", "id": "id", "type": "numeric"},
    {"name": "Entry time (UTC)", "id": "time"},
    {"name": "Symbol", "id": "symbol"},
    {"name": "Side", "id": "direction"},
    {"name": "Entry", "id": "entry", "type": "numeric"},
    {"name": "SL", "id": "sl", "type": "numeric"},
    {"name": "TP1", "id": "tp1", "type": "numeric"},
    {"name": "TP2", "id": "tp2", "type": "numeric"},
    {"name": "R gross", "id": "r_gross", "type": "numeric", "format": _r_format()},
    {"name": "R net", "id": "r_net", "type": "numeric", "format": _r_format()},
    {"name": "Exit", "id": "exit"},
    {"name": "Confluence", "id": "confluence"},
    {"name": "Session", "id": "session"},
]


def trade_list(trades: list[TradeRecord]) -> html.Div:
    if not trades:
        return html.Div("No trades.", className="rs-empty")
    r_styles = [
        {"if": {"filter_query": f"{{{c}}} {op} 0", "column_id": c}, "color": color}
        for c in ("r_gross", "r_net")
        for op, color in ((">", UP), ("<", DOWN))
    ]
    return html.Div(
        [
            html.Div(
                "Click a trade to open it on the chart (Trades overlay and its confluences on).",
                className="rs-hint",
            ),
            dash_table.DataTable(
                id="rs-trades",
                columns=TRADE_COLUMNS,
                data=trade_table_rows(trades),
                sort_action="native",
                sort_by=[{"column_id": "id", "direction": "asc"}],
                page_action="none",
                virtualization=True,  # only the visible rows are drawn (years: 17,000+ trades)
                fixed_rows={"headers": True},
                style_as_list_view=True,
                style_table={"height": "calc(100vh - 250px)", "overflowY": "auto"},
                style_header={
                    "backgroundColor": "#ffffff",
                    "color": MUTED,
                    "fontWeight": "600",
                    "borderBottom": "1px solid #e0e3eb",
                },
                style_cell={
                    "fontFamily": "-apple-system, Trebuchet MS, Roboto, sans-serif",
                    "fontSize": "13px",
                    "padding": "6px 10px",
                    "border": "none",
                    "borderBottom": "1px solid #f0f3fa",
                    "textAlign": "right",
                    "cursor": "pointer",
                },
                style_cell_conditional=[
                    {"if": {"column_id": c}, "textAlign": "left"}
                    for c in ("time", "symbol", "direction", "exit", "confluence", "session")
                ],
                style_data_conditional=[
                    *r_styles,
                    {"if": {"state": "active"}, "backgroundColor": "#e3effd", "border": "none"},
                    {
                        "if": {"filter_query": '{direction} = "Long"', "column_id": "direction"},
                        "color": UP,
                    },
                    {
                        "if": {"filter_query": '{direction} = "Short"', "column_id": "direction"},
                        "color": DOWN,
                    },
                ],
            ),
        ]
    )


def chart_link(trade: TradeRecord) -> str:
    """Chart URL focused on the trade: its symbol, the UTC days from entry to exit, and
    the entry / exit candle times to scroll to (pages/chart.py `focus_from_query`)."""
    query = {
        "symbol": trade.symbol,
        "from": trade.entry_candle.date().isoformat(),
        "to": trade.exit_time.date().isoformat(),
        "t0": trade.entry_candle.isoformat(),
        "t1": trade.exit_time.isoformat(),
    }
    return "/?" + urlencode(query)


# --- page ------------------------------------------------------------------------------


def tab_content(tab: str, trades: list[TradeRecord]):
    """(content, equity payload or None) of a tab for the filtered trades."""
    if tab == "performance":
        return performance(trades), None
    if tab == "trades":
        return trade_list(trades), None
    return overview(trades), (equity_payload(trades) if trades else None)


def layout(run_id: str, results_dir: Path = RESULTS_DIR) -> html.Div:
    back = dcc.Link("← Chart", href="/", className="rs-back")
    folder = run_folder(run_id, results_dir)
    runs = list_runs(results_dir)
    selector = dcc.Dropdown(
        id="rs-run",
        options=runs,
        value=folder.name if folder else None,
        clearable=False,
        searchable=True,
        placeholder="Open a run",
        className="rs-run",
    )
    if folder is None:
        return html.Div(
            [
                html.Div([back, html.Div(className="tb-sep"), selector], className="tb-bar tb-top"),
                html.Div([html.H2("Run not found"), html.P(run_id)], className="rs-body"),
                dcc.Store(id="rs-run-id", data=None),
            ],
            className="rs-page",
        )
    summary = _read_json(folder / "summary.json")
    settings = _read_json(folder / "settings.json")
    symbols = summary.get("symbols", [])
    preset = settings.get("preset") or "— (run before presets)"
    meta = [
        ("Symbols", ", ".join(symbols)),
        ("Days (UTC)", f"{summary.get('start')} → {summary.get('end')}"),
        ("Preset", preset),
        ("Run", run_date(folder.name, summary)),
    ]
    notes = summary.get("notes") or []
    top = html.Div(
        [
            back,
            html.Div(className="tb-sep"),
            selector,
            html.Div(className="tb-sep"),
            dcc.RadioItems(
                id="rs-symbol",
                options=[{"label": "All symbols", "value": ALL}]
                + [{"label": s, "value": s} for s in symbols],
                value=ALL,
                className="tb-timeframes rs-symbols",
            ),
        ],
        className="tb-bar tb-top",
    )
    header = html.Div(
        [
            html.H2(f"Strategy 1 · Session zone sweep · {folder.name}", className="rs-title"),
            html.Div(
                [
                    html.Span([html.Span(k, className="rs-meta-key"), v], className="rs-meta")
                    for k, v in meta
                ],
                className="rs-metas",
            ),
            *([html.Div(" · ".join(notes), className="rs-notes")] if notes else []),
        ],
        className="rs-header",
    )
    tabs = dcc.RadioItems(
        id="rs-tab",
        options=[{"label": label, "value": key} for key, label in TABS],
        value=TABS[0][0],
        className="rs-tabs",
    )
    return html.Div(
        [
            top,
            html.Div(
                [header, tabs, html.Div(id="rs-content", className="rs-content")],
                className="rs-body",
            ),
            dcc.Store(id="rs-run-id", data=folder.name),
            dcc.Store(id="rs-equity-data"),
            dcc.Store(id="rs-equity-done"),
        ],
        className="rs-page",
    )


def register_callbacks(app: Dash, results_dir: Path = RESULTS_DIR) -> None:
    @app.callback(
        Output("rs-content", "children"),
        Output("rs-equity-data", "data"),
        Input("rs-tab", "value"),
        Input("rs-symbol", "value"),
        State("rs-run-id", "data"),
    )
    def _content(tab, symbol, run_id):
        folder = run_folder(run_id, results_dir)
        trades = filtered(read_trades(folder), symbol) if folder else []
        return tab_content(tab, trades)

    app.clientside_callback(
        "function (data) { return window.dash_clientside.results.equity(data); }",
        Output("rs-equity-done", "data"),
        Input("rs-equity-data", "data"),
    )

    @app.callback(
        Output("url", "pathname", allow_duplicate=True),
        Input("rs-run", "value"),
        State("rs-run-id", "data"),
        prevent_initial_call=True,
    )
    def _open_run(run_id, current):
        if not run_id or run_id == current:
            return no_update
        return f"/results/{run_id}"

    @app.callback(
        Output("url", "href"),
        Input("rs-trades", "active_cell"),
        State("rs-run-id", "data"),
        prevent_initial_call=True,
    )
    def _open_trade(cell, run_id):
        folder = run_folder(run_id, results_dir)
        if not cell or folder is None:
            return no_update
        by_id = {t.id: t for t in read_trades(folder)}
        trade = by_id.get(cell.get("row_id"))
        return chart_link(trade) if trade else no_update
