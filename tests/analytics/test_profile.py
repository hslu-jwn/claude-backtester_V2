"""Cases: every dimension partitions all trades including unknown; fixed empty cells;
whole-period detrending; bounds minimum; best count/positive-bound gates; session
boundaries/DST/weekend; exit-ordered DD; unavailable drift; empty input.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.analytics.profile import build_profile, entry_session, markdown
from backtester.analytics.regime import RegimeLabel


def trade(i=0, r=1):
    at = datetime(2020, 1, 6, 12, tzinfo=UTC) + timedelta(days=i)
    return SimpleNamespace(
        symbol="XAUUSD",
        direction="long",
        entry_time=at,
        exit_time=at + timedelta(hours=1),
        entry=100,
        initial_stop=99,
        r_net=r,
        parts=(),
    )


def profile(trades, drift=0):
    return build_profile(trades, [RegimeLabel()] * len(trades), {"XAUUSD": drift})


def test_partition_and_detrend():
    trades = [trade(i) for i in range(30)]
    p = profile(trades, 1 / 7200)
    for dim in p["dimensions"].values():
        assert sum(c["trades"] for c in dim["cells"]) == 30
    c = p["dimensions"]["symbol"]["cells"][0]
    assert c["net_r"] == 30 and c["detrended_net_r"] == 15
    assert c["lower90_bca"] == pytest.approx(0.5)
    assert p["dimensions"]["symbol"]["best"] == "XAUUSD"
    assert len(p["dimensions"]["regime"]["cells"]) == 7
    assert len(p["strongest_skill_cells"]) == 5
    assert "**XAUUSD**" in "\n".join(markdown(p))


@pytest.mark.parametrize("n,r", [(29, 1), (30, 0), (30, -1)])
def test_no_best(n, r):
    p = profile([trade(i, r) for i in range(n)])
    assert p["dimensions"]["symbol"]["best"] is None
    assert p["dimensions"]["symbol"]["reason"]


def test_small_missing_empty():
    assert profile([trade()])["dimensions"]["symbol"]["cells"][0]["lower90_bca"] is None
    c = profile([trade()] * 30, None)["dimensions"]["symbol"]
    assert c["best"] is None and c["cells"][0]["detrended_net_r"] is None
    assert profile([])["total_trades"] == 0
    with pytest.raises(ValueError):
        build_profile([trade()], [], {})


def test_drawdown_exit_order():
    trades = [trade(i, r) for i, r in enumerate([-2, 3, -1])]
    assert profile(trades)["dimensions"]["symbol"]["cells"][0]["max_dd_r"] == 2


def test_best_highest_eligible_mean_and_strongest_bound_order():
    trades = [trade(i, 1) for i in range(30)]
    other = [trade(i, 2) for i in range(30)]
    thin = [trade(i, 100) for i in range(29)]
    for t in other:
        t.symbol = "US500"
    for t in thin:
        t.symbol = "EURUSD"
    trades += other + thin
    p = build_profile(trades, [RegimeLabel()] * len(trades), {"XAUUSD": 0, "US500": 0, "EURUSD": 0})
    assert p["dimensions"]["symbol"]["best"] == "US500"
    bounds = [r["lower90_bca"] for r in p["strongest_skill_cells"]]
    assert bounds == sorted(bounds, reverse=True)


def test_bound_exact_minimum_and_effective_concurrency():
    cell = profile([trade()] * 10)["dimensions"]["symbol"]["cells"][0]
    assert cell["lower90_bca"] == 1
    assert cell["effective_trades"] == pytest.approx(1)


def test_drift_profit_cannot_qualify_as_skill():
    p = profile([trade(i) for i in range(30)], 1 / 1800)
    dimension = p["dimensions"]["symbol"]
    cell = dimension["cells"][0]
    assert cell["net_r"] == 30
    assert cell["detrended_net_r"] == -30
    assert cell["lower90_bca"] == -1
    assert dimension["best"] is None


def test_combined_unknown_preserves_independent_trend():
    p = build_profile([trade()], [RegimeLabel("trend_up", "unknown")], {"XAUUSD": 0})
    assert p["dimensions"]["regime"]["cells"][-1]["trades"] == 1
    assert p["dimensions"]["regime_trend"]["cells"][0]["trades"] == 1


@pytest.mark.parametrize(
    "stamp,expected",
    [
        ("2020-01-06T07:59:59+00:00", "Tokyo"),
        ("2020-01-06T08:00:00+00:00", "London"),
        ("2020-01-06T13:00:00+00:00", "New York"),
        ("2020-03-16T12:00:00+00:00", "New York"),
        ("2020-01-11T12:00:00+00:00", "other"),
        ("2020-01-13T00:00:00+00:00", "Tokyo"),
    ],
)
def test_sessions(stamp, expected):
    assert entry_session(datetime.fromisoformat(stamp)) == expected
