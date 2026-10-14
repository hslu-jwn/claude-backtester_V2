"""Backtest engine: fills at the close, SL / TP in R, SL first, break-even at the next
session start, costs in R, no lookahead.
Spec: ROADMAP.md › 3.1, strategy-session-zones.md › Stop loss, CLAUDE.md › Invariant #1."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from itertools import pairwise

import pytest
from conftest import DEFAULT_START, build_series

from backtester.core.errors import LookaheadError
from backtester.core.models import Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.base import Order, Strategy

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
M5 = timedelta(minutes=5)
NO_COSTS = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))
# Monday 2026-01-05 07:30 UTC: candle 5 (07:55) closes at London's start, 08:00 UTC
BEFORE_LONDON = datetime(2026, 1, 5, 7, 30, tzinfo=UTC)


class Scripted(Strategy):
    """Dummy strategy: at base cursor k, enter each (direction, SL, TP) of script[k] (or a
    dict of Order fields without the entry)."""

    base_timeframe = Timeframe.M5

    def __init__(self, script, timeframes=(Timeframe.M5,)):
        self.script = script
        self.timeframes = timeframes
        self.seen: list[tuple[datetime, dict]] = []

    def on_candle(self, now, views):
        self.seen.append((now, views))
        base = views[Timeframe.M5]
        close = base.current.close
        return [
            Order(item["direction"], close, **{k: v for k, v in item.items() if k != "direction"})
            if isinstance(item, dict)
            else Order(item[0], close, *item[1:])
            for item in self.script.get(base.cursor, [])
        ]


def run(ohlc, script, config=NO_COSTS, start=DEFAULT_START, symbol="TEST"):
    series = build_series(ohlc, start=start, symbol=symbol)
    return run_backtest(Scripted(script), [series], config)


ENTRY = (100.0, 100.5, 99.5, 100.0)  # entry candle, close 100
QUIET = (100.0, 100.6, 99.6, 100.2)  # hits neither 98 / 104 nor 102 / 96


# --- SL / TP -----------------------------------------------------------------------------


def test_long_take_profit_is_plus_2r_with_times_of_the_hit_candle():
    [t] = run([ENTRY, QUIET, (100.2, 104.2, 100.1, 104.0)], {0: [(LONG, 98.0, 104.0)]})
    assert t.exit_reason is ExitReason.TAKE_PROFIT
    assert t.exit_price == 104.0 and t.r_gross == pytest.approx(2.0)
    assert t.entry_time == DEFAULT_START + M5 and t.entry_candle == DEFAULT_START
    assert t.exit_time == DEFAULT_START + 3 * M5 and t.exit_candle == DEFAULT_START + 2 * M5
    assert t.mfe_r == pytest.approx(2.1) and t.mae_r == pytest.approx(-0.2)


def test_long_stop_loss_is_minus_1r():
    [t] = run([ENTRY, QUIET, (100.2, 100.3, 97.9, 98.5)], {0: [(LONG, 98.0, 104.0)]})
    assert t.exit_reason is ExitReason.STOP_LOSS
    assert t.exit_price == 98.0 and t.r_gross == pytest.approx(-1.0)


def test_sl_and_tp_inside_one_candle_counts_as_sl():
    [t] = run([ENTRY, (100.0, 104.5, 97.5, 101.0)], {0: [(LONG, 98.0, 104.0)]})
    assert t.exit_reason is ExitReason.STOP_LOSS and t.r_gross == pytest.approx(-1.0)


def test_short_is_mirrored():
    [tp] = run([ENTRY, QUIET, (100.2, 100.3, 95.9, 96.1)], {0: [(SHORT, 102.0, 96.0)]})
    assert tp.exit_reason is ExitReason.TAKE_PROFIT and tp.r_gross == pytest.approx(2.0)
    [sl] = run([ENTRY, (100.0, 102.1, 95.5, 100.0)], {0: [(SHORT, 102.0, 96.0)]})
    assert sl.exit_reason is ExitReason.STOP_LOSS and sl.r_gross == pytest.approx(-1.0)


def test_entry_candle_itself_is_never_checked():
    # the entry candle's low (97) is below the SL, but that was before the entry at its close
    [t] = run([(99.0, 100.5, 97.0, 100.0), QUIET], {0: [(LONG, 98.0, 104.0)]})
    assert t.exit_reason is ExitReason.END_OF_DATA


def test_gap_through_the_sl_fills_at_the_open_gap_through_tp_at_the_tp():
    [sl] = run([ENTRY, (97.0, 97.5, 96.5, 97.2)], {0: [(LONG, 98.0, 104.0)]})
    assert sl.exit_price == 97.0 and sl.r_gross == pytest.approx(-1.5)
    [tp] = run([ENTRY, (105.0, 105.5, 104.8, 105.2)], {0: [(LONG, 98.0, 104.0)]})
    assert tp.exit_price == 104.0 and tp.r_gross == pytest.approx(2.0)


def test_open_trade_at_the_end_closes_at_the_last_close():
    [t] = run([ENTRY, QUIET, QUIET], {0: [(LONG, 98.0, 104.0)]})
    assert t.exit_reason is ExitReason.END_OF_DATA
    assert t.exit_price == 100.2 and t.r_gross == pytest.approx(0.1)
    assert t.exit_time == DEFAULT_START + 3 * M5


def test_several_trades_at_once_are_returned_in_entry_order():
    ohlc = [ENTRY, ENTRY, QUIET, (100.2, 104.2, 100.1, 104.0)]
    trades = run(ohlc, {0: [(LONG, 98.0, 102.0)], 1: [(LONG, 99.0, 104.0)]})
    assert [t.entry_time for t in trades] == [DEFAULT_START + M5, DEFAULT_START + 2 * M5]
    assert [t.r_gross for t in trades] == pytest.approx([1.0, 4.0])


def test_bad_orders_raise():
    with pytest.raises(ValueError, match="SL"):
        run([ENTRY, QUIET], {0: [(LONG, 101.0, 104.0)]})
    with pytest.raises(ValueError, match="TP"):
        run([ENTRY, QUIET], {0: [(SHORT, 102.0, 101.0)]})

    class WrongEntry(Scripted):
        def on_candle(self, now, views):
            return [Order(LONG, 99.0, 98.0, 104.0)]

    with pytest.raises(ValueError, match="not the candle close"):
        run_backtest(WrongEntry({}), [build_series([ENTRY])], NO_COSTS)


def test_every_declared_timeframe_needs_a_series():
    strategy = Scripted({}, timeframes=(Timeframe.M5, Timeframe.H1))
    with pytest.raises(ValueError, match="H1"):
        run_backtest(strategy, [build_series([ENTRY])], NO_COSTS)


# --- break-even at the next session start ------------------------------------------------


def be_candles(close_at_session_start: float):
    """Long entry 100 (SL 98, TP 106) at 07:35; candle 5 closes at London's start 08:00."""
    return [
        ENTRY,
        *[QUIET] * 4,
        (100.2, 101.2, 99.8, close_at_session_start),  # 07:55, closes 08:00
        (100.5, 100.8, 99.9, 100.3),  # back to the entry
        (100.3, 100.4, 97.9, 98.2),  # through the original SL
    ]


