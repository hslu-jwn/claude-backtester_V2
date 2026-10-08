"""Equilibrium of the BOS move as strategy 1's entry confluence.
Spec: strategy-session-zones.md › Entry sequence step 4 (equilibrium entry),
confluences.md › Equilibrium.

The hand-built London day of scenario.py, then a New York setup without FVG:
  a..d  as in scenario.py: sweep, 5m swing high 108.8 (c), BOS leg low 108.1 (c), BOS (d)
  e 13:20 green 109.0 -> 110.0, high 110.1
  f 13:25 red   110.0 -> 109.6, high 110.2, low 109.0  5m swing high 110.2: the move ends
        -> leg 108.1 - 110.2, 0.5 level 109.15: equilibrium 108.1-109.15 exists from f
        (f's own wick below 109.15 is no tap: it confirms the zone's existence)
        (f's low 109.0 < d's high 109.1: no FVG; 30m 13:00 closes green at 109.6: reaction)
  g 13:30 red   109.6 -> 109.3, low 109.0               taps it (wick below 109.15)
  h 13:35 green 109.3 -> 109.8, low 109.2               green close above 109.15: ENTRY
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
import scenario
from conftest import build_candles, build_series
from scenario import LONDON, NY_FIRST, NY_SETUP, bar, doji
from test_setup import run_tracker

from backtester.core.models import Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.detectors.swings import SwingKind, SwingPoint
from backtester.detectors.zone import ZoneKind
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.setup import StructureBreak
from backtester.strategy.session_zone_sweep.signals import SetupTracker, equilibrium_zone
from backtester.strategy.session_zone_sweep.strategy import SessionZoneSweep

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
T = datetime(2026, 1, 5, 13, 0, tzinfo=UTC)

E = bar(109.0, 110.0, lo=108.9, hi=110.1)
F = bar(110.0, 109.6, hi=110.2, lo=109.0)
G = bar(109.6, 109.3, hi=109.7, lo=109.0)
H = bar(109.3, 109.8, lo=109.2, hi=109.9)
EQ_SETUP = [*NY_SETUP[:4], E, F, G, H]
EQ_ENTRY = NY_FIRST + 7


def test_entry_at_the_equilibrium_confirmation():
    [sig] = run_tracker(LONDON + EQ_SETUP)
    assert sig.direction is LONG and sig.index == EQ_ENTRY and sig.close == 109.8
    c = sig.confluence
    assert c.kind is ZoneKind.EQUILIBRIUM
    assert (c.bottom, c.top) == (108.1, pytest.approx(109.15))
    assert c.start_index == NY_FIRST + 2  # the BOS leg's low (c)
    assert c.created_index == NY_FIRST + 5  # f confirmed the move's end swing high


def test_strategy_order_sl_below_the_leg_low():
    strategy = SessionZoneSweep(scenario.SYMBOL)
    no_costs = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))
    run_backtest(strategy, scenario.series(LONDON + EQ_SETUP), no_costs)
    [decision] = strategy.decisions
    order = decision.order
    assert order.entry == 109.8 and order.stop_loss == 108.1  # leg low, 1R = 1.7
    assert "equilibrium" in order.reason


def test_use_equilibrium_off_means_no_entry():
    assert run_tracker(LONDON + EQ_SETUP, SessionZoneSweepConfig(use_equilibrium=False)) == []


def test_red_close_or_no_tap_does_not_confirm():
    # g closes back above 109.15 but red, h never taps: only a green close counts and
    # only after a tap
    no_tap = [*NY_SETUP[:4], E, F, bar(109.6, 109.5, hi=109.7, lo=109.3), H]
    no_tap[-1] = bar(109.5, 109.8, lo=109.4, hi=109.9)
    assert run_tracker(LONDON + no_tap) == []


def test_close_inside_the_discount_half_and_wick_below_the_low_keep_it_alive():
    # g wicks below the leg low (108.0 < 108.1) and closes inside the discount half: the
    # rule invalidates only on a close below the low (confirmed by the user)
    deep = [*NY_SETUP[:4], E, F, bar(109.6, 108.9, hi=109.7, lo=108.0), H]
    deep[-1] = bar(108.9, 109.5, lo=108.8, hi=109.6)
    [sig] = run_tracker(LONDON + deep)
    assert sig.confluence.kind is ZoneKind.EQUILIBRIUM and sig.close == 109.5


def test_close_below_the_leg_low_invalidates_it():
    # g closes below 108.1 (also a bearish BOS that cancels the setup); h's green close
    # back above 109.15 is no entry
    broken = [*NY_SETUP[:4], E, F, bar(109.6, 108.0, hi=109.7, lo=107.9), H]
    broken[-1] = bar(108.0, 109.3, lo=107.95, hi=109.4)
    assert run_tracker(LONDON + broken) == []


def test_equilibrium_zone_geometry_and_short_mirrored():
    # leg extreme at candle 2, the move's high / low (104 / 98) at candle 4, end swing
    # (104 / 98) confirmed by candle 6
    swing = SwingPoint(1, T, SwingKind.HIGH, 101.0, 1, T, 0)
    long_break = StructureBreak(LONG, 3, T, swing, True, 2, 98.0)
    ohlc = [(99, 100, 99, 100), (100, 101, 99, 100), (100, 100, 98, 99), (99, 102, 99, 102),
            (102, 104, 101, 103), (103, 103.5, 102, 102), (102, 102.5, 101, 101)]  # fmt: skip
    up = build_series(ohlc)
    end = SwingPoint(6, T, SwingKind.HIGH, 104.0, 4, T, 4)
    z = equilibrium_zone(up.view(6), long_break, end)
    assert (z.direction, z.bottom, z.top, z.near, z.far) == (LONG, 98.0, 101.0, 101.0, 98.0)
    assert (z.start_index, z.created_index) == (2, 6)
    short_break = StructureBreak(SHORT, 3, T, swing, True, 2, 104.0)
    down = build_series([(202 - o, 202 - lo, 202 - h, 202 - c) for o, h, lo, c in ohlc])
    low = SwingPoint(6, T, SwingKind.LOW, 98.0, 4, T, 4)
    z = equilibrium_zone(down.view(6), short_break, low)
    assert (z.direction, z.bottom, z.top, z.near, z.far) == (SHORT, 101.0, 104.0, 101.0, 104.0)


# GBPUSD 2026-09-04 (Friday) 20:00 - 20:55, then Sunday 2026-09-06 21:00 - 21:25 after the
# weekend gap (real bid candles, rebuilt by hand). Bullish BOS at 20:55 over the 20:40
# swing high 1.35155; BOS leg low 1.35137 (20:50); break candle high 1.35178. After the gap
# down, the first swing high confirmed after the break is 1.35123 (green 21:05, doji, red 21:15):
# below the leg low. The move's high is the break candle's 1.35178, so the equilibrium is
# 1.35137 - 1.351575 from 21:15 (this crashed before: the leg was upside down). The next
# close (21:20) is below the leg low and invalidates it.
GBPUSD_FRI = datetime(2026, 9, 4, 20, 0, tzinfo=UTC)
GBPUSD_SUN = datetime(2026, 9, 6, 21, 0, tzinfo=UTC)
GBPUSD_GAP = [
    (1.35187, 1.35194, 1.35174, 1.35183),  # 20:00
    (1.35183, 1.35183, 1.35150, 1.35152),
    (1.35153, 1.35155, 1.35145, 1.35155),
    (1.35154, 1.35157, 1.35154, 1.35156),
    (1.35160, 1.35164, 1.35154, 1.35159),
    (1.35161, 1.35179, 1.35157, 1.35170),  # 20:25
    (1.35169, 1.35171, 1.35149, 1.35151),
    (1.35150, 1.35152, 1.35145, 1.35150),
    (1.35151, 1.35155, 1.35148, 1.35152),  # 20:40 swing high 1.35155
    (1.35152, 1.35154, 1.35138, 1.35144),
    (1.35145, 1.35152, 1.35137, 1.35148),  # 20:50 BOS leg low 1.35137
    (1.35146, 1.35178, 1.35138, 1.35158),  # 20:55 bullish BOS, high 1.35178
    (1.35099, 1.35104, 1.35099, 1.35104),  # Sunday 21:00
    (1.35104, 1.35115, 1.35104, 1.35115),
    (1.35115, 1.35115, 1.35115, 1.35115),
    (1.35115, 1.35123, 1.35105, 1.35106),  # 21:15 swing high 1.35123, confirmed
    (1.35118, 1.35121, 1.35101, 1.35117),
    (1.35118, 1.35134, 1.35106, 1.35118),
]
GBPUSD_BOS, GBPUSD_END = 11, 15


def test_move_high_is_the_highest_wick_not_the_end_swing_gbpusd_weekend_gap():
    fri = build_candles(GBPUSD_GAP[:12], start=GBPUSD_FRI)
    sun = build_candles(GBPUSD_GAP[12:], start=GBPUSD_SUN)
    series = CandleSeries("GBPUSD", Timeframe.M5, fri + sun)
    tracker = SetupTracker("GBPUSD")
    for i in range(GBPUSD_END + 1):
        view = series.view(i)
        tracker.update(view.current.ts + Timeframe.M5.duration, view, None)
    assert [s.price for s in tracker.structure.new_swings] == [1.35123]
    z = tracker._equilibrium[(GBPUSD_BOS, LONG)]
    assert z.kind is ZoneKind.EQUILIBRIUM and z.direction is LONG
    assert (z.bottom, z.top) == (1.35137, pytest.approx((1.35137 + 1.35178) / 2))
    assert (z.start_index, z.created_index) == (10, GBPUSD_END)


def test_no_lookahead_equilibrium_exists_only_from_the_move_end():
    """Cut the day before f, before g and before h: no signal before h; and the full run's
    signal is unchanged by candles appended after it."""
    ohlc = LONDON + EQ_SETUP
    for k in (NY_FIRST + 5, NY_FIRST + 6, NY_FIRST + 7):
        assert run_tracker(ohlc[:k]) == []
    full = run_tracker(ohlc)
    assert run_tracker(ohlc + [doji(109.8)] * 20) == full
