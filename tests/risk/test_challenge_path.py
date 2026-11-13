"""Hand-built paths for risk-management.md > Challenge path simulator."""

import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

from backtester.analytics.daily import weekdays
from backtester.risk.challenge_path import RULE_SETS, play_attempt, simulate
from backtester.risk.monte_carlo import EPS, Day, build_days

START = date(2020, 1, 1)


def trade(d, r, hour=10, weight=1.0):
    stamp = datetime.combine(d, datetime.min.time(), tzinfo=UTC) + timedelta(hours=hour)
    return SimpleNamespace(
        entry_time=stamp, exit_time=stamp + timedelta(minutes=30), r_net=r, risk_weight=weight
    )


def path(rs, rules="ftmo_2step", **kwargs):
    dates = weekdays(START, date(2020, 12, 31))[: len(rs)]
    trades = [trade(d, r) for d, r in zip(dates, rs, strict=True) if r is not None]
    return play_attempt(
        build_days(trades, dates[0], dates[-1]), 0, RULE_SETS[rules], 0.01, **kwargs
    )


def test_presets_and_frozen_validation():
    two, one, instant = (RULE_SETS[k] for k in RULE_SETS)
    assert (two.targets, two.daily_loss, two.max_loss, two.min_trading_days) == (
        (0.1, 0.05),
        0.05,
        0.1,
        4,
    )
    assert (one.targets, one.consistency, one.max_loss_mode) == ((0.1,), 0.5, "eod_trailing")
    assert (instant.targets, instant.consistency, instant.risk_base) == ((), 0.3, "initial")
    with pytest.raises(FrozenInstanceError):
        two.name = "other"
    for change in (
        {"daily_loss": 0},
        {"max_loss": 1},
        {"targets": (-0.1,)},
        {"max_loss_mode": "other"},
        {"risk_base": "other"},
        {"consistency": 0},
        {"consistency": float("nan")},
        {"min_trading_days": -1},
        {"min_trading_days": 1.5},
        {"name": ""},
    ):
        with pytest.raises(ValueError):
            replace(two, **change)


def test_two_step_compounds_and_resets_next_day():
    attempt = path([2] * 9)
    assert attempt.status == "pass"
    assert attempt.phase_results == [{"status": "pass", "days": 5, "day": 4}, {"status": "pass", "days": 4, "day": 8}]
    assert attempt.path[4]["balance"] == pytest.approx(100_000 * 1.02**5)
    assert attempt.path[5]["balance"] == pytest.approx(102_000)
    assert attempt.weekdays_to_end == 9 and attempt.end_index == 8
    assert attempt.payout_day is None
    assert json.loads(json.dumps(attempt.to_dict())) == attempt.to_dict()


def test_target_reached_early_still_needs_four_trading_days():
    attempt = path([11, None, 0, 0, 0, 6, 0, 0, 0])
    assert attempt.phase_results == [{"status": "pass", "days": 4, "day": 4}, {"status": "pass", "days": 4, "day": 8}]
    assert attempt.weekdays_to_end == 9


@pytest.mark.parametrize("rules,limit", [("ftmo_2step", 5), ("ftmo_1step", 3), ("ftmo_instant", 3)])
def test_daily_exact_boundary_and_one_dollar_inside(rules, limit):
    assert path([-limit], rules).status == "daily"
    assert path([-(limit - 0.001)], rules).status == "open"  # $4,999 / $2,999


def test_static_max_with_epsilon_and_daily_precedence():
    attempt = path([-4, -4, -(92_160 - 90_000 - EPS) / 921.6])
    assert attempt.status == "max"
    assert path([-10]).status == "daily"


def test_eod_trailing_ignores_intraday_closed_high_and_never_falls():
    dates = weekdays(START, date(2020, 1, 10))[:4]
    trades = [
        trade(dates[0], 8),
        trade(dates[1], 1000 / 1080, 9),
        trade(dates[1], -2000 / 1090, 12),
        trade(dates[2], 0),
    ]
    attempt = play_attempt(
        build_days(trades, dates[0], dates[-1]), 0, RULE_SETS["ftmo_1step"], 0.01
    )
    assert attempt.status == "open"
    assert [p["balance"] for p in attempt.path] == pytest.approx([108000, 107000, 107000, 107000])
    assert [p["max_floor"] for p in attempt.path] == pytest.approx([90000, 98000, 98000, 98000])


def test_instant_raises_floor_within_day_and_uses_initial_risk():
    trades = [trade(START, 9, 9), trade(START, 1, 12)]
    attempt = play_attempt(build_days(trades, START, START), 0, RULE_SETS["ftmo_instant"], 0.01)
    assert attempt.path[0]["balance"] == 110000
    assert attempt.path[0]["max_floor"] == 100000
    # Wide daily limit isolates the intraday max-loss rule: 109k raises floor to 99k.
    rules = replace(RULE_SETS["ftmo_instant"], daily_loss=0.5)
    trades = [trade(START, 9, 9), trade(START, -10, 12)]
    attempt = play_attempt(build_days(trades, START, START), 0, rules, 0.01)
    assert attempt.status == "max"
    assert attempt.path[0]["max_floor"] == 99000
    assert attempt.path[0]["balance"] == 109000  # breach at entry, before losing exit
    assert attempt.path[0]["worst"] == 99000


