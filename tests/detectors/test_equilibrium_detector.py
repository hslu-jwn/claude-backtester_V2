"""Equilibrium (EQ). Spec: confluences.md › Equilibrium.

Candles are (open, high, low, close); M5 from Mon 2026-01-05 00:00 UTC. Doji threshold 0.065.
"""

from __future__ import annotations

import random

import pytest
from conftest import build_series

from backtester.core.models import Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.detectors.equilibrium import (
    Equilibrium,
    EquilibriumConfig,
    EquilibriumDetector,
    deepest_wick,
    equilibrium_box,
    equilibrium_stop_loss,
)
from backtester.detectors.zone import ZoneKind, ZoneState, ZoneTransition

BULL, BEAR = Direction.BULLISH, Direction.BEARISH

# 0-3: swing high 10.5 (@0), swing low 9.5 (@1), bearish BOS at 3 (first BOS, no sweep:
#      no high was taken). Leg from the highest high since the broken low's candle (10.45
#      @1) to the BOS candle's low 9.0.
# 3-4: lows 9.0 / 8.7 take the swing low 9.5: the bottom of the move is candle 4 (8.7).
# 5-7: swing low 8.7 (@4), lower high 9.3 (@5, confirmed 6), swing low 8.9 (@6).
# 8:   bullish BOS of 9.3, high 9.6: a liquidity sweep of lows (candle 4, 8.7) -> leg
#      8.7 -> 9.6, EQ 9.15. Without the sweep the move would start at 8.75 (candle 5,
#      the lowest low since the broken high's candle).
SWEEP_THEN_BOS = [
    (10.0, 10.5, 9.9, 10.4),  # 0 green
    (10.4, 10.45, 9.5, 9.6),  # 1 red: swing high 10.5
    (9.6, 9.9, 9.55, 9.8),  # 2 green: swing low 9.5
    (9.8, 9.85, 9.0, 9.1),  # 3 red: swing high 9.9; bearish BOS of 9.5
    (9.1, 9.15, 8.7, 8.8),  # 4 red: the bottom 8.7
    (8.8, 9.3, 8.75, 9.2),  # 5 green: swing low 8.7
    (9.2, 9.25, 8.9, 9.0),  # 6 red: swing high 9.3
    (9.0, 9.2, 8.95, 9.15),  # 7 green: swing low 8.9
    (9.15, 9.6, 9.1, 9.55),  # 8 green: bullish BOS of 9.3, high 9.6
]
TAP_CONFIRM = [
    (9.55, 9.58, 9.1, 9.2),  # 9 red: wick below 9.15 (tap), red close above: no confirm
    (9.2, 9.5, 9.12, 9.45),  # 10 green: close above 9.15 -> confirmed
]


def run(ohlc, series=None, config=None):
    series = series or build_series(ohlc)
    detector = EquilibriumDetector(0.065, config)
    return [e for i in range(len(series)) for e in detector.update(series.view(i))]


def boxes(events):
    return [e for e in events if isinstance(e, Equilibrium)]


def test_after_a_sweep_the_leg_runs_from_the_sweep_extreme_to_the_bos_wick():
    _, bull = boxes(run(SWEEP_THEN_BOS))
    z = bull.zone
    assert z.kind is ZoneKind.EQUILIBRIUM and z.direction is BULL
    assert (z.bottom, z.top) == (8.7, pytest.approx(9.15))  # leg low, 50% level
    assert (z.start_index, z.created_index, bull.confirmed_index) == (4, 8, 8)
    assert (bull.leg_start, bull.leg_end, bull.swept) == (8.7, 9.6, True)
    assert bull.level == pytest.approx(9.15)
    assert bull.bos.direction is BULL and bull.bos.confirmed_index == 8


def test_without_a_sweep_the_leg_starts_where_the_bos_move_started():
    bear, _ = boxes(run(SWEEP_THEN_BOS))
    z = bear.zone
    # bearish mirrored: the far edge (top) is the leg's high, the near edge the 50%
    assert z.direction is BEAR and bear.swept is False
    assert (z.top, z.bottom) == (10.45, pytest.approx((10.45 + 9.0) / 2))
    assert (z.start_index, z.created_index) == (1, 3)


def test_the_leg_is_fixed_at_the_bos_candle():
    # candle 9 runs far above the BOS candle's high: the EQ stays 8.7 - 9.15
    ohlc = [*SWEEP_THEN_BOS, (9.55, 11.0, 9.5, 10.9)]
    _, bull = boxes(run(ohlc))
    assert (bull.zone.bottom, bull.zone.top) == (8.7, pytest.approx(9.15))


