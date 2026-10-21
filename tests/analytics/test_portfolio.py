"""Portfolio tool maths: daily R, correlation, IDM, weights, merged list, N and V.
Spec: risk-management.md > Portfolio tool (ROADMAP 12.9)."""

from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

from backtester.analytics import portfolio as pf
from backtester.analytics.portfolio import PortfolioConfig
from backtester.analytics.trial_log import append, count_only, make_record
from backtester.risk.monte_carlo import weekdays

START, END = date(2021, 3, 1), date(2021, 3, 26)  # Monday .. Friday, 4 weeks = 20 weekdays


def trade(day: date, r_net: float, hour: int = 12, symbol: str = "X"):
    exit_time = datetime(day.year, day.month, day.day, hour, 0, tzinfo=UTC)
    return SimpleNamespace(
        symbol=symbol, entry_time=exit_time - timedelta(hours=1), exit_time=exit_time,
        r_gross=r_net + 0.1, r_net=r_net, spread_r=0.05, commission_r=0.02, swap_r=-0.03,
        funding_r=0.0, mae_r=-0.5, mfe_r=1.5, entry=100.0, initial_stop=99.0,
        exit_reason="signal",
    )  # fmt: skip


def series_trades(values, start=START):
    days = weekdays(start, END)
    return [trade(d, v) for d, v in zip(days, values, strict=False)]


PATTERN = [1.0, -1.0, 2.0, -2.0] * 5  # 20 weekdays
ORTHO = [1.0, 1.0, -1.0, -1.0] * 5  # exactly uncorrelated with PATTERN


# ----- daily R -------------------------------------------------------------------------------


def test_daily_r_has_one_value_per_weekday_and_sums_trades_of_a_day():
    day = weekdays(START, END)[2]
    t = [trade(day, 1.0), trade(day, 0.5, hour=15), trade(weekdays(START, END)[0], -1.0)]
    d = pf.daily_r(t, START, END)
    assert len(d) == 20
    assert d[0] == -1.0 and d[2] == pytest.approx(1.5) and d.sum() == pytest.approx(0.5)


@pytest.mark.parametrize(
    ("day", "hour", "expected_day"),
    [
        (date(2021, 1, 11), 22, date(2021, 1, 11)),  # winter, 22:30 UTC = 23:30 Prague, same day
        (date(2021, 3, 22), 22, date(2021, 3, 22)),  # still CET
        (date(2021, 3, 29), 22, date(2021, 3, 30)),  # after the switch: 00:30 Prague next day
        (date(2021, 7, 5), 22, date(2021, 7, 6)),  # summer: next Prague day
    ],
)
def test_daily_r_cuts_the_day_at_midnight_prague_with_dst(day, hour, expected_day):
    start, end = day - timedelta(days=7), day + timedelta(days=7)
    t = SimpleNamespace(
        exit_time=datetime(day.year, day.month, day.day, hour, 30, tzinfo=UTC),
        entry_time=datetime(day.year, day.month, day.day, 20, 0, tzinfo=UTC), r_net=2.0,
    )  # fmt: skip
    d = pf.daily_r([t], start, end)
    wd = weekdays(start, end)
    assert d[wd.index(expected_day)] == 2.0 and d.sum() == 2.0


# ----- correlation ---------------------------------------------------------------------------


def test_correlation_plus_one_zero_minus_one():
    a = np.array(PATTERN)
    h = pf.correlation_matrix([a, a * 3, -a, np.array(ORTHO)])
    assert h[0, 1] == pytest.approx(1.0)
    assert h[0, 2] == pytest.approx(-1.0)
    assert h[0, 3] == pytest.approx(0.0, abs=1e-12)
    assert np.allclose(np.diag(h), 1.0) and np.allclose(h, h.T)


def test_correlation_of_a_series_without_variance_is_zero_not_nan():
    h = pf.correlation_matrix([np.array(PATTERN), np.zeros(20)])
    assert h[0, 1] == 0.0 and h[1, 1] == 1.0


def test_rolling_correlation_min_median_max_per_pair():
    a = np.array(PATTERN)
    # first half identical, second half flipped: windows range from +1 to -1
    b = np.concatenate([a[:10], -a[10:]])
    cfg = PortfolioConfig(window_days=10)
    r = pf.rolling_correlation([a, b], cfg)
    pair = r[(0, 1)]
    assert pair["windows"] == 11
    assert pair["max"] == pytest.approx(1.0) and pair["min"] == pytest.approx(-1.0)
    assert pair["min"] <= pair["median"] <= pair["max"]


