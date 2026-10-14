"""Efficiency ratio (noise) and the small statistics of the noise study.
Spec: ROADMAP.md › 11.1; knowledge base I-01 (Kaufman p.10-14)."""

from __future__ import annotations

import pytest

from backtester.analytics.noise import (
    efficiency_ratio,
    mean_by,
    median,
    random_walk_er,
    rank_correlation,
)


def test_straight_line_is_fully_efficient():
    assert efficiency_ratio([1, 2, 3, 4, 5], 2) == [None, None, 1.0, 1.0, 1.0]


def test_back_and_forth_is_pure_noise():
    assert efficiency_ratio([1, 2, 1, 2, 1], 2) == [None, None, 0.0, 0.0, 0.0]


def test_mixed_series_known_value():
    # n = 4 at index 4: |13 - 10| / (|11-10| + |10-11| + |12-10| + |13-12|) = 3 / 5
    out = efficiency_ratio([10, 11, 10, 12, 13], 4)
    assert out[:4] == [None] * 4
    assert out[4] == pytest.approx(0.6)


def test_flat_window_has_no_ratio():
    assert efficiency_ratio([5, 5, 5, 5], 2) == [None, None, None, None]


def test_downtrend_counts_as_efficient_too():
    assert efficiency_ratio([5, 4, 3], 2)[2] == pytest.approx(1.0)


def test_short_series_and_bad_period():
    assert efficiency_ratio([1, 2], 5) == [None, None]
    assert efficiency_ratio([], 3) == []
    with pytest.raises(ValueError):
        efficiency_ratio([1, 2, 3], 0)


def test_value_never_depends_on_later_closes():
    closes = [10, 11, 10, 12, 13, 9, 14, 14, 15, 11]
    full = efficiency_ratio(closes, 3)
    for k in range(1, len(closes) + 1):
        assert efficiency_ratio(closes[:k], 3) == full[:k]


def test_ratio_is_between_zero_and_one():
    closes = [100, 103, 99, 104, 98, 105, 97, 106, 96, 107, 95]
    vals = [v for v in efficiency_ratio(closes, 5) if v is not None]
    assert vals
    assert all(0.0 <= v <= 1.0 for v in vals)


# --- small statistics ---------------------------------------------------------------------------


def test_mean_by_groups_and_skips_missing_values():
    keys = ["a", "a", "b", "b", "b"]
    values = [1.0, None, 2.0, 4.0, None]
    out = mean_by(keys, values)
    assert out == {"a": (1.0, 1), "b": (3.0, 2)}


def test_mean_by_group_without_values_is_absent():
    assert mean_by(["a"], [None]) == {}


def test_median_even_odd_empty():
    assert median([3, 1, 2]) == 2
    assert median([4, 1, 3, 2]) == 2.5
    assert median([]) is None


def test_rank_correlation_monotone_is_one_even_when_not_linear():
    out = rank_correlation([1, 2, 3, 4, 5], [1, 4, 9, 16, 100])
    assert out["rho"] == pytest.approx(1.0)
    assert out["n"] == 5


def test_rank_correlation_reversed_is_minus_one():
    assert rank_correlation([1, 2, 3, 4], [9, 7, 5, 1])["rho"] == pytest.approx(-1.0)


def test_rank_correlation_with_ties_uses_average_ranks():
    # x ranks: 1, 2.5, 2.5, 4; y ranks: 1, 2, 3, 4
    out = rank_correlation([1, 2, 2, 3], [1, 2, 3, 4])
    assert out["rho"] == pytest.approx(0.9486833, abs=1e-6)


def test_rank_correlation_t_statistic():
    out = rank_correlation([1, 2, 3, 4, 5], [2, 1, 4, 3, 5])  # rho = 0.8
    assert out["rho"] == pytest.approx(0.8)
    assert out["t"] == pytest.approx(0.8 * (3 / (1 - 0.64)) ** 0.5)


def test_rank_correlation_undefined_cases():
    assert rank_correlation([1, 2], [1, 2]) is None  # fewer than 3 points
    assert rank_correlation([1, 1, 1], [1, 2, 3]) is None  # no variation
    with pytest.raises(ValueError):
        rank_correlation([1, 2, 3], [1, 2])


def test_random_walk_reference_is_seeded_and_falls_with_the_window():
    a = random_walk_er(20, bars=20_000, seed=3)
    assert a == random_walk_er(20, bars=20_000, seed=3)
    assert 0.20 < a < 0.25
    assert random_walk_er(10, bars=20_000, seed=3) > a > random_walk_er(60, bars=20_000, seed=3)
