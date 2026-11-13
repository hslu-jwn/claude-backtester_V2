"""Group normalization and closed-leg accounting. Spec: design/multi-symbol.md › B.

For sign s and relative quantity q, chart gross money is
    s*q*(chart_exit - chart_entry)*exit_value.
A CFD leg is margin-traded: only its price P/L is a quote-currency cashflow, settled at
exit, so it is valued with the exit conversion (no P/L on the notional from a conversion
change; Opus 2026-11-12, correcting the brief). Fill money uses the same formula with
executed prices. Each signed cost cashflow is multiplied by q and its settlement value,
then all money is divided by entry D. Conversion never changes the initial risk weights.

Assumptions: round-turn commission is split equally between entry and exit, each
half evaluated at that side's fill price and conversion. Accrued swap and funding
are settled at exit, using exit_value; LegFill has no intermediate settlement
conversion observations. Spread diagnostic is signed and valued at entry, never
charged again. The caller supplies fills in order. Entry values must exactly match
the basis values. Only fully closed groups are represented (residual=False);
execution, intermediate financing settlement/MTM, and residuals belong to the next
increment. No additional legacy conversion surcharge is applied: conversion is
already explicit in the cashflows.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isclose, isfinite

from backtester.core.models import Direction
from backtester.engine.costs import CostConfig, fill_spread_time, rollover_nights
from backtester.engine.trade import ExitReason
from backtester.strategy.group import GroupLeg, GroupOrder


def group_basis(
    legs: Sequence[GroupLeg], values: Sequence[float],
) -> tuple[float, tuple[float, ...]]:
    """Freeze D and stop-risk shares at entry. Spec: design/multi-symbol.md › B."""
    if len(legs) < 2 or len(legs) != len(values):
        raise ValueError("basis needs at least two legs and one value per leg")
    budgets = []
    for leg, value in zip(legs, values, strict=True):
        for name, amount in (("quantity", leg.quantity), ("stop_distance", leg.stop_distance),
                             ("value", value)):
            if not isfinite(amount) or amount <= 0:
                raise ValueError(f"{name} must be finite and positive")
        budget = leg.quantity * value * leg.stop_distance
        if not isfinite(budget) or budget <= 0:
            raise ValueError("leg risk budget must be finite and positive")
        budgets.append(budget)
    denominator = sum(budgets)
    if not isfinite(denominator) or denominator <= 0:
        raise ValueError("group D must be finite and positive")
    weights = tuple(budget / denominator for budget in budgets)
    if any(weight <= 0 for weight in weights):
        raise ValueError("risk weights must be positive (numerical underflow)")
    return denominator, weights


@dataclass(frozen=True, slots=True)
class LegFill:
    """Executed prices and settlement values. Spec: design/multi-symbol.md › B."""

    entry_fill: float
    exit_fill: float
    entry_time: datetime
    exit_time: datetime
    exit_reason: ExitReason
    entry_value: float
    exit_value: float
    chart_entry: float
    chart_exit: float

    def __post_init__(self) -> None:
        for name in ("entry_fill", "exit_fill", "chart_entry", "chart_exit",
                     "entry_value", "exit_value"):
            value = getattr(self, name)
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")
            if name in ("entry_value", "exit_value") and value <= 0:
                raise ValueError(f"{name} must be positive")
        for name in ("entry_time", "exit_time"):
            if getattr(self, name).utcoffset() != timedelta(0):
                raise ValueError(f"{name} must be UTC-aware")
        if self.exit_time < self.entry_time:
            raise ValueError("exit_time must not precede entry_time")


def _commission_sides(cfg: CostConfig, leg: GroupLeg, fill: LegFill) -> tuple[float, float]:
    return (-cfg.commission_price(leg.symbol, fill.entry_fill) / 2,
            -cfg.commission_price(leg.symbol, fill.exit_fill) / 2)


def leg_costs(cfg: CostConfig, leg: GroupLeg, fill: LegFill) -> dict[str, float]:
    """Signed price costs per relative unit. Spec: design/multi-symbol.md › B."""
    symbol = cfg.for_symbol(leg.symbol)
    nights = rollover_nights(fill.entry_time, fill.exit_time, symbol.swap_triple_weekday)
    entry_commission, exit_commission = _commission_sides(cfg, leg, fill)
    result = {
        "commission": entry_commission + exit_commission,
        "swap": cfg.swap_r_nights(leg.symbol, leg.direction, risk=1.0,
                                  nights=nights, entry=fill.entry_fill),
        "funding": (cfg.funding_r(leg.symbol, leg.direction, risk=1.0,
                                  entry_time=fill.entry_time, exits=((1.0, fill.exit_time),),
                                  entry=fill.entry_fill)
                    if cfg.funding_series(leg.symbol) is not None else 0.0),
        "spread_diagnostic": -cfg.spread(leg.symbol, fill_spread_time(fill.entry_time), fill.chart_entry),
    }
    if any(not isfinite(value) for value in result.values()):
        raise ValueError("leg costs must be finite")
    return result


@dataclass(frozen=True, slots=True)
class LegAttribution:
    """Leg contribution in units of group R. Spec: design/multi-symbol.md › B."""

    gross_r: float
    net_r: float
    commission_r: float
    swap_r: float
    funding_r: float
    spread_diagnostic_r: float


@dataclass(frozen=True, slots=True)
class GroupResult:
    """Closed group totals and attribution. Spec: design/multi-symbol.md › B."""

    group_id: str
    legs: tuple[GroupLeg, ...]
    D: float
    weights: tuple[float, ...]
    attributions: tuple[LegAttribution, ...]
    r_gross: float
    r_net: float
    exit_reasons: tuple[ExitReason, ...]
    residual: bool = False

    def reconcile(self) -> bool:
        """Check attribution sums, with abs tol 1e-12 and no relative tolerance."""
        return (
            len(self.legs) == len(self.weights) == len(self.attributions) == len(self.exit_reasons)
            and isclose(sum(self.weights), 1.0, rel_tol=0, abs_tol=1e-12)
            and isclose(sum(p.gross_r for p in self.attributions), self.r_gross,
                        rel_tol=0, abs_tol=1e-12)
            and isclose(sum(p.net_r for p in self.attributions), self.r_net,
                        rel_tol=0, abs_tol=1e-12)
        )


def group_result(
    order: GroupOrder, fills: Sequence[LegFill], cfg: CostConfig, values: Sequence[float],
) -> GroupResult:
    """Normalize executed cashflows by fixed entry risk. Spec: design/multi-symbol.md › B."""
    denominator, weights = group_basis(order.legs, values)
    if len(fills) != len(order.legs):
        raise ValueError("fills must contain one fill per ordered leg")
    parts = []
    gross_amounts = []
    net_amounts = []
    for leg, fill, value in zip(order.legs, fills, values, strict=True):
        if fill.entry_value != value:
            raise ValueError("entry_value must match the frozen basis value")
        costs = leg_costs(cfg, leg, fill)
        sign = 1 if leg.direction is Direction.BULLISH else -1
        gross = sign * leg.quantity * (fill.chart_exit - fill.chart_entry) * fill.exit_value
        fills_money = sign * leg.quantity * (fill.exit_fill - fill.entry_fill) * fill.exit_value
        entry_commission, exit_commission = _commission_sides(cfg, leg, fill)
        commission = leg.quantity * (entry_commission * fill.entry_value
                                     + exit_commission * fill.exit_value)
        swap = costs["swap"] * leg.quantity * fill.exit_value
        funding = costs["funding"] * leg.quantity * fill.exit_value
        net = fills_money + commission + swap + funding
        part = LegAttribution(
            gross / denominator, net / denominator,
            commission / denominator, swap / denominator, funding / denominator,
            costs["spread_diagnostic"] * leg.quantity * fill.entry_value / denominator,
        )
        if any(not isfinite(amount) for amount in (
            part.gross_r, part.net_r, part.commission_r, part.swap_r,
            part.funding_r, part.spread_diagnostic_r,
        )):
            raise ValueError("normalized attribution must be finite")
        parts.append(part)
        gross_amounts.append(gross)
        net_amounts.append(net)
    result = GroupResult(
        order.group_id, order.legs, denominator, weights, tuple(parts),
        sum(gross_amounts) / denominator, sum(net_amounts) / denominator,
        tuple(fill.exit_reason for fill in fills),
    )
    if not result.reconcile():
        raise ValueError("group result does not reconcile")
    return result
