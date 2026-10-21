"""MT5 preferred day by day, histdata for the days MT5 lacks (rule set by the user, 2026-10-19;
it replaced the chart-only fill after the last histdata day of ROADMAP 7.5). The chart and the
backtests read through the same `SymbolSources`."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from backtester.core.models import Timeframe
from backtester.data.adapters.cache_adapter import (
    CacheAdapter,
    MissingCacheError,
    PreferredCacheAdapter,
)
from backtester.data.cache import COLUMNS, MT5_CACHE_DIR, cache_path, write_atomic
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources

D = date.fromisoformat
SYMBOL = "XAUUSD"
HIST_LEVEL, MT5_LEVEL = 100.0, 200.0
MINUTES = 10
ALL_DAYS = [D(f"2026-10-0{i}") for i in range(1, 6)]


def put(root: Path, day: str, level: float) -> None:
    """A day with `MINUTES` moving M1 bars at price `level` from 10:00 UTC."""
    d = D(day)
    t0 = datetime(d.year, d.month, d.day, 10, tzinfo=UTC)
    rows = {"ts": pd.DatetimeIndex([t0 + timedelta(minutes=i) for i in range(MINUTES)])}
    for name in (c for c in COLUMNS if c != "ts"):
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
    sources = SymbolSources({SYMBOL: hist}, {SYMBOL: mt5})
    return sources, hist, mt5


def fetch(adapter, first, last, tf=Timeframe.M1):
    start = datetime.combine(D(first), datetime.min.time(), UTC)
    end = datetime.combine(D(last) + timedelta(days=1), datetime.min.time(), UTC)
    return adapter.fetch_frame(SYMBOL, tf, start, end)


def test_day_only_in_histdata_is_read_from_histdata(feeds):
    sources, *_ = feeds
    frame = fetch(sources.adapter(SYMBOL), "2026-10-01", "2026-10-02")
    assert set(frame["open"] // 100 * 100) == {HIST_LEVEL} and len(frame) == 2 * MINUTES


def test_day_in_both_is_read_from_mt5(feeds):
    sources, *_ = feeds
    frame = fetch(sources.adapter(SYMBOL), "2026-10-03", "2026-10-03")
    assert set(frame["open"] // 100 * 100) == {MT5_LEVEL} and len(frame) == MINUTES


def test_day_only_in_mt5_is_read_from_mt5(feeds):
    sources, *_ = feeds
    frame = fetch(sources.adapter(SYMBOL), "2026-10-04", "2026-10-05")
    assert set(frame["open"] // 100 * 100) == {MT5_LEVEL} and len(frame) == 2 * MINUTES


def test_mixed_range_has_each_day_once_and_no_duplicates_on_m5(feeds):
    sources, *_ = feeds
    adapter = sources.adapter(SYMBOL)
    frame = fetch(adapter, "2026-10-01", "2026-10-05")
    assert frame["ts"].is_monotonic_increasing and frame["ts"].is_unique
    assert len(frame) == 5 * MINUTES
    level = frame["open"] // 100 * 100
    assert list(level[frame["ts"].dt.date <= D("2026-10-02")].unique()) == [HIST_LEVEL]
    m5 = fetch(adapter, "2026-10-01", "2026-10-05", Timeframe.M5)
    assert m5["ts"].is_monotonic_increasing and m5["ts"].is_unique


def test_cached_days_are_the_union(feeds):
    sources, *_ = feeds
    assert sources.cached_days(SYMBOL) == ALL_DAYS


def test_feed_switch_is_the_first_mt5_day_after_the_last_histdata_only_day(feeds):
    sources, *_ = feeds
    assert sources.feed_switch(SYMBOL) == D("2026-10-03")  # histdata-only up to 10-02


def test_no_switch_without_histdata_only_days_or_without_mt5(tmp_path, feeds):
    _, hist, _ = feeds
    assert SymbolSources({SYMBOL: hist}).feed_switch(SYMBOL) is None
    assert SymbolSources({SYMBOL: hist}, {SYMBOL: tmp_path / "none"}).feed_switch(SYMBOL) is None
    c_hist, c_mt5 = tmp_path / "ch", tmp_path / "cm"
    put(c_hist, "2026-10-05", HIST_LEVEL)
    put(c_mt5, "2026-10-04", MT5_LEVEL)
    put(c_mt5, "2026-10-05", MT5_LEVEL)
    assert SymbolSources({SYMBOL: c_hist}, {SYMBOL: c_mt5}).feed_switch(SYMBOL) is None


def test_without_an_mt5_folder_it_is_histdata_only(tmp_path, feeds):
    _, hist, _ = feeds
    sources = SymbolSources({SYMBOL: hist}, {SYMBOL: tmp_path / "no_mt5"})
    adapter = sources.adapter(SYMBOL)
    assert len(fetch(adapter, "2026-10-01", "2026-10-03")) == 3 * MINUTES
    with pytest.raises(MissingCacheError):
        fetch(adapter, "2026-10-03", "2026-10-04")
    assert sources.cached_days(SYMBOL) == ALL_DAYS[:3]


def test_a_day_in_neither_feed_still_raises_missing_cache_error(feeds):
    sources, *_ = feeds
    with pytest.raises(MissingCacheError, match="2026-10-06"):
        fetch(sources.adapter(SYMBOL), "2026-10-05", "2026-10-06")


def test_multi_day_candles_span_the_seam(feeds):
    sources, *_ = feeds
    frame = fetch(sources.adapter(SYMBOL), "2026-10-01", "2026-10-05", Timeframe.D1)
    assert frame["ts"].is_unique  # built from both feeds, no error


def test_symbol_without_a_preferred_folder_is_left_alone(feeds):
    _, _, mt5 = feeds
    other = SymbolSources({SYMBOL: mt5})
    assert type(other.adapter(SYMBOL)) is CacheAdapter
    assert other.feed_switch(SYMBOL) is None
    assert other.cached_days(SYMBOL) == ALL_DAYS[2:]


def test_preferred_folder_changes_equality_and_hash(feeds):
    sources, hist, mt5 = feeds
    plain = SymbolSources({SYMBOL: hist})
    assert plain != sources and hash(plain) != hash(sources)
    same = SymbolSources({SYMBOL: hist}, {SYMBOL: mt5})
    assert sources == same and hash(sources) == hash(same)
    assert isinstance(sources.adapter(SYMBOL), PreferredCacheAdapter)


def test_default_sources_prefer_mt5_for_histdata_symbols_only():
    for symbol in ("NAS100", "XAUUSD", "EURUSD", "AUDUSD"):
        assert DEFAULT_SOURCES.preferred_dirs[symbol] == MT5_CACHE_DIR
        assert isinstance(DEFAULT_SOURCES.adapter(symbol), PreferredCacheAdapter)
    for symbol in ("US30", "BTCUSD", "BTCUSDT", "ETHUSDT"):  # MT5-only and Binance
        assert symbol not in DEFAULT_SOURCES.preferred_dirs
    for symbol in ("BTCUSDT", "ETHUSDT"):  # Binance: no MT5 feed, no live bot
        assert type(DEFAULT_SOURCES.adapter(symbol)) is CacheAdapter


# --- live folder: the last fallback, day by day (ROADMAP 7.8) --------------------------------------

LIVE_LEVEL = 300.0


@pytest.fixture
def with_live(feeds, tmp_path):
    """The feeds plus a live folder with 10-05 (also in MT5) and 10-06 (only live)."""
    _, hist, mt5 = feeds
    live = tmp_path / "live"
    put(live, "2026-10-05", LIVE_LEVEL)
    put(live, "2026-10-06", LIVE_LEVEL)
    return SymbolSources({SYMBOL: hist}, {SYMBOL: mt5}, {SYMBOL: live}), hist, mt5, live


def test_live_only_day_is_listed_and_read(with_live):
    sources, *_ = with_live
    assert sources.cached_days(SYMBOL)[-1] == D("2026-10-06")
    frame = fetch(sources.adapter(SYMBOL), "2026-10-06", "2026-10-06")
    assert set(frame["open"] // 100 * 100) == {LIVE_LEVEL} and len(frame) == MINUTES


def test_mt5_and_histdata_win_over_live(with_live):
    sources, *_ = with_live
    frame = fetch(sources.adapter(SYMBOL), "2026-10-01", "2026-10-05")
    assert LIVE_LEVEL not in set(frame["open"] // 100 * 100)
    assert len(frame) == 5 * MINUTES


def test_live_extends_the_run_of_cached_days(with_live):
    sources, *_ = with_live
    days = sources.cached_days(SYMBOL)
    assert days == ALL_DAYS + [D("2026-10-06")]
    frame = fetch(sources.adapter(SYMBOL), "2026-10-01", "2026-10-06")  # the seam crosses 3 feeds
    assert len(frame) == 6 * MINUTES


def test_symbol_without_a_preferred_folder_still_falls_back_to_live(tmp_path):
    mt5, live = tmp_path / "mt5", tmp_path / "live"  # US30: MT5 is the main folder
    put(mt5, "2026-10-04", MT5_LEVEL)
    put(live, "2026-10-05", LIVE_LEVEL)
    sources = SymbolSources({SYMBOL: mt5}, fallback_dirs={SYMBOL: live})
    assert sources.cached_days(SYMBOL) == [D("2026-10-04"), D("2026-10-05")]
    frame = fetch(sources.adapter(SYMBOL), "2026-10-04", "2026-10-05")
    assert len(frame) == 2 * MINUTES


def test_live_day_missing_everywhere_still_raises(with_live):
    sources, *_ = with_live
    with pytest.raises(MissingCacheError, match="2026-10-07"):
        fetch(sources.adapter(SYMBOL), "2026-10-06", "2026-10-07")


def test_live_folder_changes_equality_and_hash(with_live, feeds):
    sources, *_ = with_live
    assert sources != feeds[0] and hash(sources) != hash(feeds[0])


def test_stamp_changes_when_the_live_file_is_rewritten(with_live):
    sources, _, _, live = with_live
    before = sources.fallback_stamp(SYMBOL)
    put(live, "2026-10-06", LIVE_LEVEL + 1)  # the bot rewrites today's file each minute
    assert sources.fallback_stamp(SYMBOL) != before
    assert SymbolSources({SYMBOL: live}).fallback_stamp(SYMBOL) == ()  # no fallback: no stamp


def test_chart_reload_shows_the_rewritten_live_day(with_live):
    from backtester.ui.pages.chart import load_replay

    sources, _, _, live = with_live
    first, _ = load_replay(sources, SYMBOL, "M1", "2026-10-06", "2026-10-06")
    assert len(first) == MINUTES
    put(live, "2026-10-06", LIVE_LEVEL)  # same name; make it longer
    path = cache_path(live, SYMBOL, D("2026-10-06"))
    frame = pd.read_parquet(path)
    longer = pd.concat([frame, frame.assign(ts=frame["ts"] + timedelta(minutes=MINUTES))])
    write_atomic(longer.reset_index(drop=True), path)
    second, _ = load_replay(sources, SYMBOL, "M1", "2026-10-06", "2026-10-06")
    assert len(second) == 2 * MINUTES


def test_chart_sources_read_live_last_backtests_never():
    from backtester.data.cache import LIVE_CACHE_DIR
    from backtester.data.sources import CHART_SOURCES

    for symbol in ("US500", "NAS100", "US30", "US2000"):
        assert CHART_SOURCES.fallback_dirs[symbol] == LIVE_CACHE_DIR
    assert "BTCUSDT" not in CHART_SOURCES.fallback_dirs
    assert not DEFAULT_SOURCES.fallback_dirs  # backtests / tools never see a partial live day
    assert CHART_SOURCES.cache_dirs == DEFAULT_SOURCES.cache_dirs
