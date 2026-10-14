"""Rolling channel, SMA and KAMA of strategy 4, incremental and lookahead-free.
Spec: docs/strategy-trend-following.md › Trend signal."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backtester.core.models import Candle, Direction
from backtester.strategy.trend_following.indicators import Kama, RollingChannel, Sma

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
T0 = datetime(2026, 1, 5, tzinfo=UTC)


def candle(i, high, low, close=None):
    close = (high + low) / 2 if close is None else close
    return Candle(ts=T0 + timedelta(hours=4 * i), open=close, high=high, low=low, close=close)


def test_channel_is_over_the_previous_n_candles_and_excludes_the_current():
    ch = RollingChannel(3)
    seen = []
    for i, (h, lo) in enumerate([(10, 9), (11, 8), (12, 9.5), (13, 7)]):
        seen.append(ch.update(candle(i, h, lo)))
    # before candle 3: highs 10, 11, 12 and lows 9, 8, 9.5 -> (12, 8); nothing earlier
    assert seen[:3] == [None, None, None]
    assert seen[3] == (12, 8)


def test_channel_window_slides():
    ch = RollingChannel(2)
    out = [
        ch.update(candle(i, h, lo)) for i, (h, lo) in enumerate([(5, 1), (9, 2), (6, 3), (4, 3)])
    ]
    assert out == [None, None, (9, 1), (9, 2)]  # candle 3 sees candles 1 and 2; candle 0 left


def test_sma_value_after_n_closes():
    sma = Sma(3)
    assert [sma.update(c) for c in (1.0, 2.0, 6.0, 9.0)] == [None, None, 3.0, pytest.approx(17 / 3)]


def test_kama_matches_a_hand_computed_value():
    # er=2, fast=2, slow=30. Seed = close of candle 2 (the first with an ER): 13.
    # candle 3: ER = |12 - 11| / (|13 - 11| + |12 - 13|) = 1/3
    # SC = (1/3 * (2/3 - 2/31) + 2/31)^2 = (74/279)^2 = 0.0703485
    # KAMA = 13 + SC * (12 - 13) = 12.9296515
    k = Kama(er_period=2, fast=2, slow=30, filter_mult=0.0, filter_period=3)
    values = [k.update(c) for c in (10.0, 11.0, 13.0, 12.0)]
    assert values[:2] == [None, None]
    assert values[2] == 13.0
    assert values[3] == pytest.approx(12.9296515, abs=1e-6)
    assert k.last_change == pytest.approx(-0.0703485, abs=1e-6)


def test_kama_efficiency_ratio_is_zero_when_price_does_not_move():
    k = Kama(er_period=2, fast=2, slow=30, filter_mult=0.0, filter_period=3)
    for c in (10.0, 10.0, 10.0, 10.0):
        k.update(c)
    assert k.last_change == 0.0  # ER 0 -> SC (2/31)^2, close == KAMA -> no change


def test_kama_signal_needs_the_filter_period_of_changes():
    # er=1: ER is 1 on every move, SC = (2/3)^2 = 4/9. Seed K1 = 10 (close of candle 1).
    # candle 2 (11): K = 10.4444, d2 = 0.4444
    # candle 3 (12): K = 11.1358, d3 = 0.6914
    # candle 4 (13): K = 11.9644, d4 = 0.8286 -> three changes exist from candle 4 on
    closes = [10.0, 10.0, 11.0, 12.0, 13.0, 14.0]
    k = Kama(1, 2, 30, filter_mult=0.0, filter_period=3)
    signals = []
    for c in closes:
        k.update(c)
        signals.append(k.signal)
    # filter 0 = any rise, but not before three changes exist (candle 4)
    assert signals == [None, None, None, None, LONG, LONG]


def test_kama_filter_is_a_multiple_of_the_sample_std_of_the_last_changes():
    # std (n-1) of (0.4444, 0.6914, 0.8286) = 0.19469; d4 = 0.8286
    closes = [10.0, 10.0, 11.0, 12.0, 13.0]
    for mult, expected in ((2.0, LONG), (4.0, LONG), (5.0, None)):  # 5 x 0.19469 = 0.973 > d4
        k = Kama(1, 2, 30, filter_mult=mult, filter_period=3)
        for c in closes:
            k.update(c)
        assert k.signal is expected, mult


def test_kama_falling_market_is_the_mirror():
    closes = [20 - c for c in (10.0, 10.0, 11.0, 12.0, 13.0)]
    k = Kama(1, 2, 30, filter_mult=2.0, filter_period=3)
    for c in closes:
        k.update(c)
    assert k.signal is SHORT


def test_kama_change_equal_to_the_filter_is_no_signal():
    k = Kama(1, 2, 30, filter_mult=0.0, filter_period=3)
    for c in (10.0, 10.0, 10.0, 10.0, 10.0, 10.0):
        k.update(c)
    assert k.signal is None  # KAMA - KAMA[1] = 0 is not > 0
