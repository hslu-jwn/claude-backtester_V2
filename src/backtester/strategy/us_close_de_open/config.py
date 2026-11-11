"""Settings. Spec: strategy-us_close_de_open.md › Definitions / Cells / Control."""

from dataclasses import dataclass
from datetime import time
from math import isfinite
from zoneinfo import ZoneInfo


@dataclass(frozen=True, slots=True)
class UsCloseDeOpenConfig:
    zone: str = "Europe/Berlin"  # local entry / exit clock
    entry_time: time = time(9)  # candle close, never its open timestamp
    exit_time: time = time(9, 30)  # first later close if missing
    direction: str = "with_ref"  # with_ref, long or short (controls)
    min_ref_return_pct: float = 0.10  # absolute US close-to-close return, in percent
    stop_atr: float = 0.5  # stop distance in finished daily ATR
    atr_period: int = 14  # Wilder ATR over regular cash sessions
    atr_zone: str = "Europe/Berlin"  # independent cash-session clock
    atr_open: time = time(9)  # sessions contain candle closes in (open, close]
    atr_close: time = time(17, 30)
    atr_close_tolerance_min: int = 0  # minutes before atr_close still considered regular
    ref_symbol: str = "US500"  # observation only, never an execution symbol
    ref_zone: str = "America/New_York"
    ref_from: time = time(15, 30)  # signal candle close on the previous weekday
    ref_to: time = time(16)
    skip_nyse_short_days: bool = True  # both signal and trade dates must be full sessions
    calendar_dir: str = ""  # empty uses timed_hold/calendars

    def __post_init__(self) -> None:
        for zone in (self.zone, self.atr_zone, self.ref_zone):
            ZoneInfo(zone)
        for name in ("entry_time", "exit_time", "atr_open", "atr_close", "ref_from", "ref_to"):
            value = getattr(self, name)
            if not isinstance(value, time) or value.tzinfo is not None:
                raise ValueError(f"{name} must be a local civil time")
        if self.direction not in ("with_ref", "long", "short"):
            raise ValueError("direction must be with_ref, long or short")
        for name in ("stop_atr", "min_ref_return_pct"):
            value = getattr(self, name)
            if not isfinite(value) or value < 0 or (name == "stop_atr" and value == 0):
                raise ValueError(f"{name} must be finite and {'> 0' if name == 'stop_atr' else '>= 0'}")
        if self.exit_time <= self.entry_time:
            raise ValueError("exit_time must be after entry_time")
        if self.atr_close <= self.atr_open:
            raise ValueError("atr_close must be after atr_open")
        if self.ref_to <= self.ref_from:
            raise ValueError("ref_to must be after ref_from")
        if type(self.atr_period) is not int or self.atr_period < 1:
            raise ValueError("atr_period must be an integer >= 1")
        if type(self.atr_close_tolerance_min) is not int or self.atr_close_tolerance_min < 0:
            raise ValueError("atr_close_tolerance_min must be an integer >= 0")
        if not self.ref_symbol.strip():
            raise ValueError("ref_symbol must not be empty")
