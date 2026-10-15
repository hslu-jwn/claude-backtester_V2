"""Strategy 4 (trend following): breakout / SMA cross / KAMA events, one position,
stop-and-reverse, 3 x ATR stop, re-entry after a stop-out, warm-up, no lookahead.
Spec: docs/strategy-trend-following.md."""

from __future__ import annotations

import pytest
from conftest import DEFAULT_START, build_series

from backtester.core.models import Direction, Timeframe
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.trend_following.config import Signal, TrendFollowingConfig
from backtester.strategy.trend_following.strategy import TrendFollowing

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
H4 = Timeframe.H4
NO_COSTS = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))


def run(ohlc, tf=H4, **config):
    config.setdefault("timeframe", tf)
    return run_backtest(
        TrendFollowing("TEST", TrendFollowingConfig(**config)), [build_series(ohlc, tf)], NO_COSTS
    )


def mirror(ohlc, axis=20.0):
    return [(axis - o, axis - lo, axis - h, axis - c) for o, h, lo, c in ohlc]


def from_closes(closes, wick=0.1):
    return [(c, c + wick, c - wick, c) for c in closes]


# breakout 3 / ATR 3 on a flat start: three candles (10.0, 10.1, 9.9, 10.0), true range 0.2
FLAT = [(10.0, 10.1, 9.9, 10.0)] * 3
BREAK_UP = (10.0, 10.3, 9.95, 10.2)  # 3: close 10.2 > highest high 10.1 -> long
# ATR(3) at 3 = (0.2 * 2 + TR 0.35) / 3 = 0.25 -> stop 10.2 - 3 * 0.25 = 9.45
QUIET = (10.2, 10.3, 10.1, 10.25)  # 4: inside the channel, no event
CFG = {"breakout_period": 3, "atr_period": 3}


# --- breakout -----------------------------------------------------------------------------


def test_breakout_long_enters_at_the_close_with_stop_3_atr_below_and_no_target():
    [t] = run([*FLAT, BREAK_UP, QUIET], **CFG)
    assert t.direction is LONG and t.entry == 10.2
    assert t.initial_stop == pytest.approx(10.2 - 3 * 0.25)
    assert t.take_profit is None
    assert t.entry_candle == DEFAULT_START + 3 * H4.duration
    assert t.exit_reason is ExitReason.END_OF_DATA and t.exit_price == 10.25


def test_short_is_the_mirror_of_the_long():
    [long] = run([*FLAT, BREAK_UP, QUIET], **CFG)
    [short] = run(mirror([*FLAT, BREAK_UP, QUIET]), **CFG)
    assert short.direction is SHORT
    assert short.entry == pytest.approx(20 - long.entry)
    assert short.initial_stop == pytest.approx(20 - long.initial_stop)
    assert short.r_gross == pytest.approx(long.r_gross)


def test_breakout_close_equal_to_the_channel_is_no_event_and_a_wick_does_not_count():
    wick = (10.0, 10.4, 9.95, 10.1)  # high above the channel, close = channel high 10.1
    assert run([*FLAT, wick, QUIET], **CFG) == []


def test_breakout_repeating_while_in_position_opens_no_new_trade():
    again = (10.25, 10.6, 10.2, 10.5)  # 5: close 10.5 > highest high 10.3 of candles 2-4
    [t] = run([*FLAT, BREAK_UP, QUIET, again, (10.5, 10.9, 10.4, 10.8)], **CFG)
    assert t.entry_candle == DEFAULT_START + 3 * H4.duration
    assert t.exit_reason is ExitReason.END_OF_DATA and t.exit_price == 10.8


def test_no_signal_during_warm_up():
    # candle 2 closes above the highest high of the 2 candles before it, but N = 3
    early = [(10.0, 10.1, 9.9, 10.0), (10.0, 10.1, 9.9, 10.0), (10.0, 10.6, 10.0, 10.5)]
    assert run([*early, QUIET], **CFG) == []


def test_no_signal_until_the_atr_exists_even_when_the_channel_is_ready():
    ohlc = [*FLAT[:2], (10.0, 10.5, 10.0, 10.4), QUIET]  # breakout of N = 2 at candle 2
    assert run(ohlc, breakout_period=2, atr_period=5) == []
    [t] = run(ohlc, breakout_period=2, atr_period=2)
    assert t.direction is LONG and t.entry == 10.4