def test_rolling_correlation_shorter_than_window_has_no_windows():
    r = pf.rolling_correlation([np.arange(5.0), np.arange(5.0)], PortfolioConfig(window_days=10))
    assert r[(0, 1)] == {"windows": 0, "min": None, "median": None, "max": None}


def test_default_config_is_the_spec():
    c = PortfolioConfig()
    assert c.window_days == 126 and c.idm_cap == 2.5 and c.apply_idm is False


# ----- weights and IDM -----------------------------------------------------------------------


@pytest.mark.parametrize("n", [1, 2, 3, 7])
def test_equal_weights_sum_to_one(n):
    w = pf.equal_weights(n)
    assert len(w) == n and sum(w) == pytest.approx(1.0) and len(set(w)) == 1


def test_idm_of_identical_components_is_one():
    assert pf.idm(np.ones((3, 3)), pf.equal_weights(3), PortfolioConfig()) == pytest.approx(1.0)


def test_idm_of_two_uncorrelated_components_is_sqrt_two():
    assert pf.idm(np.eye(2), pf.equal_weights(2), PortfolioConfig()) == pytest.approx(math.sqrt(2))


def test_idm_is_capped():
    assert pf.idm(np.eye(10), pf.equal_weights(10), PortfolioConfig()) == 2.5
    assert pf.idm(np.eye(10), pf.equal_weights(10), PortfolioConfig(idm_cap=4)) == pytest.approx(
        math.sqrt(10)
    )


def test_idm_floors_negative_correlation_at_zero():
    h = np.array([[1.0, -1.0], [-1.0, 1.0]])
    assert pf.idm(h, pf.equal_weights(2), PortfolioConfig()) == pytest.approx(math.sqrt(2))


def test_idm_single_component_is_one():
    assert pf.idm(np.ones((1, 1)), [1.0], PortfolioConfig()) == pytest.approx(1.0)


# ----- merged weighted list ------------------------------------------------------------------


def test_weighted_trades_scale_every_r_field_and_keep_the_rest():
    t = trade(date(2021, 3, 2), 2.0)
    (w,) = pf.weighted_trades([[t]], [0.25], 1.0)
    assert w.r_net == pytest.approx(0.5) and w.r_gross == pytest.approx(0.525)
    assert w.spread_r == pytest.approx(0.0125) and w.swap_r == pytest.approx(-0.0075)
    assert w.mae_r == pytest.approx(-0.125) and w.mfe_r == pytest.approx(0.375)
    assert w.entry == 100.0 and w.exit_time == t.exit_time
    assert t.r_net == 2.0  # the original is untouched


def test_weighted_trades_idm_factor_multiplies_and_list_is_sorted_by_exit():
    a = [trade(date(2021, 3, 3), 1.0)]
    b = [trade(date(2021, 3, 2), 1.0)]
    merged = pf.weighted_trades([a, b], [0.5, 0.5], 1.5)
    assert [m.r_net for m in merged] == [pytest.approx(0.75)] * 2
    assert merged[0].exit_time < merged[1].exit_time


def test_combined_daily_r_is_the_weighted_sum_of_the_parts():
    a, b = series_trades(PATTERN), series_trades(ORTHO)
    res = pf.combine({"a": a, "b": b}, START, END, PortfolioConfig())
    expected = 0.5 * pf.daily_r(a, START, END) + 0.5 * pf.daily_r(b, START, END)
    assert np.allclose(pf.daily_r(res.trades, START, END), expected)
    assert res.weights == [0.5, 0.5] and res.names == ["a", "b"]
    assert res.idm == pytest.approx(math.sqrt(2)) and res.idm_applied == 1.0  # off by default


def test_apply_idm_scales_the_merged_list():
    a, b = series_trades(PATTERN), series_trades(ORTHO)
    off = pf.combine({"a": a, "b": b}, START, END, PortfolioConfig())
    on = pf.combine({"a": a, "b": b}, START, END, PortfolioConfig(apply_idm=True))
    assert on.idm_applied == pytest.approx(math.sqrt(2))
    assert sum(t.r_net for t in on.trades) == pytest.approx(
        math.sqrt(2) * sum(t.r_net for t in off.trades)
    )


