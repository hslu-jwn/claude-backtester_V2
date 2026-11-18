"""Stress scenarios beyond the worst seen day for the FTMO 2-Step simulation (T-25).

Spec: risk-management.md › Stress scenarios (T-25). Opt-in: the plain Monte Carlo is unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from backtester.risk.monte_carlo import Day, MonteCarloConfig, ftmo_by_risk, reshuffle_orders


@dataclass(frozen=True, slots=True)
class StressScenario:
    name: str
    multiple: float  # x every trade of the worst historical day
    days: int = 1  # consecutive shock days (a clustered loss)


DEFAULT_SCENARIOS = (
    StressScenario("1.5x worst day", 1.5),
    StressScenario("2x worst day", 2.0),
    StressScenario("worst day 5 in a row", 1.0, days=5),
)


def shock_day(days: list[Day], multiple: float) -> Day:
    """The worst day (lowest summed net R among days with trades), every R x `multiple`."""
    traded = [d for d in days if len(d.r)]
    worst = min(traded, key=lambda d: float(d.r.sum()), default=None)
    if worst is None or worst.r.sum() >= 0:
        raise ValueError("stress needs at least one losing day")
    return Day(
        worst.r * multiple,
        tuple((is_entry, r * multiple) for is_entry, r in worst.events),
        worst.ids,
        worst.weights,
    )


def with_shocks(
    days: list[Day], orders: np.ndarray, scenario: StressScenario, rng: np.random.Generator
) -> tuple[list[Day], np.ndarray]:
    """Days plus the shock day (last index); in each order `scenario.days` consecutive
    positions from a uniform random start are replaced by it."""
    n = orders.shape[1]
    if scenario.multiple <= 0 or not 1 <= scenario.days <= n:
        raise ValueError("multiple must be > 0 and days in 1..order length")
    shock = len(days)
    out = orders.copy()
    starts = rng.integers(0, n - scenario.days + 1, size=len(out))
    for row, s in zip(out, starts, strict=True):
        row[s : s + scenario.days] = shock
    return [*days, shock_day(days, scenario.multiple)], out


def stress_ftmo(
    days: list[Day], config: MonteCarloConfig, scenarios=DEFAULT_SCENARIOS
) -> dict[str, dict]:
    """{"baseline": ftmo_by_risk(...), <scenario name>: ftmo_by_risk(...) with its shocks}."""
    orders = reshuffle_orders(len(days), config)
    out = {"baseline": ftmo_by_risk(days, orders, config)}
    for scenario in scenarios:
        rng = np.random.default_rng(config.seed + 1)
        out[scenario.name] = ftmo_by_risk(*with_shocks(days, orders, scenario, rng), config)
    return out


__all__ = ["DEFAULT_SCENARIOS", "StressScenario", "shock_day", "stress_ftmo", "with_shocks"]
