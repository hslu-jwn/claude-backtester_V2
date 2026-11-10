"""Pre-registered TS: hand-built daily extremes, clocks and execution only."""

import tomllib
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import pytest
from test_daily_reversal import DAYS, M1, NY, bar, execute, feed, session

from backtester.core.models import Candle, Direction
from backtester.core.series import CandleSeries
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig, SymbolCosts
from backtester.engine.trade import ExitReason
from backtester.strategy.daily_reversal.config import DailyReversalConfig
from backtester.strategy.daily_reversal.strategy import DailyReversal


def pattern(age=4, low=89, high=110, close=101, tied=False, lookback=20):
    # Prior low 90 lies exactly `age` sessions before signal. Ordinary range=10.
    out = []
    for i in range(lookback):
        lo = 90 if i == lookback - age or (tied and i == lookback - 1) else 100
        out += session(i, 105, 120 if i == lookback - age else 110, lo, 105)
    return out + session(lookback, close, high, low, close)


@pytest.mark.parametrize("short", [False, True])
def test_ts_confirms_only_at_close_and_enters_next_first_m1_close(short):
    candles = pattern() + session(21, 102, 104, 101, 103)
    if short:
        candles = [Candle(c.ts, 220-c.open, 220-c.low, 220-c.high, 220-c.close) for c in candles]
    _, orders, _ = feed(candles, setup="TS")
    assert len(orders) == 1
    now, order = orders[0]
    assert now == candles[-2].ts + M1.duration
    assert order.entry == (117 if short else 103)
    assert order.stop_loss == pytest.approx(131.01 if short else 88.99)
    assert order.direction is (Direction.BEARISH if short else Direction.BULLISH)
    assert order.take_profit is None  # TS ignores E8's default 2R target


@pytest.mark.parametrize("kwargs", [
    {"age": 3}, {"close": 90}, {"close": 89}, {"low": 90},
    {"tied": True}, {"low": 70}, {"high": 121, "low": 89},
])
def test_ts_rejects_recent_tied_extreme_no_recovery_wide_and_dual_signal(kwargs):
    assert feed(pattern(**kwargs) + session(21), setup="TS")[1] == []


@pytest.mark.parametrize("hold", [1, 2])
def test_ts_exit_counts_from_signal_day_and_stop_precedes_timer(hold):
    candles = pattern() + session(21, 103, 106, 101, 104)
    if hold == 2:
        candles += session(22, 104, 107, 102, 105)
    _, trades = execute(candles, setup="TS", ts_exit_sessions=hold)
    assert len(trades) == 1
    assert trades[0].exit_reason is ExitReason.SIGNAL
    assert trades[0].exit_time == candles[-1].ts + M1.duration
    assert trades[0].take_profit is None
    if hold == 2:
        assert trades[0].swap_r < 0
    candles[-1] = Candle(candles[-1].ts, 104, 106, 88, 104)
    _, trades = execute(candles, setup="TS", ts_exit_sessions=hold)
    assert trades[0].exit_reason is ExitReason.STOP_LOSS


def test_ts_missing_first_minute_or_stop_touch_consumes_signal():
    for first in (bar(DAYS[21], "09:32", 103, 104, 101, 103),
                  bar(DAYS[21], "09:31", 103, 104, 88, 103)):
        assert feed(pattern() + [first, bar(DAYS[21], "09:33", 103, 104, 101, 103)],
                    setup="TS")[1] == []


def test_ts_missing_exit_and_censoring_are_integrity_failures():
    candles = pattern() + session(21, 103, 106, 101, 104)[:1]
    strategy, trades = execute(candles + session(22), setup="TS")
    assert trades[0].exit_time == bar(DAYS[22], "09:31", 105, 110, 100, 105).ts + M1.duration
    assert any(r["kind"] == "missing_exit_candle" for r in strategy.integrity_records())
    strategy, _ = execute(candles, setup="TS")
    assert any(r["kind"] == "censored_position" for r in strategy.integrity_records())


