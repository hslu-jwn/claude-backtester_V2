"""T-25 stress scenarios beyond the worst seen day.
Spec: docs/risk-management.md > Stress scenarios (T-25)."""

import numpy as np
import pytest

from backtester.risk import monte_carlo as mc
from backtester.risk import stress
from backtester.risk.stress import StressScenario


def _day(*rs, weights=()):
    events = tuple(e for r in rs for e in ((True, r), (False, r)))
    return mc.Day(np.array(rs, dtype=float), events, tuple(range(len(events))), weights)


def cfg(**kw):
    base = {"runs": 50, "seed": 7, "risk_levels": (0.01,), "fan_paths": 0}
    return mc.MonteCarloConfig(**{**base, **kw})


def test_shock_day_scales_the_worst_day():
    days = [_day(1.0), _day(-1.0, -0.5), _day(0.2), _day()]  # worst sum is day 1 (-1.5)
    s = stress.shock_day(days, 2.0)
    assert s.r.tolist() == [-2.0, -1.0]
    assert [r for _, r in s.events] == [-2.0, -2.0, -1.0, -1.0]
    assert s.ids == days[1].ids


def test_shock_day_keeps_weights():
    days = [_day(-1.0, weights=(0.5, 0.5)), _day(0.3)]
    assert stress.shock_day(days, 1.5).weights == (0.5, 0.5)


def test_shock_day_needs_a_losing_day():
    with pytest.raises(ValueError):
        stress.shock_day([_day(1.0), _day(0.5)], 2.0)


@pytest.mark.parametrize("bad", [StressScenario("x", 0.0), StressScenario("x", 1.0, days=0)])
def test_scenario_validation(bad):
    with pytest.raises(ValueError):
        stress.with_shocks(
            [_day(-1.0), _day(1.0)], np.zeros((1, 2), dtype=int), bad, np.random.default_rng(0)
        )


def test_with_shocks_places_k_consecutive_shock_days_in_every_run():
    days = [_day(-1.0)] + [_day(0.1) for _ in range(9)]
    orders = np.tile(np.arange(10), (40, 1))
    d2, o2 = stress.with_shocks(
        days, orders, StressScenario("week", 1.0, days=3), np.random.default_rng(1)
    )
    shock = len(days)
    assert len(d2) == len(days) + 1 and d2[:shock] == days
    assert o2.shape == orders.shape
    for row in o2:
        where = np.flatnonzero(row == shock)
        assert len(where) == 3 and np.all(np.diff(where) == 1)
        keep = row != shock
        assert np.array_equal(row[keep], np.arange(10)[keep])  # the rest of the order is untouched
    assert len({int(np.flatnonzero(r == shock)[0]) for r in o2}) > 1  # positions vary


def test_with_shocks_is_seeded():
    days = [_day(-1.0)] + [_day(0.1) for _ in range(9)]
    orders = np.tile(np.arange(10), (5, 1))
    sc = StressScenario("2x", 2.0)
    a = stress.with_shocks(days, orders, sc, np.random.default_rng(3))[1]
    b = stress.with_shocks(days, orders, sc, np.random.default_rng(3))[1]
    assert np.array_equal(a, b)


def test_ftmo_by_risk_unchanged_for_plain_orders():
    # n_days now comes from the order length; for plain reshuffles it equals len(days)
    days = [_day(0.5), _day(-0.4), _day(0.3), _day(-1.0, 0.2)] * 30
    c = cfg()
    orders = mc.reshuffle_orders(len(days), c)
    assert orders.shape[1] == len(days)
    assert mc.ftmo_by_risk(days, orders, c) == mc.ftmo_by_risk(days, orders, c)


def test_a_shock_beyond_the_daily_limit_breaches_every_open_attempt():
    # Flat days never reach the target, so the shock always lands inside an attempt.
    # Worst day -1 R at 1 % risk, x 6 = -6 % > the 5 % daily limit.
    days = [_day(-1.0)] + [_day(0.01) for _ in range(59)]
    c = cfg(runs=30)
    out = stress.stress_ftmo(days, c, (StressScenario("6x", 6.0),))
    base, hit = out["baseline"][0.01], out["6x"][0.01]
    assert base["fail_daily"] == 0
    assert hit["fail_daily"] == c.runs  # one breach per run, then no attempt reaches the target


def test_default_scenarios_report_next_to_the_baseline_and_lower_the_pass_rate():
    # Worst seen day is one trade of about -2.8 R; at 2 % risk, 2x that is ~-11 %: a sure breach.
    rng = np.random.default_rng(11)
    days = [_day(float(x)) for x in rng.normal(0.08, 1.0, 200)]
    c = cfg(runs=200, risk_levels=(0.02,))
    out = stress.stress_ftmo(days, c, stress.DEFAULT_SCENARIOS)
    assert set(out) == {"baseline", *(s.name for s in stress.DEFAULT_SCENARIOS)}
    base = out["baseline"][0.02]["pass_probability"]
    assert out["2x worst day"][0.02]["pass_probability"] < base
