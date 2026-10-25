"""Spec: risk-management.md > Costs > Tick rounding (V2.4d item 9)."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field


def round_level(price: float, tick: float, *, up: bool) -> float:
    """Directional tick rounding; preserve on-tick floats within 1e-9 price units."""
    units = price / tick
    nearest = round(units) * tick
    if math.isclose(price, nearest, rel_tol=0, abs_tol=1e-9):
        return price
    return (math.ceil(units) if up else math.floor(units)) * tick


@dataclass
class TickRoundingStats:
    """Order-attempt diagnostics, separate from closed trades so skips are retained."""

    orders_moved: int = 0
    levels_moved: int = 0
    total_move_ticks: float = 0.0
    rejected: int = 0
    rejection_reasons: dict[str, int] = field(default_factory=dict)

    @property
    def mean_move_ticks(self) -> float:
        return self.total_move_ticks / self.levels_moved if self.levels_moved else 0.0

    def record(self, moves: list[float], rejection: str | None = None) -> None:
        if moves:
            self.orders_moved += 1
            self.levels_moved += len(moves)
            self.total_move_ticks += sum(moves)
        if rejection is not None:
            self.rejected += 1
            self.rejection_reasons[rejection] = self.rejection_reasons.get(rejection, 0) + 1

    def as_dict(self) -> dict:
        return {
            "orders_moved": self.orders_moved,
            "levels_moved": self.levels_moved,
            "total_move_ticks": self.total_move_ticks,
            "mean_move_ticks": self.mean_move_ticks,
            "rejected": self.rejected,
            "rejection_reasons": dict(self.rejection_reasons),
        }

    def notes(self) -> tuple[str, ...]:
        return tuple(
            f"tick rounding rejected {count} order(s): {reason}"
            for reason, count in sorted(self.rejection_reasons.items())
        )

    @classmethod
    def combined(cls, stats) -> TickRoundingStats:
        out = cls()
        reasons = Counter()
        for item in stats:
            out.orders_moved += item.orders_moved
            out.levels_moved += item.levels_moved
            out.total_move_ticks += item.total_move_ticks
            out.rejected += item.rejected
            reasons.update(item.rejection_reasons)
        out.rejection_reasons = dict(reasons)
        return out
