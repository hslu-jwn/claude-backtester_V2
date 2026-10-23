"""Cases: exact centred max/+1; synchronous indices; planted edge; seeded noise
calibration; reproducibility; empty/short/nonfinite matrices and invalid config.
"""

import numpy as np
import pytest

from backtester.analytics import best_of_n


def test_sampler_is_shared_with_risk():
    from backtester.analytics.bootstrap import stationary_orders
    from backtester.risk.bootstrap import stationary_orders as risk_orders

    assert best_of_n.stationary_orders is risk_orders is stationary_orders


def test_exact_shared_indices(monkeypatch):
    orders = np.array([[0, 0], [1, 1], [0, 1]])

    def sample(n_days, runs, length, rng, block_days):
        assert (n_days, runs, length, block_days) == (2, 3, 2, 5)
        return orders

    monkeypatch.setattr(best_of_n, "stationary_orders", sample)
    # Centred columns [-1, 1], [1, -1]; observed max mean = 1.
    result = best_of_n.reality_check([[0, 2], [2, 0]], best_of_n.RealityCheckConfig(boots=3))
    assert result["observed_max_mean"] == 1
    assert result["p_value"] == 3 / 4


def test_edge_noise_and_reproducibility():
    rng = np.random.default_rng(44)
    matrix = rng.normal(size=(600, 6))
    matrix[:, 0] += 1
    cfg = best_of_n.RealityCheckConfig(boots=199)
    result = best_of_n.reality_check(matrix, cfg)
    assert result["p_value"] <= 0.01
    assert result == best_of_n.reality_check(matrix, cfg)
    ps = [best_of_n.reality_check(rng.normal(size=(250, 4)), cfg)["p_value"] for _ in range(30)]
    assert 0.25 < np.mean(ps) < 0.75
    assert sum(p <= 0.05 for p in ps) <= 6


def test_invalid_and_unavailable():
    for matrix in (np.empty((0, 2)), np.zeros((1, 2)), np.empty((4, 0))):
        result = best_of_n.reality_check(matrix)
        assert result["p_value"] is None and result["reason"]
    for matrix in ([1, 2], [[np.nan]], [[np.inf]]):
        with pytest.raises(ValueError):
            best_of_n.reality_check(matrix)
    with pytest.raises(ValueError):
        best_of_n.RealityCheckConfig(boots=0)
