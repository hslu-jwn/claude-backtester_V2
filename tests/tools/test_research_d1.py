"""D1 research uses UTC days, including isolated cache segments, without lookahead.

Spec: strategy-trend-following.md > Timeframes; AGENTS.md > Invariant #1.
The hand-built M1 rows straddle the NY rollover and a US DST weekend.
"""

from datetime import UTC, date, datetime, timedelta

import pytest
from m1_frames import m1

from backtester.core.models import Timeframe
from backtester.data.cache import cache_path
from backtester.data.sources import SymbolSources
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.trend_following.config import TrendFollowingConfig
from backtester.strategy.trend_following.strategy import TrendFollowing
from backtester.tools.research import run_period, run_period_many


def write_day(root, day, price):
    path = cache_path(root, "BTCUSD", day)
    path.parent.mkdir(parents=True, exist_ok=True)
    m1(
        ("00:00", price, price + 2, price - 1, price + 1, 1, 0),
        ("23:59", price + 1, price + 4, price, price + 3, 1, 0),
        day=day.isoformat(),
    ).to_parquet(path, index=False)


@pytest.mark.parametrize("path", ["single", "research", "many"])
def test_d1_runner_aggregates_each_utc_day_and_keeps_isolated_segment(tmp_path, monkeypatch, path):
    first = date(2020, 3, 5)
    # March 6 is uncached: March 5 must still produce a complete UTC daily candle.
    offsets = [0, 2, 3, 4]
    for offset in offsets:
        write_day(tmp_path, first + timedelta(days=offset), 100 + offset * 10)
    # Cached future prices must not leak into the last requested daily candle.
    write_day(tmp_path, first + timedelta(days=5), 10000)
    sources = SymbolSources.single(tmp_path, ["BTCUSD"])
    settings = RunSettings(strategy=TrendFollowingConfig(timeframe=Timeframe.D1))
    seen = []
    original = TrendFollowing.on_candle

    def observe(self, now, views):
        view = views[Timeframe.D1]
        assert view.current.ts + Timeframe.D1.duration == now
        seen.append((now, view.current.open, view.current.high, view.current.low,
                     view.current.close))
        return original(self, now, views)

    monkeypatch.setattr(TrendFollowing, "on_candle", observe)
    end = first + timedelta(days=4)
    if path == "single":
        # The direct runner also handles the isolated day (no gaps inside this range).
        result = run_backtests(["BTCUSD"], first, first, settings, sources, workers=1)
        offsets = [0]
    elif path == "research":
        result = run_period(["BTCUSD"], first, end, settings, sources, workers=1)
    else:
        [(index, result)] = run_period_many(
            ["BTCUSD"], first, end, [settings], sources, workers=1
        )
        assert index == 0
    assert seen == [
        (datetime.combine(first + timedelta(days=offset + 1), datetime.min.time(), UTC),
         100 + offset * 10, 104 + offset * 10, 99 + offset * 10, 103 + offset * 10)
        for offset in offsets
    ]
    assert result.symbols == ("BTCUSD",)
    # Four candles cannot warm up the default 20-day breakout/ATR; no guessed history.
    assert result.trades == ()
