"""Session zones on 30m. Spec: strategy-session-zones.md › Session zones, › Zone flips.

Fixtures are 30m candles in January 2026 (no DST anywhere), times in UTC:
Tokyo 00:00, London 08:00, New York 13:00. A candle belongs to the session it CLOSES in,
so with the series starting Monday 2026-01-05 08:00, London's candles are 0-8 (the last,
12:00, closes at 12:30) and New York's are 9-30 (12:30 closes at the NY open 13:00; 23:00
is the last, 23:30 closes at Tokyo's start).
Fillers are dojis (body 0 <= doji threshold 0.065): they form no swing and never break.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pytest
from conftest import build_candles

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.detectors.swings import SwingKind
from backtester.sessions import Session
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.zones import (
    Role,
    SessionZone,
    SessionZoneTracker,
    ZoneBreak,
    ZoneExpired,
    ZoneRoleSet,
)

M30 = Timeframe.M30
DOJI = 0.065
LONDON = datetime(2026, 1, 5, 8, 0, tzinfo=UTC)  # Monday
LONDON_LAST = 8  # 12:00, closes 12:30
NY_FIRST = 9  # 12:30, closes at the NY open
NY_LAST = 30  # 23:00, closes 23:30


def doji(price):
    return (price, price + 0.2, price - 0.2, price)


def green(o, c, hi=None, lo=None):
    return (o, c + 0.5 if hi is None else hi, o - 0.5 if lo is None else lo, c)


def red(o, c, hi=None, lo=None):
    return (o, o + 0.5 if hi is None else hi, c - 0.5 if lo is None else lo, c)


def series(*segments):
    """Candles from (start, [ohlc, ...]) segments, each one consecutive 30m candles."""
    candles = [c for start, ohlc in segments for c in build_candles(ohlc, M30, start)]
    return CandleSeries("TEST", M30, candles)


def run(s, config=None):
    tracker = SessionZoneTracker(DOJI, config)
    return [e for i in range(len(s)) for e in tracker.update(s.view(i))]


def of(events, kind):
    return [e for e in events if isinstance(e, kind)]


# London: a swing low at candle 1 (107, zone 107-108), a swing high at candle 3 (112,
# zone 111-112), then dojis at 109.5, ending London at 109.5 (inside neither zone).
LONDON_SWINGS = [
    red(110.0, 108.0, lo=107.5),  # 0
    green(108.0, 109.0, lo=107.0),  # 1: low swing 107, body bottoms 108 / 108
    green(109.0, 111.0, hi=112.0),  # 2: high swing 112 (candle 2), body tops 111 / 111
    red(111.0, 110.0, hi=111.2),  # 3
    *[doji(109.5)] * 5,  # 4-8
]


def ny(*ohlc, fill=109.5):
    """New York candles 9.., padded with dojis to NY's last candle (30)."""
    return [*ohlc, *[doji(fill)] * (NY_LAST - NY_FIRST + 1 - len(ohlc))]


def low_zone_events(events):
    low = next(z for z in of(events, SessionZone) if z.side is SwingKind.LOW)
    return [e for e in events if getattr(e, "zone", None) == low]


def test_zones_form_at_the_sessions_last_candle_and_are_active_in_the_next():
    events = run(series((LONDON, LONDON_SWINGS)))
    high, low = of(events, SessionZone)
    assert (high.side, high.top, high.bottom) == (SwingKind.HIGH, 112.0, 111.0)
    assert (low.side, low.top, low.bottom) == (SwingKind.LOW, 108.0, 107.0)
    assert high.confirmed_index == low.confirmed_index == LONDON_LAST  # closes at 12:30
    assert high.formed_in.session is Session.LONDON
    assert high.active_in.session is Session.NEW_YORK
    assert high.start_index == 2 and low.start_index == 0  # first turn candle


def test_a_candle_belongs_to_the_session_it_closes_in():
    # the 07:30 candle closes at the London open: it is London's first candle, so the swing
    # low with its extreme wick there (106, confirmed by 08:00) is London's
    candles = [red(110.0, 108.0, lo=106.0), green(108.0, 109.0, lo=107.0)]  # 07:30, 08:00
    candles += [*LONDON_SWINGS[2:], doji(109.5)]  # 08:30-12:00
    (low,) = [
        z
        for z in of(run(series((LONDON - timedelta(minutes=30), candles))), SessionZone)
        if z.side is SwingKind.LOW
    ]
    assert low.formed_in.session is Session.LONDON
    assert (low.swing.price, low.start_index) == (106.0, 0)
    assert low.confirmed_index == 9  # the 12:00 candle, London's last


