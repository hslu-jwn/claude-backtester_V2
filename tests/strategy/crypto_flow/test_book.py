"""Hand-calculated frozen flow rule and future-data invariance."""

from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from backtester.strategy.crypto_flow.book import (
    CryptoFlowConfig,
    eligible_signals,
    pick_legs,
    week_result,
)

MONDAY = pd.Timestamp("2026-01-05", tz="UTC")


def frame(bars=60, end_days=6):
    return pd.DataFrame(
        {
            "open": 100.0,
            "close": 110.0,
            "volume": 10.0,
            "quote_volume": 5e6,
            "taker_buy_volume": 6.0,
        },
        index=pd.date_range(
            MONDAY - pd.Timedelta(days=bars), MONDAY + pd.Timedelta(days=end_days), freq="D"
        ),
    )


def test_config_frozen():
    cfg = CryptoFlowConfig()
    assert (
        cfg.min_bars,
        cfg.volume_window,
        cfg.min_quote_volume,
        cfg.min_eligible,
        cfg.signal_days,
        cfg.quantile,
        cfg.cost_bp,
        cfg.r_bp,
    ) == (60, 30, 5e6, 20, 7, 5, 20.0, 600.0)
    with pytest.raises(FrozenInstanceError):
        cfg.min_bars = 59


def test_eligibility_boundaries():
    assert eligible_signals({"A": frame(59)}, MONDAY) == {}
    assert eligible_signals({"A": frame()}, MONDAY)["A"] == pytest.approx(0.2)
    d = frame()
    d.loc[d.index < MONDAY, "quote_volume"] = 5e6 - 1
    assert eligible_signals({"A": d}, MONDAY) == {}
    assert eligible_signals({"A": frame().drop(MONDAY)}, MONDAY) == {}
    # Keep >=60 older bars, but remove a day in the signal week.
    assert eligible_signals({"A": frame(70).drop(MONDAY - pd.Timedelta(days=3))}, MONDAY) == {}
    d = frame()
    d.loc[d.index < MONDAY, ["volume", "taker_buy_volume"]] = 0
    signals = eligible_signals({"A": d}, MONDAY)
    assert set(signals) == {"A"}  # eligible, but no sortable signal
    assert np.isnan(signals["A"])


def test_exact_signal_and_no_future_prices():
    d = frame()
    last7 = (d.index >= MONDAY - pd.Timedelta(days=7)) & (d.index < MONDAY)
    d.loc[last7, "volume"] = [1, 2, 3, 4, 5, 6, 7]
    d.loc[last7, "taker_buy_volume"] = [1, 1, 2, 2, 3, 3, 4]
    # (2*16 - 28) / 28 = 1/7.
    expected = {"A": pytest.approx(1 / 7)}
    assert eligible_signals({"A": d}, MONDAY) == expected
    d.loc[d.index >= MONDAY, :] = 999999.0
    assert eligible_signals({"A": d}, MONDAY) == expected


def test_pick_legs_and_nan_eligibility():
    signals = {f"S{i:02}": float(i) for i in reversed(range(25))}
    assert pick_legs(signals) == (
        [f"S{i:02}" for i in range(20, 25)],
        [f"S{i:02}" for i in range(5)],
    )
    tied = dict.fromkeys(sorted(signals, reverse=True), 0.0)
    assert pick_legs(tied) == pick_legs(signals)
    assert pick_legs({str(i): float(i) for i in range(19)}) is None
    signals = {str(i): float(i) for i in range(19)} | {"zero": float("nan")}
    longs, shorts = pick_legs(signals)
    assert len(longs) == len(shorts) == 3  # 20 eligible, floor(19/5) sorted
    assert "zero" not in longs + shorts
    assert pick_legs(dict.fromkeys(signals, float("nan"))) is None


def test_exact_week_delisting_and_funding_boundaries():
    k = {"L": frame(end_days=3), "S": frame()}
    k["L"].iloc[-1, k["L"].columns.get_loc("close")] = 120
    # Long +2000bp, short underlying +1000bp => price spread +1000bp.
    times = [
        MONDAY,
        MONDAY + pd.Timedelta(hours=8),
        MONDAY + pd.Timedelta(days=6, hours=16),
        MONDAY + pd.Timedelta(days=7),
    ]
    f = {
        "L": pd.Series([9, 0.0001, 0.0002, 9], index=times),
        "S": pd.Series([9, 0.0004, 0.0005, 9], index=times),
    }
    before = week_result(MONDAY, ["L"], ["S"], k, f)
    for key, value in {
        "price_bp": 1000,
        "funding_bp": 6,
        "cost_bp": 20,
        "net_bp": 986,
        "r_gross": 1006 / 600,
        "r_net": 986 / 600,
    }.items():
        assert before.trade[key] == pytest.approx(value)
    assert before.trade["entry_time"] == MONDAY
    assert before.trade["exit_time"] == MONDAY + pd.Timedelta(days=7, minutes=-1)
    long = next(r for r in before.legs if r["side"] == "long")
    assert long["funding_bp"] == pytest.approx(-3)
    assert long["exit_day"] == MONDAY + pd.Timedelta(days=3)
    for sym, data in k.items():
        data.loc[MONDAY + pd.Timedelta(days=8)] = 999999
        f[sym].loc[MONDAY + pd.Timedelta(days=8)] = 999999
    assert week_result(MONDAY, ["L"], ["S"], k, f) == before


def test_invalid_monday_and_price():
    with pytest.raises(ValueError, match="Monday"):
        eligible_signals({"A": frame()}, MONDAY + pd.Timedelta(days=1))
    k = {"A": frame(), "B": frame()}
    k["A"].loc[MONDAY, "open"] = 0
    with pytest.raises(ValueError, match="positive"):
        week_result(MONDAY, ["A"], ["B"], k, {})
