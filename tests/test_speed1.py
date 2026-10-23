"""Speed steps 1-3 preserve cache validation and closed-only replay snapshots.

Spec: docs/review/speed.md steps 1-3; ARCHITECTURE.md, no-lookahead invariant.
"""

from dataclasses import FrozenInstanceError, fields
from datetime import UTC, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest
from conftest import DEFAULT_START, build_series
from m1_frames import m1

from backtester.core.errors import LookaheadError
from backtester.core.models import Candle, Timeframe
from backtester.core.mtf import HigherTimeframeClock
from backtester.data.adapters.cache_adapter import CacheAdapter, candles_from_frame
from backtester.data.cache import cache_path, write_atomic
from backtester.engine.backtest import Backtest
from backtester.engine.replay import Replay
from backtester.strategy.base import Strategy


def frame():
    return pd.DataFrame(
        {
            "ts": pd.date_range(DEFAULT_START, periods=3, freq="min"),
            "open": [100.0, 101.0, -0.0],
            "high": [102.0, 103.0, 0.0],
            "low": [98.0, 99.0, -0.0],
            "close": [101.0, 102.0, 0.0],
            "volume": [0.0, float("nan"), -1.0],
            "spread": [float("nan"), 0.0, float("inf")],
        }
    )


def original_conversion(data):
    """The adapter's original public-constructor path, including error ordering."""
    return [
        Candle(
            row.ts.to_pydatetime(),
            row.open,
            row.high,
            row.low,
            row.close,
            row.volume,
            row.spread,
        )
        for row in data.itertuples(index=False)
    ]


def assert_candles_identical(actual, expected):
    assert len(actual) == len(expected)
    for got, want in zip(actual, expected):
        assert type(got) is Candle and type(got.ts) is type(want.ts)
        for field in fields(Candle):
            a, b = getattr(got, field.name), getattr(want, field.name)
            if isinstance(b, float):
                assert a.hex() == b.hex()  # Includes signed zero and nonfinite metadata.
            else:
                assert a == b
        with pytest.raises(FrozenInstanceError):
            got.close = 123.0


@pytest.mark.parametrize("timezone", [UTC, "America/New_York", None])
def test_cache_conversion_preserves_values_and_timestamp_handling(timezone):
    data = frame()
    data["ts"] = data.ts.dt.tz_convert(timezone)
    if timezone is None:
        with pytest.raises(ValueError, match="timezone-aware"):
            candles_from_frame(data)
    else:
        assert_candles_identical(candles_from_frame(data), original_conversion(data))


