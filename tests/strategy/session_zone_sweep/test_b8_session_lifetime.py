"""B8: actual session expiry and weekend exclusion, strategy-session-zones.md › Sessions."""

from dataclasses import replace
from datetime import UTC, datetime, time, timedelta

import pytest
import scenario
from test_setup import run_tracker
from test_zones import LONDON, LONDON_SWINGS, NY_LAST, doji, ny, of, red, run, series

from backtester.core.models import Timeframe
from backtester.detectors.swings import SwingKind
from backtester.engine.replay import Replay
from backtester.sessions import Session, SessionConfig, SessionStart
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.signals import SetupTracker
from backtester.strategy.session_zone_sweep.zones import SessionZone, ZoneExpired


def test_active_zones_are_not_expired_at_last_thirty_minute_close():
    events = run(series((LONDON, LONDON_SWINGS + ny())))
    assert of(events, ZoneExpired) == []  # 23:30 < real session end 00:00


def test_expiry_after_gap_keeps_actual_last_active_candle_index():
    after = datetime(2026, 1, 6, 0, 30, tzinfo=UTC)
    events = run(series((LONDON, LONDON_SWINGS + ny()), (after, [doji(109.5)])))
    expired = of(events, ZoneExpired)
    assert len(expired) == 2
    assert all(e.confirmed_at == after + timedelta(minutes=30) for e in expired)
    assert all(e.last_index == NY_LAST for e in expired)


@pytest.mark.parametrize("hour", [22, 23])
def test_same_setup_can_enter_in_final_half_hour_of_session(hour):
    padding = [scenario.doji(109.5)] * ((hour - 13) * 12)
    signals = run_tracker([*scenario.LONDON, *padding, *scenario.NY_SETUP])
    assert [s.at for s in signals] == [datetime(2026, 1, 5, hour, 40, tzinfo=UTC)]


@pytest.mark.parametrize("delay,minute", [(3, 55), (4, None)])
def test_entry_before_boundary_is_allowed_but_at_boundary_is_rejected(delay, minute):
    ohlc = [
        *scenario.LONDON,
        *[scenario.doji(109.5)] * 120,
        *scenario.NY_SETUP[:-1],
        *[scenario.doji(109.6)] * delay,
        scenario.NY_SETUP[-1],
    ]
    signals = run_tracker(ohlc)
    expected = [] if minute is None else [datetime(2026, 1, 5, 23, minute, tzinfo=UTC)]
    assert [s.at for s in signals] == expected


@pytest.mark.parametrize("delay,accepted", [(0, True), (1, False), (3, False)])
def test_actual_expiry_also_applies_between_thirty_minute_closes(delay, accepted):
    # Configured Tokyo start 08:45 JST = 23:45 UTC; no new 30m close until 00:00.
    sessions = replace(SessionConfig(), tokyo=SessionStart(time(8, 45), "Asia/Tokyo"))
    config = SessionZoneSweepConfig(sessions=sessions)
    ohlc = [
        *scenario.LONDON,
        *[scenario.doji(109.5)] * 120,
        *scenario.NY_SETUP[:-1],
        *[scenario.doji(109.6)] * delay,
        scenario.NY_SETUP[-1],
    ]
    signals = run_tracker(ohlc, config)
    assert bool(signals) is accepted


def test_late_entry_target_zones_belong_only_to_current_active_session():
    ohlc = [
        *scenario.LONDON,
        *[scenario.doji(109.5)] * 120,
        *scenario.NY_SETUP,
        *[scenario.doji(110.0)] * 4,
    ]
    m5, m30, *_ = scenario.series(ohlc)
    replay, tracker = Replay(m5, [m30]), SetupTracker(scenario.SYMBOL)
    snapshots = {}
    for i in range(len(replay)):
        now = replay.close_time(i)
        tracker.update(now, replay.view(i), replay.higher_view(i, Timeframe.M30))
        if now >= datetime(2026, 1, 5, 23, 30, tzinfo=UTC):
            snapshots[now] = tracker.state.live_zones
    # NY's own zones are already finalized for Tokyo, but may not set the TP of
    # a remaining NY entry. London's still-active zones must remain available.
    for now, zones in snapshots.items():
        assert zones and all(live.zone.active_in.contains(now) for live in zones)
    late = snapshots[datetime(2026, 1, 5, 23, 40, tzinfo=UTC)]
    assert all(live.zone.formed_in.session is Session.LONDON for live in late)
    boundary = snapshots[datetime(2026, 1, 6, tzinfo=UTC)]
    assert all(live.zone.formed_in.session is Session.NEW_YORK for live in boundary)


@pytest.mark.parametrize("include_weekend", [False, True])
def test_ignored_weekend_candle_cannot_create_monday_swing(include_weekend):
    friday = datetime(2026, 1, 9, 21, 0, tzinfo=UTC)
    sunday = datetime(2026, 1, 11, 23, 0, tzinfo=UTC)
    monday = datetime(2026, 1, 11, 23, 30, tzinfo=UTC)
    segments = [(friday, [red(110, 109)])]
    if include_weekend:
        segments.append((sunday, [(109, 111.5, 108, 111)]))  # green, ignored
    segments.append((monday, [red(111, 110, hi=120), *[doji(110)] * 16]))
    zones = of(run(series(*segments)), SessionZone)
    assert [
        z for z in zones if z.formed_in.session is Session.TOKYO and z.side is SwingKind.HIGH
    ] == []
