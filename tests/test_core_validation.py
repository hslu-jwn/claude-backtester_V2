"""Core review findings #1-3: reject invalid inputs without changing valid values."""

from dataclasses import replace
from datetime import datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo

import pytest
from conftest import DEFAULT_START, build_series

from backtester.core.errors import LookaheadError
from backtester.core.models import Candle


@pytest.mark.parametrize("stop", [-1, -5, -100])
def test_window_rejects_negative_stop_without_exposing_future(stop):
    for length in (1, 5, 10):
        view = build_series([(1, 2, 0, 1)] * length).view(0)
        with pytest.raises(IndexError, match="stop"):
            view.window(0, stop)
        with pytest.raises(LookaheadError):
            view.window(0, 2)
        assert view.window(0, 1) == (view.current,)
        assert view.window(0, 0) == ()


@pytest.mark.parametrize("field", ["open", "high", "low", "close"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_candle_rejects_nonfinite_ohlc(field, value):
    candle = Candle(DEFAULT_START, 1, 2, 0, 1)
    with pytest.raises(ValueError, match="finite"):
        replace(candle, **{field: value})


def test_candle_rejects_all_infinite_ohlc():
    with pytest.raises(ValueError, match="finite"):
        Candle(DEFAULT_START, *([float("inf")] * 4))


class NoOffset(tzinfo):
    def utcoffset(self, dt):
        return None


@pytest.mark.parametrize("zone", [None, NoOffset()])
def test_candle_rejects_naive_timestamp(zone):
    with pytest.raises(ValueError, match="aware"):
        Candle(datetime(2026, 1, 5, tzinfo=zone), 1, 2, 0, 1)


def test_candle_preserves_aware_timestamp_and_unknown_spread():
    ts = datetime(2026, 7, 5, tzinfo=ZoneInfo("Europe/Zurich"))
    candle = Candle(ts, 1, 2, 0, 1, spread=float("nan"))
    assert candle.ts is ts
    assert candle.ts.utcoffset() == timedelta(hours=2)
