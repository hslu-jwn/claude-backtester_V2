"""Order block. Spec: confluences.md › Order block, › Strong-move filter, › Validation.

Candles are (open, high, low, close); M5 from Mon 2026-01-05 00:00 UTC. Doji threshold
0.005. ATR(2), k = 2. Bearish cases mirror the candles around 1.0 (price -> 2.0 - price).

Base: a swing high 1.10 (confirmed by candle 1), the red leg 1-3 into the swing low 0.90
(wick on candle 3, confirmed by the green candle 4), then candle 5 closes above 1.10:
the first BOS, bullish. The OB is the red leg: candles 1-3, 0.90 to 1.09.
"""

from __future__ import annotations

import random

import pytest
from conftest import build_series

from backtester.core.models import Direction
from backtester.core.series import CandleSeries
from backtester.detectors.atr import StrongMoveConfig
from backtester.detectors.order_block import OrderBlock, OrderBlockConfig, OrderBlockDetector
from backtester.detectors.zone import ZoneKind, ZoneState, ZoneTransition

BULL, BEAR = Direction.BULLISH, Direction.BEARISH
DOJI = 0.005
ATR2 = StrongMoveConfig(atr_period=2)
FILTER_ON = OrderBlockConfig(strong_move=ATR2)
FILTER_OFF = OrderBlockConfig(strong_move_filter=False, strong_move=ATR2)

LEG = [
    (1.00, 1.10, 0.99, 1.08),  # 0 green
    (1.08, 1.09, 1.00, 1.02),  # 1 red: confirms swing high 1.10; first candle of the leg
    (1.02, 1.03, 0.95, 0.97),  # 2 red
    (0.97, 0.98, 0.90, 0.92),  # 3 red: lowest wick 0.90
    (0.92, 1.00, 0.91, 0.99),  # 4 green: confirms swing low 0.90
]
WEAK_BOS = (0.99, 1.15, 0.98, 1.14)  # 5: closes above 1.10, range 0.17 < 2 x ATR (0.175)
STRONG = (1.14, 1.40, 1.13, 1.38)  # 6: range 0.27 >= 2 x ATR (0.2575)
PULLBACK_STRONG = (1.14, 1.20, 0.92, 0.93)  # 6: red, confirms swing high 1.20, range 0.28;
# closes above the low 0.90, so no bearish BOS


def mirror(ohlc):
    return [(2.0 - o, 2.0 - lo, 2.0 - h, 2.0 - c) for o, h, lo, c in ohlc]


def run(ohlc, config=FILTER_OFF, series=None):
    series = series or build_series(ohlc)
    detector = OrderBlockDetector(DOJI, config)
    return [e for i in range(len(series)) for e in detector.update(series.view(i))]


def obs(events):
    return [e for e in events if isinstance(e, OrderBlock)]


def summary(ob):
    z = ob.zone
    return (z.direction, z.start_index, round(z.bottom, 6), round(z.top, 6), ob.confirmed_index)


def test_red_leg_into_the_low_before_a_bullish_bos_is_a_bullish_ob():
    (ob,) = obs(run([*LEG, WEAK_BOS]))
    assert summary(ob) == (BULL, 1, 0.90, 1.09, 5)
    assert ob.zone.kind is ZoneKind.ORDER_BLOCK and ob.zone.created_index == 5
    assert ob.swing.price == 0.90 and ob.swing.confirmed_index == 4
    assert ob.bos.confirmed_index == 5 and ob.bos.price == 1.10
    assert ob.strong_index is None  # filter off: exists at the BOS candle anyway


def test_bearish_mirrored():
    (ob,) = obs(run(mirror([*LEG, WEAK_BOS])))
    assert summary(ob) == (BEAR, 1, 0.91, 1.10, 5)


def test_no_bos_no_ob():
    assert obs(run(LEG)) == []


def test_lower_wick_on_the_green_turn_candle_is_not_in_the_ob():
    green_lower = (0.92, 1.00, 0.85, 0.99)  # swing low 0.85 on the green candle
    (ob,) = obs(run([*LEG[:4], green_lower, WEAK_BOS]))
    assert ob.swing.price == 0.85
    assert (ob.zone.bottom, ob.zone.top) == (0.90, 1.09)  # red candles only


def test_doji_inside_the_leg_is_skipped_with_its_wick():
    doji = (0.97, 0.99, 0.80, 0.972)  # body 0.002, wick to 0.80
    (ob,) = obs(run([*LEG[:3], doji, *LEG[3:], WEAK_BOS]))
    assert (ob.zone.start_index, ob.zone.bottom, ob.zone.top) == (1, 0.90, 1.09)


