"""Rolling channel, SMA and KAMA of strategy 4, incremental and lookahead-free.
Spec: docs/strategy-trend-following.md › Trend signal."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backtester.core.models import Candle, Direction
from backtester.strategy.trend_following.indicators import (
    DunniganSwings,
    Kama,
    Momentum,
    RollingChannel,
    Sma,
)

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


# --- momentum and Dunnigan swings (ROADMAP 10.4) -------------------------------------------


def test_momentum_is_the_sign_of_close_minus_close_n_ago_and_repeats():
    m = Momentum(2)
    out = [m.update(c) for c in [10, 10, 11, 12, 9, 9, 8]]
    # idx2: 11-10=+1, idx3: 12-10=+2 (repeat), idx4: 9-11=-2, idx5: 9-12=-3, idx6: 8-9=-1
    assert out == [None, None, LONG, LONG, SHORT, SHORT, SHORT]


def test_momentum_exactly_zero_gives_no_event():
    m = Momentum(2)
    assert [m.update(c) for c in [10, 11, 10, 11]] == [None, None, None, None]


def test_momentum_needs_n_plus_one_closes_and_rejects_period_below_1():
    m = Momentum(3)
    assert [m.update(c) for c in [1, 2, 3]] == [None, None, None]
    assert m.update(4) is LONG
    with pytest.raises(ValueError):
        Momentum(0)


def feed(swings, rows):
    """rows of (high, low[, close]); returns the event of every candle."""
    return [swings.update(candle(i, *r)) for i, r in enumerate(rows)]


UP_THEN_DOWN = [(10, 9), (11, 10), (12, 11), (11.5, 10.5)]


def test_dunnigan_downswing_starts_when_high_and_low_are_below_the_highest_candle():
    s = DunniganSwings()
    feed(s, UP_THEN_DOWN[:3])
    assert s.upswing is True and s.swing_top is None  # the first upswing has no top yet
    s.update(candle(3, 11.5, 10.5))
    assert s.upswing is False and s.swing_top == 12  # the highest candle (12, 11) is the top


def test_dunnigan_inside_candle_changes_nothing():
    s = DunniganSwings()
    feed(s, [*UP_THEN_DOWN, (11.4, 10.6)])  # inside (11.5, 10.5)
    assert s.upswing is False and s.swing_top == 12
    s.update(candle(5, 11.3, 10.7))  # inside again
    assert s.upswing is False


def test_dunnigan_outside_candle_keeps_the_swing_and_only_raises_the_top():
    s = DunniganSwings()
    feed(s, [(10, 9), (11, 10), (12, 11), (12.5, 10.5)])  # outside (12, 11)
    assert s.upswing is True
    s.update(candle(4, 12.2, 10.8))  # low above the outside candle's 10.5: no turn
    assert s.upswing is True and s.swing_top is None
    s.update(candle(5, 12.2, 10.2))  # both below (12.5, 10.5) -> downswing, top 12.5
    assert s.upswing is False and s.swing_top == 12.5


def test_dunnigan_upswing_records_the_swing_bottom_and_a_later_top_replaces_the_old():
    s = DunniganSwings()
    feed(s, [*UP_THEN_DOWN, (11.0, 10.0)])  # lowest candle of the downswing (11, 10)
    assert s.swing_bottom is None
    s.update(candle(5, 11.2, 10.2))  # both above (11, 10): upswing, bottom 10
    assert s.upswing is True and s.swing_bottom == 10
    feed(s, [(13, 12), (12.5, 11.5)])  # new high 13, then a turn: top 13 replaces 12
    assert s.swing_top == 13


def test_dunnigan_no_state_before_the_first_decisive_candle():
    s = DunniganSwings()
    feed(s, [(10, 9), (9.5, 9.5)])  # second candle inside the first: still undecided
    assert s.upswing is None


LONG_ROWS = [*UP_THEN_DOWN, (11.0, 10.0), (11.2, 10.2), (12.4, 10.5, 12.3)]


def test_dunnigan_long_needs_two_hh_hl_candles_and_a_close_above_the_swing_top():
    events = feed(DunniganSwings(), LONG_ROWS)
    assert events[:6] == [None] * 6 and events[6] is LONG


def test_dunnigan_repeats_while_the_conditions_hold():
    events = feed(DunniganSwings(), [*LONG_ROWS, (13, 11, 12.9)])
    assert events[6] is LONG and events[7] is LONG


@pytest.mark.parametrize(
    "rows",
    [
        [*UP_THEN_DOWN, (11.0, 10.0), (11.2, 10.2), (12.4, 10.5, 11.9)],  # close not above 12
        [*UP_THEN_DOWN, (11.0, 10.0), (11.2, 10.2), (12.4, 10.1, 12.3)],  # last low is lower
        [*UP_THEN_DOWN, (11.0, 10.0), (10.9, 10.2), (12.4, 10.5, 12.3)],  # prior high is lower
        [(10, 9), (11, 10), (12, 11), (13, 12, 13)],  # HH+HL twice but no swing top exists
    ],
    ids=["close-below-top", "no-higher-low", "no-higher-high", "no-swing-top"],
)
def test_dunnigan_each_missing_part_gives_no_event(rows):
    assert feed(DunniganSwings(), rows)[-1] is None


def test_dunnigan_short_is_the_mirror_of_the_long():
    rows = [(20 - r[1], 20 - r[0], *[20 - x for x in r[2:]]) for r in LONG_ROWS]
    events = feed(DunniganSwings(), rows)
    assert events[:6] == [None] * 6 and events[6] is SHORT
