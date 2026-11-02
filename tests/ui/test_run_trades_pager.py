"""Pagination of newest-run trades on the chart."""

import json
from datetime import timedelta
from types import SimpleNamespace

from dash import Dash
from plotly.utils import PlotlyJSONEncoder
from test_chart_side import T0, csv_row, make_trade, write_run

from backtester.data.sources import SymbolSources
from backtester.ui import chart_side
from backtester.ui.pages import chart


def trades(n):
    return [
        make_trade(i, "US500" if i % 2 else "NAS100", T0 + timedelta(minutes=i))
        for i in reversed(range(n))
    ]


def callback(app, output):
    return next(v["callback"].__wrapped__ for k, v in app.callback_map.items() if output in k)


def test_trade_page_clamps_and_slices():
    items = trades(250)
    first, page, pages = chart_side.trade_page(items, "time", 1)
    assert [t.id for t in first] == list(range(100))
    assert (page, pages) == (1, 3)
    last, page, pages = chart_side.trade_page(items, "time", 3)
    assert [t.id for t in last] == list(range(200, 250))
    assert (page, pages) == (3, 3)
    assert chart_side.trade_page(items, "time", 4) == (last, 3, 3)
    for invalid in (0, None, -2):
        assert chart_side.trade_page(items, "time", invalid) == (first, 1, 3)
    assert chart_side.trade_page([], "time", 1) == ((), 1, 1)


def test_pair_sort_continues_across_boundary():
    items = trades(250)
    first = chart_side.trade_page(items, "pair", 1)[0]
    second = chart_side.trade_page(items, "pair", 2)[0]
    assert [t.id for t in first + second] == list(range(0, 250, 2)) + list(range(1, 150, 2))


def test_newest_rows_and_empty(tmp_path):
    assert chart.newest_trade_rows(tmp_path)[1:] == ("No trades.", 1, 1)
    write_run(
        tmp_path,
        "20261001-090000_A",
        [
            csv_row(1, "2026-09-02T10:00:00+00:00", 1, "US500"),
            csv_row(2, "2026-09-02T09:00:00+00:00", -1, "NAS100"),
            csv_row(3, "2026-09-02T08:00:00+00:00", 1, "US500"),
        ],
    )
    rows, label, page, pages = chart.newest_trade_rows(tmp_path)
    assert [b.id["index"] for b in rows.children] == [3, 2, 1]
    assert all("--pair-rank" not in (getattr(b, "style", None) or {}) for b in rows.children)
    assert (label, page, pages) == ("1-3 of 3", 1, 1)
    assert chart.newest_trade_rows(tmp_path, "pair")[0].children[0].id["index"] == 2


def test_layout_does_not_embed_trades(tmp_path):
    write_run(
        tmp_path,
        "20261001-090000_A",
        [csv_row(i, (T0 + timedelta(minutes=i)).isoformat(), 1) for i in range(1000)],
    )
    layout = chart.layout(SymbolSources({}), results_dir=tmp_path)
    assert "run-trade'" not in str(layout)
    for id_ in ("run-trades-prev", "run-trades-next", "run-trades-label", "run-trades-page"):
        assert id_ in str(layout)
    assert len(json.dumps(layout, cls=PlotlyJSONEncoder)) < 400_000


def test_page_and_render_callbacks(tmp_path, monkeypatch):
    write_run(
        tmp_path,
        "20261001-090000_A",
        [csv_row(i, (T0 + timedelta(minutes=i)).isoformat(), 1) for i in range(250)],
    )
    app = Dash(__name__)
    chart.register_callbacks(app, SymbolSources({}), results_dir=tmp_path)
    page = callback(app, "run-trades-page.data")
    for trigger, current, expected in [
        ("run-trades-next", 1, 2),
        ("run-trades-next", 3, 3),
        ("run-trades-prev", 1, 1),
        ("run-trades-sort", 3, 1),
    ]:
        monkeypatch.setattr(chart, "ctx", SimpleNamespace(triggered_id=trigger))
        assert page(1, 1, "time", current) == expected
    render = callback(app, "run-trades-label.children")
    rows, label, prev, next_ = render("time", 3)
    assert len(rows.children) == 50
    assert (label, prev, next_) == ("201-250 of 250", False, True)
    assert render("time", 1)[2:] == (True, False)
