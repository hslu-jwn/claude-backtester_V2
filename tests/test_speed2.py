"""Speed steps 4-6: preserve closed-candle events, ordering and seeded report values.

Spec: docs/review/speed.md. Reference paths below retain the pre-optimization work.
These are regression checks, not the golden replay (which Opus runs separately).
"""

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pytest
from conftest import build_series
from test_speed_same_results import random_candles, random_walk_m1

from backtester.analytics import daily
from backtester.analytics import random_fills as fills
from backtester.core.models import Direction, Timeframe
from backtester.core.series import CandleSeries, SeriesView
from backtester.detectors.atr import Atr, StrongMoveConfig, StrongMoveFilter
from backtester.detectors.bos import BosDetector
from backtester.detectors.bpr import BprConfig, BprDetector
from backtester.detectors.breaker import BreakerDetector
from backtester.detectors.fvg import FvgConfig, FvgDetector
from backtester.detectors.order_block import OrderBlockConfig, OrderBlockDetector
from backtester.detectors.sweep import SweepConfig, SweepDetector, beyond, wick
from backtester.detectors.swings import SwingDetector, is_doji
from backtester.detectors.zone import ZoneBox, ZoneKind
from backtester.engine.costs import SymbolCosts
from backtester.risk import monte_carlo as mc
from backtester.strategy.ny_index_sweep.frames import Frame
from backtester.strategy.session_zone_sweep.journal import (
    SessionJournal,
    _confluence_dict,
    _iso,
    _record_order,
    _zone_dict,
)
from backtester.strategy.session_zone_sweep.strategy import SessionZoneSweep
from backtester.strategy.trend_following.config import Signal, TrendFollowingConfig
from backtester.strategy.trend_following.strategy import TrendFollowing


def independent_detectors(doji, fvg, ob):
    return (
        FvgDetector(doji, fvg),
        OrderBlockDetector(doji, ob),
        BreakerDetector(doji),
        BprDetector(doji, BprConfig(fvg)),
    )


@pytest.mark.parametrize("filtered", [False, True])
@pytest.mark.parametrize("different_periods", [False, True])
def test_shared_frame_matches_independent_detectors_at_every_close(filtered, different_periods):
    fc = FvgConfig(filtered, StrongMoveConfig(3, 0.8))
    oc = OrderBlockConfig(filtered, StrongMoveConfig(5 if different_periods else 3, 1.1))
    frame = Frame(Timeframe.M5, 0.1, fc, oc, tp_levels=True, atr_period=3)
    standalone = independent_detectors(0.1, fc, oc)
    bos, atr = BosDetector(SwingDetector(0.1)), Atr(3)
    series = CandleSeries("X", Timeframe.M5, random_candles(600, 31))
    expected_recent = []
    expected_untapped = {}
    events_seen = set()
    for i in range(len(series)):
        view = series.view(i)
        expected_breaks = bos.update(view)
        expected_atr = atr.update(view)
        events = [e for detector in standalone for e in detector.update(view)]
        frame.update(view)
        assert frame.breaks == expected_breaks
        assert frame.structure.swings == bos.swings
        assert frame.atr() == expected_atr
        created = []
        for event in events:
            assert event.confirmed_index == i
            events_seen.add(type(event).__name__)
            if hasattr(event, "state"):
                expected_untapped.pop(event.zone, None)
            else:
                created.append(event.zone)
                expected_recent.append(event.zone)
                expected_untapped[event.zone] = event.zone
        assert [z.box for z in frame.new_zones] == created
        assert [z.box for z in frame.recent] == expected_recent
        assert [z.box for z in frame.untapped.values()] == list(expected_untapped.values())
        frame.update(view)  # same closed view cannot emit anything twice
        assert not frame.closed and frame.new_zones == [] and frame.breaks == []
    assert {"FairValueGap", "OrderBlock", "BreakerBlock", "BalancedPriceRange"} <= events_seen
    # Extending the underlying history cannot change a prefix, even with batched updates.
    prefix = Frame(Timeframe.M5, 0.1, fc, oc, tp_levels=True, atr_period=3)
    prefix.update(CandleSeries("X", Timeframe.M5, list(series.view(299))).view(299))
    extended = Frame(Timeframe.M5, 0.1, fc, oc, tp_levels=True, atr_period=3)
    extended.update(series.view(299))
    assert prefix.recent == extended.recent and prefix.breaks == extended.breaks
    assert prefix.untapped == extended.untapped