def test_tap_then_green_close_back_above_the_50_confirms():
    events = run(SWEEP_THEN_BOS + TAP_CONFIRM)
    _, bull = boxes(events)
    steps = [(t.state, t.confirmed_index) for t in events if isinstance(t, ZoneTransition)]
    assert steps == [(ZoneState.TAPPED, 9), (ZoneState.CONFIRMED, 10)]
    assert all(t.zone == bull.zone for t in events if isinstance(t, ZoneTransition))


def test_only_a_close_below_the_leg_low_invalidates_a_wick_does_not():
    wick_below = [*SWEEP_THEN_BOS, (9.55, 9.58, 8.6, 9.0)]  # 9: wick 8.6 < 8.7, close 9.0
    steps = [t.state for t in run(wick_below) if isinstance(t, ZoneTransition)]
    assert steps == [ZoneState.TAPPED]
    close_below = [*SWEEP_THEN_BOS, (9.55, 9.58, 8.6, 8.65)]  # 9: close 8.65 < 8.7
    events = run(close_below)
    steps = [(t.state, t.zone.direction) for t in events if isinstance(t, ZoneTransition)]
    assert steps == [(ZoneState.INVALIDATED, BULL)]


def test_equilibrium_box_geometry():
    z = equilibrium_box(BULL, 2, 100.0, 5, 200.0, created_at=None)
    assert (z.bottom, z.top, z.near, z.far, z.start_index, z.created_index) == (
        100.0, 150.0, 150.0, 100.0, 2, 5,
    )  # fmt: skip
    z = equilibrium_box(BEAR, 2, 200.0, 5, 100.0, created_at=None)
    assert (z.bottom, z.top, z.near, z.far) == (150.0, 200.0, 150.0, 200.0)


def test_stop_loss_spec_example():
    # swing low 100, BOS high 200, EQ 150, deepest wick 140 -> distance 40 -> SL 96;
    # EQ-only toggle: SL beyond the deepest wick, 136
    z = equilibrium_box(BULL, 0, 100.0, 1, 200.0, created_at=None)
    assert equilibrium_stop_loss(z, 140.0, EquilibriumConfig()) == pytest.approx(96.0)
    at_wick = EquilibriumConfig(sl_at_deepest_wick=True)
    assert equilibrium_stop_loss(z, 140.0, at_wick) == pytest.approx(136.0)
    # short mirrored: swing high 200, BOS low 100, EQ 150, deepest wick 160
    z = equilibrium_box(BEAR, 0, 200.0, 1, 100.0, created_at=None)
    assert equilibrium_stop_loss(z, 160.0, EquilibriumConfig()) == pytest.approx(204.0)
    assert equilibrium_stop_loss(z, 160.0, at_wick) == pytest.approx(164.0)
    assert equilibrium_stop_loss(z, 160.0, EquilibriumConfig(sl_buffer=0.0)) == 200.0


def test_deepest_wick_counts_the_candles_after_the_bos_up_to_now():
    series = build_series(SWEEP_THEN_BOS + TAP_CONFIRM)
    _, bull = boxes(run(None, series=series))
    # candle 8 (the BOS candle, low 9.1) doesn't count; 9: 9.1, 10: 9.12
    assert deepest_wick(series.view(10), bull.zone) == 9.1
    assert deepest_wick(series.view(8), bull.zone) is None  # nothing after the BOS yet


def test_config_rejects_a_negative_buffer():
    with pytest.raises(ValueError):
        EquilibriumConfig(sl_buffer=-0.1)


def random_walk(n=800, seed=5):
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
    assert {e.zone.direction for e in boxes(full)} == {BULL, BEAR}
    assert any(e.swept for e in boxes(full)) and not all(e.swept for e in boxes(full))

    detector, seen = EquilibriumDetector(0.065), []
    for i in range(len(series)):
        new = detector.update(series.view(i))
        for e in new:
            # (a) every event is confirmed by the current candle; an EQ by its BOS candle,
            # and its leg lies in the past
            assert e.confirmed_index == i
            if isinstance(e, Equilibrium):
                assert e.bos.confirmed_index == e.zone.created_index == i
                assert e.zone.start_index <= i
        seen.extend(new)
        # (b) a fresh run over a shorter history gives exactly the events emitted so far
        if i % 97 == 0:
            short = CandleSeries("TEST", Timeframe.M5, list(series.view(i)))
            assert run(None, series=short) == seen
    assert seen == full


def test_update_out_of_order_raises():
    series = build_series(SWEEP_THEN_BOS)
    detector = EquilibriumDetector(0.065)
    detector.update(series.view(0))
    with pytest.raises(ValueError):
        detector.update(series.view(0))
