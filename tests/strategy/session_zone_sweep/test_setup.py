"""Entry sequence state machine and its wiring to the detectors.
Spec: strategy-session-zones.md › Entry sequence, › Invalidation & reset, › Zone flips."""

from __future__ import annotations

import math
import random
from datetime import UTC, date, datetime, timedelta

import pytest
import scenario
from conftest import build_series
from scenario import BOS_INDEX, ENTRY_INDEX, LONDON, NY_FIRST, NY_SETUP, bar

from backtester.core.models import Candle, Direction, Timeframe
from backtester.detectors.bos import BosDetector
from backtester.detectors.swings import SwingDetector, SwingKind, SwingPoint
from backtester.detectors.zone import ZoneBox, ZoneKind
from backtester.engine.replay import Replay
from backtester.sessions import Session, SessionInstance
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.setup import (
    Setup,
    Step,
    StructureBreak,
    StructureTracker,
)
from backtester.strategy.session_zone_sweep.signals import SetupTracker
from backtester.strategy.session_zone_sweep.zones import SessionZone

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
DOJI = 0.065
T0 = datetime(2026, 1, 5, 13, 0, tzinfo=UTC)
M5, M30 = timedelta(minutes=5), timedelta(minutes=30)


# --- StructureTracker ---------------------------------------------------------------------


def wave(n: int, seed: int = 1):
    rng = random.Random(seed)
    price, out = 100.0, []
    for i in range(n):
        close = price + 2 * math.sin(i / 6) - 2 * math.sin((i - 1) / 6) + rng.uniform(-0.6, 0.6)
        out.append((price, max(price, close) + 0.2, min(price, close) - 0.2, close))
        price = close
    return out


def test_real_breaks_are_exactly_the_bos_detector_events():
    s = build_series(wave(400))
    tracker, bos = StructureTracker(DOJI), BosDetector(SwingDetector(DOJI))
    mine, theirs = [], []
    for i in range(len(s)):
        mine += [b for b in tracker.update(s.view(i)) if b.is_bos]
        theirs += bos.update(s.view(i))
    assert [(b.index, b.direction, b.swing) for b in mine] == [
        (e.confirmed_index, e.direction, e.swing) for e in theirs
    ]
    assert tracker.trend is bos.trend


def test_with_trend_breaks_are_reported_but_are_no_bos():
    s = build_series(wave(400))
    tracker = StructureTracker(DOJI)
    found = [b for i in range(len(s)) for b in tracker.update(s.view(i))]
    with_trend = [b for b in found if not b.is_bos]
    assert with_trend  # the wave makes higher highs in uptrends
    for b in with_trend:
        previous_bos = [x for x in found if x.is_bos and x.index < b.index][-1]
        assert previous_bos.direction is b.direction


def test_leg_extreme_is_the_lowest_low_since_the_broken_swing():
    s = build_series(
        [
            (10.0, 11.0, 9.8, 10.8),  # green
            (10.8, 11.5, 10.2, 10.4),  # red: swing high 11.5 (candle 1)
            (10.4, 10.5, 9.9, 10.0),  # red, low 9.9
            (10.0, 11.8, 10.0, 11.7),  # green closes above 11.5: bullish BOS
        ]
    )
    tracker = StructureTracker(DOJI)
    [b] = [b for i in range(len(s)) for b in tracker.update(s.view(i))]
    assert b.is_bos and b.index == 3 and b.swing.price == 11.5
    assert (b.leg_index, b.leg_extreme) == (2, 9.9)


# --- Setup state machine ------------------------------------------------------------------

LONDON_SESSION = SessionInstance(Session.LONDON, date(2026, 1, 5), T0 - timedelta(hours=5), T0)
NY_SESSION = SessionInstance(
    Session.NEW_YORK, date(2026, 1, 5), T0, datetime(2026, 1, 6, 0, 0, tzinfo=UTC)
)


def zone(top=108.0, bottom=107.0) -> SessionZone:
    swing = SwingPoint(3, T0, SwingKind.LOW, bottom, 2, T0, 2)
    return SessionZone(5, T0, SwingKind.LOW, top, bottom, swing, LONDON_SESSION, NY_SESSION, 2)


def c30(k: int, o, h, lo, c) -> tuple[Candle, datetime]:
    """30m candle k of New York: opens T0 + k x 30m, returns (candle, close time)."""
    ts = T0 + k * M30
    return Candle(ts, o, h, lo, c), ts + M30


def brk(direction, index, minutes, is_bos=True, leg_index=None) -> StructureBreak:
    at = T0 + timedelta(minutes=minutes)
    swing = SwingPoint(index - 1, at, SwingKind.HIGH, 109.0, index - 2, at, index - 2)
    return StructureBreak(direction, index, at, swing, is_bos, leg_index or index - 1, 107.5)


def long_setup(**kw) -> Setup:
    return Setup(zone(), LONG, **kw)


def react(setup, k=0, candle=(107.9, 109.2, 107.5, 108.6)):
    return setup.on_30m(*c30(k, *candle), DOJI)


