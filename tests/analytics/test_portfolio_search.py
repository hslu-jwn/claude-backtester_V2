from datetime import date, timedelta
from time import perf_counter

import numpy as np
import pytest

from backtester.analytics.portfolio_search import Member, metrics, search, set_id


def member(name, values, offset=0):
    days = tuple(date(2020, 1, 1) + timedelta(days=i + offset) for i in range(len(values)))
    return Member(name, days, tuple(values))


def test_opposites_and_leave_one_out():
    a, b = member("a", [1, -2, 3]), member("b", [-1, 2, -3])
    row = search([a, b])[0]
    assert row["daily_r"] == [0, 0, 0]
    assert row["net_r"] == row["max_dd_r"] == 0
    assert row["net_dd"] is None
    assert row["avg_correlation"] == pytest.approx(-1)
    assert row["leave_one_out"]["b"]["net_r"] == 2
    assert row["leave_one_out"]["a"]["net_r"] == -2
    assert row["flags"] == ["fewer_than_250_common_days"]
    assert row["id"] == set_id(["b", "a"])


def test_metrics_hand_calculated():
    days = [date(2020, 1, i) for i in range(1, 6)]
    result = metrics(days, np.array([-2, 1, 3, -1, -1]))
    assert result["net_r"] == 0
    assert result["max_dd_r"] == 2
    assert result["worst_month"] == 0
    assert result["longest_dd_days"] == 2
    assert result["sharpe"] == 0


def test_intersection_and_loo_realign():
    a, b = member("a", [1, 2, 3]), member("b", [4, 5], 1)
    row = search([a, b])[0]
    assert row["daily_r"] == [3, 4]
    assert row["dropped_days"] == 1
    assert row["dropped_by_member"] == {"a": 1, "b": 0}
    assert row["leave_one_out"]["b"]["net_r"] == 6


@pytest.mark.parametrize(
    "bad",
    [
        Member("bad", (date(2021, 9, 14),), (1,)),
        Member("bad", (date(2020, 1, 1),), (float("nan"),)),
        Member("bad", (date(2020, 1, 1),) * 2, (1, 2)),
        Member("bad", (date(2020, 1, 1),), (1,), period="test"),
    ],
)
def test_refuse_bad_members(bad):
    with pytest.raises(ValueError):
        search([member("a", [1]), bad])


def test_empty_intersection_is_flagged():
    row = search([member("a", [1]), member("b", [1], 10)])[0]
    assert row["common_days"] == 0
    assert row["sharpe"] is None


def test_limits_and_duplicate_identity():
    for pool in (
        [member("a", [1])],
        [member("a", [1])] * 2,
        [member(str(i), [1]) for i in range(13)],
    ):
        with pytest.raises(ValueError):
            search(pool)


def test_twelve_members_fast_and_order_stable():
    days = tuple(date(2000, 1, 1) + timedelta(days=i) for i in range(3000))
    pool = [Member(str(i), days, tuple([i, -1, 2, 0] * 750), symbols=(f"S{i}",)) for i in range(12)]
    regimes = {f"S{i}": dict.fromkeys(days, "sideways / low") for i in range(12)}
    start = perf_counter()
    rows = search(pool, regimes=regimes)
    assert len(rows) == 781
    assert perf_counter() - start < 30
    assert set_id(["ab", "c"]) != set_id(["a", "bc"])


def test_sharpe_and_month_boundaries():
    result = metrics([date(2020, 1, 31), date(2020, 2, 3)], np.array([1, 3]))
    assert result["sharpe"] == pytest.approx(2 / np.sqrt(2) * np.sqrt(252))
    assert result["worst_month"] == 1


def test_zero_days_are_kept_and_constants_have_zero_correlation():
    row = search([member("a", [0, 1, 0, -1]), member("b", [0, 0, 0, 0])])[0]
    assert row["common_days"] == 4
    assert row["avg_correlation"] == 0
    assert row["daily_r"] == [0, 0.5, 0, -0.5]


def test_regimes_are_separate_symbol_attributions():
    a = member("a", [2, -1])
    b = member("b", [0, 3])
    labels = {"X": {a.days[0]: "trend_up / low"}, "Y": {a.days[0]: "sideways / high"}}
    row = search([a, b], regimes=labels)[0]
    assert row["regimes"]["X"]["trend_up / low"] == {"days": 1, "net_r": 1, "r_per_day": 1}
    assert row["regimes"]["Y"]["sideways / high"]["net_r"] == 1
    assert row["regimes"]["X"]["unknown"]["net_r"] == 1
