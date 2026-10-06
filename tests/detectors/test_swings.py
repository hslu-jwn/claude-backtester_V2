"""Swing high / low. Spec: confluences.md › Swing high / low.

Candles are (open, high, low, close); M5 from Mon 2026-01-05 00:00 UTC, so candle i closes
at 00:05 + 5 min * i. Doji threshold 0.065 (gold) unless stated.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pytest
from conftest import build_series

from backtester.core.models import Candle, Timeframe
from backtester.core.series import CandleSeries
from backtester.detectors.swings import (
    DOJI_RANGE_SHARE,
    SwingConfig,
    SwingDetector,
    SwingKind,
    equivalent_doji_body,
)
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig

HIGH, LOW = SwingKind.HIGH, SwingKind.LOW


def run(ohlc, doji=0.065, series=None):
    series = series or build_series(ohlc)
    detector = SwingDetector(doji)
    return [e for i in range(len(series)) for e in detector.update(series.view(i))]


def summary(events):
    """(kind, price, extreme candle, confirming candle) per swing."""
    return [(e.kind, e.price, e.index, e.confirmed_index) for e in events]


def test_spec_example_only_the_two_turn_candles_count():
    # green high 4410, green high 4408, red high 4405 -> swing high 4408, not 4410
    events = run(
        [
            (4400.0, 4410.0, 4399.0, 4405.0),  # green, high 4410
            (4403.0, 4408.0, 4402.0, 4407.0),  # green, high 4408 (last green)
            (4404.0, 4405.0, 4398.0, 4399.0),  # red, high 4405: the turn
        ]
    )
    assert summary(events) == [(HIGH, 4408.0, 1, 2)]


def test_swing_high_takes_the_red_candles_wick_when_it_is_higher():
    events = run([(1.0, 2.0, 0.9, 1.9), (1.9, 2.5, 1.0, 1.2)])
    assert summary(events) == [(HIGH, 2.5, 1, 1)]


def test_swing_low_mirrored():
    # red low 0.5, green low 0.7 -> swing low 0.5 on candle 0, confirmed by candle 1
    events = run([(2.0, 2.1, 0.5, 1.0), (1.0, 1.8, 0.7, 1.7)])
    assert summary(events) == [(LOW, 0.5, 0, 1)]


def test_confirmed_at_the_close_of_the_turning_candle():
    (event,) = run([(1.0, 2.0, 0.9, 1.9), (1.9, 2.5, 1.0, 1.2)])
    assert event.confirmed_at == datetime(2026, 1, 5, 0, 10, tzinfo=UTC)
    assert event.ts == datetime(2026, 1, 5, 0, 5, tzinfo=UTC)


def test_same_color_candles_make_no_swing():
    assert run([(1.0, 1.5, 0.9, 1.4), (1.4, 1.9, 1.3, 1.8), (1.8, 2.0, 1.7, 1.9)]) == []


def test_dojis_between_turn_candles_are_skipped_and_their_wicks_ignored():
    events = run(
        [
            (1.00, 1.50, 0.90, 1.40),  # green, high 1.50
            (1.40, 9.00, 1.35, 1.43),  # doji (body 0.03), huge wick: ignored
            (1.43, 1.44, 1.42, 1.43),  # doji (body 0)
            (1.43, 1.48, 1.00, 1.10),  # red: turn
        ]
    )
    assert summary(events) == [(HIGH, 1.50, 0, 3)]


def test_body_exactly_at_the_threshold_is_a_doji():
    doji = (1.0, 1.2, 0.9, 1.065)  # body 0.065
    assert run([(1.0, 1.5, 0.9, 1.4), doji]) == []
    assert summary(run([(1.0, 1.5, 0.9, 1.4), (1.0, 1.6, 0.9, 0.93)])) == [(HIGH, 1.6, 1, 1)]


def test_a_doji_never_starts_or_turns_a_swing():
    # red after only dojis: no previous non-doji candle -> nothing
    assert run([(1.0, 1.1, 0.9, 1.0), (1.0, 1.1, 0.9, 1.03), (1.0, 1.1, 0.5, 0.6)]) == []


def test_turning_candle_also_starts_the_next_swing():
    events = run(
        [
            (1.0, 1.6, 0.9, 1.5),  # green
            (1.5, 1.7, 1.1, 1.2),  # red: high 1.7 (red wick)
            (1.2, 1.4, 1.0, 1.3),  # green: low 1.0 (green wick lower than red's 1.1)
            (1.3, 1.35, 1.25, 1.27),  # red, body 0.03 -> doji, skipped
            (1.3, 1.45, 0.95, 1.0),  # red: high 1.45 (vs green 1.4)
        ]
    )
    assert summary(events) == [(HIGH, 1.7, 1, 1), (LOW, 1.0, 2, 2), (HIGH, 1.45, 4, 4)]


def test_equal_wicks_pick_the_earlier_candle():
    events = run([(1.0, 2.0, 0.9, 1.5), (1.5, 2.0, 1.0, 1.1)])
    assert summary(events) == [(HIGH, 2.0, 0, 1)]


def test_swing_across_a_weekend_is_confirmed_by_the_first_candle_after_it():
    friday = datetime(2026, 1, 9, 21, 50, tzinfo=UTC)
    candles = [
        Candle(friday, 1.0, 1.5, 0.9, 1.4),  # Friday's last candle: green
        Candle(friday + timedelta(days=2, hours=2), 1.4, 1.45, 1.0, 1.1),  # Sunday open: red
    ]
    (event,) = run(None, series=CandleSeries("TEST", Timeframe.M5, candles))
    assert (event.kind, event.price, event.index) == (HIGH, 1.5, 0)
    assert event.confirmed_at == candles[1].ts + timedelta(minutes=5)


def test_no_lookahead_events_only_at_their_candle_and_never_rewritten():
    rng = random.Random(7)
    ohlc, price = [], 100.0
    for _ in range(400):
        o = price
        c = o + rng.choice([-1, 1]) * rng.choice([0.0, 0.03, 0.5, 1.2])
        ohlc.append((o, max(o, c) + rng.random(), min(o, c) - rng.random(), c))
        price = c
    series = build_series(ohlc)
    full = run(None, series=series)
    assert full  # the random walk does produce swings

    detector, seen = SwingDetector(0.065), []
    for i in range(len(series)):
        new = detector.update(series.view(i))
        assert all(e.confirmed_index == i and e.index <= i for e in new)
        seen.extend(new)
        # (b) a fresh run over a shorter history gives exactly the events emitted so far
        if i % 97 == 0:
            assert (
                run(None, series=CandleSeries("TEST", Timeframe.M5, list(series.view(i)))) == seen
            )
    assert seen == full


def test_update_out_of_order_or_twice_raises():
    series = build_series([(1.0, 1.5, 0.9, 1.4), (1.4, 1.5, 1.0, 1.1)])
    detector = SwingDetector(0.065)
    detector.update(series.view(0))
    with pytest.raises(ValueError):
        detector.update(series.view(0))


def test_config_gold_default_gbp_pairs_scaled_others_need_a_value():
    config = SwingConfig()
    assert config.doji_threshold("XAUUSD") == 0.065
    # same share of the median 5m range as gold (histdata 2026-09-02..30)
    assert config.doji_threshold("GBPUSD") == pytest.approx(0.00028 * 0.065 / 4.255)
    assert config.doji_threshold("GBPJPY") == pytest.approx(0.066 * 0.065 / 4.255)
    with pytest.raises(KeyError, match="EURUSD"):
        config.doji_threshold("EURUSD")
    assert SwingConfig({"GBPUSD": 0.00002}).doji_threshold("GBPUSD") == 0.00002
    with pytest.raises(ValueError):
        SwingConfig({"XAUUSD": -1.0})
    assert SessionZoneSweepConfig().swings == config


def test_equivalent_doji_body_scales_gold_by_typical_candle_range():
    assert equivalent_doji_body(4.255) == pytest.approx(0.065)
    assert equivalent_doji_body(0.0004) == pytest.approx(0.0004 * DOJI_RANGE_SHARE)