def test_the_leg_ends_at_the_first_opposite_color_candle():
    # green candle 0 ends the leg: its high 1.10 is not in the OB (top 1.09)
    (ob,) = obs(run([*LEG, WEAK_BOS]))
    assert ob.zone.start_index == 1 and ob.zone.top == 1.09


def test_low_confirmed_by_the_bos_candle_itself_is_the_ob_low():
    one_green = (0.92, 1.15, 0.91, 1.14)  # confirms the low 0.90 and closes above 1.10
    (ob,) = obs(run([*LEG[:4], one_green]))
    assert summary(ob) == (BULL, 1, 0.90, 1.09, 4)
    assert ob.swing.confirmed_index == ob.bos.confirmed_index == 4


def test_filter_on_ob_waits_for_the_first_strong_candle_of_the_move_away():
    events = run([*LEG, WEAK_BOS], FILTER_ON)
    assert obs(events) == []
    (ob,) = obs(run([*LEG, WEAK_BOS, STRONG], FILTER_ON))
    assert summary(ob) == (BULL, 1, 0.90, 1.09, 6)
    assert ob.strong_index == 6 and ob.strong_threshold == pytest.approx(0.2575)
    assert ob.strong_at == ob.confirmed_at


def test_filter_on_strong_candle_before_the_bos_counts_from_the_green_turn_candle():
    strong_turn = (0.92, 1.08, 0.91, 1.07)  # range 0.17 >= 2 x 0.085
    (ob,) = obs(run([*LEG[:4], strong_turn, (1.07, 1.15, 1.06, 1.14)], FILTER_ON))
    assert ob.confirmed_index == 5 and ob.strong_index == 4


def test_filter_on_next_swing_first_means_no_ob_and_its_candle_does_not_count():
    # candle 6 is strong but red: it confirms the next swing high, so the move away ended
    events = run([*LEG, WEAK_BOS, PULLBACK_STRONG, STRONG], FILTER_ON)
    assert obs(events) == []


def test_filter_off_the_same_moves_give_the_ob_at_the_bos():
    (ob,) = obs(run([*LEG, WEAK_BOS, PULLBACK_STRONG]))
    assert ob.confirmed_index == 5


def test_validation_starts_after_the_ob_exists():
    tap = (1.14, 1.15, 1.05, 1.06)  # 6 red: wick into the OB (low 1.05 < top 1.09)
    confirm = (1.06, 1.12, 1.05, 1.11)  # 7 green: close above 1.09
    events = run([*LEG, WEAK_BOS, tap, confirm])
    states = [(e.confirmed_index, e.state) for e in events if isinstance(e, ZoneTransition)]
    assert states == [(6, ZoneState.TAPPED), (7, ZoneState.CONFIRMED)]


def random_walk(n=1500, seed=3):
    rng = random.Random(seed)
    ohlc, price = [], 100.0
    for _ in range(n):
        o = price
        c = o + rng.choice([-1, 1]) * rng.choice([0.0, 0.002, 0.3, 1.0, 3.0])
        ohlc.append((o, max(o, c) + rng.random() / 2, min(o, c) - rng.random() / 2, c))
        price = c
    return build_series(ohlc)


@pytest.mark.parametrize("config", [OrderBlockConfig(), OrderBlockConfig(strong_move_filter=False)])
def test_no_lookahead_events_only_at_their_candle_and_never_rewritten(config):
    series = random_walk()
    full = run(None, config, series)
    assert {o.direction for o in obs(full)} == {BULL, BEAR}

    detector, seen = OrderBlockDetector(DOJI, config), []
    for i in range(len(series)):
        new = detector.update(series.view(i))
        assert all(e.confirmed_index == i for e in new)
        for e in new:
            if isinstance(e, OrderBlock):
                # built only from candles up to the swing, after its BOS
                assert e.zone.start_index <= e.swing.first_index <= e.swing.confirmed_index
                assert e.swing.confirmed_index <= e.bos.confirmed_index <= i
            else:
                assert e.zone.created_index < i
        seen.extend(new)
        if i % 211 == 0:
            short = CandleSeries("TEST", series.timeframe, list(series.view(i)))
            assert run(None, config, short) == seen
    assert seen == full


def test_filter_on_keeps_a_subset_existing_at_or_after_the_bos():
    series = random_walk()
    on = obs(run(None, OrderBlockConfig(), series))
    off = {
        o.zone.start_index: o
        for o in obs(run(None, OrderBlockConfig(strong_move_filter=False), series))
    }
    assert on and len(on) < len(off)
    for o in on:
        assert o.zone.start_index in off and o.confirmed_index >= o.bos.confirmed_index
        assert o.strong_index is not None and o.strong_index <= o.confirmed_index


def test_for_symbol_needs_a_doji_threshold():
    OrderBlockDetector.for_symbol("XAUUSD")
    with pytest.raises(KeyError):
        OrderBlockDetector.for_symbol("EURUSD")
