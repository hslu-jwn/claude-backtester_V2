"""Stationarity diagnostics: ADF + half-life, Hurst, variance ratio, lag-correlation grid,
Benjamini-Hochberg, DST-week exclusion, findings. Spec: ROADMAP.md > 11.11; ideas.md T-11.
All series are synthetic with a known answer and a fixed seed."""

from __future__ import annotations

import math
from datetime import date

import numpy as np
import pytest

from backtester.analytics import stationarity as st
from backtester.analytics.stationarity import StationarityConfig

CFG = StationarityConfig()
EPOCH = date(1970, 1, 1)


def day_no(y, m, d):
    return (date(y, m, d) - EPOCH).days


def rw(n, seed=1, sigma=0.001):
    return np.cumsum(np.random.default_rng(seed).normal(0, sigma, n))


def ar1_returns(n, phi, seed=2, sigma=0.001):
    e = np.random.default_rng(seed).normal(0, sigma, n)
    r = np.zeros(n)
    for i in range(1, n):
        r[i] = phi * r[i - 1] + e[i]
    return r


def ou_levels(n, half_life, seed=3):
    phi = 0.5 ** (1 / half_life)
    e = np.random.default_rng(seed).normal(0, 0.01, n)
    y = np.zeros(n)
    for i in range(1, n):
        y[i] = phi * y[i - 1] + e[i]
    return y


# --- ADF + half-life -------------------------------------------------------------------------------


def test_adf_recovers_a_half_life_of_10_bars():
    res = st.adf(ou_levels(20_000, 10), CFG)
    assert res["half_life"] == pytest.approx(10, rel=0.2)
    assert res["lam"] < 0 and res["p_value"] < 0.01 and res["adf_t"] < -5


def test_adf_random_walk_is_not_significant():
    res = st.adf(np.cumsum(np.random.default_rng(5).normal(0, 1, 20_000)), CFG)
    assert res["p_value"] > 0.05


def test_adf_mackinnon_p_value_at_the_known_critical_values():
    # constant-only regression: critical values -2.8621 (5 %) and -3.4393 (1 %), large n
    assert st.mackinnon_p(-2.8621) == pytest.approx(0.05, abs=0.002)
    assert st.mackinnon_p(-3.4393) == pytest.approx(0.01, abs=0.002)
    assert st.mackinnon_p(5.0) == 1.0 and st.mackinnon_p(-50.0) == 0.0


def test_adf_half_life_is_none_when_lambda_is_not_negative():
    rng = np.random.default_rng(1)
    y = np.cumsum(np.full(500, 0.01) + rng.normal(0, 0.0001, 500))
    res = st.adf(y, CFG)
    assert res is not None and (res["lam"] >= 0) == (res["half_life"] is None)


def test_adf_edge_cases_give_none_not_a_crash():
    assert st.adf(np.full(1000, 7.0), CFG) is None  # constant
    assert st.adf(np.arange(10.0), CFG) is None  # too short
    assert st.adf(np.array([]), CFG) is None


# --- Hurst ---------------------------------------------------------------------------------------------


def test_hurst_random_walk_is_one_half():
    assert st.hurst(rw(50_000), CFG) == pytest.approx(0.5, abs=0.05)


def test_hurst_trending_is_above_and_mean_reverting_below_one_half():
    # persistent returns (phi 0.9: runs of ~10 bars) trend over lags 2..100; phi 0.3 only a little
    assert st.hurst(np.cumsum(ar1_returns(50_000, 0.9)), CFG) > 0.55
    assert st.hurst(np.cumsum(ar1_returns(50_000, 0.3)), CFG) > 0.5
    assert st.hurst(np.cumsum(ar1_returns(50_000, -0.5)), CFG) < 0.48


def test_hurst_edge_cases():
    assert st.hurst(np.full(5000, 1.0), CFG) is None
    assert st.hurst(rw(50), CFG) is None


# --- variance ratio ---------------------------------------------------------------------------------------


def test_variance_ratio_random_walk_is_one():
    for q in (2, 5, 10, 20):
        res = st.variance_ratio(rw(50_000, seed=7), q, CFG)
        assert res["vr"] == pytest.approx(1.0, abs=0.1)
        assert abs(res["z"]) < 3.5


