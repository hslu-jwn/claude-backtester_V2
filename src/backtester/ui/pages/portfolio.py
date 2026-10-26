"""Portfolio candidates, development only. Spec: docs/portfolio.md."""

from __future__ import annotations

import json
import re
from pathlib import Path

import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dash_table, dcc, html, no_update

from backtester.analytics.portfolio_search import CUTOFF
from backtester.paths import RESULTS_DIR
from backtester.tools import portfolio_candidates as pc
from backtester.ui import queue_model as qm
from backtester.ui import queue_panel
from backtester.ui.layout import details, info, key_strip, page
from backtester.ui.theme import color

PATH = "/portfolio"
METRICS = [
    ("Net R", "net_r"),
    ("Max DD (R)", "max_dd_r"),
    ("Net R / max DD", "net_dd"),
    ("Daily Sharpe (252)", "sharpe"),
    ("Worst month (R)", "worst_month"),
    ("Longest DD (days)", "longest_dd_days"),
    ("Average correlation", "avg_correlation"),
    ("IDM (not applied)", "idm"),
    ("Common days", "common_days"),
    ("Dropped days", "dropped_days"),
]


def _table(id_, rows, columns, **kwargs):
    return dash_table.DataTable(
        id=id_,
        data=rows,
        columns=columns,
        sort_action="native",
        page_size=20,
        style_as_list_view=True,
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": "var(--panel)", "color": "var(--text)"},
        style_cell={
            "backgroundColor": "var(--bg)",
            "color": "var(--text)",
            "borderColor": "var(--line)",
            "padding": "8px",
            "textAlign": "left",
            "fontFamily": "inherit",
            "whiteSpace": "normal",
            "height": "auto",
        },
        **kwargs,
    )


def table_rows(rows):
    keys = [key for _, key in METRICS]
    return [
        {
            "id": r["id"],
            "members": " + ".join(r["members"]),
            "flags": "; ".join(r["flags"]),
            **{k: r.get(k) for k in keys},
        }
        for r in rows
    ]


def _columns():
    return [
        {"name": "Members", "id": "members"},
        *[{"name": label, "id": key, "type": "numeric"} for label, key in METRICS],
        {"name": "Warnings", "id": "flags"},
    ]


def _options(pool):
    return [
        {
            "value": m.id,
            "label": f"{m.id} | {m.strategy} | {', '.join(m.symbols)} | "
            f"{sum(m.values):+.2f} R | {'; '.join(m.flags) or 'no flags'}",
        }
        for m in pool
    ]


def layout(results_dir=RESULTS_DIR, *, include_queue=True):
    pool, errors = pc.load_members(results_dir)
    main = [
        html.Div(
            [
                html.H2("Portfolio"),
                info(
                    "Choose 2–12 development members; all sets of 2–4, equal weights. "
                    "Daily R is exit-booked on Prague weekdays; joint zero days count. "
                    "Numbers support your choice; no pass/fail verdict."
                ),
            ],
            className="rr-head",
        ),
        html.P("Development only · before 2021-09-14 · equal weights"),
        html.Button("Reload members", id="pf-reload", className="rr-button"),
        dcc.Dropdown(
            id="pf-pool",
            options=_options(pool),
            multi=True,
            placeholder="Pick a pool of 2–12 chosen research variants",
            className="rr-select",
        ),
        html.Div(
            [
                html.Button("Find combinations", id="pf-find", className="rr-button"),
                html.Button("Monte Carlo top 10", id="pf-mc", className="rr-button"),
                info(
                    "Sort the table to choose the top ten. Default: net R / max DD, descending. "
                    "Undefined ratios sort last. Monte Carlo is queued; start the runner in the queue panel."
                ),
            ],
            className="rr-controls",
        ),
        html.Div("; ".join(errors), id="pf-errors", role="status"),
        html.Div(id="pf-message", role="status"),
        html.Div(id="pf-mc-message", role="status"),
        dcc.Store(id="pf-search"),
        _table(
            "pf-sets",
            [],
            _columns(),
            sort_by=[{"column_id": "net_dd", "direction": "desc"}],
            cell_selectable=True,
        ),
        html.Div(id="pf-detail"),
        html.Div(id="pf-detail-mc"),
        dcc.Interval(id="pf-refresh", interval=5000),
    ]
    if include_queue:
        main.append(queue_panel.layout(qm.QueueOps(qm.make_queue(results_dir))))
    return page(
        key_strip(
            [
                {"label": "Eligible development members", "value": len(pool)},
                {"label": "Weights", "value": "Equal"},
            ]
        ),
        main,
    )


