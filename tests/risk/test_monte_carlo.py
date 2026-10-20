"""Monte Carlo report kind A (day reshuffle) and the FTMO pass simulation.
Spec: docs/risk-management.md > Monte Carlo report."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

import numpy as np
import pytest

from backtester.risk import monte_carlo as mc
from backtester.risk.monte_carlo import MonteCarloConfig


@dataclass
class T:
    entry_time: datetime
    exit_time: datetime
    r_net: float
    symbol: str = "XAUUSD"


START = date(2025, 1, 6)  # a Monday (Prague = UTC+1 in winter)


def weekdays(n: int, start: date = START) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def trade(day: date, r: float, hour: int = 10, hours: float = 1.0) -> T:
    t0 = datetime(day.year, day.month, day.day, hour, tzinfo=UTC)
    return T(t0, t0 + timedelta(hours=hours), r)


def one_per_day(rs: list[float]) -> tuple[list[T], date, date]:
    days = weekdays(len(rs))
    return [trade(d, r) for d, r in zip(days, rs, strict=True)], days[0], days[-1]


def cfg(**kw) -> MonteCarloConfig:
    base = {"runs": 20, "fan_paths": 5, "risk_levels": (0.01,)}
    base.update(kw)
    return MonteCarloConfig(**base)


def test_config_validates():
    with pytest.raises(ValueError):
        MonteCarloConfig(runs=0)
    with pytest.raises(ValueError):
        MonteCarloConfig(risk_levels=())
    with pytest.raises(ValueError):
        MonteCarloConfig(risk_levels=(0.0,))
    with pytest.raises(ValueError):
        MonteCarloConfig(month_days=0)


def test_seed_determinism():
    trades, s, e = one_per_day([1, -1, 2, -0.5, 1.5, -1, 0.5, 2, -1, 1] * 3)
    a = mc.run_monte_carlo(trades, s, e, cfg(seed=7))
    b = mc.run_monte_carlo(trades, s, e, cfg(seed=7))
    c = mc.run_monte_carlo(trades, s, e, cfg(seed=8))
    assert a == b
    assert a != c
    p7 = mc.reshuffle_orders(30, cfg(seed=7))
    p8 = mc.reshuffle_orders(30, cfg(seed=8))
    assert not np.array_equal(p7, p8)


def test_reshuffle_keeps_all_days():
    orders = mc.reshuffle_orders(25, cfg(runs=10))
    assert orders.shape == (10, 25)
    for row in orders:
        assert sorted(row) == list(range(25))


def test_reshuffle_keeps_total_r():
    rs = [1, -1, 2, -0.5, 1.5, -1, 0.5]
    trades, s, e = one_per_day(rs)
    days = mc.build_days(trades, s, e)
    for row in mc.reshuffle_orders(len(days), cfg(runs=5)):
        assert sum(r for i in row for r in days[i].r) == pytest.approx(sum(rs))


def test_prague_day_boundary():
    # 2025-06-09 is a Monday; summer Prague = UTC+2: 22:30 UTC is 00:30 on Tuesday.
    mon, tue = date(2025, 6, 9), date(2025, 6, 10)
    late = T(datetime(2025, 6, 9, 20, tzinfo=UTC), datetime(2025, 6, 9, 22, 30, tzinfo=UTC), 1.0)
    early = T(datetime(2025, 6, 9, 20, tzinfo=UTC), datetime(2025, 6, 9, 21, 30, tzinfo=UTC), 2.0)
    days = mc.build_days([late, early], mon, tue)
    assert [len(d.r) for d in days] == [1, 1]
    assert list(days[0].r) == [2.0]  # 21:30 UTC = 23:30 Prague, Monday
    assert list(days[1].r) == [1.0]


def test_weekend_exit_goes_to_next_weekday():
    sat = T(datetime(2025, 1, 11, 10, tzinfo=UTC), datetime(2025, 1, 11, 11, tzinfo=UTC), 1.0)
    days = mc.build_days([sat], date(2025, 1, 6), date(2025, 1, 17))
    assert len(days) == 10
    assert [len(d.r) for d in days].index(1) == 5  # Monday Jan 13


def test_days_keep_order_inside_day():
    d = date(2025, 1, 7)
    a = trade(d, 1.0, hour=9)
    b = trade(d, 2.0, hour=12)
    days = mc.build_days([b, a], d, d)
    assert list(days[0].r) == [1.0, 2.0]


def test_compounding_three_trades():
    trades, s, e = one_per_day([1.0, -1.0, 2.0])
    res = mc.run_monte_carlo(trades, s, e, cfg())
    st = res["risks"][0.01]["stats"]
    expect = 100_000 * 1.01 * 0.99 * 1.02
    assert st["final_balance"]["p50"] == pytest.approx(expect)
    assert st["final_balance"]["p5"] == pytest.approx(expect)
    assert st["gain_pct"]["p50"] == pytest.approx(expect / 1000 - 100)


def test_monthly_gains_blocks():
    bal = [100.0 * 1.01**i for i in range(43)]  # start + 42 days
    g = mc.monthly_gains(bal, 21)
    assert len(g) == 2
    assert g[0] == pytest.approx(1.01**21 - 1)
    assert len(mc.monthly_gains(bal[:42], 21)) == 1  # 41 days -> one full month
    assert mc.monthly_gains(bal[:10], 21) == []


def test_monthly_stats_in_result():
    trades, s, e = one_per_day([1.0] * 42)
    st = mc.run_monte_carlo(trades, s, e, cfg())["risks"][0.01]["stats"]
    assert st["months"] == 2
    assert st["monthly_gain_pct"]["mean"] == pytest.approx((1.01**21 - 1) * 100)
    assert st["profitable_months"] == 1.0


def test_all_winners():
    trades, s, e = one_per_day([1.0] * 40)
    r = mc.run_monte_carlo(trades, s, e, cfg())["risks"][0.01]
    assert r["stats"]["max_dd_pct"]["median"] == 0.0
    assert r["stats"]["p_dd_over_alert"] == 0.0
    assert r["stats"]["worst_day_pct"] > 0
    assert r["stats"]["longest_losing_streak"]["median"] == 0
    f = r["ftmo"]
    assert f["attempts"] > 0
    assert f["pass_probability"] == 1.0
    assert f["fail_daily"] == 0 and f["fail_max"] == 0
    assert f["funded_lost_probability"] == 0.0


def test_all_losers_fail_by_max_loss():
    trades, s, e = one_per_day([-1.0] * 30)
    r = mc.run_monte_carlo(trades, s, e, cfg())["risks"][0.01]
    f = r["ftmo"]
    # 0.99**11 = 0.895 -> attempt over after 11 days; 30 days -> 2 finished, third open
    assert f["attempts"] == 2 * 20
    assert f["pass_probability"] == 0.0
    assert f["fail_max"] == 2 * 20 and f["fail_daily"] == 0
    assert f["median_days_to_pass"] is None
    assert r["stats"]["longest_losing_streak"]["median"] == 30
    assert r["stats"]["p_dd_over_alert"] == 1.0


def test_single_day_minus_six_percent_fails_daily():
    trades, s, e = one_per_day([-6.0])
    f = mc.run_monte_carlo(trades, s, e, cfg())["risks"][0.01]["ftmo"]
    assert f["attempts"] == 20
    assert f["fail_daily"] == 20 and f["fail_max"] == 0


def _play(trades, day, risk, **kw):
    days = mc.build_days(trades, day, day)
    return mc._play_day(days[0], 100_000.0, risk, cfg(**kw), 1e18, 0)[0]


def test_overlapping_open_trades_count_two_percent():
    d = date(2025, 1, 7)
    a = trade(d, 0.5, hour=10, hours=2)  # 10-12
    b = trade(d, 0.5, hour=11, hours=2)  # 11-13, overlaps a
    assert _play([a, b], d, 0.01, daily_loss=0.02) == "daily"
    assert _play([a, b], d, 0.01, daily_loss=0.021) is None
    c = trade(d, 0.5, hour=12, hours=1)  # starts when a ended: no overlap, worst is 1 %
    assert _play([a, c], d, 0.01, daily_loss=0.011) is None
    assert _play([a, c], d, 0.01, daily_loss=0.01) == "daily"


def test_open_trade_counted_at_realised_loss_beyond_one_r():
    d = date(2025, 1, 7)
    t = trade(d, -1.3)
    assert _play([t], d, 0.01, daily_loss=0.013) == "daily"
    assert _play([t], d, 0.01, daily_loss=0.014) is None


def test_trade_open_from_previous_day_counts_from_day_start():
    d0, d1 = date(2025, 1, 7), date(2025, 1, 8)
    t = T(datetime(2025, 1, 7, 15, tzinfo=UTC), datetime(2025, 1, 8, 12, tzinfo=UTC), 1.0)
    other = trade(d1, 0.5, hour=8, hours=1)  # inside t's lifetime
    days = mc.build_days([t, other], d0, d1)
    for loss, expect in ((0.02, "daily"), (0.021, None)):
        got = mc._play_day(days[1], 100_000.0, 0.01, cfg(daily_loss=loss), 1e18, 0)[0]
        assert got == expect  # t open from day start (1 %) plus other (1 %) = 2 %


def _seq(rs):
    days = mc.build_days(*one_per_day(rs))
    return [(i, d) for i, d in enumerate(days) if len(d.r)]


def test_min_trading_days_before_pass():
    c = cfg()
    seq = _seq([10.0, 0.0, 0.0, 0.0, 0.0])  # +10 % on day 1 at 1 % risk
    status, nxt, end_pos = mc._run_phase(seq, 0, 0.01, c.p1_target, c)
    assert status == "pass" and end_pos == 3 and nxt == 4
    short = _seq([10.0, 0.0, 0.0])
    assert mc._run_phase(short, 0, 0.01, c.p1_target, c)[0] == "open"


def test_phase_passes_at_target_on_closed_balance():
    c = cfg(min_trading_days=1)
    seq = _seq([5.0, 5.0, 5.0])
    status, _, end_pos = mc._run_phase(seq, 0, 0.01, c.p1_target, c)
    assert status == "pass" and end_pos == 1  # 1.05**2 = 1.1025 >= 1.10


def test_empty_trade_list():
    res = mc.run_monte_carlo([], date(2025, 1, 6), date(2025, 1, 31), cfg())
    r = res["risks"][0.01]
    assert r["stats"]["final_balance"]["p50"] == 100_000
    assert r["stats"]["trades_per_month"] == 0
    assert r["ftmo"]["attempts"] == 0
    assert r["ftmo"]["pass_probability"] == 0.0
    assert r["fan"]["actual"][-1] == 100_000


def test_risk_levels_side_by_side():
    trades, s, e = one_per_day([1.0, -1.0, 2.0, -0.5] * 6)
    res = mc.run_monte_carlo(trades, s, e, MonteCarloConfig(runs=10, fan_paths=3))
    assert list(res["risks"]) == [0.005, 0.01, 0.015]
    finals = [res["risks"][k]["stats"]["final_balance"]["p50"] for k in res["risks"]]
    assert finals[0] < finals[1] < finals[2]


def test_fan_structure():
    trades, s, e = one_per_day([1.0, -1.0, 2.0, -0.5] * 5)
    fan = mc.run_monte_carlo(trades, s, e, cfg())["risks"][0.01]["fan"]
    n = 20
    assert len(fan["days"]) == n + 1
    assert len(fan["p5"]) == len(fan["p50"]) == len(fan["p95"]) == n + 1
    assert len(fan["paths"]) == 5 and all(len(p) == n + 1 for p in fan["paths"])
    assert len(fan["actual"]) == n + 1 and fan["actual"][0] == 100_000
    assert fan["best"][-1] >= fan["worst"][-1]
    assert all(
        lo <= mid <= hi for lo, mid, hi in zip(fan["p5"], fan["p50"], fan["p95"], strict=True)
    )


def test_stats_constants_from_trades():
    trades, s, e = one_per_day([2.0, -1.0, -1.0, 1.0])
    st = mc.run_monte_carlo(trades, s, e, cfg())["risks"][0.01]["stats"]
    assert st["win_rate"] == 0.5
    assert st["expectancy_r"] == pytest.approx(0.25)
    assert st["profit_factor"] == pytest.approx(1.5)


# ----- funded account loss rate (ROADMAP 12.12) -----------------------------------------


def test_funded_exact_case_winning_every_day():
    # +1 R each day at 1 %: 1.01**10 = 1.1046 passes P1 on day 10, 1.01**5 = 1.0510 passes P2
    # on day 5 more (15 days), then 126 funded days without a loss; the second attempt (days
    # 142..200) passes again but its funded watch is cut off by the data end
    trades, s, e = one_per_day([1.0] * 200)
    f = mc.run_monte_carlo(trades, s, e, cfg(runs=3))["risks"][0.01]["ftmo"]
    assert f["attempts"] == 6 and f["passes"] == 6
    assert f["median_days_to_pass"] == 15.0
    assert f["funded_observed"] == 3 and f["funded_lost_probability"] == 0.0


def test_funded_exact_case_losing_every_day():
    # -1 R each day at 1 %: 0.99**10 = 0.9044 is above the 10 % max loss, 0.99**11 = 0.8953 is
    # below it: every attempt fails after 11 days (220 days = 20 attempts), no account funded
    trades, s, e = one_per_day([-1.0] * 220)
    f = mc.run_monte_carlo(trades, s, e, cfg(runs=2))["risks"][0.01]["ftmo"]
    assert f["attempts"] == 40 and f["fail_max"] == 40 and f["passes"] == 0
    assert f["funded_observed"] == 0


def test_funded_loss_rate_is_low_for_a_strong_strategy():
    # one trade a day, 60 % win rate at 1:1 (+0.2 R per trade), 0.5 % risk. Independent estimate:
    # the funded account must fall 10 % = 20 R below its start within 126 trades (daily 5 %
    # needs 10 losses in a day: impossible with one trade). The R walk has drift +25 R and
    # sd 11 R over 126 trades; touching -20 R is a ~4-sigma event, far below 1 %.
    rng = np.random.default_rng(7)
    rs = [1.0 if x < 0.6 else -1.0 for x in rng.random(1500)]
    trades, s, e = one_per_day(rs)
    f = mc.run_monte_carlo(trades, s, e, cfg(runs=60, risk_levels=(0.005,)))["risks"][0.005]["ftmo"]
    assert f["funded_observed"] > 100
    assert f["funded_lost_probability"] < 0.02


def test_funded_loss_rate_is_high_for_a_losing_strategy():
    # 40 % win rate at 1:1 (-0.2 R per trade), 1 % risk: the 10 % limit is 10 R, drift -25 R
    rng = np.random.default_rng(7)
    rs = [1.0 if x < 0.40 else -1.0 for x in rng.random(1500)]
    trades, s, e = one_per_day(rs)
    f = mc.run_monte_carlo(trades, s, e, cfg(runs=60, risk_levels=(0.01,)))["risks"][0.01]["ftmo"]
    assert f["funded_observed"] == 0 or f["funded_lost_probability"] > 0.9