def test_in_profit_at_session_start_moves_sl_to_entry():
    [t] = run(be_candles(101.0), {0: [(LONG, 98.0, 106.0)]}, start=BEFORE_LONDON)
    # candle 5 dipped to 99.8 before closing in profit: still the old SL there
    assert t.break_even_time == datetime(2026, 1, 5, 8, 0, tzinfo=UTC)
    assert t.exit_reason is ExitReason.BREAK_EVEN
    assert t.exit_candle == BEFORE_LONDON + 6 * M5
    assert t.exit_price == 100.0 and t.r_gross == pytest.approx(0.0)


def test_in_loss_at_session_start_keeps_the_original_sl():
    [t] = run(be_candles(99.9), {0: [(LONG, 98.0, 106.0)]}, start=BEFORE_LONDON)
    assert t.break_even_time is None
    assert t.exit_reason is ExitReason.STOP_LOSS and t.r_gross == pytest.approx(-1.0)


def test_exactly_at_entry_is_not_in_profit():
    [t] = run(be_candles(100.0), {0: [(LONG, 98.0, 106.0)]}, start=BEFORE_LONDON)
    assert t.break_even_time is None and t.exit_reason is ExitReason.STOP_LOSS


def test_break_even_for_shorts_is_mirrored():
    ohlc = [
        ENTRY,
        *[QUIET] * 4,
        (100.2, 100.3, 98.8, 99.0),  # closes 08:00 below the entry
        (99.0, 100.1, 98.9, 99.5),  # back to the entry
    ]
    [t] = run(ohlc, {0: [(SHORT, 102.0, 94.0)]}, start=BEFORE_LONDON)
    assert t.exit_reason is ExitReason.BREAK_EVEN and t.r_gross == pytest.approx(0.0)


