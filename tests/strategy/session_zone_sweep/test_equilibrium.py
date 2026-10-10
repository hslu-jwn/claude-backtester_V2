"""Equilibrium of the BOS move as strategy 1's entry confluence.
Spec: strategy-session-zones.md › Entry sequence step 4 (equilibrium entry), › Stop loss
(EQ), confluences.md › Equilibrium (reworked 2026-10-10).

The hand-built London day of scenario.py, then a New York setup without FVG:
  a..d  as in scenario.py: sweep, 5m swing high 108.8 (c), BOS leg low 108.1 (c), BOS (d,
        high 109.1) -> leg 108.1 - 109.1, fixed at d: equilibrium 108.1-108.6 exists from d
        (d's own wick below 108.6 is no tap: it is the BOS candle)
  e 13:20 green 109.0 -> 110.0, low 108.7     (no FVG: c's high is 108.8)
  f 13:25 red   110.0 -> 109.6, low 109.0     (30m 13:00 closes green at 109.6: reaction)
  g 13:30 red   109.6 -> 108.9, low 108.5     taps it (wick below 108.6)
  h 13:35 green 108.9 -> 109.3, low 108.8     green close above 108.6: ENTRY at 109.3
SL: deepest wick into the EQ before the entry 108.5 (g), distance to the leg low 0.4 ->
SL 108.1 - 10% x 0.4 = 108.06; EQ-only toggle: 108.5 - 0.04 = 108.46.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
import scenario
from conftest import build_candles
from scenario import LONDON, NY_FIRST, NY_SETUP, bar, doji
from test_setup import run_tracker

from backtester.core.models import Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.detectors.equilibrium import EquilibriumConfig
from backtester.detectors.zone import ZoneKind
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.signals import SetupTracker
from backtester.strategy.session_zone_sweep.strategy import SessionZoneSweep

LONG = Direction.BULLISH

E = bar(109.0, 110.0, lo=108.7, hi=110.1)
F = bar(110.0, 109.6, hi=110.2, lo=109.0)
G = bar(109.6, 108.9, hi=109.7, lo=108.5)
H = bar(108.9, 109.3, lo=108.8, hi=109.4)
EQ_SETUP = [*NY_SETUP[:4], E, F, G, H]
EQ_ENTRY = NY_FIRST + 7


def test_entry_at_the_equilibrium_confirmation():
    [sig] = run_tracker(LONDON + EQ_SETUP)
    assert sig.direction is LONG and sig.index == EQ_ENTRY and sig.close == 109.3
    c = sig.confluence
    assert c.kind is ZoneKind.EQUILIBRIUM
    assert (c.bottom, c.top) == (108.1, pytest.approx(108.6))  # leg low, 50% of 108.1-109.1
    assert c.start_index == NY_FIRST + 2  # the BOS leg's low (c)
    assert c.created_index == NY_FIRST + 3  # the BOS candle (d)
    assert sig.eq_deepest == 108.5  # g's wick


def run_strategy(config=None):
    strategy = SessionZoneSweep(scenario.SYMBOL, config)
    no_costs = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))
    run_backtest(strategy, scenario.series(LONDON + EQ_SETUP), no_costs)
    [decision] = strategy.decisions
    return decision


def test_strategy_order_sl_beyond_the_leg_low_with_the_eq_buffer():
    decision = run_strategy()
    order = decision.order
    assert order.entry == 109.3 and order.stop_loss == pytest.approx(108.06)
    assert "equilibrium" in order.reason
    assert decision.targets.sl_at_bos_leg is False


def test_eq_only_toggle_puts_the_sl_beyond_the_deepest_wick():
    eq = EquilibriumConfig(sl_at_deepest_wick=True)
    order = run_strategy(SessionZoneSweepConfig(equilibrium=eq)).order
    assert order.stop_loss == pytest.approx(108.46)


def test_the_atr_buffer_and_small_confluence_rule_do_not_apply_to_the_eq():
    config = SessionZoneSweepConfig(sl_buffer_atr_mult=5.0, small_confluence_atr_mult=100.0)
    decision = run_strategy(config)
    assert decision.order.stop_loss == pytest.approx(108.06)
    assert decision.targets.sl_at_bos_leg is False


def test_use_equilibrium_off_means_no_entry():
    assert run_tracker(LONDON + EQ_SETUP, SessionZoneSweepConfig(use_equilibrium=False)) == []


def test_no_tap_or_red_close_does_not_confirm():
    # no wick below 108.6 at all: no entry
    no_tap = [*NY_SETUP[:4], E, F, bar(109.6, 109.5, hi=109.7, lo=109.3)]
    no_tap.append(bar(109.5, 109.8, lo=109.4, hi=109.9))
    assert run_tracker(LONDON + no_tap) == []
    # g taps and closes above 108.6 but red; h red again: only a green close confirms
    red = [*NY_SETUP[:4], E, F, G, bar(108.9, 108.8, hi=109.0, lo=108.7)]
    assert run_tracker(LONDON + red) == []


def test_close_inside_the_discount_half_and_wick_below_the_low_keep_it_alive():
    # g wicks below the leg low (108.0 < 108.1) and closes inside the discount half: only
    # a close below the low invalidates
    deep = [*NY_SETUP[:4], E, F, bar(109.6, 108.3, hi=109.7, lo=108.0)]
    deep.append(bar(108.3, 108.9, lo=108.2, hi=109.0))
    [sig] = run_tracker(LONDON + deep)
    assert sig.confluence.kind is ZoneKind.EQUILIBRIUM and sig.close == 108.9
    assert sig.eq_deepest == 108.0


def test_close_below_the_leg_low_invalidates_it():
    # g closes below 108.1 (also a bearish BOS that cancels the setup); h's green close
    # back above 108.6 is no entry
    broken = [*NY_SETUP[:4], E, F, bar(109.6, 108.0, hi=109.7, lo=107.9)]
    broken.append(bar(108.0, 109.3, lo=107.95, hi=109.4))
    assert run_tracker(LONDON + broken) == []


# GBPUSD 2026-09-04 (Friday) 20:00 - 20:55, then Sunday 2026-09-06 21:00 - 21:25 after the
# weekend gap (real bid candles, rebuilt by hand). Bullish BOS at 20:55 over the 20:40
# swing high 1.35155; BOS leg low 1.35137 (20:50); break candle high 1.35178. The EQ is
# 1.35137 - 1.351575 from the BOS candle on (the old rule waited for the next swing high,
# which after the gap was below the leg low). The 21:20 close is below the leg low.
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
    (1.35115, 1.35123, 1.35105, 1.35106),  # 21:15
    (1.35118, 1.35121, 1.35101, 1.35117),  # 21:20 close below 1.35137
    (1.35118, 1.35134, 1.35106, 1.35118),
]
GBPUSD_BOS = 11


def test_eq_exists_from_the_bos_candle_gbpusd_weekend_gap():
    fri = build_candles(GBPUSD_GAP[:12], start=GBPUSD_FRI)
    sun = build_candles(GBPUSD_GAP[12:], start=GBPUSD_SUN)
    series = CandleSeries("GBPUSD", Timeframe.M5, fri + sun)
    tracker = SetupTracker("GBPUSD")
    for i in range(GBPUSD_BOS + 1):
        view = series.view(i)
        tracker.update(view.current.ts + Timeframe.M5.duration, view, None)
    z = tracker._equilibrium[(GBPUSD_BOS, LONG)]
    assert z.kind is ZoneKind.EQUILIBRIUM and z.direction is LONG
    assert (z.bottom, z.top) == (1.35137, pytest.approx((1.35137 + 1.35178) / 2))
    assert (z.start_index, z.created_index) == (10, GBPUSD_BOS)


def test_no_lookahead_equilibrium_signal_only_at_its_confirmation():
    """Cut the day before d, before g and before h: no signal; and the full run's signal is
    unchanged by candles appended after it."""
    ohlc = LONDON + EQ_SETUP
    for k in (NY_FIRST + 3, NY_FIRST + 6, NY_FIRST + 7):
        assert run_tracker(ohlc[:k]) == []
    full = run_tracker(ohlc)
    assert run_tracker(ohlc + [doji(109.3)] * 20) == full
