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
from backtester.detectors.sweep import SweepConfig, SweepDetector

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


def run(ohlc, series=None, config=None):
    series = series or build_series(ohlc)
    detector = SweepDetector(0.065, config)
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


# Falling highs, then one candle takes all of them. Highs 12.0 (@0, confirmed 1), 11.5
# (@2, confirmed 3), 11.3 (@4, confirmed 5), 11.1 (@6, confirmed 7); lows 11.0 (@1,
# confirmed 2), 10.6 (@4), 10.4 (@6), 10.45 (@7, confirmed 8).
FALLING = [
    (10.0, 12.0, 9.9, 11.8),  # 0 green
    (11.8, 11.9, 11.0, 11.1),  # 1 red: swing high 12.0
    (11.1, 11.5, 11.0, 11.4),  # 2 green: swing low 11.0 (equal wicks: the earlier candle)
    (11.4, 11.45, 10.7, 10.8),  # 3 red: swing high 11.5; bearish BOS of 11.0 -> downtrend
    (10.8, 11.3, 10.6, 11.2),  # 4 green: swing low 10.6
    (11.2, 11.25, 10.5, 10.55),  # 5 red: swing high 11.3 (close below 10.6: with the trend)
    (10.55, 11.1, 10.4, 11.0),  # 6 green: swing low 10.4 (the bottom of the move down)
    (11.0, 11.05, 10.45, 10.5),  # 7 red: swing high 11.1
    (10.5, 12.5, 10.45, 12.3),  # 8 green: wick 12.5 takes all four highs; bullish BOS of 11.1
    (12.3, 12.35, 11.8, 11.9),  # 9 red: swing high 12.5
    (11.9, 11.95, 10.3, 10.35),  # 10 red: closes below the low 10.45 -> bearish BOS
]


def test_only_the_last_n_swings_count_and_the_level_is_the_furthest_of_them():
    # candle 8 takes 12.0, 11.5, 11.3 and 11.1; with N = 3 only the last three count,
    # so the swept level is 11.5 (#3), not 12.0 (spec: more than N taken -> level #N)
    sweeps = run(FALLING)
    assert summary(sweeps) == [(BULL, 6, 10.4, 10.6, 8), (BEAR, 8, 12.5, 11.5, 10)]
    assert [s.price for s in sweeps[1].swept] == [11.1, 11.3, 11.5]
    # the low side: candle 6 took the lows 11.0 and 10.6 (10.4 is its own, not earlier)
    assert [s.price for s in sweeps[0].swept] == [11.0, 10.6]
    # N = 4: the old high 12.0 counts too
    (_, bear) = run(FALLING, config=SweepConfig(lookback_swings=4))
    assert bear.swing.price == 12.0


def test_with_n_1_only_the_last_swing_counts():
    # candle 6 takes only the last low before it (10.6), candle 8 the last high (11.1)
    sweeps = run(FALLING, config=SweepConfig(lookback_swings=1))
    assert summary(sweeps) == [(BULL, 6, 10.4, 10.6, 8), (BEAR, 8, 12.5, 11.1, 10)]
    assert [len(s.swept) for s in sweeps] == [1, 1]


def test_a_wick_beyond_only_an_older_swing_is_no_candidate():
    ohlc = [
        *UP[:3],
        (10.5, 11.2, 10.4, 11.1),  # 3 green: wick 11.2 takes 11.0, bullish BOS of 11.0
        (11.1, 11.15, 10.9, 11.0),  # 4 red: swing high 11.2
        (11.0, 11.12, 10.95, 11.1),  # 5 green: swing low 10.9
        (11.1, 11.11, 10.7, 10.75),  # 6 red: wick above 11.0 only; bearish BOS of 10.9
    ]
    # candle 3 (top 11.2) is the candidate; candles 5 and 6 are no new top
    assert summary(run(ohlc)) == [(BEAR, 3, 11.2, 11.0, 6)]
    # X = 2: candle 3 expires at candle 6; candle 6's wick 11.11 then takes 11.0, which
    # is among the last 2 highs (11.0, 11.2): a sweep by the BOS candle itself
    assert summary(run(ohlc, config=SweepConfig(lookback_swings=2, bos_within=2))) == [
        (BEAR, 6, 11.11, 11.0, 6)
    ]
    # N = 1: the last high is 11.2, so a wick above the older 11.0 is no candidate
    assert run(ohlc, config=SweepConfig(lookback_swings=1, bos_within=2)) == []


