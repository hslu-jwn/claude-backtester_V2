"""T-22 simulation tests for our estimators (CF ch.7, appendix B). Spec: research-runner.md > Causal simulation tests."""

import numpy as np
import pytest

from backtester.analytics.causal_sim import collider, confounded_mediator, fork, ols, true_effect

GATE = 3.0  # development t gate (research-runner M4)


def t_of(data, y, xs, name):
    return ols(data[y], [data[x] for x in xs])["t"][xs.index(name)]


def test_fork_x_alone_is_a_false_discovery_and_the_confounder_control_removes_it():
    d = fork(seed=0)  # Z -> X, Z -> Y; X has no effect on Y
    assert abs(t_of(d, "y", ["x"], "x")) >= GATE
    assert abs(t_of(d, "y", ["x", "z"], "x")) < GATE


def test_collider_control_creates_a_false_discovery():
    d = collider(seed=0)  # X -> Z <- Y; X and Y independent
    assert abs(t_of(d, "y", ["x"], "x")) < GATE
    assert abs(t_of(d, "y", ["x", "z"], "x")) >= GATE
    assert np.corrcoef(d["x"], d["y"])[0, 1] == pytest.approx(0, abs=0.05)


def test_confounded_mediator_control_misleads_and_no_control_recovers_the_total_effect():
    d = confounded_mediator(seed=0, effect=0.0)  # X -> Z -> Y with Z -> Y zero, W -> Z, W -> Y
    assert abs(t_of(d, "y", ["x"], "x")) < GATE  # true total effect 0
    assert (
        abs(t_of(d, "y", ["x", "z"], "x")) >= GATE
    )  # controlling the mediator opens X -> Z <- W -> Y


def test_true_effect_is_recovered_inside_its_interval():
    d = true_effect(seed=0, beta=0.1)
    r = ols(d["y"], [d["x"]])
    assert abs(r["beta"][0] - 0.1) < 2.5 * r["se"][0]
    assert r["t"][0] >= GATE


def test_ols_matches_a_hand_case():
    x = np.array([0.0, 1.0, 2.0, 3.0])
    y = 1.0 + 2.0 * x
    r = ols(y, [x])
    assert r["beta"][0] == pytest.approx(2.0)
    assert r["intercept"] == pytest.approx(1.0)


def test_generators_are_reproducible_and_sized():
    a, b = fork(seed=3, n=500), fork(seed=3, n=500)
    assert len(a["x"]) == 500 and np.array_equal(a["y"], b["y"])


@pytest.mark.parametrize(
    "y, xs",
    [
        (np.ones(3), [np.arange(3.0)]),  # n must exceed regressors + 2
        (np.arange(10.0), [np.arange(9.0)]),  # length mismatch
        (np.array([1.0, np.nan, 3, 4, 5, 6]), [np.arange(6.0)]),  # not finite
        (np.arange(10.0), [np.ones(10)]),  # constant regressor: collinear with the intercept
    ],
)
def test_bad_inputs_raise(y, xs):
    with pytest.raises(ValueError):
        ols(y, xs)
