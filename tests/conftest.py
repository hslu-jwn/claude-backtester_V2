"""Shared test helpers.

`make_candles` builds a series from compact OHLC tuples so fixtures stay readable:

    candles = make_candles([
        (1.00, 1.05, 0.99, 1.04),   # green
        (1.04, 1.06, 1.01, 1.02),   # red
    ])
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import pytest

from backtester.core.models import Candle, Timeframe
from backtester.core.series import CandleSeries

DEFAULT_START = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)  # a Monday


def build_candles(
    ohlc: Sequence[tuple[float, float, float, float]],
    timeframe: Timeframe = Timeframe.M5,
    start: datetime = DEFAULT_START,
) -> list[Candle]:
    return [
        Candle(ts=start + i * timeframe.duration, open=o, high=h, low=lo, close=c)
        for i, (o, h, lo, c) in enumerate(ohlc)
    ]


def build_series(
    ohlc: Sequence[tuple[float, float, float, float]],
    timeframe: Timeframe = Timeframe.M5,
    start: datetime = DEFAULT_START,
    symbol: str = "TEST",
) -> CandleSeries:
    return CandleSeries(symbol, timeframe, build_candles(ohlc, timeframe, start))


@pytest.fixture(autouse=True)
def trials_log_in_tmp(tmp_path, monkeypatch):
    """Tools append to results/trials.jsonl (ROADMAP 12.10); tests must never touch the real one."""
    from backtester.analytics import trial_log

    monkeypatch.setattr(trial_log, "RESULTS_DIR", tmp_path / "_results")


@pytest.fixture(autouse=True)
def no_local_news_calendar(monkeypatch):
    """The default calendar path (data/news/economic_events.csv) is the real local file; tests
    see "no calendar" for it instead. A test that loads a calendar passes its own path."""
    from backtester.data import news

    default = news.NewsConfig().path
    real = news.load_calendar

    def load_calendar(config):
        return None if config.path == default else real(config)

    monkeypatch.setattr(news, "load_calendar", load_calendar)


@pytest.fixture
def make_candles():
    return build_candles


@pytest.fixture
def make_series():
    return build_series