# --- stop-and-reverse and stop-outs -------------------------------------------------------


def test_opposite_event_closes_with_signal_and_opens_the_reverse_at_the_same_close():
    down = (10.2, 10.25, 9.6, 9.7)  # 5: close 9.7 < lowest low 9.9 of candles 2-4; low > stop 9.45
    long, short = run([*FLAT, BREAK_UP, QUIET, down], **CFG)
    assert long.exit_reason is ExitReason.SIGNAL and long.exit_price == 9.7
    assert long.r_gross == pytest.approx((9.7 - 10.2) / 0.75)
    assert short.direction is SHORT and short.entry == 9.7
    assert short.entry_time == long.exit_time
    # ATR(3): 0.25 at 3, 0.2333 at 4, (0.2333 * 2 + 0.65) / 3 = 0.37222 at 5
    assert short.initial_stop == pytest.approx(9.7 + 3 * 0.37222222)
    assert short.exit_reason is ExitReason.END_OF_DATA


def test_stop_out_then_the_same_candle_event_opens_at_its_close():
    crash = (10.2, 10.25, 9.0, 9.2)  # 4: low hits the stop 9.45; close 9.2 < lowest low 9.9
    first, second = run([*FLAT, BREAK_UP, crash, (9.2, 9.3, 9.1, 9.25)], **CFG)
    assert first.exit_reason is ExitReason.STOP_LOSS and first.exit_price == 9.45
    assert first.r_gross == pytest.approx(-1.0)
    assert second.direction is SHORT and second.entry == 9.2
    assert second.entry_candle == first.exit_candle


def test_stop_out_and_same_direction_event_in_the_same_candle_re_enters():
    shakeout = (10.2, 10.6, 9.4, 10.5)  # 4: low 9.4 hits the stop, close 10.5 > high 10.3
    first, second = run([*FLAT, BREAK_UP, shakeout, (10.5, 10.6, 10.4, 10.55)], **CFG)
    assert first.exit_reason is ExitReason.STOP_LOSS
    assert second.direction is LONG and second.entry == 10.5


def test_after_a_stop_out_the_next_event_opens_a_new_trade():
    stop_candle = (10.2, 10.25, 9.4, 10.0)  # 4: hits the stop, closes inside the channel
    quiet = (10.0, 10.15, 9.95, 10.05)  # 5: no event, flat
    breakout = (10.05, 10.6, 10.0, 10.5)  # 6: close 10.5 > highest high 10.3 of candles 3-5
    first, second = run([*FLAT, BREAK_UP, stop_candle, quiet, breakout, QUIET], **CFG)
    assert first.exit_reason is ExitReason.STOP_LOSS
    assert second.direction is LONG and second.entry == 10.5
    assert second.entry_candle == DEFAULT_START + 6 * H4.duration


# --- SMA cross ----------------------------------------------------------------------------


SMA = {"signal": Signal.SMA, "sma_period": 3, "atr_period": 3}


def test_sma_fires_only_on_the_cross_not_while_above():
    # SMA(3) at 2 = 10. Candle 3: prev close 10 <= prev SMA 10 and 10.3 > SMA 10.1 -> cross.
    # Candles 4-6 stay above their SMA: no new events.
    [t] = run(from_closes([10.0, 10.0, 10.0, 10.3, 10.5, 10.6, 10.7]), **SMA)
    assert t.direction is LONG and t.entry == 10.3
    assert t.entry_candle == DEFAULT_START + 3 * H4.duration


def test_sma_cross_down_reverses():
    closes = [10.0, 10.0, 10.0, 10.3, 10.5, 10.2, 10.1]
    # candle 5: prev close 10.5 >= prev SMA 10.267 and 10.2 < SMA(10.3, 10.5, 10.2) = 10.333
    # -> short; the long's stop (10.3 - 3 x 0.2667 = 9.5) is not touched
    long, short = run(from_closes(closes), **SMA)
    assert long.exit_reason is ExitReason.SIGNAL and long.exit_price == 10.2
    assert short.direction is SHORT and short.entry == 10.2


