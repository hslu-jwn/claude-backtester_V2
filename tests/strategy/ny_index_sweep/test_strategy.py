"""Strategy 2 end to end on random-walk weeks: every decision is checked against the spec's
rules (strategy-ny-indices.md, with the user's answers of 2026-10-11), and no decision
depends on later candles.

The walk: 1m candles Monday to Friday around the clock (NAS100 doji threshold), with
5m / 15m / 1h (UTC) and 4h (New York, closes 02:00, 06:00, ... ET) built from them.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pytest

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.backtest import EngineConfig, run_backtest
from backtester.engine.costs import CostConfig
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
from backtester.strategy.ny_index_sweep.frames import beyond, candle_open
from backtester.strategy.ny_index_sweep.strategy import NyIndexSweep
from backtester.strategy.ny_index_sweep.windows import Window

M1, M5, M15, H1, H4 = Timeframe.M1, Timeframe.M5, Timeframe.M15, Timeframe.H1, Timeframe.H4
START = datetime(2026, 9, 7, tzinfo=UTC)  # Monday
NO_COSTS = EngineConfig(
    costs=CostConfig(spread_enabled=False, commission_enabled=False),
    break_even_at_next_session=False,
)


def walk(days: int, seed: int) -> list[Candle]:
    rng = random.Random(seed)
    out, price, t, drift = [], 20000.0, START, 0.0
    while len(out) < days * 1440:
        if t.weekday() < 5:
            if rng.random() < 0.01:
                drift = rng.gauss(0, 1.5)  # trends of a few hours
            o = price
            c = o + drift + rng.gauss(0, 6.0)
            out.append(
                Candle(t, o, max(o, c) + abs(rng.gauss(0, 3)), min(o, c) - abs(rng.gauss(0, 3)), c)
            )
            price = c
        t += timedelta(minutes=1)
    return out


def aggregate(m1: list[Candle], tf: Timeframe) -> list[Candle]:
    buckets: dict[datetime, list[Candle]] = {}
    for c in m1:
        buckets.setdefault(candle_open(tf, c.ts), []).append(c)
    return [
        Candle(ts, cs[0].open, max(c.high for c in cs), min(c.low for c in cs), cs[-1].close)
        for ts, cs in buckets.items()
    ]


def series(m1: list[Candle], until: datetime | None = None) -> list[CandleSeries]:
    """Every timeframe's candles, only those closed by `until` (a cut of the history)."""
    out = []
    for tf in NyIndexSweep.timeframes:
        candles = m1 if tf is M1 else aggregate(m1, tf)
        if until is not None:
            candles = [c for c in candles if c.ts + tf.duration <= until]
        out.append(CandleSeries("NAS100", tf, candles))
    return out


def run(m1, until=None, config=None):
    strategy = NyIndexSweep("NAS100", config)
    trades = run_backtest(strategy, series(m1, until), NO_COSTS)
    return strategy, trades


@pytest.fixture(scope="module")
def week():
    m1 = walk(20, seed=2)
    strategy, trades = run(m1)
    return m1, strategy, trades


def summary(decisions):
    return [
        (d.signal.at, d.signal.close, d.signal.z3.box, d.order and d.order.stop_loss,
         d.order and d.order.take_profit, d.rejected)
        for d in decisions
    ]  # fmt: skip


def test_the_walk_gives_orders_in_both_windows_and_directions(week):
    _, strategy, trades = week
    orders = [d for d in strategy.decisions if d.order is not None]
    assert len(orders) >= 4 and len(trades) == len(orders)
    assert {d.signal.setup.window.kind for d in orders} == {Window.AM, Window.PM}
    assert {d.signal.direction for d in orders} == {Direction.BULLISH, Direction.BEARISH}


def test_every_decision_follows_the_rules(week):
    _, strategy, _ = week
    cfg, frames = strategy.config, strategy.frames
    per_window: dict[tuple, int] = {}
    for d in strategy.decisions:
        s, setup = d.signal, d.signal.setup
        w, route, bos = setup.window, setup.route, s.bos
        # inside the window, in the bias direction frozen at its start
        assert w.start < s.at <= w.end
        bias_tf = H4 if w.kind is Window.AM else M15
        assert s.direction is setup.direction is frames[bias_tf].trend_at(w.start)
        if w.kind is Window.AM:
            same = frames[H1].trend_at(w.start) is setup.direction
            assert (route.setup_tf, route.entry_tf) == ((M5, M1) if same else (M15, M5))
        # the sweep took a level; the setup-TF BoS came in time, after the extreme
        assert beyond(s.direction, setup.extreme, setup.level)
        assert setup.extreme_ts < w.end and bos.confirmed_at > w.start
        deadline = candle_open(setup.sweep_tf, setup.extreme_ts) + setup.sweep_tf.duration * (
            1 + route.bos_within
        )
        assert setup.extreme_ts + M1.duration <= bos.confirmed_at <= deadline
        assert bos.direction is s.direction
        # the 3rd confluence: in the BoS move by time (or created by the BoS), tapped in time
        z3 = s.z3.box
        assert z3.direction is s.direction and z3.created_at <= bos.confirmed_at
        assert z3.created_at == bos.confirmed_at or s.z3.start_ts >= candle_open(
            route.conf_tf, setup.extreme_ts
        )
        assert (
            bos.confirmed_at
            < s.tap_at
            <= bos.confirmed_at + route.setup_tf.duration * cfg.tap_timeout
        )
        # entry after the tap, at or after the entry-TF BoS
        assert s.entry_bos.confirmed_at >= s.tap_at and s.at >= s.entry_bos.confirmed_at
        if d.order is not None:
            o, sign = d.order, 1 if s.direction is Direction.BULLISH else -1
            assert sign * (o.entry - o.stop_loss) > 0
            tps = [p for p in (o.take_profit, o.take_profit_2, o.take_profit_3) if p is not None]
            assert all(sign * (b - a) > 0 for a, b in zip([o.entry, *tps], tps, strict=False))
            assert sign * (tps[0] - o.entry) / abs(o.entry - o.stop_loss) >= cfg.min_tp1_r - 1e-9
            key = (w.trading_date, w.kind)
            per_window[key] = per_window.get(key, 0) + 1
    assert all(n <= cfg.max_trades_per_session for n in per_window.values())


def test_no_lookahead_a_cut_history_gives_the_same_decisions_up_to_the_cut(week):
    m1, strategy, _ = week
    full = summary(strategy.decisions)
    for days in (5, 12):
        cut = START + timedelta(days=days, hours=17)
        short, _ = run([c for c in m1 if c.ts + M1.duration <= cut], cut)
        assert summary(short.decisions) == [x for x in full if x[0] <= cut]


def test_entry_tf_confluence_off_enters_at_the_entry_tf_bos_close(week):
    m1, _, _ = week
    strategy, _ = run(m1, config=NyIndexSweepConfig(entry_tf_confluence=False))
    assert strategy.decisions
    for d in strategy.decisions:
        assert d.signal.entry_zone is None and d.signal.at == d.signal.entry_bos.confirmed_at
