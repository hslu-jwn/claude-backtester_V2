"""PSR, expected max Sharpe and deflated Sharpe: hand-computed values.
Spec: risk-management.md > Trial log and deflated Sharpe (ROADMAP 12.10)."""

from __future__ import annotations

import math
from statistics import NormalDist, variance

import pytest

from backtester.analytics.deflated_sharpe import (
    DeflatedSharpeConfig,
    deflated_sharpe,
    expected_max_sharpe,
    psr,
    trade_stats,
)

N01 = NormalDist()
GAMMA = 0.5772156649


def test_config_defaults_are_the_spec_values():
    c = DeflatedSharpeConfig()
    assert c.dsr_min == 0.95 and c.min_sharpes == 2
    assert c.euler_gamma == pytest.approx(GAMMA, abs=1e-6)


def test_trade_stats_hand_values():
    s = trade_stats([1.0, 2.0, 3.0, 4.0])
    assert s.n == 4 and s.mean == 2.5
    assert s.sd == pytest.approx(math.sqrt(5 / 3))  # sample sd
    assert s.skew == pytest.approx(0.0, abs=1e-12)
    # population moments: m2 = 1.25, m4 = (2*1.5**4 + 2*0.5**4)/4 = 2.5625 -> 2.5625/1.25**2
    assert s.kurt == pytest.approx(2.5625 / 1.25**2)
    assert s.sharpe == pytest.approx(2.5 / math.sqrt(5 / 3))


def test_trade_stats_skew_sign():
    assert trade_stats([-1.0, -1.0, -1.0, 3.0]).skew > 0  # one big win
    assert trade_stats([1.0, 1.0, 1.0, -3.0]).skew < 0


@pytest.mark.parametrize("values", [[], [1.0], [2.0, 2.0, 2.0]])
def test_trade_stats_none_safe(values):
    s = trade_stats(values)
    assert s.n == len(values)
    assert s.sharpe is None and s.skew is None and s.kurt is None


def test_psr_normal_case_hand_value():
    expected = N01.cdf(0.1 * math.sqrt(100) / math.sqrt(1 + 0.005))
    assert psr(0.1, 0.0, 101, 0.0, 3.0) == pytest.approx(expected)


def test_psr_at_the_benchmark_is_half():
    assert psr(0.2, 0.2, 50, -0.5, 6.0) == pytest.approx(0.5)


def test_negative_skew_and_high_kurtosis_lower_psr():
    base = psr(0.15, 0.0, 200, 0.0, 3.0)
    assert psr(0.15, 0.0, 200, -1.0, 3.0) < base
    assert psr(0.15, 0.0, 200, 0.0, 10.0) < base


@pytest.mark.parametrize(
    ("sharpe", "n", "skew", "kurt"),
    [(0.1, 1, 0.0, 3.0), (0.1, 0, 0.0, 3.0), (3.0, 50, 2.0, 3.0)],
)
def test_psr_none_for_n_below_2_or_nonpositive_denominator(sharpe, n, skew, kurt):
    # third case: 1 - 2*3 + (2/4)*9 = -0.5 <= 0
    assert psr(sharpe, 0.0, n, skew, kurt) is None


def test_expected_max_sharpe_hand_value_n10_v1():
    n = 10
    expected = (1 - GAMMA) * N01.inv_cdf(1 - 1 / n) + GAMMA * N01.inv_cdf(1 - 1 / (n * math.e))
    assert expected_max_sharpe(10, 1.0) == pytest.approx(expected, abs=1e-6)
    assert 1.5 < expected_max_sharpe(10, 1.0) < 1.65  # about 1.57


def test_expected_max_sharpe_n1_is_zero_and_scales_with_sqrt_v():
    assert expected_max_sharpe(1, 4.0) == 0.0
    assert expected_max_sharpe(0, 4.0) == 0.0
    assert expected_max_sharpe(10, 4.0) == pytest.approx(2 * expected_max_sharpe(10, 1.0))


def _stats():
    return trade_stats([1.0, -1.0, 2.0, -0.5, 1.5, -1.0, 0.5, 1.0, -0.2, 0.8] * 10)


def test_n1_dsr_equals_psr_zero():
    s = _stats()
    r = deflated_sharpe(s, 1, [])
    assert r.sr0 == 0.0 and r.dsr == pytest.approx(r.psr0)
    assert r.psr0 == pytest.approx(psr(s.sharpe, 0.0, s.n, s.skew, s.kurt))


def test_v_rule_family_variance_when_two_sharpes():
    s = _stats()
    sharpes = [0.05, 0.1, 0.2]
    r = deflated_sharpe(s, 10, sharpes)
    assert r.variance == pytest.approx(variance(sharpes))
    assert r.sr0 == pytest.approx(expected_max_sharpe(10, variance(sharpes)))
    assert r.n_trials == 10


def test_v_rule_fallback_one_over_n_with_fewer_than_two_sharpes():
    s = _stats()
    for sharpes in ([], [0.1]):
        assert deflated_sharpe(s, 10, sharpes).variance == pytest.approx(1 / s.n)


def test_n_trials_below_one_counts_as_one():
    assert deflated_sharpe(_stats(), 0, []).n_trials == 1


def test_more_trials_lower_dsr():
    s = _stats()
    d = [deflated_sharpe(s, n, [0.05, 0.15]).dsr for n in (1, 5, 20, 100)]
    assert d == sorted(d, reverse=True) and d[0] > d[-1]


def test_undefined_stats_give_none_everywhere():
    r = deflated_sharpe(trade_stats([1.0]), 5, [0.1, 0.2])
    assert r.psr0 is None and r.dsr is None and r.sr0 is None
    assert r.n_trials == 5


def test_nonpositive_denominator_gives_none_dsr():
    # skew very high with a big Sharpe: 1 - g3*SR + (g4-1)/4*SR^2 can go <= 0
    s = trade_stats([0.0] * 5 + [100.0] + [0.1] * 2)
    r = deflated_sharpe(s, 1, [])
    assert (r.psr0 is None) == (r.dsr is None)
