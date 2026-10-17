"""Position sizing: lots = risk % x balance / (SL distance x value of 1.0 price move per lot).

The value of a 1.0 price move per lot is `trade_tick_value / trade_tick_size` of the symbol (MT5
`symbol_info`, read at runtime; the tick value is already in the account currency). Lots are
rounded DOWN to the volume step, capped at the symbol's maximum; below the minimum there is no
trade and the reason says so. Spec: docs/live-trading.md › Risk, docs/risk-management.md.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

STEP_TOLERANCE = 1e-9  # float noise when dividing by the step (0.29 / 0.01 = 28.999999999999996)


@dataclass(frozen=True, slots=True)
class SymbolSpec:
    tick_size: float
    tick_value: float  # account currency per tick per 1 lot
    volume_min: float
    volume_step: float
    volume_max: float

    def __post_init__(self) -> None:
        for name in ("tick_size", "tick_value", "volume_min", "volume_step", "volume_max"):
            if not getattr(self, name) > 0:
                raise ValueError(f"{name} must be > 0")

    @property
    def value_per_unit(self) -> float:
        """Account currency per 1.0 price move per lot."""
        return self.tick_value / self.tick_size


@dataclass(frozen=True, slots=True)
class Sized:
    lots: float | None  # None: no trade
    risk_money: float = 0.0  # what the lots really risk at the SL distance
    reason: str = ""  # why there is no trade, or "capped at ..."


def spec_from_symbol_info(info) -> SymbolSpec:
    return SymbolSpec(
        info.trade_tick_size,
        info.trade_tick_value,
        info.volume_min,
        info.volume_step,
        info.volume_max,
    )


def lots_for_risk(
    balance: float, risk_percent: float, sl_distance: float, spec: SymbolSpec
) -> Sized:
    """Lots risking `risk_percent` % of `balance` over `sl_distance` (price units)."""
    if balance <= 0 or risk_percent <= 0 or sl_distance <= 0:
        raise ValueError("balance, risk_percent and sl_distance must be > 0")
    per_lot = sl_distance * spec.value_per_unit
    raw = balance * risk_percent / 100 / per_lot
    steps = math.floor(raw / spec.volume_step + STEP_TOLERANCE)
    lots = round(steps * spec.volume_step, 8)
    if lots < spec.volume_min - STEP_TOLERANCE:
        return Sized(
            None,
            reason=f"{raw:.4f} lots is below the minimum lot {spec.volume_min:g}",
        )
    reason = ""
    if lots > spec.volume_max:
        lots, reason = spec.volume_max, f"capped at the maximum lot {spec.volume_max:g}"
    return Sized(lots, lots * per_lot, reason)