def test_the_bos_must_come_within_x_candles_of_the_top():
    ohlc = [
        *UP,
        (11.7, 11.75, 11.2, 11.3),  # 7 red: swing high 11.8
        (11.3, 11.35, 10.8, 10.85),  # 8 red: bearish BOS, 2 candles after the top (6)
    ]
    # X = 1: candle 6's top expires; the BOS candle's own wick 11.35 is above 11.0 (still
    # among the last 3 highs), so it is a sweep by the BOS candle itself
    assert summary(run(ohlc, config=SweepConfig(bos_within=1))) == [(BEAR, 8, 11.35, 11.0, 8)]
    assert summary(run(ohlc, config=SweepConfig(lookback_swings=2, bos_within=1))) == []
    assert summary(run(ohlc, config=SweepConfig(bos_within=2))) == [(BEAR, 6, 11.8, 11.5, 8)]


def test_a_new_extreme_restarts_the_count():
    ohlc = [
        *UP,
        (11.7, 11.75, 11.4, 11.5),  # 7 red: swing high 11.8
        (11.5, 12.0, 11.45, 11.9),  # 8 green: new top 12.0
        (11.9, 11.95, 11.3, 11.35),  # 9 red: bearish BOS, 3 candles after 6, 1 after 8
    ]
    assert summary(run(ohlc, config=SweepConfig(bos_within=1))) == [(BEAR, 8, 12.0, 11.8, 9)]


def test_an_expired_top_lets_a_lower_wick_start_a_new_candidate():
    ohlc = [
        *UP,
        (11.7, 11.75, 11.2, 11.3),  # 7 red: swing high 11.8 (top: candle 6)
        (11.3, 11.6, 11.25, 11.55),  # 8 green: swing low 11.2
        (11.55, 11.58, 11.25, 11.3),  # 9 red: swing high 11.6
        (11.3, 11.65, 11.28, 11.5),  # 10 green: wick 11.65 takes 11.6 (below the top 11.8)
        (11.5, 11.52, 11.0, 11.05),  # 11 red: bearish BOS of 11.25 (swing low @9-10)
    ]
    # bos_within = 3: candle 6's top expires after candle 9, so candle 10 is the new top
    assert summary(run(ohlc, config=SweepConfig(bos_within=3))) == [(BEAR, 10, 11.65, 11.6, 11)]
    # default 10: candle 6 is still the top, candle 10 is no new extreme
    assert summary(run(ohlc)) == [(BEAR, 6, 11.8, 11.5, 11)]


def test_close_beyond_off_a_close_above_a_high_does_not_sweep_it():
    # candle 3 (close 11.3) and candle 6 (close 11.7) close above the highs they wick
    # above; candle 7 wicks above 11.5 and closes below it (but above 11.0)
    ohlc = [
        *UP,
        (11.7, 11.75, 11.2, 11.3),  # 7 red: wick 11.75 > 11.5, close 11.3 < 11.5
        (11.3, 11.35, 10.8, 10.85),  # 8 red: bearish BOS of 10.9
    ]
    off = SweepConfig(close_beyond_counts=False)
    (sweep,) = run(ohlc, config=off)
    assert summary([sweep]) == [(BEAR, 7, 11.75, 11.5, 8)]
    assert [s.price for s in sweep.swept] == [11.5]  # 11.0: closed above, not swept
    # default (on): candle 6 is the top, as before
    assert summary(run(ohlc)) == [(BEAR, 6, 11.8, 11.5, 8)]


def test_close_beyond_off_a_higher_candle_that_sweeps_nothing_ends_the_candidate():
    ohlc = [
        *UP,
        (11.7, 11.75, 11.2, 11.3),  # 7 red: the candidate (off), swing high 11.8
        (11.3, 12.0, 11.25, 11.9),  # 8 green: above 11.75, but closes above every high
        (11.6, 11.65, 11.1, 11.15),  # 9 red: wick takes 11.5 only; bearish BOS of 11.2
    ]
    # price went above candle 7's top, so candle 7 is no sweep; candle 9 is its own
    off = SweepConfig(close_beyond_counts=False)
    assert summary(run(ohlc, config=off)) == [(BEAR, 9, 11.65, 11.5, 9)]


