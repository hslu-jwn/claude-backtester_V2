"""Zone validation state machine. Spec: confluences.md › Validation.

Bullish zone 1.00-1.10 confirmed by candle 0 (a placeholder); the candles after it are the
ones checked. Candles are (open, high, low, close); doji threshold 0.01. Bearish cases are
the same candles mirrored around 1.05 (price -> 2.10 - price), so one parameterized test
covers both directions.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from conftest import build_series

from backtester.core.models import Direction
from backtester.detectors.zone import ZoneBook, ZoneBox, ZoneKind, ZoneState, ZoneValidator

BULL, BEAR = Direction.BULLISH, Direction.BEARISH
ACTIVE, TAPPED, CONFIRMED, INVALIDATED = (
    ZoneState.ACTIVE,
    ZoneState.TAPPED,
    ZoneState.CONFIRMED,
    ZoneState.INVALIDATED,
)
DOJI = 0.01
CREATED = (1.20, 1.25, 1.15, 1.22)  # candle 0: confirms the zone


def mirror(ohlc):
    o, h, lo, c = ohlc
    return (2.10 - o, 2.10 - lo, 2.10 - h, 2.10 - c)


def zone(direction=BULL, top=1.10, bottom=1.00, created=0):
    created_at = datetime(2026, 1, 5, 0, 5 * (created + 1), tzinfo=UTC)
    return ZoneBox(ZoneKind.FVG, direction, top, bottom, created, created, created_at)


def run(candles, direction=BULL):
    """(index, previous, state) per transition of the zone over candles after candle 0."""
    ohlc = [CREATED, *candles]
    if direction is BEAR:
        ohlc = [mirror(c) for c in ohlc]
    series = build_series(ohlc)
    validator = ZoneValidator(zone(direction), DOJI)
    return [
        (t.confirmed_index, t.previous, t.state)
        for i in range(1, len(series))
        for t in validator.on_candle(series.view(i))
    ]


both = pytest.mark.parametrize("direction", [BULL, BEAR])


@both
def test_wick_into_the_zone_is_a_tap_no_close_inside_needed(direction):
    assert run([(1.20, 1.21, 1.08, 1.18)], direction) == [(1, ACTIVE, TAPPED)]


@both
def test_wick_touching_the_edge_is_no_tap(direction):
    assert run([(1.20, 1.21, 1.10, 1.18)], direction) == []


@both
def test_green_close_above_after_a_tap_confirms(direction):
    candles = [(1.20, 1.21, 1.05, 1.08), (1.08, 1.15, 1.07, 1.12)]
    assert run(candles, direction) == [(1, ACTIVE, TAPPED), (2, TAPPED, CONFIRMED)]


@both
def test_tap_and_confirmation_on_the_same_candle(direction):
    assert run([(1.15, 1.20, 1.05, 1.18)], direction) == [
        (1, ACTIVE, TAPPED),
        (1, TAPPED, CONFIRMED),
    ]


@both
def test_green_close_above_without_a_tap_does_nothing(direction):
    assert run([(1.15, 1.25, 1.12, 1.22)], direction) == []


@both
def test_red_close_above_the_zone_does_not_confirm(direction):
    candles = [(1.20, 1.21, 1.05, 1.08), (1.18, 1.19, 1.08, 1.12)]
    assert run(candles, direction) == [(1, ACTIVE, TAPPED)]


@both
def test_a_doji_never_confirms(direction):
    candles = [(1.20, 1.21, 1.05, 1.08), (1.12, 1.15, 1.07, 1.125)]  # body 0.005
    assert run(candles, direction) == [(1, ACTIVE, TAPPED)]


@both
def test_close_exactly_at_the_top_does_not_confirm(direction):
    candles = [(1.20, 1.21, 1.05, 1.08), (1.08, 1.12, 1.07, 1.10)]
    assert run(candles, direction) == [(1, ACTIVE, TAPPED)]


@both
def test_close_below_the_bottom_invalidates_straight_from_active(direction):
    assert run([(1.20, 1.21, 0.95, 0.98)], direction) == [(1, ACTIVE, INVALIDATED)]


@both
def test_close_below_the_bottom_invalidates_after_a_tap(direction):
    candles = [(1.20, 1.21, 1.05, 1.08), (1.08, 1.09, 0.96, 0.99)]
    assert run(candles, direction) == [(1, ACTIVE, TAPPED), (2, TAPPED, INVALIDATED)]


@both
def test_any_candle_invalidates_also_a_doji_or_a_green_one(direction):
    gap_down_doji = (0.985, 0.99, 0.97, 0.99)  # body 0.005
    assert run([gap_down_doji], direction) == [(1, ACTIVE, INVALIDATED)]
    green_below = (0.90, 0.99, 0.89, 0.98)
    assert run([green_below], direction) == [(1, ACTIVE, INVALIDATED)]


@both
def test_close_exactly_at_the_bottom_does_not_invalidate(direction):
    assert run([(1.20, 1.21, 0.99, 1.00)], direction) == [(1, ACTIVE, TAPPED)]


@both
def test_confirmed_and_invalidated_are_final(direction):
    after_confirm = [(1.15, 1.20, 1.05, 1.18), (1.18, 1.19, 0.90, 0.95)]
    assert run(after_confirm, direction)[-1] == (1, TAPPED, CONFIRMED)
    after_invalid = [(1.20, 1.21, 0.95, 0.98), (0.98, 1.20, 0.97, 1.18)]
    assert run(after_invalid, direction) == [(1, ACTIVE, INVALIDATED)]


def test_transition_carries_zone_close_time_and_close():
    series = build_series([CREATED, (1.20, 1.21, 1.08, 1.18)])
    (t,) = ZoneValidator(zone(), DOJI).on_candle(series.view(1))
    assert t.zone == zone() and t.close == 1.18
    assert t.confirmed_at == datetime(2026, 1, 5, 0, 10, tzinfo=UTC)


def test_the_creating_candle_and_earlier_or_repeated_candles_are_rejected():
    series = build_series([CREATED, (1.20, 1.21, 1.08, 1.18)])
    validator = ZoneValidator(zone(), DOJI)
    with pytest.raises(ValueError):
        validator.on_candle(series.view(0))  # the zone's own candle
    validator.on_candle(series.view(1))
    with pytest.raises(ValueError):
        validator.on_candle(series.view(1))


def test_zone_box_needs_top_above_bottom():
    with pytest.raises(ValueError):
        zone(top=1.0, bottom=1.0)


def test_book_drops_finished_zones_and_reports_all_transitions():
    series = build_series([CREATED, (1.20, 1.21, 1.08, 1.18), (1.18, 1.19, 0.90, 0.95)])
    book = ZoneBook(DOJI)
    upper, lower = zone(top=1.10, bottom=1.00), zone(top=0.90, bottom=0.80)
    book.add(upper)
    book.add(lower)
    assert [(t.zone, t.state) for t in book.on_candle(series.view(1))] == [(upper, TAPPED)]
    # candle 2 closes below the upper zone (invalidated) and wicks to 0.90 (no tap of lower)
    assert [(t.zone, t.state) for t in book.on_candle(series.view(2))] == [(upper, INVALIDATED)]
    assert book.open_zones == [lower]
