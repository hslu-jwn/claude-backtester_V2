"""Chart page wiring of the MT5 fill (ROADMAP 7.5): the chart's own loading uses the chart
adapter and days; backtests and the strategy trades overlay keep the plain histdata sources."""

from __future__ import annotations

from datetime import date
from functools import partial

import pytest
from test_chart_feed import HIST_LEVEL, MT5_LEVEL, SYMBOL, feeds, put  # noqa: F401

from backtester.ui import chart_data as cd
from backtester.ui.chart_config import ChartConfig
from backtester.ui.pages import chart

D = date.fromisoformat


@pytest.fixture
def wired(feeds, monkeypatch):  # noqa: F811
    """The chart module's fill functions pointed at the temporary histdata / MT5 caches."""
    sources, hist, mt5 = feeds
    for name in ("chart_adapter", "chart_cached_days", "feed_switch"):
        monkeypatch.setattr(chart, name, partial(getattr(cd, name), histdata_dir=hist, mt5_dir=mt5))
    chart._cached_replay.cache_clear()
    chart.chart_data.cache_clear()
    yield sources
    chart._cached_replay.cache_clear()
    chart.chart_data.cache_clear()


def test_chart_range_past_the_last_histdata_day_loads_mt5_days(wired):
    payload, message = chart.base_payload(wired, SYMBOL, "M1", "2026-10-02", "2026-10-05")
    assert payload is not None, message
    opens = payload["candles"]["o"]
    assert len(opens) == 40  # 4 days x 10 minutes, MT5 copy of 10-03 not added
    assert HIST_LEVEL <= min(opens) < HIST_LEVEL + 10  # histdata days
    assert max(opens) >= MT5_LEVEL  # MT5 days after the last histdata day


def test_chart_days_and_replay_feed_switch_include_mt5(wired):
    days = chart.chart_cached_days(wired, SYMBOL)
    assert D("2026-10-05") in days and D("2026-10-05") not in wired.cached_days(SYMBOL)
    replay, _ = chart.load_replay(wired, SYMBOL, "M1", "2026-10-02", "2026-10-05")
    data = chart.chart_data(replay, chart.DEFAULT_SETTINGS, wired, ChartConfig())
    assert (
        data.feed_switch == chart.feed_switch(wired, SYMBOL) == D("2026-10-04")
    )  # first MT5 day after histdata


def test_strategy_overlays_get_the_plain_histdata_sources(wired, monkeypatch):
    seen = []

    class Fake:
        strategy_settings = False
        needs_sources = True

        def detect(self, replay, settings, sources):
            seen.append(sources)
            return []

    replay, _ = chart.load_replay(wired, SYMBOL, "M1", "2026-10-01", "2026-10-03")
    chart._cached_events.cache_clear()
    chart._cached_events(replay, Fake(), chart.DEFAULT_SETTINGS, wired)
    assert seen == [wired]
    assert wired.cached_days(SYMBOL) == [D("2026-10-01"), D("2026-10-02"), D("2026-10-03")]
    assert not isinstance(wired.adapter(SYMBOL), cd.FeedFillAdapter)
