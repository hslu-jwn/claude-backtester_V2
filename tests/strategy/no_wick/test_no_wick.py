"""Strategy 3 (no-wick candle in the trend): signal, entry modes, SL / TP, trend source,
no lookahead. Spec: docs/strategy-no-wick.md, confluences.md (swings, BOS, trend)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from conftest import DEFAULT_START, build_series

from backtester.core.models import Direction, Timeframe
from backtester.detectors.settings import DetectorSettings
from backtester.detectors.swings import SwingConfig
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.no_wick.config import EntryMode, NoWickConfig, TrendSource
from backtester.strategy.no_wick.strategy import NoWick

M5, M15, M30, H1, H4 = (Timeframe.M5, Timeframe.M15, Timeframe.M30, Timeframe.H1, Timeframe.H4)
FIVE = timedelta(minutes=5)
NO_COSTS = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))
DETECTORS = DetectorSettings(swings=SwingConfig(doji_max_body={"TEST": 0.01}))

# An uptrend on the series' own timeframe: swing low 9.7 (confirmed at 1), swing high 10.6
# (3), swing low 10.0 (5), then candle 6 closes at 10.8 above 10.6: bullish BOS at 6.
UPTREND = [
    (10.0, 10.2, 9.8, 9.9),  # 0 red
    (9.9, 10.1, 9.7, 10.0),  # 1 green: swing low 9.7
    (10.0, 10.5, 9.95, 10.4),  # 2 green
    (10.4, 10.6, 10.2, 10.3),  # 3 red: swing high 10.6
    (10.3, 10.4, 10.0, 10.1),  # 4 red
    (10.1, 10.5, 10.05, 10.45),  # 5 green: swing low 10.0
    (10.45, 10.9, 10.4, 10.8),  # 6 green, closes above 10.6: BOS up, uptrend
]
SIGNAL = (10.8, 11.0, 10.8, 10.95)  # 7 green, low = open: long signal
UP = (10.95, 12.0, 10.9, 11.9)  # reaches any 1R target used below


def mirror(ohlc, axis=20.0):
    """Price-mirrored candles: green <-> red, highs <-> lows."""
    return [(axis - o, axis - lo, axis - h, axis - c) for o, h, lo, c in ohlc]


def strategy(**config):
    return NoWick("TEST", NoWickConfig(**config), DETECTORS)


def run(ohlc, tf=M5, **config):
    config.setdefault("timeframe", tf)
    config.setdefault("trend_source", TrendSource.SAME)
    return run_backtest(strategy(**config), [build_series(ohlc, tf)], NO_COSTS)


def test_long_signal_enters_at_the_close_with_sl_at_the_swing_and_tp_at_1r():
    [t] = run([*UPTREND, SIGNAL, UP])
    assert t.direction is Direction.BULLISH and t.entry == 10.95
    assert t.initial_stop == pytest.approx(10.0 - 0.1 * 0.95)  # swing 10.0, buffer 10% of 0.95
    assert t.take_profit == pytest.approx(10.95 + (10.95 - t.initial_stop))
    assert t.exit_reason is ExitReason.TAKE_PROFIT and t.r_gross == pytest.approx(1.0)
    assert t.entry_candle == DEFAULT_START + 7 * FIVE


def test_short_is_the_mirror_of_the_long():
    [long] = run([*UPTREND, SIGNAL, UP])
    [short] = run(mirror([*UPTREND, SIGNAL, UP]))
    assert short.direction is Direction.BEARISH
    assert short.entry == pytest.approx(20 - long.entry)
    assert short.initial_stop == pytest.approx(20 - long.initial_stop)
    assert short.take_profit == pytest.approx(20 - long.take_profit)
    assert short.exit_reason is ExitReason.TAKE_PROFIT


@pytest.mark.parametrize(
    "candle",
    [
        (10.8, 11.0, 10.7, 10.95),  # green with a lower wick
        (10.95, 11.0, 10.8, 10.8),  # red: wrong colour in an uptrend
        (10.8, 10.8, 10.8, 10.8),  # no range
    ],
)
def test_no_signal_for_a_wick_the_wrong_colour_or_no_range(candle):
    assert run([*UPTREND, candle, (10.9, 11.0, 10.8, 10.9)]) == []


def test_no_signal_before_the_first_bos():
    # a no-wick green candle that closes below the swing high 10.6: still no trend
    assert run([*UPTREND[:6], (10.5, 10.55, 10.5, 10.55)]) == []
    # the candle that closes above it is itself the BOS: from its close the trend is up
    assert len(run([*UPTREND[:6], SIGNAL])) == 1


def test_wick_share_allows_a_small_lower_wick():
    candle = (10.8, 11.0, 10.79, 10.95)  # lower wick 0.01 of range 0.21 = 4.8%
    wicked_up = (10.95, 12.0, 10.7, 11.9)  # its own lower wick is 19% of its range
    assert run([*UPTREND, candle, wicked_up]) == []
    [t] = run([*UPTREND, candle, wicked_up], max_wick_share=0.05)
    assert t.entry == 10.95


def test_body_end_is_a_limit_at_the_open_filled_by_a_later_candle():
    # candle 8 trades back down to 10.8 (the signal candle's open) and closes at 10.9
    ohlc = [*UPTREND, SIGNAL, (10.95, 11.0, 10.8, 10.9), (10.9, 12.0, 10.85, 11.9)]
    [t] = run(ohlc, entry_mode=EntryMode.BODY_END)
    assert t.entry == 10.8 and t.entry_candle == DEFAULT_START + 8 * FIVE
    assert t.initial_stop == pytest.approx(10.0 - 0.1 * 0.8)  # buffer from the limit level
    assert t.take_profit == pytest.approx(10.8 + (10.8 - t.initial_stop))
    assert t.exit_reason is ExitReason.TAKE_PROFIT


def test_a_gap_through_the_limit_fills_at_the_open_and_through_the_stop_drops_it():
    gap = (10.7, 10.75, 10.65, 10.7)  # whole candle below the 10.8 level, above the stop 9.92
    [t] = run([*UPTREND, SIGNAL, gap, (10.7, 12.0, 10.65, 11.9)], entry_mode=EntryMode.BODY_END)
    assert t.entry == 10.7 and t.initial_stop == pytest.approx(10.0 - 0.1 * 0.8)
    deep = (9.5, 9.6, 9.4, 9.5)  # below the stop as well
    assert run([*UPTREND, SIGNAL, deep, UP], entry_mode=EntryMode.BODY_END) == []


def test_middle_is_a_limit_at_half_the_range():
    ohlc = [*UPTREND, SIGNAL, (10.95, 11.0, 10.88, 10.9), (10.9, 12.0, 10.85, 11.9)]
    [t] = run(ohlc, entry_mode=EntryMode.MIDDLE)
    assert t.entry == pytest.approx(10.9)


def test_limit_order_expires_after_the_given_candles():
    away = (11.0, 11.2, 10.9, 11.1)  # has a wick, never trades back down to 10.8
    touch = (11.0, 11.1, 10.8, 10.9)
    six = run([*UPTREND, SIGNAL, *[away] * 5, touch], entry_mode=EntryMode.BODY_END)
    assert len(six) == 1  # filled by the 6th candle after the signal
    seven = run([*UPTREND, SIGNAL, *[away] * 6, touch], entry_mode=EntryMode.BODY_END)
    assert seven == []
    custom = run(
        [*UPTREND, SIGNAL, *[away] * 6, touch],
        entry_mode=EntryMode.BODY_END,
        order_expiry_candles=7,
    )
    assert len(custom) == 1


def test_swing_not_below_the_entry_gives_no_trade():
    # candle 7 red pulls back; candle 8 green, low = open = 10.7 confirms a swing low at 10.7:
    # for body_end the entry level is 10.7 itself, so there is no room below it
    pull = (10.9, 10.95, 10.75, 10.8)
    sig = (10.7, 10.9, 10.7, 10.85)
    follow = (10.85, 11.0, 10.7, 10.9)
    assert run([*UPTREND, pull, sig, follow], entry_mode=EntryMode.BODY_END) == []
    [t] = run([*UPTREND, pull, sig, (10.85, 11.5, 10.8, 11.4)])
    assert t.entry == 10.85 and t.initial_stop < 10.7


def test_consecutive_signals_are_separate_trades():
    second = (10.95, 11.1, 10.95, 11.05)
    trades = run([*UPTREND, SIGNAL, second, (11.05, 11.06, 10.9, 11.0)])
    assert [t.entry for t in trades] == [10.95, 11.05]


def test_higher_timeframe_trend_decides_with_trend_source_higher():
    pad = [(10.0, 10.0, 10.0, 10.0)] * 21  # 15m candles 0..6 cover M5 candles 0..20
    base = build_series([*pad, *UPTREND, SIGNAL, UP], M5)
    down15 = build_series(mirror(UPTREND), M15)
    up15 = build_series(UPTREND, M15)
    cfg = {"timeframe": M5, "trend_source": TrendSource.HIGHER}
    assert run_backtest(strategy(**cfg), [base, down15], NO_COSTS) == []
    [t] = run_backtest(strategy(**cfg), [base, up15], NO_COSTS)
    assert t.direction is Direction.BULLISH
    same = {**cfg, "trend_source": TrendSource.SAME}
    assert len(run_backtest(strategy(**same), [base, down15], NO_COSTS)) == 1


def test_declared_timeframes_follow_the_config():
    pairs = {M5: M15, M15: H1, M30: H4, H1: H4}
    for tf, higher in pairs.items():
        s = strategy(timeframe=tf)
        assert s.base_timeframe is tf and s.timeframes == (tf, higher)
    s = strategy(timeframe=M15, trend_source=TrendSource.SAME)
    assert s.timeframes == (M15,)


@pytest.mark.parametrize("mode", list(EntryMode))
def test_appending_future_candles_never_changes_orders_already_given(mode):
    full = [*UPTREND, SIGNAL, (10.95, 11.0, 10.8, 10.9), (10.9, 12.0, 10.85, 11.9), *UPTREND]
    whole = run(full, entry_mode=mode)
    for cut in range(8, len(full)):
        part = run(full[:cut], entry_mode=mode)
        known = [t for t in whole if t.entry_time <= DEFAULT_START + cut * FIVE]
        key = lambda t: (t.entry, t.initial_stop, t.take_profit, t.entry_candle)
        assert [key(t) for t in part] == [key(t) for t in known]


@pytest.mark.parametrize(
    "bad",
    [
        {"timeframe": Timeframe.M1},
        {"timeframe": Timeframe.H4},
        {"max_wick_share": -0.1},
        {"max_wick_share": 1.0},
        {"sl_buffer": -0.1},
        {"rr": 0.0},
        {"order_expiry_candles": 0},
    ],
)
def test_bad_config_raises(bad):
    with pytest.raises(ValueError):
        NoWickConfig(**bad)


def test_defaults_are_the_spec_values():
    c = NoWickConfig()
    assert (c.timeframe, c.trend_source, c.entry_mode) == (M15, TrendSource.HIGHER, EntryMode.CLOSE)
    assert (c.max_wick_share, c.sl_buffer, c.rr, c.order_expiry_candles) == (0.0, 0.10, 1.0, 6)
