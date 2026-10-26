"""Research cards. Spec: design/ui-proposal.md > Page: Research / Research card."""

from __future__ import annotations

from pathlib import Path

from dash import ALL as EVERY  # the page's own ALL is the strategy / symbol filter value
from dash import Dash, Input, Output, State, ctx, dcc, html

from backtester.paths import RESULTS_DIR
from backtester.ui import parameter_heatmap, queue_panel
from backtester.ui import queue_model as qm
from backtester.ui import research_model as rm
from backtester.ui.layout import details, info, key_strip, page

PATH = "/research"
ALL = "__all__"
TITLE = "Research"
HINT = "Expand a card for diagnostics and Open results. Research diagnostics: chosen variant only."
PIPELINE_ID = "rr-pipeline"
PIPELINE_HINT = "Research pipeline of this grid: queue job and pipeline.json"
EMPTY_TEXT = "No runs yet."
PAGE_SIZE = 50
VERDICT_COLOURS = {
    "green": "var(--green)",
    "yellow": "var(--amber)",
    "red": "var(--red)",
}
VERDICT_LABELS = {"green": "edge", "yellow": "weak", "red": "no edge"}
FLAG_OPTIONS = [
    {"label": "All", "value": rm.FILTER_ALL},
    {"label": "Unflagged only", "value": rm.FILTER_UNFLAGGED},
    {"label": "Flagged only", "value": rm.FILTER_FLAGGED},
]
SORT_OPTIONS = [
    {"label": label, "value": value}
    for label, value in (
        ("Verdict", "verdict"),
        ("Test net R", "test_net_r"),
        ("Net R", "net_r"),
        ("R/trade", "avg_r"),
        ("PF", "profit_factor"),
        ("Drawdown", "max_dd_r"),
        ("Detrended", "detrended_net_r"),
        ("RC p", "rc_p"),
    )
]

# Label, row key, decimal places (None means text), suffix.
CHIPS = (
    ("Period", "period", None, ""),
    ("Trades", "trades", 0, ""),
    ("Net R", "net_r", 1, ""),
    ("R/trade", "avg_r", 2, ""),
    ("Win %", "win_rate", 0, "%"),
    ("Max DD", "max_dd_r", 1, " R"),
    ("PF", "profit_factor", 2, ""),
    ("OOS net R", "test_net_r", 1, ""),
    ("Detrended", "detrended_net_r", 1, ""),
    ("MC DD p95", "mc_dd_p95_pct", 0, "%"),
    ("Prop pass %", "prop_pass_pct", 0, "%"),
    ("Best condition", "best_condition", None, ""),
    ("Sensitivity", "sensitivity", None, ""),
)
TILES = (
    ("Source", "source", None, ""),
    ("Strategy", "strategy", None, ""),
    ("Idea", "idea", None, ""),
    ("Variant", "variant", None, ""),
    ("Symbols", "symbols", None, ""),
    ("Test period", "test_period", None, ""),
    ("Half 1 R", "half_first_net_r", 1, ""),
    ("Half 2 R", "half_second_net_r", 1, ""),
    ("Costs x1.5 net R", "net_r_stressed", 1, ""),
    ("Without best net R", "net_r_without_best", 1, ""),
    ("Deflated Sharpe", "deflated_sharpe", 2, ""),
    ("RC p", "rc_p", 2, ""),
    ("PBO", "pbo", 2, ""),
    ("P(mean > 0)", "p_mean_pos", 0, "%"),
    ("Posterior odds (to 1)", "posterior_odds", 2, ""),
    ("BCa lower 95% daily mean R", "lower95", 2, ""),
    ("Log PF", "log_pf", 2, ""),
    ("WFE", "wfe", 2, ""),
    ("Monkey kind 1", "monkey", None, ""),
    ("Monkey kind 1 net percentile", "monkey_net_percentile", 0, "%"),
    ("Monkey kind 1 DD percentile", "monkey_dd_percentile", 0, "%"),
    ("Best regime", "best_regime", None, ""),
    ("MC risk per trade", "mc_risk_pct", 2, "%"),
    ("Test trades", "test_trades", 0, ""),
    ("Test win %", "test_win_rate", 0, "%"),
    ("Test t-stat", "t_stat", 2, ""),
    ("Test variants", "n_variants", 0, ""),
    ("Verdict reason", "verdict_reason", None, ""),
)


