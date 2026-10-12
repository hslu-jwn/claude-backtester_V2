"""Break of structure + trend. Spec: confluences.md › Break of structure (BOS), › Trend.

Candles are (open, high, low, close); M5 from Mon 2026-01-05 00:00 UTC, so candle i closes
at 00:05 + 5 min * i. Doji threshold 0.065 (gold).
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from itertools import pairwise

import pytest
from conftest import build_series

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.detectors.bos import BosDetector
from backtester.detectors.swings import RangeShare, SwingDetector
from backtester.detectors.trend import Trend, TrendDetector, trend_at

BULL, BEAR = Direction.BULLISH, Direction.BEARISH

# swing high 1.5 confirmed at candle 1, swing low 0.95 confirmed at candle 2
BASE = [(1.0, 1.5, 0.9, 1.4), (1.4, 1.45, 1.0, 1.1), (1.1, 1.3, 0.95, 1.2)]


def run(ohlc, series=None):
    series = series or build_series(ohlc)
    detector = BosDetector(SwingDetector(0.065))
    return [e for i in range(len(series)) for e in detector.update(series.view(i))]


def summary(events):
    """(direction, broken price, breaking candle) per BOS."""
    return [(e.direction, e.price, e.confirmed_index) for e in events]


def test_green_close_above_the_swing_high_is_a_bullish_bos():
    (event,) = run([*BASE, (1.2, 1.6, 1.15, 1.55)])
    assert summary([event]) == [(BULL, 1.5, 3)]
    assert event.swing.index == 0 and event.close == 1.55
    assert event.confirmed_at == datetime(2026, 1, 5, 0, 20, tzinfo=UTC)


def test_wick_above_without_a_close_is_no_bos():
    assert run([*BASE, (1.2, 1.6, 1.15, 1.45)]) == []


def test_close_exactly_at_the_level_is_no_bos():
    assert run([*BASE, (1.2, 1.6, 1.15, 1.5)]) == []


def test_red_candle_closing_above_the_high_is_no_bullish_bos():
    # gap up: a red candle opening and closing above 1.5 (it confirms a new high instead)
    events = run([*BASE, (1.7, 1.75, 1.52, 1.6)])
    assert events == []


def test_bearish_mirrored_red_close_below_the_swing_low():
    assert summary(run([*BASE, (1.2, 1.25, 0.9, 0.92)])) == [(BEAR, 0.95, 3)]


def test_green_candle_closing_below_the_low_is_no_bearish_bos():
    assert run([*BASE, (0.8, 0.9, 0.75, 0.85)]) == []


def test_a_level_is_broken_only_once():
    events = run([*BASE, (1.2, 1.6, 1.15, 1.55), (1.55, 1.7, 1.5, 1.65)])
    assert summary(events) == [(BULL, 1.5, 3)]


def test_older_unbroken_higher_high_gives_no_bos_after_the_latest_high_broke():
    ohlc = [
        (1.0, 2.0, 0.9, 1.9),  # 0 green
        (1.9, 1.95, 1.0, 1.1),  # 1 red: swing high H1 = 2.0
        (1.1, 1.3, 0.95, 1.2),  # 2 green: swing low 0.95
        (1.2, 1.25, 1.05, 1.1),  # 3 red: swing high H2 = 1.3 (newer, lower)
        (1.1, 1.5, 1.08, 1.45),  # 4 green: closes above H2 -> BOS
        (1.45, 2.2, 1.4, 2.1),  # 5 green: closes above H1, but H1 is not the latest high
    ]
    assert summary(run(ohlc)) == [(BULL, 1.3, 4)]


def test_one_close_through_several_highs_is_one_bos_against_the_latest():
    ohlc = [
        (1.0, 2.0, 0.9, 1.9),
        (1.9, 1.95, 1.0, 1.1),  # H1 = 2.0
        (1.1, 1.3, 0.95, 1.2),
        (1.2, 1.25, 1.05, 1.1),  # H2 = 1.3
        (1.1, 2.5, 1.08, 2.4),  # closes above both
    ]
    assert summary(run(ohlc)) == [(BULL, 1.3, 4)]


HIGHER_HIGH = [
    *BASE,
    (1.2, 1.6, 1.15, 1.55),  # 3: BOS of 1.5 -> uptrend
    (1.55, 1.58, 1.4, 1.45),  # 4 red: new swing high 1.6
    (1.45, 1.7, 1.44, 1.65),  # 5 green: closes above 1.6 (higher high), swing low 1.4
]


def test_a_break_with_the_trend_is_no_bos():
    # in an uptrend a close above the latest swing high (higher high) is no BOS
    assert summary(run(HIGHER_HIGH)) == [(BULL, 1.5, 3)]


def test_bos_directions_alternate_only_against_the_trend():
    ohlc = [
        *HIGHER_HIGH,
        (1.65, 1.66, 1.3, 1.35),  # 6 red: closes below the swing low 1.4 -> bearish BOS
    ]
    assert summary(run(ohlc)) == [(BULL, 1.5, 3), (BEAR, 1.4, 6)]


def test_a_level_closed_through_with_the_trend_is_used_up():
    ohlc = [
        (1.0, 1.5, 0.9, 1.4),  # 0 green
        (1.4, 1.45, 1.0, 1.1),  # 1 red: swing high 1.5
        (1.1, 1.3, 0.95, 1.2),  # 2 green: swing low 0.95
        (1.2, 1.25, 0.9, 0.92),  # 3 red: bearish BOS of 0.95 -> downtrend; swing high 1.3
        (0.92, 1.0, 0.88, 0.99),  # 4 green: swing low 0.88
        (0.99, 1.0, 0.85, 0.86),  # 5 red: lower low through 0.88 -> no BOS; swing high 1.0
        (0.86, 1.1, 0.84, 1.05),  # 6 green: bullish BOS of 1.0 -> uptrend; swing low 0.84
    ]
    assert summary(run(ohlc)) == [(BEAR, 0.95, 3), (BULL, 1.0, 6)]


def test_red_candle_confirming_a_high_breaks_the_low_confirmed_before_it():
    # candle 3 confirms the swing high 1.35 (usable only from candle 4 on) and closes below
    # the low 0.95 confirmed at candle 2
    (event,) = run([*BASE, (1.2, 1.35, 0.9, 0.92)])
    assert summary([event]) == [(BEAR, 0.95, 3)]


def test_green_candle_confirming_a_low_can_break_the_earlier_high():
    ohlc = [(1.0, 1.5, 0.9, 1.4), (1.4, 1.45, 1.0, 1.1), (1.1, 1.6, 1.05, 1.55)]
    assert summary(run(ohlc)) == [(BULL, 1.5, 2)]


def test_a_doji_never_causes_a_bos():
    # body 0.02 <= 0.065: neither green nor red, even though it closes above 1.5 / below 0.95
    assert run([*BASE, (1.49, 1.55, 1.45, 1.51)]) == []
    assert run([*BASE, (0.96, 1.0, 0.9, 0.94)]) == []
    # body exactly at the threshold is still a doji; just above it breaks
    assert run([*BASE, (1.45, 1.55, 1.44, 1.515)]) == []
    assert summary(run([*BASE, (1.45, 1.55, 1.44, 1.5151)])) == [(BULL, 1.5, 3)]


def test_range_share_doji_never_causes_a_bos_even_when_the_body_is_large_in_price():
    # closes above 1.5 with a body of 0.2 in a candle of range 5 (4%): a doji by share
    wide = (1.4, 4.0, -1.0, 1.6)
    assert summary(run([*BASE, wide])) == [(BULL, 1.5, 3)]  # fixed amount 0.065: breaks
    detector = BosDetector(SwingDetector(RangeShare(0.10)))
    series = build_series([*BASE, wide])
    assert [e for i in range(4) for e in detector.update(series.view(i))] == []


def test_level_survives_a_doji_and_breaks_on_the_next_real_close():
    ohlc = [*BASE, (1.49, 1.55, 1.45, 1.51), (1.51, 1.6, 1.5, 1.58)]
    assert summary(run(ohlc)) == [(BULL, 1.5, 4)]


def test_break_on_the_first_candle_after_a_weekend():
    friday = datetime(2026, 1, 9, 21, 45, tzinfo=UTC)
    candles = [
        Candle(friday, 1.0, 1.5, 0.9, 1.4),
        Candle(friday + timedelta(minutes=5), 1.4, 1.45, 1.0, 1.1),  # high 1.5
        Candle(friday + timedelta(days=2, hours=1, minutes=10), 1.55, 1.7, 1.5, 1.65),
    ]
    (event,) = run(None, series=CandleSeries("TEST", Timeframe.M5, candles))
    assert (event.direction, event.price, event.confirmed_index) == (BULL, 1.5, 2)
    assert event.confirmed_at == candles[2].ts + timedelta(minutes=5)


def random_walk(n=600, seed=11):
    rng = random.Random(seed)
    ohlc, price = [], 100.0
    for _ in range(n):
        o = price
        c = o + rng.choice([-1, 1]) * rng.choice([0.0, 0.03, 0.5, 1.2])
        ohlc.append((o, max(o, c) + rng.random(), min(o, c) - rng.random(), c))
        price = c
    return build_series(ohlc)


def test_no_lookahead_events_only_at_their_candle_and_never_rewritten():
    series = random_walk()
    full = run(None, series=series)
    assert {e.direction for e in full} == {BULL, BEAR}
    assert all(a.direction is not b.direction for a, b in pairwise(full))

    detector, seen = BosDetector(SwingDetector(0.065)), []
    for i in range(len(series)):
        new = detector.update(series.view(i))
        # (a) emitted by its breaking candle, against a swing confirmed before it
        assert all(e.confirmed_index == i and e.swing.confirmed_index < i for e in new)
        seen.extend(new)
        # (b) a fresh run over a shorter history gives exactly the events emitted so far
        if i % 97 == 0:
            short = CandleSeries("TEST", Timeframe.M5, list(series.view(i)))
            assert run(None, series=short) == seen
    assert seen == full


def test_update_out_of_order_or_twice_raises():
    series = build_series(BASE)
    detector = BosDetector(SwingDetector(0.065))
    detector.update(series.view(0))
    with pytest.raises(ValueError):
        detector.update(series.view(0))


def test_for_symbol_needs_a_doji_threshold():
    BosDetector.for_symbol("XAUUSD")
    with pytest.raises(KeyError):
        BosDetector.for_symbol("EURUSD")


# --- trend ---------------------------------------------------------------------------

TREND_OHLC = [
    *BASE,  # high 1.5 @1, low 0.95 @2
    (1.2, 1.25, 0.9, 0.92),  # 3: bearish BOS of 0.95 -> downtrend (also confirms high 1.3)
    (0.92, 1.0, 0.88, 0.99),  # 4 green: swing low 0.88
    (0.98, 1.0, 0.85, 0.86),  # 5 red: lower low through 0.88: no BOS; swing high 1.0
    (0.86, 1.1, 0.84, 1.05),  # 6 green: bullish BOS of 1.0 -> flips to uptrend
]


def trend_run(series):
    detector = TrendDetector(BosDetector(SwingDetector(0.065)))
    out = []
    for i in range(len(series)):
        out.append((detector.update(series.view(i)), detector.trend))
    return out


def test_trend_none_before_the_first_bos_then_set_confirmed_and_flipped():
    steps = trend_run(build_series(TREND_OHLC))
    assert [trend for _, trend in steps] == [
        Trend.NONE,
        Trend.NONE,
        Trend.NONE,
        Trend.DOWN,
        Trend.DOWN,
        Trend.DOWN,
        Trend.UP,
    ]
    changes = [c for new, _ in steps for c in new]
    assert [(c.previous, c.trend, c.confirmed_index) for c in changes] == [
        (Trend.NONE, Trend.DOWN, 3),
        (Trend.DOWN, Trend.UP, 6),
    ]
    assert changes[1].bos.price == 1.0


def test_trend_at_matches_the_incremental_detector():
    series = random_walk(seed=3)
    bos = run(None, series=series)
    for i, (_, trend) in enumerate(trend_run(series)):
        change = trend_at(bos, i)
        assert (change.trend if change else Trend.NONE) is trend


def test_trend_detector_no_lookahead():
    series = random_walk(seed=5)
    full = [c for new, _ in trend_run(series) for c in new]
    assert full
    for cut in (50, 200, 401):
        short = CandleSeries("TEST", Timeframe.M5, list(series.view(cut)))
        assert [c for new, _ in trend_run(short) for c in new] == [
            c for c in full if c.confirmed_index <= cut
        ]