def test_variance_ratio_trend_above_and_mean_reversion_below_one():
    up = st.variance_ratio(np.cumsum(ar1_returns(20_000, 0.3)), 5, CFG)
    down = st.variance_ratio(np.cumsum(ar1_returns(20_000, -0.3)), 5, CFG)
    assert up["vr"] > 1.2 and up["z"] > 3 and up["p_value"] < 0.01
    assert down["vr"] < 0.8 and down["z"] < -3 and down["p_value"] < 0.01


def test_variance_ratio_vr2_is_one_plus_first_autocorrelation():
    r = ar1_returns(50_000, 0.3)
    res = st.variance_ratio(np.cumsum(r), 2, CFG)
    rho1 = np.corrcoef(r[1:], r[:-1])[0, 1]
    assert res["vr"] == pytest.approx(1 + rho1, abs=0.01)


def test_variance_ratio_edge_cases():
    assert st.variance_ratio(np.full(1000, 1.0), 5, CFG) is None
    assert st.variance_ratio(rw(8), 5, CFG) is None


# --- lag correlation (non-overlapping pairs) ---------------------------------------------------------------


def test_lag_corr_uses_n_div_k_plus_h_pairs():
    r = np.random.default_rng(1).normal(0, 1, 1000)
    assert st.lag_corr(r, 5, 10, 1)["pairs"] == 1000 // 15 == 66


def test_lag_corr_exact_value_when_next_is_twice_past():
    a = np.random.default_rng(2).normal(0, 1, 100)
    r = np.column_stack([a, 2 * a]).ravel()  # blocks (a, 2a): k = h = 1
    res = st.lag_corr(r, 1, 1, 30)
    assert res["pairs"] == 100 and res["corr"] == pytest.approx(1.0)
    anti = np.column_stack([a, -a]).ravel()
    assert st.lag_corr(anti, 1, 1, 30)["corr"] == pytest.approx(-1.0)


def test_lag_corr_sums_the_blocks_and_t_formula():
    r = np.array([1, 2, 3, 4, 0, 1, 5, 5, 5, 0, 2, 2], float)  # k=2, h=1 -> blocks of 3
    res = st.lag_corr(r, 2, 1, 2)
    past, nxt = [1 + 2, 4 + 0, 5 + 5, 0 + 2], [3, 1, 5, 2]
    corr = np.corrcoef(past, nxt)[0, 1]
    assert res["pairs"] == 4 and res["corr"] == pytest.approx(corr)
    assert res["t"] == pytest.approx(corr * math.sqrt(2) / math.sqrt(1 - corr**2))


def test_lag_corr_too_few_pairs_or_constant_is_none():
    r = np.random.default_rng(3).normal(0, 1, 100)
    assert st.lag_corr(r, 25, 25, 30) is None  # 2 pairs
    assert st.lag_corr(np.zeros(1000), 1, 1, 30) is None


def test_lag_corr_random_returns_are_uncorrelated():
    res = st.lag_corr(np.random.default_rng(9).normal(0, 1, 100_000), 5, 5, 30)
    assert abs(res["t"]) < 3.5


# --- p-values and Benjamini-Hochberg -------------------------------------------------------------------


def test_student_t_p_value_known_points():
    assert st.t_p_value(2.042, 30) == pytest.approx(0.05, abs=0.001)
    assert st.t_p_value(0.0, 10) == pytest.approx(1.0)
    assert st.t_p_value(-1.96, 10_000) == pytest.approx(0.05, abs=0.001)
    assert st.normal_p_value(1.96) == pytest.approx(0.05, abs=0.001)


def test_benjamini_hochberg_hand_example():
    p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
    assert st.benjamini_hochberg(p, 0.05) == [True, True] + [False] * 8
    order = (4, 9, 0, 7, 2, 1, 6, 3, 8, 5)
    shuffled = [p[i] for i in order]
    flags = st.benjamini_hochberg(shuffled, 0.05)
    assert sorted(x for x, f in zip(shuffled, flags, strict=True) if f) == [0.001, 0.008]


def test_benjamini_hochberg_is_a_step_up_procedure():
    # 0.04 alone is above 0.05 / 3 * 2 but the largest p (0.04 <= 0.05) lets all three pass
    assert st.benjamini_hochberg([0.01, 0.04, 0.03], 0.05) == [True, True, True]
    assert st.benjamini_hochberg([0.5, 0.9], 0.05) == [False, False]
    assert st.benjamini_hochberg([], 0.05) == []
    assert st.benjamini_hochberg([None, 0.001, float("nan")], 0.05) == [False, True, False]


