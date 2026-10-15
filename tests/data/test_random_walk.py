"""Random-walk M1 paths. Spec: risk-management.md > Monte Carlo report > D.

Hand-built profile (NAS100-like: closed 20:00-22:00 UTC and on weekends), no market data.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import numpy as np
import pandas as pd

from backtester.data.random_walk import (
    HOURS,
    MINUTES_PER_DAY,
    RandomWalkConfig,
    VolatilityProfile,
    generate_frame,
    write_path,
)
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.trend_following.config import TrendFollowingConfig

CONFIG = RandomWalkConfig(years=1)
SIGMA = tuple(0.0004 if 13 <= h < 20 else 0.0002 for h in range(HOURS))
BREAK = 0.001


def _presence() -> tuple[tuple[float, ...], ...]:
    rows = []
    for weekday in range(7):
        row = [0.0] * MINUTES_PER_DAY
        if weekday < 5:
            for minute in range(MINUTES_PER_DAY):
                if not 20 * 60 <= minute < 22 * 60:
                    row[minute] = 1.0
        rows.append(tuple(row))
    return tuple(rows)


PROFILE = VolatilityProfile(
    start_price=18000.0,
    digits=2,
    sigma=SIGMA,
    wick=(0.0001,) * HOURS,
    break_sigma=(BREAK,) * HOURS,
    presence=_presence(),
)


def test_deterministic_per_seed_and_path_index():
    a = generate_frame(PROFILE, "NAS100", 3, CONFIG)
    b = generate_frame(PROFILE, "NAS100", 3, CONFIG)
    pd.testing.assert_frame_equal(a, b)
    c = generate_frame(PROFILE, "NAS100", 4, CONFIG)
    assert not np.allclose(a["bid_close"].to_numpy()[:1000], c["bid_close"].to_numpy()[:1000])
    d = generate_frame(PROFILE, "NAS100", 3, replace(CONFIG, seed=43))
    assert not np.allclose(a["bid_close"].to_numpy()[:1000], d["bid_close"].to_numpy()[:1000])


def test_no_candles_in_closed_hours_and_weekends():
    f = generate_frame(PROFILE, "NAS100", 0, CONFIG)
    ts = f["ts"]
    assert (ts.dt.weekday < 5).all()
    assert not ts.dt.hour.isin([20, 21]).any()
    assert ts.dt.tz is not None and str(ts.dt.tz) == "UTC"
    assert (ts.dt.second == 0).all() and ts.is_monotonic_increasing and ts.is_unique


def test_ohlc_consistent_and_rounded():
    f = generate_frame(PROFILE, "NAS100", 1, CONFIG)
    top = f[["bid_open", "bid_close"]].max(axis=1)
    bottom = f[["bid_open", "bid_close"]].min(axis=1)
    assert (f["bid_high"] >= top).all() and (f["bid_low"] <= bottom).all()
    assert (f["bid_high"] >= f["bid_low"]).all()
    assert np.allclose(f["bid_close"], f["bid_close"].round(2))
    assert f["ask_close"].isna().all()  # histdata layout


def test_per_hour_stdev_matches_profile_and_drift_is_zero():
    f = generate_frame(PROFILE, "NAS100", 2, RandomWalkConfig(years=2))
    inside = f["ts"].diff().dt.total_seconds() == 60
    ret = np.log(f["bid_close"] / f["bid_open"])
    for hour in (3, 10, 15, 18):
        sel = ret[inside & (f["ts"].dt.hour == hour)]
        assert abs(sel.std() / SIGMA[hour] - 1) < 0.05
    assert abs(ret.mean()) < 3 * ret.std() / np.sqrt(len(ret))


def test_open_equals_previous_close_inside_a_session():
    f = generate_frame(PROFILE, "NAS100", 0, CONFIG)
    inside = (f["ts"].diff().dt.total_seconds() == 60).to_numpy()
    prev_close = f["bid_close"].shift(1)
    assert np.allclose(f["bid_open"][inside], prev_close[inside], atol=0.011)


def test_breaks_gap_with_break_sigma():
    f = generate_frame(PROFILE, "NAS100", 5, RandomWalkConfig(years=2))
    gap = f["ts"].diff().dt.total_seconds() > 300
    jump = np.log(f["bid_open"] / f["bid_close"].shift(1))[gap]
    assert len(jump) > 300
    assert abs(jump.std() / BREAK - 1) < 0.12


def test_from_candles_recovers_profile_and_presence():
    f = generate_frame(PROFILE, "NAS100", 7, RandomWalkConfig(years=2))
    measured = VolatilityProfile.from_candles(f, 2)
    assert abs(measured.sigma[15] / SIGMA[15] - 1) < 0.05
    assert abs(measured.sigma[3] / SIGMA[3] - 1) < 0.05
    assert abs(measured.break_sigma[0] / BREAK - 1) < 0.2
    assert measured.presence[6][600] == 0.0  # Sunday closed
    assert measured.presence[2][21 * 60] == 0.0  # closed hour
    assert measured.presence[2][600] > 0.9
    assert measured.start_price == f["bid_close"].iloc[-1]


def test_smoke_runs_a_strategy_on_a_synthetic_path(tmp_path):
    start, end = date(2024, 1, 1), date(2024, 2, 11)
    sources = write_path(PROFILE, "NAS100", 0, tmp_path, CONFIG, start, end)
    assert len(sources.cached_days("NAS100")) == 42  # empty weekend days count as cached
    result = run_backtests(
        ["NAS100"],
        date(2024, 1, 29),
        end,
        RunSettings(strategy=TrendFollowingConfig()),
        sources,
    )
    run = result.runs["NAS100"]
    assert (run.first_day, run.last_day) == (date(2024, 1, 29), end)
