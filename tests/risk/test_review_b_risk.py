"""B1-B3 regressions. Spec: risk-management.md (user decisions, 2026-10-22)."""

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

from backtester.risk import monte_carlo as mc
from backtester.risk import prop_card as pc
from backtester.risk.adaptive import AdaptiveRisk
from backtester.risk.prop_rules import GuardConfig, evaluate
from backtester.ui import live_model, prop_firm_card


def day(*rs):
    return mc.Day(
        np.array(rs, dtype=float),
        tuple(event for r in rs for event in ((True, r), (False, r))),
        tuple(i for i in range(len(rs)) for _ in range(2)),
    )


@pytest.mark.parametrize("start", [96_000.0, 110_000.0])
def test_b1_guard_daily_limit_is_initial_money_from_day_start(start):
    config = GuardConfig(daily_stop_percent=10)
    assert not evaluate(config, start, start - 4_999).breach
    hit = evaluate(config, start, start - 5_000)
    assert hit.breach and hit.reason == "FTMO daily loss reached"
    assert hit.day_pl_percent == pytest.approx(-5_000 / start * 100)


def test_b1_guard_initial_override_and_custom_percent():
    config = GuardConfig(daily_stop_percent=10, ftmo_daily_loss_percent=3)
    assert not evaluate(config, 60_000, 58_501, initial_balance=50_000).breach
    assert evaluate(config, 60_000, 58_500, initial_balance=50_000).breach


@pytest.mark.parametrize("adaptive", [None, AdaptiveRisk(floor=1, daily_budget=0.2)])
@pytest.mark.parametrize("start", [96_000.0, 110_000.0])
def test_b1_replay_uses_initial_daily_limit(adaptive, start):
    config = mc.MonteCarloConfig(adaptive=adaptive)
    # Funded risk is 1,000 per trade: a 4,999 loss survives; exactly 5,000 breaches.
    for loss, expected in ((4_999, None), (5_000, "daily")):
        status, _ = mc._play_day(
            day(-loss / 1_000), start, 0.01, config, mc.NO_TARGET, 0, fixed=True
        )
        assert status == expected


@pytest.mark.parametrize("start", [96_000.0, 110_000.0])
def test_b1_live_daily_bar_normalizes_money_by_initial_balance(start):
    status = {
        "day_pl": -2_500.0,
        "day_pl_percent": -2_500 / start * 100,
        "equity": start - 2_500,
        "initial_balance": 100_000.0,
    }
    daily = live_model.ftmo_bars(status)[0]
    assert daily["used"] == 2.5
    assert daily["fraction"] == 0.5
    assert daily["left"] == 2.5


@pytest.mark.parametrize("missing", ["day_pl", "initial_balance"])
def test_b1_live_daily_bar_requires_money_and_initial(missing):
    status = {"day_pl": -1_000, "initial_balance": 100_000, "day_pl_percent": -1}
    del status[missing]
    assert live_model.ftmo_bars(status)[0]["used"] is None


@pytest.mark.parametrize("adaptive", [None, AdaptiveRisk(floor=1, daily_budget=0.2)])
@pytest.mark.parametrize(
    ("rs", "expected", "balance"),
    [
        ((10, -15, 10), "daily", 93_500),  # target first; later loss breaches before recovery
        ((10, -1), None, 108_900),  # target lost before the close
        ((10, 1), "pass", 111_100),
    ],  # closing balance includes the whole day
)
def test_b2_passing_day_is_completed(adaptive, rs, expected, balance):
    config = mc.MonteCarloConfig(min_trading_days=1, adaptive=adaptive)
    status, closing = mc._play_day(day(*rs), 100_000, 0.01, config, 110_000, 0)
    assert status == expected
    assert closing == pytest.approx(balance)


