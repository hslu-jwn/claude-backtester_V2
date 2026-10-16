"""Monte Carlo verdict: seven checks, EDGE / WEAK / NO EDGE.
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
    stressed_net=6.0, net_without_best=7.0, fill_median=8.0, dsr=0.99,
)  # fmt: skip


def check(verdict, key):
    return next(c for c in verdict.checks if c.key == key)


def test_all_pass_is_edge():
    v = evaluate(GOOD)
    assert v.label == "EDGE" and v.failed == ()
    assert (
        [c.key for c in v.checks] == list(CHECK_KEYS)
        and len(CHECK_KEYS) == 7
        and CHECK_KEYS[-1] == "deflated_sharpe"
    )
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
        ({"dsr": 0.949}, "deflated_sharpe"),
        ({"dsr": 0.0}, "deflated_sharpe"),
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


# ----- halves of the run's own period (user decision 2026-10-15) -----------------------------


def _tr(day, r):
    from datetime import UTC, datetime
    from types import SimpleNamespace

    return SimpleNamespace(
        entry_time=datetime(day.year, day.month, day.day, 14, 30, tzinfo=UTC), r_net=r
    )


def test_period_halves_split_at_the_middle_date():
    from datetime import date

    from backtester.analytics.verdict import middle_date, period_halves

    start, end = date(2020, 1, 1), date(2021, 9, 13)
    mid = middle_date(start, end)
    assert mid == date(2020, 11, 6)  # 621 days, half = 310
    trades = [_tr(date(2020, 3, 1), 1.0), _tr(mid, 2.0), _tr(date(2020, 11, 7), 4.0),
              _tr(date(2021, 9, 13), 8.0)]  # fmt: skip
    assert period_halves(trades, start, end) == (3.0, 12.0)  # the middle date is in the first half


def test_period_halves_empty_half_has_net_zero_and_fails_the_check():
    from datetime import date

    from backtester.analytics.verdict import VerdictInputs, evaluate, period_halves

    start, end = date(2020, 1, 1), date(2020, 12, 31)
    first, second = period_halves([_tr(date(2020, 2, 1), 5.0)], start, end)
    assert (first, second) == (5.0, 0.0)
    v = evaluate(VerdictInputs(1.0, 3.0, 99.0, first, second, 1.0, 1.0, 1.0))
    assert "halves" in v.failed


def test_period_halves_ignores_trades_outside_nothing_and_one_day_period():
    from datetime import date

    from backtester.analytics.verdict import period_halves

    d = date(2020, 5, 5)
    assert period_halves([_tr(d, 2.0)], d, d) == (2.0, 0.0)


# ----- check 7: deflated Sharpe (ROADMAP 12.10, rule set by the user 2026-10-16) --------------


def test_dsr_equality_passes_and_value_and_threshold_are_shown():
    v = evaluate(replace(GOOD, dsr=0.95))
    c = check(v, "deflated_sharpe")
    assert c.passed and c.available and c.value == 0.95 and c.threshold == 0.95
    assert v.label == "EDGE"


def test_dsr_none_is_not_available_and_not_a_failure():
    v = evaluate(replace(GOOD, dsr=None))
    c = check(v, "deflated_sharpe")
    assert not c.available and not c.passed and c.value is None
    assert v.label == "EDGE" and "deflated_sharpe" in v.not_available
    assert "deflated_sharpe" not in v.failed


def test_dsr_default_input_is_none():
    assert VerdictInputs(1.0, 3.0, 99.0, 1.0, 1.0, 1.0, 1.0, 1.0).dsr is None


def test_dsr_counts_toward_weak_and_no_edge():
    assert evaluate(replace(GOOD, dsr=0.5, t=1.0)).label == "WEAK"  # 2 fails
    assert evaluate(replace(GOOD, dsr=0.5, t=1.0, fill_median=-1.0)).label == "NO EDGE"


def test_dsr_min_is_configurable():
    v = evaluate(GOOD, VerdictConfig(dsr_min=0.995))
    assert v.failed == ("deflated_sharpe",)
    with pytest.raises(ValueError):
        VerdictConfig(dsr_min=1.5)