def test_only_the_next_session_start_counts():
    # entered at 08:00 (closes at London's start): the next start is New York, 13:00 UTC
    start = BEFORE_LONDON + 5 * M5
    [t] = run(be_candles(101.0)[5:], {0: [(LONG, 99.0, 106.0)]}, start=start)
    assert t.break_even_time is None


def test_break_even_can_be_switched_off():
    config = EngineConfig(costs=NO_COSTS.costs, break_even_at_next_session=False)
    [t] = run(be_candles(101.0), {0: [(LONG, 98.0, 106.0)]}, config, start=BEFORE_LONDON)
    assert t.break_even_time is None and t.exit_reason is ExitReason.STOP_LOSS


# XAUUSD with costs: spread 0.25 + commission $6 / $100 per 1.0 = 0.06 -> a long's
# break-even stop is 100.31, where a hit is 0R net.
GOLD = EngineConfig()


def test_break_even_with_costs_is_0r_net():
    [t] = run(
        be_candles(101.0), {0: [(LONG, 98.0, 106.0)]}, GOLD, start=BEFORE_LONDON, symbol="XAUUSD"
    )
    assert t.break_even_stop == pytest.approx(100.31)
    assert t.exit_reason is ExitReason.BREAK_EVEN and t.exit_price == pytest.approx(100.31)
    assert t.r_net == pytest.approx(0.0)
    assert t.r_gross == pytest.approx(0.155)  # 0.31 / risk 2


def test_close_in_profit_but_below_the_cost_level_does_not_move_the_sl():
    [t] = run(
        be_candles(100.3), {0: [(LONG, 98.0, 106.0)]}, GOLD, start=BEFORE_LONDON, symbol="XAUUSD"
    )
    assert t.break_even_time is None and t.break_even_stop is None
    assert t.exit_reason is ExitReason.STOP_LOSS and t.r_gross == pytest.approx(-1.0)


def test_short_break_even_with_costs_is_mirrored():
    ohlc = [
        ENTRY,
        *[QUIET] * 4,
        (100.2, 100.3, 98.8, 99.0),  # closes 08:00 below 99.69
        (99.0, 99.8, 98.9, 99.5),  # back up through 99.69
    ]
    [t] = run(ohlc, {0: [(SHORT, 102.0, 94.0)]}, GOLD, start=BEFORE_LONDON, symbol="XAUUSD")
    assert t.break_even_stop == pytest.approx(99.69)
    assert t.exit_reason is ExitReason.BREAK_EVEN and t.r_net == pytest.approx(0.0)


# --- costs in R ---------------------------------------------------------------------------

