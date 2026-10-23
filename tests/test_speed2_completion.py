"""Remaining sharing regressions for docs/review/speed.md, steps 4-6.

The partial commit already implements each item. These checks exercise pool feed
boundaries and compare the session pipeline with independently owned detectors.
"""

from dataclasses import replace

import pytest
from conftest import build_series
from test_speed_same_results import random_candles

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.detectors.atr import Atr, StrongMoveConfig
from backtester.detectors.bos import BosDetector
from backtester.detectors.bpr import BprConfig, BprDetector
from backtester.detectors.breaker import BreakerDetector
from backtester.detectors.fvg import FvgConfig, FvgDetector
from backtester.detectors.order_block import OrderBlockConfig, OrderBlockDetector
from backtester.detectors.settings import DetectorSettings
from backtester.detectors.shared import DetectorPool
from backtester.detectors.swings import SwingDetector
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.setup import StructureTracker
from backtester.strategy.session_zone_sweep.signals import SetupTracker


@pytest.mark.parametrize("consumer", ["atr", "swings", "bos", "filter", "fvg"])
@pytest.mark.parametrize("mismatch", ["symbol", "timeframe", "candle"])
def test_shared_cached_view_rejects_a_different_feed_without_advancing(consumer, mismatch):
    candles = list(
        build_series(
            [
                (100.0, 102.0, 99.0, 101.0),
                (101.0, 103.0, 100.0, 100.5),
                (100.5, 104.0, 100.0, 103.0),
            ]
        ).view(2)
    )
    series = CandleSeries("X", Timeframe.M5, candles)
    pool = DetectorPool(0.1)
    detector = {
        "atr": pool.atr(2),
        "swings": pool.swings,
        "bos": pool.bos,
        "filter": pool.strong_move(StrongMoveConfig(2, 0.8)),
        "fvg": pool.fvg(FvgConfig()),
    }[consumer]
    first = detector.update(series.view(0))
    assert detector.update(series.view(0)) == first
    other = CandleSeries(
        "Y" if mismatch == "symbol" else "X",
        Timeframe.M15 if mismatch == "timeframe" else Timeframe.M5,
        [replace(c) for c in candles] if mismatch == "candle" else candles,
    )
    with pytest.raises(ValueError, match="same closed candle view"):
        detector.update(other.view(0))
    # A failed cache query cannot consume a candle or poison the correct feed.
    assert detector.update(series.view(0)) == first
    detector.update(series.view(1))
    with pytest.raises(ValueError, match="once per candle in order"):
        detector.update(series.view(0))
    detector.update(series.view(2))


@pytest.mark.parametrize("different_periods", [False, True])
def test_session_pipeline_shares_each_primitive_once_per_closed_candle(
    monkeypatch, different_periods
):
    calls = {cls: 0 for cls in (FvgDetector, BosDetector, SwingDetector, Atr)}
    for cls in calls:
        original = cls.update

        def counted(self, view, _cls=cls, _original=original, **kwargs):
            calls[_cls] += 1
            return _original(self, view, **kwargs)

        monkeypatch.setattr(cls, "update", counted)
    settings = DetectorSettings(
        fvg=FvgConfig(True, StrongMoveConfig(3, 0.8)),
        order_block=OrderBlockConfig(True, StrongMoveConfig(5 if different_periods else 3, 1.1)),
    )
    config = SessionZoneSweepConfig(strong_move=StrongMoveConfig(3, 2.0))
    tracker = SetupTracker("XAUUSD", config, settings)
    series = CandleSeries("XAUUSD", Timeframe.M5, random_candles(60, 19))
    for i in range(len(series)):
        view = series.view(i)
        tracker.update(view.current.ts + Timeframe.M5.duration, view, None)
    assert calls == {
        FvgDetector: len(series),
        BosDetector: len(series),
        SwingDetector: len(series),
        Atr: len(series) * (2 if different_periods else 1),
    }


@pytest.mark.parametrize("filtered", [False, True])
@pytest.mark.parametrize("with_trend", [False, True])
def test_session_shared_events_match_independent_detectors_and_prefix(filtered, with_trend):
    settings = DetectorSettings(
        fvg=FvgConfig(filtered, StrongMoveConfig(3, 0.8)),
        order_block=OrderBlockConfig(filtered, StrongMoveConfig(5, 1.1)),
    )
    config = SessionZoneSweepConfig(entry_bos_with_trend=with_trend)
    fast, reference, prefix = (SetupTracker("XAUUSD", config, settings) for _ in range(3))
    doji = reference.doji_max_body
    reference.structure = StructureTracker(doji)
    reference._atr = Atr(config.strong_move.atr_period)
    reference._fvg = FvgDetector(doji, settings.fvg)
    reference._ob = OrderBlockDetector(doji, settings.order_block)
    reference._bpr = BprDetector(doji, BprConfig(settings.fvg))
    reference._breaker = BreakerDetector(doji)
    series = CandleSeries("XAUUSD", Timeframe.M5, random_candles(400, 31))
    short = CandleSeries("XAUUSD", Timeframe.M5, series.view(199).last(200))
    snapshots = []
    prefix_snapshots = []
    for i in range(len(series)):
        actual, expected = fast._update_5m(series.view(i)), reference._update_5m(series.view(i))
        assert actual == expected
        assert fast.zone_transitions == reference.zone_transitions
        assert list(fast._usable.values()) == list(reference._usable.values())
        assert fast._equilibrium == reference._equilibrium
        assert fast._atr.current == reference._atr.current
        assert fast.structure.trend is reference.structure.trend
        assert all(b.index == i for b in actual[0])
        if i < len(short):
            prefix_result = prefix._update_5m(short.view(i))
            assert prefix_result == actual
            assert prefix.zone_transitions == fast.zone_transitions
            assert prefix._equilibrium == fast._equilibrium
            snapshots.append((tuple(actual[0]), tuple(actual[1]), tuple(fast.zone_transitions)))
            prefix_snapshots.append(
                (tuple(prefix_result[0]), tuple(prefix_result[1]), tuple(prefix.zone_transitions))
            )
    # Later closes leave all already emitted events untouched.
    assert snapshots == prefix_snapshots
    assert fast.zone_transitions and fast.structure.trend is not None