def test_consistency_continues_and_uses_net_phase_profit():
    attempt = path([6, 4000 / 1060, -1000 / 1100, 3000 / 1090], "ftmo_1step")
    assert attempt.status == "pass" and attempt.weekdays_to_end == 4
    assert attempt.path[1]["balance"] == pytest.approx(110000)
    assert attempt.path[3]["balance"] == pytest.approx(112000)


def test_instant_survives_watch_and_records_first_payout_day():
    attempt = path([1] * 6, "ftmo_instant", watch_days=5)
    assert attempt.status == "survived" and attempt.weekdays_to_end == 5
    assert attempt.payout_day == 3  # fourth day: 1,000 <= 30% of 4,000
    assert path([1] * 3, "ftmo_instant", watch_days=5).status == "open"
    assert path([None] * 5, "ftmo_instant", watch_days=5).status == "survived"


def test_open_when_data_ends_and_start_index_skips_previous_days():
    days = build_days([trade(START, -20)], START, date(2020, 1, 3))
    attempt = play_attempt(days, 1, RULE_SETS["ftmo_2step"], 0.01)
    assert attempt.status == "open" and attempt.start_index == 1
    assert attempt.end_index == 2 and attempt.weekdays_to_end == 2
    assert all(p["balance"] == 100000 for p in attempt.path)


def test_monthly_starts_determinism_excludes_outside_exits_and_open_rates():
    end = date(2020, 3, 31)
    trades = [trade(date(2019, 12, 31), -100), trade(START, -5), trade(date(2020, 4, 1), -100)]
    a = simulate(trades, START, end, ["ftmo_2step"], 0.01, {"ftmo_2step": 100})
    assert a == simulate(trades, START, end, ["ftmo_2step"], 0.01, {"ftmo_2step": 100})
    row = a["rules"]["ftmo_2step"]
    assert [t["start_date"] for t in row["attempts"]] == ["2020-01-01", "2020-02-03", "2020-03-02"]
    s = row["summary"]
    assert (s["attempts"], s["open"], s["pass_pct"], s["daily_pct"]) == (3, 2, 0, 100)
    assert s["cost_per_funded_before_refund"] is None


def test_fees_percentiles_refund_and_no_finished_attempts():
    end = date(2020, 2, 28)
    dates = weekdays(START, end)
    # January funds after nine weekdays; February fails on the first day.
    trades = [trade(d, 2) for d in dates[:9]] + [trade(date(2020, 2, 3), -5)]
    s = simulate(trades, START, end, ["ftmo_2step"], 0.01, {"ftmo_2step": 250})["rules"][
        "ftmo_2step"
    ]["summary"]
    assert (s["pass_pct"], s["daily_pct"], s["max_pct"]) == (50, 50, 0)
    assert s["median_weekdays_to_funding"] == s["p90_weekdays_to_funding"] == 9
    assert s["cost_per_funded_before_refund"] == 500
    assert s["cost_per_funded_after_refund"] == 0
    s = simulate([], START, end, ["ftmo_1step"], 0.01)["rules"]["ftmo_1step"]["summary"]
    assert s["pass_pct"] is None and s["daily_pct"] is None


def test_weighted_overlap_matches_monte_carlo_worst_approximation():
    day = Day(
        np.array([1.0, -1.0]),
        ((True, 1.0), (True, -1.0), (False, 1.0), (False, -1.0)),
        weights=(0.25, 0.5, 0.25, 0.5),
    )
    attempt = play_attempt([day], 0, RULE_SETS["ftmo_2step"], 0.01)
    assert attempt.path[0]["worst"] == pytest.approx(98750)
    assert attempt.path[0]["balance"] == pytest.approx(99990)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"risk": 0},
        {"risk": float("nan")},
        {"watch_days": 0},
        {"initial": float("inf")},
        {"start_index": -1},
    ],
)
def test_invalid_attempt_inputs(kwargs):
    values = {
        "days": [Day(np.array([]), ())],
        "start_index": 0,
        "rules": RULE_SETS["ftmo_2step"],
        "risk": 0.01,
    }
    values.update(kwargs)
    with pytest.raises(ValueError):
        play_attempt(**values)


@pytest.mark.parametrize("r,weight", [(float("nan"), 1), (1, -1), (float("inf"), 1)])
def test_bad_trade_data_is_rejected(r, weight):
    with pytest.raises(ValueError):
        simulate([trade(START, r, weight=weight)], START, START, ["ftmo_2step"], 0.01)


def test_an_attempt_never_inherits_a_position_opened_before_its_start():
    """Opus review: a fresh account cannot hold a trade entered before the attempt's start date,
    even if that trade exits on or after it (here: entered Friday 31 Jan, exits Monday 3 Feb)."""
    held = SimpleNamespace(
        entry_time=datetime(2020, 1, 31, 15, tzinfo=UTC),
        exit_time=datetime(2020, 2, 3, 9, tzinfo=UTC),
        r_net=-3.0,
    )
    fresh = trade(date(2020, 2, 4), 1.0)
    out = simulate([held, fresh], date(2020, 1, 1), date(2020, 2, 28), ["ftmo_2step"], 0.01)
    feb = next(a for a in out["rules"]["ftmo_2step"]["attempts"] if a["start_date"] == "2020-02-03")
    assert feb["path"][0]["balance"] == 100_000.0  # the -3 R exit belongs to the January attempt only
    assert feb["path"][1]["balance"] == pytest.approx(101_000.0)