def test_no_confirmed_swing_on_one_side_no_zone_on_that_side():
    # only green candles after the low: the highest wick (candle 8) is no swing
    rising = [red(110.0, 108.0), green(108.0, 109.0, lo=107.0)]
    rising += [green(109.0 + i, 110.0 + i) for i in range(7)]
    zones = of(run(series((LONDON, rising))), SessionZone)
    assert [z.side for z in zones] == [SwingKind.LOW]


def test_no_swing_at_all_no_zone():
    assert run(series((LONDON, [doji(100.0)] * 10))) == []


def test_swing_confirmed_by_the_next_sessions_first_candle_does_not_count():
    # London's highest wick 120 (candle 8) is confirmed only by NY's red first candle
    # (12:30, closes at the NY open): London keeps the earlier 112 swing, and NY doesn't
    # get the 120 one either
    candles = [*LONDON_SWINGS[:4], *[green(110.0 + i, 111.0 + i) for i in range(4)]]  # 4-7
    candles += [green(115.0, 116.0, hi=120.0)]  # 8
    candles += ny(red(116.0, 115.0, hi=119.0), fill=115.0)  # 9
    events = run(series((LONDON, candles)))
    london = [z for z in of(events, SessionZone) if z.formed_in.session is Session.LONDON]
    assert [(z.side, z.swing.price) for z in london] == [
        (SwingKind.HIGH, 112.0),
        (SwingKind.LOW, 107.0),
    ]
    new_york = [z for z in of(events, SessionZone) if z.formed_in.session is Session.NEW_YORK]
    assert all(z.side is not SwingKind.HIGH for z in new_york)


def test_swing_with_its_extreme_on_the_next_sessions_first_candle_counts_there():
    # NY's first candle (12:30) has the high 121; its other turn candle (12:00) closed in
    # London, so it doesn't count: the zone and the box come from the NY candle only
    candles = [*LONDON_SWINGS[:4], *[green(110.0 + i, 111.0 + i) for i in range(4)]]  # 4-7
    candles += [green(114.0, 115.5)]  # 8: London's last, body top 115.5
    candles += ny(red(116.0, 115.0, hi=121.0), fill=115.0)  # 9: body top 116
    events = run(series((LONDON, candles)))
    new_york = [z for z in of(events, SessionZone) if z.formed_in.session is Session.NEW_YORK]
    assert [(z.side, z.top, z.bottom) for z in new_york] == [(SwingKind.HIGH, 121.0, 116.0)]
    assert new_york[0].swing.index == NY_FIRST
    assert new_york[0].start_index == NY_FIRST  # not London's turn candle 8
    assert new_york[0].confirmed_index == NY_LAST


def test_most_extreme_confirmed_swing_wins_over_a_higher_unconfirmed_wick():
    candles = [
        green(100.0, 101.0, hi=103.0),  # 0
        red(101.0, 100.5),  # 1: swing high 103
        green(100.5, 102.0, hi=105.0),  # 2
        red(102.0, 101.0),  # 3: swing high 105 (most extreme confirmed)
        green(101.0, 102.0, hi=104.0),  # 4
        red(102.0, 101.5),  # 5: swing high 104
        green(101.5, 102.0),  # 6
        green(102.0, 106.0, hi=108.0),  # 7: highest wick, never confirmed in London
        doji(106.0),  # 8
    ]
    zones = of(run(series((LONDON, candles))), SessionZone)
    assert [(z.side, z.top, z.bottom) for z in zones if z.side is SwingKind.HIGH] == [
        (SwingKind.HIGH, 105.0, 102.0)
    ]


def test_zone_runs_from_the_extreme_wick_to_the_innermost_body_edge_dojis_skipped():
    candles = [
        green(100.0, 104.0, hi=106.0),  # 0: body top 104
        (104.0, 107.0, 103.9, 104.03),  # 1: doji with the highest wick, skipped
        red(103.0, 101.0, hi=105.0),  # 2: body top 103 -> high zone 103-106
        *[doji(102.0)] * 6,
    ]
    (high,) = of(run(series((LONDON, candles))), SessionZone)
    assert (high.top, high.bottom) == (106.0, 103.0)


