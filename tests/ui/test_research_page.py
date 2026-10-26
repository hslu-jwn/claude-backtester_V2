"""Research page (ROADMAP 6.1 d2, 6.2): one row per research variant and per plain run.
Spec: research-runner.md > Research page. Pure row logic in ui/research_model.py."""

from __future__ import annotations

import csv
import json
import os

import pytest

from backtester.analytics.scorecard import FLAG_LABELS
from backtester.runner import TRADE_COLUMNS
from backtester.ui import app as app_module
from backtester.ui import nav
from backtester.ui import research_model as rm
from backtester.ui.pages import research, results

RID = "grid_abc123"


def _json(component) -> str:
    return json.dumps(component, default=lambda o: o.to_plotly_json())


def _write_csv(path, rows):
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows(rows)


def _run_folder(
    folder, symbols=("XAUUSD",), start="2020-01-01", end="2022-12-31", r=(1.0, -0.5),
    strategy="session_zone_sweep",
):  # fmt: skip
    """A normal run folder with six trades whose r_net cycle through `r`."""
    folder.mkdir(parents=True)
    rows = []
    for i in range(1, 7):
        year = 2020 + (i - 1) % 3
        net = r[i % len(r)]
        row = dict.fromkeys(TRADE_COLUMNS, "")
        row.update(
            id=i, symbol=symbols[0], direction="long", session="x",
            entry_time=f"{year}-03-02T08:05:00+00:00", entry_candle=f"{year}-03-02T08:00:00+00:00",
            entry=100.0, initial_stop=99.0, take_profit=101.0, tp1_share=1.0, planned_rr=1.0,
            exit_time=f"{year}-03-02T09:00:00+00:00", exit_price=101.0, exit_reason="take_profit",
            r_gross=net, r_net=net, confluence="fvg", parts="[]",
        )  # fmt: skip
        rows.append(row)
    _write_csv(folder / "trades.csv", rows)
    (folder / "summary.json").write_text(
        json.dumps({"run_id": folder.name, "symbols": list(symbols), "start": start, "end": end}),
        encoding="utf-8",
    )
    (folder / "settings.json").write_text(
        json.dumps({"preset": "my preset", "strategy": {"name": strategy}}), encoding="utf-8"
    )


def _variant_csv_row(vid, name, rank, net, trades=150, flags=""):
    return {
        "variant_id": vid, "variant": name, "rank": rank, "trades": trades, "win_rate": 0.45,
        "avg_r": net / trades, "net_r": net, "profit_factor": 1.2, "max_dd_r": 9.0,
        "half_first_net_r": net / 2, "half_second_net_r": net / 2, "net_r_stressed": net - 5,
        "net_r_without_best": net - 3, "flags": flags, "set.x": vid,
    }  # fmt: skip


@pytest.fixture
def results_dir(tmp_path):
    rd = tmp_path / "results"
    folder = rd / "research" / RID
    (folder / "variants").mkdir(parents=True)
    _write_csv(
        folder / "variants.csv",
        [
            _variant_csv_row("v1", "x=1", 1, 40.0),
            _variant_csv_row("v2", "x=2", 2, 20.0, flags="half_not_profitable;too_few_trades"),
            _variant_csv_row("v3", "x=3", "", -5.0, trades=30, flags="too_few_trades"),
        ],
    )
    _write_csv(
        folder / "test.csv",
        [
            {"test_run": 1, "variant_id": "v1", "variant": "x=1", "start": "2021-09-14",
             "end": "2026-10-01", "trades": 200, "net_r": 10.0, "deflated_sharpe": 0.4,
             "verdict": "yellow", "verdict_label": "weak edge", "flags": "", "run_folder": "T1"},
            {"test_run": 2, "variant_id": "v1", "variant": "x=1", "start": "2021-09-14",
             "end": "2026-10-01", "trades": 210, "net_r": -3.0, "deflated_sharpe": 0.1,
             "verdict": "red", "verdict_label": "no edge", "flags": "test_failed",
             "run_folder": "T2"},
        ],
    )  # fmt: skip
    (folder / "research.json").write_text(
        json.dumps(
            {
                "id": RID, "strategy": "opening_range", "symbols": ["NAS100", "US500"],
                "periods": {"development": {"start": "2018-01-02", "end": "2021-09-13"},
                            "test": {"start": "2021-09-14", "end": "2026-10-01"}},
                "chosen": {"id": "v1", "dev_run": "DEV1"},
                "test": {"status": "done", "run": 2},
            }
        ),
        encoding="utf-8",
    )  # fmt: skip
    for vid in ("v1", "v2", "v3"):
        _run_folder(folder / "variants" / vid)
    _run_folder(rd / "DEV1")  # the chosen dev copy: shown once, as the research row
    _run_folder(rd / "T1")
    _run_folder(rd / "T2")
    _run_folder(rd / "20261001-100000_XAUUSD", r=(1.0, 0.6))
    _run_folder(rd / "20261002-100000_GBPUSD", symbols=("GBPUSD",), r=(-1.0, -0.2))
    (rd / "20261003-100000_BAD").mkdir()
    (rd / "20261003-100000_BAD" / "summary.json").write_text("{not json", encoding="utf-8")
    (rd / "20261004-100000_NOTRADES").mkdir()
    return rd


