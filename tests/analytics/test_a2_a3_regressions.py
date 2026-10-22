"""Regression cases for briefs/phase4-a2-a3.md; no strategy rules change."""

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest
from test_entry_screen import t0, trade
from test_gap_buckets import CFG, at, bars

from backtester.analytics import orderflow, portfolio, stationarity, trial_log
from backtester.analytics.entry_screen import EntryScreenConfig, _hit_scan
from backtester.analytics.gap_buckets import gap_days
from backtester.analytics.random_fills import max_slippage_r
from backtester.analytics.walk_forward import walk_forward
from backtester.risk import monte_carlo as mc
from backtester.risk.adaptive import AdaptiveRisk


def test_training_excludes_exits_at_or_after_test_start():
    boundary = datetime(2021, 1, 1, tzinfo=UTC)

    def t(entry, exit, r):
        return SimpleNamespace(entry_time=entry, exit_time=exit, r_net=r)

    a = [t(boundary - timedelta(days=2), boundary, 100)]
    b = [t(boundary - timedelta(days=2), boundary - timedelta(seconds=1), 1)]
    pick = walk_forward({"a": a, "b": b}, first_year=2020, last_year=2021).picks[0]
    assert pick.variant == "b" and pick.train_net == 1
    a[0].exit_time = boundary + timedelta(days=30)
    assert walk_forward({"a": a, "b": b}, first_year=2020, last_year=2021).picks[0] == pick


@pytest.mark.parametrize("adaptive", [None, AdaptiveRisk()])
@pytest.mark.parametrize("factor", [1.0, 1.5])
def test_portfolio_weights_reach_day_exposure(adaptive, factor):
    start = datetime(2026, 1, 5, 12, tzinfo=UTC)
    t = SimpleNamespace(entry_time=start, exit_time=start + timedelta(hours=1), r_net=-2.0)
    weighted = portfolio.weighted_trades([[t]] * 6, [1 / 6] * 6, factor)
    [day] = mc.build_days(weighted, start.date(), start.date())
    status, balance = mc._play_day(
        day, 100_000, 0.01, mc.MonteCarloConfig(adaptive=adaptive), mc.NO_TARGET, 0
    )
    assert status is None
    assert 96_900 < balance < 98_100
    assert t.r_net == -2.0


def test_weighted_real_trade_keeps_risk_weight_and_partial_exits():
    from backtester.core.models import Direction
    from backtester.engine.trade import ExitReason, PartialExit, TradeResult

    stamp = datetime(2026, 1, 5, 12, tzinfo=UTC)
    part = PartialExit(0.5, stamp, stamp, 110, 110, ExitReason.TAKE_PROFIT, 1.0, 1.0)
    stop = replace(part, reason=ExitReason.STOP_LOSS)
    t = TradeResult(
        symbol="X",
        direction=Direction.BULLISH,
        entry_time=stamp,
        entry_candle=stamp,
        entry=100,
        entry_fill=100,
        initial_stop=90,
        take_profit=110,
        exit_time=stamp,
        exit_candle=stamp,
        exit_price=90,
        exit_fill=90,
        exit_reason=ExitReason.STOP_LOSS,
        r_gross=0.0,
        r_net=0.0,
        spread_r=0.0,
        commission_r=0.0,
        break_even_time=None,
        break_even_stop=None,
        mae_r=-1.0,
        mfe_r=1.0,
        parts=(part, stop),
    )
    [weighted] = portfolio.weighted_trades([[t]], [0.25], 1.5)
    assert weighted.risk_weight == 0.375
    assert weighted.parts == t.parts
    assert max_slippage_r(t, 1) == pytest.approx([0.2, 0.1])
    [day] = mc.build_days([weighted], stamp.date(), stamp.date())
    assert day.weights == (0.375, 0.375)


@pytest.mark.parametrize("as_dict", [False, True])
def test_random_fill_stop_slippage_is_weighted_per_part(as_dict):
    parts = [
        {"share": 0.5, "reason": "take_profit"},
        {"share": 0.2, "reason": "stop_loss"},
        {"share": 0.3, "reason": "break_even"},
    ]
    t = SimpleNamespace(
        entry=100,
        initial_stop=90,
        exit_reason="break_even",
        parts=parts if as_dict else [SimpleNamespace(**p) for p in parts],
    )
    assert max_slippage_r(t, 1) == pytest.approx([0.2, 0.04, 0.06])


