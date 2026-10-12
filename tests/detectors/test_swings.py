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
from backtester.detectors.settings import DetectorSettings
from backtester.detectors.swings import (
    DOJI_RANGE_SHARE,
    RangeShare,
    SwingConfig,
    SwingDetector,
    SwingKind,
    equivalent_doji_body,
    is_doji,
)

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
        assert all(e.confirmed_index == i and e.first_index <= e.index <= i for e in new)
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
    # indices: median over 2020-01..2026-09 (user's choice, 2026-10-10)
    assert config.doji_threshold("NAS100") == pytest.approx(0.1767, abs=1e-4)
    assert config.doji_threshold("US500") == pytest.approx(0.0384, abs=1e-4)
    with pytest.raises(KeyError, match="EURUSD"):
        config.doji_threshold("EURUSD")
    assert SwingConfig({"GBPUSD": 0.00002}).doji_threshold("GBPUSD") == 0.00002
    with pytest.raises(ValueError):
        SwingConfig({"XAUUSD": -1.0})
    assert DetectorSettings().swings == config  # the shared default (RunSettings.detectors)


def test_equivalent_doji_body_scales_gold_by_typical_candle_range():
    assert equivalent_doji_body(4.255) == pytest.approx(0.065)
    assert equivalent_doji_body(0.0004) == pytest.approx(0.0004 * DOJI_RANGE_SHARE)


# --- doji as a share of the candle's own range (user, 2026-10-12; spec › Swing high / low) ---


def candle(o, h, low, c):
    return build_series([(o, h, low, c)]).view(0).current


def test_range_share_doji_is_a_body_up_to_that_share_of_the_candles_own_range():
    share = RangeShare(0.10)
    assert is_doji(candle(100.0, 110.0, 100.0, 101.0), share)  # body 1 = 10% of range 10
    assert not is_doji(candle(100.0, 110.0, 100.0, 101.01), share)
    assert is_doji(candle(100.0, 100.0, 100.0, 100.0), share)  # flat candle: no range, no body
    # the same body is a doji in a long candle and a real candle in a short one
    assert is_doji(candle(100.0, 160.0, 100.0, 105.0), share)
    assert not is_doji(candle(100.0, 106.0, 100.0, 105.0), share)


def test_a_plain_float_threshold_is_still_a_price_amount():
    assert not is_doji(candle(100.0, 160.0, 100.0, 105.0), 0.065)
    assert is_doji(candle(100.0, 160.0, 100.0, 100.05), 0.065)


def test_config_range_share_replaces_the_fixed_amounts_when_set():
    assert not isinstance(SwingConfig().doji_threshold("XAUUSD"), RangeShare)  # default: off
    threshold = SwingConfig(doji_range_share=0.1).doji_threshold("XAUUSD")
    assert isinstance(threshold, RangeShare) and threshold == 0.1
    # a symbol without a fixed amount still has a threshold in this mode
    assert SwingConfig(doji_range_share=0.1).doji_threshold("EURUSD") == 0.1


def test_config_rejects_a_range_share_outside_zero_to_one():
    with pytest.raises(ValueError):
        SwingConfig(doji_range_share=-0.1)
    with pytest.raises(ValueError):
        SwingConfig(doji_range_share=1.5)


def test_a_wide_thin_candle_is_skipped_by_swings_in_range_share_mode():
    # the big green candle 2 is a doji by share (body 5 of range 100) but not by 0.065
    ohlc = [
        (100.0, 110.0, 99.0, 108.0),  # 0 green
        (108.0, 109.0, 100.0, 101.0),  # 1 red: swing high 110 (wick of 0)
        (101.0, 160.0, 60.0, 106.0),  # 2 body 5, range 100: doji by share
        (106.0, 107.0, 95.0, 96.0),  # 3 red
    ]
    # fixed amount: candle 2 is a real candle, it makes a swing low 60 and a swing high 160
    assert summary(run(ohlc)) == [(HIGH, 110.0, 0, 1), (LOW, 60.0, 2, 2), (HIGH, 160.0, 2, 3)]
    # share: candle 2 is skipped with its huge wicks, only the first swing remains
    assert summary(run(ohlc, doji=RangeShare(0.10))) == [(HIGH, 110.0, 0, 1)]