def test_role_by_price_from_the_forming_sessions_last_close():
    events = run(series((LONDON, LONDON_SWINGS)))
    roles = {e.zone.side: e.role for e in of(events, ZoneRoleSet)}
    # London closed at 109.5: the low zone (107-108) is below price, the high (111-112) above
    assert roles == {SwingKind.LOW: Role.SUPPORT, SwingKind.HIGH: Role.RESISTANCE}
    assert all(
        e.confirmed_index == LONDON_LAST and e.close == 109.5 for e in of(events, ZoneRoleSet)
    )


def test_the_active_sessions_first_candle_can_already_break_the_zone():
    events = low_zone_events(run(series((LONDON, LONDON_SWINGS + ny(red(109.5, 106.5))))))
    assert [(b.confirmed_index, b.number) for b in of(events, ZoneBreak)] == [(NY_FIRST, 1)]


def test_close_inside_the_zone_first_close_outside_sets_the_role_no_break():
    candles = [*LONDON_SWINGS[:4], *[doji(107.5)] * 5]  # London ends inside 107-108
    candles += ny(
        (107.5, 107.9, 107.2, 107.6),  # 9: still inside
        (106.6, 106.7, 106.0, 106.62),  # 10: doji closing below: sets no role
        red(107.6, 106.5),  # 11: first close outside, below -> resistance, no break
        green(106.5, 108.4),  # 12: close above resistance -> 1st break
        fill=108.5,
    )
    events = run(series((LONDON, candles)))
    low = next(z for z in of(events, SessionZone) if z.side is SwingKind.LOW)
    roles = [e for e in of(events, ZoneRoleSet) if e.zone == low]
    assert [(e.confirmed_index, e.role) for e in roles] == [(11, Role.RESISTANCE)]
    breaks = [e for e in of(events, ZoneBreak) if e.zone == low]
    assert [(b.confirmed_index, b.number, b.role) for b in breaks] == [(12, 1, Role.SUPPORT)]


FLIPS = ny(
    (109.5, 109.6, 106.0, 107.5),  # 9: wick below support, close inside: nothing
    (106.9, 107.0, 106.0, 106.9),  # 10: doji closing below: no break
    red(107.5, 106.8),  # 11: close below 107 -> 1st break, now resistance
    red(106.8, 106.6, hi=110.0),  # 12: wick above 108: nothing
    green(106.6, 108.2),  # 13: close above 108 -> 2nd break, support again
    red(108.2, 106.5),  # 14: close below 107 -> 3rd break, killed
    green(106.5, 109.0),  # 15: would be a 4th break: the zone is gone
)


def test_flips_on_each_break_and_the_third_break_kills_the_zone():
    events = low_zone_events(run(series((LONDON, LONDON_SWINGS + FLIPS))))
    breaks = of(events, ZoneBreak)
    assert [(b.confirmed_index, b.number, b.role, b.killed) for b in breaks] == [
        (11, 1, Role.RESISTANCE, False),
        (13, 2, Role.SUPPORT, False),
        (14, 3, Role.RESISTANCE, True),
    ]
    assert [b.close for b in breaks] == [106.8, 108.2, 106.5]
    assert of(events, ZoneExpired) == []  # killed, not expired: nothing after the kill


def test_kill_break_count_is_a_setting():
    config = SessionZoneSweepConfig(zone_kill_breaks=2)
    events = low_zone_events(run(series((LONDON, LONDON_SWINGS + FLIPS)), config))
    assert [(b.number, b.killed) for b in of(events, ZoneBreak)] == [(1, False), (2, True)]
    with pytest.raises(ValueError):
        SessionZoneSweepConfig(zone_kill_breaks=0)


def test_kill_rule_off_keeps_flipping_the_zone():
    config = SessionZoneSweepConfig(zone_kill=False)
    events = low_zone_events(run(series((LONDON, LONDON_SWINGS + FLIPS)), config))
    breaks = of(events, ZoneBreak)
    # the 3rd break no longer kills it, so a later close breaks it a 4th time
    assert [(b.number, b.killed) for b in breaks] == [(n, False) for n in (1, 2, 3, 4)]
    assert [b.role for b in breaks][:3] == [Role.RESISTANCE, Role.SUPPORT, Role.RESISTANCE]