@pytest.mark.parametrize("adaptive", [None, AdaptiveRisk(floor=1, daily_budget=0.2)])
def test_b2_unfinished_share_and_finished_denominator(adaptive):
    config = mc.MonteCarloConfig(
        runs=1, risk_levels=(0.01,), min_trading_days=1, funded_days=1, adaptive=adaptive
    )
    # One pass (P1 day 1, P2 day 2), one funded day, one failure, one unfinished attempt.
    days = [day(10), day(5), day(0), day(-6), day(0)]
    result = mc.ftmo_by_risk(days, [np.arange(5)], config)[0.01]
    assert result["attempts"] == 2  # finished attempts, retained API meaning
    assert result["passes"] == result["fail_daily"] == 1
    assert result["unfinished_attempts"] == 1
    assert result["total_attempts"] == 3
    assert result["unfinished_share"] == pytest.approx(1 / 3)
    assert result["pass_probability"] == 0.5


@pytest.mark.parametrize("adaptive", [None, AdaptiveRisk()])
def test_b2_no_phantom_attempt_after_last_day_or_without_trades(adaptive):
    config = mc.MonteCarloConfig(runs=1, risk_levels=(0.01,), adaptive=adaptive)
    for days in ([], [day()], [day(-6)]):
        result = mc.ftmo_by_risk(days, [np.arange(len(days))], config)[0.01]
        assert result["unfinished_attempts"] == 0
        assert result["total_attempts"] == result["attempts"] + result["unfinished_attempts"]


@pytest.mark.parametrize("adaptive", [None, AdaptiveRisk()])
def test_b2_only_unfinished_and_phase_two_unfinished(adaptive):
    config = mc.MonteCarloConfig(runs=1, risk_levels=(0.01,), min_trading_days=1, adaptive=adaptive)
    for days in ([day(0)], [day(10)]):
        result = mc.ftmo_by_risk(days, [np.arange(len(days))], config)[0.01]
        assert result["attempts"] == result["passes"] == 0
        assert result["unfinished_attempts"] == result["total_attempts"] == 1
        assert result["unfinished_share"] == 1
        assert result["pass_probability"] == 0


def test_b2_card_carries_and_displays_unfinished_share_for_both_modes():
    start = date(2025, 1, 6)
    stamp = datetime(2025, 1, 6, 10, tzinfo=UTC)
    trade = SimpleNamespace(entry_time=stamp, exit_time=stamp + timedelta(hours=1), r_net=0)
    preset = pc.FirmPreset("FTMO", mc.MonteCarloConfig(runs=2, risk_levels=(0.01,)))
    card = pc.compute_card([trade], start, start, preset, pc.PropCardConfig(1, 1))
    for row in card["rows"] + card["adaptive_rows"]:
        assert row["unfinished_attempts"] == row["total_attempts"] == 2
        assert row["unfinished_share"] == 1
    rendered = str(prop_firm_card.card_body({"state": "ready", "card": card}))
    assert "Unfinished attempts" in rendered
    assert rendered.count("100.0 %") == 2
    assert "finished attempts" in rendered


@pytest.mark.parametrize("fixed", [False, True])
@pytest.mark.parametrize("weight", [0.5, 1.0, 2.0])
def test_b3_entry_risk_and_skips_ignore_open_trades_future_result(fixed, weight):
    config = mc.MonteCarloConfig(adaptive=AdaptiveRisk(daily_budget=0.0225))
    results = []
    for future_r in (1, -1.5, -20):
        # The second trade closes first. Its sizing must be identical in all three futures.
        events = ((True, future_r * weight), (True, 1), (False, 1), (False, future_r * weight))
        sample = mc.Day(
            np.array([1, future_r * weight]), events, (0, 1, 1, 0), (weight, 1, 1, weight)
        )
        stats = {}
        status, bal = mc._play_day(
            sample, 100_000, 0.01, config, mc.NO_TARGET, 0, fixed=fixed, stats=stats
        )
        # Remove trade 0's realised P/L: what remains is exactly trade 1's entry risk.
        results.append((bal - 100_000 - future_r * 1_000 * weight, stats.get("skipped", 0)))
        assert status == ("daily" if future_r == -20 else None)
    for result in results:
        assert result == pytest.approx((min(1_000, 2_250 - 1_000 * weight), 0))