@pytest.mark.parametrize("column", ["open", "high", "low", "close"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_cache_prices_raise_the_original_error(column, bad):
    data = frame()
    data.loc[1, column] = bad
    with pytest.raises(ValueError) as expected:
        original_conversion(data)
    with pytest.raises(ValueError) as actual:
        candles_from_frame(data)
    assert str(actual.value) == str(expected.value)


@pytest.mark.parametrize(
    "bad",
    [
        {"high": 100.0},
        {"low": 103.0},
        {"open": 104.0},
        {"close": 104.0},
        {"high": 99.0, "low": 100.0},
        {"ts": pd.NaT},
    ],
)
def test_malformed_rows_raise_the_original_first_error(bad):
    data = frame()
    for column, value in bad.items():
        data.loc[1, column] = value
    data.loc[2, "open"] = float("inf")  # A later error must not mask row 1.
    with pytest.raises(ValueError) as expected:
        original_conversion(data)
    with pytest.raises(ValueError) as actual:
        candles_from_frame(data)
    assert str(actual.value) == str(expected.value)


def test_unusual_frame_layouts_and_dtypes_keep_constructor_behavior():
    data = frame()
    data["open"] = data.open.astype(object)
    data = data[list(reversed(data.columns))].assign(extra="ignored")
    assert_candles_identical(candles_from_frame(data), original_conversion(data))
    data.loc[1, "open"] = "bad"
    with pytest.raises(TypeError):
        candles_from_frame(data)
    assert candles_from_frame(pd.DataFrame()) == []


def test_extreme_finite_prices_remain_exact():
    data = frame()
    for column in ("open", "high", "low", "close"):
        data[column] = [np.finfo(float).max, -np.finfo(float).max, np.nextafter(0.0, 1.0)]
    assert_candles_identical(candles_from_frame(data), original_conversion(data))


@pytest.mark.parametrize("timezone", [UTC, ZoneInfo("UTC")])
def test_standard_utc_frames_are_validated_without_per_candle_revalidation(monkeypatch, timezone):
    data = frame()
    data["ts"] = data.ts.dt.tz_convert(timezone)
    expected = original_conversion(data)
    calls = []
    original = Candle.__post_init__

    def counted(self):
        calls.append(self)
        original(self)

    monkeypatch.setattr(Candle, "__post_init__", counted)
    assert_candles_identical(candles_from_frame(data), expected)
    assert calls == []
    # The normal constructor must still reject malformed candles.
    with pytest.raises(ValueError, match="finite"):
        Candle(DEFAULT_START, float("inf"), 2.0, 0.0, 1.0)
    assert len(calls) == 1


def test_bad_ohlc_in_a_cached_day_still_raises(tmp_path):
    data = m1(("12:00", 100.0, 99.0, 98.0, 100.0, 1.0, 0.2))
    path = cache_path(tmp_path, "TEST", pd.Timestamp("2026-09-02").date())
    write_atomic(data, path)
    with pytest.raises(ValueError, match="Inconsistent OHLC"):
        CacheAdapter(tmp_path).fetch(
            "TEST",
            Timeframe.M1,
            pd.Timestamp("2026-09-02", tz="UTC").to_pydatetime(),
            pd.Timestamp("2026-09-03", tz="UTC").to_pydatetime(),
        )


@pytest.mark.parametrize("timeframe", list(Timeframe))
def test_timeframe_duration_is_constant(timeframe):
    assert timeframe.duration == timedelta(minutes=timeframe.value)
    assert timeframe.duration is timeframe.duration


def test_clock_snapshots_survive_advancing_rewinding_and_future_extension():
    prices = [(1.0, 2.0, 0.0, 1.0)] * 3
    clock = HigherTimeframeClock(build_series(prices[:2], Timeframe.H1))
    longer = HigherTimeframeClock(build_series(prices, Timeframe.H1))
    assert clock.view_at(DEFAULT_START + timedelta(minutes=59)) is None
    first = clock.view_at(DEFAULT_START + timedelta(hours=1))
    saved = tuple(first)
    assert tuple(clock.view_at(DEFAULT_START + timedelta(minutes=119))) == saved
    assert clock.view_at(DEFAULT_START + timedelta(hours=2)).cursor == 1
    assert clock.view_at(DEFAULT_START) is None
    assert tuple(clock.view_at(DEFAULT_START + timedelta(hours=1))) == saved
    assert tuple(longer.view_at(DEFAULT_START + timedelta(hours=1))) == saved
    assert first.cursor == 0 and tuple(first) == saved
    for action in (lambda: first[1], lambda: first.at(1), lambda: first.window(0, 2)):
        with pytest.raises(LookaheadError):
            action()


@pytest.mark.parametrize("cursor", [-1, 2])
def test_replay_close_time_still_rejects_invalid_cursors(cursor):
    replay = Replay(build_series([(1.0, 2.0, 0.0, 1.0)] * 2))
    with pytest.raises(IndexError, match=f"cursor {cursor} out of range 0..1"):
        replay.close_time(cursor)


class RecordingStrategy(Strategy):
    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5, Timeframe.M15, Timeframe.H1)

    def __init__(self):
        self.seen = []

    def on_candle(self, now, views):
        self.seen.append((now, views))
        return []


def test_engine_calculates_close_time_once_and_retains_closed_snapshots(monkeypatch):
    prices = [(1.0, 2.0, 0.0, 1.0)] * 24
    series = [build_series(prices, tf) for tf in RecordingStrategy.timeframes]
    strategy = RecordingStrategy()
    calls = []
    original = Replay.close_time

    def counted(self, cursor):
        calls.append(cursor)
        return original(self, cursor)

    monkeypatch.setattr(Replay, "close_time", counted)
    assert Backtest(strategy, series).run() == []
    assert calls == list(range(24))
    for cursor, (now, views) in enumerate(strategy.seen):
        assert now == DEFAULT_START + timedelta(minutes=5 * (cursor + 1))
        assert views[Timeframe.M5].cursor == cursor
        for tf in (Timeframe.M15, Timeframe.H1):
            expected = (5 * (cursor + 1)) // tf.value - 1
            view = views[tf]
            if expected < 0:
                assert view is None
            else:
                assert view.cursor == expected
                with pytest.raises(LookaheadError):
                    view[expected + 1]
    assert len({id(views) for _, views in strategy.seen}) == 24