def test_zone_expires_at_the_end_of_its_session_and_is_not_checked_after():
    tokyo = LONDON + timedelta(hours=15, minutes=30)  # 23:30, closes at Tokyo's start
    s = series((LONDON, LONDON_SWINGS + ny()), (tokyo, [red(109.5, 100.0), *[doji(100)] * 3]))
    events = low_zone_events(run(s))
    (expired,) = of(events, ZoneExpired)
    assert (expired.confirmed_index, expired.last_index) == (NY_LAST, NY_LAST)
    assert of(events, ZoneBreak) == []  # Tokyo's close below 107 comes too late


def test_friday_new_york_zones_carry_into_monday_tokyo_sunday_candles_ignored():
    friday_ny = datetime(2026, 1, 9, 13, 0, tzinfo=UTC)  # Friday, gold closes at 22:00
    friday = [red(110.0, 108.0, lo=107.5), green(108.0, 109.0, lo=107.0)]  # low zone 107-108
    friday += [doji(109.5)] * 16  # 2-17, last closes 22:00 at 109.5
    sunday = [red(109.5, 100.0)]  # 23:00, closes 23:30 on Sunday: ignored
    monday = [doji(100.0), red(100.0, 99.5), doji(99.5)]  # 23:30 closes at Tokyo's start
    s = series(
        (friday_ny, friday),
        (datetime(2026, 1, 11, 23, 0, tzinfo=UTC), sunday + monday),
    )
    events = run(s)
    (zone,) = of(events, SessionZone)
    assert zone.formed_in.session is Session.NEW_YORK and zone.formed_in.trading_date.day == 9
    assert zone.active_in.session is Session.TOKYO and zone.active_in.trading_date.day == 12
    assert zone.confirmed_index == 19  # known at Tokyo's first candle, not on Sunday
    (role,) = of(events, ZoneRoleSet)
    assert (role.role, role.close) == (Role.SUPPORT, 109.5)  # Friday's close, not Sunday's
    # Sunday's close at 100 broke nothing; Tokyo's red close below 107 is the 1st break
    assert [(b.confirmed_index, b.role) for b in of(events, ZoneBreak)] == [(20, Role.RESISTANCE)]
    off = SessionZoneSweepConfig(friday_ny_carries_to_monday_tokyo=False)
    assert run(s, off) == []


def test_only_30m_candles():
    tracker = SessionZoneTracker(DOJI)
    s = CandleSeries("TEST", Timeframe.M5, build_candles([doji(1.0)], Timeframe.M5, LONDON))
    with pytest.raises(ValueError, match="M30"):
        tracker.update(s.view(0))


def random_walk(n=1500, seed=3):
    """Continuous 30m candles over weekends too (those are ignored)."""
    rng = random.Random(seed)
    ohlc, price = [], 100.0
    for _ in range(n):
        o = price
        c = o + rng.choice([-1, 1]) * rng.choice([0.0, 0.03, 0.5, 1.2, 3.0])
        ohlc.append((o, max(o, c) + rng.random(), min(o, c) - rng.random(), c))
        price = c
    return CandleSeries("TEST", M30, build_candles(ohlc, M30, LONDON))


def test_no_lookahead_events_only_at_their_candle_and_never_rewritten():
    s = random_walk()
    full = run(s)
    assert {type(e) for e in full} == {SessionZone, ZoneRoleSet, ZoneBreak, ZoneExpired}
    assert any(b.killed for b in of(full, ZoneBreak))

    tracker, seen = SessionZoneTracker(DOJI), []
    for i in range(len(s)):
        new = tracker.update(s.view(i))
        # (a) every event is confirmed by the current candle; a zone's swing was confirmed
        # by then, and nothing happens to a zone before it exists
        assert all(e.confirmed_index == i for e in new)
        assert all(z.swing.confirmed_index <= i for z in of(new, SessionZone))
        assert all(e.zone.confirmed_index <= i for e in new if not isinstance(e, SessionZone))
        seen.extend(new)
        # (b) a fresh run over a shorter history gives exactly the events emitted so far
        if i % 97 == 0:
            short = CandleSeries("TEST", M30, list(s.view(i)))
            assert run(short) == seen
    assert seen == full
