"""Robustness report on R trade lists. Spec: ROADMAP.md › 6.4,
knowledge/topics/testing-and-robustness.md (Kaufman ch. 21)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import pytest

from backtester.analytics.robustness import (
    RobustnessConfig,
    daily_r,
    grid_stats,
    kurtosis,
    plateau_cell,
    plateau_index,
    profitable_share,
    shock_dates,
    shock_report,
    smooth_grid,
    smooth_series,
    stressed_net,
    trade_robustness,
    welch_t,
    without_best,
)

T0 = datetime(2026, 9, 2, 12, tzinfo=UTC)


@dataclass(frozen=True)
class T:
    symbol: str = "XAUUSD"
    entry_time: datetime = T0
    exit_time: datetime = T0
    r_gross: float = 0.0
    r_net: float = 0.0


def t(r_net, r_gross=None, exit_days=0, entry_days=0, symbol="XAUUSD"):
    return T(
        symbol=symbol,
        entry_time=T0 + timedelta(days=entry_days),
        exit_time=T0 + timedelta(days=exit_days),
        r_gross=r_net if r_gross is None else r_gross,
        r_net=r_net,
    )


# --- grid statistics --------------------------------------------------------------------


def test_profitable_share_counts_strictly_positive():
    assert profitable_share([1, -1, 2, 0]) == 0.5
    assert profitable_share([]) is None


def test_grid_stats_robust_when_enough_variants_profit():
    s = grid_stats([1.0, 2.0, 3.0])
    assert s["n"] == 3
    assert s["mean"] == pytest.approx(2.0)
    assert s["std"] == pytest.approx(1.0)  # sample st.dev
    assert s["adjusted"] == pytest.approx(1.0)  # mean - 1 sd
    assert s["profitable_share"] == 1.0
    assert s["robust"] is True


def test_grid_stats_not_robust_below_the_declared_share():
    # 2 of 4 profitable = 0.5 < 0.70
    s = grid_stats([5.0, 5.0, -1.0, -1.0])
    assert s["profitable_share"] == 0.5
    assert s["robust"] is False


def test_grid_stats_share_threshold_is_configurable():
    s = grid_stats([5.0, 5.0, -1.0, -1.0], RobustnessConfig(robust_share=0.5))
    assert s["robust"] is True


def test_grid_stats_single_value_and_empty():
    assert grid_stats([2.0])["std"] == 0.0
    s = grid_stats([])
    assert s["n"] == 0
    assert s["mean"] is None
    assert s["robust"] is False


# --- smoothing and plateau ---------------------------------------------------------------


def test_smooth_series_averages_neighbours_with_edges():
    assert smooth_series([0, 3, 0]) == pytest.approx([1.5, 1.0, 1.5])


def test_smooth_series_none_stays_none_and_is_not_counted():
    out = smooth_series([2, None, 4])
    assert out[1] is None
    assert out[0] == pytest.approx(2.0)  # only itself (neighbour is None)
    assert out[2] == pytest.approx(4.0)


def test_plateau_beats_a_lone_spike():
    # the 9 is a spike (smoothed 3); the flat 5s are a plateau (smoothed 5)
    assert plateau_index([0, 9, 0, 5, 5, 5, 0]) == 4


def test_plateau_index_empty_and_all_none():
    assert plateau_index([]) is None
    assert plateau_index([None, None]) is None


def test_smooth_grid_uses_the_3x3_neighbourhood():
    out = smooth_grid([[0, 0, 0], [0, 9, 0], [0, 0, 0]])
    assert out[1][1] == pytest.approx(1.0)  # 9 / 9 cells
    assert out[0][0] == pytest.approx(2.25)  # 9 / 4 cells in the corner


def test_smooth_grid_ignores_missing_cells():
    out = smooth_grid([[None, 2], [4, None]])
    assert out[0][0] is None
    assert out[0][1] == pytest.approx(3.0)  # mean(2, 4)


def test_plateau_cell_picks_the_best_smoothed_cell():
    grid = [[0] * 7 for _ in range(7)]
    grid[1][1] = 9  # a lone spike: smoothed 9 / 9 = 1
    for r in (3, 4, 5):
        for c in (3, 4, 5):
            grid[r][c] = 4  # a plateau: its centre keeps 4
    assert plateau_cell(grid) == (4, 4)
    assert plateau_cell([[None]]) is None


def test_edge_cells_are_averaged_over_fewer_neighbours():
    # a documented property: a spike in a corner is damped by 4 cells, not 9
    out = smooth_grid([[9, 0], [0, 0]])
    assert out[0][0] == pytest.approx(9 / 4)


# --- tests between periods -----------------------------------------------------------------


def test_welch_t_known_values():
    out = welch_t([1, 2, 3], [4, 5, 6])
    assert out["t"] == pytest.approx(-3.6742, abs=1e-3)
    assert out["df"] == pytest.approx(4.0)
    assert out["significant"] is True  # |t| >= 2


def test_welch_t_equal_samples_is_zero():
    out = welch_t([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    assert out["t"] == pytest.approx(0.0)
    assert out["df"] == pytest.approx(8.0)
    assert out["significant"] is False


def test_welch_t_needs_two_values_each_and_some_variance():
    assert welch_t([1], [1, 2, 3]) is None
    assert welch_t([1, 1, 1], [2, 2, 2]) is None  # no variance anywhere


# --- shape of the returns -------------------------------------------------------------------


def test_kurtosis_of_a_fat_tail_series():
    values = [0.0] * 98 + [10.0, -10.0]  # m2 = 2, m4 = 200 -> 200 / 4
    assert kurtosis(values) == pytest.approx(50.0)


def test_kurtosis_of_two_point_series_is_one():
    assert kurtosis([1, 1, 1, -1, -1, -1]) == pytest.approx(1.0)


def test_kurtosis_undefined_for_few_or_flat_values():
    assert kurtosis([1, 2, 3]) is None
    assert kurtosis([1, 1, 1, 1]) is None


def test_daily_r_sums_trades_by_exit_date_in_order():
    trades = [t(1.0, exit_days=0), t(-0.5, exit_days=0), t(2.0, exit_days=1)]
    assert daily_r(trades) == pytest.approx([0.5, 2.0])
    assert daily_r([]) == []


def test_without_best_removes_the_single_best_trade():
    out = without_best([t(3.0), t(1.0), t(-1.0)])
    assert out["net"] == pytest.approx(3.0)
    assert out["best"] == pytest.approx(3.0)
    assert out["net_without_best"] == pytest.approx(0.0)
    assert without_best([])["net_without_best"] == 0.0


# --- costs ---------------------------------------------------------------------------------


def test_stressed_net_scales_the_whole_cost():
    # gross 1.0, net 0.8: cost 0.2 -> 0.3 at x1.5
    assert stressed_net([t(0.8, r_gross=1.0)], 1.5) == pytest.approx(0.7)


def test_stressed_net_leaves_swap_income_alone():
    # net above gross (swap income): no cost to scale
    assert stressed_net([t(1.1, r_gross=1.0)], 1.5) == pytest.approx(1.1)


def test_stressed_net_factor_one_is_the_net_result():
    trades = [t(0.8, r_gross=1.0), t(-1.2, r_gross=-1.0), t(1.1, r_gross=1.0)]
    assert stressed_net(trades, 1.0) == pytest.approx(sum(x.r_net for x in trades))


def test_stressed_net_rejects_a_factor_below_one():
    with pytest.raises(ValueError):
        stressed_net([t(1.0)], 0.9)


# --- shock days --------------------------------------------------------------------------------


def day(i, rng):
    """A daily bar with range `rng` closing mid-range (true range = range)."""
    d = date(2026, 1, 1) + timedelta(days=i)
    return (d, 100 + rng / 2, 100 - rng / 2, 100.0)


def test_shock_day_is_a_range_above_k_times_the_atr_of_the_days_before():
    days = [day(i, 1.0) for i in range(10)] + [day(10, 4.0), day(11, 3.0)]
    # day 10: 4.0 > 3.5 x 1.0 -> shock; day 11: ATR of days 1..10 = 1.3 -> 4.55 > 3.0
    assert shock_dates(days) == {date(2026, 1, 11)}


def test_shock_day_needs_a_strictly_larger_range():
    days = [day(i, 1.0) for i in range(10)] + [day(10, 3.5)]
    assert shock_dates(days) == set()


def test_no_shock_before_the_atr_has_enough_days():
    days = [day(0, 1.0), day(1, 50.0)]
    assert shock_dates(days) == set()


def test_shock_uses_the_true_range_across_a_gap():
    # a quiet day, then a gap day with a small range but a 5 gap from the previous close
    days = [day(i, 1.0) for i in range(10)]
    d = date(2026, 1, 1) + timedelta(days=10)
    days.append((d, 105.5, 105.0, 105.2))  # range 0.5, true range 5.5
    assert shock_dates(days) == {d}


def test_shock_config_is_respected():
    days = [day(i, 1.0) for i in range(10)] + [day(10, 3.0)]
    assert shock_dates(days) == set()
    assert shock_dates(days, RobustnessConfig(shock_range_atr=2.5)) == {date(2026, 1, 11)}


def test_shock_report_splits_the_result_by_exit_day():
    shock = date(2026, 9, 2)
    shocks = {"XAUUSD": {shock}}
    trades = [
        t(2.0, exit_days=0),  # exits 9/2: shock day
        t(-1.0, exit_days=0),  # exits 9/2
        t(1.0, exit_days=1),  # exits 9/3
        t(5.0, exit_days=0, symbol="GBPUSD"),  # other symbol: no shock set
    ]
    rep = shock_report(trades, shocks)
    assert rep["shock_days_with_trades"] == 1
    assert rep["shock_days_profitable"] == 1
    assert rep["profitable_share"] == 1.0
    assert rep["understated_risk"] is True  # more than half were profitable
    assert rep["net_r_total"] == pytest.approx(7.0)
    assert rep["net_r_shock_days"] == pytest.approx(1.0)
    assert rep["net_r_without_shocks"] == pytest.approx(6.0)
    assert rep["net_r_shocks_reversed"] == pytest.approx(5.0)


def test_shock_report_losing_shock_days_do_not_flag():
    shocks = {"XAUUSD": {date(2026, 9, 2)}}
    rep = shock_report([t(-2.0, exit_days=0), t(1.0, exit_days=1)], shocks)
    assert rep["profitable_share"] == 0.0
    assert rep["understated_risk"] is False
    assert rep["net_r_shocks_reversed"] == pytest.approx(-1.0 + 4.0)


def test_shock_report_without_shock_trades():
    rep = shock_report([t(1.0, exit_days=3)], {"XAUUSD": {date(2026, 9, 2)}})
    assert rep["shock_days_with_trades"] == 0
    assert rep["profitable_share"] is None
    assert rep["understated_risk"] is False
    assert rep["net_r_without_shocks"] == pytest.approx(1.0)


def test_shock_report_shared_dates_are_per_symbol():
    # the same date is a shock for XAUUSD only: a GBPUSD trade that day is a normal one
    shocks = {"XAUUSD": {date(2026, 9, 2)}}
    rep = shock_report([t(3.0, symbol="GBPUSD")], shocks)
    assert rep["net_r_shock_days"] == 0.0


# --- the whole report of one trade list ------------------------------------------------------------


def trades_in_halves():
    # first half (entered 2022): nets 0.9 / 1.1, each with cost 0.2; second half (2027): -0.6 / -0.4
    first = [
        t(
            0.9 + 0.2 * (i % 2),
            r_gross=1.1 + 0.2 * (i % 2),
            entry_days=-1500 + i,
            exit_days=-1500 + i,
        )
        for i in range(6)
    ]
    second = [
        t(-0.6 + 0.2 * (i % 2), r_gross=-0.4 + 0.2 * (i % 2), entry_days=400 + i, exit_days=400 + i)
        for i in range(6)
    ]
    return first + second


def test_trade_robustness_assembles_the_measures():
    rep = trade_robustness(trades_in_halves())
    assert rep["trades"] == 12
    assert rep["net_r"] == pytest.approx(6.0 - 3.0)
    assert rep["net_r_without_best"] == pytest.approx(3.0 - 1.1)
    assert rep["net_r_stressed"] == pytest.approx(3.0 - 12 * 0.1)  # each cost 0.2 -> 0.3
    assert rep["half_first_net_r"] == pytest.approx(6.0)
    assert rep["half_second_net_r"] == pytest.approx(-3.0)
    assert rep["half_first_trades"] == 6
    assert rep["welch_significant"] is True
    assert rep["kurtosis_daily"] is not None
    assert rep["kurtosis_flag"] in (True, False)


def test_trade_robustness_empty_list():
    rep = trade_robustness([])
    assert rep["trades"] == 0
    assert rep["net_r"] == 0.0
    assert rep["welch_t"] is None
    assert rep["kurtosis_flag"] is False


def test_trade_robustness_with_shocks_adds_the_shock_measures():
    rep = trade_robustness([t(1.0), t(2.0, exit_days=5)], shocks={"XAUUSD": {T0.date()}})
    assert rep["shock_days_with_trades"] == 1
    assert rep["net_r_without_shocks"] == pytest.approx(2.0)


def test_halves_use_the_entry_year_and_the_configured_end_year():
    a = t(1.0, entry_days=0)  # 2026-09-02
    cfg = RobustnessConfig(first_half_end_year=2026)
    rep = trade_robustness([a], cfg)
    assert rep["half_first_trades"] == 1
    assert rep["half_second_trades"] == 0


def test_kurtosis_flag_uses_the_threshold():
    values = [0.0] * 98 + [10.0, -10.0]  # kurtosis 50
    trades = [t(v, exit_days=i, entry_days=i) for i, v in enumerate(values)]
    assert trade_robustness(trades)["kurtosis_flag"] is True
    assert trade_robustness(trades, RobustnessConfig(kurtosis_warn=60.0))["kurtosis_flag"] is False


def test_config_validation():
    with pytest.raises(ValueError):
        RobustnessConfig(robust_share=1.5)
    with pytest.raises(ValueError):
        RobustnessConfig(cost_stress=0.5)
    with pytest.raises(ValueError):
        RobustnessConfig(shock_atr_period=0)
    assert math.isclose(RobustnessConfig().cost_stress, 1.5)
