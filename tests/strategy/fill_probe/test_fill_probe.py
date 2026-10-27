"""Fill probe (test tool for the demo bot): entries on the interval minutes, alternating
direction, ATR stop / TP, time exit, one trade at a time, no lookahead. Not a researched
strategy. Spec: docs/strategy-fill-probe.md.

Flat fixture: every M1 candle is open = close = 100, high 101, low 99 -> true range 2, so the
Wilder ATR is exactly 2 once 14 candles exist: stop distance 3 x 2 = 6, TP at 1R = 6."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.engine.trade import ExitReason
from backtester.strategy.fill_probe.config import FillProbeConfig
from backtester.strategy.fill_probe.strategy import FillProbe

LONG, SHORT = Direction.BULLISH, Direction.BEARISH
M1 = Timeframe.M1
START = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)
NO_COSTS = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False))
FLAT = (100.0, 101.0, 99.0, 100.0)


def candles(n: int, ohlc=FLAT, start: datetime = START) -> list[Candle]:
    o, h, lo, c = ohlc
    return [Candle(ts=start + i * M1.duration, open=o, high=h, low=lo, close=c) for i in range(n)]


def hhmm(t: datetime) -> str:
    return t.strftime("%H:%M")


def new(**cfg) -> FillProbe:
    return FillProbe("TEST", FillProbeConfig(**cfg))


def drive(strategy: FillProbe, cs: list[Candle], on_order=None) -> list[tuple[datetime, object]]:
    """Feed the closed candles one by one; returns [(now, order)]. `on_order(strategy, order,
    now)` may free the trade."""
    series = CandleSeries("TEST", M1, cs)
    sent = []
    for i, c in enumerate(cs):
        now = c.ts + M1.duration
        for order in strategy.on_candle(now, {M1: series.view(i)}):
            sent.append((now, order))
            if on_order:
                on_order(strategy, order, now)
    return sent


def free_at_once(strategy, order, now):
    strategy.on_trade_closed(order.ref, None)


def test_declares_m1_and_warmup():
    s = new()
    assert s.base_timeframe is M1
    assert s.timeframes == (M1,)
    assert s.min_warmup_days == 1


def test_config_defaults_and_validation():
    c = FillProbeConfig()
    assert (c.interval_minutes, c.atr_period, c.stop_atr, c.target_r, c.max_hold_minutes) == (
        30, 14, 3.0, 1.0, 20,
    )  # fmt: skip
    for bad in (
        {"interval_minutes": 0},
        {"atr_period": 0},
        {"stop_atr": 0},
        {"target_r": -1},
        {"max_hold_minutes": 0},
    ):
        with pytest.raises(ValueError):
            FillProbeConfig(**bad)


def test_entries_only_on_interval_minutes():
    sent = drive(new(), candles(125), free_at_once)
    assert [hhmm(t) for t, _ in sent] == ["00:30", "01:00", "01:30", "02:00"]


def test_no_order_before_atr_exists():
    # the 14th candle closes at 00:14: at 00:05 / 00:10 there is no ATR yet
    assert drive(new(interval_minutes=5), candles(14), free_at_once) == []
    sent = drive(new(interval_minutes=5), candles(16), free_at_once)
    assert [hhmm(t) for t, _ in sent] == ["00:15"]


def test_direction_alternates_long_then_short():
    sent = drive(new(), candles(190), free_at_once)
    assert [o.direction for _, o in sent] == [LONG, SHORT, LONG, SHORT, LONG, SHORT]


def test_long_levels_from_hand_computed_atr():
    [(_, o)] = drive(new(), candles(31))
    assert o.direction is LONG
    assert o.entry == 100.0
    assert o.stop_loss == pytest.approx(94.0)  # 3 x ATR 2
    assert o.take_profit == pytest.approx(106.0)  # 1R
    assert o.confluence == "probe"
    assert o.reason == "fill probe long #1"


def test_short_mirrors_the_long():
    sent = drive(new(), candles(61), free_at_once)
    short = sent[1][1]
    assert short.direction is SHORT
    assert short.stop_loss == pytest.approx(106.0)
    assert short.take_profit == pytest.approx(94.0)
    assert short.reason == "fill probe short #2"


def test_target_r_scales_and_zero_means_no_take_profit():
    [(_, o)] = drive(new(target_r=2.0), candles(31))
    assert o.take_profit == pytest.approx(112.0)
    [(_, o)] = drive(new(target_r=0), candles(31))
    assert o.take_profit is None
    assert o.stop_loss == pytest.approx(94.0)


def test_atr_is_wilder_with_previous_close():
    # 14 candles with TR 2 (ATR 2), then a candle 91 low 90 high 92 after close 100 -> TR 10,
    # then 14 candles with TR 2: the entry is the close of the 30th candle (00:30)
    gap = Candle(START + 14 * M1.duration, 91.0, 92.0, 90.0, 91.0)
    cs = candles(14) + [gap] + candles(15, (91.0, 92.0, 90.0, 91.0), START + 15 * M1.duration)
    [(_, o)] = drive(new(), cs)
    atr = 2.0
    for tr in [10.0] + [2.0] * 15:
        atr = (atr * 13 + tr) / 14
    assert o.entry == 91.0
    assert o.stop_loss == pytest.approx(91.0 - 3.0 * atr)


def test_no_second_entry_while_open_until_freed():
    assert len(drive(new(), candles(125))) == 1  # never freed: only the 00:30 order

    s = new()
    series = CandleSeries("TEST", M1, cs := candles(125))
    times = []
    for i, c in enumerate(cs):
        now = c.ts + M1.duration
        times += [hhmm(now) for _ in s.on_candle(now, {M1: series.view(i)})]
        if hhmm(now) == "00:45":
            s.on_trade_closed(("fill_probe", 1), None)
    assert times == ["00:30", "01:00"]


def test_skipped_order_frees_but_alternation_continues():
    series = CandleSeries("TEST", M1, cs := candles(95))
    s = new()
    got = []
    for i, c in enumerate(cs):
        now = c.ts + M1.duration
        for o in s.on_candle(now, {M1: series.view(i)}):
            got.append(o.direction)
            if len(got) == 1:
                s.on_order_skipped(o.ref, now)  # skipped: the next one is the short
    assert got == [LONG, SHORT]


def test_skipped_order_blocks_nothing_but_open_one_does():
    s = new()
    series = CandleSeries("TEST", M1, cs := candles(95))
    n = 0
    for i, c in enumerate(cs):
        now = c.ts + M1.duration
        n += len(s.on_candle(now, {M1: series.view(i)}))  # 00:30 sent, never freed
    assert n == 1


def test_time_exit_after_max_hold_minutes():
    s = new(max_hold_minutes=20)
    series = CandleSeries("TEST", M1, cs := candles(60))
    ref, exit_at = None, None
    for i, c in enumerate(cs):
        now = c.ts + M1.duration
        orders = s.on_candle(now, {M1: series.view(i)})
        if orders:
            ref = orders[0].ref
        ex = s.exits()
        if ex and exit_at is None:
            assert ex == [ref]
            exit_at = now
    assert exit_at == START + timedelta(minutes=50)  # entered 00:30 + 20 minutes
    s.on_trade_closed(ref, None)
    assert s.exits() == []


def test_no_exit_when_nothing_open():
    s = new()
    drive(s, candles(10))
    assert s.exits() == []


def test_no_order_when_the_last_candle_does_not_close_at_now():
    series = CandleSeries("TEST", M1, cs := candles(30))  # candle 29 closes at 00:30
    s = new()
    for i in range(28):
        s.on_candle(cs[i].ts + M1.duration, {M1: series.view(i)})
    at_0030 = START + timedelta(minutes=30)
    # the newest candle of the view closed at 00:29: the market is closed at 00:30
    assert s.on_candle(at_0030, {M1: series.view(28)}) == []
    assert len(s.on_candle(at_0030, {M1: series.view(29)})) == 1


def test_no_lookahead_future_candles_never_change_earlier_orders():
    cs = [
        Candle(START + i * M1.duration, 100 + 0.1 * i, 101 + 0.1 * i, 99 + 0.1 * i, 100 + 0.1 * i)
        for i in range(200)
    ]
    short = drive(new(), cs[:100], free_at_once)
    long_ = drive(new(), cs, free_at_once)
    assert short
    assert len(long_) > len(short)
    assert long_[: len(short)] == short


def test_runs_through_the_engine_and_produces_several_trades():
    # quiet market: neither the stop (3 ATR) nor the TP is reached, the time exit closes
    cs = candles(60 * 6, (100.0, 100.5, 99.5, 100.0))
    trades = run_backtest(new(), [CandleSeries("TEST", M1, cs)], NO_COSTS)
    assert len(trades) >= 8
    assert [t.direction for t in trades[:4]] == [LONG, SHORT, LONG, SHORT]
    closed = trades[:-1]  # the last one ends with the data
    assert all(t.exit_reason is ExitReason.SIGNAL for t in closed)
    assert all(t.exit_time - t.entry_time == timedelta(minutes=20) for t in closed)
    assert all(t.entry_time.minute % 30 == 0 for t in trades)


def test_engine_take_profit_frees_the_strategy():
    # the long of 00:30 hits its TP (106) in the 00:31 candle; the short of 01:00 is a new trade
    cs = candles(31) + [Candle(START + 31 * M1.duration, 100.0, 107.0, 100.0, 100.0)]
    cs += candles(100, FLAT, START + 32 * M1.duration)
    trades = run_backtest(new(), [CandleSeries("TEST", M1, cs)], NO_COSTS)
    assert trades[0].exit_reason is ExitReason.TAKE_PROFIT
    assert trades[1].direction is SHORT
