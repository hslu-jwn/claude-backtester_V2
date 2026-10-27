"""Settings of the fill probe: every tunable value with its default.

Spec: docs/strategy-fill-probe.md. TEST TOOL, never research or trade it for profit.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FillProbeConfig:
    interval_minutes: int = 30  # enter on candles closing at minutes divisible by this
    atr_period: int = 14  # Wilder ATR of the M1 candles
    stop_atr: float = 3.0  # stop distance in ATR
    target_r: float = 1.0  # take profit at this many R; 0 = no take profit
    max_hold_minutes: int = 20  # time exit after this many minutes

    def __post_init__(self) -> None:
        if self.interval_minutes < 1:
            raise ValueError("interval_minutes must be >= 1")
        if self.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if self.stop_atr <= 0:
            raise ValueError("stop_atr must be > 0")
        if self.target_r < 0:
            raise ValueError("target_r must be >= 0 (0 = no take profit)")
        if self.max_hold_minutes < 1:
            raise ValueError("max_hold_minutes must be >= 1")