@pytest.fixture(autouse=True)
def _clear_cache():
    rm.clear_cache()


def by_source(rows):
    return {r["source"]: r for r in rows}


def test_rows_one_per_variant_and_plain_run(results_dir):
    sources = [r["source"] for r in rm.load_rows(results_dir)]
    assert sorted(sources) == sorted(
        [f"{RID} v1", f"{RID} v2", f"{RID} v3", "20261001-100000_XAUUSD", "20261002-100000_GBPUSD"]
    )
    # the chosen dev copy and the test runs are not listed twice
    assert not any(s in ("DEV1", "T1", "T2") for s in sources)


def test_research_row_fields(results_dir):
    v2 = by_source(rm.load_rows(results_dir))[f"{RID} v2"]
    assert v2["strategy_name"] == "opening_range"
    assert v2["symbols"] == "NAS100, US500"
    assert v2["period"] == "2018-01-02 → 2021-09-13"
    assert v2["variant"] == "x=2" and v2["trades"] == 150 and v2["net_r"] == 20.0
    assert v2["win_rate"] == pytest.approx(45.0)  # shown in percent
    assert v2["test_net_r"] is None and v2["verdict"] == ""
    assert v2["flag_keys"] == ["half_not_profitable", "too_few_trades"]
    assert v2["href"] == f"/results/research~{RID}~v2"


def test_chosen_variant_carries_the_latest_test(results_dir):
    v1 = by_source(rm.load_rows(results_dir))[f"{RID} v1"]
    assert v1["test_net_r"] == -3.0 and v1["deflated_sharpe"] == pytest.approx(0.1)
    assert v1["verdict"] == "red" and v1["verdict_label"] == "no edge"
    assert "test_failed" in v1["flag_keys"]
    assert v1["href"] == "/results/DEV1"  # the chosen variant opens its dev run copy


def test_plain_run_scorecard_and_flags(results_dir):
    rows = by_source(rm.load_rows(results_dir))
    good, bad = rows["20261001-100000_XAUUSD"], rows["20261002-100000_GBPUSD"]
    assert good["trades"] == 6 and good["net_r"] == pytest.approx(3 * 1.0 + 3 * 0.6)
    assert good["strategy_name"] == "session_zone_sweep" and good["symbols"] == "XAUUSD"
    assert good["period"] == "2020-01-01 → 2022-12-31"
    assert good["test_net_r"] is None and good["verdict"] == ""
    assert "too_few_trades" in good["flag_keys"]  # 6 < 100
    assert bad["net_r"] < 0 and "not_profitable_without_best" in bad["flag_keys"]
    assert good["href"] == "/results/20261001-100000_XAUUSD"


def test_broken_and_empty_folders_are_skipped(results_dir):
    sources = [r["source"] for r in rm.load_rows(results_dir)]
    assert not any("BAD" in s or "NOTRADES" in s for s in sources)


def test_missing_results_dir_and_broken_research_files(tmp_path):
    assert rm.load_rows(tmp_path / "nothing") == []
    folder = tmp_path / "research" / "r1"
    folder.mkdir(parents=True)
    (folder / "research.json").write_text("garbage", encoding="utf-8")
    (folder / "variants.csv").write_text("variant_id\n", encoding="utf-8")
    assert rm.load_rows(tmp_path) == []
    (folder / "research.json").write_text("{}", encoding="utf-8")
    (folder / "variants.csv").write_text("variant_id,net_r,trades\nv1,abc,5\n,1,1\n", "utf-8")
    assert rm.load_rows(tmp_path) == []  # unreadable numbers: row skipped, no crash


