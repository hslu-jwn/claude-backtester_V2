"""Empirical-Bayes prior per family type on the ledger's est / se (review A change 8; file 10 › C)."""

import importlib.util

import numpy as np

spec = importlib.util.spec_from_file_location("ledger_prior", "research/screens/ledger_prior.py")
lp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lp)


def test_marginal_density_integrates_to_one():
    t = np.linspace(-30, 30, 60001)
    for pi, s in ((0.0, 1.0), (0.3, 2.0), (1.0, 0.5)):
        assert abs(np.trapezoid(lp.marginal(t, pi, s), t) - 1) < 1e-4


def test_fit_recovers_null_and_planted_slab():
    rng = np.random.default_rng(1)
    null = rng.normal(size=2000)
    assert lp.fit(null)[0] < 0.08
    n = 3000
    real = rng.random(n) < 0.3
    delta = np.where(real, np.abs(rng.normal(0, 2.0, n)), 0.0)
    pi, s = lp.fit(delta + rng.normal(size=n))
    assert abs(pi - 0.3) < 0.08 and abs(s - 2.0) < 0.6


def test_beta_hyperprior_pulls_small_type_to_the_pooled_pi():
    t = np.array([3.0, 2.5])  # two strong rows alone would fit pi near 1
    free = lp.fit(t)[0]
    pulled = lp.fit(t, prior_mean=0.1, strength=20)[0]
    assert pulled < free and pulled < 0.5


def test_posterior_probability_is_bounded_and_rises_with_t():
    p = lp.posterior_positive(np.array([-2.0, 0.0, 2.0, 4.0]), 0.2, 1.5)
    assert np.all((p >= 0) & (p <= 1)) and np.all(np.diff(p) > 0)


def test_rows_use_gross_looked_rows_and_one_per_dup_group():
    rows = [
        {
            "id": "A",
            "est": "4",
            "se": "2",
            "est_basis": "gross",
            "est_sample": "dev",
            "type": "a",
            "dup_group": "G",
        },
        {
            "id": "B",
            "est": "9",
            "se": "1",
            "est_basis": "gross",
            "est_sample": "dev",
            "type": "a",
            "dup_group": "G",
        },
        {
            "id": "C",
            "est": "1",
            "se": "1",
            "est_basis": "net",
            "est_sample": "dev",
            "type": "a",
            "dup_group": "",
        },
        {
            "id": "D",
            "est": "1",
            "se": "1",
            "est_basis": "gross",
            "est_sample": "expected",
            "type": "a",
            "dup_group": "",
        },
        {
            "id": "E",
            "est": "-3",
            "se": "1",
            "est_basis": "gross",
            "est_sample": "presample",
            "type": "e",
            "dup_group": "",
        },
        {
            "id": "F",
            "est": "",
            "se": "",
            "est_basis": "",
            "est_sample": "",
            "type": "b",
            "dup_group": "",
        },
    ]
    got = lp.observations(rows)
    assert got == {
        "a": [("A", 2.0)],
        "e": [("E", -3.0)],
    }  # first row of group G kept; net / expected / blank dropped
