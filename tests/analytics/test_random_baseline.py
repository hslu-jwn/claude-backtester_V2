"""Random-entry baseline (kind B). Spec: risk-management.md > Monte Carlo report, B."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.analytics.random_baseline import RandomBaselineConfig, random_entry_baseline

D0 = datetime(2026, 1, 5, 14, 30, tzinfo=UTC)


def trades(rs, symbol="NAS100"):
    return [
        SimpleNamespace(symbol=symbol, entry_time=D0 + timedelta(days=i), r_net=r)
        for i, r in enumerate(rs)
    ]


def test_fade_always_wins_percentile_near_100():
    n = 30
    res = random_entry_baseline(trades([1.0] * n), trades([-1.0] * n))
    assert res.strategy_net_r == n and res.days == n
    assert res.percentile == 100.0  # no random run takes every day
    assert res.p95 < n and res.mean == pytest.approx(0, abs=3)


def test_identical_lists_every_run_equals_the_strategy():
    t = trades([1.0, -1.0, 0.5, 2.0])
    res = random_entry_baseline(t, t, RandomBaselineConfig(runs=50))
    assert set(res.run_net_r) == {2.5}
    assert res.percentile == 0.0  # strictly below: none
    assert res.mean == res.p5 == res.p95 == 2.5


def test_percentile_math_on_a_tiny_enumeration():
    # two days; strategy [1, 1] = 2; alternative [0, 0]; runs total 0, 1 or 2
    cfg = RandomBaselineConfig(runs=4000)
    res = random_entry_baseline(trades([1.0, 1.0]), trades([0.0, 0.0]), cfg)
    runs = res.run_net_r
    expected = sum(r < 2.0 for r in runs) / len(runs) * 100
    assert res.percentile == pytest.approx(expected)
    assert 70 < res.percentile < 80  # P(not both) = 0.75
    assert res.mean == pytest.approx(1.0, abs=0.05)


def test_deterministic_and_seed_dependent():
    a, b = trades([1.0, -2.0, 0.3, 0.7, 1.1]), trades([0.2, 0.1, -1.0, 0.0, 3.0])
    r1 = random_entry_baseline(a, b)
    assert r1 == random_entry_baseline(a, b)
    assert r1.run_net_r != random_entry_baseline(a, b, RandomBaselineConfig(seed=7)).run_net_r


def test_p_strategy_one_always_takes_the_strategy():
    res = random_entry_baseline(
        trades([1.0, 2.0]), trades([-5.0, -5.0]), RandomBaselineConfig(runs=10, p_strategy=1.0)
    )
    assert set(res.run_net_r) == {3.0}


def test_match_is_per_symbol_and_day_not_by_order():
    a = trades([1.0, 2.0])
    b = list(reversed(trades([10.0, 20.0])))  # same days, other order
    res = random_entry_baseline(a, b, RandomBaselineConfig(runs=1, p_strategy=0.0))
    assert res.run_net_r == (30.0,)


@pytest.mark.parametrize(
    "a,b",
    [
        (trades([1.0, 1.0]), trades([1.0])),  # day missing
        (trades([1.0]), trades([1.0], symbol="US500")),  # other symbol
        (trades([1.0]) * 2, trades([1.0])),  # duplicate day
    ],
)
def test_unmatched_or_duplicate_days_raise(a, b):
    with pytest.raises(ValueError):
        random_entry_baseline(a, b)


def test_config_validation():
    with pytest.raises(ValueError):
        RandomBaselineConfig(runs=0)
    with pytest.raises(ValueError):
        RandomBaselineConfig(p_strategy=1.5)
    assert (RandomBaselineConfig().runs, RandomBaselineConfig().seed) == (1000, 42)
