"""Chart only: MT5 bars after a histdata symbol's last histdata day (ROADMAP 7.5).
Backtests keep one feed (data split rule): the engine's sources are never changed."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from backtester.core.models import Timeframe
from backtester.data.adapters.cache_adapter import CacheAdapter, MissingCacheError
from backtester.data.cache import (
    COLUMNS,
    DEFAULT_CACHE_DIR,
    MT5_CACHE_DIR,
    cache_path,
    write_atomic,
)
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.ui.chart_data import (
    FeedFillAdapter,
    chart_adapter,
    chart_cached_days,
    feed_switch,
)

D = date.fromisoformat
SYMBOL = "XAUUSD"
HIST_LEVEL, MT5_LEVEL = 100.0, 200.0
MINUTES = 10


def put(root: Path, day: str, level: float) -> None:
    """A day with `MINUTES` moving M1 bars at price `level` from 10:00 UTC."""
    d = D(day)
    t0 = datetime(d.year, d.month, d.day, 10, tzinfo=UTC)
    rows = {"ts": pd.DatetimeIndex([t0 + timedelta(minutes=i) for i in range(MINUTES)])}
    for i, name in enumerate(c for c in COLUMNS if c != "ts"):
        rows[name] = [level + 0.1 * m + (0.05 if "high" in name else 0) for m in range(MINUTES)]
    frame = pd.DataFrame(rows)[COLUMNS]
    frame[[c for c in COLUMNS if c.endswith("volume")]] = float("nan")
    write_atomic(frame, cache_path(root, SYMBOL, d))


@pytest.fixture
def feeds(tmp_path):
    hist, mt5 = tmp_path / "histdata", tmp_path / "mt5"
    for day in ("2026-10-01", "2026-10-02", "2026-10-03"):
        put(hist, day, HIST_LEVEL)
    for day in ("2026-10-03", "2026-10-04", "2026-10-05"):  # 10-03 overlaps histdata
        put(mt5, day, MT5_LEVEL)
    sources = SymbolSources({SYMBOL: hist})
    return sources, hist, mt5


def span(first: str, last: str):
    return (
        datetime.combine(D(first), datetime.min.time(), UTC),
        datetime.combine(D(last) + timedelta(days=1), datetime.min.time(), UTC),
    )


def fetch(adapter, first, last):
    start, end = span(first, last)
    return adapter.fetch_frame(SYMBOL, Timeframe.M1, start, end)


def test_range_inside_histdata_is_unchanged(feeds):
    sources, hist, mt5 = feeds
    plain = fetch(CacheAdapter(hist), "2026-10-01", "2026-10-03")
    chart = fetch(
        chart_adapter(sources, SYMBOL, mt5_dir=mt5, histdata_dir=hist), "2026-10-01", "2026-10-03"
    )
    pd.testing.assert_frame_equal(plain, chart)
    assert set(chart["open"] // 100 * 100) == {HIST_LEVEL}


def test_range_crossing_the_last_histdata_day_continues_with_mt5(feeds):
    sources, hist, mt5 = feeds
    frame = fetch(
        chart_adapter(sources, SYMBOL, mt5_dir=mt5, histdata_dir=hist), "2026-10-02", "2026-10-05"
    )
    assert frame["ts"].is_monotonic_increasing and frame["ts"].is_unique
    days = frame["ts"].dt.date
    level = frame["open"] // 100 * 100
    assert set(level[days <= D("2026-10-03")]) == {HIST_LEVEL}  # histdata up to its last day
    assert set(level[days > D("2026-10-03")]) == {MT5_LEVEL}  # MT5 after it
    assert sorted(days.unique()) == [
        D("2026-10-02"),
        D("2026-10-03"),
        D("2026-10-04"),
        D("2026-10-05"),
    ]
    assert len(frame) == 4 * MINUTES  # MT5's copy of 10-03 is not added


def test_higher_timeframe_on_the_mixed_range_has_no_duplicates(feeds):
    sources, hist, mt5 = feeds
    start, end = span("2026-10-01", "2026-10-05")
    frame = chart_adapter(sources, SYMBOL, mt5_dir=mt5, histdata_dir=hist).fetch_frame(
        SYMBOL, Timeframe.M5, start, end
    )
    assert frame["ts"].is_monotonic_increasing and frame["ts"].is_unique


def test_without_an_mt5_cache_the_chart_is_histdata_only(tmp_path, feeds):
    sources, hist, _ = feeds
    adapter = chart_adapter(sources, SYMBOL, mt5_dir=tmp_path / "no_mt5", histdata_dir=hist)
    assert len(fetch(adapter, "2026-10-01", "2026-10-03")) == 3 * MINUTES
    with pytest.raises(MissingCacheError):
        fetch(adapter, "2026-10-03", "2026-10-04")
    assert feed_switch(sources, SYMBOL, mt5_dir=tmp_path / "no_mt5", histdata_dir=hist) is None
    assert chart_cached_days(sources, SYMBOL, mt5_dir=tmp_path / "no_mt5", histdata_dir=hist) == [
        D("2026-10-01"), D("2026-10-02"), D("2026-10-03")
    ]  # fmt: skip


def test_feed_switch_is_the_first_mt5_day_after_histdata(feeds):
    sources, hist, mt5 = feeds
    assert feed_switch(sources, SYMBOL, mt5_dir=mt5, histdata_dir=hist) == D("2026-10-04")
    assert chart_cached_days(sources, SYMBOL, mt5_dir=mt5, histdata_dir=hist) == [
        D(f"2026-10-0{i}") for i in range(1, 6)
    ]


def test_no_switch_when_mt5_has_nothing_after_histdata(tmp_path):
    hist, mt5 = tmp_path / "h", tmp_path / "m"
    put(hist, "2026-10-05", HIST_LEVEL)
    put(mt5, "2026-10-04", MT5_LEVEL)
    put(mt5, "2026-10-05", MT5_LEVEL)
    sources = SymbolSources({SYMBOL: hist})
    assert feed_switch(sources, SYMBOL, mt5_dir=mt5, histdata_dir=hist) is None


def test_symbol_not_read_from_histdata_is_left_alone(feeds, tmp_path):
    _, hist, mt5 = feeds
    other = SymbolSources({SYMBOL: mt5})  # e.g. an MT5-only symbol or a --cache-dir override
    adapter = chart_adapter(other, SYMBOL, mt5_dir=mt5, histdata_dir=hist)
    assert type(adapter) is CacheAdapter and adapter.cache_dir == mt5
    assert feed_switch(other, SYMBOL, mt5_dir=mt5, histdata_dir=hist) is None
    assert chart_cached_days(other, SYMBOL, mt5_dir=mt5, histdata_dir=hist) == other.cached_days(
        SYMBOL
    )


def test_the_fill_is_an_adapter_of_the_chart_only(feeds):
    sources, hist, mt5 = feeds
    assert isinstance(
        chart_adapter(sources, SYMBOL, mt5_dir=mt5, histdata_dir=hist), FeedFillAdapter
    )


# --- the engine keeps one feed ---------------------------------------------------------------


def test_backtest_sources_still_read_histdata_only(feeds):
    sources, hist, mt5 = feeds
    chart_adapter(sources, SYMBOL, mt5_dir=mt5, histdata_dir=hist)  # building it changes nothing
    assert sources.cached_days(SYMBOL) == [D("2026-10-01"), D("2026-10-02"), D("2026-10-03")]
    adapter = sources.adapter(SYMBOL)
    assert type(adapter) is CacheAdapter and adapter.cache_dir == hist
    with pytest.raises(MissingCacheError):
        fetch(adapter, "2026-10-04", "2026-10-05")


def test_default_sources_are_untouched_by_the_chart_fill():
    for symbol in ("NAS100", "XAUUSD", "EURUSD"):
        adapter = DEFAULT_SOURCES.adapter(symbol)
        assert type(adapter) is CacheAdapter and adapter.cache_dir == DEFAULT_CACHE_DIR
    assert DEFAULT_SOURCES.cache_dir("US30") == MT5_CACHE_DIR


def test_engine_and_runner_do_not_import_the_chart_feed():
    from backtester import runner
    from backtester.engine import backtest

    for module in (runner, backtest):
        assert "chart_data" not in Path(module.__file__).read_text(encoding="utf-8")