def _format(value, digits=None, suffix="") -> str:
    if value is None or value == "":
        return "–"
    if digits is None:
        return str(value)
    number = rm._num(value)
    return f"{number:.{digits}f}{suffix}" if number is not None else "–"


def _metric(row, field, class_name):
    label, key, digits, suffix = field
    value = row.get(key)
    if key == "p_mean_pos" and value is not None:
        value *= rm.PERCENT
    return html.Div(
        [
            html.Span(label, className="rr-metric-label"),
            html.Span(_format(value, digits, suffix), className="rr-metric-value"),
        ],
        className=class_name,
    )


def diagnostic_tiles(data, prefix=""):
    """Saved diagnostic records as wrapping labelled values, without raw file syntax."""
    if isinstance(data, dict):
        return html.Div(
            [
                diagnostic_tiles(value, f"{prefix} · {key.replace('_', ' ').title()}".strip(" ·"))
                for key, value in data.items()
            ],
            className="rr-tiles",
        )
    if isinstance(data, list):
        return html.Div(
            [diagnostic_tiles(value, f"{prefix} {index}") for index, value in enumerate(data, 1)],
            className="rr-diagnostics",
        )
    return html.Div(
        [
            html.Span(prefix, className="rr-metric-label"),
            html.Span(_format(data, 2 if isinstance(data, (float, int)) else None)),
        ],
        className="rr-tile",
    )


def pipeline_chip(row: dict):
    """The pipeline state of a research card ("queued", "step 2 of 3: ...", "done", "failed:
    ..."); a plain run has none. The text is empty (chip hidden) when the grid has no pipeline
    state; the page refreshes it with the queue panel (`register_callbacks`)."""
    if not row.get("is_research"):
        return None
    text = row.get("pipeline")
    return html.Div(
        f"Pipeline: {text}" if text else "",
        id={"type": PIPELINE_ID, "rid": row.get("research_id") or "", "card": row["source"]},
        title=PIPELINE_HINT,
        className=qm.pipeline_class(text),
    )


def card(row: dict) -> html.Details:
    """A wrapping summary and closed diagnostic fold, with its existing results link."""
    verdict = row.get("verdict_colour", row.get("verdict", ""))
    colour = VERDICT_COLOURS.get(verdict, "var(--muted)")
    label = row.get("verdict_label") or VERDICT_LABELS.get(verdict, "not tested")
    flags = rm.flag_text(row.get("flag_keys", []))
    summary = html.Summary(
        [
            html.Div(
                [
                    html.Span("●", style={"color": colour}, title=label),
                    html.Strong(f"{row.get('strategy', '–')} · {row.get('source', '–')}"),
                    html.Span(label, style={"color": colour}),
                ],
                className="rr-card-title",
            ),
            html.Div(row.get("idea") or row.get("strategy") or "–", className="rr-idea"),
            html.Div(
                [
                    pipeline_chip(row),
                    *[_metric(row, field, "rr-chip") for field in CHIPS],
                    html.Div(
                        flags or "⚠ none",
                        title=rm.flag_tooltip(row.get("flag_keys", [])),
                        className="rr-chip rr-flags",
                    ),
                ],
                className="rr-chips",
            ),
        ]
    )
    tiles = [_metric(row, field, "rr-tile") for field in (*CHIPS, *TILES)]
    tiles.append(
        html.Div(
            [
                html.Span("N / N_eff", className="rr-metric-label"),
                html.Span(f"{_format(row.get('n'), 0)} / {_format(row.get('n_eff'), 2)}"),
            ],
            className="rr-tile",
        )
    )
    # Partition by the displayed value, including invalid numeric values; zero is computed.
    missing, filled = [], []
    for tile in tiles:
        value = tile.children[1].children
        empty = value in ("–", "-", "– / –", "- / -")
        (missing if empty else filled).append(tile)
    diagnostics = [
        details(
            label,
            diagnostic_tiles(row[key]),
        )
        for label, key in (
            ("Drawdown bounds", "drawdown_bounds"),
            ("Grid", "grid"),
            ("Walk-forward windows", "walk_forward"),
            ("Sensitivity neighbours", "sensitivity_rows"),
        )
        if row.get(key)
    ]
    return html.Details(
        [
            summary,
            html.Div(
                [
                    html.Div(filled, className="rr-tiles"),
                    html.Div(
                        rm.flag_tooltip(row.get("flag_keys", [])) or "No warning flags",
                        className="rr-flags",
                    ),
                    *diagnostics,
                    parameter_heatmap.panel(
                        row.get("heatmap_rows", []),
                        row.get("heatmap_chosen"),
                        row.get("source", ""),
                    )
                    if row.get("is_research")
                    else None,
                    dcc.Link("Open results", href=row["href"], className="rr-button rr-results"),
                    *(
                        [
                            details(
                                f"Not computed yet ({len(missing)})",
                                html.Div(missing, className="rr-tiles"),
                            )
                        ]
                        if missing
                        else []
                    ),
                ],
                className="rr-card-body",
            ),
        ],
        open=False,
        className="rr-card",
        style={"borderLeftColor": colour},
    )