def test_sweep_and_reaction_on_one_green_30m_candle():
    s = long_setup()
    assert react(s) and s.step is Step.BOS and s.reaction_open == T0


def test_sweep_then_reaction_on_a_later_candle():
    s = long_setup()
    assert not react(s, 0, (109.0, 109.2, 107.8, 107.9))  # wick in, red close inside
    assert s.step is Step.REACTION
    assert react(s, 1, (107.9, 108.6, 107.9, 108.5))  # green close above 108
    assert s.reaction_open == T0 + M30


def test_a_touch_is_no_sweep_and_no_sweep_means_no_reaction():
    s = long_setup()
    react(s, 0, (109.0, 109.2, 108.0, 108.6))  # low touches the top only
    assert s.step is Step.SWEEP


@pytest.mark.parametrize(
    "candle",
    [
        (108.9, 109.0, 107.5, 108.5),  # red close above the zone
        (108.5, 108.8, 107.5, 108.5),  # doji
        (107.2, 107.9, 107.1, 107.8),  # green but closes inside the zone
    ],
)
def test_only_a_green_close_above_the_zone_is_the_reaction(candle):
    s = long_setup()
    assert not react(s, 0, candle)
    assert s.step is Step.REACTION


def test_bos_must_close_during_the_reaction_candle_or_after():
    s = long_setup()
    react(s, 1)  # 30m candle 13:30-14:00
    s.on_breaks([brk(LONG, 5, 30)])  # closed 13:30: before the reaction candle
    assert s.step is Step.BOS
    s.on_breaks([brk(LONG, 7, 35)])  # closed 13:35, inside it
    assert s.step is Step.CONFLUENCE and s.bos.index == 7


def test_with_trend_break_counts_only_with_the_setting():
    s = long_setup()
    react(s)
    s.on_breaks([brk(LONG, 3, 15, is_bos=False), brk(SHORT, 4, 20)])
    assert s.step is Step.BOS
    s = long_setup(with_trend_bos=True)
    react(s)
    s.on_breaks([brk(LONG, 3, 15, is_bos=False)])
    assert s.step is Step.CONFLUENCE


def test_opposite_bos_after_the_bos_restarts_but_a_with_trend_break_does_not():
    s = long_setup()
    react(s)
    s.on_breaks([brk(LONG, 3, 15)])
    s.on_breaks([brk(SHORT, 6, 30, is_bos=False)])
    assert s.step is Step.CONFLUENCE
    s.on_breaks([brk(SHORT, 8, 40)])
    assert s.step is Step.SWEEP and s.bos is None


def fvg(created, direction=LONG, top=108.8, bottom=108.6) -> ZoneBox:
    return ZoneBox(ZoneKind.FVG, direction, top, bottom, created - 2, created, T0)


def test_confluence_must_form_in_the_bos_leg_or_later_and_confirm_after_the_bos():
    s = long_setup()
    react(s)
    s.on_breaks([brk(LONG, 6, 30, leg_index=4)])
    assert s.accepts(fvg(4), 7)
    assert s.accepts(fvg(9), 10)
    assert not s.accepts(fvg(3), 7)  # formed before the leg's low
    assert not s.accepts(fvg(4), 6)  # confirmed by the BOS candle itself
    assert not s.accepts(fvg(4, SHORT), 7)
    assert not long_setup().accepts(fvg(4), 7)  # no BOS yet


def test_after_an_entry_only_later_30m_closes_count():
    s = long_setup()
    s.reset(not_before=T0 + M30 + M5)  # entered at 13:35
    assert not react(s, 0) and s.step is Step.SWEEP  # closes 13:30: ignored
    assert react(s, 1)  # closes 14:00, after the entry


def test_a_flip_starts_the_short_at_the_bos_step():
    s = Setup(zone(), SHORT)
    candle, _ = c30(2, 107.5, 107.6, 106.0, 106.2)  # red close below the zone
    s.start_from_flip(candle)
    assert s.step is Step.BOS and s.reaction_open == candle.ts
    s.on_breaks([brk(SHORT, 14, 65)])
    assert s.step is Step.CONFLUENCE


def test_short_is_mirrored():
    s = Setup(zone(), SHORT)  # used as resistance from below: near edge = bottom 107
    assert react(s, 0, (106.5, 107.5, 106.0, 106.2))
    s.on_breaks([brk(SHORT, 3, 15)])
    assert s.accepts(fvg(3, SHORT, 106.8, 106.6), 4)


# --- wiring: the hand-built London / New York day ----------------------------------------


def run_tracker(ohlc, config=None):
    m5, m30, *_ = scenario.series(ohlc)
    replay = Replay(m5, [m30])
    tracker = SetupTracker(scenario.SYMBOL, config)
    signals = []
    for i in range(len(replay)):
        now = replay.close_time(i)
        signals += tracker.update(now, replay.view(i), replay.higher_view(i, Timeframe.M30))
    return signals


