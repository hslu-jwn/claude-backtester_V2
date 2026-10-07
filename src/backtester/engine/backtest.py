"""The backtest loop. Spec: ARCHITECTURE.md › How a backtest steps through time,
ROADMAP.md › 3.1, strategy-session-zones.md › Stop loss.

Steps the strategy's base timeframe (5m for strategy 1) with `Replay`, so the strategy
gets exactly the views the chart replay shows. Per base candle i, `now` = its close time:

1. Open trades are checked against candle i's OHLC only (`OpenTrade.exit_on`: SL before
   TP when both are inside the candle).
2. Break-even rule: the first candle closing at or after the first session start after a
   trade's entry decides. Close in profit (beyond the entry on the chart) -> the SL moves
   to the entry price from the next candle on; otherwise the original SL stays for good.
3. `strategy.on_candle(now, views)`; views of every declared timeframe, higher ones only
   with candles closed at `now`. The strategy owns and updates its detectors itself.
4. New orders are filled at candle i's close and managed from candle i + 1.

Trades still open after the last candle are closed at its close (END_OF_DATA).
Output: closed trades in R, in entry order.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
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
    # strategy-session-zones.md › Stop loss: SL to break-even at the next session start
    break_even_at_next_session: bool = True
    sessions: SessionConfig = DEFAULT_SESSIONS


DEFAULT_ENGINE = EngineConfig()


def run_backtest(
    strategy: Strategy,
    series: Sequence[CandleSeries],
    config: EngineConfig = DEFAULT_ENGINE,
) -> list[TradeResult]:
    """Run `strategy` over `series` (one per timeframe it declares, same symbol)."""
    return Backtest(strategy, series, config).run()


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

    def run(self) -> list[TradeResult]:
        replay = self._replay
        open_trades: list[OpenTrade] = []
        closed: list[TradeResult] = []
        for cursor in range(len(replay)):
            view = replay.view(cursor)
            candle = view.current
            now = replay.close_time(cursor)
            still_open = []
            for trade in open_trades:
                trade.track_excursion(candle)
                hit = trade.exit_on(candle)
                if hit is None:
                    self._check_break_even(trade, candle, now)
                    still_open.append(trade)
                else:
                    closed.append(self._close(trade, now, candle, *hit))
            open_trades = still_open
            views = self._views(cursor, view)
            for order in self._strategy.on_candle(now, views):
                open_trades.append(self._fill(order, candle, now))
        if open_trades:
            last = replay.view(len(replay) - 1).current
            now = replay.close_time(len(replay) - 1)
            for trade in open_trades:
                closed.append(self._close(trade, now, last, last.close, ExitReason.END_OF_DATA))
        closed.sort(key=lambda t: t.entry_time)
        return closed

    def _views(self, cursor: int, view: SeriesView) -> dict[Timeframe, SeriesView | None]:
        views: dict[Timeframe, SeriesView | None] = {self._replay.timeframe: view}
        for tf in self._higher:
            views[tf] = self._replay.higher_view(cursor, tf)
        return views

    def _fill(self, order: Order, candle: Candle, now: datetime) -> OpenTrade:
        """Enter at the close of the current base candle (spec: "enter at that close")."""
        entry = candle.close
        if not math.isclose(order.entry, entry):
            raise ValueError(f"order entry {order.entry} is not the candle close {entry} at {now}")
        sign = 1 if order.direction is Direction.BULLISH else -1
        if sign * (entry - order.stop_loss) <= 0:
            raise ValueError(f"{order.direction.value} SL {order.stop_loss} not beyond {entry}")
        if sign * (order.take_profit - entry) <= 0:
            raise ValueError(f"{order.direction.value} TP {order.take_profit} not beyond {entry}")
        symbol = self._replay.symbol
        spread = self._config.costs.spread(symbol)
        check = None
        if self._config.break_even_at_next_session:
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
            tags=order.tags,
            reason=order.reason,
        )

    @staticmethod
    def _check_break_even(trade: OpenTrade, candle: Candle, now: datetime) -> None:
        if trade.break_even_check is None or now < trade.break_even_check:
            return
        trade.break_even_check = None  # only the next session start counts
        if trade.r_at(candle.close) > 0:
            trade.stop_loss = trade.entry
            trade.break_even_time = now

    def _close(
        self, trade: OpenTrade, now: datetime, candle: Candle, price: float, reason: ExitReason
    ) -> TradeResult:
        costs = self._config.costs
        return trade.close(
            exit_time=now,
            exit_candle=candle.ts,
            exit_price=price,
            reason=reason,
            spread=costs.spread(trade.symbol),
            commission_r=costs.commission_r(trade.symbol, trade.risk),
        )