def test_default_sort_verdict_then_test_then_dev(results_dir):
    rows = rm.sort_rows(rm.load_rows(results_dir))
    assert rows[0]["source"] == f"{RID} v1"  # a verdict before none
    rest = [r["net_r"] for r in rows[1:]]
    assert rest == sorted(rest, reverse=True)


def test_sort_green_first_then_test_net_r():
    def mk(v, test, dev):
        return {"verdict": v, "test_net_r": test, "net_r": dev}

    rows = [mk("", None, 99), mk("red", 5, 1), mk("green", 1, 1), mk("green", 7, 0),
            mk("yellow", 3, 3), mk("red", 5, 2)]  # fmt: skip
    got = [(r["verdict"], r["test_net_r"], r["net_r"]) for r in rm.sort_rows(rows)]
    assert got == [("green", 7, 0), ("green", 1, 1), ("yellow", 3, 3), ("red", 5, 2),
                   ("red", 5, 1), ("", None, 99)]  # fmt: skip


def test_filters(results_dir):
    rows = rm.load_rows(results_dir)
    assert {r["strategy_name"] for r in rm.filter_rows(rows, strategy="opening_range")} == {
        "opening_range"
    }
    gbp = rm.filter_rows(rows, symbol="GBPUSD")
    assert [r["source"] for r in gbp] == ["20261002-100000_GBPUSD"]
    assert len(rm.filter_rows(rows, symbol="NAS100")) == 3  # several symbols in a row
    assert all(not r["flag_keys"] for r in rm.filter_rows(rows, flagged="unflagged"))
    only = rm.filter_rows(rows, flagged="flagged")
    assert only and all(r["flag_keys"] for r in only)
    assert all(r["trades"] >= 100 for r in rm.filter_rows(rows, min_trades=100))
    assert len(rm.filter_rows(rows)) == len(rows)
    assert len(rm.filter_rows(rows, min_trades=None, strategy=None, symbol=None)) == len(rows)


def test_flag_text_short_with_full_label_tooltip():
    keys = ["too_few_trades", "test_failed"]
    assert rm.flag_text(keys) == "⚠ few trades · ⚠ test failed"
    assert rm.flag_tooltip(keys) == "too few trades; test failed"
    assert rm.flag_text([]) == "" and rm.flag_tooltip([]) == ""
    assert set(rm.FLAG_SHORT) == set(FLAG_LABELS)  # every flag has a short text


def test_table_rows_have_display_fields(results_dir):
    table = rm.table_rows(rm.sort_rows(rm.load_rows(results_dir)))
    first = table[0]
    assert first["id"] == first["source"]
    assert first["flags"].startswith("⚠") and first["flags_tooltip"]
    assert first["verdict_colour"] == "red"
    assert first["verdict"] == "red · no edge"
    assert "Source" in _json(research.card(first))


