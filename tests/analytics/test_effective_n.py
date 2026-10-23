"""Cases: identical/independent/anticorrelated/constant trials; missing/faulty data;
disjoint, overlapping, opposite-side and zero-duration trades; Prague midnight/DST.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest

from backtester.analytics.effective_n import effective_trials, trade_uniqueness


def test_trial_counts():
    x = np.arange(10.0)
    assert effective_trials(np.column_stack((x, x, x)))["n_eff"] == pytest.approx(1)
    result = effective_trials(np.random.default_rng(42).normal(size=(20000, 5)))
    assert result["n"] == 5 and result["n_eff"] == pytest.approx(5, abs=0.2)
    assert effective_trials(np.ones((10, 3)))["n_eff"] == pytest.approx(1)
    assert effective_trials(x[:, None])["n_eff"] == 1
    assert effective_trials(np.column_stack((x, -x)))["n_eff"] is None
    assert effective_trials(np.empty((0, 2)))["reason"]
    with pytest.raises(ValueError):
        effective_trials([[np.inf, 1]])


def test_different_constant_decimals_are_uncorrelated():
    result = effective_trials(np.tile([0.1, 0.3], (240, 1)))
    assert result["n_eff"] == 2
    assert result["mean_correlation"] == 0


def trade(start, end):
    return SimpleNamespace(entry_time=start, exit_time=end)


def test_hand_built_uniqueness():
    a = datetime(2024, 1, 1, 12, tzinfo=UTC)
    # Trades A on days 1,2; B on day 2; C on day 4.
    trades = [
        trade(a, a + timedelta(days=1)),
        trade(a + timedelta(days=1), a + timedelta(days=1, hours=1)),
        trade(a + timedelta(days=3), a + timedelta(days=3)),
    ]
    result = trade_uniqueness(trades)
    assert result["weights"] == [0.75, 0.5, 1.0]
    assert result["effective_trades"] == 2.25
    assert result["average_uniqueness"] == 0.75
    # Direction is irrelevant: two identical holding intervals count twice.
    assert trade_uniqueness([trades[0], trades[0]])["weights"] == [0.5, 0.5]
    assert trade_uniqueness([])["effective_trades"] == 0
    with pytest.raises(ValueError):
        trade_uniqueness([trade(a, a - timedelta(hours=1))])


def test_prague_midnight_and_dst():
    # March 31 is 23 hours; exit exactly at April 1 Prague midnight is exclusive.
    a = datetime(2024, 3, 30, 23, tzinfo=UTC)
    b = datetime(2024, 3, 31, 22, tzinfo=UTC)
    assert trade_uniqueness([trade(a, b), trade(b, b)])["weights"] == [1, 1]