# XAUUSD: spread 0.25, $6 per lot, $100 per 1.0 move. Risk 2.5: spread 0.1R,
# commission 6 / (2.5 * 100) = 0.024R.
GOLD_WIN = [ENTRY, (100.0, 105.1, 99.9, 105.0)]
GOLD_LOSS = [ENTRY, (100.0, 100.1, 97.4, 97.6)]


def test_long_costs_spread_at_entry_and_commission():
    [t] = run(GOLD_WIN, {0: [(LONG, 97.5, 105.0)]}, EngineConfig(), symbol="XAUUSD")
    assert t.entry_fill == pytest.approx(100.25) and t.exit_fill == 105.0
    assert t.spread_r == pytest.approx(0.1) and t.commission_r == pytest.approx(0.024)
    assert t.r_gross == pytest.approx(2.0) and t.r_net == pytest.approx(1.876)
    [loss] = run(GOLD_LOSS, {0: [(LONG, 97.5, 105.0)]}, EngineConfig(), symbol="XAUUSD")
    assert loss.r_gross == pytest.approx(-1.0) and loss.r_net == pytest.approx(-1.124)


def test_short_costs_spread_at_exit():
    ohlc = [ENTRY, (100.0, 100.1, 94.9, 95.0)]
    [t] = run(ohlc, {0: [(SHORT, 102.5, 95.0)]}, EngineConfig(), symbol="XAUUSD")
    assert t.entry_fill == 100.0 and t.exit_fill == pytest.approx(95.25)
    assert t.r_gross == pytest.approx(2.0) and t.r_net == pytest.approx(1.876)


def test_costs_can_be_switched_off_one_by_one():
    script = {0: [(LONG, 97.5, 105.0)]}
    no_spread = EngineConfig(costs=CostConfig(spread_enabled=False))
    [t] = run(GOLD_WIN, script, no_spread, symbol="XAUUSD")
    assert t.spread_r == 0 and t.entry_fill == 100.0 and t.r_net == pytest.approx(1.976)
    no_commission = EngineConfig(costs=CostConfig(commission_enabled=False))
    [t] = run(GOLD_WIN, script, no_commission, symbol="XAUUSD")
    assert t.commission_r == 0 and t.r_net == pytest.approx(1.9)
    [t] = run(GOLD_WIN, script, NO_COSTS, symbol="XAUUSD")
    assert t.r_net == t.r_gross


def test_forex_commission_depends_on_the_sl_distance():
    costs = CostConfig()
    # GBPUSD 20 pips: $5 / (0.002 * 100,000) = 0.025R, spread 0.3 pip = 0.015R
    assert costs.commission_r("GBPUSD", 0.002) == pytest.approx(0.025)
    assert costs.spread_r("GBPUSD", 0.002) == pytest.approx(0.015)
    # GBPJPY 20 pips at USDJPY 150: $5 / (0.2 * 100,000 / 150) = 0.0375R
    assert costs.commission_r("GBPJPY", 0.2) == pytest.approx(0.0375)
    assert costs.spread_r("GBPJPY", 0.2) == pytest.approx(0.05)


def test_unknown_symbol_with_costs_on_raises():
    with pytest.raises(KeyError, match="no cost settings for TEST"):
        run([ENTRY, QUIET], {0: [(LONG, 98.0, 104.0)]}, EngineConfig())


# --- multi-timeframe views and no lookahead ----------------------------------------------


def wave(n: int) -> list[tuple[float, float, float, float]]:
    """A deterministic up-and-down path, consecutive candles open at the previous close."""
    closes = [100 + 3 * math.sin(i / 5) + 0.8 * math.sin(i * 1.7) for i in range(n + 1)]
    return [(o, max(o, c) + 0.3, min(o, c) - 0.3, c) for o, c in pairwise(closes)]


