"""Stop loss (incl. SL size), take profit (reversal levels, 4H OB limit, TP1 / TP2), 1h
levels and the strategy's orders.
Spec: strategy-session-zones.md › Stop loss, › Take profit, › Backtest options."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
import scenario
from conftest import build_series
from scenario import LONDON, NY_SETUP, TO_TARGET

from backtester.core.models import Direction
from backtester.detectors.order_block import OrderBlockConfig
from backtester.detectors.swings import SwingKind, SwingPoint
from backtester.detectors.zone import ZoneBox, ZoneKind
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.setup import EntrySignal, StructureBreak
from backtester.strategy.session_zone_sweep.strategy import LAST_MINUTES_TAG, SessionZoneSweep
from backtester.strategy.session_zone_sweep.targets import (
    MIN_RR,
    OB,
    SWING,
    ZONE,
    Level,
    ObstacleTracker,
    Rejected,
    UnmitigatedOrderBlocks,
    stop_loss,
    take_profit,
    targets,
    zone_levels,
)
from backtester.strategy.session_zone_sweep.zones import Role

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
T = datetime(2026, 1, 5, 13, 0, tzinfo=UTC)
CFG = SessionZoneSweepConfig()


def signal(direction=LONG, top=101.0, bottom=100.0, leg_extreme=98.0, close=102.0):
    swing = SwingPoint(1, T, SwingKind.HIGH, 101.5, 1, T, 0)
    bos = StructureBreak(direction, 3, T, swing, True, 2, leg_extreme)
    fvg = ZoneBox(ZoneKind.FVG, direction, top, bottom, 3, 5, T)
    return EntrySignal(direction, None, fvg, bos, T, 7, T, close)


# --- stop loss ----------------------------------------------------------------------------


def test_sl_below_the_confluence_low():
    assert stop_loss(signal(), atr=1.0, config=CFG) == 100.0


def test_small_confluence_puts_the_sl_below_the_bos_leg_low():
    # height 1.0 < 0.5 x ATR 2.5 = 1.25
    assert stop_loss(signal(), atr=2.5, config=CFG) == 98.0
    assert stop_loss(signal(), atr=None, config=CFG) == 100.0  # no ATR yet: never small


def test_sl_buffer_and_short_mirrored():
    config = SessionZoneSweepConfig(sl_buffer_atr_mult=0.1)
    assert stop_loss(signal(), atr=1.0, config=config) == pytest.approx(99.9)
    short = signal(SHORT, top=101.0, bottom=100.0, leg_extreme=104.0, close=99.0)
    assert stop_loss(short, atr=1.0, config=config) == pytest.approx(101.1)
    assert stop_loss(short, atr=2.5, config=CFG) == 104.0


class Obs4h:
    """Stand-in for the 4H OBs: none, or one with its near edge at `edge`."""

    def __init__(self, edge=None):
        self.edge = edge

    def near_edges(self, direction, entry):
        return [] if self.edge is None else [self.edge]


def sized(config, atr=1.0, sig=None, limits=None):
    """targets() for the default signal: entry 102, SL 100 (2 x ATR 1.0), no levels."""
    obstacles = ObstacleTracker(0.065)
    return targets(sig or signal(), atr, [], obstacles, limits or Obs4h(), config)


def test_small_sl_is_widened_to_min_sl_atr_mult():
    found = sized(SessionZoneSweepConfig(min_sl_atr_mult=3.0))
    assert found.stop_loss == pytest.approx(99.0) and found.sl_widened
    found = sized(SessionZoneSweepConfig(min_sl_atr_mult=1.5))  # 2 x ATR is wide enough
    assert found.stop_loss == 100.0 and not found.sl_widened
    short = signal(SHORT, top=101.0, bottom=100.0, leg_extreme=104.0, close=99.5)  # SL 101
    found = sized(SessionZoneSweepConfig(min_sl_atr_mult=3.0), sig=short)
    assert found.stop_loss == pytest.approx(102.5)
    no_small = SessionZoneSweepConfig(small_confluence_atr_mult=0.0)
    assert sized(no_small, atr=10.0).stop_loss == 100.0  # off by default: 0.2 x ATR stays


def test_too_wide_sl_means_no_trade():
    found = sized(SessionZoneSweepConfig(max_sl_atr_mult=1.5))
    assert isinstance(found, Rejected) and "wider than 1.5" in found.reason
    assert sized(SessionZoneSweepConfig(max_sl_atr_mult=2.0)).stop_loss == 100.0
    assert sized(CFG, atr=0.1).stop_loss == 100.0  # off by default: 20 x ATR is taken


def test_targets_uses_the_4h_ob_as_limit():
    # entry 102, 1R = 2: a 4H OB at 104 is 1R away -> no trade; at 105 (1.5R) -> TP 104.4
    found = sized(CFG, limits=Obs4h(104.0))
    assert isinstance(found, Rejected) and "4H OB" in found.reason
    found = sized(CFG, limits=Obs4h(105.0))
    assert (found.take_profit, found.take_profit_2, found.limit) == (104.4, None, 105.0)


# --- take profit (entry 100, SL 99: 1R = 1.0) --------------------------------------------


def lv(*prices, source=SWING):
    return [Level(p, source) for p in prices]


def tp(levels=(), config=CFG, limit=None, direction=LONG, entry=100.0, sl=99.0, atr=None):
    """(TP1, TP2), or Rejected."""
    found = take_profit(direction, entry, sl, list(levels), limit, atr, config)
    return found if isinstance(found, Rejected) else found[:2]


def test_tp1_is_the_first_level_at_or_beyond_min_rr():
    found = take_profit(LONG, 100.0, 99.0, lv(102.5, source=ZONE), None, None, CFG)
    assert found == (102.5, None, ZONE, None)
    assert tp(lv(100.5, 101.6)) == (101.6, None)  # 100.5 is below 1.2R: passed
    assert tp(lv(101.2)) == (101.2, None)  # exactly 1.2R counts


def test_no_level_in_reach_means_tp_at_min_rr():
    assert take_profit(LONG, 100.0, 99.0, [], None, None, CFG) == (101.2, None, MIN_RR, None)
    assert tp(lv(100.5, 103.5)) == (101.2, None)  # one below 1.2R, one beyond the 3R cap


def test_tp2_is_the_next_level_up_to_the_cap():
    found = take_profit(LONG, 100.0, 99.0, [*lv(101.6), Level(102.0, OB)], None, None, CFG)
    assert found == (101.6, 102.0, SWING, OB)
    assert tp(lv(101.6, 102.0, 102.5)) == (101.6, 102.0)
    assert tp(lv(101.6, 103.0)) == (101.6, 103.0)  # 3R exactly is in reach
    assert tp(lv(101.6, 103.5)) == (101.6, None)  # beyond the cap: all at TP1
    assert tp(lv(101.6, 102.0), SessionZoneSweepConfig(tp_cap_r=1.8)) == (101.6, None)


def test_tp2_may_pass_obstacles_passable_levels():
    levels = lv(101.6, 102.0, 102.5, 102.9)
    assert tp(levels, SessionZoneSweepConfig(obstacles_passable=1)) == (101.6, 102.5)
    assert tp(levels, SessionZoneSweepConfig(obstacles_passable=2)) == (101.6, 102.9)
    # fewer levels before the cap than it may pass: the furthest one in reach
    one = SessionZoneSweepConfig(obstacles_passable=1)
    assert tp(lv(101.6, 102.0, 103.5), one) == (101.6, 102.0)


def test_levels_closer_than_0_2r_count_as_one():
    # 101.5 / 101.65 / 101.8 chain into one level (its nearest price), 102.5 is the next
    assert tp(lv(101.5, 101.65, 101.8, 102.5)) == (101.5, 102.5)
    assert tp(lv(101.5, 101.7)) == (101.5, 101.7)  # 0.2R apart exactly: two levels
    # a cluster starting below 1.2R is passed as a whole
    assert tp(lv(101.1, 101.25, 102.5)) == (102.5, None)


def test_4h_ob_is_a_hard_limit():
    assert tp(lv(101.5, 102.5), limit=102.0) == (101.5, None)  # 102.5 beyond the 4H OB
    assert tp(lv(102.5), limit=102.0) == (101.2, None)  # nothing in reach: min R
    assert tp(lv(101.5, 102.0), limit=102.0) == (101.5, 102.0)  # at the OB's edge
    found = tp(lv(101.5), limit=101.1)
    assert isinstance(found, Rejected) and "4H OB" in found.reason
    assert tp(limit=101.2) == (101.2, None)


def test_tp_buffer_below_levels_and_the_4h_ob():
    config = SessionZoneSweepConfig(tp_buffer_atr_mult=0.1)  # 0.2 with ATR 2
    assert tp(lv(101.6, 102.5), config, atr=2.0) == (pytest.approx(101.4), pytest.approx(102.3))
    assert tp(lv(101.6, 102.5), config, limit=102.0, atr=2.0) == (pytest.approx(101.4), None)
    assert isinstance(tp(config=config, limit=101.3, atr=2.0), Rejected)  # 101.1 < 1.2R


def test_short_tp_is_mirrored():
    assert tp(lv(98.5, 97.5), direction=SHORT, entry=100.0, sl=101.0) == (98.5, 97.5)
    assert tp(direction=SHORT, entry=100.0, sl=101.0) == (98.8, None)
    assert isinstance(tp(limit=99.0, direction=SHORT, entry=100.0, sl=101.0), Rejected)


def test_zone_levels_are_the_near_edges_of_opposite_role_zones_beyond_the_entry():
    zones = [
        (Role.RESISTANCE, 106.0, 105.0),
        (Role.RESISTANCE, 104.0, 103.0),
        (Role.SUPPORT, 99.0, 98.0),
        (Role.RESISTANCE, 100.5, 99.5),  # entry inside: not a level
        (None, 103.0, 102.0),  # role unknown
    ]
    assert zone_levels(LONG, 100.0, zones) == lv(105.0, 103.0, source=ZONE)
    assert zone_levels(SHORT, 100.0, zones) == lv(99.0, source=ZONE)
    assert zone_levels(LONG, 107.0, zones) == []


# --- 1h levels and 4H OBs -----------------------------------------------------------------

NO_FILTER = OrderBlockConfig(strong_move_filter=False)


def feed(tracker, ohlc):
    s = build_series(ohlc)
    for i in range(len(s)):
        tracker.update(s.view(i))
    return tracker


def obstacles_after(ohlc, config=CFG):
    return feed(ObstacleTracker(0.065, config), ohlc)


def test_untouched_swing_high_is_a_level_until_a_wick_reaches_it():
    up_down = [(100.0, 105.0, 99.5, 104.0), (104.0, 104.5, 101.0, 102.0)]  # high 105
    assert obstacles_after(up_down).levels(LONG, 102.0) == lv(105.0)
    assert obstacles_after(up_down).levels(SHORT, 102.0) == []
    touched = [*up_down, (102.0, 105.0, 101.5, 103.0)]
    assert obstacles_after(touched).levels(LONG, 102.0) == []


def test_1h_fvgs_are_no_levels():
    gap_down = [
        (110.0, 110.5, 108.0, 108.5),  # 1: low 108
        (108.5, 108.6, 104.0, 104.5),  # 2
        (104.5, 106.0, 103.5, 105.5),  # 3: high 106 < 108: bearish FVG 106-108
    ]
    assert obstacles_after(gap_down).levels(LONG, 105.5) == []


# A bearish OB: green leg (candles 1, 2) into the swing high 108.5, bearish BOS by candle 4
# closing below the swing low 102.5. Leg range 102.9-108.5, reached at its bottom 102.9.
BEARISH_OB = [
    (105.0, 105.1, 102.5, 103.0),  # 0 red
    (103.0, 104.1, 102.9, 104.0),  # 1 green: swing low 102.5
    (104.0, 108.5, 103.9, 108.0),  # 2 green
    (108.0, 108.1, 105.9, 106.0),  # 3 red: swing high 108.5
    (106.0, 106.1, 101.9, 102.0),  # 4 red: closes below 102.5 -> bearish BOS
]


def test_unmitigated_bearish_1h_ob_is_a_level_until_tapped():
    tracker = obstacles_after(BEARISH_OB, NO_FILTER)
    assert tracker.levels(LONG, 102.0) == [Level(102.9, OB), Level(108.5, SWING)]
    tapped = obstacles_after([*BEARISH_OB, (102.0, 103.0, 101.5, 102.2)], NO_FILTER)
    assert tapped.levels(LONG, 102.2) == [Level(108.5, SWING)]  # 103 > 102.9: tapped


def test_4h_obs_near_edges_and_no_lookahead():
    obs = feed(UnmitigatedOrderBlocks(0.065, NO_FILTER), BEARISH_OB)
    assert obs.near_edges(LONG, 102.0) == [102.9] and obs.near_edges(SHORT, 102.0) == []
    before = feed(UnmitigatedOrderBlocks(0.065, NO_FILTER), BEARISH_OB[:4])
    assert before.near_edges(LONG, 102.0) == []  # exists only from the BOS candle


# --- the strategy's orders on the hand-built day -----------------------------------------

NO_COSTS = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))


def run(ohlc, config=None, engine=NO_COSTS, extra_levels=()):
    strategy = SessionZoneSweep(scenario.SYMBOL, config)
    if extra_levels:
        levels = strategy.obstacles.levels
        strategy.obstacles.levels = lambda d, e: [*levels(d, e), *extra_levels]
    trades = run_backtest(strategy, scenario.series(ohlc), engine)
    return strategy, trades


def test_scenario_order_and_trade():
    strategy, [trade] = run(LONDON + NY_SETUP + TO_TARGET)
    [decision] = strategy.decisions
    order = decision.order
    # SL at the FVG's bottom (0.4 high, not small: 5m ATR ~0.35), 1R = 0.9; the London
    # high zone (bottom 113) is 3.33R away, beyond the 3R cap: no level in reach -> 1.2R
    assert order.direction is LONG and order.entry == 110.0
    assert order.stop_loss == 109.1
    assert order.take_profit == pytest.approx(111.08) and order.take_profit_2 is None
    assert decision.targets.tp1_from == MIN_RR and decision.rejected == ""
    assert order.tags == frozenset()
    assert trade.exit_reason is ExitReason.TAKE_PROFIT and trade.r_gross == pytest.approx(1.2)


def test_session_zone_as_tp_and_min_rr():
    strategy, _ = run(LONDON + NY_SETUP, SessionZoneSweepConfig(tp_cap_r=4.0))
    targets_ = strategy.decisions[0].targets
    assert (targets_.take_profit, targets_.tp1_from) == (113.0, ZONE)
    config = SessionZoneSweepConfig(tp_cap_r=4.0, min_rr=3.5)  # zone at 3.33R: passed
    strategy, _ = run(LONDON + NY_SETUP, config)
    assert strategy.decisions[0].order.take_profit == pytest.approx(110.0 + 3.5 * 0.9)


def test_two_tps_order_and_weighted_result():
    # an extra 1h level at 111.5 (1.67R): TP1 there, TP2 at the London zone (113, 3.33R)
    # once the cap allows it; the run to 112.8 hits TP1 and leaves the rest open
    config = SessionZoneSweepConfig(tp_cap_r=4.0)
    ohlc = LONDON + NY_SETUP + TO_TARGET
    # unrounded to the tick (round_to_tick is on by default): the slippage stays exact here
    no_ticks = EngineConfig(
        costs=CostConfig(spread_enabled=False, commission_enabled=False, round_to_tick=False)
    )
    strategy, [trade] = run(ohlc, config, no_ticks, extra_levels=[Level(111.5, SWING)])
    order = strategy.decisions[0].order
    assert (order.take_profit, order.take_profit_2) == (111.5, 113.0)
    assert order.tp1_share == 0.5 and order.break_even_after_tp1
    assert trade.exit_reason is ExitReason.END_OF_DATA
    assert trade.r_gross == pytest.approx(0.5 * 1.5 / 0.9 + 0.5 * 2.8 / 0.9)
    # Spread/commission off; entry and stop still pay scaled slippage (B4).
    assert trade.break_even_stop == pytest.approx(110 + 2 * 0.1 * 110 / 4342.74)
    share = SessionZoneSweepConfig(tp_cap_r=4.0, tp1_share=0.3, break_even_after_tp1=False)
    strategy, _ = run(ohlc, share, extra_levels=[Level(111.5, SWING)])
    order = strategy.decisions[0].order
    assert order.tp1_share == 0.3 and not order.break_even_after_tp1


def test_rejected_trades_keep_their_reason():
    strategy, trades = run(LONDON + NY_SETUP, SessionZoneSweepConfig(max_sl_atr_mult=1.0))
    [decision] = strategy.decisions
    assert trades == [] and decision.order is None and "wider than" in decision.rejected


def test_last_minutes_tag_and_exclusion():
    # 13:40 is 10h20 before Tokyo's start (00:00 UTC): tag it with a 12h window
    tagged = SessionZoneSweepConfig(tag_last_minutes_before_next_session=12 * 60)
    strategy, [trade] = run(LONDON + NY_SETUP, tagged)
    assert trade.tags == frozenset({LAST_MINUTES_TAG})
    excluded = SessionZoneSweepConfig(
        tag_last_minutes_before_next_session=12 * 60, include_last_minutes_trades=False
    )
    strategy, trades = run(LONDON + NY_SETUP, excluded)
    assert trades == [] and strategy.decisions[0].order is None


def test_strategy_rejects_another_symbol():
    with pytest.raises(ValueError, match="GBPUSD candles for a XAUUSD strategy"):
        run_backtest(SessionZoneSweep("XAUUSD"), scenario.series(LONDON, symbol="GBPUSD"), NO_COSTS)


def test_no_lookahead_orders_never_depend_on_later_candles():
    from test_setup import random_days

    ohlc = random_days(4, seed=7)
    full, full_trades = run(ohlc)
    assert full_trades
    for k in (300, 577, 900):
        part, part_trades = run(ohlc[:k])
        cut = scenario.START + k * scenario.M5
        assert part.decisions == [d for d in full.decisions if d.signal.at <= cut]
        finished = [t for t in part_trades if t.exit_reason is not ExitReason.END_OF_DATA]
        assert finished == [t for t in full_trades if t.exit_time <= cut]
