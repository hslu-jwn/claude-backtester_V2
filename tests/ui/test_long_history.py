"""The chart with years of cached data: the Trades overlay's run window, its range limit
and refusing hopeless ranges early. Spec: ROADMAP.md › 6.3 (full history)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest

from backtester.core.models import Candle, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.replay import Replay
from backtester.ui.chart_config import DEFAULT_CONFIG
from backtester.ui.overlays import OverlayUnavailable
from backtester.ui.pages.chart import _load_frame
from backtester.ui.trades_overlay import detect_trades, run_window

YEARS = {date(2020, 1, 1) + timedelta(days=i) for i in range(2465)}  # 2020-01-01..2026-09-30


def test_the_run_starts_on_the_1st_of_the_month_before_and_ends_a_week_after():
    assert run_window(YEARS, date(2026, 9, 14), date(2026, 9, 18)) == (
        date(2026, 8, 1),
        date(2026, 9, 25),
    )
    # every range starting in the same month: the same start, so the same trades
    assert run_window(YEARS, date(2026, 9, 1), date(2026, 9, 3))[0] == date(2026, 8, 1)
    assert run_window(YEARS, date(2026, 1, 20), date(2026, 1, 21))[0] == date(2025, 12, 1)


def test_the_run_stays_within_the_cached_days():
    assert run_window(YEARS, date(2020, 1, 10), date(2020, 1, 12))[0] == date(2020, 1, 1)
    assert run_window(YEARS, date(2026, 9, 28), date(2026, 9, 30))[1] == date(2026, 9, 30)


class NoSources:
    def cached_days(self, symbol):
        raise AssertionError("the strategy must not run for a range this long")


def test_trades_are_refused_for_ranges_longer_than_the_limit():
    t0 = datetime(2025, 1, 1, tzinfo=UTC)
    candles = [Candle(t0 + timedelta(days=i), 100, 101, 99, 100) for i in range(200)]
    replay = Replay(CandleSeries("XAUUSD", Timeframe.D1, candles))
    with pytest.raises(OverlayUnavailable, match="up to 183 days"):
        detect_trades(replay, sources=NoSources())


class CountingSources:
    """Cached days only; reading candles fails the test."""

    def cached_days(self, symbol):
        return sorted(YEARS)

    def adapter(self, symbol):
        raise AssertionError("must be refused before reading the cache")


def test_years_on_5m_are_refused_before_reading_the_cache():
    frame, message = _load_frame(
        CountingSources(), "XAUUSD", "M5", "2020-01-01", "2026-09-30", DEFAULT_CONFIG
    )
    assert frame is None and "far more than the limit" in message and "4h or D" in message


def test_a_range_near_the_limit_is_still_loaded_and_checked_exactly():
    config = replace(DEFAULT_CONFIG, max_candles=20_000)
    with pytest.raises(AssertionError, match="before reading"):  # it does try to read
        _load_frame(CountingSources(), "XAUUSD", "M5", "2026-06-01", "2026-09-15", config)
