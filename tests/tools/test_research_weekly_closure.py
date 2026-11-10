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


@pytest.mark.parametrize("symbol", ["BTCUSD", "ETHUSD"])
@pytest.mark.parametrize("missing_neighbor", [7, 9])
def test_saturday_next_to_missing_friday_or_sunday_remains_a_gap(
    tmp_path, symbol, missing_neighbor
):
    sources, _ = cache(tmp_path, symbol, date(2022, 1, 1), 10)
    for day in (8, missing_neighbor):
        cache_path(tmp_path, symbol, date(2022, 1, day)).unlink()
    assert date(2022, 1, 8) not in sources.covered_days(symbol)
    assert segments(symbol, date(2022, 1, 1), date(2022, 1, 10), sources) == [
        (date(2022, 1, 1), date(2022, 1, min(8, missing_neighbor) - 1)),
        (date(2022, 1, max(8, missing_neighbor) + 1), date(2022, 1, 10)),
    ]
    with pytest.raises(MissingCacheError):
        sources.adapter(symbol).fetch_frame(
            symbol, Timeframe.M1, datetime(2022, 1, 1, tzinfo=UTC),
            datetime(2022, 1, 11, tzinfo=UTC)
        )


@pytest.mark.parametrize("symbol", ["BTCUSD", "ETHUSD"])
@pytest.mark.parametrize("year", [2018, 2021, 2022, 2026])
def test_mixed_present_and_isolated_missing_saturdays_are_loadable(tmp_path, symbol, year):
    first, last = date(year, 1, 1), date(year, 1, 31)
    sources, days = cache(tmp_path, symbol, first, 31)
    saturdays = [d for d in days if d.weekday() == 5]
    missing = saturdays[1:3]  # keep actual Saturday candles elsewhere in the same year
    for day in missing:
        cache_path(tmp_path, symbol, day).unlink()
    physical = [d for d in days if d not in missing]
    assert segments(symbol, first, last, sources) == [(first, last)]
    assert sources.cached_days(symbol) == physical
    assert sources.covered_days(symbol) == set(days)
    for timeframe in (Timeframe.M1, Timeframe.D1):
        frame = sources.adapter(symbol).fetch_frame(
            symbol, timeframe, datetime(year, 1, 1, tzinfo=UTC),
            datetime(year, 2, 1, tzinfo=UTC), boundary=DayBoundary.UTC
        )
        assert list(frame.ts.dt.date) == physical


@pytest.mark.parametrize("symbol", ["BTCUSD", "ETHUSD"])
def test_isolated_saturday_at_year_boundary_is_covered(tmp_path, symbol):
    first, last = date(2021, 12, 31), date(2022, 1, 2)
    sources, _ = cache(tmp_path, symbol, first, 3, omitted=(5,))
    assert segments(symbol, first, last, sources) == [(first, last)]


@pytest.mark.parametrize("symbol", ["GBPUSD", "BTCUSDT", "XAUUSD"])
def test_other_symbols_keep_isolated_saturday_gaps_in_mixed_cache(tmp_path, symbol):
    sources, _ = cache(tmp_path, symbol, date(2022, 1, 1), 10)
    cache_path(tmp_path, symbol, date(2022, 1, 8)).unlink()
    assert segments(symbol, date(2022, 1, 1), date(2022, 1, 10), sources) == [
        (date(2022, 1, 1), date(2022, 1, 7)), (date(2022, 1, 9), date(2022, 1, 10))
    ]
