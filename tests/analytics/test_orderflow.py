"""Order-flow study on BTC / ETH bars: aggregation, features, forward targets, deciles, shuffle
baseline. Spec: ROADMAP.md > 11.13. Hand-built frames with known answers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backtester.analytics.orderflow import (
    OrderflowConfig,
    add_features,
    add_targets,
    aggregate,
    bucket,
    decile_table,
    half_spreads,
    shuffle_p95,
    spread,
)

T0 = pd.Timestamp("2020-01-01", tz="UTC")
HOUR = pd.Timedelta("1h")


def m1_frame(n: int, delta=None) -> pd.DataFrame:
    idx = pd.date_range(T0, periods=n, freq="1min")
    close = np.arange(n, dtype=float) + 100.0
    return pd.DataFrame(
        {
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": np.full(n, 2.0),
            "delta": np.ones(n) if delta is None else np.asarray(delta, float),
        },
        index=idx,
    )


def bars_frame(close, delta=None, volume=None, freq="1h") -> pd.DataFrame:
    n = len(close)
    idx = pd.date_range(T0, periods=n, freq=freq)
    close = np.asarray(close, dtype=float)
    return pd.DataFrame(
        {
            "open": close, "high": close + 1, "low": close - 1, "close": close,
            "volume": np.full(n, 10.0) if volume is None else np.asarray(volume, float),
            "delta": np.zeros(n) if delta is None else np.asarray(delta, float),
        },
        index=idx,
    )  # fmt: skip


def test_aggregate_sums_delta_and_volume_and_ohlc():
    bars = aggregate(m1_frame(10, delta=np.arange(10)), "5min")
    assert len(bars) == 2
    assert bars["delta"].tolist() == [0 + 1 + 2 + 3 + 4, 5 + 6 + 7 + 8 + 9]
    assert bars["volume"].tolist() == [10.0, 10.0]
    assert bars["open"].iloc[1] == 105.0 and bars["close"].iloc[0] == 104.0
    assert bars["high"].iloc[0] == 105.0 and bars["low"].iloc[0] == 99.0
    assert bars["close_time"].iloc[0] == T0 + pd.Timedelta("5min")


def test_aggregate_drops_bars_without_any_trade():
    m1 = m1_frame(15)
    m1 = m1[(m1.index < T0 + pd.Timedelta("5min")) | (m1.index >= T0 + pd.Timedelta("10min"))]
    bars = aggregate(m1, "5min")
    assert bars.index.tolist() == [T0, T0 + pd.Timedelta("10min")]


def test_imbalance_is_delta_over_volume():
    bars = bars_frame([1, 2, 3], delta=[5, -5, 0], volume=[10, 10, 10])
    out = add_features(bars, OrderflowConfig(), None, HOUR)
    assert out["imbalance"].tolist() == [0.5, -0.5, 0.0]


def test_cvd_window_sum_known_at_close():
    bars = bars_frame(np.arange(6), delta=[1, 2, 3, 4, 5, 6])
    cfg = OrderflowConfig(cvd_windows=(3,), z_window=3)
    out = add_features(bars, cfg, None, HOUR)
    assert np.isnan(out["cvd_3"].iloc[1])
    assert out["cvd_3"].tolist()[2:] == [6, 9, 12, 15]


def test_cvd_zscore_against_last_window():
    bars = bars_frame(np.arange(6), delta=[1, 2, 3, 4, 5, 6])
    cfg = OrderflowConfig(cvd_windows=(1,), z_window=3)
    out = add_features(bars, cfg, None, HOUR)
    # at bar 4: (5 - mean(3,4,5)) / std(3,4,5, ddof=1) = 1 / 1
    assert out["cvd_z_1"].iloc[4] == pytest.approx(1.0)
    assert np.isnan(out["cvd_z_1"].iloc[1])


def test_features_do_not_use_future_bars():
    delta = [1, 2, 3, 4, 5, 6, 7, 8]
    cfg = OrderflowConfig(cvd_windows=(2,), z_window=4)
    full = add_features(bars_frame(np.arange(8), delta=delta), cfg, None, HOUR)
    head = add_features(bars_frame(np.arange(5), delta=delta[:5]), cfg, None, HOUR)
    for col in ("cvd_2", "cvd_z_2", "div_2", "imbalance"):
        pd.testing.assert_series_equal(full[col].iloc[:5], head[col], check_names=False)


def test_divergence_flags_bearish_and_bullish():
    # running delta = 5 10 15 6 -3 -4 -5 -3 -4
    close = [10, 11, 12, 11, 13, 9, 8, 9, 7]
    delta = [5, 5, 5, -9, -9, -1, -1, 2, -1]
    cfg = OrderflowConfig(cvd_windows=(3,), z_window=3)
    out = add_features(bars_frame(close, delta=delta), cfg, None, HOUR)
    assert out["div_3"].iloc[4] == -1  # new price high (13 > 12), running delta far below 15
    assert out["div_3"].iloc[2] == 0  # not enough history
    assert out["div_3"].iloc[5] == 0  # new price low and new delta low: confirmed
    assert out["div_3"].iloc[8] == 1  # new price low (7 < 8), running delta -4 above its low -5


def test_relative_volume_same_time_of_day_previous_days():
    n = 24 * 4
    vol = np.full(n, 1.0)
    for d, v in enumerate([10, 20, 30, 60]):
        vol[d * 24 + 3] = v
    cfg = OrderflowConfig(cvd_windows=(2,), z_window=3, relvol_days=3)
    out = add_features(bars_frame(np.arange(n), volume=vol), cfg, None, HOUR)
    assert out["relvol"].iloc[3 * 24 + 3] == pytest.approx(60 / 20)
    assert np.isnan(out["relvol"].iloc[2 * 24 + 3])  # fewer than 3 earlier days
    assert out["relvol"].iloc[3 * 24 + 4] == pytest.approx(1.0)


def test_funding_is_last_funding_time_at_or_before_bar_close():
    bars = bars_frame(np.arange(10))
    funding = pd.Series([0.1, 0.2], index=pd.DatetimeIndex([T0, T0 + 8 * HOUR]))
    cfg = OrderflowConfig(cvd_windows=(2,), z_window=3)
    out = add_features(bars, cfg, funding, HOUR)
    assert out["funding"].iloc[0] == 0.1
    assert out["funding"].iloc[6] == 0.1  # closes 07:00
    assert out["funding"].iloc[7] == 0.2  # closes 08:00, the 08:00 rate is known then


def test_targets_start_at_feature_bar_close():
    bars = bars_frame([100, 110, 121, 100, 100, 100, 100, 100])
    out = add_targets(bars, OrderflowConfig(horizons=(1, 3), atr_period=2), HOUR)
    assert out["ret_1"].iloc[0] == pytest.approx(10.0)  # percent, close[0] -> close[1]
    assert out["ret_1"].iloc[1] == pytest.approx(10.0)
    assert out["ret_3"].iloc[0] == pytest.approx(0.0)  # close[0] -> close[3]
    assert out["ret_1"].iloc[2] == pytest.approx((100 / 121 - 1) * 100)
    assert np.isnan(out["ret_3"].iloc[-1]) and np.isnan(out["ret_1"].iloc[-1])


def test_targets_atr_units_use_atr_known_at_feature_close():
    bars = bars_frame([100, 102, 104, 106, 108, 110])  # true range 3 from bar 1 on
    out = add_targets(bars, OrderflowConfig(horizons=(1,), atr_period=2), HOUR)
    assert out["atr_1"].iloc[2] == pytest.approx(2 / 3)
    assert np.isnan(out["atr_1"].iloc[0])


def test_targets_nan_across_time_gap():
    bars = bars_frame(np.arange(100, 106, dtype=float))
    bars = bars.drop(bars.index[3])
    out = add_targets(bars, OrderflowConfig(horizons=(1,), atr_period=2), HOUR)
    assert np.isnan(out["ret_1"].iloc[2])  # next row is two hours later
    assert not np.isnan(out["ret_1"].iloc[3])


def test_bucket_deciles_equal_counts_and_nan_excluded():
    x = np.arange(100, dtype=float)
    x[5] = np.nan
    codes = bucket(x, 10)
    assert codes[5] == -1
    assert set(codes[codes >= 0]) == set(range(10))
    counts = np.bincount(codes[codes >= 0])
    assert counts.max() - counts.min() <= 1
    assert codes[0] == 0 and codes[99] == 9


def test_bucket_discrete_feature_uses_values():
    codes = bucket(np.array([-1, 0, 0, 1, 1, 1, np.nan]), 10)
    assert codes.tolist() == [0, 1, 1, 2, 2, 2, -1]


def test_decile_table_known_values():
    x = np.arange(20, dtype=float)
    y = np.where(x >= 10, 1.0, -1.0)
    tab = decile_table(x, y, 2)
    assert tab["n"].tolist() == [10, 10]
    assert tab["mean"].tolist() == [-1.0, 1.0]
    assert tab["median"].tolist() == [-1.0, 1.0]
    assert tab["hit_rate"].tolist() == [0.0, 1.0]


def test_decile_table_tstat_sign_and_overlap_correction():
    rng = np.random.default_rng(0)
    y = rng.normal(0, 1, 400)
    x = np.arange(400, dtype=float)
    y[x >= 200] += 5
    y[x < 200] -= 5
    tab = decile_table(x, y, 2)
    assert tab["t"].iloc[1] > 10 and tab["t"].iloc[0] < 0
    tab3 = decile_table(x, y, 2, overlap=4)
    assert tab3["t"].iloc[1] == pytest.approx(tab["t"].iloc[1] / 2)


def test_spread_top_minus_bottom():
    x = np.arange(20, dtype=float)
    y = np.where(x >= 10, 3.0, 1.0)
    assert spread(bucket(x, 2), y) == pytest.approx(2.0)
    assert spread(bucket(x, 10), -y) == pytest.approx(-2.0)


def test_half_spreads_use_whole_sample_buckets():
    x = np.arange(40, dtype=float)
    y = np.where(x >= 20, 1.0, -1.0)
    codes = bucket(x, 2)
    a, b = half_spreads(codes, y, np.arange(40) < 20)
    assert np.isnan(a) and np.isnan(b)  # each half holds only one end bucket
    x2 = np.tile(np.arange(20, dtype=float), 2)
    y2 = np.where(x2 >= 10, 1.0, -1.0)
    a, b = half_spreads(bucket(x2, 2), y2, np.arange(40) < 20)
    assert a == pytest.approx(2.0) and b == pytest.approx(2.0)


def test_shuffle_p95_is_deterministic_and_small_for_noise():
    rng = np.random.default_rng(1)
    codes = bucket(rng.normal(size=2000), 10)
    y = rng.normal(size=2000)
    a = shuffle_p95(codes, y, 200, seed=7)
    assert a == shuffle_p95(codes, y, 200, seed=7)
    assert a != shuffle_p95(codes, y, 200, seed=8)
    assert 0 < a < 0.4


def test_real_effect_beats_shuffle_p95():
    x = np.arange(2000, dtype=float)
    y = x / 2000 + np.random.default_rng(3).normal(0, 0.1, 2000)
    codes = bucket(x, 10)
    assert spread(codes, y) > shuffle_p95(codes, y, 200, seed=1)


def test_shift_p95_deterministic_and_wider_than_shuffle_for_persistent_series():
    from backtester.analytics.orderflow import shift_p95

    rng = np.random.default_rng(5)
    x = np.cumsum(rng.normal(size=3000))  # persistent feature
    y = np.cumsum(rng.normal(size=3000))  # persistent target (overlapping returns, trends)
    codes = bucket(x, 10)
    a = shift_p95(codes, y, 200, seed=3)
    assert a == shift_p95(codes, y, 200, seed=3)
    assert a > 3 * shuffle_p95(codes, y, 200, seed=3)


def test_shift_p95_keeps_codes_in_order():
    from backtester.analytics.orderflow import shift_p95

    codes = bucket(np.arange(100, dtype=float), 2)
    y = np.where(codes == 1, 1.0, 0.0)
    # every circular shift of a perfectly sorted feature still pairs the halves mostly
    # with themselves or each other: the spread is bounded by the real spread
    assert 0 <= shift_p95(codes, y, 50, seed=1) <= 1.0
