"""Cases: symmetric mean vs t, exact small-n t, seed reproducibility, constant/empty/
singleton, invalid config/nonfinite input, balanced log PF, no wins/losses, sparse PF
replicates. Spec: research-runner.md > Skill vs trend, and bounds.
"""

import numpy as np
import pytest

from backtester.analytics.bounds import BoundsConfig, log_pf_bounds, mean_bounds


def test_symmetric_mean_and_seed():
    x = np.random.default_rng(8).normal(size=2000)
    a = mean_bounds(x)
    assert a == mean_bounds(x)
    assert a["lower95_bca"] == pytest.approx(a["lower95_t"], abs=0.008)
    assert a["lower90_bca"] > a["lower95_bca"]


def test_exact_student_t():
    # n=2, mean=2, SE=1; one-sided t(.95, 1) = 6.313751514675.
    assert mean_bounds([1, 3])["lower95_t"] == pytest.approx(2 - 6.313751514675)


@pytest.mark.parametrize("x", [[], [2]])
def test_too_short(x):
    assert mean_bounds(x)["lower95_bca"] is None


def test_constant():
    a = mean_bounds([2] * 10)
    assert a["lower95_bca"] == a["lower95_t"] == 2


@pytest.mark.parametrize("x", [[float("nan")], [float("inf")]])
def test_nonfinite(x):
    with pytest.raises(ValueError):
        mean_bounds(x)


def test_config():
    assert BoundsConfig().boots == 5000
    with pytest.raises(ValueError):
        BoundsConfig(boots=0)


def test_log_pf_balanced():
    a = log_pf_bounds([1, -1] * 100)
    assert a["estimate"] == 0
    assert a["lower95_bca"] < a["lower90_bca"] < 0
    assert a == log_pf_bounds([1, -1] * 100)


@pytest.mark.parametrize("x", [[], [0, 0], [1, 2], [-1, -2]])
def test_undefined_pf(x):
    assert log_pf_bounds(x)["estimate"] is None


def test_sparse_pf_not_conditioned_on_finite_replicates():
    a = log_pf_bounds([1, -1])
    assert a["estimate"] == 0
    assert a["lower95_bca"] is None
    assert a["reason"]