def test_ts_no_lookahead_every_prefix_and_one_position():
    candles = pattern() + session(21, 103, 106, 101, 104) + session(22)
    _, expected, expected_exits = feed(candles, setup="TS", ts_exit_sessions=2)
    assert len(expected) == len(expected_exits) == 1
    for n in range(1, len(candles) + 1):
        _, orders, exits = feed(candles[:n], setup="TS", ts_exit_sessions=2)
        cutoff = candles[n-1].ts + M1.duration
        assert orders == [x for x in expected if x[0] <= cutoff]
        assert exits == [x for x in expected_exits if x[0] <= cutoff]


@pytest.mark.parametrize("symbol", ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"])
def test_ts_fx_daily_clock_sunday_open_weekend_stubs_and_dst(symbol):
    strategy = DailyReversal(symbol, DailyReversalConfig(setup="TS"))
    candles = []
    for i in range(22):
        end = datetime.combine(DAYS[i], time(17), NY)
        start = end - timedelta(days=1) + M1.duration
        lo = 90 if i == 16 else (89 if i == 20 else 100)
        candles += [Candle(start.astimezone(UTC)-M1.duration, 105, 110, lo, 105),
                    Candle(end.astimezone(UTC)-M1.duration, 105, 105, 105, 105)]
    _, orders, exits = feed(candles, strategy)
    assert len(orders) == len(exits) == 1
    assert orders[0][0] == candles[-2].ts + M1.duration
    assert exits[0][0] == candles[-1].ts + M1.duration
    assert not strategy.integrity_records()
    for day, utc_hour in [(datetime(2026, 3, 9).date(), 21),
                          (datetime(2026, 11, 2).date(), 22)]:
        s = DailyReversal(symbol, DailyReversalConfig(setup="TS"))
        end = datetime.combine(day, time(17), NY)
        start = end - timedelta(days=1) + M1.duration
        weekend = start - timedelta(days=1)
        feed([Candle(weekend.astimezone(UTC)-M1.duration, 105, 110, 100, 105),
              Candle(start.astimezone(UTC)-M1.duration, 105, 110, 100, 105),
              Candle(end.astimezone(UTC)-M1.duration, 105, 105, 105, 105)], s)
        assert len(s._history) == 1
        assert end.astimezone(UTC).hour == utc_hour


@pytest.mark.parametrize("kwargs", [
    {"ts_lookback": 0}, {"ts_lookback": True}, {"ts_min_age": 0},
    {"ts_atr_period": 0}, {"ts_range_atr": float("nan")},
    {"ts_range_atr": 0}, {"ts_range_atr": True}, {"ts_exit_sessions": 3},
    {"ts_exit_sessions": True},
])
def test_ts_config_invalid(kwargs):
    with pytest.raises(ValueError):
        DailyReversalConfig(setup="TS", **kwargs)


def test_ts_grid_four_cells_and_defaults_preserve_e8():
    from backtester.tools import research_grid

    raw = tomllib.loads(Path("research/grids/daily_reversal_ts.toml").read_text())
    assert raw["symbols"] == ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "US500", "NAS100"]
    assert raw["min_trades"] == 150
    assert all(raw[k] is False for k in ("monkeys", "sensitivity", "entry_screen", "shocks"))
    spec = research_grid.load_grid("research/grids/daily_reversal_ts.toml")
    variants, size, sampled = research_grid.expand(spec)
    configs = [research_grid.variant_settings(spec, v).strategy for v in variants]
    assert size == 4 and not sampled
    assert [(c.ts_lookback, c.ts_exit_sessions) for c in configs] == [(20, 1), (20, 2), (55, 1), (55, 2)]
    assert all(c.setup == "TS" for c in configs)
    assert DailyReversalConfig().setup == "E8"


