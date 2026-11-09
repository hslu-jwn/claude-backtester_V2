"""Gates of submission M15_ALTERNATING_PATH_BATCH. Spec: strategy-alternating-path.md > Gates."""

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

from backtester.analytics.entry_screen import M1Data
from backtester.tools import alternating_path_gates as g


def trade(entry, minutes=60, net=1.0, gross=None, spread=0.0, commission=0.0, symbol="EURUSD"):
    gross = net + spread + commission if gross is None else gross
    return SimpleNamespace(
        symbol=symbol,
        entry_time=entry,
        exit_time=entry + timedelta(minutes=minutes),
        r_gross=gross,
        r_net=net,
        spread_r=spread,
        commission_r=commission,
        swap_r=0.0,
        funding_r=0.0,
        conversion_r=0.0,
    )


T0 = datetime(2020, 1, 6, 10, 0, tzinfo=UTC)  # Monday, London = UTC in winter


def test_cost_components_split_slippage_as_the_rest():
    t = trade(T0, net=0.7, gross=1.0, spread=0.1, commission=0.05)
    assert g.components(t) == pytest.approx((0.1, 0.05, 0.15))


def test_conversion_is_not_a_cost_component():
    t = trade(T0, net=0.7, gross=1.0, spread=0.1, commission=0.05)
    t.conversion_r = -0.02  # inside r_net: r_net = fills - commission + conversion
    assert g.components(t) == pytest.approx((0.1, 0.05, 0.13))


def test_doubling_one_component_subtracts_it_once_more():
    t = trade(T0, net=0.7, gross=1.0, spread=0.1, commission=0.05)
    assert g.net([t]) == pytest.approx(0.7)
    assert g.net([t], "spread") == pytest.approx(0.6)
    assert g.net([t], "commission") == pytest.approx(0.65)
    assert g.net([t], "slippage") == pytest.approx(0.55)
    assert g.net([t], "all") == pytest.approx(0.4)


def test_midpoint_close_belongs_to_the_first_half():
    start, end = date(2020, 1, 1), date(2020, 1, 2)  # midpoint 2020-01-02 00:00 UTC
    mid = datetime(2020, 1, 2, tzinfo=UTC)
    on_mid = trade(mid - timedelta(minutes=60), net=1.0)
    after = trade(mid - timedelta(minutes=59), net=-2.0)
    first, second = g.halves([on_mid, after], start, end)
    assert (first, second) == ([on_mid], [after])


def test_five_best_center_dates_are_removed_from_both_cells():
    days = [T0 + timedelta(days=d) for d in range(7)]  # Mon..Sun, weekdays only matter here
    center = [trade(d, net=n) for d, n in zip(days, (5, 4, 3, 2, 1, -1, -2), strict=True)]
    neighbor = [trade(d, minutes=30, net=1.0) for d in days]
    dates = g.best_dates(center, 5)
    assert dates == {d.date() for d in days[:5]}
    assert g.net(g.without_dates(center, dates)) == pytest.approx(-3)
    assert g.net(g.without_dates(neighbor, dates)) == pytest.approx(2)


def test_london_date_follows_dst():
    summer = datetime(2020, 7, 1, 23, 30, tzinfo=UTC)  # 00:30 London next day
    assert g.london_date(trade(summer)) == date(2020, 7, 2)


def test_daily_series_counts_every_weekday_with_zeros():
    series = g.daily_series([trade(T0, net=2.0)], date(2020, 1, 6), date(2020, 1, 12))
    assert series.tolist() == [2.0, 0.0, 0.0, 0.0, 0.0]


def test_bootstrap_is_seeded_and_exact_on_a_constant_series():
    assert g.block_bootstrap(np.ones(50), 5, 200, 2026014) == pytest.approx(
        {"lower_2_5": 1.0, "lower_5": 1.0, "mean": 1.0}
    )
    x = np.array([1.0, -1.0, 3.0, -2.0, 0.5, 0.0, 2.0, -1.5, 1.0, 0.25])
    assert g.block_bootstrap(x, 5, 500, 7) == g.block_bootstrap(x, 5, 500, 7)
    low = g.block_bootstrap(x, 5, 500, 7)
    assert low["lower_2_5"] <= low["lower_5"] <= low["mean"]


def test_circular_blocks_wrap_around():
    idx = g.block_indices(n=7, block=5, starts=np.array([5, 0]))
    assert idx.tolist() == [5, 6, 0, 1, 2, 0, 1]


def m1(start, minutes, skip=(), broken=()):
    ts = [int((start + timedelta(minutes=i)).timestamp()) for i in range(minutes) if i not in skip]
    n = len(ts)
    high = np.full(n, 1.2)
    for i in broken:
        high[i] = 0.9  # below open / close
    return M1Data(
        np.array(ts, dtype=np.int64), np.full(n, 1.0), high, np.full(n, 0.8), np.full(n, 1.1)
    )


def test_integrity_counts_trades_with_a_missing_or_broken_minute():
    data = m1(T0, 200, skip=(30,), broken=(150,))
    ok = trade(T0 + timedelta(minutes=60), minutes=60)  # minutes 60..119 present
    missing = trade(T0, minutes=60)  # minute 30 missing
    bad = trade(T0 + timedelta(minutes=130), minutes=30)  # minute 150 broken
    edge = trade(
        T0 - timedelta(minutes=29), minutes=59
    )  # (entry, exit] = minutes -29..29: before data
    assert g.integrity_failures([ok, missing, bad], data) == [bad]
    assert g.integrity_failures([edge], data) == [edge]


@pytest.mark.parametrize(
    ("skip", "fails"),
    [(range(10, 13), False), (range(10, 15), False), (range(10, 16), True),
     ((59,), True), ((2, 4, 6, 8, 10, 12), False)],
)
def test_integrity_tolerates_only_short_internal_gaps(skip, fails):
    t = trade(T0)
    assert bool(g.integrity_failures([t], m1(T0, 60, skip=skip))) is fails


def test_integrity_gap_limit_is_configurable_and_invalid_still_fails():
    t = trade(T0)
    assert g.integrity_failures([t], m1(T0, 60, skip=range(10, 13)), max_gap_minutes=2) == [t]
    assert g.integrity_failures([t], m1(T0, 60, broken=(10,))) == [t]
