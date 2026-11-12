"""Paired M1 execution. Spec: design/multi-symbol.md › B.

Assumptions for this increment:
* Undeclared leg policies default to required M1, max_age=0, one warm-up candle;
  references may explicitly override leg timeframes/freshness. All callbacks require
  market.ready; protective execution continues independently of readiness.
* A next open may equal intent_time (the signal candle has just closed). Expiry is
  inclusive in OPEN time. Pending intents at end of data are rejected as expired.
* Entry-candle SL/TP are active immediately: after atomic acceptance, manage that
  already closed candle, SL first. Both simultaneous stops precede scheduling peers.
  A queued group exit takes precedence over later extremes of its execution candle.
  Exit IDs requested at an entry-confirming close also apply to that newly filled
  group, scheduling opens at or after this close, never its earlier entry open.
* Entry and scheduled-exit timestamps are actual OPEN times; stop/TP timestamps are
  confirming CLOSE times, as in the legacy engine. Callbacks occur when established
  at the close; entry-candle closure callbacks follow that close's strategy decision.
* A peer exit uses ExitReason.SIGNAL; TP alone does not schedule other legs. Slippage
  stays scaled at chart entry; short spread refreshes at the managing candle's open
  time and chart entry, matching the legacy engine. Tick rounding freezes actual
  rounded initial stop distances in D (unrounded intent remains in open-group views).
* values is a constant symbol mapping, or a sequence in strategy.legs order; defaults
  are each symbol's value_per_price_unit. Causal conversion symbols are a later
  increment. Closed results use 2a-1 accounting unchanged, including its financing
  settlement convention. No news input exists in this interface yet.

Engine-owned source candles never cross the strategy boundary. M1 events are consumed
on a union close clock, without looking ahead for a common entry or peer exit candle.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from math import isfinite
from types import MappingProxyType

from backtester.core.market import ReferenceInput
from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.costs import CostConfig
from backtester.engine.group_trade import GroupResult, LegFill, group_basis, group_result
from backtester.engine.market_replay import MarketReplay
from backtester.engine.ticks import round_level
from backtester.engine.trade import ExitReason, OpenTrade
from backtester.strategy.group import GroupOrder, GroupStrategy


@dataclass(frozen=True, slots=True)
class OpenGroupLeg:
    """Remaining exposure and stale mark. Spec: design/multi-symbol.md › B."""

    symbol: str
    direction: Direction
    quantity: float
    entry_time: datetime
    chart_entry: float
    entry_fill: float
    stop_loss: float
    mark: float
    mark_time: datetime


@dataclass(frozen=True, slots=True)
class UnresolvedGroup:
    """Unexecuted exposure, never a forced fill. Spec: design/multi-symbol.md › B."""

    group_id: str
    open_legs: tuple[OpenGroupLeg, ...]
    residual: bool = True


@dataclass(frozen=True, slots=True)
class RejectedGroup:
    """Atomic rejection. Spec: design/multi-symbol.md › B."""

    group_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class GroupRunResult:
    """Execution outcome; fills retain leg order. Spec: design/multi-symbol.md › B.

    fills includes accepted groups; None denotes an unexecuted exit, not a mark.
    """

    closed: tuple[GroupResult, ...]
    unresolved: tuple[UnresolvedGroup, ...]
    rejected: tuple[RejectedGroup, ...]
    notes: tuple[str, ...]
    fills: Mapping[str, tuple[LegFill | None, ...]]


@dataclass(slots=True)
class _OpenGroup:
    intent: GroupOrder
    basis_order: GroupOrder
    values: tuple[float, ...]
    trades: list[OpenTrade]
    exit_after: datetime | None = None
    fills: list[LegFill | None] = field(default_factory=list)

    @property
    def closed(self):
        return all(t.is_closed for t in self.trades)


def _fill_group(order, candles, cfg, values):
    trades, legs, basis_values = [], [], []
    for leg in order.legs:
        candle = candles[leg.symbol]
        settings = cfg.for_symbol(leg.symbol)
        sign = 1 if leg.direction is Direction.BULLISH else -1
        entry = candle.open
        stop = entry - sign * leg.stop_distance
        target = (entry + sign * leg.take_profit_distance
                  if leg.take_profit_distance is not None else None)
        if not all(isfinite(v) for v in (entry, stop) + (() if target is None else (target,))):
            raise ValueError(f"{leg.symbol}: nonfinite price")
        if cfg.round_to_tick and settings.tick_size is not None:
            stop = round_level(stop, settings.tick_size, up=sign > 0)
            if target is not None:
                target = round_level(target, settings.tick_size, up=sign < 0)
        risk = sign * (entry - stop)
        if risk <= 0:
            raise ValueError(f"{leg.symbol}: stop distance <= 0 after tick rounding")
        if target is not None and sign * (target - entry) <= 0:
            raise ValueError(f"{leg.symbol}: target distance <= 0 after tick rounding")
        spread = cfg.spread(leg.symbol, candle.ts, entry)
        slippage = cfg.slippage(leg.symbol, entry)
        fill = entry + (spread if sign > 0 else 0) + sign * slippage
        if not all(isfinite(v) for v in (spread, slippage, fill)):
            raise ValueError(f"{leg.symbol}: nonfinite fill")
        if cfg.refuse_stop_in_spread and sign < 0 and stop - (entry + spread) <= 1e-9 * abs(entry):
            raise ValueError(f"{leg.symbol}: stop inside spread")
        if cfg.too_expensive(leg.symbol, risk, candle.ts, entry, fill):
            raise ValueError(f"{leg.symbol}: cost limit exceeded")
        value = values[leg.symbol] if values is not None else settings.value_per_price_unit
        basis_values.append(value)
        legs.append(replace(leg, stop_distance=risk))
        trades.append(OpenTrade(
            symbol=leg.symbol, direction=leg.direction, entry_time=candle.ts,
            entry_candle=candle.ts, entry=entry, entry_fill=fill, initial_stop=stop,
            stop_loss=stop, take_profit=target, break_even_check=None,
            break_even_level=entry, spread=spread, slippage=slippage,
            tp_penetration=cfg.tp_penetration, short_tp_on_ask=cfg.short_tp_on_ask,
            short_sl_on_ask=cfg.short_sl_on_ask,
        ))
    basis = replace(order, legs=tuple(legs))
    group_basis(basis.legs, basis_values)  # atomic validation before exposing any leg
    return _OpenGroup(order, basis, tuple(basis_values), trades, fills=[None] * len(trades))


def _manage(group, candles, now, cfg):
    stopped = False
    for index, trade in enumerate(group.trades):
        candle = candles.get(trade.symbol)
        if trade.is_closed or candle is None:
            continue
        if trade.sign < 0:
            trade.spread = cfg.spread(trade.symbol, candle.ts, trade.entry)
        if group.exit_after is not None and candle.ts >= group.exit_after:
            trade.close_all(candle, candle.ts, candle.open, ExitReason.SIGNAL)
        else:
            trade.on_candle(candle, now)
        if trade.is_closed:
            part = trade.parts[-1]
            value = group.values[index]
            group.fills[index] = LegFill(
                trade.entry_fill, part.fill, trade.entry_time, part.time, part.reason,
                value, value, trade.entry, part.price,
            )
            stopped |= part.reason is ExitReason.STOP_LOSS
    if stopped and group.exit_after is None:
        group.exit_after = now


def run_group_backtest(
    strategy: GroupStrategy,
    series_by_symbol: Mapping[str, CandleSeries | Sequence[CandleSeries]],
    cfg: CostConfig,
    values: Mapping[str, float] | Sequence[float] | None = None,
) -> GroupRunResult:
    """Run one shared M1 clock. Spec: design/multi-symbol.md › B.

    Each mapping value is an M1 series or a sequence containing M1 plus all declared
    higher timeframes. MarketReplay validates the exact dependency bundle.
    """
    legs = strategy.legs
    if (not isinstance(legs, tuple) or len(legs) < 2 or len(set(legs)) != len(legs)
            or any(not isinstance(s, str) or not s for s in legs)):
        raise ValueError("legs must be a tuple of at least two distinct symbols")
    declarations = {r.symbol: r for r in strategy.references}
    if len(declarations) != len(strategy.references):
        raise ValueError("duplicate reference symbol declaration")
    for symbol in legs:
        declaration = declarations.get(symbol)
        declarations[symbol] = (replace(declaration, required=True) if declaration else
                                ReferenceInput(symbol, "leg", (Timeframe.M1,), timedelta(0)))
    sources = []
    for symbol, bundle in series_by_symbol.items():
        bundle = (bundle,) if isinstance(bundle, CandleSeries) else tuple(bundle)
        if any(s.symbol != symbol for s in bundle):
            raise ValueError("series symbol must match its mapping key")
        sources.extend(bundle)
    replay = MarketReplay(tuple(declarations.values()), sources)
    if values is not None and not isinstance(values, Mapping):
        values = dict(zip(legs, values, strict=True))
    # Index engine-owned events by close time, without inspecting future prices.
    events: dict[datetime, dict[str, Candle]] = {}
    for source in sources:
        if source.timeframe is Timeframe.M1:
            for candle in source._candles:
                events.setdefault(candle.ts + Timeframe.M1.duration, {})[source.symbol] = candle
    active, pending, accepted = [], [], []
    closed, rejected, notes = [], [], []
    seen_ids = set()
    marks = {}

    def finish():
        for group in tuple(active):
            if group.closed:
                result = group_result(group.basis_order, group.fills, cfg, group.values)
                closed.append(result)
                active.remove(group)
                strategy.on_group_closed(result)

    for now, candles in sorted(events.items()):
        for symbol, candle in candles.items():
            marks[symbol] = (candle.close, now)
        for group in active:
            _manage(group, candles, now, cfg)
        finish()
        market = replay.advance(now)
        exit_ids = []
        if market.ready:
            orders = strategy.on_group_candle(now, market)
            exit_ids = strategy.group_exits(now, market, tuple(g.intent for g in active))
            for group in active:
                if group.intent.group_id in exit_ids and group.exit_after is None:
                    group.exit_after = now
            for order in orders:
                if order.group_id in seen_ids:
                    rejected.append(RejectedGroup(order.group_id, "duplicate group id"))
                    continue
                seen_ids.add(order.group_id)
                if order.intent_time != now:
                    rejected.append(RejectedGroup(order.group_id, "intent_time must equal now"))
                elif any(leg.symbol not in legs for leg in order.legs):
                    rejected.append(RejectedGroup(order.group_id, "leg rejected: undeclared symbol"))
                else:
                    pending.append(order)
        for order in tuple(pending):
            deadline = order.intent_time + timedelta(minutes=order.expiry_minutes)
            opening = now - Timeframe.M1.duration
            eligible = (order.intent_time <= opening <= deadline
                        and all(leg.symbol in candles for leg in order.legs))
            if eligible:
                pending.remove(order)
                try:
                    group = _fill_group(order, candles, cfg, values)
                except (ValueError, KeyError, OverflowError) as exc:
                    rejected.append(RejectedGroup(order.group_id, f"leg rejected: {exc}"))
                    continue
                active.append(group)
                accepted.append(group)
                _manage(group, candles, now, cfg)
                if order.group_id in exit_ids and group.exit_after is None:
                    group.exit_after = now
            elif opening >= deadline:
                pending.remove(order)
                rejected.append(RejectedGroup(order.group_id, "expired"))
        finish()
    rejected.extend(RejectedGroup(o.group_id, "expired") for o in pending)
    if pending:
        notes.append("Pending intents expired at end of data without an executable common open.")
    unresolved = tuple(UnresolvedGroup(g.intent.group_id, tuple(
        OpenGroupLeg(t.symbol, t.direction, leg.quantity, t.entry_time, t.entry,
                     t.entry_fill, t.stop_loss, *marks[t.symbol])
        for leg, t in zip(g.intent.legs, g.trades, strict=True) if not t.is_closed
    )) for g in active)
    return GroupRunResult(tuple(closed), unresolved, tuple(rejected), tuple(notes),
                          MappingProxyType({g.intent.group_id: tuple(g.fills) for g in accepted}))
