"""Top toolbar: timeframe buttons, quick ranges, backtest from the toolbar, results page.
Spec: ROADMAP.md › 4.0 (Phase 4 › UI layout)."""

from __future__ import annotations

from datetime import date, timedelta

from backtester.data.sources import SymbolSources
from backtester.ui import app as app_module
from backtester.ui.pages import chart
from backtester.ui.pages.chart import (
    quick_range,
    timeframe_label,
)

SEP = [date(2026, 9, 1) + timedelta(days=i) for i in range(30)]  # 09-01 .. 09-30


def test_timeframe_buttons_read_like_tradingview():
    assert [timeframe_label(t) for t in ("M1", "M5", "M15", "M30", "H1", "H4")] == [
        "1m",
        "5m",
        "15m",
        "30m",
        "1h",
        "4h",
    ]
    assert [o["value"] for o in chart.layout(SymbolSources({})).children[0].children[2].options]


def test_quick_ranges_end_on_the_last_cached_day():
    assert quick_range(SEP, "1M") == (date(2026, 9, 1), date(2026, 9, 30))  # 08-31 + 1 day
    days = [date(2026, 1, 1) + timedelta(days=i) for i in range(365)]  # the whole of 2026
    assert quick_range(days, "3M") == (date(2026, 10, 1), date(2026, 12, 31))
    assert quick_range(days, "6M") == (date(2026, 7, 1), date(2026, 12, 31))
    assert quick_range(days, "YTD") == (date(2026, 1, 1), date(2026, 12, 31))
    assert quick_range(days, "1Y") == (date(2026, 1, 1), date(2026, 12, 31))
    assert quick_range(days, "All") == (date(2026, 1, 1), date(2026, 12, 31))
    assert quick_range([], "1M") is None


def test_quick_ranges_stop_at_a_missing_day():
    # 09-10 was never downloaded: a range over it can't be shown, so it starts after it
    days = [d for d in SEP if d != date(2026, 9, 10)]
    assert quick_range(days, "1M") == (date(2026, 9, 11), date(2026, 9, 30))
    assert quick_range(days, "All") == (date(2026, 9, 11), date(2026, 9, 30))


def test_month_back_keeps_the_day_or_the_months_last_one():
    days = [date(2026, 1, 1) + timedelta(days=i) for i in range(90)]  # up to 03-31
    assert quick_range(days, "1M") == (date(2026, 3, 1), date(2026, 3, 31))  # 02-28 + 1 day


def test_pages_by_address():
    sources = SymbolSources({})
    assert "Run not found" in str(app_module.page_for("/results/nope", sources))
    assert "chart-lwc" in str(app_module.page_for("/", sources))
    assert "chart-lwc" in str(app_module.page_for(None, sources))


def test_screenshot_button_and_its_menu_are_top_right():
    """ROADMAP 4.0b part 3 (the picture itself is made in the browser, chart.js `shot`)."""
    top = chart.layout(SymbolSources({})).children[0]
    ids = [getattr(c, "className", "") for c in top.children]
    assert ids[-2:] == ["tb-spacer", "tb-anchor tb-shot"]
    text = str(top.children[-1])
    assert "shot-save" in text and "shot-copy" in text and "pop-shot" in text


def test_zoom_buttons_and_the_go_to_field():
    """ROADMAP 4.0b parts 4 and 5 (zoom and go-to run in the browser, chart.js)."""
    page = str(chart.layout(SymbolSources({})))
    for id_ in ("tb-zoom", "tb-zoom-reset", "chart-goto-input", "chart-goto"):
        assert f"'{id_}'" in page


def test_bottom_bar_has_no_range_buttons_or_date_picker():
    """User, 2026-10-19: the loaded days come from the last-month default, scrolling and
    "Go to"; the quick ranges, the calendar icon and the date picker are gone."""
    page = str(chart.layout(SymbolSources({})))
    for k in ("1M", "3M", "6M", "YTD", "1Y", "All"):
        assert f"'range-{k}'" not in page
    assert "DatePickerRange(id='chart-dates'" not in page and "icon-calendar" not in page
    assert "chart-goto-input" in page and "chart-message" in page and "'UTC'" in page
    assert "DatePickerRange(id='bt-dates'" in page  # the backtest popover keeps its own days


def test_loading_bar_is_at_the_top_of_the_chart_pane():
    page = chart.layout(SymbolSources({}))
    pane = page.children[1].children[0].children[1]  # key strip, then tb-chart
    assert "chart-bar" in str(pane.children) and "chart-lwc" in str(pane.children)


def test_binance_symbols_are_hidden_from_the_symbol_lists(monkeypatch):
    # user, 2026-10-20: BTCUSDT / ETHUSDT (Binance) stay for research only, BTCUSD / ETHUSD (FTMO)
    # are the ones on the chart and in backtests
    shown = ["BTCUSD", "BTCUSDT", "ETHUSDT", "XAUUSD"]
    monkeypatch.setattr(SymbolSources, "available_symbols", lambda self: shown)
    page = chart.layout(SymbolSources({}))
    lists = []

    def walk(node):
        if getattr(node, "id", None) in ("chart-symbol", "bt-symbols"):
            lists.append([o if isinstance(o, str) else o["value"] for o in node.options])
        for child in getattr(node, "children", None) or []:
            if hasattr(child, "to_plotly_json"):
                walk(child)
        kids = getattr(node, "children", None)
        if hasattr(kids, "to_plotly_json"):
            walk(kids)

    walk(page)
    assert len(lists) == 2
    assert all(ids == ["BTCUSD", "XAUUSD"] for ids in lists)