# --- DST weeks and symbol end -------------------------------------------------------------------------------


def test_dst_gap_ranges_2016_and_2018():
    assert st.us_only_dst_ranges(2016) == [
        (date(2016, 3, 13), date(2016, 3, 27)),
        (date(2016, 10, 30), date(2016, 11, 6)),
    ]
    assert st.us_only_dst_ranges(2018) == [
        (date(2018, 3, 11), date(2018, 3, 25)),
        (date(2018, 10, 28), date(2018, 11, 4)),
    ]


def test_dst_gap_day_numbers_stop_after_the_last_year():
    days = st.us_only_dst_days(CFG)
    assert day_no(2016, 3, 13) in days and day_no(2016, 3, 26) in days
    assert day_no(2016, 3, 27) not in days and day_no(2016, 3, 12) not in days
    assert day_no(2018, 11, 3) in days and day_no(2018, 11, 4) not in days
    assert max(days) < day_no(2019, 1, 1)
    assert day_no(2015, 3, 15) in days


def test_symbol_end_cuts_ger40():
    assert st.symbol_end("GER40", date(2021, 9, 13), CFG) == date(2020, 6, 12)
    assert st.symbol_end("GER40", date(2019, 1, 1), CFG) == date(2019, 1, 1)
    assert st.symbol_end("XAUUSD", date(2021, 9, 13), CFG) == date(2021, 9, 13)


# --- time of day -------------------------------------------------------------------------------------------


def m5_series(day0, days, step=300):
    """Epoch seconds of M5 bars for `days` days from day number `day0`."""
    return day0 * 86400 + np.arange(days * 288) * step


def test_time_of_day_buckets_mean_and_t():
    secs = m5_series(day_no(2020, 6, 1), 20)
    bucket = (secs % 86400) // 1800
    ret = np.where(bucket == 10, 0.001, 0.0)  # 05:00-05:30 always up
    ret = ret + np.random.default_rng(1).normal(0, 0.0001, len(secs))
    rows = st.time_of_day_rows(secs, np.exp(np.cumsum(ret)), set(), CFG)
    by = {r["bucket"]: r for r in rows}
    assert len(rows) == 48
    assert by["05:00"]["mean_return"] == pytest.approx(0.001, abs=0.0001)
    assert by["05:00"]["mean_t"] > 10 and abs(by["12:00"]["mean_t"]) < 4
    assert by["05:00"]["obs"] == 20 * 6


def test_time_of_day_first_order_autocorrelation_in_bucket():
    secs = m5_series(day_no(2020, 6, 1), 200)
    ret = np.random.default_rng(4).normal(0, 0.001, len(secs))
    bucket = (secs % 86400) // 1800
    for i in range(1, len(ret)):  # momentum inside 10:00-10:30 only
        if bucket[i] == 20 and bucket[i - 1] == 20:
            ret[i] = 0.7 * ret[i - 1] + 0.3 * ret[i]
    rows = st.time_of_day_rows(secs, np.exp(np.cumsum(ret)), set(), CFG)
    by = {r["bucket"]: r for r in rows}
    assert by["10:00"]["ac1"] > 0.5 and by["10:00"]["ac_t"] > 8
    assert abs(by["03:00"]["ac1"]) < 0.2


def test_time_of_day_drops_excluded_days_and_gaps():
    secs = m5_series(day_no(2016, 3, 7), 21)
    closes = np.exp(np.cumsum(np.random.default_rng(1).normal(0, 0.001, len(secs))))
    full = {r["bucket"]: r["obs"] for r in st.time_of_day_rows(secs, closes, set(), CFG)}
    dst = st.us_only_dst_days(CFG)
    cut = {r["bucket"]: r["obs"] for r in st.time_of_day_rows(secs, closes, dst, CFG)}
    assert full["12:00"] - cut["12:00"] == 14 * 6  # 2016-03-13..26
    keep = np.ones(len(secs), bool)
    keep[300] = False  # a missing bar: the return across the hole is not a 5-minute return
    holey = {
        r["bucket"]: r["obs"] for r in st.time_of_day_rows(secs[keep], closes[keep], set(), CFG)
    }
    assert sum(full.values()) - sum(holey.values()) == 2