def test_higher_timeframes_are_only_seen_once_closed():
    m5 = build_series(wave(24))
    m30 = build_series(wave(4), Timeframe.M30)
    h1 = build_series(wave(2), Timeframe.H1)
    strategy = Scripted({}, timeframes=(Timeframe.M5, Timeframe.M30, Timeframe.H1))
    run_backtest(strategy, [h1, m5, m30], NO_COSTS)
    assert len(strategy.seen) == 24
    for now, views in strategy.seen:
        base = views[Timeframe.M5]
        assert base.current.ts + M5 == now
        with pytest.raises(LookaheadError):
            base[base.cursor + 1]
        for tf in (Timeframe.M30, Timeframe.H1):
            view = views[tf]
            if view is not None:
                assert view.current.ts + tf.duration <= now
    assert strategy.seen[4][1][Timeframe.M30] is None  # 00:20 candle closes 00:25
    assert strategy.seen[5][1][Timeframe.M30].cursor == 0  # closes 00:30
    assert strategy.seen[10][1][Timeframe.H1] is None
    assert strategy.seen[11][1][Timeframe.H1].cursor == 0


class EveryNth(Strategy):
    """Enters on every 4th candle, direction from the last two closes (views only)."""

    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)

    def on_candle(self, now, views):
        view: SeriesView = views[Timeframe.M5]
        if view.cursor % 4 or len(view) < 2:
            return []
        close, prev = view[-1].close, view[-2].close
        if close >= prev:
            return [Order(LONG, close, close - 1.0, close + 2.0)]
        return [Order(SHORT, close, close + 1.0, close - 2.0)]


def test_future_candles_never_change_finished_trades():
    """No-lookahead: a trade closed by candle k is identical whether or not the history
    continues after k; only END_OF_DATA trades may differ."""
    full_ohlc = wave(300)
    full = run_backtest(EveryNth(), [build_series(full_ohlc)], NO_COSTS)
    assert {t.exit_reason for t in full} >= {ExitReason.STOP_LOSS, ExitReason.TAKE_PROFIT}
    for k in (40, 97, 150, 299):
        part = run_backtest(EveryNth(), [build_series(full_ohlc[:k])], NO_COSTS)
        finished = [t for t in part if t.exit_reason is not ExitReason.END_OF_DATA]
        assert finished == [t for t in full if t.exit_time <= DEFAULT_START + k * M5]
        assert [t.entry_time for t in part] == [
            t.entry_time for t in full if t.entry_time <= DEFAULT_START + k * M5
        ]


# --- two TPs: partial closes (strategy-session-zones.md › Take profit) ---------------------

NO_SESSION_BE = EngineConfig(
    costs=CostConfig(spread_enabled=False, commission_enabled=False),
    break_even_at_next_session=False,
)


def two_tps(direction=LONG, sl=98.0, tp1=102.4, tp2=104.0, share=0.5, be=True):
    """Entry 100, 1R = 2: TP1 at 1.2R, TP2 at 2R by default."""
    return {
        0: [
            {
                "direction": direction,
                "stop_loss": sl,
                "take_profit": tp1,
                "take_profit_2": tp2,
                "tp1_share": share,
                "break_even_after_tp1": be,
            }
        ]
    }


TP1_CANDLE = (100.2, 102.5, 100.1, 102.2)  # reaches TP1 102.4, closes above break-even


def test_tp1_then_tp2_is_the_weighted_sum():
    ohlc = [ENTRY, TP1_CANDLE, (102.2, 104.1, 101.0, 103.9)]
    [t] = run(ohlc, two_tps(), NO_SESSION_BE)
    first, rest = t.parts
    assert (first.share, first.price, first.reason) == (0.5, 102.4, ExitReason.TAKE_PROFIT)
    assert first.time == DEFAULT_START + 2 * M5 and first.r_gross == pytest.approx(1.2)
    assert (rest.share, rest.price, rest.reason) == (0.5, 104.0, ExitReason.TAKE_PROFIT)
    assert t.r_gross == pytest.approx(0.5 * 1.2 + 0.5 * 2.0)
    assert t.exit_time == DEFAULT_START + 3 * M5 and t.exit_price == 104.0
    assert t.planned_r == pytest.approx(1.6)
    # the SL of the rest moved to break-even with the TP1 candle (no costs: the entry)
    assert t.break_even_time == DEFAULT_START + 2 * M5 and t.break_even_stop == 100.0


