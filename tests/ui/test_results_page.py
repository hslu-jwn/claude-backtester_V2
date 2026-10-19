"""Results page: header, run selector, symbol filter, tabs, trade link to the chart.
Spec: ROADMAP.md › 3.6. Numbers come from analytics/metrics.py (tested there); these tests
check the page shows them for the right trades."""

from __future__ import annotations

import csv
import json
from datetime import date

import pytest

from backtester.analytics.records import read_trades
from backtester.data.sources import SymbolSources
from backtester.runner import TRADE_COLUMNS
from backtester.ui import app as app_module
from backtester.ui.pages import results
from backtester.ui.pages.chart import focus_from_query, focus_selection, initial_dates

RUN = "20261008-120000_XAUUSD-GBPUSD"


def row(id_, symbol, direction, session, entry, exit_, r_gross, r_net, **kw):
    out = dict.fromkeys(TRADE_COLUMNS, "")
    out.update(
        id=id_, symbol=symbol, direction=direction, session=session,
        entry_time=entry, entry_candle=entry.replace(":05:", ":00:"), entry=100.0,
        initial_stop=99.0, take_profit=101.2, tp1_share=1.0, planned_rr=1.2,
        exit_time=exit_, exit_price=100.0 + r_gross, exit_reason="take_profit" if r_net > 0
        else "stop_loss", r_gross=r_gross, r_net=r_net, confluence="fvg",
        parts=json.dumps([{"share": 1.0, "reason": "take_profit" if r_net > 0 else "stop_loss"}]),
    )  # fmt: skip
    out.update(kw)
    return out


@pytest.fixture
def results_dir(tmp_path):
    folder = tmp_path / RUN
    folder.mkdir()
    rows = [
        row(1, "XAUUSD", "long", "london 2026-09-02", "2026-09-02T08:05:00+00:00",
            "2026-09-02T09:00:00+00:00", 1.2, 1.1),
        row(2, "GBPUSD", "short", "new_york 2026-09-02", "2026-09-02T13:05:00+00:00",
            "2026-09-02T14:00:00+00:00", -1.0, -1.1, confluence="order_block"),
        row(3, "XAUUSD", "short", "new_york 2026-09-03", "2026-09-03T13:05:00+00:00",
            "2026-09-04T01:00:00+00:00", -1.0, -1.05, tags="last_90m"),
    ]  # fmt: skip
    with open(folder / "trades.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, TRADE_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    summary = {
        "run_id": RUN, "symbols": ["XAUUSD", "GBPUSD"], "start": "2026-09-02",
        "end": "2026-09-30", "notes": ["XAUUSD: 2026-09-01 not cached"],
    }  # fmt: skip
    (folder / "summary.json").write_text(json.dumps(summary))
    (folder / "settings.json").write_text(json.dumps({"preset": "Tight SL"}))
    older = tmp_path / "20261001-090000_XAUUSD"
    older.mkdir()
    (older / "summary.json").write_text(json.dumps({"symbols": ["XAUUSD"]}))
    (tmp_path / "presets").mkdir()  # not a run: no summary.json
    return tmp_path


def test_header_shows_run_symbols_days_preset_and_run_date(results_dir):
    page = str(results.layout(RUN, results_dir))
    for text in (RUN, "XAUUSD, GBPUSD", "2026-09-02 → 2026-09-30", "Tight SL",
                 "2026-10-08 12:00 UTC", "2026-09-01 not cached"):  # fmt: skip
        assert text in page
    # a run before presets existed
    (results_dir / RUN / "settings.json").write_text("{}")
    assert "run before presets" in str(results.layout(RUN, results_dir))


def test_run_selector_lists_runs_newest_first_and_skips_other_folders(results_dir):
    assert [o["value"] for o in results.list_runs(results_dir)] == [
        RUN,
        "20261001-090000_XAUUSD",
    ]


def test_run_ids_never_leave_the_results_folder(results_dir):
    for bad in ("..", "../etc", "a/b", "", "missing", "presets"):
        assert results.run_folder(bad, results_dir) is None
        assert "Run not found" in str(results.layout(bad, results_dir))


def test_overview_cards_and_equity_curve_follow_the_symbol_filter(results_dir):
    trades = read_trades(results_dir / RUN)
    content, equity = results.tab_content("overview", results.filtered(trades, results.ALL))
    text = str(content)
    assert "-1.05 R" in text and "3" in text  # net R of all three, trade count
    assert equity["net"] == pytest.approx([0.0, 1.1, 0.0, -1.05])
    assert equity["dd"] == pytest.approx([0.0, 0.0, -1.1, -2.15])
    gold = results.filtered(trades, "XAUUSD")
    assert [t.id for t in gold] == [1, 3]
    _, equity = results.tab_content("overview", gold)
    assert equity["net"] == pytest.approx([0.0, 1.1, 0.05])
    assert results.tab_content("trades", gold)[1] is None  # no curve on other tabs


