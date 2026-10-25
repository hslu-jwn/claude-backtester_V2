"""Cases: straight/mirrored/flat/zigzag; warm-up; volatility; closed-entry boundary;
future append invariance; weekends/DST; ADX; invalid config; one adapter read per symbol.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.analytics.regime import RegimeClassifier, RegimeConfig, label_trades
from backtester.core.models import Candle, Timeframe
from backtester.core.series import CandleSeries


def series(values, times=None):
    times = times or [
        datetime(2020, 1, 1, tzinfo=UTC) + timedelta(days=i) for i in range(len(values))
    ]
    return CandleSeries(
        "XAUUSD", Timeframe.D1, [Candle(t, v, v + 1, v - 1, v) for t, v in zip(times, values)]
    )


def labels(values, **kw):
    s = series(values)
    c = RegimeClassifier(RegimeConfig(er_days=4, atr_period=2, vol_lookback_days=3, **kw))
    return [c.update(s.view(i)) for i in range(len(s))]


@pytest.mark.parametrize(
    "values,expected",
    [
        (list(range(100, 110)), "trend_up"),
        (list(range(110, 100, -1)), "trend_down"),
        ([100, 101] * 5, "sideways"),
        ([100] * 10, "sideways"),
    ],
)
def test_known_trends(values, expected):
    rows = labels(values)
    assert rows[-1].regime_trend == expected
    assert rows[0].regime_trend == rows[0].regime_vol == "unknown"
    assert rows[3].regime_trend == "unknown"
    assert rows[4].regime_trend == expected


def test_vol_rank_uses_previous_observations():
    rows = labels(list(range(100, 110)))  # ATR/close declines every day
    assert rows[3].regime_vol == "unknown"
    assert rows[4].regime_vol == "low"
    assert labels([100] * 10)[-1].regime_vol == "high"  # ties counted <=


def test_entry_boundary_future_weekend_and_dst():
    from backtester.analytics.regime import RegimeHistory

    times = [datetime(2020, 3, 2 + i, 22, tzinfo=UTC) for i in range(5)]
    times += [datetime(2020, 3, 9, 21, tzinfo=UTC)]
    s = series([100, 101, 102, 103, 104, 1], times)
    cfg = RegimeConfig(er_days=2, atr_period=1, vol_lookback_days=2)
    before = times[-1] + Timeframe.D1.duration - timedelta(microseconds=1)
    short = RegimeHistory(series([100, 101, 102, 103, 104], times[:-1]), cfg)
    full = RegimeHistory(s, cfg)
    assert full.at(before) == short.at(before)
    assert full.at(before).regime_trend == "trend_up"
    assert full.at(before + timedelta(microseconds=1)).regime_trend == "trend_down"
    assert full.at(times[0]).regime_trend == "unknown"


def test_autumn_dst_25_hour_day_label_waits_for_the_real_close():
    """Opus 2026-10-25: the 17:00 New York day of 2020-10-31 ends 2020-11-01 22:00 UTC (25 h);
    an entry at 21:30 UTC must not see that day's label yet."""
    from backtester.analytics.regime import RegimeHistory, _d1_close

    times = [datetime(2020, 10, 27 + i, 21, tzinfo=UTC) for i in range(5)]  # 17:00 EDT
    assert _d1_close(times[-1]) == datetime(2020, 11, 1, 22, tzinfo=UTC)
    cfg = RegimeConfig(er_days=2, atr_period=1, vol_lookback_days=2)
    full = RegimeHistory(series([100, 101, 102, 103, 1], times), cfg)
    short = RegimeHistory(series([100, 101, 102, 103], times[:-1]), cfg)
    early = datetime(2020, 11, 1, 21, 30, tzinfo=UTC)
    assert full.at(early) == short.at(early)  # the crash day is not known yet
    assert full.at(datetime(2020, 11, 1, 22, tzinfo=UTC)).regime_trend == "trend_down"


def test_incremental_append_and_order():
    assert labels(list(range(100, 110))) == labels(list(range(100, 130)))[:10]
    s = series([100, 101])
    c = RegimeClassifier()
    with pytest.raises(ValueError):
        c.update(s.view(1))


def test_adx_direction():
    assert (
        labels(list(range(100, 150)), trend_method="adx", adx_period=3)[-1].regime_trend
        == "trend_up"
    )
    assert (
        labels(list(range(150, 100, -1)), trend_method="adx", adx_period=3)[-1].regime_trend
        == "trend_down"
    )
    assert labels([100] * 50, trend_method="adx", adx_period=3)[-1].regime_trend == "sideways"


@pytest.mark.parametrize(
    "kw", [{"er_days": 0}, {"trend_method": "bad"}, {"vol_high_rank": 2}, {"atr_period": -1}]
)
def test_bad_config(kw):
    with pytest.raises(ValueError):
        RegimeConfig(**kw)


def test_one_adapter_read():
    calls = []
    s = series(list(range(100, 130)))

    class Adapter:
        def fetch(self, symbol, timeframe, start, end):
            calls.append((symbol, timeframe))
            return list(s.view(len(s) - 1))

    sources = SimpleNamespace(
        adapter=lambda s: Adapter(), cached_days=lambda s: [datetime(2020, 1, 1).date()]
    )
    trades = [SimpleNamespace(symbol="XAUUSD", entry_time=datetime(2020, 2, 1, tzinfo=UTC))] * 2
    result = label_trades(trades, sources)
    assert len(result) == 2 and calls == [("XAUUSD", Timeframe.D1)]
