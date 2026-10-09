"""Top toolbar: timeframe buttons, quick ranges, backtest from the toolbar, results page.
Spec: ROADMAP.md › 4.0 (Phase 4 › UI layout)."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from dash import no_update

from backtester.data.sources import SymbolSources
from backtester.ui import app as app_module
from backtester.ui.pages import chart
from backtester.ui.pages.chart import poll_backtest, quick_range, start_backtest, timeframe_label

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


class FakeRun:
    def __init__(self, folder=None, error=None):
        self.done, self.total, self.folder, self.error = 0, 0, folder, error
        self.finished = False


def test_backtest_runs_in_the_background_reports_progress_and_opens_its_results():
    started = []

    def fake_start(symbols, start, end, settings, sources, preset):
        started.append((symbols, start, end))
        return run

    run = FakeRun(folder=Path("results/20261008-120000_XAUUSD"))
    job, timer_off, status, bar, page = start_backtest(
        None, ["XAUUSD"], "2026-09-02", "2026-09-30", fake_start
    )
    assert started == [(["XAUUSD"], date(2026, 9, 2), date(2026, 9, 30))]
    assert timer_off is False and "Running XAUUSD" in status and page is no_update
    run.done, run.total = 250, 1000
    _, timer_off, status, bar, page = poll_backtest(job)
    assert timer_off is False and status == "250 of 1,000 candles" and bar == {"width": "25%"}
    run.finished = True
    job_after, timer_off, status, bar, page = poll_backtest(job)
    assert job_after is None and timer_off is True and bar == {"width": "100%"}
    assert page == "/results/20261008-120000_XAUUSD"
    assert poll_backtest(job)[1] is True  # forgotten afterwards


def test_backtest_errors_and_missing_input_are_shown():
    run = FakeRun(error=ValueError("XAUUSD: no cached day"))
    job = start_backtest(None, ["XAUUSD"], "2026-09-02", "2026-09-30", lambda *a, **k: run)[0]
    run.finished = True
    _, timer_off, status, _, page = poll_backtest(job)
    assert timer_off and status == "Failed: XAUUSD: no cached day" and page is no_update
    _, timer_off, status, _, _ = start_backtest(None, [], "2026-09-02", "2026-09-30")
    assert timer_off and status.startswith("Pick one or more symbols")


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