def test_frame_computes_fvg_bos_swings_and_each_atr_period_once(monkeypatch):
    calls = {cls: 0 for cls in (FvgDetector, BosDetector, SwingDetector, Atr)}
    for cls in calls:
        original = cls.update

        def counted(self, view, _cls=cls, _original=original, **kw):
            calls[_cls] += 1
            return _original(self, view, **kw)

        monkeypatch.setattr(cls, "update", counted)
    frame = Frame(Timeframe.M5, 0.1, FvgConfig(), OrderBlockConfig(), atr_period=14)
    series = CandleSeries("X", Timeframe.M5, random_candles(30, 4))
    frame.update(series.view(29))
    assert calls == dict.fromkeys(calls, 30)


class BackwardScanSweep(SweepDetector):
    """Original cancellation including doji skipping, candidate changes and wick-first."""

    def _cancel_breakout(self, view, direction, side):
        if side.candidate is None:
            return
        level = side.candidate.swept[-1].price
        counted, closes = 0, []
        for i in range(view.cursor, -1, -1):
            candle = view[i]
            if is_doji(candle, self.doji_max_body):
                continue
            closed = beyond(direction, candle.close, level)
            wick_only = self.config.cancel_wick_first and counted > 0
            if not (beyond(direction, wick(direction, candle), level) if wick_only else closed):
                return
            counted += 1
            if closed:
                closes.append(candle.close)
            if counted == self.config.cancel_closes:
                break
        else:
            return
        accepted = min(closes) if direction is Direction.BEARISH else max(closes)
        side.levels = [s for s in side.levels if not beyond(direction, accepted, s.price)]
        side.candidate = None


@pytest.mark.parametrize("wick_first", [False, True])
@pytest.mark.parametrize("count", [1, 2, 3, 7])
def test_incremental_sweep_cancellation_matches_backward_scan(wick_first, count):
    config = SweepConfig(two_closes_cancel=True, cancel_wick_first=wick_first, cancel_closes=count)
    fast, slow = SweepDetector(0.1, config), BackwardScanSweep(0.1, config)
    candles = random_candles(450, 9)
    # Long runs of dojis with changing wicks must neither count nor reset the streak.
    for i in range(70, 130):
        candles[i] = replace(candles[i], open=candles[i].close)
    series = CandleSeries("X", Timeframe.M5, candles)
    for i in range(len(series)):
        assert fast.update(series.view(i)) == slow.update(series.view(i))
        assert fast._sides == slow._sides


def test_sweep_long_doji_run_has_linear_candle_reads(monkeypatch):
    candles = list(
        build_series(
            [
                (10.0, 11.0, 9.5, 10.8),
                (10.8, 10.9, 10.0, 10.2),
                (10.2, 10.6, 9.8, 10.5),
                (10.5, 11.5, 10.4, 11.3),
                (11.3, 11.4, 10.9, 11.0),
                (11.0, 11.3, 10.95, 11.2),
                (11.2, 11.8, 11.1, 11.7),
            ]
        ).view(6)
    )
    last = candles[-1]
    candles += [
        replace(last, ts=last.ts + timedelta(minutes=5 * i), open=last.close, high=last.high + i)
        for i in range(1, 501)
    ]
    series = CandleSeries("X", Timeframe.M5, candles)
    calls = 0
    original = SeriesView.__getitem__

    def counted(self, index):
        nonlocal calls
        calls += 1
        return original(self, index)

    monkeypatch.setattr(SeriesView, "__getitem__", counted)
    detector = SweepDetector(0.1, SweepConfig(two_closes_cancel=True, bos_within=1000))
    for i in range(len(series)):
        detector.update(series.view(i))
    assert calls < 30 * len(series)


