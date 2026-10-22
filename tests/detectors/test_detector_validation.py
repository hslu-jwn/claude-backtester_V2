"""Detector review findings #2-3: config and ATR validation."""

import pytest
from conftest import build_series

from backtester.detectors.atr import Atr, true_range
from backtester.detectors.sweep import SweepConfig


def test_sweep_rejects_nan_tolerance():
    with pytest.raises(ValueError, match="equal_tolerance_atr"):
        SweepConfig(equal_tolerance_atr=float("nan"))


@pytest.mark.parametrize("field", ["lookback_swings", "bos_within", "atr_period", "cancel_closes"])
@pytest.mark.parametrize("value", [1.5, float("nan"), float("inf"), -float("inf"), 2.0])
def test_sweep_rejects_noninteger_counters(field, value):
    # Even integral-valued floats cannot be used as slice/range counters.
    with pytest.raises(TypeError, match=field):
        SweepConfig(**{field: value})


@pytest.mark.parametrize("tolerance", [None, 0.0, 0.5, float("inf")])
def test_sweep_retains_supported_tolerance_and_zero_bos_window(tolerance):
    config = SweepConfig(equal_tolerance_atr=tolerance, bos_within=0)
    assert config.equal_tolerance_atr == tolerance


@pytest.mark.parametrize("field", ["open", "high", "low", "close"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("period", [1, 3])
def test_atr_rejects_nonfinite_input_without_changing_state(field, value, period):
    series = build_series([(10, 11, 9, 10), (10, 12, 9, 11), (11, 13, 10, 12)])
    atr = Atr(period)
    atr.update(series.view(0))
    candle = series.view(1).current
    original = getattr(candle, field)
    # Simulate corrupt input past Candle's constructor to test ATR's own boundary.
    object.__setattr__(candle, field, value)
    before = (atr.current, atr._prev_close, atr._tr_sum, tuple(atr._values))
    with pytest.raises(ValueError, match="finite"):
        atr.update(series.view(1))
    assert (atr.current, atr._prev_close, atr._tr_sum, tuple(atr._values)) == before
    object.__setattr__(candle, field, original)
    atr.update(series.view(1))
    atr.update(series.view(2))
    expected = Atr(period)
    for i in range(3):
        expected.update(series.view(i))
    assert atr.current == expected.current


@pytest.mark.parametrize("previous", [float("nan"), float("inf"), -float("inf")])
def test_true_range_rejects_nonfinite_previous_close(previous):
    candle = build_series([(10, 11, 9, 10)]).view(0).current
    with pytest.raises(ValueError, match="finite"):
        true_range(candle, previous)


def test_atr_rejects_nonfinite_true_range_without_changing_state():
    # Finite prices can still overflow when their range is calculated.
    series = build_series([(0, 1e308, -1e308, 0)])
    atr = Atr(1)
    with pytest.raises(ValueError, match="finite"):
        atr.update(series.view(0))
    assert atr.current is None and atr._prev_close is None and atr._tr_sum == 0
