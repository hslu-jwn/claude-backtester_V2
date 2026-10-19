"""Trade focus: one order (entry, SL, TP) opened on the chart from a backtest trade, the chart's
side panel or a live trade. Pure parts of `ui/trade_focus.py` (ROADMAP 7.6): link round trip,
timeframe of a run, the order drawing, the days to load. The browser side is in chart.js."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from urllib.parse import urlparse

import pytest

from backtester.analytics.records import TradeRecord
from backtester.core.models import Timeframe
from backtester.ui import trade_focus as tfo
from backtester.ui.chart_config import DEFAULT_CONFIG
from backtester.ui.drawing import Box, Label, Line, Marker


def at(h, m=0, day=2):
    return datetime(2026, 10, day, h, m, tzinfo=UTC)


def trade(**kw) -> TradeRecord:
    base = dict(  # noqa: C408
        id=1, symbol="NAS100", direction="long", session="", entry_time=at(14, 36),
        entry_candle=at(14, 35), entry=100.0, initial_stop=99.0, take_profit=102.0,
        take_profit_2=None, tp1_share=1.0, planned_r=2.0, exit_time=at(15, 11),
        exit_price=102.0, exit_reason="take_profit", r_gross=2.0, r_net=1.9, spread_r=0.0,
        commission_r=0.0, tags=frozenset(), confluence="", reason="", parts=(),
    )  # fmt: skip
    return TradeRecord(**{**base, **kw})


# --- order and link ---------------------------------------------------------------------------


def test_trade_order_carries_entry_sl_tp_and_exit():
    o = tfo.trade_order(trade())
    assert o == {
        "symbol": "NAS100", "direction": "long", "entry_time": "2026-10-02T14:36:00Z",
        "entry": 100.0, "sl": 99.0, "tp": 102.0, "exit_time": "2026-10-02T15:11:00Z",
        "exit": 102.0,
    }  # fmt: skip


def test_an_open_backtest_trade_has_no_exit():
    o = tfo.trade_order(trade(exit_reason="end_of_data"))
    assert o["exit_time"] is None and o["exit"] is None


def test_no_take_profit_stays_none():
    assert tfo.trade_order(trade(take_profit=None))["tp"] is None


def test_the_furthest_take_profit_is_the_target_with_two_tps():
    o = tfo.trade_order(trade(take_profit=101.0, take_profit_2=103.0))
    assert o["tp"] == 103.0


@pytest.mark.parametrize("direction", ["long", "short"])
def test_link_round_trip(direction):
    short = direction == "short"
    o = tfo.trade_order(
        trade(direction=direction, initial_stop=101.0 if short else 99.0,
              take_profit=98.0 if short else 102.0)
    )  # fmt: skip
    link = tfo.order_link(o, "M5")
    assert link.startswith("/?") and "+" not in urlparse(link).query.replace("%2B", "")
    focus = tfo.focus_from_query(link.removeprefix("/"))
    assert focus["order"] == o
    assert focus["symbol"] == "NAS100" and focus["tf"] == "M5"
    assert focus == tfo.focus_from_order(o, "M5")


def test_link_round_trip_open_trade_without_tp():
    o = tfo.make_order("US500", "short", at(15, 0), 7700.5, 7710.25)
    focus = tfo.focus_from_query(tfo.order_link(o, "M1").removeprefix("/"))
    assert focus["order"] == o
    assert o["tp"] is None and o["exit_time"] is None
    assert focus["t1"] == focus["t0"]  # an open order: nothing after the entry is known


def test_focus_days_are_the_trade_days_plus_a_margin_of_candles():
    o = tfo.trade_order(trade(exit_time=at(2, 0, day=3)))  # closes the next day
    m1 = tfo.focus_from_order(o, "M1")
    h1 = tfo.focus_from_order(o, "H1")
    assert (m1["from"], m1["to"]) == ("2026-10-01", "2026-10-04")
    assert h1["from"] < m1["from"] and h1["to"] > m1["to"]  # a coarser chart needs more days
    assert m1["t0"] == "2026-10-02T14:36:00Z" and m1["t1"] == "2026-10-03T02:00:00Z"


def test_old_links_without_the_order_still_parse():
    search = (
        "?symbol=XAUUSD&from=2026-09-03&to=2026-09-04"
        "&t0=2026-09-03T13:00:00%2B00:00&t1=2026-09-04T01:00:00%2B00:00"
    )
    assert tfo.focus_from_query(search) == {
        "symbol": "XAUUSD", "from": "2026-09-03", "to": "2026-09-04",
        "t0": "2026-09-03T13:00:00+00:00", "t1": "2026-09-04T01:00:00+00:00",
    }  # fmt: skip


@pytest.mark.parametrize(
    "search",
    [
        None,
        "",
        "?symbol=X",
        "?symbol=X&dir=long",  # no entry
        "?symbol=X&dir=sideways&entry=2026-10-02T14:36:00Z&ep=1&sl=0.5",
        "?symbol=X&dir=long&entry=bad&ep=1&sl=0.5",
        "?symbol=X&dir=long&entry=2026-10-02T14:36:00Z&ep=one&sl=0.5",
        "?symbol=X&dir=long&entry=2026-10-02T14:36:00Z&ep=1&sl=nan",
        "?symbol=X&dir=long&entry=2026-10-02T14:36:00Z&ep=1&sl=0.5&exit=garbage",
        "?symbol=X&dir=long&entry=2026-10-02T14:36:00Z&ep=1&sl=0.5&exit=2026-10-01T00:00:00Z",
    ],
)
def test_bad_order_links_are_ignored(search):
    assert tfo.focus_from_query(search) is None


def test_a_stop_at_the_entry_is_not_an_order():
    bad = "?symbol=X&dir=long&entry=2026-10-02T14:36:00Z&ep=1&sl=1"
    assert tfo.focus_from_query(bad) is None  # R would be a division by zero


def test_an_unknown_timeframe_is_dropped_not_fatal():
    link = tfo.order_link(tfo.trade_order(trade()), "M5").replace("tf=M5", "tf=X9")
    focus = tfo.focus_from_query(link.removeprefix("/"))
    assert focus["tf"] is None  # the chart keeps its timeframe


def test_chip_text():
    long = tfo.trade_order(trade())
    assert tfo.chip_text(long) == "Trade: NAS100 long 2026-10-02 14:36"
    assert tfo.chip_text(tfo.trade_order(trade(direction="short", initial_stop=101.0))).endswith(
        "14:36"
    )


# --- timeframe ------------------------------------------------------------------------------------


def write_run(tmp_path, strategy_name, **strategy):
    folder = tmp_path / "20261008-120000_NAS100"
    folder.mkdir()
    settings = {"preset": "x", "strategy": {"name": strategy_name, **strategy}}
    (folder / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    return folder


def test_run_timeframe_is_the_strategys_base_timeframe(tmp_path):
    assert tfo.run_timeframe(write_run(tmp_path, "opening_range"), "NAS100") == "M1"


def test_run_timeframe_of_strategy_1_is_5m(tmp_path):
    assert tfo.run_timeframe(write_run(tmp_path, "session_zone_sweep"), "XAUUSD") == "M5"


def test_run_timeframe_follows_a_configurable_strategy(tmp_path):
    folder = write_run(tmp_path, "trend_following", timeframe="H4")
    assert tfo.run_timeframe(folder, "XAUUSD") == "H4"


def test_run_timeframe_falls_back_without_settings(tmp_path):
    folder = tmp_path / "20261008-120000_NAS100"
    folder.mkdir()
    assert tfo.run_timeframe(folder, "NAS100") == tfo.DEFAULT_TIMEFRAME
    (folder / "settings.json").write_text("{not json", encoding="utf-8")
    assert tfo.run_timeframe(folder, "NAS100") == tfo.DEFAULT_TIMEFRAME
    (folder / "settings.json").write_text('{"strategy": {"name": "nope"}}', encoding="utf-8")
    assert tfo.run_timeframe(folder, "NAS100") == tfo.DEFAULT_TIMEFRAME


def test_live_trades_use_the_bots_timeframe():
    assert tfo.LIVE_TIMEFRAME == "M1"  # the opening-range bot trades on 1m candles


# --- live trades ----------------------------------------------------------------------------------


def test_live_closed_trade_row_becomes_an_order_without_tp():
    row = {
        "symbol": "US500", "side": "sell", "entry_time": "2026-10-19T13:47:00+00:00",
        "entry_fill": 7700.5, "sl": 7710.0, "exit_time": "2026-10-19T15:02:10+00:00",
        "exit_price": 7695.0,
    }  # fmt: skip
    o = tfo.live_order(row)
    assert o == {
        "symbol": "US500", "direction": "short", "entry_time": "2026-10-19T13:47:00Z",
        "entry": 7700.5, "sl": 7710.0, "tp": None, "exit_time": "2026-10-19T15:02:10Z",
        "exit": 7695.0,
    }  # fmt: skip


def test_live_open_position_becomes_an_open_order():
    pos = {"symbol": "NAS100", "side": "buy", "entry": 29500.0, "sl": 29400.0,
           "since": "2026-10-19T14:35:00+00:00"}  # fmt: skip
    o = tfo.live_order(pos)
    assert o["direction"] == "long" and o["exit_time"] is None and o["tp"] is None
    assert o["entry_time"] == "2026-10-19T14:35:00Z"


@pytest.mark.parametrize(
    "row",
    [
        {}, {"symbol": "US500", "side": "buy"},
        {"symbol": "US500", "side": "buy", "entry_fill": "x", "sl": 1, "entry_time": "z"},
        {"symbol": "US500", "side": "hold", "entry_fill": 1, "sl": 1,
         "entry_time": "2026-10-19T13:47:00+00:00"},
    ],
)  # fmt: skip
def test_live_rows_that_are_not_orders_give_none(row):
    assert tfo.live_order(row) is None


def test_live_link_goes_to_the_chart_on_the_bots_timeframe():
    row = {"symbol": "US500", "side": "buy", "entry_fill": 7700.0, "sl": 7690.0,
           "entry_time": "2026-10-19T13:47:00+00:00"}  # fmt: skip
    link = tfo.live_link(row)
    focus = tfo.focus_from_query(link.removeprefix("/"))
    assert focus["tf"] == "M1" and focus["order"]["tp"] is None
    assert tfo.live_link({"symbol": "US500"}) is None


# --- days to load ---------------------------------------------------------------------------------


def days(first, last):
    return [first + timedelta(days=i) for i in range((last - first).days + 1)]


def focus_of(**kw):
    o = tfo.trade_order(trade(**kw))
    return tfo.focus_from_order(o, "M5")


def test_focus_dates_inside_the_cache():
    cached = days(date(2026, 9, 1), date(2026, 10, 10))
    assert tfo.focus_dates(cached, focus_of(), DEFAULT_CONFIG) == ("2026-09-30", "2026-10-04")


def test_focus_dates_are_cut_to_the_run_of_cached_days():
    cached = days(date(2026, 10, 2), date(2026, 10, 3))
    assert tfo.focus_dates(cached, focus_of(), DEFAULT_CONFIG) == ("2026-10-02", "2026-10-03")
    hole = [*days(date(2026, 9, 1), date(2026, 9, 20)), *days(date(2026, 10, 1), date(2026, 10, 3))]
    assert tfo.focus_dates(hole, focus_of(), DEFAULT_CONFIG) == ("2026-10-01", "2026-10-03")


def test_a_trade_after_the_last_cached_day_has_no_days():
    cached = days(date(2026, 9, 1), date(2026, 10, 1))
    assert tfo.focus_dates(cached, focus_of(), DEFAULT_CONFIG) is None
    assert tfo.focus_dates([], focus_of(), DEFAULT_CONFIG) is None


def test_focus_dates_respect_the_candle_limit():
    cached = days(date(2025, 1, 1), date(2026, 12, 31))
    long_trade = focus_of(exit_time=at(15, 0, day=2) + timedelta(days=66))  # a 5m trade of 67 days
    first, last = tfo.focus_dates(cached, long_trade, DEFAULT_CONFIG)
    n = (date.fromisoformat(last) - date.fromisoformat(first)).days + 1
    assert n * 1440 // Timeframe.M5.value <= DEFAULT_CONFIG.max_candles  # the margin was cut
    assert first <= "2026-10-02" and last >= "2026-12-07"  # the trade itself is always in


# --- the drawing ---------------------------------------------------------------------------------


def opens(n=100, start=None):
    start = start or at(14, 0)
    return [start + timedelta(minutes=i) for i in range(n)]


def parts(drawings):
    boxes = [d for d in drawings if isinstance(d, Box)]
    lines = [d for d in drawings if isinstance(d, Line)]
    labels = [d for d in drawings if isinstance(d, Label)]
    markers = [d for d in drawings if isinstance(d, Marker)]
    return boxes, lines, labels, markers


def draw(order, o=None, tf=Timeframe.M1):
    return tfo.order_drawings(order, opens() if o is None else o, tf, 2, DEFAULT_CONFIG)


def test_long_order_boxes_and_levels():
    order = tfo.trade_order(trade())  # entry 14:36 candle -> index 35, exit 15:11 -> 70
    boxes, lines, labels, markers = parts(draw(order))
    profit = next(b for b in boxes if b.fill == DEFAULT_CONFIG.trade_profit_color)
    loss = next(b for b in boxes if b.fill == DEFAULT_CONFIG.trade_loss_color)
    assert (profit.x0, profit.x1, profit.bottom, profit.top) == (35, 70, 100.0, 102.0)
    assert (loss.x0, loss.x1, loss.bottom, loss.top) == (35, 70, 99.0, 100.0)
    prices = {round(line.y0, 6) for line in lines}
    assert prices == {99.0, 100.0, 102.0}
    texts = " | ".join(label.text for label in labels)
    assert "Entry 100.00" in texts and "SL 99.00" in texts and "TP 102.00" in texts
    assert "-1.00R" in texts and "+2.00R" in texts
    assert len(markers) == 1 and (markers[0].x, markers[0].y) == (70, 102.0)  # the exit


def test_short_order_is_the_mirror_of_the_long():
    long = parts(draw(tfo.trade_order(trade())))
    short_order = tfo.trade_order(
        trade(direction="short", initial_stop=101.0, take_profit=98.0, exit_price=98.0)
    )
    boxes, _lines, labels, _markers = parts(draw(short_order))
    profit = next(b for b in boxes if b.fill == DEFAULT_CONFIG.trade_profit_color)
    loss = next(b for b in boxes if b.fill == DEFAULT_CONFIG.trade_loss_color)
    assert (profit.bottom, profit.top) == (98.0, 100.0)  # TP below the entry
    assert (loss.bottom, loss.top) == (100.0, 101.0)  # SL above it
    assert (profit.x0, profit.x1) == (long[0][0].x0, long[0][0].x1)
    texts = " | ".join(label.text for label in labels)
    assert "+2.00R" in texts and "-1.00R" in texts


def test_open_order_ends_at_the_last_candle_and_has_no_exit_marker():
    order = tfo.make_order("NAS100", "long", at(14, 36), 100.0, 99.0, 102.0)
    boxes, _lines, _labels, markers = parts(draw(order))
    assert all(b.x0 == 35 and b.x1 == 99 for b in boxes)  # 100 candles: last index 99
    assert markers == []


def test_order_without_tp_draws_only_the_risk_side():
    order = tfo.make_order("US500", "long", at(14, 36), 100.0, 99.0)
    boxes, _lines, labels, _ = parts(draw(order))
    assert [b.fill for b in boxes] == [DEFAULT_CONFIG.trade_loss_color]
    assert not any("TP" in label.text for label in labels)


def test_exit_after_the_loaded_candles_is_cut_to_the_last_candle_without_marker():
    order = tfo.trade_order(trade(exit_time=at(18, 0)))  # candles end at 15:39
    boxes, _, _, markers = parts(draw(order))
    assert all(b.x1 == 99 for b in boxes) and markers == []


def test_order_outside_the_loaded_candles_draws_nothing():
    early = tfo.trade_order(trade(entry_time=at(9, 0), exit_time=at(9, 30)))
    assert draw(early) == []
    late = tfo.trade_order(trade(entry_time=at(20, 0), exit_time=at(20, 30)))
    assert draw(late) == []
    assert draw(tfo.trade_order(trade()), []) == []


def test_coarse_timeframe_places_the_order_on_the_containing_candle():
    h1 = [at(h) for h in range(10, 20)]  # 10:00 .. 19:00 candles
    order = tfo.trade_order(trade())  # entry 14:36 close -> the 14:00 candle (index 4)
    boxes, *_ = parts(draw(order, h1, Timeframe.H1))
    assert all(b.x0 == 4 for b in boxes) and boxes[0].x1 == 5  # exit 15:11 -> 15:00 candle


def test_a_candle_closing_exactly_at_the_entry_time_is_the_entry_candle():
    # entry_time is the CLOSE of the entry candle (14:36 close = the 14:35 candle)
    boxes, *_ = parts(draw(tfo.trade_order(trade(entry_time=at(14, 35)))))
    assert boxes[0].x0 == 34  # the 14:34 candle closes at 14:35


def test_encoded_drawings_are_json_for_the_browser():
    payload = tfo.order_payload(tfo.trade_order(trade()), opens(), Timeframe.M1, 2, DEFAULT_CONFIG)
    assert payload and all("k" in d and "o" in d for d in payload)
    json.dumps(payload)  # serialisable


def test_latest_dates_are_the_newest_run_of_days():
    cached = [*days(date(2026, 1, 1), date(2026, 1, 20)), *days(date(2026, 8, 1), date(2026, 9, 1))]
    first, last = tfo.latest_dates(cached, "M5", DEFAULT_CONFIG)
    assert last == "2026-09-01" and first == "2026-08-01"  # never across the hole
    assert tfo.latest_dates([], "M5", DEFAULT_CONFIG) is None
    assert tfo.latest_dates(cached, "D1", DEFAULT_CONFIG)[0] == "2026-08-01"


def test_chip_text_with_a_note():
    text = tfo.chip_text(tfo.trade_order(trade()), "not in the cache")
    assert text == "Trade: NAS100 long 2026-10-02 14:36 (not in the cache)"


# --- the chart page's payload ---------------------------------------------------------------------


def test_order_draw_payload_is_keyed_to_the_chart_and_only_for_its_symbol(tmp_path):
    from m1_frames import m1

    from backtester.data.cache import cache_path
    from backtester.data.sources import SymbolSources
    from backtester.ui.pages.chart import chart_key, order_draw_payload

    path = cache_path(tmp_path, "NAS100", date(2026, 10, 2))
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        (f"{14 + i // 60}:{i % 60:02d}", 100.0, 100.5, 99.5, 100.2, 1.0, 0.1) for i in range(60)
    ]
    m1(*rows, day="2026-10-02").to_parquet(path, index=False)
    sources = SymbolSources({"NAS100": tmp_path})
    order = tfo.trade_order(trade(entry_time=at(14, 11), exit_time=at(14, 31)))
    payload = order_draw_payload(sources, order, "NAS100", "M1", "2026-10-02", "2026-10-02")
    assert payload["key"] == chart_key("NAS100", "M1", "2026-10-02", "2026-10-02")
    assert payload["items"] and all(d["o"] == "order" for d in payload["items"])
    box = next(d for d in payload["items"] if d["k"] == "b")
    assert (box["x0"], box["x1"]) == (10, 30)  # the 14:10 and 14:30 candles
    assert order_draw_payload(sources, order, "US500", "M1", "2026-10-02", "2026-10-02") is None
    assert order_draw_payload(sources, None, "NAS100", "M1", "2026-10-02", "2026-10-02") is None
    replay = {"on": True}
    args = (sources, order, "NAS100", "M1", "2026-10-02", "2026-10-02", replay)
    assert order_draw_payload(*args) is None  # the order would show the future in a replay
    assert order_draw_payload(sources, order, "NAS100", "M1", "2026-10-05", "2026-10-05") is None


# --- the run's trades without a focused trade (any strategy) ---------------------------------------


def nas_sources(tmp_path):
    from m1_frames import m1

    from backtester.data.cache import cache_path
    from backtester.data.sources import SymbolSources

    path = cache_path(tmp_path, "NAS100", date(2026, 10, 2))
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        (f"{14 + i // 60}:{i % 60:02d}", 100.0, 100.5, 99.5, 100.2, 1.0, 0.1) for i in range(60)
    ]
    m1(*rows, day="2026-10-02").to_parquet(path, index=False)
    return SymbolSources({"NAS100": tmp_path})


def test_run_trades_of_the_shown_symbol_are_drawn_light_without_a_focus(tmp_path):
    from backtester.ui.pages.chart import order_draw_payload

    sources = nas_sources(tmp_path)
    inside = trade(id=1, entry_time=at(14, 11), exit_time=at(14, 31))
    second = trade(id=2, entry_time=at(14, 41), exit_time=at(14, 51), direction="short",
                   initial_stop=101.0, take_profit=98.0)  # fmt: skip
    other = trade(id=3, symbol="US500", entry_time=at(14, 11), exit_time=at(14, 31))
    outside = trade(id=4, entry_time=at(20, 11), exit_time=at(20, 31))
    args = ("NAS100", "M1", "2026-10-02", "2026-10-02")
    payload = order_draw_payload(sources, None, *args, run_trades=[inside, second, other, outside])
    boxes = [d for d in payload["items"] if d["k"] == "b"]
    assert sorted((b["x0"], b["x1"]) for b in boxes) == [(10, 30), (10, 30), (40, 50), (40, 50)]
    assert not any(d["k"] in ("t", "m") for d in payload["items"])  # light: no labels, no marker
    # with a focused trade only that order is drawn (labelled)
    focused = order_draw_payload(
        sources, tfo.trade_order(inside), *args, run_trades=[inside, second]
    )
    assert {(b["x0"], b["x1"]) for b in focused["items"] if b["k"] == "b"} == {(10, 30)}
    assert any(d["k"] == "t" for d in focused["items"])
    assert order_draw_payload(sources, None, *args) is None  # no run
    assert order_draw_payload(sources, None, *args, run_trades=[other]) is None


def test_run_orders_work_for_an_opening_range_run(tmp_path):
    """A run of another strategy (opening-range breakout: no TP, 1m base) opens and draws too."""
    folder = write_run(tmp_path, "opening_range")
    t = trade(take_profit=None, exit_reason="signal")
    order = tfo.trade_order(t)
    assert order["tp"] is None
    assert tfo.run_timeframe(folder, "NAS100") == "M1"
    assert not any(isinstance(d, Box) and d.fill == DEFAULT_CONFIG.trade_profit_color
                   for d in draw(order))  # fmt: skip


def test_side_panel_focus_of_an_opening_range_run_opens_on_1m_without_the_trades_overlay(tmp_path):
    from backtester.ui.pages.chart import focus_selection, side_trade_focus

    folder = write_run(tmp_path, "opening_range")
    focus = side_trade_focus(trade(take_profit=None, exit_reason="signal"), folder, 1)
    assert focus["tf"] == "M1" and focus["order"]["tp"] is None
    assert focus_selection(focus, []) is None  # the strategy is not run
