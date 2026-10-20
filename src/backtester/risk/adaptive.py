"""Adaptive risk for prop-firm accounts: the risk per trade shrinks with the room to the
max-loss line, and a daily risk budget cuts or skips trades. Pure functions, no Dash.
Spec: risk-management.md > Prop-firm field > Adaptive risk (rules set by the user, 2026-10-20).
"""

from __future__ import annotations

from dataclasses import dataclass

EPS = 1e-9  # float tolerance when a risk is compared with what is left of the budget


@dataclass(frozen=True, slots=True)
class AdaptiveRisk:
    """Settings of the adaptive risk (defaults: the spec). The full room is the account's
    max loss (`MonteCarloConfig.max_loss` x the initial balance)."""

    enabled: bool = True
    floor: float = 0.25  # least share of the base risk (also the least a trade may be cut to)
    daily_budget: float = 0.03  # of the initial balance: today's loss + open risk + new risk

    def __post_init__(self) -> None:
        if not 0 < self.floor <= 1:
            raise ValueError("floor must be in (0, 1]")
        if self.daily_budget <= 0:
            raise ValueError("daily_budget must be > 0")


def risk_factor(equity: float, init: float, max_loss: float, floor: float) -> float:
    """Share of the base risk: room / full room, never above 1, never below `floor`.
    Room = equity - the static max-loss line (init x (1 - max_loss)); full room = init x max_loss."""
    room = equity - init * (1.0 - max_loss)
    return min(1.0, max(floor, room / (init * max_loss)))


def budgeted_risk(desired: float, floor_risk: float, allowed: float) -> float | None:
    """The risk (in money) a new trade gets when `allowed` of the daily budget is left: the
    desired risk, cut to `allowed`; None (skip the trade) when not even `floor_risk` fits."""
    if allowed < floor_risk - EPS:
        return None
    return min(desired, allowed)
