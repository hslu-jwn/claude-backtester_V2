"""Frozen settings. Spec: strategy-h1-shock.md › Grid and primary setting."""
from dataclasses import dataclass
from math import isfinite

SYMBOLS = ("XAUUSD", "GBPUSD", "GBPJPY", "NAS100", "US500")


@dataclass(frozen=True, slots=True)
class H1ShockConfig:
    response_mode: str = "CONTINUATION"
    event_z_threshold: float = 3.0
    holding_hours: int = 1
    same_clock_lookback: int = 60
    atr_period_h1: int = 20
    stop_atr_multiplier: float = 6.0
    minimum_event_cost_multiple: float = 5.0
    risk_fraction_equity: float = .001
    minimum_m1_count: int = 55
    maximum_missing_run: int = 5
    stale_run_minutes: int = 15
    mad_scale: float = 1.4826
    warmup_days: int = 120
    calendar_dir: str = ""

    def __post_init__(self):
        if self.response_mode not in ("CONTINUATION", "REVERSAL"):
            raise ValueError("response_mode must be CONTINUATION or REVERSAL")
        for name in ("event_z_threshold", "stop_atr_multiplier", "minimum_event_cost_multiple",
                     "risk_fraction_equity", "mad_scale"):
            if not isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be finite and positive")
        for name in ("holding_hours", "same_clock_lookback", "atr_period_h1", "minimum_m1_count",
                     "maximum_missing_run", "stale_run_minutes", "warmup_days"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.holding_hours > 3 or self.minimum_m1_count > 60:
            raise ValueError("holding_hours <= 3 and minimum_m1_count <= 60 required")
        if self.risk_fraction_equity > 1:
            raise ValueError("risk_fraction_equity must be <= 1")
