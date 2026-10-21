"""Research page `/research` (ROADMAP 6.1 d2 / 6.2): every research variant and every plain
backtest run in one sortable table, with its scorecard, test result, verdict and warning flags.

Spec: research-runner.md > Research page. Rows come from `ui/research_model.py` (research
folders and plain runs, cached by file mtime). Default order: verdict (green first), then test
net R, then development net R; the headers sort by any column. Filters: strategy, symbol,
flags (all / unflagged / flagged) and minimum trades. A row click opens its results page
(`/results/<run id>`; a research variant opens `/results/research~<id>~<variant>`). The Reload
button reads the folders again.
"""

from __future__ import annotations

from pathlib import Path

from dash import Dash, Input, Output, State, dash_table, dcc, html, no_update
from dash.dash_table.Format import Format, Scheme, Sign

from backtester.paths import RESULTS_DIR
from backtester.ui import research_model as rm

PATH = "/research"
ALL = "__all__"
TITLE = "Research"
HINT = "Click a row to open its results. Verdict, test net R and deflated Sharpe: chosen variants."
EMPTY_TEXT = "No runs yet."
GREEN, YELLOW, RED = "#2ebd85", "#f0b90b", "#f6465d"
FLAG_COLOUR = "#f0b90b"
VERDICT_COLOURS = {"green": GREEN, "yellow": YELLOW, "red": RED}


def _num(id_: str, name: str, digits: int = 2, sign: bool = False) -> dict:
    fmt = Format(precision=digits, scheme=Scheme.fixed)
    if sign:
        fmt = fmt.sign(Sign.positive)
    return {"id": id_, "name": name, "type": "numeric", "format": fmt}


COLUMNS = [
    {"id": "source", "name": "Source"},
    {"id": "strategy", "name": "Strategy"},
    {"id": "variant", "name": "Variant"},
    {"id": "symbols", "name": "Symbols"},
    {"id": "period", "name": "Period"},
    _num("trades", "Trades", 0),
    _num("win_rate", "Win %", 1),
    _num("avg_r", "Avg R", 3, True),
    _num("net_r", "Net R", 1, True),
    _num("profit_factor", "PF", 2),
    _num("max_dd_r", "Max DD R", 1),
    _num("half_first_net_r", "Half 1 R", 1, True),
    _num("half_second_net_r", "Half 2 R", 1, True),
    _num("net_r_stressed", "Net R costs x1.5", 1, True),
    _num("net_r_without_best", "Net R w/o best", 1, True),
    _num("test_net_r", "Test net R", 1, True),
    _num("deflated_sharpe", "Deflated Sharpe", 2),
    {"id": "verdict", "name": "Verdict"},
    {"id": "flags", "name": "Flags"},
]
TEXT_COLUMNS = ("source", "strategy", "variant", "symbols", "period", "verdict", "flags")
NUMBER_COLUMNS = (
    "net_r",
    "avg_r",
    "half_first_net_r",
    "half_second_net_r",
    "net_r_stressed",
    "net_r_without_best",
    "test_net_r",
)
FLAG_OPTIONS = [
    {"label": "All", "value": rm.FILTER_ALL},
    {"label": "Unflagged only", "value": rm.FILTER_UNFLAGGED},
    {"label": "Flagged only", "value": rm.FILTER_FLAGGED},
]


def href_for_click(cell: dict | None, table: list[dict] | None) -> str | None:
    """The results link of the clicked row, None without a valid click."""
    if not cell or not table:
        return None
    for row in table:
        if row["id"] == cell.get("row_id"):
            return row["href"]
    return None


def _strategy_options(rows: list[dict]) -> list[dict]:
    names = {r["strategy_name"]: r["strategy"] for r in rows}
    return [{"label": "All strategies", "value": ALL}] + [
        {"label": label, "value": name} for name, label in sorted(names.items(), key=lambda x: x[1])
    ]


def _symbol_options(rows: list[dict]) -> list[dict]:
    symbols = {s for r in rows for s in r["symbol_list"]}
    return [{"label": "All symbols", "value": ALL}] + [
        {"label": s, "value": s} for s in sorted(symbols)
    ]


def view(rows, strategy, symbol, flagged, min_trades) -> tuple[list[dict], list[dict], str]:
    """(table data, tooltips, count text) for the filters."""
    shown = rm.sort_rows(
        rm.filter_rows(
            rows,
            None if strategy in (None, ALL) else strategy,
            None if symbol in (None, ALL) else symbol,
            flagged,
            min_trades,
        )
    )
    data = rm.table_rows(shown)
    tips = [
        {"flags": {"value": r["flags_tooltip"], "type": "text"}} if r["flags_tooltip"] else {}
        for r in data
    ]
    count = f"{len(shown)} of {len(rows)} rows" if rows else EMPTY_TEXT
    return data, tips, count


