"""Chart page side panel (ROADMAP 7.4): newest-run summary, trades in view, layout ids,
overlay switches moved out of the toolbar, collapse toggle, click on a trade goes to it."""

from __future__ import annotations

import csv
import json
from datetime import UTC, date, datetime, timedelta

import pytest

from backtester.analytics.records import TradeRecord
from backtester.data.sources import SymbolSources
from backtester.runner import TRADE_COLUMNS
from backtester.ui import app as app_module
from backtester.ui import chart_side
from backtester.ui.pages import chart


def make_trade(id_, symbol, entry, direction="long", r_net=1.0, reason="take_profit", conf="fvg"):
    row = dict.fromkeys(TRADE_COLUMNS, "")
    row.update(
        id=id_, symbol=symbol, direction=direction, entry_time=entry.isoformat(),
        entry_candle=entry.isoformat(), entry=100.0, initial_stop=99.0,
        exit_time=(entry + timedelta(hours=1)).isoformat(), exit_price=101.0,
        exit_reason=reason, r_gross=r_net, r_net=r_net, confluence=conf, parts="[]",
    )  # fmt: skip
    return TradeRecord.from_row(row)


def write_run(root, name, rows):
    folder = root / name
    folder.mkdir()
    (folder / "summary.json").write_text(json.dumps({"symbols": ["XAUUSD"]}))
    with open(folder / "trades.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, TRADE_COLUMNS)
        w.writeheader()
        for r in rows:
            out = dict.fromkeys(TRADE_COLUMNS, "")
            out.update(r)
            w.writerow(out)
    return folder


def csv_row(id_, entry, r_net, symbol="XAUUSD"):
    return {
        "id": id_, "symbol": symbol, "direction": "long", "entry_time": entry,
        "entry_candle": entry, "entry": 100.0, "initial_stop": 99.0, "exit_time": entry,
        "exit_price": 100.0, "exit_reason": "take_profit" if r_net > 0 else "stop_loss",
        "r_gross": r_net, "r_net": r_net, "confluence": "fvg", "parts": "[]",
    }  # fmt: skip


T0 = datetime(2026, 9, 2, 8, 0, tzinfo=UTC)

# --- newest run summary ----------------------------------------------------------------


def test_no_run_gives_no_summary_and_the_card_says_so(tmp_path):
    assert chart_side.run_summary(tmp_path) is None
    assert chart_side.run_summary(tmp_path / "missing") is None
    assert "No backtest yet" in str(chart_side.result_body(None))


def test_one_run_is_summarised_from_its_trades(tmp_path):
    write_run(
        tmp_path, "20261001-090000_XAUUSD",
        [csv_row(1, "2026-09-02T08:00:00+00:00", 2.0),
         csv_row(2, "2026-09-02T09:00:00+00:00", -1.0),
         csv_row(3, "2026-09-02T10:00:00+00:00", -1.0)],
    )  # fmt: skip
    s = chart_side.run_summary(tmp_path)
    assert s["run_id"] == "20261001-090000_XAUUSD"
    assert s["href"] == "/results/20261001-090000_XAUUSD"
    assert s["trades"] == 3 and s["net_r"] == pytest.approx(0.0)
    assert s["win_rate"] == pytest.approx(1 / 3)
    assert s["max_drawdown_r"] == pytest.approx(2.0)
    text = str(chart_side.result_body(s))
    assert "20261001-090000_XAUUSD" in text and "/results/20261001-090000_XAUUSD" in text
    assert "0.0 R" in text and "-0.0" not in text and "-2.0 R" in text  # net 0, drawdown 2


def test_several_runs_use_the_newest(tmp_path):
    write_run(tmp_path, "20261001-090000_A", [csv_row(1, "2026-09-02T08:00:00+00:00", -1.0)])
    write_run(tmp_path, "20261008-120000_B", [csv_row(1, "2026-09-02T08:00:00+00:00", 3.0)])
    write_run(tmp_path, "20260901-090000_C", [csv_row(1, "2026-09-02T08:00:00+00:00", -1.0)])
    (tmp_path / "presets").mkdir()  # not a run
    s = chart_side.run_summary(tmp_path)
    assert s["run_id"] == "20261008-120000_B" and s["net_r"] == pytest.approx(3.0)
    assert chart_side.newest_run(tmp_path).name == "20261008-120000_B"


def test_a_run_without_trades_has_zero_trades(tmp_path):
    write_run(tmp_path, "20261001-090000_A", [])
    s = chart_side.run_summary(tmp_path)
    assert s["trades"] == 0 and s["net_r"] == 0 and s["win_rate"] is None
    assert "—" in str(chart_side.result_body(s))  # no win rate


# --- trades in view --------------------------------------------------------------------


def test_trades_in_view_start_is_inclusive_end_is_exclusive():
    trades = [
        make_trade(1, "XAUUSD", T0 - timedelta(minutes=5)),  # before
        make_trade(2, "XAUUSD", T0),  # on the start: in
        make_trade(3, "XAUUSD", T0 + timedelta(minutes=30)),
        make_trade(4, "XAUUSD", T0 + timedelta(hours=1)),  # on the end: out
    ]
    found = chart_side.trades_in_view(trades, "XAUUSD", T0, T0 + timedelta(hours=1))
    assert [t.id for t in found] == [2, 3]


def test_trades_in_view_filters_symbol_sorts_and_handles_empty():
    trades = [
        make_trade(1, "XAUUSD", T0 + timedelta(minutes=20)),
        make_trade(2, "GBPUSD", T0 + timedelta(minutes=10)),
        make_trade(3, "XAUUSD", T0 + timedelta(minutes=5)),
    ]
    found = chart_side.trades_in_view(trades, "XAUUSD", T0, T0 + timedelta(hours=1))
    assert [t.id for t in found] == [3, 1]
    assert chart_side.trades_in_view([], "XAUUSD", T0, T0 + timedelta(hours=1)) == []
    assert chart_side.trades_in_view(trades, "NAS100", T0, T0 + timedelta(hours=1)) == []
    assert chart_side.trades_in_view(trades, "XAUUSD", T0, T0) == []  # empty range


def test_view_times_reads_the_browsers_range():
    start, end = chart_side.view_times({"from": 1_788_000_000, "to": 1_788_003_600})
    assert end - start == timedelta(hours=1) and start.tzinfo is UTC
    assert chart_side.view_times(None) is None
    assert chart_side.view_times({"from": None, "to": 1}) is None


def test_open_trades_show_open_and_closed_ones_their_r():
    closed = chart_side.trade_item(make_trade(1, "XAUUSD", T0, "short", -1.0, "stop_loss", "bpr"))
    text = str(closed)
    assert "SHORT" in text and "Sep 02 · BPR" in text and "-1.00R" in text
    op = str(chart_side.trade_item(make_trade(2, "XAUUSD", T0, "long", 0.4, "end_of_data")))
    assert "LONG" in op and "open" in op and "0.40R" not in op
    assert chart_side.is_open(make_trade(3, "XAUUSD", T0, reason="end_of_data"))


def test_trades_body_empty_no_run_and_cap():
    assert "No trades in view" in str(chart_side.trades_body([]))
    assert "No backtest yet" in str(chart_side.trades_body([], has_run=False))
    many = [make_trade(i, "XAUUSD", T0 + timedelta(minutes=i)) for i in range(50)]
    body = chart_side.trades_body(many)
    assert len(body) == chart_side.MAX_LISTED + 1 and "+10 more" in str(body[-1])


# --- layout ----------------------------------------------------------------------------


def ids_in(component) -> list[str]:
    found: list[str] = []

    def walk(c):
        if c is None or isinstance(c, (str, int, float)):
            return
        if isinstance(c, (list, tuple)):
            for x in c:
                walk(x)
            return
        cid = getattr(c, "id", None)
        if isinstance(cid, str):
            found.append(cid)
        walk(getattr(c, "children", None))

    walk(component)
    return found


def popover_ids(page, popover_id: str) -> list[str]:
    def find(c):
        if c is None or isinstance(c, (str, int, float)):
            return None
        if isinstance(c, (list, tuple)):
            return next((f for x in c if (f := find(x)) is not None), None)
        if getattr(c, "id", None) == popover_id:
            return c
        return find(getattr(c, "children", None))

    return ids_in(find(page))


def test_layout_has_the_side_panel_without_overlays_and_overlays_in_the_settings(tmp_path):
    """User, 2026-10-19: the Overlays card moved into the Settings popover (same ids)."""
    page = chart.layout(SymbolSources({}), results_dir=tmp_path)
    toolbar, main = page.children[0], page.children[1]
    side = main.children[-1]
    side_ids = set(ids_in(side))
    assert "side-trades" in side_ids and "ch-card-overlays" not in side_ids
    assert {"ch-card-result", "ch-card-trades"} <= side_ids
    assert not side_ids & {"chart-overlays", "chart-overlay-types", "chart-overlay-summary"}
    assert "chart-lwc" in ids_in(main) and "chart-lwc" not in side_ids
    settings = set(popover_ids(page, "pop-settings"))
    assert {"chart-overlays", "chart-overlay-types", "chart-overlay-summary"} <= settings
    assert {"chart-sessions", "chart-day-boundary", "chart-filters"} <= settings
    tb_ids = set(ids_in(toolbar))
    assert "chart-sessions" in tb_ids and "side-toggle" in tb_ids
    all_ids = ids_in(page)
    assert len(all_ids) == len(set(all_ids))  # every id once
    assert "chart-range" in all_ids and "side-collapsed" in all_ids


def test_settings_popover_has_a_chart_settings_and_a_chart_overlays_section():
    text = str(chart.layout(SymbolSources({})))
    assert "Chart Settings" in text and "Chart Overlays" in text
    assert text.index("Chart Settings") < text.index("Chart Overlays")
    assert "Show overlays" in text


def test_side_panel_shows_the_newest_run(tmp_path):
    assert "No backtest yet" in str(chart.layout(SymbolSources({}), results_dir=tmp_path))
    write_run(tmp_path, "20261008-120000_B", [csv_row(1, "2026-09-02T08:00:00+00:00", 3.0)])
    text = str(chart.layout(SymbolSources({}), results_dir=tmp_path))
    assert "20261008-120000_B" in text and "+3.0 R" in text


def test_overlay_switch_options_cover_every_overlay_type():
    from backtester.ui.overlays import OVERLAYS

    values = {o["value"] for o in chart.overlay_controls()[1].options}
    assert set(OVERLAYS) <= values


# --- collapse toggle -------------------------------------------------------------------


def test_collapse_toggle_flips_only_on_a_click():
    assert chart_side.collapsed_after(None, False) is False  # page build, no click
    assert chart_side.collapsed_after(0, True) is True
    assert chart_side.collapsed_after(1, False) is True
    assert chart_side.collapsed_after(2, True) is False
    assert chart_side.main_class(True) == "ch-main ch-collapsed"
    assert chart_side.main_class(False) == "ch-main" == chart_side.main_class(None)


# --- click on a trade goes to it -------------------------------------------------------


def test_clicking_a_trade_goes_to_its_entry_and_loads_its_days():
    cached = [date(2026, 9, 1) + timedelta(days=i) for i in range(30)]
    at = datetime(2026, 9, 20, 13, 0, tzinfo=UTC)
    goto, start, end, message = chart.goto_outputs(
        at, "XAUUSD", "M5", "2026-09-01", "2026-09-05", None, 7, cached
    )
    assert goto == {"t": int(at.timestamp()), "symbol": "XAUUSD", "n": 7}
    assert message is chart.no_update and start is not chart.no_update
    assert date.fromisoformat(start) <= at.date() <= date.fromisoformat(end)
    # inside the shown days: only the goto command
    goto, start, end, _ = chart.goto_outputs(
        datetime(2026, 9, 3, 9, 0, tzinfo=UTC), "XAUUSD", "M5", "2026-09-01", "2026-09-05",
        None, 8, cached,
    )  # fmt: skip
    assert goto["n"] == 8 and start is chart.no_update and end is chart.no_update
    # a day that isn't cached: a message, no command
    _, _, _, message = chart.goto_outputs(
        datetime(2026, 12, 1, tzinfo=UTC), "XAUUSD", "M5", "2026-09-01", "2026-09-05", None, 9, cached
    )  # fmt: skip
    assert "not in the cache" in message


def test_the_app_builds_with_the_side_panel_callbacks():
    app = app_module.create_app(SymbolSources({}))
    outputs = " ".join(app.callback_map)
    assert "side-trades.children" in outputs and "ch-main.className" in outputs
    assert "side-collapsed.data" in outputs