def test_time_of_day_too_few_obs_gives_no_row():
    secs = m5_series(day_no(2020, 6, 1), 2)
    closes = np.exp(np.cumsum(np.full(len(secs), 1e-4)))
    assert st.time_of_day_rows(secs, closes, set(), CFG) == []


# --- the series driver (periods, random walk reference) ------------------------------------------------------


def test_random_walk_reference_is_seeded_and_matches_sigma():
    a = st.random_walk(5000, 0.002, CFG)
    b = st.random_walk(5000, 0.002, CFG)
    assert np.array_equal(a, b) and len(a) == 5001
    assert np.diff(a).std() == pytest.approx(0.002, rel=0.05)


def test_series_rows_has_three_periods_real_and_reference_and_no_nan():
    y = np.log(100) + rw(6000, seed=11)
    out = st.series_rows("EURUSD", "H1", y, 3000, CFG)
    for fam in ("adf", "hurst", "vr", "lagcorr"):
        rows = out[fam]
        assert {r["period"] for r in rows} == {"whole", "first_half", "second_half"}
        assert {r["source"] for r in rows} == {"real", "random_walk"}
        for r in rows:
            for k, v in r.items():
                assert not (isinstance(v, float) and math.isnan(v)), (fam, k)
    whole = [r for r in out["vr"] if r["period"] == "whole" and r["source"] == "real"]
    assert {r["q"] for r in whole} == set(CFG.vr_qs)
    assert all(r["bars"] == 6000 for r in out["hurst"] if r["period"] == "whole")


def test_series_rows_short_series_gives_no_rows_not_a_crash():
    out = st.series_rows("EURUSD", "D1", rw(20), 10, CFG)
    assert out["adf"] == [] and out["hurst"] == [] and out["vr"] == [] and out["lagcorr"] == []


# --- findings ----------------------------------------------------------------------------------------------


def cell(family, symbol, key, period, p, value, tf="H1"):
    return {"family": family, "symbol": symbol, "timeframe": tf, "cell": key, "period": period,
            "p_value": p, "value": value}  # fmt: skip


def trio(family, symbol, key, p, value, h1=None, h2=None):
    return [
        cell(family, symbol, key, "whole", p, value),
        cell(family, symbol, key, "first_half", 0.2, value if h1 is None else h1),
        cell(family, symbol, key, "second_half", 0.2, value if h2 is None else h2),
    ]


def test_finding_needs_bh_both_halves_same_sign_and_a_sibling():
    cells = (
        trio("vr", "NAS100", "q=5", 1e-9, 0.1)
        + trio("vr", "US500", "q=5", 0.3, 0.05)  # sibling, same sign
        + trio("vr", "XAUUSD", "q=5", 1e-9, 0.1, h2=-0.1)  # halves disagree
        + trio("vr", "GBPJPY", "q=5", 1e-9, 0.1)  # no JPY sibling present
        + [cell("vr", f"S{i}", "q=2", "whole", 0.5, 0.01) for i in range(20)]
    )
    rows, counts = st.find_findings(cells, CFG)
    assert [(r["symbol"], r["cell"]) for r in rows] == [("NAS100", "q=5")]
    assert "US500" in rows[0]["siblings"] and "BH" in rows[0]["reason"]
    assert counts["vr"]["bh_significant"] == 3 and counts["vr"]["findings"] == 1
    assert counts["vr"]["cells"] == 4 + 20


def test_sibling_with_opposite_sign_does_not_count():
    cells = trio("vr", "NAS100", "q=5", 1e-9, 0.1) + trio("vr", "US500", "q=5", 0.3, -0.05)
    assert st.find_findings(cells, CFG)[0] == []


def test_symbol_without_a_group_cannot_be_a_finding():
    assert st.find_findings(trio("vr", "DXY", "q=5", 1e-9, 0.1), CFG)[0] == []


def test_findings_with_nothing_significant_or_no_cells():
    assert st.find_findings([], CFG) == ([], {})
    rows, counts = st.find_findings(trio("adf", "NAS100", "-", 0.5, -0.01), CFG)
    assert rows == [] and counts["adf"]["bh_significant"] == 0


def test_sibling_groups_are_disjoint_and_hold_the_core_symbols():
    seen = [s for g in CFG.sibling_groups.values() for s in g]
    assert len(seen) == len(set(seen))
    assert {"XAUUSD", "XAGUSD", "NAS100", "US500", "GBPJPY", "USDJPY"} <= set(seen)
