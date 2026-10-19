"""Chart page wiring of the day-by-day MT5 preference (rule of 2026-10-19): the chart reads
through the same `SymbolSources` as backtests and the strategy overlays."""

from __future__ import annotations

from datetime import date

import pytest
from test_chart_feed import HIST_LEVEL, MT5_LEVEL, SYMBOL, feeds, put  # noqa: F401

from backtester.ui.chart_config import ChartConfig
from backtester.ui.pages import chart

D = date.fromisoformat


@pytest.fixture
def wired(feeds):  # noqa: F811
    sources, _, _ = feeds
    chart._cached_replay.cache_clear()
    chart.chart_data.cache_clear()
    yield sources
    chart._cached_replay.cache_clear()
    chart.chart_data.cache_clear()


def test_chart_range_reads_mt5_where_it_has_the_day(wired):
    payload, message = chart.base_payload(wired, SYMBOL, "M1", "2026-10-02", "2026-10-05")
    assert payload is not None, message
    opens = payload["candles"]["o"]
    assert len(opens) == 40  # 4 days x 10 minutes, each day once
    assert HIST_LEVEL <= min(opens) < HIST_LEVEL + 10  # 10-02: histdata only
    assert max(opens) >= MT5_LEVEL  # 10-03 on: MT5


def test_replay_feed_switch_is_the_first_mt5_day_after_histdata_only_days(wired):
    replay, _ = chart.load_replay(wired, SYMBOL, "M1", "2026-10-02", "2026-10-05")
    data = chart.chart_data(replay, chart.DEFAULT_SETTINGS, wired, ChartConfig())
    assert data.feed_switch == wired.feed_switch(SYMBOL) == D("2026-10-03")


def test_strategy_overlays_get_the_same_sources(wired):
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
