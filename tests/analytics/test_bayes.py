"""Spec: research-runner.md > Bayesian view.

Test-case list (before code): closed-form Beta(2,2) and one-sided BF; symmetric
break-even list; prior shrinkage; interval narrowing; known normal update;
overlap lowers effective n; seeded identical/clearly-better A/B; KL planning
10:1 vs card 20:1; scratches; empty/one-sign/singleton/constant data; nonfinite
R and invalid intervals/config; extreme evidence stays JSON-safe; flag boundary.
"""

import json
import math
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.analytics.bayes import BayesConfig, compare, report, trades_needed, warning_flags


def trades(values, overlap=False):
    start = datetime(2020, 1, 1, tzinfo=UTC)
    return [
        SimpleNamespace(
            r_net=r,
            entry_time=start + timedelta(days=0 if overlap else i),
            exit_time=start + timedelta(days=0 if overlap else i, hours=1),
        )
        for i, r in enumerate(values)
    ]


def test_beta_closed_form_and_bf():
    result = report(trades([1, -1]), BayesConfig(strong_strength=2))
    flat = result["win_rate"]["flat"]
    assert (flat["alpha"], flat["beta"]) == (2, 2)
    assert flat["mean"] == 0.5
    assert flat["p_above"] == pytest.approx(0.5)
    lo, hi = flat["interval"]
    assert 3 * lo**2 - 2 * lo**3 == pytest.approx(0.025)
    assert 3 * hi**2 - 2 * hi**3 == pytest.approx(0.975)
    assert result["evidence"]["bayes_factor"] == pytest.approx(2 / 3)
    assert result["evidence"]["posterior_odds"] == pytest.approx(2 / 150)


def test_priors_and_sample_size():
    values = [1] * 14 + [-1] * 6
    small = report(trades(values))
    rates = small["win_rate"]
    assert rates["flat"]["mean"] > rates["weak"]["mean"] > rates["strong"]["mean"] > 0.5
    big = report(trades(values * 10))
    for key in rates:
        assert (
            big["win_rate"][key]["interval"][1] - big["win_rate"][key]["interval"][0]
            < rates[key]["interval"][1] - rates[key]["interval"][0]
        )


def test_mean_known_update_and_overlap():
    independent = report(trades([3, -1]))
    mean = independent["mean_r"]
    variance = 1 / (1 / 0.075**2 + 2 / 8)
    assert mean["mean"] == pytest.approx(variance * 2 / 8)
    assert mean["sd"] == pytest.approx(math.sqrt(variance))
    assert independent["n"] == independent["effective_n"] == 2
    overlapping = report(trades([3, -1], overlap=True))
    assert overlapping["n"] == 2 and overlapping["effective_n"] == 1
    assert overlapping["mean_r"]["sd"] > mean["sd"]
    assert overlapping["mean_r"]["mean"] < mean["mean"]


def test_ab_seeded_and_clear_difference():
    a = trades([1, -1] * 100)
    same = compare(a, a)
    assert same == compare(a, a)
    assert same["p_mean_b_gt_a"] == pytest.approx(0.5, abs=0.015)
    assert same["p_win_b_gt_a"] == pytest.approx(0.5, abs=0.015)
    better = compare(a, trades([1] * 180 + [-1] * 20))
    assert better["p_mean_b_gt_a"] > 0.99
    assert better["p_win_b_gt_a"] > 0.99


def test_planning():
    assert trades_needed(0.55, 0.5) == 1241
    assert trades_needed(0.55, 0.5, BayesConfig(target_odds=20)) == 1380
    assert trades_needed(0.5, 0.5) is None
    assert trades_needed(0.4, 0.5) is None


@pytest.mark.parametrize("values", [[], [1], [-1, -2], [1, 2], [0, 0]])
def test_missing_payoffs(values):
    r = report(trades(values))
    assert r["p_star"] is None and r["win_rate"] == {}
    assert r["evidence"]["reason"]
    json.dumps(r, allow_nan=False)


def test_scratches_and_degenerate_variance():
    r = report(trades([1, -1, 0]))
    assert r["wins"] == 1 and r["n"] == 3 and r["p_star"] == 0.5
    assert r["win_rate"]["flat"]["beta"] == 3
    for values in ([1], [1, 1], []):
        assert report(trades(values))["mean_r"]["p_positive"] is None
    assert compare([], [])["p_mean_b_gt_a"] is None


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_bad_r(value):
    with pytest.raises(ValueError, match="finite"):
        report(trades([value]))


def test_invalid_interval():
    t = trades([1])[0]
    t.exit_time = t.entry_time - timedelta(seconds=1)
    with pytest.raises(ValueError, match="interval"):
        report([t])


@pytest.mark.parametrize(
    "settings",
    [
        {"strong_strength": 0},
        {"mean_prior_sd": float("nan")},
        {"draws": 0},
        {"weak_threshold": 2},
        {"prior_odds": -1},
        {"target_odds": 0},
        {"draws": 1.5},
    ],
)
def test_invalid_config(settings):
    with pytest.raises(ValueError):
        BayesConfig(**settings)


def test_extreme_and_flags():
    r = report(trades([1] * 10000 + [-1]))
    assert r["evidence"]["log_bayes_factor"] > 1000
    json.dumps(r, allow_nan=False)
    assert warning_flags({"mean_r": {"p_positive": 0.899}}) == ["bayes_weak"]
    assert warning_flags({"mean_r": {"p_positive": 0.9}}) == []
    assert warning_flags({"mean_r": {"p_positive": None}}) == []