def test_rest_stopped_at_break_even_after_tp1():
    ohlc = [ENTRY, TP1_CANDLE, (102.2, 102.3, 99.9, 100.5)]
    [t] = run(ohlc, two_tps(), NO_SESSION_BE)
    assert [p.reason for p in t.parts] == [ExitReason.TAKE_PROFIT, ExitReason.BREAK_EVEN]
    assert t.exit_reason is ExitReason.BREAK_EVEN and t.r_gross == pytest.approx(0.6)


def test_break_even_counts_from_the_candle_after_tp1():
    # the TP1 candle's low (99.5) is below the entry, but may have come before TP1
    ohlc = [ENTRY, (100.2, 102.5, 99.5, 102.2), (102.2, 102.3, 100.5, 101.0)]
    [t] = run(ohlc, two_tps(), NO_SESSION_BE)
    assert t.exit_reason is ExitReason.END_OF_DATA and len(t.parts) == 2


def test_tp1_candle_closing_back_below_break_even_stops_the_rest_in_it():
    ohlc = [ENTRY, (100.2, 102.5, 99.5, 99.8), QUIET]
    [t] = run(ohlc, two_tps(), NO_SESSION_BE)
    assert [p.reason for p in t.parts] == [ExitReason.TAKE_PROFIT, ExitReason.BREAK_EVEN]
    assert t.parts[1].time == DEFAULT_START + 2 * M5 and t.parts[1].price == 100.0
    assert t.r_gross == pytest.approx(0.6)


def test_without_break_even_after_tp1_the_rest_keeps_its_sl():
    ohlc = [ENTRY, TP1_CANDLE, (102.2, 102.3, 97.9, 98.5)]
    [t] = run(ohlc, two_tps(be=False), NO_SESSION_BE)
    assert t.break_even_time is None and t.exit_reason is ExitReason.STOP_LOSS
    assert t.r_gross == pytest.approx(0.5 * 1.2 - 0.5)


def test_tp1_and_tp2_in_one_candle_sl_first_with_tp1():
    [both] = run([ENTRY, (100.2, 104.1, 100.1, 104.0)], two_tps(), NO_SESSION_BE)
    assert len(both.parts) == 2 and both.r_gross == pytest.approx(1.6)
    [sl] = run([ENTRY, (100.2, 102.5, 97.9, 101.0)], two_tps(), NO_SESSION_BE)
    assert len(sl.parts) == 1 and sl.r_gross == pytest.approx(-1.0)


def test_tp1_share_setting():
    ohlc = [ENTRY, TP1_CANDLE, (102.2, 102.3, 99.9, 100.5)]
    [t] = run(ohlc, two_tps(share=0.25), NO_SESSION_BE)
    assert [p.share for p in t.parts] == [0.25, 0.75]
    assert t.r_gross == pytest.approx(0.25 * 1.2)


def test_short_two_tps_mirrored():
    ohlc = [ENTRY, (99.8, 99.9, 97.5, 97.8), (97.8, 99.0, 95.9, 96.2)]
    [t] = run(ohlc, two_tps(SHORT, sl=102.0, tp1=97.6, tp2=96.0), NO_SESSION_BE)
    assert [p.price for p in t.parts] == [97.6, 96.0]
    assert t.r_gross == pytest.approx(1.6)


