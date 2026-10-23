"""Adaptive risk for prop-firm accounts (ROADMAP 5.7).
Spec: docs/risk-management.md > Prop-firm field > Adaptive risk."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import numpy as np
import pytest

from backtester.risk import monte_carlo as mc
from backtester.risk.adaptive import AdaptiveRisk, risk_factor
from backtester.risk.monte_carlo import MonteCarloConfig

INIT = 100_000.0


def cfg(adaptive: AdaptiveRisk | None = None, **kw) -> MonteCarloConfig:
    base = {"runs": 20, "fan_paths": 0, "risk_levels": (0.01,), "adaptive": adaptive}
    base.update(kw)
    return MonteCarloConfig(**base)


def day(*events):
    """events: ("in"|"out", trade id, r) in time order."""
    rs = [e[2] for e in events if e[0] == "in"]
    return mc.Day(
        np.array(rs, dtype=float),
        tuple((e[0] == "in", e[2]) for e in events),
        tuple(e[1] for e in events),
    )


def play(d, bal=INIT, risk=0.01, adaptive=None, fixed=False, **kw):
    stats: dict = {}
    status, out = mc._play_day(
        d, bal, risk, cfg(adaptive or AdaptiveRisk(), **kw), 1e18, 0, fixed, stats
    )
    return status, out, stats


# ----- config and the factor ---------------------------------------------------------------


def test_config_validates():
    with pytest.raises(ValueError):
        AdaptiveRisk(floor=0.0)
    with pytest.raises(ValueError):
        AdaptiveRisk(floor=1.5)
    with pytest.raises(ValueError):
        AdaptiveRisk(daily_budget=0.0)
    assert AdaptiveRisk().floor == 0.25 and AdaptiveRisk().daily_budget == 0.03
    assert MonteCarloConfig().adaptive is None


@pytest.mark.parametrize(
    ("equity", "factor"),
    [
        (100_000.0, 1.0),  # room 10 % = full room
        (97_500.0, 0.75),  # room 7.5 %
        (95_000.0, 0.5),  # room 5 %
        (92_500.0, 0.25),  # room 2.5 %
        (90_000.0, 0.25),  # room 0: floor
        (85_000.0, 0.25),  # below the line: floor
        (110_000.0, 1.0),  # in profit: capped at the base risk
    ],
)
def test_factor_is_linear_in_the_room_with_floor_and_cap(equity, factor):
    assert risk_factor(equity, INIT, 0.10, 0.25) == pytest.approx(factor)


def test_factor_uses_the_given_floor():
    assert risk_factor(90_000.0, INIT, 0.10, 0.1) == pytest.approx(0.1)
    assert risk_factor(92_500.0, INIT, 0.10, 0.1) == pytest.approx(0.25)


# ----- risk fixed at entry -----------------------------------------------------------------


def test_risk_is_fixed_at_entry_not_at_exit():
    # two trades enter together at full room (1000 each); both lose 1 R. The second loses its
    # entry risk (1000), not 1 % of the balance after the first loss (which would be 990)
    d = day(("in", 0, -1.0), ("in", 1, -1.0), ("out", 0, -1.0), ("out", 1, -1.0))
    status, bal, _ = play(d)
    assert status is None
    assert bal == pytest.approx(98_000.0)


def test_risk_shrinks_with_the_room_at_entry():
    # balance 95,000: room 5 %, factor 0.5, risk$ = 1 % x 95,000 x 0.5 = 475
    _, bal, _ = play(day(("in", 0, -1.0), ("out", 0, -1.0)), bal=95_000.0)
    assert bal == pytest.approx(95_000.0 - 475.0)


def test_challenge_in_profit_risks_the_base_on_the_current_balance():
    _, bal, _ = play(day(("in", 0, 1.0), ("out", 0, 1.0)), bal=120_000.0)
    assert bal == pytest.approx(121_200.0)  # factor capped at 1, 1 % of 120,000


def test_funded_base_risk_is_on_the_initial_balance():
    d = day(("in", 0, 1.0), ("out", 0, 1.0))
    _, bal, _ = play(d, bal=95_000.0, fixed=True)  # 1 % of 100,000 x factor 0.5 = 500
    assert bal == pytest.approx(95_500.0)
    _, bal, _ = play(d, bal=95_000.0, fixed=False)  # challenge: 1 % of 95,000 x 0.5 = 475
    assert bal == pytest.approx(95_475.0)


# ----- daily risk budget -------------------------------------------------------------------


def test_fourth_trade_is_skipped_when_three_percent_is_open():
    d = day(
        ("in", 0, 1.0), ("in", 1, 1.0), ("in", 2, 1.0), ("in", 3, 1.0),
        ("out", 0, 1.0), ("out", 1, 1.0), ("out", 2, 1.0), ("out", 3, 1.0),
    )  # fmt: skip
    status, bal, stats = play(d)
    assert status is None
    assert bal == pytest.approx(103_000.0)  # the 4th trade's +1 R is not taken
    assert stats["skipped"] == 1 and stats["entries"] == 4


def test_new_trade_is_cut_to_the_remaining_budget():
    d = day(
        ("in", 0, 1.0), ("in", 1, 1.0), ("in", 2, 1.0),
        ("out", 0, 1.0), ("out", 1, 1.0), ("out", 2, 1.0),
    )  # fmt: skip
    # budget 2.5 %: 2,000 open, so the third trade gets 500 (floor risk 250 fits)
    _, bal, stats = play(d, adaptive=AdaptiveRisk(daily_budget=0.025))
    assert bal == pytest.approx(102_500.0) and stats.get("skipped", 0) == 0
    # budget 2.2 %: 200 left < floor risk 250 -> skipped
    _, bal, stats = play(d, adaptive=AdaptiveRisk(daily_budget=0.022))
    assert bal == pytest.approx(102_000.0) and stats["skipped"] == 1
    # budget 2.25 %: exactly the floor risk fits
    _, bal, stats = play(d, adaptive=AdaptiveRisk(daily_budget=0.0225))
    assert bal == pytest.approx(102_250.0) and stats.get("skipped", 0) == 0


def test_open_trade_counts_at_initial_risk_even_if_it_later_loses_more():
    # Trade 0 reserves 1,000 while open. Its later 1.5 R loss is unknown at trade 1's entry.
    d = day(("in", 0, -1.5), ("in", 1, 1.0), ("out", 1, 1.0), ("out", 0, -1.5))
    _, bal, _ = play(d, adaptive=AdaptiveRisk(daily_budget=0.025))  # 1,500 left -> full 1,000
    assert bal == pytest.approx(100_000.0 - 1_500.0 + 1_000.0)
    _, bal, _ = play(d, adaptive=AdaptiveRisk(daily_budget=0.0225))  # 1,250 left -> full 1,000
    assert bal == pytest.approx(100_000.0 - 1_500.0 + 1_000.0)


def test_loss_so_far_uses_up_the_budget():
    # sequence of lone losing trades: the day cannot lose more than 3 % of the initial balance
    events = []
    for i in range(10):
        events += [("in", i, -1.0), ("out", i, -1.0)]
    status, bal, stats = play(day(*events))
    assert status is None
    assert INIT - bal <= 0.03 * INIT + 1e-6
    assert INIT - bal == pytest.approx(0.03 * INIT)  # later trades cut / skipped, budget used
    assert stats["skipped"] >= 1


def test_overlapping_losers_cannot_breach_the_daily_limit():
    # ten trades open together, all stopped out: only three fit, the day loses exactly 3 %
    events = [("in", i, -1.0) for i in range(10)] + [("out", i, -1.0) for i in range(10)]
    status, bal, stats = play(day(*events))
    assert status is None and bal == pytest.approx(97_000.0) and stats["skipped"] == 7


def test_skipped_trade_exit_is_ignored_and_does_not_open_risk():
    # after the skipped trade 3 exits nothing is left open; a later entry has the budget again
    d = day(
        ("in", 0, 1.0), ("in", 1, 1.0), ("in", 2, 1.0), ("in", 3, 5.0), ("out", 3, 5.0),
        ("out", 0, 1.0), ("out", 1, 1.0), ("out", 2, 1.0),
    )  # fmt: skip
    _, bal, stats = play(d)
    assert bal == pytest.approx(103_000.0) and stats["skipped"] == 1


def test_breach_is_still_detected_with_a_daily_limit_below_the_budget():
    d = day(("in", 0, -1.0), ("in", 1, -1.0), ("in", 2, -1.0), ("out", 0, -1.0))
    status, _, _ = play(d, daily_loss=0.025)  # 3 % open at the stops > 2.5 %
    assert status == "daily"


# ----- fixed-risk regression after B2 ------------------------------------------------------


@dataclass
class T:
    entry_time: datetime
    exit_time: datetime
    r_net: float


def golden_trades():
    rng = np.random.default_rng(11)
    days, d = [], date(2024, 1, 1)
    while len(days) < 260:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    trades = []
    for dd in days:
        for _ in range(int(rng.integers(0, 4))):
            h = int(rng.integers(7, 18))
            t0 = datetime(dd.year, dd.month, dd.day, h, tzinfo=UTC)
            r = float(rng.choice([-1.0, -1.0, -0.5, 1.5, 2.0, 0.3]))
            trades.append(T(t0, t0 + timedelta(hours=float(rng.integers(1, 5))), r))
    return trades, days[0], days[-1]


# B2 (user, 2026-10-22): play passing days to the close. Account-path statistics are unchanged;
# FTMO counts/times now include later trades on those days (see test_review_b_risk.py).
# Same trades, seed 11 / MC seed 42, 30 runs.
GOLDEN = {
    0.005: (35, 35, 0, 0, 74.0, 26, 0.0, 157526.51649220887, 6.627505823080764),
    0.01: (62, 60, 0, 2, 42.0, 41, 0.43902439024390244, 244683.78272027196, 12.906836610244342),
    0.015: (124, 101, 1, 22, 29.0, 85, 0.9764705882352941, 374816.91141752165, 18.85956405435207),
}  # fmt: skip


def test_fixed_risk_regression_with_full_passing_days():
    trades, s, e = golden_trades()
    res = mc.run_monte_carlo(trades, s, e, MonteCarloConfig(runs=30, fan_paths=0))
    for risk, want in GOLDEN.items():
        f, st = res["risks"][risk]["ftmo"], res["risks"][risk]["stats"]
        got = (
            f["attempts"], f["passes"], f["fail_daily"], f["fail_max"], f["median_days_to_pass"],
            f["funded_observed"], f["funded_lost_probability"],
            st["final_balance"]["p50"], st["max_dd_pct"]["p95"],
        )  # fmt: skip
        assert got == want


# ----- whole simulation --------------------------------------------------------------------


def test_adaptive_simulation_runs_and_reports_the_new_numbers():
    trades, s, e = golden_trades()
    c = MonteCarloConfig(runs=30, fan_paths=0, adaptive=AdaptiveRisk())
    f = mc.run_monte_carlo(trades, s, e, c)["risks"][0.015]["ftmo"]
    assert f["attempts"] > 0
    assert f["average_days_to_pass"] is None or f["average_days_to_pass"] > 0
    assert f["skipped_trades"] >= 0 and f["trades_seen"] > 0
    assert f["fail_daily"] == 0  # the 3 % budget keeps a day away from the 5 % limit


def test_average_days_to_pass_is_reported_for_the_fixed_path_too():
    rs = [1.0] * 200
    days, d = [], date(2025, 1, 6)
    while len(days) < 200:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    trades = [
        T(datetime(x.year, x.month, x.day, 10, tzinfo=UTC),
          datetime(x.year, x.month, x.day, 11, tzinfo=UTC), r)
        for x, r in zip(days, rs, strict=True)
    ]  # fmt: skip
    f = mc.run_monte_carlo(trades, days[0], days[-1], cfg(None, runs=3))["risks"][0.01]["ftmo"]
    assert f["average_days_to_pass"] == 15.0 and f["median_days_to_pass"] == 15.0
    assert f["skipped_trades"] == 0