def test_sma_needs_the_previous_sma_too():
    # closes jump at candle 2, the first with an SMA(3): no previous SMA, no cross
    assert run(from_closes([10.0, 10.0, 11.0, 11.5, 12.0]), **SMA) == []


# --- KAMA ---------------------------------------------------------------------------------


KAMA = {
    "signal": Signal.KAMA, "kama_er_period": 1, "kama_fast": 2, "kama_slow": 30,
    "kama_filter_period": 3, "kama_filter": 2.0, "atr_period": 3,
}  # fmt: skip


def test_kama_signal_enters_when_the_filter_allows_and_repeats_without_new_trades():
    # see test_tf_indicators: three KAMA changes exist at candle 4 (d4 = 0.8286 > 2 x 0.19469)
    [t] = run(from_closes([10.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0]), **KAMA)
    assert t.direction is LONG and t.entry == 13.0
    assert t.entry_candle == DEFAULT_START + 4 * H4.duration


def test_kama_filter_too_large_gives_no_trade_and_filter_0_trades_any_rise():
    # five candles: the last three KAMA changes are the ones of test_tf_indicators
    closes = from_closes([10.0, 10.0, 11.0, 12.0, 13.0])
    assert run(closes, **{**KAMA, "kama_filter": 5.0}) == []
    [t] = run(closes, **{**KAMA, "kama_filter": 0.0})
    assert t.entry == 13.0


# --- config, interface --------------------------------------------------------------------


def test_defaults_are_the_spec_values():
    c = TrendFollowingConfig()
    assert (c.timeframe, c.signal) == (H4, Signal.BREAKOUT)
    assert (c.breakout_period, c.sma_period) == (20, 50)
    assert (c.kama_er_period, c.kama_fast, c.kama_slow) == (10, 2, 30)
    assert (c.kama_filter, c.kama_filter_period) == (0.1, 20)
    assert (c.atr_period, c.stop_atr_mult) == (20, 3.0)


@pytest.mark.parametrize(
    "bad",
    [
        {"timeframe": Timeframe.M5},
        {"timeframe": Timeframe.W1},
        {"breakout_period": 0},
        {"sma_period": 1},
        {"kama_er_period": 0},
        {"kama_fast": 0},
        {"kama_fast": 30, "kama_slow": 30},
        {"kama_filter": -0.1},
        {"kama_filter_period": 1},
        {"atr_period": 0},
        {"stop_atr_mult": 0.0},
    ],
)
def test_bad_config_raises(bad):
    with pytest.raises(ValueError):
        TrendFollowingConfig(**bad)


@pytest.mark.parametrize("tf", [Timeframe.M15, Timeframe.M30, Timeframe.H1, H4, Timeframe.D1])
def test_allowed_timeframes_are_the_base_and_the_only_timeframe(tf):
    s = TrendFollowing("TEST", TrendFollowingConfig(timeframe=tf))
    assert s.base_timeframe is tf and s.timeframes == (tf,)
    assert s.uses_session_break_even is False


def test_warm_up_candles_follow_the_signal_and_the_atr():
    def need(**c):
        return TrendFollowing("TEST", TrendFollowingConfig(**c)).warmup_candles

    assert need(signal=Signal.BREAKOUT, breakout_period=100, atr_period=20) == 100
    assert need(signal=Signal.SMA, sma_period=200, atr_period=20) == 200
    assert need(signal=Signal.KAMA, kama_er_period=10, kama_filter_period=20) == 30
    assert need(signal=Signal.BREAKOUT, breakout_period=20, atr_period=50) == 49


def test_min_warmup_days_cover_the_candles_with_weekends():
    s = TrendFollowing(
        "TEST", TrendFollowingConfig(timeframe=Timeframe.D1, signal=Signal.SMA, sma_period=200)
    )
    assert s.min_warmup_days >= 200 * 7 / 5  # trading days only, weekends are not candles


# --- no lookahead -------------------------------------------------------------------------