def test_scenario_gives_one_long_entry_at_the_fvg_confirmation():
    [sig] = run_tracker(LONDON + NY_SETUP)
    assert sig.direction is LONG and sig.index == ENTRY_INDEX and sig.close == 110.0
    assert sig.at == T0 + 8 * M5  # h closes 13:40
    assert sig.zone.side is SwingKind.LOW and (sig.zone.bottom, sig.zone.top) == (107.0, 108.0)
    assert sig.zone.formed_in.session is Session.LONDON
    assert sig.reaction_open == T0
    assert sig.bos.index == BOS_INDEX and sig.bos.is_bos
    assert (sig.bos.leg_index, sig.bos.leg_extreme) == (NY_FIRST + 2, 108.1)
    c = sig.confluence
    assert (c.kind, c.bottom, c.top, c.created_index) == (ZoneKind.FVG, 109.1, 109.5, NY_FIRST + 5)


def test_no_sweep_no_entry():
    ny = list(NY_SETUP)
    ny[0] = bar(109.5, 108.2, hi=109.6, lo=108.0)  # a touches 108, no wick into the zone
    ny[1] = bar(108.2, 108.6, lo=108.05, hi=108.7)
    assert run_tracker(LONDON + ny) == []


def test_fvgs_against_the_5m_trend_are_not_used():
    """The FVG forms before the 5m BOS (no 5m trend yet at its candle 3), is tapped and
    confirmed after the BOS: no entry. (FVGs only: h also taps the BOS move's EQ, 108.1 ->
    109.3, and the breaker of b, and i confirms them.)"""
    ny = [
        bar(108.3, 107.6, hi=108.4, lo=107.4),  # a: sweep (30m opens 108.3)
        *NY_SETUP[1:3],  # b, c: 5m swing high 108.8
        bar(108.2, 108.5, lo=108.1, hi=108.55),  # d
        bar(108.5, 108.7, lo=108.45, hi=108.75),  # e
        bar(108.7, 108.78, lo=108.6, hi=108.8),  # f: FVG 108.55-108.6, no trend yet
        bar(108.78, 109.2, lo=108.7, hi=109.3),  # g: bullish BOS
        bar(109.2, 108.9, hi=109.25, lo=108.58),  # h: taps the FVG
        bar(108.9, 109.1, lo=108.85, hi=109.15),  # i: confirms it
    ]
    fvg_only = SessionZoneSweepConfig(
        confluence_kinds=frozenset({ZoneKind.FVG}), use_equilibrium=False
    )
    assert run_tracker(LONDON + ny, fvg_only) == []
    no_breaker = SessionZoneSweepConfig(
        confluence_kinds=frozenset({ZoneKind.FVG, ZoneKind.ORDER_BLOCK, ZoneKind.BPR})
    )
    [eq] = run_tracker(LONDON + ny, no_breaker)
    assert eq.confluence.kind is ZoneKind.EQUILIBRIUM


def test_skip_tokyo_does_not_touch_a_new_york_setup():
    assert len(run_tracker(LONDON + NY_SETUP, SessionZoneSweepConfig(skip_tokyo=True))) == 1


def random_days(days: int, seed: int):
    """A few days of 5m random walk (weekdays, no gaps): enough zones and setups."""
    rng = random.Random(seed)
    price, out = 2000.0, []
    for i in range(days * 288):
        close = price + rng.gauss(0, 1.2) + 0.8 * math.sin(i / 40)
        hi, lo = (
            max(price, close) + abs(rng.gauss(0, 0.6)),
            min(price, close) - abs(rng.gauss(0, 0.6)),
        )
        out.append((price, hi, lo, close))
        price = close
    return out


def test_no_lookahead_signals_never_depend_on_later_candles():
    ohlc = random_days(4, seed=7)
    full = run_tracker(ohlc)
    assert len(full) >= 3  # the walk must actually produce setups
    for k in (300, 577, 900):
        part = run_tracker(ohlc[:k])
        assert part == [s for s in full if s.index < k]


def test_each_confluence_type_can_be_switched_off():
    """confluences.md › Confluence toggles: a type switched off never triggers an entry; the
    other types still do. Seeds 2 and 5 give FVG, OB, breaker and EQ entries (BPRs take the
    same path as OBs)."""
    defaults, covered = SessionZoneSweepConfig(), set()
    for seed in (2, 5):
        ohlc = random_days(6, seed=seed)
        kinds = {s.confluence.kind for s in run_tracker(ohlc)}
        covered |= kinds
        for kind in kinds:
            if kind is ZoneKind.EQUILIBRIUM:
                config = SessionZoneSweepConfig(use_equilibrium=False)
            else:
                config = SessionZoneSweepConfig(confluence_kinds=defaults.confluence_kinds - {kind})
            left = {s.confluence.kind for s in run_tracker(ohlc, config)}
            assert kind not in left and left, (seed, kind)
    assert covered >= {ZoneKind.FVG, ZoneKind.ORDER_BLOCK, ZoneKind.BREAKER, ZoneKind.EQUILIBRIUM}