def test_two_tps_net_of_costs():
    # XAUUSD, risk 2: spread 0.125R, commission 6 / (2 x 100) = 0.03R; break-even 100.31
    gold = EngineConfig(break_even_at_next_session=False)
    win = [ENTRY, TP1_CANDLE, (102.2, 104.1, 101.0, 103.9)]
    [t] = run(win, two_tps(), gold, symbol="XAUUSD")
    assert t.r_net == pytest.approx(1.6 - 0.125 - 0.03)
    back = [ENTRY, TP1_CANDLE, (102.2, 102.3, 99.9, 100.5)]
    [t] = run(back, two_tps(), gold, symbol="XAUUSD")
    assert t.break_even_stop == pytest.approx(100.31)
    # TP1 half: 0.5 x (102.4 - 100.25) / 2 - 0.015 commission; the rest ends at 0R net
    assert t.r_net == pytest.approx(0.5 * 2.15 / 2 - 0.015)
    rest = t.parts[1]
    assert 0.5 * rest.r_fills - 0.015 == pytest.approx(0.0)


def test_bad_two_tp_orders_raise():
    with pytest.raises(ValueError, match="TP2"):
        run([ENTRY, QUIET], two_tps(tp2=102.0), NO_SESSION_BE)
    with pytest.raises(ValueError, match="tp1_share"):
        run([ENTRY, QUIET], two_tps(share=1.0), NO_SESSION_BE)


# --- three TPs (strategy-ny-indices.md › Take Profit) -----------------------------------


def three_tps(tp3=105.0, be=True):
    """Entry 100, 1R = 2: TP1 102.4 (1.2R), TP2 104 (2R), TP3 105 (2.5R), a third each."""
    return {
        0: [
            {
                "direction": LONG,
                "stop_loss": 98.0,
                "take_profit": 102.4,
                "take_profit_2": 104.0,
                "take_profit_3": tp3,
                "tp1_share": 1 / 3,
                "tp2_share": 1 / 3,
                "break_even_after_tp1": be,
            }
        ]
    }


def test_three_tps_close_a_third_each():
    ohlc = [ENTRY, TP1_CANDLE, (102.2, 104.1, 101.0, 103.9), (103.9, 105.2, 103.5, 105.0)]
    [t] = run(ohlc, three_tps(), NO_SESSION_BE)
    assert [p.price for p in t.parts] == [102.4, 104.0, 105.0]
    assert [p.share for p in t.parts] == pytest.approx([1 / 3, 1 / 3, 1 / 3])
    assert t.r_gross == pytest.approx((1.2 + 2.0 + 2.5) / 3)
    assert t.planned_r == pytest.approx((1.2 + 2.0 + 2.5) / 3)
    assert (t.take_profit_3, t.tp2_share) == (105.0, pytest.approx(1 / 3))
    assert t.break_even_time == DEFAULT_START + 2 * M5  # after TP1


def test_three_tps_rest_at_break_even_after_tp2():
    ohlc = [ENTRY, TP1_CANDLE, (102.2, 104.1, 101.0, 103.9), (103.9, 104.0, 99.9, 100.5)]
    [t] = run(ohlc, three_tps(), NO_SESSION_BE)
    assert [p.reason for p in t.parts] == [
        ExitReason.TAKE_PROFIT,
        ExitReason.TAKE_PROFIT,
        ExitReason.BREAK_EVEN,
    ]
    assert t.r_gross == pytest.approx((1.2 + 2.0) / 3)


def test_all_three_tps_in_one_candle():
    [t] = run([ENTRY, (100.2, 105.5, 100.1, 105.2)], three_tps(), NO_SESSION_BE)
    assert len(t.parts) == 3 and t.exit_reason is ExitReason.TAKE_PROFIT


def test_bad_three_tp_orders_raise():
    with pytest.raises(ValueError, match="TP3"):
        run([ENTRY, QUIET], three_tps(tp3=103.0), NO_SESSION_BE)


