"""Scorecard of a trade list and its warning flags. Spec: research-runner.md > Scorecard,
Warning flags (ROADMAP 6.1 + 6.2)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.analytics.scorecard import (
    FLAG_HALF,
    FLAG_HIGH_WIN_SMALL_EDGE,
    FLAG_STRESSED,
    FLAG_TEST_FAILED,
    FLAG_TOO_FEW,
    FLAG_WITHOUT_BEST,
    SCORE_KEYS,
    ScorecardConfig,
    flags,
    scorecard,
)


def trade(year=2020, r_net=1.0, r_gross=None, day=1):
    entry = datetime(year, 3, day, 14, 30, tzinfo=UTC)
    return SimpleNamespace(
        symbol="NAS100",
        entry_time=entry,
        exit_time=entry + timedelta(hours=2),
        r_gross=r_net if r_gross is None else r_gross,
        r_net=r_net,
        planned_r=None,
    )


def row(**kw):
    """A scorecard row that triggers no flag, with `kw` changed."""
    base = {
        "trades": 200, "win_rate": 0.5, "avg_r": 0.2, "net_r": 40.0,
        "half_first_net_r": 20.0, "half_second_net_r": 20.0,
        "net_r_stressed": 30.0, "net_r_without_best": 35.0, "period": "development",
    }  # fmt: skip
    return {**base, **kw}


# --- numbers ---------------------------------------------------------------------------


def test_numbers_of_a_small_list():
    trades = [trade(2020, 2.0, day=1), trade(2020, -1.0, day=2), trade(2021, 1.0, day=3),
              trade(2021, -1.0, day=4)]  # fmt: skip
    s = scorecard(trades, ScorecardConfig(), date(2020, 1, 1), date(2021, 12, 31))
    assert set(SCORE_KEYS) <= set(s)
    assert s["trades"] == 4
    assert s["win_rate"] == 0.5
    assert s["net_r"] == pytest.approx(1.0)
    assert s["avg_r"] == pytest.approx(0.25)
    assert s["profit_factor"] == pytest.approx(3.0 / 2.0)  # gross wins / gross losses
    # exits in time order: +2, -1, +1, -1 -> peak 2, then 1, then 2 -> 1, drawdown 1
    assert s["max_dd_r"] == pytest.approx(1.0)
    assert s["net_r_without_best"] == pytest.approx(-1.0)  # 1 - 2


def test_halves_split_at_the_middle_year_of_the_period():
    trades = [trade(2018, 1.0), trade(2019, 2.0), trade(2020, -0.5), trade(2021, 4.0)]
    s = scorecard(trades, ScorecardConfig(), date(2018, 1, 1), date(2021, 12, 31))
    # middle year (2018 + 2021) // 2 = 2019: entries up to 2019 are the first half
    assert s["half_first_net_r"] == pytest.approx(3.0)
    assert s["half_second_net_r"] == pytest.approx(3.5)


def test_halves_without_a_period_use_the_first_and_last_trade_year():
    trades = [trade(2020, 1.0), trade(2022, 5.0)]
    s = scorecard(trades, ScorecardConfig())
    assert s["half_first_net_r"] == pytest.approx(1.0)  # middle year 2021
    assert s["half_second_net_r"] == pytest.approx(5.0)


def test_profit_factor_is_none_without_a_losing_trade():
    s = scorecard([trade(r_net=1.0), trade(r_net=2.0)], ScorecardConfig())
    assert s["profit_factor"] is None
    assert s["win_rate"] == 1.0


def test_costs_x_1_5_scales_the_cost_of_each_trade():
    # gross 1.0, net 0.8 -> cost 0.2 -> stressed 1.0 - 0.3 = 0.7
    s = scorecard([trade(r_net=0.8, r_gross=1.0)], ScorecardConfig())
    assert s["net_r_stressed"] == pytest.approx(0.7)
    assert scorecard([trade(r_net=0.8, r_gross=1.0)], ScorecardConfig(cost_stress=2.0))[
        "net_r_stressed"
    ] == pytest.approx(0.6)


def test_empty_list():
    s = scorecard([], ScorecardConfig(), date(2020, 1, 1), date(2021, 1, 1))
    assert s["trades"] == 0
    assert s["win_rate"] is None and s["avg_r"] is None and s["profit_factor"] is None
    assert s["net_r"] == 0.0 and s["max_dd_r"] == 0.0
    assert s["half_first_net_r"] == 0.0 and s["half_second_net_r"] == 0.0
    assert s["net_r_stressed"] == 0.0 and s["net_r_without_best"] == 0.0


def test_a_half_without_trades_is_zero():
    s = scorecard([trade(2018, 3.0)], ScorecardConfig(), date(2018, 1, 1), date(2022, 1, 1))
    assert s["half_first_net_r"] == pytest.approx(3.0)
    assert s["half_second_net_r"] == 0.0


# --- flags -----------------------------------------------------------------------------


def test_a_clean_row_has_no_flag():
    assert flags(row(), ScorecardConfig()) == []


def test_too_few_trades_below_the_minimum_only():
    cfg = ScorecardConfig(min_trades=100)
    assert FLAG_TOO_FEW in flags(row(trades=99), cfg)
    assert FLAG_TOO_FEW not in flags(row(trades=100), cfg)
    assert FLAG_TOO_FEW in flags(row(trades=30), ScorecardConfig(min_trades=50))


def test_high_win_rate_with_a_small_edge():
    cfg = ScorecardConfig()
    assert FLAG_HIGH_WIN_SMALL_EDGE in flags(row(win_rate=0.70, avg_r=0.09), cfg)  # at 70 %
    assert FLAG_HIGH_WIN_SMALL_EDGE not in flags(row(win_rate=0.69, avg_r=0.09), cfg)
    assert FLAG_HIGH_WIN_SMALL_EDGE not in flags(row(win_rate=0.80, avg_r=0.10), cfg)  # 0.1 is ok


def test_one_half_not_profitable():
    cfg = ScorecardConfig()
    assert FLAG_HALF in flags(row(half_first_net_r=0.0), cfg)
    assert FLAG_HALF in flags(row(half_second_net_r=-1.0), cfg)
    assert FLAG_HALF not in flags(row(half_first_net_r=0.01), cfg)


def test_not_profitable_with_costs_x_1_5():
    assert FLAG_STRESSED in flags(row(net_r_stressed=0.0), ScorecardConfig())
    assert FLAG_STRESSED not in flags(row(net_r_stressed=0.1), ScorecardConfig())


def test_not_profitable_without_the_best_trade():
    assert FLAG_WITHOUT_BEST in flags(row(net_r_without_best=-0.1), ScorecardConfig())
    assert FLAG_WITHOUT_BEST not in flags(row(net_r_without_best=0.1), ScorecardConfig())


def test_test_failed_only_on_a_test_row():
    cfg = ScorecardConfig()
    assert FLAG_TEST_FAILED in flags(row(period="test", net_r=0.0, verdict="green"), cfg)
    assert FLAG_TEST_FAILED in flags(row(period="test", net_r=5.0, verdict="red"), cfg)
    assert FLAG_TEST_FAILED not in flags(row(period="test", net_r=5.0, verdict="yellow"), cfg)
    assert FLAG_TEST_FAILED not in flags(row(period="development", net_r=-5.0), cfg)


def test_row_without_numbers_gets_no_error():
    # an empty run: win rate / average R are None
    out = flags(row(trades=0, win_rate=None, avg_r=None, net_r=0.0), ScorecardConfig())
    assert FLAG_TOO_FEW in out and FLAG_HIGH_WIN_SMALL_EDGE not in out


def test_config_rejects_nonsense():
    with pytest.raises(ValueError):
        ScorecardConfig(min_trades=-1)
    with pytest.raises(ValueError):
        ScorecardConfig(high_win_rate=1.5)
    with pytest.raises(ValueError):
        ScorecardConfig(cost_stress=0.5)