def test_performance_tab_has_every_split_with_readable_names(results_dir):
    text = str(results.tab_content("performance", read_trades(results_dir / RUN))[0])
    for title in ("Symbol", "Session", "Long / short", "Confluence", "TP outcome", "Tag"):
        assert title in text
    for group in ("New York", "London", "Order block", "FVG", "last 1.5h", "no TP"):
        assert group in text
    assert "rs-histogram" in text


def test_trade_list_rows_and_the_link_to_the_chart(results_dir):
    trades = read_trades(results_dir / RUN)
    rows = results.trade_table_rows(trades)
    assert rows[1] == {
        "id": 2, "time": "2026-09-02 13:05", "symbol": "GBPUSD", "direction": "Short",
        "entry": 100.0, "sl": 99.0, "tp1": 101.2, "tp2": None, "r_gross": -1.0,
        "r_net": -1.1, "exit": "SL", "confluence": "Order block",
        "session": "New York 2026-09-02",
    }  # fmt: skip
    link = results.chart_link(trades[2])  # entered 09-03, closed 09-04
    focus = focus_from_query(link.removeprefix("/"))
    assert focus == {
        "symbol": "XAUUSD",
        "from": "2026-09-03",
        "to": "2026-09-04",
        "t0": "2026-09-03T13:00:00+00:00",
        "t1": "2026-09-04T01:00:00+00:00",
    }


def test_chart_focus_selects_symbol_days_and_the_trades_overlay():
    focus = {"symbol": "GBPUSD", "from": "2026-09-03", "to": "2026-09-04", "t0": "", "t1": ""}
    assert focus_selection(focus, ["fvg"]) == (
        "GBPUSD",
        ["on"],
        ["fvg", "trades", "trades.confluences"],
    )
    assert focus_selection({**focus, "done": True}, []) is None  # applied once
    assert focus_selection(None, []) is None
    days = [date(2026, 9, d) for d in range(1, 11)]
    assert initial_dates(days, "GBPUSD", focus) == ("2026-09-03", "2026-09-04")
    assert initial_dates(days, "XAUUSD", focus) == ("2026-09-01", "2026-09-10")
    assert initial_dates(days, "GBPUSD", {**focus, "done": True}) == ("2026-09-01", "2026-09-10")
    assert initial_dates([], "GBPUSD", focus) is None


def test_bad_focus_queries_are_ignored():
    upside_down = "?symbol=X&from=2026-09-04&to=2026-09-03&t0=2026-09-04T00:00&t1=2026-09-04"
    for search in (None, "", "?symbol=X", upside_down, "?symbol=X&from=bad&to=x&t0=1&t1=2"):
        assert focus_from_query(search) is None


def test_pages_by_address_pass_the_focus_to_the_chart():
    sources = SymbolSources({})
    search = "?symbol=XAUUSD&from=2026-09-02&to=2026-09-02&t0=2026-09-02T08:00&t1=2026-09-02T09:00"
    page = app_module.page_for("/", sources, search)
    store = next(c for c in page.children if getattr(c, "id", None) == "chart-focus")
    assert store.data["symbol"] == "XAUUSD"


def test_performance_tab_has_results_per_year_and_quarter_per_symbol(results_dir):
    trades = read_trades(results_dir / RUN)
    text = str(results.tab_content("performance", trades)[0])
    assert "Per year" in text and "Per quarter" in text and "2026 Q3" in text
    assert "All symbols" in text and "GBPUSD" in text
    gold = str(results.tab_content("performance", results.filtered(trades, "XAUUSD"))[0])
    assert "GBPUSD" not in gold  # one symbol: only the "all" columns (the same numbers)


def make_run(folder, name):
    (folder / name).mkdir()
    (folder / name / "summary.json").write_text(json.dumps({"symbols": ["X"]}))


def test_newest_timestamped_run_beats_a_study_folder_name(tmp_path):
    for name in ("gap_fade_walk_forward", "20261001-090000_A", "20261008-120000_B", "zz_study"):
        make_run(tmp_path, name)
    values = [o["value"] for o in results.list_runs(tmp_path)]
    assert values[:2] == ["20261008-120000_B", "20261001-090000_A"]
    assert values[2:] == ["zz_study", "gap_fade_walk_forward"]  # others after, as before


def test_only_named_folders_keep_the_old_order_and_empty_is_empty(tmp_path):
    assert results.list_runs(tmp_path) == []
    for name in ("a_study", "b_study"):
        make_run(tmp_path, name)
    assert [o["value"] for o in results.list_runs(tmp_path)] == ["b_study", "a_study"]