# --- equal-high tolerance and "two closes beyond" (user, 2026-10-12; spec › Liquidity sweep) ---
# After UP[:6] the last highs are 11.0 and 11.5 (0.5 apart). ATR period 1 makes the ATR
# known before candle 6 the true range of candle 5: 0.35.
EQUAL = [
    *UP[:6],
    (11.1, 11.3, 11.05, 11.25),  # 6 green: wick 11.3 takes 11.0 but not 11.5
    (11.25, 11.28, 10.7, 10.75),  # 7 red: closes below the low 10.9 -> bearish BOS
]


def mirror(ohlc, k=40.0):
    """The same candles upside down (highs <-> lows); prices become k - price."""
    return [(k - o, k - lo, k - hi, k - c) for o, hi, lo, c in ohlc]


# bos_within = 2: the top at candle 3 (it took 11.0) has expired when candle 6 comes
def tolerance(atr_multiple, **kw):
    return SweepConfig(equal_tolerance_atr=atr_multiple, atr_period=1, bos_within=2, **kw)


def test_default_is_any_of_the_last_n_so_the_lower_high_is_swept():
    assert summary(run(EQUAL, config=SweepConfig(bos_within=2))) == [(BEAR, 6, 11.3, 11.0, 7)]


def test_tolerance_zero_needs_the_most_extreme_of_the_last_n():
    assert run(EQUAL, config=tolerance(0.0)) == []


def test_a_high_within_the_tolerance_of_the_highest_counts_as_the_level():
    # 11.5 - 11.0 = 0.5 <= 2 x 0.35
    assert summary(run(EQUAL, config=tolerance(2.0))) == [(BEAR, 6, 11.3, 11.0, 7)]


def test_a_high_beyond_the_tolerance_does_not_count():
    # 0.5 > 1 x 0.35: 11.0 is a lower high, 11.5 is still ahead
    assert run(EQUAL, config=tolerance(1.0)) == []


def test_infinite_tolerance_is_any_of_the_last_n():
    any_of_n = run(EQUAL, config=SweepConfig(bos_within=2))
    assert any_of_n and run(EQUAL, config=tolerance(float("inf"))) == any_of_n


def test_tolerance_is_zero_while_the_atr_is_not_known_yet():
    config = SweepConfig(equal_tolerance_atr=100.0, bos_within=2)  # ATR(14) needs 14 candles
    assert run(EQUAL, config=config) == []


def test_a_wick_beyond_the_most_extreme_is_a_sweep_with_any_tolerance():
    assert summary(
        run(UP[:6] + [(11.2, 11.8, 11.1, 11.7), (11.7, 11.75, 10.7, 10.8)], config=tolerance(0.0))
    ) == [(BEAR, 6, 11.8, 11.5, 7)]


def test_tolerance_works_mirrored_for_lows():
    (sweep,) = run(mirror(EQUAL), config=tolerance(2.0))
    assert summary([sweep]) == [(BULL, 6, 40.0 - 11.3, 40.0 - 11.0, 7)]
    assert run(mirror(EQUAL), config=tolerance(1.0)) == []


# Candle 6 closes 11.7 beyond 11.5 and 11.0; what follows decides.
TWO = SweepConfig(two_closes_cancel=True)


def test_two_closes_beyond_the_level_are_no_sweep_but_a_breakout():
    ohlc = [
        *UP,
        (11.7, 11.9, 11.6, 11.85),  # 7 green: second close beyond 11.5
        (11.85, 11.9, 10.8, 10.85),  # 8 red: bearish BOS
    ]
    assert summary(run(ohlc)) == [(BEAR, 7, 11.9, 11.5, 8)]  # without the rule
    assert run(ohlc, config=TWO) == []


