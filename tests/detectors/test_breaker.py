"""Breaker block. Spec: confluences.md › Breaker block, › Validation.

Candles are (open, high, low, close); M5 from Mon 2026-01-05 00:00 UTC. Doji threshold 0.065.
"""

from __future__ import annotations

import random

import pytest
from conftest import build_series

from backtester.core.models import Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.detectors.breaker import BreakerBlock, BreakerDetector
from backtester.detectors.zone import ZoneKind, ZoneState, ZoneTransition

BULL, BEAR = Direction.BULLISH, Direction.BEARISH

# Swing high 10.3 (@0, confirmed 1), swing low 9.6 (@2), a doji, then the move up into the
# swing high 10.6: green 4 (high 10.28) + red 5 (high 10.6, the swing's wick). Candle 7
# closes above 10.6: bullish BOS (the first on the chart). The breaker is the green run into
# 10.6, walking back from candle 4: 4 green, 3 doji (skipped, its 9.5 wick doesn't count),
# 2 green, 1 red (ends the run) -> 9.6 - 10.28 (the red turn candle's 10.6 is not in it).
UP = [
    (10.0, 10.3, 9.9, 10.2),  # 0 green
    (10.2, 10.25, 9.7, 9.8),  # 1 red: swing high 10.3
    (9.8, 10.0, 9.6, 9.95),  # 2 green: swing low 9.6
    (9.95, 10.05, 9.5, 9.96),  # 3 doji
    (9.96, 10.28, 9.9, 10.25),  # 4 green
    (10.25, 10.6, 10.1, 10.15),  # 5 red: swing high 10.6 (wick on the red candle)
    (10.15, 10.3, 10.05, 10.25),  # 6 green: swing low 10.05
    (10.25, 10.8, 10.2, 10.75),  # 7 green: closes above 10.6 -> bullish BOS
]
TAP = (10.75, 10.78, 10.2, 10.3)  # 8 red: wick below 10.28
CONFIRM = (10.3, 10.5, 10.25, 10.45)  # 9 green: close above 10.28


def run(ohlc, series=None):
    series = series or build_series(ohlc)
    detector = BreakerDetector(0.065)
    return [e for i in range(len(series)) for e in detector.update(series.view(i))]


def blocks(events):
    return [e for e in events if isinstance(e, BreakerBlock)]


def test_the_green_run_into_the_broken_high_from_the_bos_candle():
    (b,) = blocks(run(UP))
    z = b.zone
    assert z.kind is ZoneKind.BREAKER and z.direction is BULL
    assert (z.bottom, z.top) == (9.6, 10.28)
    assert (z.start_index, z.created_index, b.confirmed_index) == (2, 7, 7)
    assert b.swing.price == 10.6 and b.bos.confirmed_index == 7
    assert blocks(run(UP[:7])) == []  # nothing before the BOS candle


def test_bearish_is_mirrored():
    down = [(20 - o, 20 - lo, 20 - h, 20 - c) for o, h, lo, c in UP]
    (b,) = blocks(run(down))
    z = b.zone
    assert z.direction is BEAR
    assert (z.bottom, z.top) == (pytest.approx(9.72), pytest.approx(10.4))
    assert (z.start_index, z.created_index) == (2, 7)


def test_tap_then_green_close_confirms():
    events = run([*UP, TAP, CONFIRM])
    steps = [(t.state, t.confirmed_index) for t in events if isinstance(t, ZoneTransition)]
    assert steps == [(ZoneState.TAPPED, 8), (ZoneState.CONFIRMED, 9)]


def test_a_close_below_invalidates():
    # 8 closes below 9.6: the breaker is invalidated (and a bearish BOS of 10.05 makes a
    # bearish breaker of the red run into that low: candle 5, 10.1 - 10.6)
    events = run([*UP, (10.75, 10.78, 9.5, 9.55)])
    steps = [(t.state, t.zone.direction) for t in events if isinstance(t, ZoneTransition)]
    assert steps == [(ZoneState.INVALIDATED, BULL)]
    bear = blocks(events)[1].zone
    assert (bear.direction, bear.bottom, bear.top, bear.start_index) == (BEAR, 10.1, 10.6, 5)


def random_walk(n=800, seed=3):
    rng = random.Random(seed)
    ohlc, price = [], 100.0
    for _ in range(n):
        o = price
        c = o + rng.choice([-1, 1]) * rng.choice([0.0, 0.03, 0.5, 1.2])
        ohlc.append((o, max(o, c) + rng.random(), min(o, c) - rng.random(), c))
        price = c
    return build_series(ohlc)


def test_no_lookahead_events_only_from_their_confirming_candle_and_never_rewritten():
    series = random_walk()
    full = run(None, series=series)
    assert {b.zone.direction for b in blocks(full)} == {BULL, BEAR}
    detector, seen = BreakerDetector(0.065), []
    for i in range(len(series)):
        new = detector.update(series.view(i))
        for e in new:
            assert e.confirmed_index == i
            if isinstance(e, BreakerBlock):
                # the run lies before the swing's confirmation, the swing before the BOS
                assert e.zone.start_index <= e.swing.index <= e.swing.confirmed_index < i
        seen.extend(new)
        if i % 97 == 0:
            short = CandleSeries("TEST", Timeframe.M5, list(series.view(i)))
            assert run(None, series=short) == seen
    assert seen == full


def test_update_out_of_order_raises():
    series = build_series(UP)
    detector = BreakerDetector(0.065)
    detector.update(series.view(0))
    with pytest.raises(ValueError):
        detector.update(series.view(0))