def _read_search(key, results_dir):
    if not isinstance(key, str) or not re.fullmatch(r"[a-f0-9]{20}", key):
        raise ValueError("Find combinations first")
    return json.loads(
        (Path(results_dir) / "portfolio" / f"search_{key}.json").read_text(encoding="utf-8")
    )


def monte_carlo_rows(row, results_dir):
    """Read only a development summary for the current saved member content."""
    path = Path(results_dir) / "portfolio" / row["id"] / "summary.json"
    try:
        summary = json.loads(path.read_text(encoding="utf-8"))
        meta = summary["meta"]
        if meta["source"] != "development" or meta["end"] >= CUTOFF.isoformat():
            return []
        pool, _ = pc.load_members(results_dir)
        by_id = {m.id: m for m in pool}
        if summary.get("fingerprint") != pc.pool_hash([by_id[i] for i in row["members"]]):
            return []
        risks = summary["monte_carlo"]["risks"]
        return [
            {
                "risk_pct": float(level) * 100,
                "pass_pct": value["ftmo"]["pass_probability"] * 100,
                "median_days_to_pass": value["ftmo"]["median_days_to_pass"],
            }
            for level, value in sorted(risks.items(), key=lambda p: float(p[0]))
        ]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def set_details(row, results_dir):
    equity = go.Figure(
        go.Scatter(x=row["days"], y=row["equity"], mode="lines", name="Equal-weight R")
    )
    equity.update_layout(template="plotly_dark", title="Combined development equity (R)")
    matrix = go.Figure(
        go.Heatmap(
            z=row["correlation"],
            x=row["members"],
            y=row["members"],
            zmin=-1,
            zmax=1,
            colorscale="RdBu",
        )
    )
    matrix.update_layout(
        template="plotly_dark", title="Pearson correlation · common development days"
    )
    for figure in (equity, matrix):
        figure.update_layout(
            paper_bgcolor=color("bg"), plot_bgcolor=color("panel"), font={"color": color("text")}
        )
    regime_rows = [
        {"symbol": s, "regime": label, **g}
        for s, groups in row["regimes"].items()
        for label, g in groups.items()
    ]
    loo = [
        {"removed": name, **{key: value.get(key) for _, key in METRICS}}
        for name, value in row["leave_one_out"].items()
    ]
    return html.Div(
        [
            html.H3(" + ".join(row["members"])),
            html.P(f"Set ID: {row['id']}"),
            html.P(
                f"{row['common_days']} common days; {row['dropped_days']} union days dropped. "
                f"Dropped per member: {row['dropped_by_member']}"
            ),
            dcc.Graph(figure=equity),
            dcc.Graph(figure=matrix),
            details(
                "Regimes by symbol",
                [
                    html.P(
                        "Each symbol conditions the entire combined daily R separately, "
                        "using its last closed D1 at Prague midnight. Rows across symbols overlap; do not add them."
                    ),
                    _table(
                        "pf-regimes",
                        regime_rows,
                        [
                            {"name": k, "id": k}
                            for k in ("symbol", "regime", "days", "net_r", "r_per_day")
                        ],
                    ),
                ],
            ),
            details(
                "Leave one member out (remaining members' common days)",
                _table(
                    "pf-loo",
                    loo,
                    [
                        {"name": "Removed", "id": "removed"},
                        *[{"name": label, "id": key, "type": "numeric"} for label, key in METRICS],
                    ],
                ),
            ),
        ]
    )


