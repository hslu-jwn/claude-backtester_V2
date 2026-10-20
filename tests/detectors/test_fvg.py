"""Fair value gap. Spec: confluences.md › Fair value gap, › Strong-move filter, › Validation.

Candles are (open, high, low, close); M5 from Mon 2026-01-05 00:00 UTC, so candle i closes
at 00:05 + 5 min * i. ATR(2) and k = 2 in most tests, so candle 2 (index 2) is checked
against the ATR of candles 0-1 (0.10 here): it is strong from a range of 0.20.
Bearish cases mirror the candles around 1.0 (price -> 2.0 - price).
"""

from __future__ import annotations

import random
from datetime import UTC, datetime

import pytest
from conftest import build_series

from backtester.core.models import Direction
from backtester.core.series import CandleSeries
from backtester.detectors.atr import StrongMoveConfig
from backtester.detectors.fvg import FairValueGap, FvgConfig, FvgDetector
from backtester.detectors.zone import ZoneKind, ZoneState, ZoneTransition

BULL, BEAR = Direction.BULLISH, Direction.BEARISH
DOJI = 0.005
ATR2 = StrongMoveConfig(atr_period=2)
FILTER_ON = FvgConfig(strong_move_filter=True, strong_move=ATR2)
FILTER_OFF = FvgConfig(strong_move_filter=False, strong_move=ATR2)

QUIET = [(1.00, 1.05, 0.95, 1.02), (1.02, 1.06, 0.96, 1.04)]  # ranges 0.10, ATR(2) = 0.10
STRONG_PUSH = (1.04, 1.40, 1.03, 1.38)  # range 0.37 >= 0.20
WEAK_PUSH = (1.04, 1.18, 1.03, 1.17)  # range 0.15 < 0.20
# candle 3: low 1.20 above candle 1's high 1.06 -> bullish FVG 1.06-1.20
BULL_FVG = [*QUIET, STRONG_PUSH, (1.38, 1.45, 1.20, 1.42)]


def mirror(ohlc):
    return [(2.0 - o, 2.0 - lo, 2.0 - h, 2.0 - c) for o, h, lo, c in ohlc]


def run(ohlc, config=FILTER_ON, series=None):
    series = series or build_series(ohlc)
    detector = FvgDetector(DOJI, config)
    return [e for i in range(len(series)) for e in detector.update(series.view(i))]


def fvgs(events):
    return [e for e in events if isinstance(e, FairValueGap)]


def transitions(events):
    return [(e.confirmed_index, e.state) for e in events if isinstance(e, ZoneTransition)]


def test_bullish_gap_between_candle_1_and_candle_3_wicks():
    (fvg,) = fvgs(run(BULL_FVG))
    zone = fvg.zone
    assert (zone.kind, zone.direction, zone.bottom, zone.top) == (ZoneKind.FVG, BULL, 1.06, 1.20)
    assert (zone.start_index, fvg.confirmed_index) == (1, 3)
    assert fvg.confirmed_at == zone.created_at == datetime(2026, 1, 5, 0, 20, tzinfo=UTC)
    assert fvg.strong and fvg.middle_range == pytest.approx(0.37)
    assert fvg.middle_threshold == pytest.approx(0.20)


def test_bearish_mirrored():
    (fvg,) = fvgs(run(mirror(BULL_FVG)))
    zone = fvg.zone
    assert zone.direction is BEAR
    assert (zone.bottom, zone.top) == (pytest.approx(0.80), pytest.approx(0.94))
    assert (zone.start_index, fvg.confirmed_index) == (1, 3)


@pytest.mark.parametrize("flip", [False, True])
def test_equal_wicks_are_no_gap(flip):
    ohlc = [*QUIET, STRONG_PUSH, (1.38, 1.45, 1.06, 1.42)]  # candle 3 low = candle 1 high
    assert run(mirror(ohlc) if flip else ohlc) == []


def test_candle_2_wick_and_color_do_not_matter():
    red_push = (1.40, 1.42, 0.98, 1.21)  # red, range 0.44, wick far into candle 1's range
    (fvg,) = fvgs(run([*QUIET, red_push, (1.21, 1.30, 1.20, 1.28)]))
    assert (fvg.zone.bottom, fvg.zone.top) == (1.06, 1.20)


@pytest.mark.parametrize("flip", [False, True])
def test_weak_candle_2_no_fvg_with_the_filter_on_fvg_with_it_off(flip):
    ohlc = [*QUIET, WEAK_PUSH, (1.17, 1.25, 1.10, 1.22)]  # gap 1.06-1.10
    ohlc = mirror(ohlc) if flip else ohlc
    assert run(ohlc, FILTER_ON) == []
    (fvg,) = fvgs(run(ohlc, FILTER_OFF))
    assert not fvg.strong and fvg.middle_threshold == pytest.approx(0.20)


