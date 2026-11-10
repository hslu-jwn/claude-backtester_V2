"""Frozen defaults. Spec: strategy-daily_reversal.md > Frozen experiment and gates."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class DailyReversalConfig:
    setup: str = "E8"  # E8 (both directions) or CAP (long only)
    target_r: float = 2.0  # 0 = no target (TOML encoding of none)
    hold_sessions: int = 5  # full cash sessions after the fill session
    tick_size: float | None = None  # None = shared symbol tick metadata
    e8_lookback: int = 7  # preceding sessions for day 1
    e8_first_day: int = 3  # first possible confirmation day
    e8_last_day: int = 6  # final possible confirmation day
    e8_valid_sessions: int = 4  # subsequent sessions for the pending trigger
    cap_lookback: int = 9  # preceding sessions for low and range comparisons
    cap_top_fraction: float = 0.25  # inclusive close in the top quarter
    cap_valid_sessions: int = 2  # subsequent sessions for the pending trigger

    def __post_init__(self) -> None:
        if self.setup not in ("E8", "CAP"):
            raise ValueError("setup must be E8 or CAP")
        if isinstance(self.target_r, bool) or not isfinite(self.target_r) or self.target_r < 0:
            raise ValueError("target_r must be finite and >= 0 (0 disables target)")
        if self.tick_size is not None and (
            isinstance(self.tick_size, bool) or not isfinite(self.tick_size) or self.tick_size <= 0
        ):
            raise ValueError("tick_size must be finite and > 0")
        for name in (
            "hold_sessions",
            "e8_lookback",
            "e8_first_day",
            "e8_last_day",
            "e8_valid_sessions",
            "cap_lookback",
            "cap_valid_sessions",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if not 3 <= self.e8_first_day <= self.e8_last_day:
            raise ValueError("E8 confirmation window must start at or after day 3")
        if not isfinite(self.cap_top_fraction) or not 0 < self.cap_top_fraction <= 1:
            raise ValueError("cap_top_fraction must be in (0, 1]")
