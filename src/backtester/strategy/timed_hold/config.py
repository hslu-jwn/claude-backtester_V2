"""Settings of strategy 10 (timed hold): every tunable value with its spec default.

Spec: docs/strategy-timed-hold.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo

DIRECTIONS = ("long", "short", "with_day", "against_day")
DAY_FILTERS = ("all", "fomc", "turn_of_month", "pre_holiday", "month_day")
TRADING_DAYS = ("weekdays", "nyse")


@dataclass(frozen=True, slots=True)
class TimedHoldConfig:
    zone: str = "America/New_York"  # clock of entry_time / exit_time (DST via zoneinfo)
    entry_time: time = time(9, 30)  # entry at the close of the 1m candle closing at this time
    exit_time: time = time(16, 0)  # an open trade closes at the close of this candle
    hold_days: int = 0  # 0 = same day; otherwise trading days after the entry date
    trading_days: str = "weekdays"  # calendar for hold_days and month_day
    direction: str = "long"  # long, short, with_day / against_day (vs the last finished ATR close)
    stop_atr: float = 0.5  # stop distance in daily ATR
    atr_period: int = 14  # Wilder ATR over the daily sessions of atr_zone
    atr_zone: str = "America/New_York"  # clock of the ATR sessions
    atr_open: time = time(9, 30)  # a session = candles closing in (atr_open, atr_close]
    atr_close: time = time(16, 0)
    atr_close_tolerance_min: int = 0  # FX: 180 with 00:00-23:59 UTC (Friday data ends ~21:00)
    # FX: leave Saturday / Sunday atr_zone dates out of the ATR (the Sunday-evening stub is not a day)
    atr_skip_weekend: bool = False
    skip_nyse_short_days: bool = False  # skip NYSE closures and early closes
    day_filter: str = "all"  # all, fomc, turn_of_month, pre_holiday, month_day
    month_day: int = 0  # positive from month start, negative from end; 0 = unused
    tom_days_after: int = 3  # turn_of_month: trading days of the new month that qualify
    calendar_dir: str = ""  # "" = the package folder strategy/timed_hold/calendars/
    # with_day / against_day only: trade only when |entry - previous close| >= this x ATR (0 = off)
    min_move_atr: float = 0.0

    def __post_init__(self) -> None:
        ZoneInfo(self.zone)  # raises for an unknown zone
        ZoneInfo(self.atr_zone)
        if type(self.hold_days) is not int or self.hold_days < 0:
            raise ValueError("hold_days must be an integer >= 0")
        if self.trading_days not in TRADING_DAYS:
            raise ValueError(f"trading_days must be one of {TRADING_DAYS}")
        if type(self.month_day) is not int:
            raise ValueError("month_day must be an integer")
        if self.day_filter == "month_day" and self.month_day == 0:
            raise ValueError("month_day must be non-zero for day_filter month_day")
        if self.hold_days == 0 and self.exit_time <= self.entry_time:
            raise ValueError("exit_time must be after entry_time")
        if self.atr_close <= self.atr_open:
            raise ValueError("atr_close must be after atr_open")
        if self.stop_atr <= 0:
            raise ValueError("stop_atr must be > 0")
        if self.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if self.atr_close_tolerance_min < 0:
            raise ValueError("atr_close_tolerance_min must be >= 0")
        if self.direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {DIRECTIONS}")
        if self.day_filter not in DAY_FILTERS:
            raise ValueError(f"day_filter must be one of {DAY_FILTERS}")
        if self.tom_days_after < 0:
            raise ValueError("tom_days_after must be >= 0")
        if self.min_move_atr < 0:
            raise ValueError("min_move_atr must be >= 0")
        if self.min_move_atr and self.direction in ("long", "short"):
            raise ValueError("min_move_atr needs direction with_day or against_day")