def test_cache_by_mtime(results_dir, monkeypatch):
    calls = []
    real = rm.read_trades
    monkeypatch.setattr(rm, "read_trades", lambda folder: calls.append(folder) or real(folder))
    rm.load_rows(results_dir)
    n = len(calls)
    assert n >= 2
    rm.load_rows(results_dir)
    assert len(calls) == n  # nothing re-read
    trades = results_dir / "20261001-100000_XAUUSD" / "trades.csv"
    st = trades.stat()
    os.utime(trades, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
    rm.load_rows(results_dir)
    assert len(calls) == n + 1  # only the changed run
    rm.load_rows(results_dir)
    assert len(calls) == n + 1


def test_a_new_run_is_picked_up(results_dir):
    before = len(rm.load_rows(results_dir))
    _run_folder(results_dir / "20261009-100000_XAUUSD")
    assert len(rm.load_rows(results_dir)) == before + 1  # the folder listing is never cached


def test_results_page_opens_a_research_variant_folder(results_dir):
    token = f"research~{RID}~v2"
    assert results.run_folder(token, results_dir) == (
        results_dir / "research" / RID / "variants" / "v2"
    )
    for bad in ("research~..~..", f"research~{RID}~nope", "research~a/b~c", "research~x"):
        assert results.run_folder(bad, results_dir) is None
    assert "Run not found" not in _json(results.layout(token, results_dir))


def test_page_route_nav_and_app(results_dir):
    assert research.PATH == "/research"
    assert nav.section_of("/research") == "research"
    cls = nav.link_classes("/research", False)
    assert "active" in cls["research"] and "active" not in cls["backtest"]
    assert '"href": "/research"' in _json(nav.layout())
    page = _json(research.layout(results_dir))
    assert "rr-cards" in page and "Reload" in page and "rr-table" not in page
    assert "rr-cards.children" in " ".join(app_module.create_app().callback_map)


def test_click_opens_the_row_link(results_dir):
    table = rm.table_rows(rm.load_rows(results_dir))
    cell = {"row_id": f"{RID} v2", "column_id": "source"}
    assert research.href_for_click(cell, table) == f"/results/research~{RID}~v2"
    assert research.href_for_click(None, table) is None
    assert research.href_for_click({"row_id": "nope"}, table) is None


NEW_FIELDS = (
    "rc_p",
    "pbo",
    "n_eff",
    "p_mean_pos",
    "detrended_net_r",
    "lower95",
    "sensitivity",
    "wfe",
    "mc_dd_p95_pct",
    "prop_pass_pct",
    "monkey",
    "best_regime",
    "best_condition",
)


def _diagnostics(rd):
    folder = rd / "research" / RID
    data = json.loads((folder / "research.json").read_text("utf-8"))
    data.update(
        idea="Trade the opening range",
        sensitivity={"status": "gentle"},
        walk_forward={"efficiency": 0.65},
    )
    (folder / "research.json").write_text(json.dumps(data), "utf-8")
    files = {
        "significance.json": {
            "reality_check": {"p_value": 0.03},
            "pbo": {"pbo": 0.2},
            "effective_trials": {"n": 3, "n_eff": 2.5},
        },
        "bayes.json": {
            "development": {"mean_r": {"p_positive": 0.97}, "evidence": {"posterior_odds": 4.0}}
        },
        "skill_bounds.json": {
            "development": {
                "scores": {"detrended_net_r": 25.0, "lower95_mean_daily_r": 0.02, "log_pf": 0.3}
            }
        },
        "monkeys.json": {
            "available": True,
            "kinds": [
                {
                    "kind": 1,
                    "passed": True,
                    "net_r": {"percentile": 96},
                    "max_dd_r": {"percentile": 93},
                }
            ],
        },
        "profile.json": {
            "development": {
                "dimensions": {"regime": {"best": "up / low"}},
                "strongest_skill_cells": [
                    {"dimension": "session", "condition": "London", "lower90_bca": 0.2}
                ],
            }
        },
    }
    for name, content in files.items():
        (folder / name).write_text(json.dumps(content), "utf-8")
    _write_csv(folder / "sensitivity.csv", [{"setting": "x", "status": "done", "net_r": 25}])
    _write_csv(folder / "walk_forward.csv", [{"window": 1, "wfe": 0.65}])
    _write_csv(folder / "grid.csv", [{"variant_id": "v1", "net_r": 40}])
    (rd / "DEV1" / "drawdown_bounds.json").write_text('{"available": true}', "utf-8")
    mc = rd / "monte_carlo" / "DEV1"
    mc.mkdir(parents=True)
    (mc / "summary.json").write_text(
        json.dumps(
            {
                "monte_carlo": {
                    "risks": {
                        "0.005": {
                            "stats": {"max_dd_pct": {"p95": 4}},
                            "ftmo": {"pass_probability": 0.9},
                        },
                        "0.01": {
                            "stats": {"max_dd_pct": {"p95": 8}},
                            "ftmo": {"pass_probability": 0.75},
                        },
                        "0.015": {
                            "stats": {"max_dd_pct": {"p95": 12}},
                            "ftmo": {"pass_probability": 0.6},
                        },
                    }
                }
            }
        ),
        "utf-8",
    )


def test_all_diagnostics_are_chosen_only_and_cards_filled(results_dir):
    _diagnostics(results_dir)
    rows = rm.load_rows(results_dir)
    chosen = by_source(rows)[f"{RID} v1"]
    expected = [
        0.03,
        0.2,
        2.5,
        0.97,
        25,
        0.02,
        "gentle",
        0.65,
        8,
        75,
        "pass",
        "up / low",
        "session: London",
    ]
    assert [chosen[k] for k in NEW_FIELDS] == expected
    assert chosen["idea"] == "Trade the opening range"
    assert chosen["n"] == 3 and chosen["posterior_odds"] == 4
    assert chosen["monkey_net_percentile"] == 96 and chosen["monkey_dd_percentile"] == 93
    for row in rows[1:]:
        assert all(row[k] is None for k in NEW_FIELDS)
    rendered = _json(research.card(chosen))
    for text in (
        "RC p",
        "PBO",
        "N / N_eff",
        "P(mean",
        "WFE",
        "Open results",
        "Detrended",
        "MC DD p95",
        "Prop pass %",
        "London",
        "Costs x1.5",
    ):
        assert text in rendered
    assert chosen["href"] in rendered


def test_optional_diagnostics_missing_broken_and_cache_refresh(results_dir):
    chosen = by_source(rm.load_rows(results_dir))[f"{RID} v1"]
    assert all(chosen[k] is None for k in NEW_FIELDS)
    assert chosen["idea"] == chosen["strategy"]
    assert "\\u2013" in _json(research.card(chosen))
    _diagnostics(results_dir)  # cached missing files must be invalidated
    assert by_source(rm.load_rows(results_dir))[f"{RID} v1"]["rc_p"] == 0.03
    folder = results_dir / "research" / RID
    for name in ("significance", "bayes", "skill_bounds", "monkeys", "profile"):
        (folder / f"{name}.json").write_text("{broken", "utf-8")
    chosen = by_source(rm.load_rows(results_dir))[f"{RID} v1"]
    for key in (
        "rc_p",
        "pbo",
        "n_eff",
        "p_mean_pos",
        "detrended_net_r",
        "lower95",
        "monkey",
        "best_condition",
        "best_regime",
    ):
        assert chosen[key] is None
    (folder / "profile.json").write_text('{"development": {"strongest_skill_cells": []}}', "utf-8")
    assert by_source(rm.load_rows(results_dir))[f"{RID} v1"]["best_condition"] == "none"
    (folder / "significance.json").write_text('{"reality_check": [], "pbo": "bad"}', "utf-8")
    assert by_source(rm.load_rows(results_dir))[f"{RID} v1"]["rc_p"] is None
    mc = results_dir / "monte_carlo" / "DEV1" / "summary.json"
    mc.write_text("[]", "utf-8")
    assert by_source(rm.load_rows(results_dir))[f"{RID} v1"]["mc_dd_p95_pct"] is None
    assert rm._num("nan") is None and rm._num("inf") is None


@pytest.mark.parametrize(
    "sort_by",
    [
        "verdict",
        "test_net_r",
        "net_r",
        "avg_r",
        "profit_factor",
        "max_dd_r",
        "detrended_net_r",
        "rc_p",
    ],
)
def test_each_card_sort_and_plain_runs_last(sort_by):
    a = {
        "source": "a",
        "is_research": True,
        "verdict": "green",
        "test_net_r": 4,
        "net_r": 10,
        "avg_r": 0.2,
        "profit_factor": 2,
        "max_dd_r": 2,
        "detrended_net_r": 9,
        "rc_p": 0.01,
    }
    b = {
        **a,
        "source": "b",
        "verdict": "yellow",
        "test_net_r": 2,
        "net_r": 5,
        "avg_r": 0.1,
        "profit_factor": 1.2,
        "max_dd_r": 4,
        "detrended_net_r": 3,
        "rc_p": 0.2,
    }
    missing = {"source": "missing", "is_research": True}
    plain = {**a, "source": "plain", "is_research": False, "net_r": 999}
    assert [r["source"] for r in rm.sort_card_rows([plain, b, missing, a], sort_by)] == [
        "a",
        "b",
        "missing",
        "plain",
    ]


def test_card_paging_wrapping_and_control_ids(results_dir):
    from dash import dash_table, html

    from tests.ui.test_v25a_theme import walk

    rows = rm.load_rows(results_dir) * 25
    first, more, count = research.card_view(rows, research.ALL, research.ALL, "all", None)
    assert len(first) == 50 and more is False and count == "50 of 125 rows"
    second, more, _ = research.card_view(rows, research.ALL, research.ALL, "all", None, limit=100)
    assert len(second) == 100 and more is False
    last, more, _ = research.card_view(rows, research.ALL, research.ALL, "all", None, limit=150)
    assert len(last) == 125 and more is True
    filtered, _, _ = research.card_view(rows, research.ALL, "GBPUSD", "all", None)
    assert len(filtered) == 25
    nodes = list(walk(research.layout(results_dir)))
    assert not any(isinstance(n, dash_table.DataTable) for n in nodes)
    assert all(n.open is False for n in nodes if isinstance(n, html.Details))
    ids = {i for n in nodes if isinstance(i := getattr(n, "id", ""), str)}  # pattern ids are dicts
    assert {
        "rr-cards",
        "rr-sort",
        "rr-more",
        "rr-limit",
        "rr-keys",
        "rr-count",
        "rr-strategy",
        "rr-symbol",
        "rr-flagged",
        "rr-min-trades",
        "rr-reload",
    } <= ids
    css = (research.Path(research.__file__).parents[1] / "assets/research.css").read_text("utf-8")
    assert "flex-wrap: wrap" in css and "overflow-wrap: anywhere" in css
    assert "overflow-x: auto" not in css.lower() and "nowrap" not in css


def test_grid_idea_is_optional_text(tmp_path):
    from backtester.tools.research_grid import GridError, load_grid

    path = tmp_path / "grid.toml"
    base = 'strategy = "opening_range"\nsymbols = ["US500"]\n'
    path.write_text(base + 'idea = "Trade the opening range"\n', "utf-8")
    assert load_grid(path).idea == "Trade the opening range"
    path.write_text(base, "utf-8")
    assert load_grid(path).idea == ""
    path.write_text(base + "idea = 42\n", "utf-8")
    with pytest.raises(GridError, match="idea"):
        load_grid(path)


def test_callback_show_more_and_filter_sort_reload_reset(results_dir, monkeypatch):
    from types import SimpleNamespace

    from dash import Dash

    app = Dash(__name__)
    research.register_callbacks(app, results_dir)
    callback = next(iter(app.callback_map.values()))["callback"].__wrapped__
    rows = rm.load_rows(results_dir) * 25
    monkeypatch.setattr(rm, "load_rows", lambda _: rows)
    monkeypatch.setattr(research, "ctx", SimpleNamespace(triggered_id="rr-more"))
    values = callback(research.ALL, research.ALL, "all", None, "net_r", 0, 1, 50)
    assert len(values[0]) == 100 and values[-1] == 100 and values[1] is False
    assert "125" in _json(values[5])  # key strip counts all rows
    for trigger in (
        "rr-strategy",
        "rr-symbol",
        "rr-flagged",
        "rr-min-trades",
        "rr-sort",
        "rr-reload",
    ):
        monkeypatch.setattr(research, "ctx", SimpleNamespace(triggered_id=trigger))
        values = callback(research.ALL, research.ALL, "all", None, "net_r", 1, 1, 100)
        assert len(values[0]) == 50 and values[-1] == 50


def test_grid_idea_written_to_research_metadata(tmp_path, monkeypatch):
    from datetime import date

    from backtester.tools import research as runner

    path = tmp_path / "idea.toml"
    path.write_text(
        'strategy = "opening_range"\nsymbols = ["US500"]\nidea = "Opening idea"', "utf-8"
    )
    monkeypatch.setattr(runner, "cached_span", lambda *a: (date(2020, 1, 1), date(2022, 1, 1)))

    def stop_before_execution(*args, **kwargs):
        raise RuntimeError("stop before backtest")

    monkeypatch.setattr(runner, "run_period_many", stop_before_execution)
    with pytest.raises(RuntimeError, match="stop before backtest"):
        runner.run_research(path, results_dir=tmp_path / "results", log=lambda *a: None)
    saved = next((tmp_path / "results/research").glob("*/research.json"))
    assert json.loads(saved.read_text("utf-8"))["idea"] == "Opening idea"


def test_additional_flags_have_readable_full_labels():
    assert rm.flag_tooltip(["monkey_beaten"]) == "matched random strategies beat the strategy"
    assert "monkey_beaten" not in rm.flag_text(["monkey_beaten"])


def test_optional_diagnostics_render_as_wrapping_metrics():
    from dash import html

    from tests.ui.test_v25a_theme import walk

    nodes = list(walk(research.diagnostic_tiles({"bounds_r": {"lower95": 0.25}})))
    assert not any(isinstance(n, html.Pre) for n in nodes)
    rendered = _json(nodes)
    assert "Bounds R" in rendered and "0.25" in rendered


def test_research_rows_name_their_folder_and_the_card_shows_the_pipeline(results_dir):
    rows = rm.load_rows(results_dir)
    research_rows = [r for r in rows if r["is_research"]]
    assert research_rows and all(r["research_id"] == RID for r in research_rows)
    assert all("research_id" not in r or not r["research_id"] for r in rows if not r["is_research"])
    folder = results_dir / "research" / RID
    (folder / "pipeline.json").write_text(
        json.dumps(
            {"state": "running", "current": "monte_carlo",
             "steps": [{"name": n, "state": "pending"} for n in ("research", "monte_carlo", "card_inputs")]}
        ),
        encoding="utf-8",
    )  # fmt: skip
    page = _json(research.layout(results_dir))
    assert "Pipeline: step 2 of 3: monte_carlo" in page
    assert "qp-panel" in page
