"""Spec: risk-management.md > Monte Carlo report, V2.4d item 4."""

import numpy as np
import pytest

from backtester.risk.bootstrap import stationary_orders
from backtester.risk.monte_carlo import MonteCarloConfig, reshuffle_orders


def test_default_reproducibility_replacement_and_range():
    config = MonteCarloConfig(runs=100, seed=7)
    assert config.sampling == "block_bootstrap" and config.block_days == 5
    a = reshuffle_orders(20, config)
    assert np.array_equal(a, reshuffle_orders(20, config))
    assert a.shape == (100, 20) and a.min() >= 0 and a.max() < 20
    assert any(len(set(row)) < 20 for row in a)
    assert not np.array_equal(a, reshuffle_orders(20, MonteCarloConfig(runs=100, seed=8)))


def test_permutation_exact_legacy_stream():
    config = MonteCarloConfig(runs=15, seed=19, sampling="permutation")
    rng = np.random.default_rng(19)
    expected = np.array([rng.permutation(23) for _ in range(15)])
    assert np.array_equal(reshuffle_orders(23, config), expected)


def test_empty_and_single_day():
    assert reshuffle_orders(0, MonteCarloConfig(runs=3)).shape == (3, 0)
    assert np.array_equal(reshuffle_orders(1, MonteCarloConfig(runs=3)), np.zeros((3, 1)))


def test_can_repeat_losses_and_exceed_historic_drawdown():
    from backtester.risk.monte_carlo import Day, _one_run

    days = [Day(np.array([r]), ()) for r in (-1.0, 2.0, -1.0, 2.0)]
    config = MonteCarloConfig(runs=1000, block_days=1, risk_levels=(0.01,))
    actual = _one_run(days, np.arange(4), 0.01, config)["max_dd"]
    worst = max(_one_run(days, row, 0.01, config)["max_dd"] for row in reshuffle_orders(4, config))
    assert worst == pytest.approx(1 - 0.99**4)
    assert worst > actual


@pytest.mark.parametrize("mean", [1.0, 2.0, 5.0, 12.0])
def test_geometric_blocks_uniform_starts_and_wrapping(mean):
    # A random restart can accidentally choose the adjacent index (probability 1/n).
    # Correct that before estimating geometric block length; avoid censoring at row ends.
    n = 31
    a = stationary_orders(n, 8000, 80, np.random.default_rng(42), mean)
    adjacent = a[:, 1:] == (a[:, :-1] + 1) % n
    restart = (1 - adjacent.mean()) / (1 - 1 / n)
    assert 1 / restart == pytest.approx(mean, rel=0.025)
    assert np.any((a[:, :-1] == n - 1) & (a[:, 1:] == 0))
    frequencies = np.bincount(a[:, 0], minlength=n) / len(a)
    assert np.max(np.abs(frequencies - 1 / n)) < 0.009


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sampling": "unknown"},
        {"block_days": 0},
        {"block_days": 0.5},
        {"block_days": float("nan")},
        {"block_days": float("inf")},
    ],
)
def test_invalid_config(kwargs):
    with pytest.raises(ValueError):
        MonteCarloConfig(**kwargs)


def test_card_sweep_account_and_adaptive_share_bootstrap_orders():
    from dataclasses import replace

    from backtester.risk import monte_carlo as mc
    from backtester.risk import prop_card as pc
    from backtester.tools import risk_sweep
    from tests.risk.test_monte_carlo import one_per_day

    trades, start, end = one_per_day([2.0, -1.0, -1.0, 2.0, 0.5] * 40)
    config = MonteCarloConfig(runs=13, seed=7, risk_levels=(0.01,))
    days = mc.build_days(trades, start, end)
    orders = reshuffle_orders(len(days), config)
    fixed = mc.ftmo_by_risk(days, orders, config)[0.01]
    output = mc.run_monte_carlo(trades, start, end, config)["risks"][0.01]
    assert output["ftmo"] == fixed
    # Fan paths use the same entire Days, preserving the intra-day trades.
    assert (
        output["fan"]["paths"][0] == mc._one_run(days, orders[0], 0.01, config)["day_bal"].tolist()
    )
    preset = pc.FirmPreset("test", config)
    card = pc.compute_card(trades, start, end, preset, pc.PropCardConfig(min_days=1, min_trades=1))
    adaptive = mc.ftmo_by_risk(days, orders, replace(config, adaptive=preset.adaptive))[0.01]
    sweep = risk_sweep.evaluate(
        trades,
        start,
        end,
        risk_sweep.SweepConfig(runs=13, seed=7),
        [risk_sweep.Variant(0.01, None, None)],
        workers=1,
    )[0]
    for key in ("attempts", "fail_daily", "fail_max", "pass_probability", "median_days_to_pass"):
        assert card["rows"][0][key] == sweep[key] == fixed[key]
        assert card["adaptive_rows"][0][key] == adaptive[key]
