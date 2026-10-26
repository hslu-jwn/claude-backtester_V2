"""Development-only slices of a saved grid's variant table. Spec: V2.6 step 5."""

import html as html_escape

import plotly.graph_objects as go
from dash import MATCH, Input, Output, State, dcc, html

from backtester.ui.theme import color

METRICS = {"net_r": "Net R", "avg_r": "R per trade", "win_rate": "Win rate", "trades": "Trades"}


def varied_parameters(rows):
    return [
        key
        for key in (rows[0] if rows else {})
        if key.startswith("set.") and len({str(r.get(key)) for r in rows}) > 1
    ]


def heatmap(rows, chosen, x, y, metric):
    varied = varied_parameters(rows)
    if x == y or x not in varied or y not in varied or metric not in METRICS:
        raise ValueError("Choose two different varied parameters and a development metric")
    selected = next(r for r in rows if r["variant_id"] == chosen)
    fixed = [p for p in varied if p not in (x, y)]

    def values(p):
        vals = {str(r[p]) for r in rows}
        try:
            return sorted(vals, key=float)
        except ValueError:
            return sorted(vals)

    xs, ys = values(x), values(y)
    cells = {
        (str(r[x]), str(r[y])): r for r in rows if all(str(r[p]) == str(selected[p]) for p in fixed)
    }
    z, texts = [], []
    for yy in ys:
        line, tips = [], []
        for xx in xs:
            row = cells.get((xx, yy))
            value = None if row is None else row.get(metric)
            line.append(None if value in (None, "") else float(value))
            tips.append(
                ""
                if row is None
                else "<br>".join(html_escape.escape(f"{k}: {v}") for k, v in row.items())
            )
        z.append(line)
        texts.append(tips)
    r_metric = metric in {"net_r", "avg_r"}
    fig = go.Figure(
        go.Heatmap(
            x=xs,
            y=ys,
            z=z,
            text=texts,
            hoverongaps=False,
            hovertemplate="%{text}<extra></extra>",
            zmid=0 if r_metric else None,
            colorscale=[[0, color("red")], [0.5, color("panel")], [1, color("green")]]
            if r_metric
            else [[0, color("panel")], [1, color("accent")]],
            colorbar={"title": METRICS[metric]},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[str(selected[x])],
            y=[str(selected[y])],
            mode="markers",
            marker={
                "symbol": "square-open",
                "size": 22,
                "color": color("text"),
                "line": {"width": 3},
            },
            name="Chosen variant",
            hovertemplate=html_escape.escape(chosen) + "<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor=color("panel"),
        plot_bgcolor=color("panel"),
        font={"color": color("text")},
        xaxis_title=x.removeprefix("set."),
        yaxis_title=y.removeprefix("set."),
        xaxis_type="category",
        yaxis_type="category",
        margin={"l": 55, "r": 25, "t": 30, "b": 65},
    )
    return fig


def panel(rows, chosen, identity):
    varied = varied_parameters(rows)
    if len(varied) < 2:
        return html.P("Parameter heat map: this grid has fewer than two varied parameters.")

    def id_(kind):
        return {"type": f"heatmap-{kind}", "index": identity}

    return html.Details(
        [
            html.Summary("Parameter heat map · development only"),
            dcc.Store(id=id_("data"), data={"rows": rows, "chosen": chosen}),
            dcc.Dropdown(varied, varied[0], id=id_("x"), clearable=False),
            dcc.Dropdown(varied, varied[1], id=id_("y"), clearable=False),
            dcc.Dropdown(
                [{"label": v, "value": k} for k, v in METRICS.items()],
                "net_r",
                id=id_("metric"),
                clearable=False,
            ),
            dcc.Graph(id=id_("figure"), figure=heatmap(rows, chosen, *varied[:2], "net_r")),
        ]
    )


def register_callbacks(app):
    @app.callback(
        Output({"type": "heatmap-figure", "index": MATCH}, "figure"),
        Input({"type": "heatmap-x", "index": MATCH}, "value"),
        Input({"type": "heatmap-y", "index": MATCH}, "value"),
        Input({"type": "heatmap-metric", "index": MATCH}, "value"),
        State({"type": "heatmap-data", "index": MATCH}, "data"),
    )
    def update(x, y, metric, data):
        if x == y:
            fig = go.Figure()
            fig.add_annotation(text="Choose two different parameters", showarrow=False)
            return fig
        return heatmap(data["rows"], data["chosen"], x, y, metric)