def href_for_click(cell: dict | None, table: list[dict] | None) -> str | None:
    """Compatibility for consumers of the previous row-click helper."""
    if not cell or not table:
        return None
    return next((r["href"] for r in table if r["id"] == cell.get("row_id")), None)


def _strategy_options(rows):
    names = {r["strategy_name"]: r["strategy"] for r in rows}
    return [{"label": "All strategies", "value": ALL}] + [
        {"label": label, "value": name} for name, label in sorted(names.items(), key=lambda x: x[1])
    ]


def _symbol_options(rows):
    return [{"label": "All symbols", "value": ALL}] + [
        {"label": s, "value": s} for s in sorted({s for r in rows for s in r["symbol_list"]})
    ]


def _filtered(rows, strategy, symbol, flagged, min_trades, sort_by="verdict"):
    return rm.sort_card_rows(
        rm.filter_rows(
            rows,
            None if strategy in (None, ALL) else strategy,
            None if symbol in (None, ALL) else symbol,
            flagged,
            min_trades,
        ),
        sort_by,
    )


def view(rows, strategy, symbol, flagged, min_trades):
    """Legacy data/filter helper retained for row consumers."""
    shown = _filtered(rows, strategy, symbol, flagged, min_trades)
    data = rm.table_rows(shown)
    tips = [
        {"flags": {"value": r["flags_tooltip"], "type": "text"}} if r["flags_tooltip"] else {}
        for r in data
    ]
    return data, tips, f"{len(shown)} of {len(rows)} rows" if rows else EMPTY_TEXT


def card_view(rows, strategy, symbol, flagged, min_trades, sort_by="verdict", limit=PAGE_SIZE):
    shown = _filtered(rows, strategy, symbol, flagged, min_trades, sort_by)
    visible = shown[:limit]
    count = f"{len(visible)} of {len(shown)} rows" if rows else EMPTY_TEXT
    return [card(r) for r in visible], len(shown) <= limit, count


def counts(rows):
    return key_strip(
        [
            {"label": "Runs", "value": len(rows)},
            {
                "label": "Green verdicts",
                "value": sum(r.get("verdict") == "green" for r in rows),
                "sign": "green",
            },
            {"label": "Flagged", "value": sum(bool(r["flag_keys"]) for r in rows)},
        ]
    )


_ops: dict[str, qm.QueueOps] = {}