def original_records(journal, run_end):
    out = []
    for session in sorted(journal._sessions, key=lambda s: s.start):
        zones = [r for r in journal._zones.values() if r.zone.active_in == session]
        confluences = [r for (s, _), r in journal._confluences.items() if s == session]
        out.append(
            {
                "session": session.session.value,
                "trading_date": session.trading_date.isoformat(),
                "start": _iso(session.start),
                "end": _iso(session.end),
                "zones": [_zone_dict(r, run_end) for r in zones],
                "confluences": [
                    _confluence_dict(r, run_end) for r in sorted(confluences, key=_record_order)
                ],
            }
        )
    return out


def test_session_records_preserve_group_order_and_export_does_not_mutate(monkeypatch):
    from backtester.data.adapters.cache_adapter import candles_from_frame
    from backtester.data.resample import resample
    from backtester.engine.backtest import run_backtest

    m1 = random_walk_m1(10, 7)
    strategy = SessionZoneSweep("XAUUSD")
    series = [
        CandleSeries("XAUUSD", tf, candles_from_frame(resample(m1, tf)))
        for tf in dict.fromkeys(strategy.timeframes)
    ]
    run_backtest(strategy, series)
    fast = strategy.session_records()
    assert len(fast) > 10 and any(r["confluences"] for r in fast)
    monkeypatch.setattr(SessionJournal, "records", original_records)
    assert strategy.session_records() == fast
    assert strategy.session_records() == fast


@pytest.mark.parametrize("signal", list(Signal))
def test_trend_signal_matches_all_indicators_with_only_selected_indicator_updated(signal):
    config = TrendFollowingConfig(
        signal=signal,
        breakout_period=3,
        sma_period=3,
        momentum_period=3,
        kama_er_period=3,
        kama_filter_period=3,
    )
    fast, reference = TrendFollowing("X", config), TrendFollowing("X", config)
    selected = {
        Signal.BREAKOUT: "_channel",
        Signal.SMA: "_sma_cross",
        Signal.MOMENTUM: "_momentum",
        Signal.DUNNIGAN: "_dunnigan",
        Signal.KAMA: "_kama",
    }

    class Unused:
        def update(self, *args):
            pytest.fail("an unselected indicator was updated")

    for option, name in selected.items():
        if option is not signal:
            setattr(fast, name, Unused())
    for candle in random_candles(120, 15):
        channel = reference._channel.update(candle)
        sma = reference._sma_cross.update(candle.close, 1.0)
        reference._kama.update(candle.close)
        momentum = reference._momentum.update(candle.close)
        dunnigan = reference._dunnigan.update(candle)
        breakout = (
            None
            if channel is None
            else (
                Direction.BULLISH
                if candle.close > channel[0]
                else Direction.BEARISH
                if candle.close < channel[1]
                else None
            )
        )
        expected = {
            Signal.BREAKOUT: breakout,
            Signal.SMA: sma,
            Signal.KAMA: reference._kama.signal,
            Signal.MOMENTUM: momentum,
            Signal.DUNNIGAN: dunnigan,
        }[signal]
        assert fast._event(candle, 1.0) is expected


def test_daily_lookup_preserves_dst_weekend_outside_period_and_accumulation_order():
    start, end = date(2026, 3, 27), date(2026, 4, 2)
    stamps = [
        datetime(2026, 3, 25, tzinfo=UTC),
        datetime(2026, 3, 28, tzinfo=UTC),
        datetime(2026, 3, 29, 22, 30, tzinfo=UTC),
        datetime(2026, 4, 5, tzinfo=UTC),
    ]
    trades = [
        SimpleNamespace(exit_time=t, r_net=r)
        for t, r in zip(stamps, [1e16, 1.0, -1e16, 3.0], strict=True)
    ]
    days = daily.weekdays(start, end)
    expected = np.zeros(len(days))
    for trade in trades:
        d = trade.exit_time.astimezone(daily.PRAGUE).date()
        i = next((k for k, w in enumerate(days) if w >= d), len(days) - 1)
        expected[i] += trade.r_net
    np.testing.assert_array_equal(daily.daily_net_r(trades, start, end), expected)
    assert daily.daily_net_r(trades, date(2026, 3, 28), date(2026, 3, 29)).size == 0


