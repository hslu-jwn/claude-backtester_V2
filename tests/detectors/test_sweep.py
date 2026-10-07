"""Liquidity sweep. Spec: confluences.md › Liquidity sweep.

Candles are (open, high, low, close); M5 from Mon 2026-01-05 00:00 UTC, so candle i closes
at 00:05 + 5 min * i. Doji threshold 0.065.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime

import pytest
from conftest import build_series

from backtester.core.models import Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.detectors.sweep import SweepDetector

BULL, BEAR = Direction.BULLISH, Direction.BEARISH

# Uptrend: swing high 11.0 (wick @0, confirmed 1), swing low 9.8 (@2), bullish BOS of 11.0
# at candle 3 (top 11.5, takes the broken high), swing high 11.5 confirmed 4, swing low
# 10.9 confirmed 5, then candle 6 runs to 11.8 (takes 11.0 and 11.5): the top so far.
UP = [
    (10.0, 11.0, 9.5, 10.8),  # 0 green
    (10.8, 10.9, 10.0, 10.2),  # 1 red: swing high 11.0
    (10.2, 10.6, 9.8, 10.5),  # 2 green: swing low 9.8
    (10.5, 11.5, 10.4, 11.3),  # 3 green: bullish BOS of 11.0 -> uptrend
    (11.3, 11.4, 10.9, 11.0),  # 4 red: swing high 11.5
    (11.0, 11.3, 10.95, 11.2),  # 5 green: swing low 10.9
    (11.2, 11.8, 11.1, 11.7),  # 6 green: wick to 11.8, above 11.5 and 11.0
]


def run(ohlc, series=None):
    series = series or build_series(ohlc)
    detector = SweepDetector(0.065)
    return [e for i in range(len(series)) for e in detector.update(series.view(i))]


def summary(events):
    """(direction, sweeping candle, its wick, most extreme swing taken, BOS candle)."""
    return [(e.direction, e.index, e.extreme, e.swing.price, e.confirmed_index) for e in events]


def test_a_new_high_followed_by_a_bearish_bos_is_a_sweep_from_the_bos_candle():
    ohlc = [
        *UP,
        (11.7, 11.75, 11.2, 11.3),  # 7 red: swing high 11.8
        (11.3, 11.35, 10.8, 10.85),  # 8 red: closes below the low 10.9 -> bearish BOS
    ]
    (sweep,) = run(ohlc)
    assert summary([sweep]) == [(BEAR, 6, 11.8, 11.5, 8)]
    assert [s.price for s in sweep.swept] == [11.0, 11.5]  # the broken high counts too
    assert sweep.bos.direction is BEAR and sweep.bos.price == 10.9
    assert sweep.confirmed_at == datetime(2026, 1, 5, 0, 45, tzinfo=UTC)
    # nothing before the BOS candle: the candidate isn't a sweep yet
    assert run(ohlc[:8]) == []


def test_a_new_high_with_no_bos_is_no_sweep():
    ohlc = [*UP, (11.7, 12.0, 11.65, 11.95)]  # 7 green: the uptrend just goes on
    assert run(ohlc) == []


def test_a_higher_high_replaces_the_earlier_top():
    ohlc = [
        *UP,
        (11.7, 11.75, 11.4, 11.5),  # 7 red: swing high 11.8
        (11.5, 12.0, 11.45, 11.9),  # 8 green: swing low 11.4, wick 12.0 takes 11.8 too
        (11.9, 11.95, 11.3, 11.35),  # 9 red: closes below 11.4 -> bearish BOS
    ]
    (sweep,) = run(ohlc)
    assert summary([sweep]) == [(BEAR, 8, 12.0, 11.8, 9)]
    assert [s.price for s in sweep.swept] == [11.0, 11.5, 11.8]


def test_an_equal_top_does_not_replace_the_earlier_one():
    ohlc = [
        *UP,
        (11.7, 11.75, 11.4, 11.5),  # 7 red: swing high 11.8
        (11.5, 11.8, 11.45, 11.7),  # 8 green: wick exactly 11.8, swing low 11.4
        (11.7, 11.72, 11.3, 11.35),  # 9 red: bearish BOS of 11.4
    ]
    assert summary(run(ohlc)) == [(BEAR, 6, 11.8, 11.5, 9)]


def test_a_lower_high_before_the_bos_does_not_matter():
    ohlc = [
        *UP,
        (11.7, 11.75, 11.2, 11.3),  # 7 red: swing high 11.8
        (11.3, 11.6, 11.25, 11.55),  # 8 green: swing low 11.2, wick below the top
        (11.55, 11.58, 11.25, 11.3),  # 9 red: lower high 11.6, close above 11.2
        (11.3, 11.35, 11.0, 11.05),  # 10 red: closes below 11.2 -> bearish BOS
    ]
    assert summary(run(ohlc)) == [(BEAR, 6, 11.8, 11.5, 10)]


def test_the_bos_candle_alone_sweeps_the_high_it_broke():
    # spec example: a bullish BOS closes above a high, price runs a bit higher, then a
    # bearish BOS: the top took the broken high
    ohlc = [
        *UP[:4],
        (11.3, 11.4, 10.9, 11.0),  # 4 red: swing high 11.5 (no higher candle after it)
        (11.0, 11.3, 10.95, 11.2),  # 5 green: swing low 10.9
        (11.2, 11.25, 10.7, 10.75),  # 6 red: bearish BOS of 10.9
    ]
    (sweep,) = run(ohlc)
    assert summary([sweep]) == [(BEAR, 3, 11.5, 11.0, 6)]


def test_a_doji_wick_can_sweep_and_becomes_the_top():
    ohlc = [
        *UP,
        (11.7, 11.9, 11.65, 11.72),  # 7 doji: wick 11.9 above the top 11.8
        (11.72, 11.75, 11.2, 11.3),  # 8 red: swing high 11.8 (the doji's wick doesn't count)
        (11.3, 11.35, 10.8, 10.85),  # 9 red: bearish BOS of 10.9
    ]
    (sweep,) = run(ohlc)
    assert summary([sweep]) == [(BEAR, 7, 11.9, 11.5, 9)]


def test_one_candle_can_sweep_and_make_the_bos():
    ohlc = [*UP[:6], (11.2, 11.9, 10.7, 10.75)]  # 6 red: wick above 11.5, close below 10.9
    assert summary(run(ohlc)) == [(BEAR, 6, 11.9, 11.5, 6)]


def test_before_the_first_bos_every_confirmed_high_counts():
    ohlc = [
        (10.0, 11.0, 9.5, 10.8),  # 0 green
        (10.8, 10.9, 10.0, 10.2),  # 1 red: swing high 11.0
        (10.2, 11.2, 10.1, 10.9),  # 2 green: swing low 10.0, wick above 11.0 (no BOS yet)
        (10.9, 10.95, 9.8, 9.85),  # 3 red: first BOS on the chart, bearish of 10.0
    ]
    assert summary(run(ohlc)) == [(BEAR, 2, 11.2, 11.0, 3)]


# Downtrend: swing low 9.0 (@0, confirmed 1), swing high 9.7 (@2), bearish BOS of 9.0 at
# candle 3 (low 8.8), swing low 8.8 confirmed 4, swing high 9.2 confirmed 5.
DOWN = [
    (10.0, 10.5, 9.0, 9.2),  # 0 red
    (9.2, 9.6, 9.1, 9.5),  # 1 green: swing low 9.0
    (9.5, 9.7, 9.3, 9.4),  # 2 red: swing high 9.7
    (9.4, 9.45, 8.8, 8.9),  # 3 red: bearish BOS of 9.0 -> downtrend
    (8.9, 9.2, 8.85, 9.1),  # 4 green: swing low 8.8
    (9.1, 9.15, 8.95, 9.0),  # 5 red: swing high 9.2
    (9.0, 9.3, 8.98, 9.1),  # 6 green: wick above 9.2, swing low 8.95
    (9.1, 9.12, 8.6, 8.65),  # 7 red: closes below 8.95, but that's with the trend
]


def test_a_wick_above_a_high_in_a_downtrend_without_a_bos_is_no_sweep():
    # candle 7 closes below the low after candle 6's wick above 9.2: in a downtrend that
    # is no BOS, so no sweep
    assert run(DOWN) == []


def test_sweep_of_lows_is_mirrored():
    ohlc = [*DOWN, (8.65, 9.4, 8.62, 9.35)]  # 8 green: closes above 9.3 -> bullish BOS
    (sweep,) = run(ohlc)
    # the bottom of the move is candle 7 (8.6); it took 9.0 (broken by the BOS), 8.95, 8.8
    assert summary([sweep]) == [(BULL, 7, 8.6, 8.8, 8)]
    assert [s.price for s in sweep.swept] == [9.0, 8.95, 8.8]


def random_walk(n=800, seed=11):
    rng = random.Random(seed)
    ohlc, price = [], 100.0
    for _ in range(n):
        o = price
        c = o + rng.choice([-1, 1]) * rng.choice([0.0, 0.03, 0.5, 1.2])
        ohlc.append((o, max(o, c) + rng.random(), min(o, c) - rng.random(), c))
        price = c
    return build_series(ohlc)


def test_no_lookahead_events_only_at_their_bos_candle_and_never_rewritten():
    series = random_walk()
    full = run(None, series=series)
    assert {e.direction for e in full} == {BULL, BEAR}

    detector, seen = SweepDetector(0.065), []
    for i in range(len(series)):
        new = detector.update(series.view(i))
        for e in new:
            # (a) emitted by its BOS candle; the sweeping candle and the swings it took
            # all lie before that, each swing confirmed before the sweeping candle
            assert e.confirmed_index == e.bos.confirmed_index == i
            assert e.index <= i
            assert all(s.confirmed_index < e.index for s in e.swept)
            assert e.direction is e.bos.direction
        seen.extend(new)
        # (b) a fresh run over a shorter history gives exactly the events emitted so far
        if i % 97 == 0:
            short = CandleSeries("TEST", Timeframe.M5, list(series.view(i)))
            assert run(None, series=short) == seen
    assert seen == full


def test_update_out_of_order_raises():
    series = build_series(UP)
    detector = SweepDetector(0.065)
    detector.update(series.view(0))
    with pytest.raises(ValueError):
        detector.update(series.view(0))


def test_for_symbol_needs_a_doji_threshold():
    SweepDetector.for_symbol("XAUUSD")
    with pytest.raises(KeyError):
        SweepDetector.for_symbol("EURUSD")
