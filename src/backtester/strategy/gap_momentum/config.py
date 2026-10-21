"""Settings of strategy 7 (gap momentum): every tunable value with its spec default.

Spec: docs/strategy-gap-momentum.md (rules set by the user, 2026-10-20).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo

# session per mode: (open, close) in New York time; the exit default is the last candle before
# the close (index 15:59, fx 16:59), so a trade is flat before the 17:00 rollover (no swap)
SESSIONS = {"index": (time(9, 30), time(16, 0)), "fx": (time(5, 0), time(17, 0))}
EXIT_DEFAULTS = {"index": time(15, 59), "fx": time(16, 59)}


@dataclass(frozen=True, slots=True)
class GapMomentumConfig:
    mode: str = "index"  # "index": cash session 09:30-16:00 ET; "fx": 05:00-17:00 ET
    zone: str = "America/New_York"  # time zone of the sessions (DST via zoneinfo)
    entry_z: float = 0.1  # gap beyond the prior high / low by this x sd (Chan); 0 = any gap beyond
    vol_days: int = 90  # sd of this many daily close-to-close log returns (Chan)
    atr_period: int = 14  # Wilder ATR over the daily sessions, for the stop
    stop_atr: float = 1.0  # stop = this x daily ATR from the entry (rule set by the user)
    target_r: float = 0.0  # take profit at this many R of the stop; 0 = none (Chan)
    exit_time: time | None = None  # signal exit at this candle's close; None = mode default
    # "momentum" = with the gap (spec); "fade" = research only: the other direction on the same
    # days with the same stop and exit (random-entry baseline, Monte Carlo kind B)
    side: str = "momentum"
    # the last candle of the previous session counts as its closing candle when it closes this
    # many minutes before the session end (FTMO gold ends 16:55 ET; user, 2026-10-20); 0 = strict
    close_tolerance_min: int = 10

    def __post_init__(self) -> None:
        ZoneInfo(self.zone)  # raises for an unknown zone
        if self.mode not in SESSIONS:
            raise ValueError("mode must be 'index' or 'fx'")
        if self.side not in ("momentum", "fade"):
            raise ValueError("side must be 'momentum' or 'fade'")
        if self.close_tolerance_min < 0:
            raise ValueError("close_tolerance_min must be >= 0")
        if self.entry_z < 0:
            raise ValueError("entry_z must be >= 0")
        if self.vol_days < 2:
            raise ValueError("vol_days must be >= 2")
        if self.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if self.stop_atr <= 0:
            raise ValueError("stop_atr must be > 0")
        if self.target_r < 0:
            raise ValueError("target_r must be >= 0")
        open_t, close_t = SESSIONS[self.mode]
        if not open_t < self.exit_time_resolved < close_t:
            raise ValueError(f"exit_time must be between {open_t:%H:%M} and {close_t:%H:%M}")

    @property
    def session_open(self) -> time:
        return SESSIONS[self.mode][0]

    @property
    def session_close(self) -> time:
        return SESSIONS[self.mode][1]

    @property
    def exit_time_resolved(self) -> time:
        return self.exit_time or EXIT_DEFAULTS[self.mode]