WAVES = [
    *FLAT, BREAK_UP, QUIET, (10.25, 10.6, 10.2, 10.5), (10.5, 10.55, 9.0, 9.2),
    (9.2, 9.3, 9.1, 9.25), (9.25, 9.4, 9.0, 9.1), (9.1, 10.9, 9.1, 10.8), (10.8, 11.0, 10.6, 10.7),
    (10.7, 10.8, 8.5, 8.6), (8.6, 8.7, 8.4, 8.5),
]  # fmt: skip


@pytest.mark.parametrize("config", [CFG, SMA, KAMA], ids=["breakout", "sma", "kama"])
def test_appending_future_candles_never_changes_orders_already_given(config):
    whole = run(WAVES, **config)
    assert whole  # the fixture trades under every signal
    key = lambda t: (t.direction, t.entry, t.initial_stop, t.entry_candle)
    for cut in range(1, len(WAVES) + 1):
        part = run(WAVES[:cut], **config)
        known = [t for t in whole if t.entry_time <= DEFAULT_START + cut * H4.duration]
        assert [key(t) for t in part] == [key(t) for t in known], cut


# --- momentum, Dunnigan, SMA band (ROADMAP 10.4) ---------------------------------------------

MOM = {"signal": Signal.MOMENTUM, "momentum_period": 2, "atr_period": 3}
DUN = {"signal": Signal.DUNNIGAN, "atr_period": 3}
DUN_ROWS = [
    (9.5, 10, 9, 9.5), (10.5, 11, 10, 10.5), (11.5, 12, 11, 11.5), (11, 11.5, 10.5, 11),
    (10.5, 11, 10, 10.5), (10.7, 11.2, 10.2, 10.7), (11, 12.4, 10.5, 12.3),
    (12.3, 12.6, 12.0, 12.5),
]  # fmt: skip


def test_momentum_long_enters_at_the_first_positive_change_and_keeps_the_position():
    [t] = run(from_closes([10.0, 10.0, 10.5, 10.6, 10.7]), **MOM)
    assert t.direction is LONG and t.entry == 10.5
    assert t.entry_candle == DEFAULT_START + 2 * H4.duration
    assert t.exit_reason is ExitReason.END_OF_DATA


def test_momentum_short_is_the_mirror_and_zero_change_gives_no_trade():
    [t] = run(mirror(from_closes([10.0, 10.0, 10.5, 10.6, 10.7])), **MOM)
    assert t.direction is SHORT and t.entry == pytest.approx(9.5)
    assert run(from_closes([10.0] * 6), **MOM) == []


def test_momentum_reverses_when_the_change_turns_negative():
    long, short = run(from_closes([10.0, 10.0, 10.5, 10.6, 10.2, 9.9]), **MOM)
    # idx4: 10.2 - 10.5 < 0 -> reverse at 10.2; the long's stop 10.5 - 3 x ATR is not touched
    assert long.exit_reason is ExitReason.SIGNAL and long.exit_price == 10.2
    assert short.direction is SHORT and short.entry == 10.2


def test_dunnigan_trades_the_two_candle_hh_hl_with_close_above_the_swing_top():
    [t] = run(DUN_ROWS, **DUN)
    assert t.direction is LONG and t.entry == 12.3
    assert t.entry_candle == DEFAULT_START + 6 * H4.duration


def test_dunnigan_short_is_the_mirror():
    [t] = run(mirror(DUN_ROWS), **DUN)
    assert t.direction is SHORT and t.entry == pytest.approx(20 - 12.3)


BAND = {"signal": Signal.SMA, "sma_period": 3, "atr_period": 3}
BAND_CLOSES = [10.0, 10.0, 10.0, 10.3, 12.0, 12.1]


def test_sma_band_zero_is_the_plain_cross():
    [t] = run(from_closes(BAND_CLOSES), **BAND)
    assert t.entry == 10.3 and t.entry_candle == DEFAULT_START + 3 * H4.duration
    assert run(from_closes(BAND_CLOSES), **BAND, sma_band_atr=0.0)[0].entry == 10.3


def test_sma_band_shifts_the_cross_a_plain_cross_inside_the_band_gives_no_event():
    # candle 3: SMA 10.1 + 1 x ATR 0.2667 = 10.367 > close 10.3 -> inside the band, no event;
    # candle 4: SMA 10.7667 + 0.7778 = 11.544 < close 12 -> beyond the band -> long at 12
    [t] = run(from_closes(BAND_CLOSES), **BAND, sma_band_atr=1.0)
    assert t.direction is LONG and t.entry == 12.0
    assert t.entry_candle == DEFAULT_START + 4 * H4.duration


