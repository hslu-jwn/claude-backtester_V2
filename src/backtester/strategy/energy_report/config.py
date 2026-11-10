"""Frozen strategy settings, adapted from _template. Spec: strategy-energy_report.md."""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class EnergyReportConfig:
    family: str = "F"  # F follows the reaction; V fades it
    k: float = 0.15  # inclusive reaction threshold in daily ATR units
    stop_atr: float = 1.0  # fixed stop distance in daily ATR units
    days: str = "report"  # report Wednesdays or disjoint Tuesday/Thursday control
    atr_period: int = 14  # Wilder period on completed NY 17:00 days
    calendar_dir: str = ""  # empty uses the existing timed_hold NYSE calendar

    def __post_init__(self) -> None:
        if self.family not in ("F", "V"):
            raise ValueError("family must be F or V")
        if self.days not in ("report", "control"):
            raise ValueError("days must be report or control")
        for name in ("k", "stop_atr"):
            if not isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if type(self.atr_period) is not int or self.atr_period <= 0:
            raise ValueError("atr_period must be a positive integer")