def test_ts_55_day_window_keeps_old_extreme_until_it_rolls_out():
    days = []
    day = date(2026, 1, 5)
    while len(days) < 57:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    candles = []
    for i, day in enumerate(days):
        low = 80 if i == 0 else (90 if i == 51 else (89 if i == 55 else 100))
        candles += [bar(day, "09:31", 105, 110, low, 105),
                    bar(day, "16:00", 105, 105, 105, 105)]
    assert len(feed(candles, setup="TS", ts_lookback=20)[1]) == 1
    assert feed(candles, setup="TS", ts_lookback=55)[1] == []
    # Signal undercuts the entire 55-day history, rather than merely the last 20.
    candles[110] = bar(days[55], "09:31", 105, 110, 79, 105)
    assert len(feed(candles, setup="TS", ts_lookback=55)[1]) == 1


def test_ts_range_filter_uses_prior_wilder_atr_and_includes_equality():
    prior = pattern()[:-2]
    strategy, _, _ = feed(prior, setup="TS")
    expected = 10 + (20 / 14) * (13 / 14) ** 3
    assert strategy._ts_atr == pytest.approx(expected)
    width = strategy._ts_atr * 3
    for excess, count in [(0, 1), (0.001, 0)]:
        candles = prior + session(20, 101, 110, 110 - width - excess, 101) + session(21)
        assert len(feed(candles, setup="TS")[1]) == count


def test_ts_partial_and_invalid_sessions_reset_history_and_atr():
    for broken in ([bar(DAYS[20], "09:32", 101, 110, 89, 101),
                    bar(DAYS[20], "16:00", 101, 101, 101, 101)],
                   [bar(DAYS[20], "09:31", 0, 0, 0, 0),
                    bar(DAYS[20], "16:00", 101, 101, 101, 101)]):
        strategy, orders, _ = feed(pattern()[:-2] + broken, setup="TS")
        assert not orders and not strategy._history
        assert strategy._ts_atr is None
        assert strategy.integrity_records()


def test_ts_nonfinite_atr_from_extreme_positive_prices_cannot_arm():
    candles = []
    for i in range(20):
        candles += session(i, 105, 1e308, 1 if i == 16 else 2, 105)
    candles += session(20, 105, 110, 0.5, 105) + session(21)
    assert feed(candles, setup="TS")[1] == []


def test_ts_dual_signal_skip_precedes_rejection_of_nonpositive_stop():
    # Both price patterns qualify; long stop is invalid with this extreme tick size.
    assert feed(pattern(high=121) + session(21), setup="TS", tick_size=100)[1] == []


@pytest.mark.parametrize("hold", [1, 2])
@pytest.mark.parametrize("short", [False, True])
def test_ts_fx_actual_one_two_rollovers_and_side_specific_swap(hold, short):
    # First M1 close=103, stop=88.99, so risk=14.01 in either mirrored direction.
    candles = pattern() + session(21, 103, 106, 101, 103)
    if hold == 2:
        candles += session(22, 104, 107, 102, 105)
    fx = []
    for i, candle in enumerate(candles):
        end = datetime.combine(DAYS[i // 2], time(17), NY)
        now = end if i % 2 else end - timedelta(days=1) + M1.duration
        fx.append(Candle(now.astimezone(UTC)-M1.duration, candle.open, candle.high,
                         candle.low, candle.close))
    if short:
        fx = [Candle(c.ts, 220-c.open, 220-c.low, 220-c.high, 220-c.close) for c in fx]
    costs = CostConfig(symbols={"EURUSD": SymbolCosts(
        0, 0, 1, swap_long_per_lot=-1, swap_short_per_lot=-2,
        swap_triple_weekday=4, tick_size=0.01)}, spread_table=None,
        conversion_adjustment=0, tp_penetration=0)
    strategy = DailyReversal("EURUSD", DailyReversalConfig(setup="TS", ts_exit_sessions=hold))
    trades = run_backtest(strategy, [CandleSeries("EURUSD", M1, fx)], EngineConfig(costs=costs))
    assert len(trades) == 1
    trade = trades[0]
    assert trade.exit_reason is ExitReason.SIGNAL
    assert trade.exit_time == fx[-1].ts + M1.duration
    assert trade.swap_r == pytest.approx(-hold * (2 if short else 1) / 14.01)
    assert not strategy.integrity_records()
