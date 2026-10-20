"""Balanced price range. Spec: confluences.md › Balanced price range, › Validation.

Candles are (open, high, low, close); M5 from Mon 2026-01-05 00:00 UTC, so candle i closes
at 00:05 + 5 min * i. FVG strong-move filter off (default) unless stated.
Every fixture starts with a bearish FVG 1.30-1.40 (candles 0-2, confirmed by candle 2).
Bearish cases mirror the candles around 1.0 (price -> 2.0 - price).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from conftest import build_series
from test_fvg import mirror, random_walk

from backtester.core.models import Direction
from backtester.core.series import CandleSeries
from backtester.detectors.bpr import BalancedPriceRange, BprConfig, BprDetector
from backtester.detectors.fvg import FvgConfig
from backtester.detectors.zone import ZoneKind, ZoneState, ZoneTransition

BULL, BEAR = Direction.BULLISH, Direction.BEARISH
DOJI = 0.005

BEAR_FVG = [
    (1.50, 1.52, 1.40, 1.42),  # 0: low 1.40
    (1.42, 1.43, 1.20, 1.22),  # 1: push down
    (1.22, 1.30, 1.15, 1.18),  # 2: high 1.30 -> bearish FVG 1.30-1.40
]
NEWER_C1 = (1.18, 1.25, 1.16, 1.24)  # 3: high 1.25 = the newer gap's bottom
# 4 closes above 1.40 (invalidates the bearish FVG), 5's low 1.35 -> bullish FVG 1.25-1.35
INVALIDATED_BY_C2 = [*BEAR_FVG, NEWER_C1, (1.24, 1.50, 1.23, 1.48), (1.48, 1.60, 1.35, 1.58)]
# 4 only taps it, 5 closes above 1.40 and leaves the same bullish FVG
INVALIDATED_BY_C3 = [*BEAR_FVG, NEWER_C1, (1.24, 1.39, 1.23, 1.38), (1.38, 1.60, 1.35, 1.58)]


def run(ohlc, config=None, series=None):
    series = series or build_series(ohlc)
    detector = BprDetector(DOJI, config)
    return [e for i in range(len(series)) for e in detector.update(series.view(i))]


def bprs(events):
    return [e for e in events if isinstance(e, BalancedPriceRange)]


def transitions(events):
    return [(e.confirmed_index, e.state) for e in events if isinstance(e, ZoneTransition)]


@pytest.mark.parametrize(
    ("ohlc", "invalidated_at"), [(INVALIDATED_BY_C2, 4), (INVALIDATED_BY_C3, 5)]
)
def test_older_fvg_invalidated_by_the_move_that_forms_the_newer_one(ohlc, invalidated_at):
    (bpr,) = bprs(run(ohlc))
    zone = bpr.zone
    assert (zone.kind, zone.direction) == (ZoneKind.BPR, BULL)  # the newer FVG's direction
    assert (zone.bottom, zone.top) == (1.30, 1.35)  # overlap of 1.30-1.40 and 1.25-1.35
    assert (zone.start_index, zone.created_index, bpr.confirmed_index) == (0, 5, 5)
    assert bpr.confirmed_at == zone.created_at == datetime(2026, 1, 5, 0, 30, tzinfo=UTC)
    assert (bpr.older.direction, bpr.older.bottom, bpr.older.top) == (BEAR, 1.30, 1.40)
    assert (bpr.newer.direction, bpr.newer.bottom, bpr.newer.top) == (BULL, 1.25, 1.35)
    assert bpr.older_invalidated_index == invalidated_at


def test_bearish_mirrored():
    (bpr,) = bprs(run(mirror(INVALIDATED_BY_C2)))
    zone = bpr.zone
    assert zone.direction is BEAR
    assert (zone.bottom, zone.top) == (pytest.approx(0.65), pytest.approx(0.70))
    assert zone.created_index == 5


def test_older_fvg_still_open_when_the_newer_one_forms_is_no_bpr():
    ohlc = [
        *BEAR_FVG,
        NEWER_C1,
        (1.24, 1.39, 1.23, 1.38),  # 4: taps it, no close above 1.40
        (1.38, 1.395, 1.36, 1.39),  # 5: low 1.36 -> bullish FVG 1.25-1.36, overlapping
        (1.39, 1.50, 1.38, 1.48),  # 6: now closes above 1.40, but not the same move
    ]
    assert bprs(run(ohlc)) == []


def test_older_fvg_invalidated_before_the_newer_ones_candle_1_is_no_bpr():
    ohlc = [
        *BEAR_FVG,
        (1.18, 1.45, 1.16, 1.42),  # 3: closes above 1.40 -> invalidated
        (1.30, 1.33, 1.26, 1.28),  # 4: newer candle 1, high 1.33
        (1.28, 1.55, 1.27, 1.53),  # 5
        (1.53, 1.60, 1.36, 1.58),  # 6: low 1.36 -> bullish FVG 1.33-1.36, overlapping
    ]
    assert bprs(run(ohlc)) == []


def test_older_fvg_confirmed_before_is_no_bpr():
    ohlc = [
        *BEAR_FVG,
        (1.18, 1.35, 1.16, 1.17),  # 3: taps it and closes red below 1.30 -> confirmed
        (1.17, 1.50, 1.16, 1.48),  # 4
        (1.48, 1.60, 1.38, 1.58),  # 5: bullish FVG 1.35-1.38, overlapping
    ]
    assert bprs(run(ohlc)) == []


def test_fvgs_that_only_touch_are_no_bpr():
    ohlc = [
        *BEAR_FVG,
        (1.18, 1.40, 1.16, 1.24),  # 3: high 1.40 = the older FVG's top
        (1.24, 1.50, 1.23, 1.48),  # 4: invalidates it
        (1.48, 1.60, 1.45, 1.58),  # 5: bullish FVG 1.40-1.45 touches 1.30-1.40
    ]
    assert bprs(run(ohlc)) == []


def test_each_older_fvg_invalidated_by_the_move_forms_its_own_bpr():
    ohlc = [
        *BEAR_FVG,  # A: bearish 1.30-1.40
        (1.18, 1.19, 1.05, 1.06),  # 3: high 1.19 -> B: bearish 1.19-1.20
        (1.06, 1.16, 1.04, 1.15),  # 4: newer candle 1, high 1.16
        (1.15, 1.50, 1.14, 1.48),  # 5: closes above 1.40 -> invalidates A and B
        (1.48, 1.60, 1.35, 1.58),  # 6: bullish FVG 1.16-1.35
    ]
    found = [(b.older.top, b.zone.bottom, b.zone.top) for b in bprs(run(ohlc))]
    assert found == [(1.40, 1.30, 1.35), (1.20, 1.19, 1.20)]
    assert all(b.confirmed_index == 6 for b in bprs(run(ohlc)))


def test_an_older_fvg_forms_at_most_one_bpr():
    ohlc = [
        *BEAR_FVG,
        NEWER_C1,  # 3: high 1.25
        (1.24, 1.28, 1.22, 1.27),  # 4: high 1.28
        (1.36, 1.50, 1.35, 1.48),  # 5: invalidates it; bullish FVG 1.25-1.35 -> BPR
        (1.48, 1.55, 1.33, 1.52),  # 6: bullish FVG 1.28-1.33, same move, already paired
    ]
    (bpr,) = bprs(run(ohlc))
    assert (bpr.newer.bottom, bpr.newer.top, bpr.confirmed_index) == (1.25, 1.35, 5)


def test_validation_tap_then_confirm_after_the_newer_fvgs_candle_3():
    ohlc = [
        *INVALIDATED_BY_C2,
        (1.58, 1.59, 1.32, 1.34),  # 6: wick into 1.30-1.35, no close above
        (1.34, 1.45, 1.33, 1.44),  # 7: green close above 1.35
    ]
    assert transitions(run(ohlc)) == [(6, ZoneState.TAPPED), (7, ZoneState.CONFIRMED)]


def test_invalidation_and_open_zones():
    ohlc = [*INVALIDATED_BY_C2, (1.58, 1.59, 1.25, 1.28)]  # 6: closes below 1.30
    series = build_series(ohlc)
    detector = BprDetector(DOJI)
    out = [detector.update(series.view(i)) for i in range(len(series))]
    assert detector.open_zones == [] and transitions(out[6]) == [(6, ZoneState.INVALIDATED)]
    assert out[6][0].zone == bprs(out[5])[0].zone


def test_only_bpr_transitions_are_emitted():
    # 6 also confirms the newer bullish FVG (tap + green close above 1.35); not a BPR event
    ohlc = [*INVALIDATED_BY_C2, (1.58, 1.59, 1.32, 1.34), (1.34, 1.45, 1.33, 1.44)]
    events = run(ohlc)
    assert all(e.zone.kind is ZoneKind.BPR for e in events)


def test_fvg_strong_move_filter_applies():
    # filter on with ATR(14): no strong candle during the ATR warm-up -> no FVG, no BPR
    assert run(INVALIDATED_BY_C2, BprConfig(FvgConfig(strong_move_filter=True))) == []


@pytest.mark.parametrize("config", [BprConfig(), BprConfig(FvgConfig(strong_move_filter=True))])
def test_no_lookahead_events_only_at_their_candle_and_never_rewritten(config):
    series = random_walk(n=3000)
    full = run(None, config, series)
    assert {b.zone.direction for b in bprs(full)} == {BULL, BEAR}

    detector, seen = BprDetector(DOJI, config), []
    for i in range(len(series)):
        new = detector.update(series.view(i))
        # (a) every event is confirmed by the current candle; transitions come after the
        # candle that created their BPR, which is the newer FVG's candle 3
        assert all(e.confirmed_index == i for e in new)
        assert all(e.zone.created_index < i for e in new if isinstance(e, ZoneTransition))
        assert all(b.newer.created_index == i for b in bprs(new))
        assert all(
            b.newer.start_index <= b.older_invalidated_index <= i
            and b.older.created_index < b.older_invalidated_index
            for b in bprs(new)
        )
        seen.extend(new)
        # (b) a fresh run over a shorter history gives exactly the events emitted so far
        if i % 331 == 0:
            short = CandleSeries("TEST", series.timeframe, list(series.view(i)))
            assert run(None, config, short) == seen
    assert seen == full


def test_update_out_of_order_or_twice_raises():
    series = build_series(INVALIDATED_BY_C2)
    detector = BprDetector(DOJI)
    detector.update(series.view(0))
    with pytest.raises(ValueError):
        detector.update(series.view(0))
    with pytest.raises(ValueError):
        detector.update(series.view(2))


def test_for_symbol_needs_a_doji_threshold():
    BprDetector.for_symbol("XAUUSD")
    with pytest.raises(KeyError):
        BprDetector.for_symbol("FOOBAR")
