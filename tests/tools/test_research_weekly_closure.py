"""Weekly crypto closures are coverage, never fabricated candles or missing trading days."""

from datetime import UTC, date, datetime, timedelta

import pytest
from m1_frames import m1

from backtester.core.models import Timeframe
from backtester.data.adapters.cache_adapter import MissingCacheError
from backtester.data.cache import cache_path, empty_cache_frame
from backtester.data.resample import DayBoundary
from backtester.data.sources import SymbolSources
from backtester.runner import RunSettings, _load
from backtester.strategy.trend_following.config import TrendFollowingConfig
from backtester.tools.research import segments


def cache(root, symbol, first, count, omitted=(), empty_weekends=False):
    days = []
    for offset in range(count):
        day = first + timedelta(days=offset)
        if day.weekday() in omitted:
            continue
        path = cache_path(root, symbol, day)
        path.parent.mkdir(parents=True, exist_ok=True)
        frame = empty_cache_frame() if empty_weekends and day.weekday() >= 5 else m1(
            ("12:00", 100, 102, 99, 101, 1, 0), day=day.isoformat()
        )
        frame.to_parquet(path, index=False)
        days.append(day)
    return SymbolSources.single(root, [symbol]), days


@pytest.mark.parametrize("symbol", ["BTCUSD", "ETHUSD"])
def test_missing_saturdays_make_one_loadable_segment_without_fake_candles(tmp_path, symbol):
    first, last = date(2019, 1, 1), date(2019, 1, 21)
    sources, days = cache(tmp_path, symbol, first, 21, omitted=(5,))
    assert segments(symbol, first, last, sources) == [(first, last)]
    assert sources.cached_days(symbol) == days  # no virtual files in the inventory
    adapter = sources.adapter(symbol)
    start, end = datetime(2019, 1, 1, tzinfo=UTC), datetime(2019, 1, 22, tzinfo=UTC)
    for tf in (Timeframe.M1, Timeframe.D1, Timeframe.W1):
        frame = adapter.fetch_frame(symbol, tf, start, end, boundary=DayBoundary.UTC)
        if tf != Timeframe.W1:
            assert list(frame.ts.dt.date) == days
        else:
            assert len(frame) == 2  # two complete calendar weeks, no half edge week
    job = _load(sources, symbol, last, last, RunSettings(
        strategy=TrendFollowingConfig(timeframe=Timeframe.D1)
    ))
    assert job.warmup_from == first


def test_real_multiday_hole_still_splits_and_adapter_refuses_it(tmp_path):
    first, last = date(2019, 1, 1), date(2019, 1, 21)
    sources, _ = cache(tmp_path, "BTCUSD", first, 21, omitted=(5,))
    for day in (date(2019, 1, 10), date(2019, 1, 11)):
        cache_path(tmp_path, "BTCUSD", day).unlink()
    assert segments("BTCUSD", first, last, sources) == [
        (first, date(2019, 1, 9)), (date(2019, 1, 13), last)
    ]
    with pytest.raises(MissingCacheError):
        sources.adapter("BTCUSD").fetch_frame(
            "BTCUSD", Timeframe.M1, datetime(2019, 1, 1, tzinfo=UTC),
            datetime(2019, 1, 22, tzinfo=UTC)
        )


@pytest.mark.parametrize("symbol", ["GBPUSD", "BTCUSDT"])
def test_other_symbols_do_not_infer_saturday_closures(tmp_path, symbol):
    sources, _ = cache(tmp_path, symbol, date(2019, 1, 4), 4, omitted=(5,))
    assert segments(symbol, date(2019, 1, 4), date(2019, 1, 7), sources) == [
        (date(2019, 1, 4), date(2019, 1, 4)), (date(2019, 1, 6), date(2019, 1, 7))
    ]


def test_fx_cached_empty_weekend_still_makes_one_segment(tmp_path):
    sources, _ = cache(tmp_path, "GBPUSD", date(2019, 1, 4), 4, empty_weekends=True)
    assert segments("GBPUSD", date(2019, 1, 4), date(2019, 1, 7), sources) == [
        (date(2019, 1, 4), date(2019, 1, 7))
    ]


def test_saturday_trading_in_another_year_does_not_change_old_closures(tmp_path):
    sources, _ = cache(tmp_path, "BTCUSD", date(2019, 1, 4), 4, omitted=(5,))
    cache(tmp_path, "BTCUSD", date(2022, 1, 1), 2)
    assert segments("BTCUSD", date(2019, 1, 4), date(2019, 1, 7), sources) == [
        (date(2019, 1, 4), date(2019, 1, 7))
    ]


def test_missing_saturday_in_a_year_with_saturday_files_remains_a_gap(tmp_path):
    sources, _ = cache(tmp_path, "BTCUSD", date(2022, 1, 1), 10)
    cache_path(tmp_path, "BTCUSD", date(2022, 1, 8)).unlink()
    assert segments("BTCUSD", date(2022, 1, 1), date(2022, 1, 10), sources) == [
        (date(2022, 1, 1), date(2022, 1, 7)), (date(2022, 1, 9), date(2022, 1, 10))
    ]