def test_a_doji_does_not_count_as_a_close_and_does_not_break_the_streak():
    ohlc = [
        *UP,
        (11.7, 11.95, 11.65, 11.72),  # 7 doji (body 0.02) closing beyond: ignored
        (11.72, 11.9, 10.8, 10.85),  # 8 red: bearish BOS
    ]
    assert summary(run(ohlc, config=TWO)) == [(BEAR, 7, 11.95, 11.5, 8)]
    ohlc[-1:-1] = [(11.72, 11.9, 11.7, 11.85)]  # a real candle closing beyond follows
    ohlc[-1] = (11.85, 11.9, 10.8, 10.85)
    assert run(ohlc, config=TWO) == []


def test_a_close_back_below_the_level_keeps_it_a_sweep():
    ohlc = [
        *UP,
        (11.7, 11.9, 11.2, 11.3),  # 7 red: top 11.9, closes below 11.5
        (11.3, 11.35, 10.8, 10.85),  # 8 red: bearish BOS
    ]
    assert summary(run(ohlc, config=TWO)) == [(BEAR, 7, 11.9, 11.5, 8)]


def test_a_wick_above_with_a_close_below_then_one_close_beyond_is_still_a_sweep():
    ohlc = [
        *UP[:6],
        (11.2, 11.8, 11.1, 11.45),  # 6 green: wick above 11.5, closes below it
        (11.45, 11.6, 11.4, 11.55),  # 7 green: one close beyond 11.5 (no new top)
        (11.55, 11.58, 10.8, 10.85),  # 8 red: bearish BOS
    ]
    assert summary(run(ohlc, config=TWO)) == [(BEAR, 6, 11.8, 11.5, 8)]


def test_two_closes_work_mirrored_for_lows():
    ohlc = [
        *UP,
        (11.7, 11.9, 11.6, 11.85),
        (11.85, 11.9, 10.8, 10.85),
    ]
    assert run(mirror(ohlc), config=TWO) == []
    assert run(mirror(ohlc))[0].direction is BULL


def test_the_breakout_no_longer_counts_its_levels_as_sweepable():
    # after the breakout (candles 6, 7) the highs 11.0 / 11.5 are accepted; a later wick
    # above 11.5 must not make a sweep of them when a BOS follows
    ohlc = [
        *UP,
        (11.7, 11.9, 11.6, 11.85),  # 7 second close beyond: breakout
        (11.85, 11.88, 11.6, 11.7),  # 8 red, swing high 11.9 confirmed
        (11.7, 11.89, 11.65, 11.75),  # 9 wick 11.89 above 11.5, below 11.9
        (11.75, 11.8, 10.7, 10.75),  # 10 red: bearish BOS of 10.9
    ]
    assert run(ohlc, config=TWO) == []


def test_config_rejects_values_below_one_and_negative():
    with pytest.raises(ValueError):
        SweepConfig(lookback_swings=0)
    with pytest.raises(ValueError):
        SweepConfig(bos_within=-1)
    with pytest.raises(ValueError):
        SweepConfig(equal_tolerance_atr=-0.1)
    with pytest.raises(ValueError):
        SweepConfig(atr_period=0)


def random_walk(n=800, seed=11):
    rng = random.Random(seed)
    ohlc, price = [], 100.0
    for _ in range(n):
        o = price
        c = o + rng.choice([-1, 1]) * rng.choice([0.0, 0.03, 0.5, 1.2])
        ohlc.append((o, max(o, c) + rng.random(), min(o, c) - rng.random(), c))
        price = c
    return build_series(ohlc)


@pytest.mark.parametrize(
    "config",
    [
        SweepConfig(),
        SweepConfig(lookback_swings=1, bos_within=2, close_beyond_counts=False),
        SweepConfig(equal_tolerance_atr=0.5, two_closes_cancel=True),
        SweepConfig(equal_tolerance_atr=0.0, atr_period=3, two_closes_cancel=True),
    ],
)
def test_no_lookahead_events_only_at_their_bos_candle_and_never_rewritten(config):
    series = random_walk()
    full = run(None, series=series, config=config)
    assert {e.direction for e in full} == {BULL, BEAR}

    detector, seen = SweepDetector(0.065, config), []
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
            assert run(None, series=short, config=config) == seen
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
