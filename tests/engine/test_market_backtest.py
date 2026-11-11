"""Market capability is opt-in; execution remains owned by the primary."""

from datetime import UTC, datetime, timedelta

import pytest
from conftest import build_series

from backtester.core.market import ReferenceInput
from backtester.core.models import Direction
from backtester.core.models import Timeframe as TF
from backtester.engine.backtest import Backtest, EngineConfig
from backtester.engine.costs import CostConfig
from backtester.engine.market_replay import MarketReplay
from backtester.engine.trade import ExitReason
from backtester.strategy.base import MarketAwareStrategy, Order

START = datetime(2026, 1, 5, 10, tzinfo=UTC)
MIN = timedelta(minutes=1)
CONFIG = EngineConfig(costs=CostConfig(spread_enabled=False, commission_enabled=False),
                      break_even_at_next_session=False)


class Observer(MarketAwareStrategy):
    base_timeframe = TF.M5
    timeframes = (TF.M5,)
    uses_session_break_even = False

    def __init__(self):
        self.seen = []
        self.processed = []
        self.orders = []
        self.skipped = []

    def on_order_skipped(self, ref, now):
        self.skipped.append((ref, now))

    def on_market_candle(self, now, views, market):
        self.seen.append(market)
        for symbol in market.views:
            view = market.views[symbol][TF.M1]
            for i in market.newly_closed[symbol][TF.M1]:
                self.processed.append((symbol, view.at(i).current.ts))
        price = views[TF.M5].current.close
        orders = [Order(Direction.BULLISH, price, price - 2, price + 4)]
        self.orders.append((now, market.ready, orders))
        return orders


def run(future=False, reverse=False):
    refs = (ReferenceInput("B", "b", (TF.M1,), max_age=MIN),
            ReferenceInput("C", "c", (TF.M1,), max_age=MIN))
    histories = [build_series([(100, 101, 99, 100)] * (30 if future else 10),
                             TF.M1, START, s) for s in ("B", "C")]
    primary = build_series([(100, 101, 99, 100), (100, 105, 97, 100)], TF.M5, START)
    observer = Observer()
    engine = Backtest(observer, [primary], CONFIG,
                      market=MarketReplay(refs, histories[::-1] if reverse else histories))
    return observer, engine.run()


def test_future_reference_append_mapping_order_cannot_change_orders_fills_or_r():
    first, trades = run()
    for future, reverse in ((True, False), (True, True), (False, True)):
        other, other_trades = run(future, reverse)
        assert other.orders == first.orders
        assert other_trades == trades
        assert other.processed == first.processed
    assert len(first.seen) == 2  # no reference-only callbacks
    assert len(first.processed) == 20 and len(set(first.processed)) == 20
    assert trades[0].exit_reason is ExitReason.STOP_LOSS
    assert trades[0].r_gross == -1


def test_missing_reference_blocks_new_entries_but_primary_stop_still_runs():
    cfg = ReferenceInput("B", "b", (TF.M1,), max_age=MIN)
    ref = build_series([(100, 101, 99, 100)] * 5, TF.M1, START, "B")
    primary = build_series([(100, 101, 99, 100), (100, 101, 97, 100)], TF.M5, START)
    strategy = Observer()
    engine = Backtest(strategy, [primary], CONFIG, market=MarketReplay((cfg,), [ref]))
    trades = engine.run()
    assert len(trades) == 1 and trades[0].exit_reason is ExitReason.STOP_LOSS
    assert len(strategy.seen) == 2 and not strategy.seen[-1].ready
    assert engine.market_blocked and engine.market_blocked[0][0] == START + 10 * MIN
    assert strategy.skipped == [(None, START + 10 * MIN)]


def test_capability_requires_provider_and_legacy_rejects_provider():
    from backtester.strategy.base import Strategy

    class Legacy(Strategy):
        base_timeframe = TF.M5
        timeframes = (TF.M5,)

        def on_candle(self, now, views):
            return []

    primary = build_series([(100, 101, 99, 100)], TF.M5, START)
    with pytest.raises(ValueError, match="market"):
        Backtest(Observer(), [primary], CONFIG)
    with pytest.raises(ValueError, match="market"):
        Backtest(Legacy(), [primary], CONFIG, market=MarketReplay((), []))


@pytest.mark.parametrize("changed", ["B", "C"])
def test_each_reference_future_values_do_not_change_prefix(changed):
    refs = tuple(ReferenceInput(s, s, (TF.M1,), max_age=MIN) for s in ("B", "C"))
    primary = build_series([(100, 101, 99, 100)] * 3, TF.M5, START)
    histories = [build_series([(100, 101, 99, 100)] * 10 +
                             ([(500, 900, 1, 800)] * 5 if s == changed else
                              [(100, 101, 99, 100)] * 5), TF.M1, START, s)
                 for s in ("B", "C")]
    strategy = Observer()
    Backtest(strategy, [primary], CONFIG, market=MarketReplay(refs, histories)).run()
    baseline, _ = run()
    assert strategy.orders[:2] == baseline.orders
    assert strategy.processed[:20] == baseline.processed


def test_new_mode_rejects_non_utc_primary_and_reference_to_primary():
    from zoneinfo import ZoneInfo

    primary = build_series([(100, 101, 99, 100)], TF.M5,
                           START.astimezone(ZoneInfo("America/New_York")))
    with pytest.raises(ValueError, match="UTC"):
        Backtest(Observer(), [primary], CONFIG, market=MarketReplay((), []))
    primary = build_series([(100, 101, 99, 100)], TF.M5, START)
    cfg = ReferenceInput("TEST", "self", (TF.M1,), max_age=MIN)
    with pytest.raises(ValueError, match="execution"):
        Backtest(Observer(), [primary], CONFIG,
                 market=MarketReplay((cfg,), [build_series([], TF.M1, START)]))
