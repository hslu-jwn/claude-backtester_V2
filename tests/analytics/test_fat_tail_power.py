"""T-24 fat-tail power check. Spec: research-runner.md > Fat-tail power check (T-24)."""

import numpy as np
import pytest

from backtester.analytics.fat_tail_power import PowerConfig, draw, power_check


def test_every_scenario_has_the_requested_sd():
    cfg = PowerConfig(sims=400, seed=1)
    for name in cfg.scenarios:
        x = draw(name, n=500, sd=80.0, cfg=cfg)
        assert x.shape == (400, 500)
        assert abs(x.std() / 80.0 - 1) < 0.08, name


def test_gaussian_power_is_half_when_the_expected_t_equals_the_gate():
    n, sd = 100, 50.0
    edge = 3.0 * sd / np.sqrt(n)  # expected t = 3
    r = power_check(n, edge, sd, PowerConfig(sims=8000, seed=2, scenarios=("gaussian",)))
    assert abs(r["gaussian"]["power"] - 0.5) < 0.04


def test_zero_edge_false_pass_is_small_under_gaussian():
    r = power_check(100, 0.0, 50.0, PowerConfig(sims=8000, seed=3, scenarios=("gaussian",)))
    assert r["gaussian"]["false_pass"] < 0.01
    assert r["gaussian"]["power"] == r["gaussian"]["false_pass"]  # edge 0: power is the false pass


def test_seed_makes_it_reproducible():
    cfg = PowerConfig(sims=500, seed=7)
    assert power_check(60, 10.0, 40.0, cfg) == power_check(60, 10.0, 40.0, cfg)


def test_two_sided_gate_catches_a_negative_edge_one_sided_does_not():
    n, sd = 100, 50.0
    edge = -4.0 * sd / np.sqrt(n)
    one = power_check(n, edge, sd, PowerConfig(sims=2000, seed=4, scenarios=("gaussian",)))
    two = power_check(
        n,
        edge,
        sd,
        PowerConfig(sims=2000, seed=4, scenarios=("gaussian",), two_sided=True, threshold=3.3),
    )
    assert one["gaussian"]["power"] < 0.01
    assert two["gaussian"]["power"] > 0.6


def test_verdict_parks_when_any_scenario_is_below_the_floor():
    n, sd = 60, 100.0
    weak = power_check(n, 5.0, sd, PowerConfig(sims=2000, seed=5))
    assert weak["verdict"] == "PARK"
    strong = power_check(n, 60.0, sd, PowerConfig(sims=2000, seed=5))
    assert strong["verdict"] == "OK"
    assert strong["min_power"] == min(strong[s]["power"] for s in PowerConfig().scenarios)


def test_fat_tails_change_power_at_a_moderate_edge():
    """Student-t(3) at the same sd puts more mass near zero: power differs from the Gaussian one."""
    n, sd = 40, 100.0
    edge = 2.5 * sd / np.sqrt(n)
    r = power_check(n, edge, sd, PowerConfig(sims=6000, seed=6))
    assert abs(r["student_t3"]["power"] - r["gaussian"]["power"]) > 0.02


def test_rare_loss_inflates_false_passes_in_short_samples_and_is_flagged():
    r = power_check(40, 0.0, 100.0, PowerConfig(sims=20000, seed=8))
    assert r["rare_loss"]["false_pass"] > 3 * r["gaussian"]["false_pass"]
    assert "rare_loss" in r["false_pass_flags"]
    assert "rare_gain" not in r["false_pass_flags"]  # the mirror deflates false passes


def test_jump_scenarios_are_zero_mean():
    cfg = PowerConfig(sims=2000, seed=9)
    for name in ("rare_loss", "rare_gain"):
        assert abs(draw(name, 400, 50.0, cfg).mean()) < 0.5


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n": 2, "edge": 1.0, "sd": 1.0},
        {"n": 50, "edge": 1.0, "sd": 0.0},
        {"n": 50, "edge": 1.0, "sd": -1.0},
        {"n": 50, "edge": float("nan"), "sd": 1.0},
    ],
)
def test_bad_inputs_raise(kwargs):
    with pytest.raises(ValueError):
        power_check(**kwargs, cfg=PowerConfig(sims=10))


def test_bad_config_raises():
    with pytest.raises(ValueError):
        PowerConfig(sims=0)
    with pytest.raises(ValueError):
        PowerConfig(scenarios=("cauchy",))
    with pytest.raises(ValueError):
        PowerConfig(garch_alpha=0.2, garch_beta=0.85)  # alpha + beta >= 1: no stationary variance
    with pytest.raises(ValueError):
        PowerConfig(jump_prob=0.0)