def queue_ops(results_dir: Path = RESULTS_DIR) -> qm.QueueOps:
    """The queue actions of this results folder, one per folder (it remembers a runner start)."""
    key = str(Path(results_dir).resolve())
    if key not in _ops:
        _ops[key] = qm.QueueOps(qm.make_queue(results_dir))
    return _ops[key]


def _load(results_dir: Path, ops: qm.QueueOps) -> list[dict]:
    rows = rm.load_rows(results_dir)
    qm.attach_pipeline(rows, ops.queue, results_dir)
    return rows


def layout(results_dir: Path = RESULTS_DIR, ops: qm.QueueOps | None = None) -> html.Div:
    ops = ops if ops is not None else queue_ops(results_dir)
    rows = _load(results_dir, ops)
    cards, exhausted, count = card_view(rows, ALL, ALL, rm.FILTER_ALL, None)
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
                    "Sort by",
                    dcc.Dropdown(
                        id="rr-sort",
                        options=SORT_OPTIONS,
                        value="verdict",
                        clearable=False,
                        className="rr-select",
                    ),
                ],
                className="rr-label",
            ),
            html.Span(count, id="rr-count", className="rr-count"),
        ],
        className="rr-controls",
    )
    advanced = details(
        "Filters",
        html.Div(
            [
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
            ],
            className="rr-controls",
        ),
    )
    return html.Div(
        [
            html.Div([html.Span(TITLE, className="rr-title"), info(HINT)], className="rr-head"),
            page(
                html.Div(counts(rows), id="rr-keys"),
                [
                    queue_panel.layout(ops),
                    controls,
                    advanced,
                    dcc.Store(id="rr-limit", data=PAGE_SIZE),
                    html.Div(cards, id="rr-cards", className="rr-cards"),
                    html.Button(
                        "Show more",
                        id="rr-more",
                        n_clicks=0,
                        hidden=exhausted,
                        className="rr-button",
                    ),
                ],
            ),
        ],
        className="rr-page",
    )


def register_callbacks(
    app: Dash, results_dir: Path = RESULTS_DIR, ops: qm.QueueOps | None = None
) -> None:
    ops = ops if ops is not None else queue_ops(results_dir)

    @app.callback(
        Output("rr-cards", "children"),
        Output("rr-more", "hidden"),
        Output("rr-count", "children"),
        Output("rr-strategy", "options"),
        Output("rr-symbol", "options"),
        Output("rr-keys", "children"),
        Output("rr-limit", "data"),
        Input("rr-strategy", "value"),
        Input("rr-symbol", "value"),
        Input("rr-flagged", "value"),
        Input("rr-min-trades", "value"),
        Input("rr-sort", "value"),
        Input("rr-reload", "n_clicks"),
        Input("rr-more", "n_clicks"),
        State("rr-limit", "data"),
    )
    def _refresh(strategy, symbol, flagged, min_trades, sort_by, _reload, _more, limit):
        limit = (limit or PAGE_SIZE) + PAGE_SIZE if ctx.triggered_id == "rr-more" else PAGE_SIZE
        rows = _load(results_dir, ops)
        cards, exhausted, count = card_view(
            rows, strategy, symbol, flagged, min_trades, sort_by, limit
        )
        return (
            cards,
            exhausted,
            count,
            _strategy_options(rows),
            _symbol_options(rows),
            counts(rows),
            limit,
        )

    @app.callback(
        Output({"type": PIPELINE_ID, "rid": EVERY, "card": EVERY}, "children"),
        Output({"type": PIPELINE_ID, "rid": EVERY, "card": EVERY}, "className"),
        Input("qp-interval", "n_intervals"),
    )
    def _pipeline(_tick):
        ids = [o["id"] for o in ctx.outputs_list[0]]
        texts = qm.pipeline_texts([i["rid"] for i in ids], ops.queue, results_dir)
        shown = [texts.get(i["rid"]) for i in ids]
        return (
            [f"Pipeline: {t}" if t else "" for t in shown],
            [qm.pipeline_class(t) for t in shown],
        )

    queue_panel.register_callbacks(app, ops)
    parameter_heatmap.register_callbacks(app)