class Notified(Scripted):
    """Records the trades the engine reports closed, with the order's `ref`."""

    def __init__(self, script):
        super().__init__(script)
        self.closed = []

    def on_trade_closed(self, ref, result):
        self.closed.append((ref, result.exit_reason, self.seen[-1][0] if self.seen else None))


def test_the_strategy_hears_when_its_trade_closed_before_its_next_candle():
    script = {0: [{"direction": LONG, "stop_loss": 98.0, "take_profit": 102.0, "ref": "a"}]}
    strategy = Notified(script)
    series = build_series([ENTRY, QUIET, (100.2, 102.5, 100.1, 102.2), QUIET])
    [t] = run_backtest(strategy, [series], NO_SESSION_BE)
    # closed by candle 2: reported before on_candle for candle 2 (last seen: candle 1)
    assert strategy.closed == [("a", ExitReason.TAKE_PROFIT, DEFAULT_START + 2 * M5)]
    assert t.exit_time == DEFAULT_START + 3 * M5


# --- limit fills (strategy 3: orders filled at their level inside a later candle) --------


class LimitAt(Strategy):
    """At base cursor `at`, emit one limit order (filled at `entry`, inside this candle)."""

    base_timeframe = Timeframe.M5
    timeframes = (Timeframe.M5,)

    def __init__(self, at, direction, entry, stop_loss, take_profit):
        self._args = (at, direction, entry, stop_loss, take_profit)

    def on_candle(self, now, views):
        at, direction, entry, stop_loss, take_profit = self._args
        if views[Timeframe.M5].cursor != at:
            return []
        return [Order(direction, entry, stop_loss, take_profit, limit_fill=True)]


def run_limit(ohlc, *args):
    return run_backtest(LimitAt(*args), [build_series(ohlc)], NO_COSTS)


def test_limit_order_fills_at_its_level_not_at_the_close():
    # candle 1 trades down to 99.0 and closes at 100.4: filled at 99.0, 1R = 1.0
    [t] = run_limit(
        [ENTRY, (100.0, 100.5, 99.0, 100.4), (100.4, 101.2, 100.3, 101.1)],
        1,
        LONG,
        99.0,
        98.0,
        100.0,
    )
    assert t.entry == 99.0 and t.entry_candle == DEFAULT_START + M5
    assert t.entry_time == DEFAULT_START + 2 * M5  # close of the fill candle
    assert t.exit_reason is ExitReason.TAKE_PROFIT and t.r_gross == pytest.approx(1.0)


def test_stop_inside_the_fill_candle_is_a_loss_and_a_tp_there_is_not_counted():
    [sl] = run_limit([ENTRY, (100.0, 100.5, 97.5, 98.5)], 1, LONG, 99.0, 98.0, 100.0)
    assert sl.exit_reason is ExitReason.STOP_LOSS and sl.r_gross == pytest.approx(-1.0)
    assert sl.exit_candle == DEFAULT_START + M5
    # the fill candle also reaches the TP (high 100.9 >= 100.0): not counted, still open
    [t] = run_limit([ENTRY, (100.0, 100.9, 99.0, 100.5)], 1, LONG, 99.0, 98.0, 100.0)
    assert t.exit_reason is ExitReason.END_OF_DATA


def test_short_limit_is_mirrored():
    [t] = run_limit(
        [ENTRY, (100.0, 101.0, 99.6, 99.8), (99.8, 99.9, 98.8, 99.0)], 1, SHORT, 101.0, 102.0, 100.0
    )
    assert t.entry == 101.0 and t.exit_reason is ExitReason.TAKE_PROFIT
    assert t.r_gross == pytest.approx(1.0)


def test_limit_level_outside_the_candle_raises():
    with pytest.raises(ValueError, match="limit"):
        run_limit([ENTRY, (100.0, 100.5, 99.5, 100.2)], 1, LONG, 99.0, 98.0, 100.0)
