"""Runner checks: monthly decay and extreme trades (research-runner.md V2.4c)."""

from datetime import UTC, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from backtester.analytics import robustness as rb


def trade(value, month=1, day=1):
    entry = datetime(2020, month, day, tzinfo=UTC)
    return SimpleNamespace(
        symbol="US500",
        direction="long",
        entry_time=entry,
        exit_time=entry + timedelta(hours=2),
        exit_reason="signal",
        r_net=value,
    )


def test_months_include_gaps_and_use_utc_entry():
    a = trade(2)
    a.entry_time = datetime(2023, 2, 1, 0, 30, tzinfo=timezone(timedelta(hours=1)))
    b = trade(3)
    b.entry_time = datetime(2023, 3, 1, tzinfo=UTC)
    assert rb.monthly_net([b, a]) == {"2023-01": 2, "2023-02": 0, "2023-03": 3}
    assert rb.monthly_net([]) == {}


def test_ols_perfect_constant_short_and_declining():
    line = rb.returns_slope(dict(zip(range(12), range(1, 13), strict=True)))
    assert line["slope_per_year"] == pytest.approx(12)
    assert line["standard_error"] is None and line["t_stat"] is None
    assert line["perfect_fit"] is True and line["n_months"] == 12
    assert rb.returns_slope(dict.fromkeys(range(6), 2))["slope_per_year"] == 0
    short = rb.returns_slope(dict.fromkeys(range(5), 2))
    assert all(short[k] is None for k in ("slope_per_year", "standard_error", "t_stat"))
    noisy = [12, 10, 11, 8, 9, 6, 7, 4, 5, 2, 3, 0]
    assert rb.returns_slope(dict(enumerate(noisy)))["t_stat"] <= -2


def test_extremes_sort_ties_and_small_lists():
    trades = [trade(i // 2, day=i + 1) for i in range(25)]
    rows = rb.top_trades(list(reversed(trades)))
    best = [r for r in rows if r["side"] == "best"]
    worst = [r for r in rows if r["side"] == "worst"]
    assert len(best) == len(worst) == 10
    assert [r["r_net"] for r in best] == [12, 11, 11, 10, 10, 9, 9, 8, 8, 7]
    assert [r["r_net"] for r in worst] == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
    assert best[1]["entry_time"] < best[2]["entry_time"]
    assert best[0]["hold_hours"] == 2 and best[0]["rank"] == 1
    assert len(rb.top_trades(trades[:3])) == 6


def test_top_ten_contribution():
    result = rb.extreme_summary([trade(i, day=i + 1) for i in range(25)])
    assert result == {"net_r": 300, "net_r_without_best": 105, "best_share": 195 / 300}
    assert rb.extreme_summary([trade(-1)])["best_share"] is None
    assert rb.extreme_summary([trade(0)])["best_share"] is None


def test_ols_standard_error_is_annualized_and_order_independent():
    # x=0..5, y=0,2,1,4,3,6: Sxx=17.5, Sxy=18, Syy=66-256/6.
    values = [0, 2, 1, 4, 3, 6]
    result = rb.returns_slope(dict(reversed(list(enumerate(values)))))
    se_month = ((66 - 256 / 6 - 324 / 17.5) / 4 / 17.5) ** 0.5
    assert result["slope_per_year"] == pytest.approx(18 / 17.5 * 12)
    assert result["standard_error"] == pytest.approx(se_month * 12)
    assert result["t_stat"] == pytest.approx((18 / 17.5) / se_month)


def test_extremes_are_json_safe_for_engine_enums():
    import json

    from backtester.core.models import Direction
    from backtester.engine.trade import ExitReason

    t = trade(1)
    t.direction = Direction.BULLISH
    t.exit_reason = next(iter(ExitReason))
    rows = rb.top_trades([t])
    json.dumps(rows, allow_nan=False)
    assert rows[0]["direction"] == "long"
    assert rows[0]["exit_reason"] == t.exit_reason.value
