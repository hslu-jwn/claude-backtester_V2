"""Finite-number parsing shared by UI view models."""

import math


def _number(value) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None