@pytest.mark.parametrize("minutes,expected", [(0, 1), (5, 1), (10, 1), (11, 0)])
def test_gap_bucket_last_close_tolerance(minutes, expected):
    data, days = bars([(115.0, 118.0)])
    stamp, high, low, close = data[-1]
    data[-1] = (stamp - timedelta(minutes=minutes), high, low, close)
    cfg = replace(CFG, close_tolerance_min=10)
    records = gap_days(data, cfg)
    assert len(records) == expected
    if expected:
        assert records[0].close == 118
    # Also finalize when the next session arrives (rather than only end of input).
    records = gap_days(data + [(at(days[-1] + timedelta(days=1), "09:30"), 119, 119, 119)], cfg)
    assert len(records) == expected


def test_entry_hit_deadline_uses_trade_timestamp():
    start = t0()
    # Last pre-entry candle closes 14:04; entry is 14:05; gain arrives at 14:07.
    # Remove the candle closing exactly at entry.
    from backtester.analytics.entry_screen import M1Data
    from backtester.core.models import Candle

    data = M1Data.from_candles(
        [
            Candle(start - timedelta(minutes=2), 100, 100, 100, 100),
            Candle(start, 100, 100, 100, 100),
            Candle(start + timedelta(minutes=1), 100, 101, 100, 101),
        ]
    )
    rows = _hit_scan(
        [trade(at=start)], {"X": data}, 1, EntryScreenConfig(bars=(2,), shuffle_runs=2)
    )
    assert rows[0]["real_hit_rate"] == 1.0


def test_entry_hit_does_not_use_a_candle_after_deadline():
    from backtester.analytics.entry_screen import M1Data, _hit_signs
    from backtester.core.models import Candle

    start = t0()
    data = M1Data.from_candles(
        [
            Candle(start - timedelta(minutes=2), 100, 100, 100, 100),
            Candle(start + timedelta(minutes=2), 100, 101, 100, 101),
        ]
    )
    signs = _hit_signs(data, np.array([0]), np.array([100.0]), 2, 1, np.array([start.timestamp()]))
    assert signs.tolist() == [0]


def test_orderflow_common_buckets_with_missing_targets():
    x = np.arange(20.0)
    y = x.copy()
    y[10:] = np.nan
    codes = orderflow.bucket(x, 2)
    table = orderflow.decile_table(x, y, 2)
    assert list(table["bucket"]) == [0]
    assert table["mean"].tolist() == [4.5]
    assert np.isnan(orderflow.spread(codes, y))
    assert all(np.isnan(v) for v in orderflow.half_spreads(codes, y, x < 10))


def test_orderflow_noise_uses_same_extreme_buckets():
    codes = orderflow.bucket(np.arange(30.0), 3)
    y = np.arange(30.0)
    y[20:] = np.nan
    assert np.isnan(orderflow.spread(codes, y))
    assert np.isnan(orderflow.shuffle_p95(codes, y, 5, 42))
    assert np.isnan(orderflow.shift_p95(codes, y, 5, 42))


@pytest.mark.parametrize("root", ["null", "[]", "42", '"text"', "true"])
def test_trial_reader_warns_for_non_object_root(tmp_path, root):
    path = tmp_path / "trials.jsonl"
    path.write_text(root + "\n", encoding="utf-8")
    trial_log.append(trial_log.count_only("valid", "x", 1), path)
    with pytest.warns(UserWarning, match="skipped bad line 1"):
        records = trial_log.read_all(path)
    assert len(records) == 1 and records[0].family == "valid"


def test_stationarity_missing_sibling_p_value():
    base = {"family": "lagcorr", "symbol": "NAS100", "timeframe": "H1", "cell": "k=1", "value": 0.2}
    cells = [dict(base, period=p, p_value=1e-9) for p in ("whole", "first_half", "second_half")]
    cells.append(dict(base, symbol="US500", period="whole", p_value=None))
    found, _ = stationarity.find_findings(cells, stationarity.StationarityConfig())
    assert len(found) == 1 and "p=n/a" in found[0]["siblings"]


def test_empty_daily_series_have_finite_correlation_and_idm():
    result = portfolio.combine({"a": [], "b": []}, date(2026, 1, 10), date(2026, 1, 11))
    assert result.corr == [[1.0, 0.0], [0.0, 1.0]]
    assert result.idm == pytest.approx(np.sqrt(2))
    assert result.rolling[(0, 1)]["windows"] == 0


@pytest.mark.parametrize("field", ["entry_time", "exit_time"])
def test_risk_days_reject_naive_timestamps_even_without_weekdays(field):
    stamp = datetime(2026, 1, 5, tzinfo=UTC)
    t = SimpleNamespace(entry_time=stamp, exit_time=stamp, r_net=1.0)
    setattr(t, field, stamp.replace(tzinfo=None))
    for start, end in [
        (date(2026, 1, 5), date(2026, 1, 5)),
        (date(2026, 1, 10), date(2026, 1, 11)),
    ]:
        with pytest.raises(ValueError, match="timezone-aware"):
            mc.build_days([t], start, end)