def monte_carlo_details(row, results_dir):
    mc_rows = monte_carlo_rows(row, results_dir)
    return html.Div(
        [
            html.H4("Development Monte Carlo / prop-firm"),
            _table(
                "pf-mc-results",
                mc_rows,
                [
                    {"name": k, "id": k, "type": "numeric"}
                    for k in ("risk_pct", "pass_pct", "median_days_to_pass")
                ],
            )
            if mc_rows
            else html.P("Not available yet."),
        ]
    )


def register_callbacks(app: Dash, results_dir=RESULTS_DIR):
    @app.callback(
        Output("pf-pool", "options"),
        Output("pf-errors", "children"),
        Input("pf-reload", "n_clicks"),
        prevent_initial_call=True,
    )
    def _reload(_):
        pool, errors = pc.load_members(results_dir)
        return _options(pool), "; ".join(errors)

    @app.callback(
        Output("pf-search", "data"),
        Output("pf-sets", "data"),
        Output("pf-message", "children"),
        Input("pf-find", "n_clicks"),
        State("pf-pool", "value"),
        prevent_initial_call=True,
    )
    def _find(_, ids):
        try:
            pool, _errors = pc.load_members(results_dir)
            by_id = {m.id: m for m in pool}
            chosen = [by_id[i] for i in (ids or [])]
            rows = pc.cached_search(chosen, results_dir)
            return (
                pc.search_hash(chosen),
                table_rows(rows),
                f"{len(rows)} development combinations. Click a row for details.",
            )
        except (ValueError, OSError, KeyError) as exc:
            return None, [], str(exc)

    @app.callback(
        Output("pf-mc-message", "children"),
        Input("pf-mc", "n_clicks"),
        State("pf-search", "data"),
        State("pf-sets", "sort_by"),
        prevent_initial_call=True,
    )
    def _queue(_, key, sort_by):
        try:
            saved = _read_search(key, results_dir)
            pool, _errors = pc.load_members(results_dir)
            by_id = {m.id: m for m in pool}
            parts = [by_id[i] for i in saved["pool"]]
            if pc.search_hash(parts) != key:
                raise ValueError("Member data changed; find combinations again")
            sort = (sort_by or [{"column_id": "net_dd", "direction": "desc"}])[0]
            if sort["column_id"] not in pc.SORT_KEYS:
                raise ValueError("Sort by a numeric search metric to rank Monte Carlo candidates")
            jobs = pc.queue_top(
                saved["sets"],
                parts,
                sort["column_id"],
                qm.make_queue(results_dir),
                results_dir,
                sort["direction"] == "desc",
            )
            return f"Queued {len(jobs)} development Monte Carlo jobs; completed/active jobs are reused."
        except (ValueError, OSError, KeyError) as exc:
            return str(exc)

    @app.callback(
        Output("pf-detail", "children"),
        Input("pf-sets", "active_cell"),
        Input("pf-search", "data"),
    )
    def _detail(cell, key):
        if not cell or not key:
            return "Select a combination."
        try:
            rows = _read_search(key, results_dir)["sets"]
            row = next((r for r in rows if r["id"] == cell.get("row_id")), None)
            return set_details(row, results_dir) if row else "Select a combination."
        except (ValueError, OSError, KeyError):
            return no_update

    @app.callback(
        Output("pf-detail-mc", "children"),
        Input("pf-sets", "active_cell"),
        Input("pf-search", "data"),
        Input("pf-refresh", "n_intervals"),
    )
    def _detail_mc(cell, key, _tick):
        if not cell or not key:
            return ""
        try:
            rows = _read_search(key, results_dir)["sets"]
            row = next((r for r in rows if r["id"] == cell.get("row_id")), None)
            return monte_carlo_details(row, results_dir) if row else ""
        except (ValueError, OSError, KeyError):
            return no_update
