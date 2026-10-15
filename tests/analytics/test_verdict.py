"""Monte Carlo verdict: six checks, EDGE / WEAK / NO EDGE.
Spec: risk-management.md > Monte Carlo report > Verdict (ROADMAP 12.7)."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from backtester.analytics.verdict import (
    CHECK_KEYS,
    VerdictConfig,
    VerdictInputs,
    evaluate,
    t_statistic,
)

GOOD = VerdictInputs(
    mean_r=0.1, t=3.0, percentile=99.0, half_first_net=5.0, half_second_net=4.0,
    stressed_net=6.0, net_without_best=7.0, fill_median=8.0,
)  # fmt: skip


def check(verdict, key):
    return next(c for c in verdict.checks if c.key == key)


def test_all_pass_is_edge():
    v = evaluate(GOOD)
    assert v.label == "EDGE" and v.failed == ()
    assert [c.key for c in v.checks] == list(CHECK_KEYS) and len(CHECK_KEYS) == 6
    assert all(c.passed and c.available for c in v.checks)


@pytest.mark.parametrize(
    ("change", "key"),
    [
        ({"t": 1.99}, "t_stat"),
        ({"mean_r": 0.0}, "t_stat"),
        ({"mean_r": -0.1, "t": 3.0}, "t_stat"),
        ({"t": None}, "t_stat"),
        ({"percentile": 94.9}, "random_entries"),
        ({"half_first_net": 0.0}, "halves"),
        ({"half_second_net": -1.0}, "halves"),
        ({"stressed_net": 0.0}, "cost_stress"),
        ({"net_without_best": -0.1}, "without_best"),
        ({"fill_median": 0.0}, "random_fills"),
    ],
)
def test_each_single_failure_is_weak(change, key):
    v = evaluate(replace(GOOD, **change))
    assert v.label == "WEAK" and v.failed == (key,)
    assert not check(v, key).passed


def test_two_failures_weak_three_no_edge():
    assert evaluate(replace(GOOD, t=1.0, fill_median=-1.0)).label == "WEAK"
    v = evaluate(replace(GOOD, t=1.0, fill_median=-1.0, stressed_net=-2.0))
    assert v.label == "NO EDGE" and len(v.failed) == 3


def test_threshold_equality_t_and_percentile_pass():
    v = evaluate(replace(GOOD, t=2.0, percentile=95.0))
    assert v.label == "EDGE"
    assert check(v, "t_stat").threshold == 2.0
    assert check(v, "random_entries").threshold == 95.0


def test_net_checks_need_strictly_more_than_zero():
    v = evaluate(replace(GOOD, stressed_net=0.0, net_without_best=0.0, fill_median=0.0))
    assert set(v.failed) == {"cost_stress", "without_best", "random_fills"}
    assert v.label == "NO EDGE"


def test_not_available_check_is_listed_and_not_failed():
    v = evaluate(replace(GOOD, percentile=None))
    c = check(v, "random_entries")
    assert not c.available and not c.passed and c.value is None
    assert v.label == "EDGE" and v.failed == ()
    assert "n/a" in v.reason


def test_not_available_does_not_hide_other_failures():
    assert evaluate(replace(GOOD, percentile=None, t=1.0)).label == "WEAK"
    v = evaluate(replace(GOOD, percentile=None, t=1.0, stressed_net=-1, fill_median=-1))
    assert v.label == "NO EDGE"


def test_check_values_and_halves_value_is_the_weaker_half():
    v = evaluate(GOOD)
    assert check(v, "t_stat").value == 3.0
    assert check(v, "halves").value == 4.0
    assert check(v, "cost_stress").value == 6.0


def test_config_thresholds_are_used():
    cfg = VerdictConfig(t_min=3.5, percentile_min=99.5)
    v = evaluate(GOOD, cfg)
    assert set(v.failed) == {"t_stat", "random_entries"}
    with pytest.raises(ValueError):
        VerdictConfig(percentile_min=101.0)


def test_reason_names_failed_checks_and_is_one_line():
    v = evaluate(replace(GOOD, t=1.0))
    assert "\n" not in v.reason and "t" in v.reason.lower()
    assert "all" in evaluate(GOOD).reason.lower()


def test_no_trades_is_no_edge():
    v = evaluate(VerdictInputs(None, None, None, 0.0, 0.0, 0.0, 0.0, 0.0))
    assert v.label == "NO EDGE"


def test_t_statistic():
    assert t_statistic([1.0, 3.0]) == pytest.approx(2.0 / (math.sqrt(2.0) / math.sqrt(2)))
    assert t_statistic([1.0]) is None
    assert t_statistic([]) is None
    assert t_statistic([2.0, 2.0, 2.0]) is None  # no variance
    assert t_statistic([-1.0, -3.0]) < 0
