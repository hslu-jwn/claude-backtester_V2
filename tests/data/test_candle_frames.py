"""Candles -> per-UTC-day cache frames, the same columns and values as the MT5 downloader
writes (ROADMAP 7.8): `bid_*` = the bar, `ask_*` = bid + spread (NaN when spread is 0)."""

from __future__ import annotations

from datetime import UTC, date, datetime

import numpy as np
import pandas as pd
import pytest

from backtester.core.models import Candle
from backtester.data.cache import COLUMNS, cache_path, read_cached_day, write_atomic
from backtester.data.mt5_download import cache_frame, candle_day_frames


def candle(day, hh, mm, price, spread=0.25, volume=7.0):
    ts = datetime(2026, 9, day, hh, mm, tzinfo=UTC)
    return Candle(ts, price, price + 1, price - 1, price + 0.5, volume, spread)


def test_no_candles_no_frames():
    assert candle_day_frames([]) == {}


def test_split_on_the_utc_day_with_cache_columns():
    frames = candle_day_frames(
        [candle(1, 23, 58, 100), candle(1, 23, 59, 101), candle(2, 0, 0, 102)]
    )
    assert sorted(frames) == [date(2026, 9, 1), date(2026, 9, 2)]
    first = frames[date(2026, 9, 1)]
    assert list(first.columns) == COLUMNS and len(first) == 2
    assert len(frames[date(2026, 9, 2)]) == 1


def test_values_equal_the_downloaders_cache_frame():
    candles = [candle(1, 10, 0, 100, spread=0.25, volume=7), candle(1, 10, 1, 101, spread=0.0)]
    (frame,) = candle_day_frames(candles).values()
    bars = pd.DataFrame(
        {
            "ts": pd.to_datetime([c.ts for c in candles], utc=True),
            "open": [c.open for c in candles], "high": [c.high for c in candles],
            "low": [c.low for c in candles], "close": [c.close for c in candles],
            "volume": [c.volume for c in candles], "spread": [c.spread for c in candles],
        }
    )  # fmt: skip
    pd.testing.assert_frame_equal(frame, cache_frame(bars))
    assert frame["ask_close"].iloc[0] == pytest.approx(100.75)
    assert np.isnan(frame["ask_close"].iloc[1])  # spread 0: no ask, never "ask = bid"


def test_nan_spread_has_no_ask():
    (frame,) = candle_day_frames([candle(1, 10, 0, 100, spread=float("nan"))]).values()
    assert np.isnan(frame["ask_open"].iloc[0]) and frame["bid_open"].iloc[0] == 100


def test_round_trip_through_the_day_cache(tmp_path):
    (frame,) = candle_day_frames([candle(1, 10, 0, 100), candle(1, 10, 1, 101)]).values()
    path = cache_path(tmp_path, "US500", date(2026, 9, 1))
    write_atomic(frame, path)
    back = read_cached_day(path)
    assert list(back.columns) == COLUMNS
    pd.testing.assert_frame_equal(back, frame)
