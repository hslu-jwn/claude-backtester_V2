"""Stop loss, take profit, 1h obstacles and the strategy's orders.
Spec: strategy-session-zones.md › Stop loss, › Take profit, › Backtest options."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
import scenario
from conftest import build_series
from scenario import LONDON, NY_SETUP, TO_TARGET

from backtester.core.models import Direction
from backtester.detectors.swings import SwingKind, SwingPoint
from backtester.detectors.zone import ZoneBox, ZoneKind
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.session_zone_sweep.setup import EntrySignal, StructureBreak
from backtester.strategy.session_zone_sweep.strategy import LAST_MINUTES_TAG, SessionZoneSweep
from backtester.strategy.session_zone_sweep.targets import (
    ObstacleTracker,
    stop_loss,
    take_profit,
    target_zone_level,
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


# --- take profit (entry 100, SL 99: 1R = 1.0) --------------------------------------------


def tp(zone_level=None, obstacles=(), config=CFG, direction=LONG, entry=100.0, sl=99.0):
    return take_profit(direction, entry, sl, zone_level, list(obstacles), None, config)


def test_tp_at_the_resistance_zone_bottom_capped_at_3r():
    assert tp(102.5) == (102.5, "zone")
    assert tp(105.0) == (103.0, "zone_cap")


def test_price_above_the_zone_uses_a_1h_level_between_1_2_and_2r():
    assert tp(None, [100.5, 101.6, 101.9]) is None  # 100.5 is an obstacle below 1.2R
    passable = SessionZoneSweepConfig(obstacles_passable=1)
    assert tp(None, [100.5, 101.6, 101.9], passable) == (101.6, "fallback_level")
    assert tp(None, [102.5]) == (102.0, "fallback_max")  # no level in range: 2R


def test_tp_sits_below_the_first_obstacle_it_may_not_pass():
    assert tp(103.0, [101.5, 102.5]) == (101.5, "obstacle")
    one = SessionZoneSweepConfig(obstacles_passable=1)
    assert tp(103.0, [101.5, 102.5], one) == (102.5, "obstacle")
    assert tp(103.0, [101.5, 102.5], SessionZoneSweepConfig(obstacles_passable=2)) == (
        103.0,
        "zone",
    )


def test_obstacles_closer_than_0_2r_count_as_one():
    one = SessionZoneSweepConfig(obstacles_passable=1)
    # 101.5 / 101.65 / 101.8 chain into one cluster, 102.5 is the next
    assert tp(103.0, [101.5, 101.65, 101.8, 102.5], one) == (102.5, "obstacle")
    # 0.2R apart exactly is two obstacles
    assert tp(103.0, [101.5, 101.7, 102.5], one) == (101.7, "obstacle")


def test_tp_below_1_2r_means_no_trade():
    assert tp(101.1) is None
    assert tp(103.0, [101.1]) is None
    assert tp(101.2) == (101.2, "zone")


def test_tp_buffer_below_an_obstacle():
    config = SessionZoneSweepConfig(tp_buffer_atr_mult=0.1)
    found = take_profit(LONG, 100.0, 99.0, 103.0, [102.0], 2.0, config)
    assert found == (pytest.approx(101.8), "obstacle")


def test_short_tp_is_mirrored():
    assert tp(97.5, [], direction=SHORT, entry=100.0, sl=101.0) == (97.5, "zone")
    assert tp(95.0, [98.5], direction=SHORT, entry=100.0, sl=101.0) == (98.5, "obstacle")


def test_target_zone_is_the_nearest_resistance_above_the_entry():
    zones = [
        (Role.RESISTANCE, 106.0, 105.0),
        (Role.RESISTANCE, 104.0, 103.0),
        (Role.SUPPORT, 99.0, 98.0),
        (Role.RESISTANCE, 100.5, 99.5),  # entry inside: not a target
        (None, 103.0, 102.0),  # role unknown
    ]
    assert target_zone_level(LONG, 100.0, zones) == 103.0
    assert target_zone_level(SHORT, 100.0, zones) == 99.0
    assert target_zone_level(LONG, 107.0, zones) is None


# --- 1h obstacles -------------------------------------------------------------------------


def obstacles_after(ohlc):
    tracker = ObstacleTracker(0.065, CFG)
    s = build_series(ohlc)
    for i in range(len(s)):
        tracker.update(s.view(i))
    return tracker


def test_untouched_swing_high_is_an_obstacle_until_a_wick_reaches_it():
    up_down = [(100.0, 105.0, 99.5, 104.0), (104.0, 104.5, 101.0, 102.0)]  # high 105
    assert obstacles_after(up_down).levels(LONG, 102.0) == [105.0]
    assert obstacles_after(up_down).levels(SHORT, 102.0) == []
    touched = [*up_down, (102.0, 105.0, 101.5, 103.0)]
    assert obstacles_after(touched).levels(LONG, 102.0) == []


def test_bearish_fvg_is_an_obstacle_until_tapped():
    gap_down = [
        (110.0, 110.5, 108.0, 108.5),  # 1: low 108
        (108.5, 108.6, 104.0, 104.5),  # 2
        (104.5, 106.0, 103.5, 105.5),  # 3: high 106 < 108: bearish FVG 106-108
    ]
    # candle 3 also confirms a swing low (red, green) at 103.5
    assert obstacles_after(gap_down).levels(LONG, 105.5) == [106.0]
    tapped = [*gap_down, (105.5, 106.5, 105.4, 106.2)]  # green: no new swing high
    assert obstacles_after(tapped).levels(LONG, 105.5) == []


# --- the strategy's orders on the hand-built day -----------------------------------------

NO_COSTS = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))


def run(ohlc, config=None, engine=NO_COSTS):
    strategy = SessionZoneSweep(scenario.SYMBOL, config)
    trades = run_backtest(strategy, scenario.series(ohlc), engine)
    return strategy, trades


def test_scenario_order_and_trade():
    strategy, [trade] = run(LONDON + NY_SETUP + TO_TARGET)
    [decision] = strategy.decisions
    order = decision.order
    # SL at the FVG's bottom (0.4 high, not small: 5m ATR ~0.35), 1R = 0.9; the London
    # high zone (113-114) is 3.33R away: TP capped at 3R
    assert order.direction is LONG and order.entry == 110.0
    assert order.stop_loss == 109.1
    assert order.take_profit == pytest.approx(112.7)
    assert decision.targets.target == "zone_cap"
    assert order.tags == frozenset()
    assert trade.exit_reason is ExitReason.TAKE_PROFIT and trade.r_gross == pytest.approx(3.0)


def test_lower_cap_and_minimum_rr():
    strategy, _ = run(LONDON + NY_SETUP, SessionZoneSweepConfig(tp_cap_r=2.0))
    assert strategy.decisions[0].order.take_profit == pytest.approx(111.8)
    strategy, trades = run(LONDON + NY_SETUP, SessionZoneSweepConfig(min_rr=3.5))
    [decision] = strategy.decisions
    assert decision.targets is None and decision.order is None and trades == []


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
