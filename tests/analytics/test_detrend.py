"""Cases: linear rise long/short, partial exits, zero drift, multiple symbols, weighted R,
bad stop/direction/times/shares/drift, missing drift, bias reversal and partial occupancy,
one cached read per block, endpoint sorting and insufficient data.
Spec: research-runner.md > Skill vs trend, and bounds.
"""

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace as NS

import pandas as pd
import pytest

from backtester.analytics.detrend import detrend, load_drifts, position_bias

START = datetime(2020, 1, 6, tzinfo=UTC)


def trade(**kw):
    values = {
        "symbol": "X",
        "entry_time": START,
        "exit_time": START + timedelta(seconds=100),
        "entry": 100,
        "initial_stop": 90,
        "direction": "long",
        "r_net": 1,
        "parts": (),
    }
    return NS(**(values | kw))


def test_linear_long_short_and_zero():
    assert detrend([trade()], {"X": 0.1})["total"]["detrended_net_r"] == 0
    a = detrend([trade(direction="short", r_net=-1)], {"X": 0.1})
    assert a["symbols"]["X"]["trend_r"] == -1
    assert a["total"]["detrended_net_r"] == 0
    assert detrend([trade()], {"X": 0})["total"]["detrended_net_r"] == 1


def test_partial_weight_and_total():
    parts = ({"time": (START + timedelta(seconds=50)).isoformat(), "share": 0.5},)
    a = detrend([trade(parts=parts, risk_weight=0.5), trade(symbol="Y")], {"X": 0.1, "Y": 0})
    assert a["symbols"]["X"]["trend_r"] == 0.375
    assert a["trades"][0]["trend_r"] == 0.375
    assert a["trades"][0]["detrended_r"] == 0.625
    assert a["total"]["detrended_net_r"] == 1.625
    assert a["total"]["detrended_avg_r"] == 0.8125


@pytest.mark.parametrize(
    "kw",
    [
        {"initial_stop": 100},
        {"direction": "bad"},
        {"exit_time": START - timedelta(seconds=1)},
        {"entry": float("nan")},
        {"parts": ({"time": START, "share": 1.1},)},
    ],
)
def test_invalid_trade(kw):
    with pytest.raises(ValueError):
        detrend([trade(**kw)], {"X": 0.1})


def test_missing_or_bad_drift():
    assert detrend([trade()], {})["total"]["detrended_net_r"] is None
    with pytest.raises(ValueError):
        detrend([trade()], {"X": float("nan")})


def test_bias_partial_and_clipped_overlap():
    a = START - timedelta(hours=1)
    end = a + timedelta(days=1)
    parts = ({"time": a + timedelta(hours=12), "share": 0.5},)
    result = position_bias(
        [trade(entry_time=a, exit_time=end, parts=parts)], date(2020, 1, 6), date(2020, 1, 6)
    )
    assert result["symbols"]["X"] == pytest.approx({"long": 0.75, "short": 0, "flat": 0.25})
    result = position_bias(
        [trade(entry_time=a, exit_time=end)] * 2, date(2020, 1, 6), date(2020, 1, 6)
    )
    assert result["symbols"]["X"] == pytest.approx({"long": 1, "short": 0, "flat": 0})


def test_missing_prices_are_unavailable():
    sources = NS(adapter=lambda s: NS(), cached_days=lambda s: [])
    assert load_drifts(["X"], date(2020, 1, 6), date(2020, 1, 7), sources) == {"X": None}


def test_bias_preserves_intraday_reversal():
    # Monday Prague 00:00 to noon long, noon to Tuesday 00:00 short.
    a = START - timedelta(hours=1)
    mid, end = a + timedelta(hours=12), a + timedelta(days=1)
    result = position_bias(
        [
            trade(entry_time=a, exit_time=mid),
            trade(entry_time=mid, exit_time=end, direction="short"),
        ],
        date(2020, 1, 6),
        date(2020, 1, 6),
    )
    assert result["symbols"]["X"] == pytest.approx({"long": 0.5, "short": 0.5, "flat": 0})


def test_cache_blocks():
    calls = []

    def fetch(symbol, tf, start, end):
        calls.append((start, end))
        return pd.DataFrame({"ts": [start + timedelta(minutes=1), start], "close": [12, 10]})

    sources = NS(
        adapter=lambda s: NS(fetch_frame=fetch),
        cached_days=lambda s: [date(2020, 1, 6), date(2020, 1, 7), date(2020, 1, 9)],
    )
    a = load_drifts(["X"], date(2020, 1, 6), date(2020, 1, 9), sources)
    assert len(calls) == 2
    assert a["X"] == pytest.approx(2 / (3 * 86400 + 60))