@pytest.mark.parametrize("n", [0, 1, 7, 8, 15, 127, 128, 129, 255, 257, 1100])
def test_random_fill_totals_are_bit_identical_to_matrix_algorithm(n):
    config = fills.RandomFillsConfig(runs=13, seed=17)
    costs = {"X": SymbolCosts(0.0, 0.0, 1, slippage=0.1)}
    trades = [
        SimpleNamespace(
            symbol="X",
            entry=100.0,
            initial_stop=98.0,
            exit_reason="stop_loss",
            r_net=(-1.0) ** i * (i + 0.1),
            limit_fill=i % 3 == 0,
            parts=[
                {"reason": "stop_loss", "share": 0.25},
                {"reason": "take_profit", "share": 0.75},
            ],
        )
        for i in range(n)
    ]
    rng = np.random.default_rng(config.seed)
    reduction = np.zeros((config.runs, n))
    base = np.array([t.r_net for t in trades])
    for i, trade in enumerate(trades):
        for bound in fills.max_slippage_r(trade, 0.1, config):
            reduction[:, i] += rng.uniform(0.0, bound, config.runs) if bound > 0 else 0.0
    expected = (base - reduction).sum(axis=1)
    got = fills.random_fills(trades, config, costs)
    assert [r.hex() for r in got.run_net_r] == [float(r).hex() for r in expected]
    assert got.base_net_r == float(base.sum())
    assert (got.p5, got.p50, got.p95) == tuple(np.percentile(expected, [5, 50, 95]))


def test_risk_independent_streaks_are_reused_across_risk_levels(monkeypatch):
    start = datetime(2026, 1, 5, 10, tzinfo=UTC)
    trades = [
        SimpleNamespace(
            entry_time=start + timedelta(days=i),
            exit_time=start + timedelta(days=i, hours=1),
            r_net=r,
        )
        for i, r in enumerate([1.0, -1.0, -0.5, 2.0, -1.0] * 4)
    ]
    config = mc.MonteCarloConfig(runs=5, risk_levels=(0.005, 0.01, 0.02), month_days=3)
    expected = {
        risk: mc.run_monte_carlo(
            trades, start.date(), date(2026, 2, 1), replace(config, risk_levels=(risk,))
        )["risks"][risk]
        for risk in config.risk_levels
    }
    calls = 0
    original = mc.longest_streak

    def counted(*args):
        nonlocal calls
        calls += 1
        return original(*args)

    monkeypatch.setattr(mc, "longest_streak", counted)
    actual = mc.run_monte_carlo(trades, start.date(), date(2026, 2, 1), config)
    assert actual["risks"] == expected
    assert calls == config.runs + 1


def test_hash_heavy_zone_values_are_not_hashed_during_session_run(monkeypatch):
    from backtester.detectors.zone import ZoneTransition
    from backtester.strategy.session_zone_sweep.signals import SetupTracker

    tracker = SetupTracker("XAUUSD")
    series = CandleSeries("XAUUSD", Timeframe.M5, random_candles(150, 2))

    # Detectors and validators use ids internally; strategy membership must do so too.
    def forbidden_hash(self):
        pytest.fail("a full ZoneBox was hashed")

    monkeypatch.setattr(ZoneBox, "__hash__", forbidden_hash)
    for i in range(len(series)):
        view = series.view(i)
        tracker.update(view.current.ts + Timeframe.M5.duration, view, None)
    assert any(isinstance(e, ZoneTransition) for e in tracker.zone_transitions) or tracker._usable