def test_sma_band_short_is_the_mirror():
    [t] = run(mirror(from_closes(BAND_CLOSES)), **BAND, sma_band_atr=1.0)
    assert t.direction is SHORT and t.entry == pytest.approx(8.0)


def test_sma_band_gives_no_event_while_the_previous_atr_is_unknown():
    closes = from_closes([10.0, 10.0, 10.5, 10.5])
    cfg = {"signal": Signal.SMA, "sma_period": 2, "atr_period": 3}
    assert run(closes, **cfg)[0].entry == 10.5  # plain cross at candle 2
    assert run(closes, **cfg, sma_band_atr=0.5) == []  # ATR exists at 2, the one before not


def test_new_config_defaults_and_validation():
    c = TrendFollowingConfig()
    assert (c.momentum_period, c.sma_band_atr) == (20, 0.0)
    for bad in ({"momentum_period": 0}, {"sma_band_atr": -0.1}):
        with pytest.raises(ValueError):
            TrendFollowingConfig(**bad)


def test_warm_up_candles_of_the_new_signals():
    def need(**c):
        return TrendFollowing("TEST", TrendFollowingConfig(**c)).warmup_candles

    assert need(signal=Signal.MOMENTUM, momentum_period=252) == 252
    assert need(signal=Signal.DUNNIGAN, atr_period=3) == 10  # DUNNIGAN_WARMUP_CANDLES
    assert need(signal=Signal.DUNNIGAN) == 19  # the default ATR(20) is longer
    assert need(signal=Signal.SMA, sma_period=50, sma_band_atr=0.5) == 50
    assert need(signal=Signal.SMA, sma_period=20, sma_band_atr=0.5, atr_period=50) == 50
    assert need(signal=Signal.SMA, sma_period=20, atr_period=50) == 49  # plain: as before


DUN_WAVES = [*DUN_ROWS, (12.5, 12.6, 9.0, 9.5), (9.5, 9.6, 9.0, 9.2), (9.2, 11.9, 9.1, 11.8)]


@pytest.mark.parametrize(
    ("config", "ohlc"),
    [(MOM, WAVES), (DUN, DUN_WAVES), ({**BAND, "sma_band_atr": 0.5}, WAVES)],
    ids=["momentum", "dunnigan", "sma-band"],
)
def test_new_signals_appending_future_candles_never_changes_orders_already_given(config, ohlc):
    whole = run(ohlc, **config)
    assert whole
    key = lambda t: (t.direction, t.entry, t.initial_stop, t.entry_candle)
    for cut in range(1, len(ohlc) + 1):
        part = run(ohlc[:cut], **config)
        known = [t for t in whole if t.entry_time <= DEFAULT_START + cut * H4.duration]
        assert [key(t) for t in part] == [key(t) for t in known], cut


# --- cost filter (risk-management.md › Costs › Cost filter) -------------------------------


def test_a_skipped_order_leaves_the_strategy_flat_so_the_next_event_tries_again():
    from backtester.engine.costs import SymbolCosts

    class Counting(TrendFollowing):
        sent = 0

        def on_candle(self, now, views):
            orders = super().on_candle(now, views)
            self.sent += len(orders)
            return orders

    up_again = (10.2, 10.5, 10.15, 10.45)  # 4: close 10.45 > highest high 10.3 -> long again
    strategy = Counting("TEST", TrendFollowingConfig(timeframe=H4, **CFG))
    costs = CostConfig(
        symbols={"TEST": SymbolCosts(spread=1.0, commission_per_lot=0, contract_size=1)},
        max_cost_r=0.5,  # spread 1.0 against stops under 1.0 away: every order is skipped
    )
    trades = run_backtest(
        strategy, [build_series([*FLAT, BREAK_UP, up_again], H4)], EngineConfig(costs=costs)
    )
    assert trades == [] and strategy.sent == 2  # flat after the skip: the repeat is an entry
