"""Critical cases before implementation; Spec: risk-management.md > Monte Carlo report."""

from dataclasses import replace

import numpy as np
import pytest

from backtester.risk.bootstrap import stationary_orders
from backtester.risk.drawdown_bounds import DrawdownBoundsConfig, drawdown_bounds, max_drawdown_r

FAST = DrawdownBoundsConfig(outer=12, inner=40, horizon_days=9)


def test_known_drawdown_and_initial_peak():
    assert max_drawdown_r(np.array([[2.0, -3.0, -2.0, 4.0, -1.0]])) == pytest.approx([5.0])
    assert max_drawdown_r(np.array([[-2.0, -1.0, 4.0]])) == pytest.approx([3.0])


def test_nested_reference_loop_and_scaling():
    data = np.array([2.0, -3.0, -2.0, 4.0, -1.0])
    config = replace(FAST, outer=4, inner=8)
    rng = np.random.default_rng(config.seed)
    histories = stationary_orders(len(data), config.outer, len(data), rng, config.block_days)
    quantiles = []
    for indices in histories:
        future = stationary_orders(
            len(data), config.inner, config.horizon_days, rng, config.block_days
        )
        dds = []
        for path in data[indices][future]:
            equity = peak = dd = 0.0
            for r in path:
                equity += r
                peak = max(peak, equity)
                dd = max(dd, peak - equity)
            dds.append(dd)
        quantiles.append(np.quantile(dds, config.quantiles))
    expected = np.quantile(quantiles, [0.5, 0.9, 0.95], axis=0).T
    result = drawdown_bounds(data, config)
    assert result == drawdown_bounds(data, config)
    for row, values in zip(result["rows"], expected, strict=True):
        assert list(row["bounds_r"].values()) == pytest.approx(values)
        for risk in config.risk_levels:
            assert list(row["bounds_pct"][str(risk)].values()) == pytest.approx(values * risk * 100)


def test_monotone_in_quantile_and_confidence():
    rows = drawdown_bounds([2.0, -3.0, -2.0, 4.0, -1.0], FAST)["rows"]
    values = np.array([list(row["bounds_r"].values()) for row in rows])
    assert np.all(np.diff(values, axis=0) >= 0)
    assert np.all(np.diff(values, axis=1) >= 0)


@pytest.mark.parametrize("data", [[1.0, 2.0, 3.0], [0.0, 0.0], [4.0]])
def test_nonnegative_zero_drawdown(data):
    assert all(
        all(v == 0 for v in row["bounds_r"].values()) for row in drawdown_bounds(data, FAST)["rows"]
    )


def test_single_losing_day_and_empty():
    for row in drawdown_bounds([-1.0], FAST)["rows"]:
        assert list(row["bounds_r"].values()) == [9.0, 9.0, 9.0]
    assert drawdown_bounds([], FAST)["status"] == "unavailable"


@pytest.mark.parametrize("data", [[float("nan")], [float("inf")], [[1, 2]]])
def test_invalid_data(data):
    with pytest.raises(ValueError):
        drawdown_bounds(data, FAST)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"outer": 0},
        {"inner": 0},
        {"horizon_days": 0},
        {"outer": 1.5},
        {"block_days": 0.5},
        {"block_days": float("nan")},
        {"quantiles": (1.1,)},
        {"risk_levels": (0.0,)},
    ],
)
def test_invalid_config(kwargs):
    with pytest.raises(ValueError):
        replace(FAST, **kwargs)
