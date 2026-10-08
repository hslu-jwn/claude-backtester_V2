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
from scenario import LONDON, NY_FIRST, NY_SETUP, bar, doji
from test_setup import run_tracker

from backtester.core.models import Direction
from backtester.detectors.swings import SwingKind, SwingPoint
from backtester.detectors.zone import ZoneKind
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.setup import StructureBreak
from backtester.strategy.session_zone_sweep.signals import equilibrium_zone
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
    swing = SwingPoint(1, T, SwingKind.HIGH, 101.0, 1, T, 0)
    long_break = StructureBreak(LONG, 3, T, swing, True, 2, 98.0)
    end = SwingPoint(6, T, SwingKind.HIGH, 104.0, 5, T, 5)
    z = equilibrium_zone(long_break, end)
    assert (z.direction, z.bottom, z.top, z.near, z.far) == (LONG, 98.0, 101.0, 101.0, 98.0)
    assert (z.start_index, z.created_index) == (2, 6)
    short_break = StructureBreak(SHORT, 3, T, swing, True, 2, 104.0)
    low = SwingPoint(6, T, SwingKind.LOW, 98.0, 5, T, 5)
    z = equilibrium_zone(short_break, low)
    assert (z.direction, z.bottom, z.top, z.near, z.far) == (SHORT, 101.0, 104.0, 101.0, 104.0)


def test_no_lookahead_equilibrium_exists_only_from_the_move_end():
    """Cut the day before f, before g and before h: no signal before h; and the full run's
    signal is unchanged by candles appended after it."""
    ohlc = LONDON + EQ_SETUP
    for k in (NY_FIRST + 5, NY_FIRST + 6, NY_FIRST + 7):
        assert run_tracker(ohlc[:k]) == []
    full = run_tracker(ohlc)
    assert run_tracker(ohlc + [doji(109.8)] * 20) == full