def test_during_atr_warm_up_candle_2_is_never_strong():
    default_atr = FvgConfig(strong_move_filter=True)  # ATR(14): no ATR before candle 13
    assert run(BULL_FVG, default_atr) == []
    off = FvgConfig()  # filter off by default
    (fvg,) = fvgs(run(BULL_FVG, off))
    assert not fvg.strong and fvg.middle_threshold is None


def test_filter_uses_its_own_k():
    k4 = FvgConfig(True, StrongMoveConfig(atr_period=2, atr_mult=4.0))  # needs 0.40
    assert run(BULL_FVG, k4) == []


def test_fvgs_of_both_directions_whatever_the_trend():
    # up gap, then a down gap right after: both are FVGs (the strategy picks by trend)
    ohlc = [
        *BULL_FVG,
        (1.42, 1.43, 1.30, 1.31),  # 4 red
        (1.31, 1.32, 0.90, 0.92),  # 5 red push, range 0.42
        (0.92, 0.95, 0.85, 0.88),  # 6: high 0.95 below candle 4's low 1.30 -> bearish FVG
    ]
    found = [(f.direction, f.confirmed_index) for f in fvgs(run(ohlc))]
    assert found == [(BULL, 3), (BEAR, 6)]


def test_validation_tap_then_confirm_after_candle_3():
    ohlc = [*BULL_FVG, (1.42, 1.43, 1.15, 1.18), (1.18, 1.30, 1.17, 1.28)]
    events = run(ohlc)
    assert transitions(events) == [(4, ZoneState.TAPPED), (5, ZoneState.CONFIRMED)]


def test_candle_3_does_not_check_its_own_fvg():
    # candle 3 is green and closes above the top, but it formed the FVG: no tap, no confirm
    assert transitions(run(BULL_FVG)) == []


def test_invalidation_and_open_zones():
    ohlc = [*BULL_FVG, (1.42, 1.43, 1.00, 1.02)]  # closes below 1.06
    series = build_series(ohlc)
    detector = FvgDetector(DOJI, FILTER_ON)
    out = [detector.update(series.view(i)) for i in range(len(series))]
    assert len(detector.open_zones) == 0 and transitions(out[4]) == [(4, ZoneState.INVALIDATED)]
    invalidated = out[4][0]
    assert invalidated.zone == fvgs(out[3])[0].zone  # the box is kept (e.g. for inverse FVGs)


def test_a_doji_never_confirms_an_fvg():
    ohlc = [*BULL_FVG, (1.42, 1.43, 1.15, 1.18), (1.25, 1.30, 1.17, 1.253)]  # body 0.003
    assert transitions(run(ohlc)) == [(4, ZoneState.TAPPED)]


def random_walk(n=800, seed=5):
    rng = random.Random(seed)
    ohlc, price = [], 100.0
    for _ in range(n):
        o = price + rng.choice([0.0, 0.0, 0.0, rng.uniform(-1, 1)])  # sometimes a gap
        c = o + rng.choice([-1, 1]) * rng.choice([0.0, 0.002, 0.3, 1.0, 3.0])
        ohlc.append((o, max(o, c) + rng.random() / 2, min(o, c) - rng.random() / 2, c))
        price = c
    return build_series(ohlc)


@pytest.mark.parametrize("config", [FvgConfig(strong_move_filter=True), FvgConfig()])
def test_no_lookahead_events_only_at_their_candle_and_never_rewritten(config):
    series = random_walk()
    full = run(None, config, series)
    assert {f.direction for f in fvgs(full)} == {BULL, BEAR}
    assert {s for _, s in transitions(full)} == set(ZoneState) - {ZoneState.ACTIVE}

    detector, seen = FvgDetector(DOJI, config), []
    for i in range(len(series)):
        new = detector.update(series.view(i))
        # (a) every event is confirmed by the current candle; transitions come after the
        # candle that created their zone
        assert all(e.confirmed_index == i for e in new)
        assert all(e.zone.created_index < i for e in new if isinstance(e, ZoneTransition))
        seen.extend(new)
        # (b) a fresh run over a shorter history gives exactly the events emitted so far
        if i % 89 == 0:
            short = CandleSeries("TEST", series.timeframe, list(series.view(i)))
            assert run(None, config, short) == seen
    assert seen == full


def test_filter_on_keeps_a_subset_of_the_filter_off_fvgs():
    series = random_walk()
    on = {f.zone for f in fvgs(run(None, FvgConfig(strong_move_filter=True), series))}
    off = fvgs(run(None, FvgConfig(), series))
    assert on == {f.zone for f in off if f.strong} and len(on) < len(off)


def test_update_out_of_order_or_twice_raises():
    series = build_series(BULL_FVG)
    detector = FvgDetector(DOJI)
    detector.update(series.view(0))
    with pytest.raises(ValueError):
        detector.update(series.view(0))
    with pytest.raises(ValueError):
        detector.update(series.view(2))


def test_for_symbol_needs_a_doji_threshold():
    FvgDetector.for_symbol("XAUUSD")
    with pytest.raises(KeyError):
        FvgDetector.for_symbol("FOOBAR")
