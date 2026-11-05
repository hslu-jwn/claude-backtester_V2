"""Frozen submission baseline. Spec: strategy-alternating-path.md > Configuration."""

from dataclasses import dataclass, fields

SYMBOLS = ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD")


@dataclass(frozen=True, slots=True)
class AlternatingPathConfig:
    response_mode: str = "FOLLOW_LAST"
    holding_minutes: int = 60
    aggregation_minutes: int = 15
    alternating_changes: int = 4
    path_activity_atr_min: float = 1.0
    stop_atr_multiplier: float = 1.0
    atr_period: int = 96
    first_signal_london: str = "09:00"
    last_signal_london: str = "13:45"
    exit_deadline_london: str = "15:00"

    def __post_init__(self) -> None:
        if self.response_mode not in ("FOLLOW_LAST", "FADE_LAST"):
            raise ValueError("response_mode must be FOLLOW_LAST or FADE_LAST")
        if type(self.holding_minutes) is not int or self.holding_minutes not in (30, 60):
            raise ValueError("holding_minutes must be integer 30 or 60")
        for field in fields(self):
            if field.name in ("response_mode", "holding_minutes"):
                continue
            value = getattr(self, field.name)
            if isinstance(value, bool) or value != field.default:
                raise ValueError(f"{field.name} is fixed by the submission")
            if isinstance(field.default, int) and type(value) is not int:
                raise ValueError(f"{field.name} must be an integer")
