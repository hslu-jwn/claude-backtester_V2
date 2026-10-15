"""The backtest loop. Spec: ARCHITECTURE.md › How a backtest steps through time,
ROADMAP.md › 3.1, strategy-session-zones.md › Stop loss.

Steps the strategy's base timeframe (5m for strategy 1) with `Replay`, so the strategy
gets exactly the views the chart replay shows. Per base candle i, `now` = its close time:

1. Open trades are checked against candle i's OHLC only (`OpenTrade.on_candle`: SL before
   TP when both are inside the candle; an order with two TPs closes in two parts, and the
   rest's SL may move to break-even after TP1, see engine/trade.py).
2. Break-even rule: the first candle closing at or after the first session start after a
   trade's entry decides. Break-even includes the costs: the level where a hit ends at 0R
   net (long: entry + spread + commission as a price distance). Close beyond that level ->
   the SL moves there from the next candle on; otherwise the original SL stays for good.
3. `strategy.on_candle(now, views)`; views of every declared timeframe, higher ones only
   with candles closed at `now`. The strategy owns and updates its detectors itself.
3b. `strategy.exits()`: the open trades whose `Order.ref` it names close at this candle's
   close (ExitReason.SIGNAL, costs as for any exit); `on_trade_closed` runs for each BEFORE
   the new orders are filled (stop-and-reverse, strategy 4). Unknown refs are ignored.
4. New orders are filled at candle i's close and managed from candle i + 1, unless the
   cost filter skips them (`CostConfig.max_cost_r`; `strategy.on_order_skipped`). A limit order
   (`Order.limit_fill`) is filled at its level inside candle i; in that candle only its SL
   counts (SL first, a TP there is not counted), then it is managed from candle i + 1.

Trades still open after the last candle are closed at its close (END_OF_DATA).
Output: closed trades in R, in entry order. `progress(done, total)` (optional) is called
every `progress_every` base candles and once at the end (ROADMAP 3.4: progress bar).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import datetime

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries, SeriesView
from backtester.engine.costs import CostConfig
from backtester.engine.replay import Replay
from backtester.engine.trade import ExitReason, OpenTrade, TradeResult
from backtester.sessions import DEFAULT_SESSIONS, SessionConfig, next_session_start
from backtester.strategy.base import Order, Strategy


@dataclass(frozen=True, slots=True)
class EngineConfig:
    costs: CostConfig = field(default_factory=CostConfig)
    # SL to break-even at the next session start if in profit (strategy-session-zones.md
    # › Stop loss)
    break_even_at_next_session: bool = True
    sessions: SessionConfig = DEFAULT_SESSIONS


DEFAULT_ENGINE = EngineConfig()

Progress = Callable[[int, int], None]  # (base candles done, total)


def run_backtest(
    strategy: Strategy,
    series: Sequence[CandleSeries],
    config: EngineConfig = DEFAULT_ENGINE,
    progress: Progress | None = None,
) -> list[TradeResult]:
    """Run `strategy` over `series` (one per timeframe it declares, same symbol)."""
    return Backtest(strategy, series, config).run(progress)


class Backtest:
    def __init__(
        self,
        strategy: Strategy,
        series: Sequence[CandleSeries],
        config: EngineConfig = DEFAULT_ENGINE,
    ):
        by_tf = {s.timeframe: s for s in series}
        if len(by_tf) != len(series):
            raise ValueError("two series with the same timeframe")
        missing = set(strategy.timeframes) - set(by_tf)
        if strategy.base_timeframe not in by_tf:
            missing.add(strategy.base_timeframe)
        if missing:
            raise ValueError(f"no series for {sorted(tf.name for tf in missing)}")
        self._strategy = strategy
        self._config = config
        self._higher = tuple(tf for tf in strategy.timeframes if tf is not strategy.base_timeframe)
        self._replay = Replay(by_tf[strategy.base_timeframe], [by_tf[tf] for tf in self._higher])

    def run(self, progress: Progress | None = None, progress_every: int = 500) -> list[TradeResult]:
        replay = self._replay
        open_trades: list[OpenTrade] = []
        closed: list[TradeResult] = []
        total = len(replay)
        for cursor in range(total):
            if progress is not None and cursor and cursor % progress_every == 0:
                progress(cursor, total)
            view = replay.view(cursor)
            candle = view.current
            now = replay.close_time(cursor)
            still_open = []
            for trade in open_trades:
                trade.track_excursion(candle)
                trade.on_candle(candle, now)
                if trade.is_closed:
                    result = self._result(trade)
                    closed.append(result)
                    self._strategy.on_trade_closed(trade.ref, result)
                else:
                    self._check_break_even(trade, candle, now)
                    still_open.append(trade)
            open_trades = still_open
            views = self._views(cursor, view)
            orders = self._strategy.on_candle(now, views)
            open_trades = self._signal_exits(open_trades, candle, now, closed)
            for order in orders:
                trade = self._fill(order, candle, now)
                if self._config.costs.too_expensive(trade.symbol, trade.risk, trade.entry_time):
                    self._strategy.on_order_skipped(order.ref, now)
                    continue
                if order.limit_fill:
                    trade.on_fill_candle(candle, now)
                if trade.is_closed:
                    result = self._result(trade)
                    closed.append(result)
                    self._strategy.on_trade_closed(trade.ref, result)
                else:
                    open_trades.append(trade)
        if open_trades:
            last = replay.view(len(replay) - 1).current
            now = replay.close_time(len(replay) - 1)
            for trade in open_trades:
                trade.close_all(last, now, last.close, ExitReason.END_OF_DATA)
                closed.append(self._result(trade))
        if progress is not None:
            progress(total, total)
        closed.sort(key=lambda t: t.entry_time)
        return closed

    def _signal_exits(
        self, open_trades: list[OpenTrade], candle: Candle, now: datetime, closed: list
    ) -> list[OpenTrade]:
        """Close the trades the strategy asked for (`Strategy.exits`) at this close."""
        refs = self._strategy.exits()
        if not refs:
            return open_trades
        keep = []
        for trade in open_trades:
            if trade.ref is not None and trade.ref in refs:
                trade.close_all(candle, now, candle.close, ExitReason.SIGNAL)
                result = self._result(trade)
                closed.append(result)
                self._strategy.on_trade_closed(trade.ref, result)
            else:
                keep.append(trade)
        return keep

    def _views(self, cursor: int, view: SeriesView) -> dict[Timeframe, SeriesView | None]:
        views: dict[Timeframe, SeriesView | None] = {self._replay.timeframe: view}
        for tf in self._higher:
            views[tf] = self._replay.higher_view(cursor, tf)
        return views

    def _fill(self, order: Order, candle: Candle, now: datetime) -> OpenTrade:
        """Enter at the close of the current base candle (spec: "enter at that close"), or
        for a limit order at its level, which the candle must have traded through."""
        entry = order.entry if order.limit_fill else candle.close
        if order.limit_fill:
            if not candle.low <= entry <= candle.high:
                raise ValueError(f"limit entry {entry} outside the candle at {now}")
        elif not math.isclose(order.entry, entry):
            raise ValueError(f"order entry {order.entry} is not the candle close {entry} at {now}")
        sign = 1 if order.direction is Direction.BULLISH else -1
        if sign * (entry - order.stop_loss) <= 0:
            raise ValueError(f"{order.direction.value} SL {order.stop_loss} not beyond {entry}")
        if order.take_profit is None:
            if order.take_profit_2 is not None:
                raise ValueError("TP2 without a TP1")
        elif sign * (order.take_profit - entry) <= 0:
            raise ValueError(f"{order.direction.value} TP {order.take_profit} not beyond {entry}")
        if order.take_profit_2 is not None:
            if sign * (order.take_profit_2 - order.take_profit) <= 0:
                raise ValueError(f"TP2 {order.take_profit_2} not beyond TP1 {order.take_profit}")
            if not 0 < order.tp1_share < 1:
                raise ValueError(f"tp1_share {order.tp1_share} must be in (0, 1) with a TP2")
        if order.take_profit_3 is not None:
            tp2 = order.take_profit_2
            if tp2 is None or sign * (order.take_profit_3 - tp2) <= 0:
                raise ValueError(f"TP3 {order.take_profit_3} not beyond TP2 {tp2}")
            if not order.tp2_share or 1 - order.tp1_share - order.tp2_share <= 1e-12:
                raise ValueError("tp1_share + tp2_share must leave a share for TP3")
        symbol = self._replay.symbol
        spread = self._config.costs.spread(symbol, now)
        check = None
        if self._config.break_even_at_next_session and self._strategy.uses_session_break_even:
            check = next_session_start(now, self._config.sessions).start
        return OpenTrade(
            symbol=symbol,
            direction=order.direction,
            entry_time=now,
            entry_candle=candle.ts,
            entry=entry,
            entry_fill=entry + spread if sign > 0 else entry,
            initial_stop=order.stop_loss,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            break_even_check=check,
            break_even_level=entry + sign * self._config.costs.break_even_offset(symbol, now),
            tags=order.tags,
            reason=order.reason,
            confluence=order.confluence,
            take_profit_2=order.take_profit_2,
            tp1_share=order.tp1_share if order.take_profit_2 is not None else 1.0,
            break_even_after_tp1=order.break_even_after_tp1,
            take_profit_3=order.take_profit_3,
            tp2_share=order.tp2_share if order.take_profit_3 is not None else None,
            ref=order.ref,
            spread=spread,
        )

    @staticmethod
    def _check_break_even(trade: OpenTrade, candle: Candle, now: datetime) -> None:
        if trade.break_even_check is None or now < trade.break_even_check:
            return
        trade.break_even_check = None  # only the next session start counts
        if trade.sign * (candle.close - trade.break_even_level) > 0:
            trade.move_to_break_even(now)

    def _result(self, trade: OpenTrade) -> TradeResult:
        costs = self._config.costs
        swap_r = costs.swap_r(
            trade.symbol, trade.direction, trade.risk, trade.entry_time,
            [(p.share, p.time) for p in trade.parts],
        )  # fmt: skip
        return trade.result(costs.commission_r(trade.symbol, trade.risk), swap_r)