def test_combine_reports_whole_period_and_rolling_correlation():
    a = series_trades(PATTERN)
    res = pf.combine({"a": a, "b": series_trades([-v for v in PATTERN])}, START, END,
                     PortfolioConfig(window_days=10))  # fmt: skip
    assert res.corr[0][1] == pytest.approx(-1.0)
    assert res.rolling[(0, 1)]["min"] == pytest.approx(-1.0)
    assert res.component_stats[0]["trades"] == 20


def test_combine_needs_components():
    with pytest.raises(ValueError):
        pf.combine({}, START, END, PortfolioConfig())


# ----- N and V from the component families ---------------------------------------------------


def rec(family, values):
    ts = [
        SimpleNamespace(r_net=v, exit_time=datetime(2021, 3, 1, 12, tzinfo=UTC) + timedelta(days=i))
        for i, v in enumerate(values)
    ]
    return make_record(family, "s", {"k": len(values)}, ["X"], START, END, "mt5", ts)


def test_n_is_the_sum_of_family_counts_including_count_only_lines(tmp_path):
    log = tmp_path / "t.jsonl"
    append(count_only("fam_a", "s", 36, "back-fill"), log)
    append(rec("fam_a", [1.0, -0.5, 2.0]), log)
    append(rec("fam_b", [0.5, 0.2, -0.1, 0.4]), log)
    append(rec("other", [1.0, 2.0, -1.0]), log)
    n, sharpes = pf.component_trials([["fam_a"], ["fam_b"]], [log])
    assert n == 36 + 1 + 1
    assert len(sharpes) == 2  # the count-only line has no Sharpe


def test_prefix_pattern_and_shared_family_counted_once(tmp_path):
    log = tmp_path / "t.jsonl"
    append(count_only("gm_fx", "s", 10), log)
    append(count_only("gm_index", "s", 5), log)
    append(count_only("gap_fade", "s", 7), log)
    n, _ = pf.component_trials([["gm_*"], ["gm_fx", "gap_fade"]], [log])
    assert n == 10 + 5 + 7


def test_trials_are_read_from_several_logs_and_deduplicated(tmp_path):
    one, two = tmp_path / "1.jsonl", tmp_path / "2.jsonl"
    r = rec("f", [1.0, -1.0, 0.5])
    append(r, one)
    append(r, two)  # same key in both: one trial
    append(count_only("f", "s", 4, "x"), two)
    n, sharpes = pf.component_trials([["f"]], [one, two])
    assert n == 5 and len(sharpes) == 1


def test_missing_log_gives_zero_trials(tmp_path):
    assert pf.component_trials([["nothing"]], [tmp_path / "none.jsonl"]) == (0, [])


def test_daily_r_equals_the_monte_carlo_kind_a_days_incl_weekend_and_outside_period():
    from backtester.risk.monte_carlo import build_days

    days = weekdays(START, END)
    t = [trade(days[0], 1.0), trade(days[4], 2.0, hour=23), trade(date(2021, 3, 6), 4.0),
         trade(date(2021, 2, 20), 0.5), trade(date(2021, 4, 20), 0.25)]  # fmt: skip
    mine = pf.daily_r(t, START, END)
    theirs = np.array([float(d.r.sum()) for d in build_days(t, START, END)])
    assert np.allclose(mine, theirs) and mine.sum() == pytest.approx(7.75)


def test_portfolio_daily_r_is_the_weighted_sum_of_the_components_daily_r():
    from backtester.analytics.daily import daily_net_r

    a = [trade(date(2021, 3, 1), 1.0), trade(date(2021, 3, 3), -2.0)]
    b = [trade(date(2021, 3, 1), 4.0), trade(date(2021, 3, 6), 2.0, hour=9)]  # Saturday -> Monday 8
    w = [0.25, 0.75]
    merged = pf.weighted_trades([a, b], w, 1.0)
    expected = w[0] * daily_net_r(a, START, END) + w[1] * daily_net_r(b, START, END)
    assert np.allclose(daily_net_r(merged, START, END), expected)


def test_dsr_on_daily_r_equals_psr0_at_n_1_and_uses_days_as_n():
    from backtester.analytics.daily import daily_net_r
    from backtester.analytics.deflated_sharpe import deflated_sharpe, trade_stats

    ts = [trade(date(2021, 3, 1) + timedelta(days=i), r) for i, r in enumerate([1, -1, 2, -0.5, 1])]
    stats = trade_stats(daily_net_r(ts, START, END))
    assert stats.n == 20  # days, not trades
    res = deflated_sharpe(stats, 1, [])
    assert res.sr0 == 0.0 and res.dsr == pytest.approx(res.psr0) and res.variance == 1 / 20
