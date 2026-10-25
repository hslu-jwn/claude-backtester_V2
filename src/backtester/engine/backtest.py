"""The backtest loop. Spec: ARCHITECTURE.md › How a backtest steps through time,
ROADMAP.md › 3.1, strategy-session-zones.md › Stop loss.

Steps the strategy's base timeframe (5m for strategy 1) with `Replay`, so the strategy
gets exactly the views the chart replay shows. Per base candle i, `now` = its close time:

1. Open trades are checked against candle i's OHLC only (`OpenTrade.on_candle`: SL before
   TP when both are inside the candle; an order with two TPs closes in two parts, and the
   rest's SL may move to break-even after TP1, see engine/trade.py). The optional
   M1 resolution follows ARCHITECTURE.md > Intrabar resolution after this base close.
2. Break-even rule: the first candle closing at or after the first session start after a
   trade's entry decides. Break-even includes the costs: the level where a hit ends at 0R
   net (solved using the entry fill, exit commission and slippage). Close beyond that level ->
   the SL moves there from the next candle on; otherwise the original SL stays for good.
3. `strategy.on_candle(now, views)`; views of every declared timeframe, higher ones only
   with candles closed at `now`. The strategy owns and updates its detectors itself.
3b. `strategy.exits()`: the open trades whose `Order.ref` it names close at this candle's
   close (ExitReason.SIGNAL, costs as for any exit); `on_trade_closed` runs for each BEFORE
   the new orders are filled (stop-and-reverse, strategy 4). Unknown refs are ignored.
4. New orders are filled at candle i's close and managed from candle i + 1, unless the
   cost filter skips them (`CostConfig.max_cost_r`; `strategy.on_order_skipped`). A limit order
   (`Order.limit_fill`) must be in the previous step's `pending_limit_orders` snapshot.
   It is filled at its level inside candle i; in that candle only its SL counts (SL first,
   a TP there is not counted), then it is managed from candle i + 1.

Trades still open after the last candle are closed at its close (END_OF_DATA).
Output: closed trades in R, in entry order. `progress(done, total)` (optional) is called
every `ProgressThrottle.every_candles` base candles or every `every_seconds`, whichever comes
first, and once at the end (ROADMAP 3.4 / 7.6: progress bar).
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries, SeriesView
from backtester.engine.costs import CostConfig
from backtester.engine.replay import Replay
from backtester.engine.ticks import TickRoundingStats, round_level
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
    # ambiguous candles: m1 replay (default set by the user 2026-10-24) or sl_first (legacy)
    intrabar: str = "m1"

    def __post_init__(self) -> None:
        if self.intrabar not in ("sl_first", "m1"):
            raise ValueError("intrabar must be sl_first or m1")


DEFAULT_ENGINE = EngineConfig()


@dataclass(frozen=True, slots=True)
class ProgressThrottle:
    """When `Backtest.run` reports progress: every `every_candles` base candles or after
    `every_seconds`, whichever comes first (short runs move as smoothly as long ones). The
    clock is read only every `clock_check_candles` candles, so it costs nothing measurable."""

    every_candles: int = 500
    every_seconds: float = 0.2
    clock_check_candles: int = 16


DEFAULT_THROTTLE = ProgressThrottle()

Progress = Callable[[int, int], None]  # (base candles done, total)
IntrabarSource = Callable[[str, datetime, datetime], Sequence[Candle]]


def run_backtest(
    strategy: Strategy,
    series: Sequence[CandleSeries],
    config: EngineConfig = DEFAULT_ENGINE,
    progress: Progress | None = None,
    *,
    intrabar_source: IntrabarSource | None = None,
    tick_rounding: TickRoundingStats | None = None,
    diagnostics_start: datetime | None = None,
) -> list[TradeResult]:
    """Run `strategy` over `series` (one per timeframe it declares, same symbol)."""
    return Backtest(
        strategy,
        series,
        config,
        intrabar_source=intrabar_source,
        tick_rounding=tick_rounding,
        diagnostics_start=diagnostics_start,
    ).run(progress)


class Backtest:
    def __init__(
        self,
        strategy: Strategy,
        series: Sequence[CandleSeries],
        config: EngineConfig = DEFAULT_ENGINE,
        *,
        intrabar_source: IntrabarSource | None = None,
        tick_rounding: TickRoundingStats | None = None,
        diagnostics_start: datetime | None = None,
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
        self._intrabar_source = intrabar_source
        self.tick_rounding = tick_rounding if tick_rounding is not None else TickRoundingStats()
        self._diagnostics_start = diagnostics_start
        strategy.limit_fill_check = (
            self._limit_fill_allowed
            if config.costs.tp_penetration or config.costs.round_to_tick
            else None
        )
        self._higher = tuple(tf for tf in strategy.timeframes if tf is not strategy.base_timeframe)
        self._replay = Replay(by_tf[strategy.base_timeframe], [by_tf[tf] for tf in self._higher])

    def run(
        self,
        progress: Progress | None = None,
        throttle: ProgressThrottle = DEFAULT_THROTTLE,
        clock: Callable[[], float] = time.monotonic,
    ) -> list[TradeResult]:
        replay = self._replay
        last_step, last_time = 0, clock() if progress is not None else 0.0
        open_trades: list[OpenTrade] = []
        pending_limits: list[Order] = []
        closed: list[TradeResult] = []
        total = len(replay)
        for cursor in range(total):
            if progress is not None and cursor:
                due = cursor - last_step >= throttle.every_candles
                if not due and cursor % throttle.clock_check_candles == 0:
                    due = clock() - last_time >= throttle.every_seconds
                if due:
                    progress(cursor, total)
                    last_step, last_time = cursor, clock()
            view = replay.view(cursor)
            candle = view.current
            now = replay.close_time(cursor)
            still_open = []
            for trade in open_trades:
                self._manage_candle(trade, candle, now)
                if trade.is_closed:
                    result = self._result(trade)
                    closed.append(result)
                    self._strategy.on_trade_closed(trade.ref, result)
                else:
                    self._check_break_even(trade, candle, now)
                    still_open.append(trade)
            open_trades = still_open
            views = self._views(now, view)
            orders = self._strategy.on_candle(now, views)
            open_trades = self._signal_exits(open_trades, candle, now, closed)
            for order in orders:
                filled = self._fill(order, candle, now, pending_limits)
                if filled is None:
                    continue
                trade, placed = filled
                if self._config.costs.too_expensive(
                    trade.symbol, trade.risk, trade.entry_time, trade.entry, trade.entry_fill
                ):
                    self._strategy.on_order_skipped(order.ref, now)
                    continue
                if order.limit_fill:
                    self._manage_candle(trade, candle, now, placed=placed)
                if trade.is_closed:
                    result = self._result(trade)
                    closed.append(result)
                    self._strategy.on_trade_closed(trade.ref, result)
                else:
                    open_trades.append(trade)
            pending_limits = list(self._strategy.pending_limit_orders())
        if open_trades:
            last = replay.view(len(replay) - 1).current
            now = replay.close_time(len(replay) - 1)
            for trade in open_trades:
                trade.close_all(last, now, last.close, ExitReason.END_OF_DATA)
                result = self._result(trade)
                closed.append(result)
                self._strategy.on_trade_closed(trade.ref, result)
        if progress is not None:
            progress(total, total)
        closed.sort(key=lambda t: t.entry_time)
        return closed

    def _manage_candle(
        self, trade: OpenTrade, candle: Candle, now: datetime, *, placed: Order | None = None
    ) -> None:
        """Spec: ARCHITECTURE.md > Intrabar resolution. Default execution stays intact."""
        ambiguous = self._replay.timeframe is not Timeframe.M1 and trade.ambiguous(
            candle, limit_fill=placed is not None
        )
        if ambiguous:
            trade.intrabar_ambiguous += 1
            if self._config.intrabar == "m1":
                minutes = self._minutes(candle, now)
                if minutes and self._replay_minutes(trade, minutes, placed=placed):
                    return
                trade.intrabar = "fallback"
                trade.intrabar_fallbacks += 1
        if placed is not None:
            trade.on_fill_candle(candle, now)
        else:
            trade.track_excursion(candle)
            trade.on_candle(candle, now)

    def _minutes(self, candle: Candle, now: datetime) -> list[Candle]:
        """Validate the whole interval before mutating a position; never replay future data."""
        if self._intrabar_source is None:
            return []
        duration = Timeframe.M1.duration
        minutes = [
            c
            for c in self._intrabar_source(self._replay.symbol, candle.ts, now)
            if candle.ts <= c.ts and c.ts + duration <= now
        ]
        expected = int((now - candle.ts) / duration)
        if len(minutes) != expected or any(
            c.ts != candle.ts + i * duration for i, c in enumerate(minutes)
        ):
            return []
        return minutes

    def _replay_minutes(
        self, trade: OpenTrade, minutes: Sequence[Candle], *, placed: Order | None = None
    ) -> bool:
        """Spec: ARCHITECTURE.md > Intrabar resolution; strategies never see this replay."""
        first = 0
        if placed is not None:
            threshold = placed.entry - trade.sign * trade.tp_penetration * trade.spread
            first = next(
                (
                    i
                    for i, minute in enumerate(minutes)
                    if trade.sign * ((minute.low if trade.sign > 0 else minute.high) - threshold)
                    <= 0
                ),
                -1,
            )
            if first < 0:
                return False  # inconsistent M1 coverage: preserve the base fill atomically
            trade.entry_time = minutes[first].ts + Timeframe.M1.duration
        before = len(trade.parts)
        for i in range(first, len(minutes)):
            minute = minutes[i]
            now = minute.ts + Timeframe.M1.duration
            trade.track_excursion(minute)
            if placed is not None and i == first:
                trade.on_fill_candle(minute, now)
            else:
                trade.on_candle(minute, now, intrabar=True)
            if trade.is_closed:
                break
        if len(trade.parts) > before:
            tp_first = trade.parts[before].reason is ExitReason.TAKE_PROFIT
            trade.intrabar_tp_first += int(tp_first)
            trade.intrabar_sl_first += int(not tp_first)
            if not trade.intrabar:
                trade.intrabar = "tp_first" if tp_first else "sl_first"
        return True

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

    def _views(self, now: datetime, view: SeriesView) -> dict[Timeframe, SeriesView | None]:
        views: dict[Timeframe, SeriesView | None] = {self._replay.timeframe: view}
        for tf in self._higher:
            views[tf] = self._replay.higher_view_at(now, tf)
        return views

    @staticmethod
    def _consume_pending_limit(order: Order, candle: Candle, pending: list[Order]) -> Order:
        """Require prior placement; allow the existing gap fill at the open.

        Spec: strategy-no-wick.md › Entry; AGENTS.md › Invariant #1.
        """
        for index, placed in enumerate(pending):
            expected = placed
            gapped = (
                candle.high < placed.entry
                if placed.direction is Direction.BULLISH
                else candle.low > placed.entry
            )
            if gapped:
                expected = replace(placed, entry=candle.open)
            if order == expected:
                pending.pop(index)
                return placed
        raise ValueError("limit order must have been placed at the previous step")

    def _limit_fill_allowed(self, placed: Order, candle: Candle, now: datetime) -> bool:
        """Current candle only; keep the placed level when existing gap pricing applies.

        Spec: risk-management.md > Costs > Limit penetration. Strategies use this before
        consuming pending orders, so insufficient penetration retains their expiry rules.
        """
        sign = 1 if placed.direction is Direction.BULLISH else -1
        extreme = candle.low if sign > 0 else candle.high
        level = placed.entry
        tick = self._tick_size()
        if tick is not None:
            level = round_level(level, tick, up=sign < 0)
        entry = level
        if not candle.low <= entry <= candle.high:
            entry = candle.open
        distance = self._config.costs.tp_penetration * self._config.costs.spread(
            self._replay.symbol, now, entry
        )
        return sign * (extreme - (level - sign * distance)) <= 0

    def _tick_size(self) -> float | None:
        costs = self._config.costs
        return costs.for_symbol(self._replay.symbol).tick_size if costs.round_to_tick else None

    @staticmethod
    def _validate_levels(order: Order, entry: float) -> None:
        """Existing order contract; also applied after rounding (Costs > Tick rounding)."""
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
            if not math.isfinite(order.tp1_share) or not 0 < order.tp1_share < 1:
                raise ValueError(f"tp1_share {order.tp1_share} must be in (0, 1) with a TP2")
        if order.take_profit_3 is not None:
            tp2 = order.take_profit_2
            if tp2 is None or sign * (order.take_profit_3 - tp2) <= 0:
                raise ValueError(f"TP3 {order.take_profit_3} not beyond TP2 {tp2}")
            if (
                order.tp2_share is None
                or not math.isfinite(order.tp2_share)
                or order.tp2_share <= 0
            ):
                raise ValueError("tp2_share must be finite and positive with a TP3")
            if 1 - order.tp1_share - order.tp2_share <= 1e-12:
                raise ValueError("tp1_share + tp2_share must leave a share for TP3")

    def _fill(
        self, order: Order, candle: Candle, now: datetime, pending_limits: list[Order]
    ) -> tuple[OpenTrade, Order | None] | None:
        """Enter at the close of the current base candle (spec: "enter at that close"), or
        for a limit order at its level, which the candle must have traded through."""
        for name in ("entry", "stop_loss", "take_profit", "take_profit_2", "take_profit_3"):
            price = getattr(order, name)
            if price is not None and not math.isfinite(price):
                raise ValueError(f"order {name} must be finite")
        entry = order.entry if order.limit_fill else candle.close
        placed = None
        if order.limit_fill:
            placed = self._consume_pending_limit(order, candle, pending_limits)
            if not candle.low <= entry <= candle.high:
                raise ValueError(f"limit entry {entry} outside the candle at {now}")
            if (
                self._config.costs.tp_penetration or self._config.costs.round_to_tick
            ) and not self._limit_fill_allowed(placed, candle, now):
                return None
        elif not math.isclose(order.entry, entry):
            raise ValueError(f"order entry {order.entry} is not the candle close {entry} at {now}")
        sign = 1 if order.direction is Direction.BULLISH else -1
        self._validate_levels(order, entry)
        tick = self._tick_size()
        moves: list[float] = []
        count = self._diagnostics_start is None or candle.ts >= self._diagnostics_start
        if tick is not None:
            levels = {}
            for name in ("stop_loss", "take_profit", "take_profit_2", "take_profit_3"):
                price = getattr(order, name)
                if price is None:
                    continue
                up = sign > 0 if name == "stop_loss" else sign < 0
                levels[name] = round_level(price, tick, up=up)
                if levels[name] != price:
                    moves.append(abs(levels[name] - price) / tick)
            order = replace(order, **levels)
            if placed is not None:
                level = round_level(placed.entry, tick, up=sign < 0)
                if level != placed.entry:
                    moves.append(abs(level - placed.entry) / tick)
                # Round only the strategy's limit. A gap already filled at the open
                # keeps that observed price, even if the new level is in the candle.
                if candle.low <= placed.entry <= candle.high:
                    entry = level
                placed = replace(placed, entry=level)
            try:
                self._validate_levels(order, entry)
            except ValueError as exc:
                if count:
                    self.tick_rounding.record(moves, str(exc))
                self._strategy.on_order_skipped(order.ref, now)
                return None
        symbol = self._replay.symbol
        spread = self._config.costs.spread(symbol, now, entry)
        slippage = self._config.costs.slippage(symbol, entry)
        entry_fill = entry + (spread if sign > 0 else 0.0)
        if not order.limit_fill:
            entry_fill += sign * slippage
        check = None
        if self._config.break_even_at_next_session and self._strategy.uses_session_break_even:
            check = next_session_start(now, self._config.sessions).start
        break_even = entry + sign * self._config.costs.break_even_offset(
            symbol, now, entry, order.direction, entry_fill
        )
        if tick is not None:
            rounded_be = round_level(break_even, tick, up=sign > 0)
            if rounded_be != break_even:
                moves.append(abs(rounded_be - break_even) / tick)
            break_even = rounded_be
            if count:
                self.tick_rounding.record(moves)
        trade = OpenTrade(
            symbol=symbol,
            direction=order.direction,
            entry_time=now,
            entry_candle=candle.ts,
            entry=entry,
            entry_fill=entry_fill,
            initial_stop=order.stop_loss,
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            break_even_check=check,
            break_even_level=break_even,
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
            slippage=slippage,
            limit_fill=order.limit_fill,
            tp_penetration=self._config.costs.tp_penetration,
            short_tp_on_ask=self._config.costs.short_tp_on_ask,
        )
        return trade, placed

    @staticmethod
    def _check_break_even(trade: OpenTrade, candle: Candle, now: datetime) -> None:
        if trade.break_even_check is None or now < trade.break_even_check:
            return
        trade.break_even_check = None  # only the next session start counts
        if trade.sign * (candle.close - trade.break_even_level) > 0:
            trade.move_to_break_even(now)

    def _result(self, trade: OpenTrade) -> TradeResult:
        costs = self._config.costs
        exits = [(p.share, p.time) for p in trade.parts]
        swap_r = costs.swap_r(
            trade.symbol, trade.direction, trade.risk, trade.entry_time, exits, trade.entry
        )
        funding_r = costs.funding_r(
            trade.symbol, trade.direction, trade.risk, trade.entry_time, exits, trade.entry
        )
        commission_r = costs.commission_r(
            trade.symbol, trade.risk, trade.entry_fill, [(p.share, p.fill) for p in trade.parts]
        )
        return trade.result(commission_r, swap_r, funding_r)
