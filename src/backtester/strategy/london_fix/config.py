"""Frozen submission defaults. Spec: strategy-london-fix.md > Configuration."""

from dataclasses import dataclass
from datetime import time
from math import isfinite

SYMBOLS = ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD")
# Numeric sides in SYMBOLS order, a fixed tuple compatible with V2 settings serialization.
SIDE_MAP = (1.0, 1.0, 1.0, 1.0, -1.0, -1.0)


def clock_time(value: str) -> time:
    """A minute boundary, written HH:MM (no seconds or UTC offset)."""
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        raise ValueError("London clock times must be HH:MM")
    parsed = time.fromisoformat(value)
    if parsed.tzinfo is not None or parsed.second or parsed.microsecond:
        raise ValueError("London clock times must be minute boundaries")
    return parsed


@dataclass(frozen=True, slots=True)
class LondonFixConfig:
    entry_time_london: str = "16:03"  # completed M1 signal's London close time
    atr_period: int = 60  # submission atr_period_m1: Wilder true ranges including signal
    stop_atr_multiplier: float = 4.0  # fixed initial stop distance in ATR
    holding_minutes: int = 360  # elapsed minutes from entry close
    force_close_london: str = "23:55"  # deadline on the London entry date
    side_map: tuple[float, ...] = SIDE_MAP  # immutable numeric sides in SYMBOLS order

    def __post_init__(self) -> None:
        for name in ("atr_period", "holding_minutes"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if not isfinite(self.stop_atr_multiplier) or self.stop_atr_multiplier <= 0:
            raise ValueError("stop_atr_multiplier must be finite and positive")
        if clock_time(self.entry_time_london) >= clock_time(self.force_close_london):
            raise ValueError("entry_time_london must precede force_close_london")
        if not isinstance(self.side_map, tuple) or self.side_map != SIDE_MAP:
            raise ValueError("side_map is fixed by the submission")