def test_journal_equal_distinct_boxes_share_one_record_and_bpr_ranges_stay_distinct():
    from backtester.detectors.swings import SwingKind
    from backtester.sessions import session_of
    from backtester.strategy.session_zone_sweep.signals import SetupLink
    from backtester.strategy.session_zone_sweep.zones import SessionZone

    view = CandleSeries("X", Timeframe.M5, random_candles(3, 1)).view(2)
    now = view.current.ts + Timeframe.M5.duration
    session = session_of(now)
    zone = SessionZone(2, now, SwingKind.HIGH, 102.0, 101.0, None, session, session, 0)
    box = ZoneBox(ZoneKind.BPR, Direction.BULLISH, 101.0, 100.0, 0, 2, now)
    other = replace(box, bottom=99.0)
    journal = SessionJournal()
    journal._on_link(SetupLink(zone, Direction.BULLISH, box, False), now, view)
    journal._on_link(SetupLink(zone, Direction.BULLISH, replace(box), True), now, view)
    journal._on_link(SetupLink(zone, Direction.BULLISH, other, False), now, view)
    assert len(journal._confluences) == 2
    assert next(iter(journal._confluences.values())).setup_confirmed


def test_session_zone_ids_distinguish_two_sessions_finalized_at_the_same_close():
    from backtester.detectors.swings import SwingKind
    from backtester.sessions import session_of
    from backtester.strategy.session_zone_sweep.zones import SessionZone

    view = CandleSeries("X", Timeframe.M5, random_candles(3, 1)).view(2)
    now = view.current.ts + Timeframe.M5.duration
    first, second = session_of(now), session_of(now + timedelta(hours=12))
    assert first != second
    # A data gap can finalize an old session and the current session on one update.
    zone = SessionZone(2, now, SwingKind.HIGH, 102.0, 101.0, None, first, second, 0)
    other = replace(zone, formed_in=second)
    journal = SessionJournal()
    journal._on_zone_event(zone, view)
    journal._on_zone_event(other, view)
    assert [r.zone for r in journal._zones.values()] == [zone, other]


@pytest.mark.parametrize("cursor", [1, 2])
def test_standalone_filter_preserves_out_of_order_value_error(cursor):
    view = build_series([(100.0, 101.0, 99.0, 100.0)] * 3).view(cursor)
    with pytest.raises(ValueError, match="once per candle in order"):
        StrongMoveFilter().update(view)


def test_obstacle_tracker_shares_swings_with_its_order_blocks(monkeypatch):
    from backtester.strategy.session_zone_sweep.targets import ObstacleTracker

    calls = 0
    original = SwingDetector.update

    def counted(self, view):
        nonlocal calls
        calls += 1
        return original(self, view)

    monkeypatch.setattr(SwingDetector, "update", counted)
    tracker = ObstacleTracker(0.1)
    series = CandleSeries("X", Timeframe.H1, random_candles(30, 4))
    for i in range(len(series)):
        tracker.update(series.view(i))
    assert calls == len(series)


def test_random_fills_allocations_are_bounded_in_trade_count(monkeypatch):
    original = np.zeros
    shapes = []
    # SeedSequence has its own unrelated one-dimensional zero allocation. Seed
    # before instrumenting the report's working arrays.
    rng = np.random.default_rng(42)
    monkeypatch.setattr(np.random, "default_rng", lambda seed: rng)

    def counted(shape, *args, **kwargs):
        shapes.append(shape)
        return original(shape, *args, **kwargs)

    monkeypatch.setattr(np, "zeros", counted)
    trade = SimpleNamespace(
        symbol="X", entry=100.0, initial_stop=98.0, exit_reason="stop_loss", r_net=-1.0
    )
    fills.random_fills(
        [trade] * 5000,
        fills.RandomFillsConfig(runs=13),
        {"X": SymbolCosts(0.0, 0.0, 1, slippage=0.1)},
    )
    assert shapes and all(shape[0] == 13 and shape[1] <= 128 for shape in shapes)