def _style_data_conditional() -> list[dict]:
    out = [{"if": {"state": "active"}, "backgroundColor": "#172238", "border": "none"}]
    for col in NUMBER_COLUMNS:
        out.append({"if": {"column_id": col, "filter_query": f"{{{col}}} > 0"}, "color": GREEN})
        out.append({"if": {"column_id": col, "filter_query": f"{{{col}}} < 0"}, "color": RED})
    for colour, hexcode in VERDICT_COLOURS.items():
        out.append(
            {
                "if": {"column_id": "verdict", "filter_query": f'{{verdict_colour}} = "{colour}"'},
                "color": hexcode,
                "fontWeight": "600",
            }
        )
    out.append({"if": {"column_id": "flags"}, "color": FLAG_COLOUR})
    return out


def layout(results_dir: Path = RESULTS_DIR) -> html.Div:
    rows = rm.load_rows(results_dir)
    data, tips, count = view(rows, ALL, ALL, rm.FILTER_ALL, None)
    controls = html.Div(
        [
            dcc.Dropdown(
                id="rr-strategy",
                options=_strategy_options(rows),
                value=ALL,
                clearable=False,
                className="rr-select",
            ),
            dcc.Dropdown(
                id="rr-symbol",
                options=_symbol_options(rows),
                value=ALL,
                clearable=False,
                className="rr-select",
            ),
            dcc.RadioItems(
                id="rr-flagged",
                options=FLAG_OPTIONS,
                value=rm.FILTER_ALL,
                className="rr-radio",
                inline=True,
            ),
            html.Label(
                [
                    "Min trades ",
                    dcc.Input(
                        id="rr-min-trades",
                        type="number",
                        min=0,
                        step=1,
                        debounce=True,
                        className="rr-input",
                    ),
                ],
                className="rr-label",
            ),
            html.Button("Reload", id="rr-reload", n_clicks=0, className="rr-button"),
            html.Span(count, id="rr-count", className="rr-count"),
        ],
        className="rr-controls",
    )
    table = dash_table.DataTable(
        id="rr-table",
        columns=COLUMNS,
        data=data,
        hidden_columns=[],
        tooltip_data=tips,
        tooltip_delay=0,
        tooltip_duration=None,
        sort_action="native",
        page_action="none",
        virtualization=True,
        fixed_rows={"headers": True},
        style_as_list_view=True,
        style_table={
            "height": "calc(100vh - 190px)",
            "overflowY": "auto",
            "overflowX": "auto",
            "minWidth": "100%",
        },
        style_header={
            "backgroundColor": "#111a2b",
            "color": "#7d8aa5",
            "fontWeight": "600",
            "borderBottom": "1px solid #1d2a40",
            "whiteSpace": "normal",
        },
        style_cell={
            "backgroundColor": "#0b1220",
            "color": "#e6ebf5",
            "fontFamily": "-apple-system, Trebuchet MS, Roboto, sans-serif",
            "fontSize": "13px",
            "padding": "6px 10px",
            "border": "none",
            "borderBottom": "1px solid #1d2a40",
            "textAlign": "right",
            "cursor": "pointer",
            "minWidth": "70px",
            "whiteSpace": "nowrap",
        },
        style_cell_conditional=[
            {"if": {"column_id": c}, "textAlign": "left"} for c in TEXT_COLUMNS
        ],
        style_data_conditional=_style_data_conditional(),
        css=[{"selector": ".dash-tooltip", "rule": "max-width: 420px;"}],
    )
    return html.Div(
        [
            html.Div(
                [html.Span(TITLE, className="rr-title"), html.Span(HINT, className="rr-hint")],
                className="rr-head",
            ),
            controls,
            table,
        ],
        className="rr-page",
    )


def register_callbacks(app: Dash, results_dir: Path = RESULTS_DIR) -> None:
    @app.callback(
        Output("rr-table", "data"),
        Output("rr-table", "tooltip_data"),
        Output("rr-count", "children"),
        Output("rr-strategy", "options"),
        Output("rr-symbol", "options"),
        Input("rr-strategy", "value"),
        Input("rr-symbol", "value"),
        Input("rr-flagged", "value"),
        Input("rr-min-trades", "value"),
        Input("rr-reload", "n_clicks"),
    )
    def _refresh(strategy, symbol, flagged, min_trades, _reload):
        rows = rm.load_rows(results_dir)
        data, tips, count = view(rows, strategy, symbol, flagged, min_trades)
        return data, tips, count, _strategy_options(rows), _symbol_options(rows)

    @app.callback(
        Output("url", "pathname", allow_duplicate=True),
        Input("rr-table", "active_cell"),
        State("rr-table", "data"),
        prevent_initial_call=True,
    )
    def _open(cell, data):
        href = href_for_click(cell, data)
        return href if href else no_update
