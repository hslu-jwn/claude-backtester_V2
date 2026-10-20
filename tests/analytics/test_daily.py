"""Daily net R helper. Spec: risk-management.md > Trial log and deflated Sharpe > Daily Sharpe
(ROADMAP 12.13)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

from backtester.analytics.daily import daily_net_r, weekdays


def tr(exit_utc: datetime, r: float):
    return SimpleNamespace(entry_time=exit_utc - timedelta(hours=1), exit_time=exit_utc, r_net=r)


def utc(*a):
    return datetime(*a, tzinfo=UTC)


# Fri 2021-03-26 .. Wed 03-31 (Prague DST starts Sun 03-28: +1 before, +2 after)
START, END = date(2021, 3, 26), date(2021, 3, 31)


def test_weekdays_skip_the_weekend():
    assert weekdays(START, END) == [date(2021, 3, 26), date(2021, 3, 29), date(2021, 3, 30),
                                    date(2021, 3, 31)]  # fmt: skip
    assert weekdays(date(2021, 3, 27), date(2021, 3, 28)) == []


def test_known_week_with_dst_change_and_weekend_exits():
    trades = [
        tr(utc(2021, 3, 26, 12), 1.0),  # Fri
        tr(utc(2021, 3, 26, 23, 30), 2.0),  # 00:30 Sat in Prague (CET) -> weekend -> Monday
        tr(utc(2021, 3, 28, 10), 4.0),  # Sunday -> Monday
        tr(utc(2021, 3, 29, 22, 30), 8.0),  # 00:30 Tue in Prague (CEST, +2) -> Tuesday
    ]
    d = daily_net_r(trades, START, END)
    assert d.tolist() == [1.0, 6.0, 8.0, 0.0]  # Wednesday is empty = 0


def test_trade_before_the_dst_change_stays_on_its_day_with_the_old_offset():
    # 22:30 UTC = 23:30 CET on Fri 26 Mar: still Friday
    d = daily_net_r([tr(utc(2021, 3, 26, 22, 30), 1.0)], START, END)
    assert d.tolist() == [1.0, 0.0, 0.0, 0.0]


def test_empty_trades_and_empty_period():
    assert daily_net_r([], START, END).tolist() == [0.0] * 4
    assert (
        daily_net_r([tr(utc(2021, 3, 26, 12), 1.0)], date(2021, 3, 27), date(2021, 3, 28)).size == 0
    )


def test_outside_the_period_goes_to_the_first_and_last_day():
    d = daily_net_r([tr(utc(2021, 3, 1, 12), 1.0), tr(utc(2021, 5, 1, 12), 2.0)], START, END)
    assert d.tolist() == [1.0, 0.0, 0.0, 2.0]


def test_sum_is_the_net_r():
    ts = [tr(utc(2021, 3, 29, 9), 0.5), tr(utc(2021, 3, 29, 11), -0.25)]
    assert daily_net_r(ts, START, END).sum() == pytest.approx(0.25)


def test_equals_the_monte_carlo_kind_a_days():
    from backtester.risk.monte_carlo import build_days

    ts = [tr(utc(2021, 3, 26, 12), 1.0), tr(utc(2021, 3, 26, 23, 30), 2.0),
          tr(utc(2021, 3, 28, 10), 4.0), tr(utc(2021, 3, 29, 22, 30), 8.0),
          tr(utc(2021, 2, 1, 9), 0.5), tr(utc(2021, 6, 1, 9), 0.25)]  # fmt: skip
    mine = daily_net_r(ts, START, END)
    theirs = np.array([float(x.r.sum()) for x in build_days(ts, START, END)])
    assert np.allclose(mine, theirs)
