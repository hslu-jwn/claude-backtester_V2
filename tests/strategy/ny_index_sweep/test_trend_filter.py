"""Strategy 2's trend filter: the direction of the last SMA-band cross on the filter timeframe.

Spec: strategy-ny-indices.md › Backtest options › Trend filter.
"""

from __future__ import annotations

import pytest

from backtester.core.models import Direction, Timeframe
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig, TrendFilterConfig
from backtester.strategy.ny_index_sweep.trend_filter import TrendFilter

H1 = Timeframe.H1
BULL, BEAR = Direction.BULLISH, Direction.BEARISH
# closes 1, 1, 1, 4, 5, 0: SMA(3) cross up at candle 3, down at candle 5 (no band)
OHLC = [(c, c + 0.5, c - 0.5, c) for c in (1.0, 1.0, 1.0, 4.0, 5.0, 0.0)]
SMALL = TrendFilterConfig(enabled=True, sma_period=3, band_atr=0.0, atr_period=2)


def test_direction_is_the_last_cross_and_holds_between_crosses(make_series):
    s = make_series(OHLC, H1)
    f = TrendFilter(SMALL)
    seen = []
    for cursor in range(len(s)):
        f.update(s.view(cursor))
        seen.append(f.direction)
    assert seen == [None, None, None, BULL, BULL, BEAR]


def test_catches_up_on_every_candle_closed_since_the_last_call(make_series):
    s = make_series(OHLC, H1)
    f = TrendFilter(SMALL)
    f.update(s.view(2))
    assert f.direction is None
    f.update(s.view(5))  # candles 3, 4, 5 in one call: the cross at 3 is not skipped
    assert f.direction is BEAR
    f.update(s.view(5))  # same cursor again: nothing changes
    f.update(None)  # no candle of the filter timeframe yet
    assert f.direction is BEAR


def test_no_lookahead_a_cut_series_gives_the_same_direction(make_series):
    full = make_series(OHLC, H1)
    for cut in range(len(OHLC)):
        a, b = TrendFilter(SMALL), TrendFilter(SMALL)
        a.update(full.view(cut))
        b.update(make_series(OHLC[: cut + 1], H1).view(cut))
        assert a.direction is b.direction


def test_defaults_are_off_and_strategy_4s_best_variant():
    cfg = NyIndexSweepConfig().trend_filter
    assert cfg == TrendFilterConfig()
    assert (cfg.enabled, cfg.timeframe, cfg.sma_period, cfg.band_atr, cfg.atr_period) == (
        False, H1, 50, 1.0, 20,
    )  # fmt: skip


@pytest.mark.parametrize(
    "kwargs",
    [
        {"timeframe": Timeframe.M1},  # not a timeframe strategy 2 loads for this
        {"timeframe": Timeframe.D1},
        {"sma_period": 1},
        {"band_atr": -0.5},
        {"atr_period": 0},
    ],
)
def test_rejects_bad_settings(kwargs):
    with pytest.raises(ValueError):
        TrendFilterConfig(**kwargs)


def test_settings_json_round_trip_keeps_the_trend_filter():
    from backtester.settings import RunSettings, from_json, to_json

    cfg = NyIndexSweepConfig(
        trend_filter=TrendFilterConfig(enabled=True, timeframe=Timeframe.H4, sma_period=40)
    )
    settings = RunSettings(strategy=cfg)
    assert from_json(to_json(settings)).strategy.trend_filter == cfg.trend_filter
