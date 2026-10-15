"""Settings of strategy 6 (opening-range breakout): every tunable value with its spec default.

Spec: docs/strategy-opening-range.md (rules chosen by Claude with the user's go, 2026-10-15).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, time
from enum import Enum
from types import MappingProxyType
from zoneinfo import ZoneInfo


class EntryMode(Enum):
    RANGE = "range"  # break of the high / low of the first `range_minutes`
    BAND = "band"  # break of the session-open close +/- band_atr x daily ATR


class NarrowDay(Enum):
    OFF = "off"
    NR4 = "nr4"  # the previous session was the narrowest of the last 4
    INSIDE = "inside"  # the previous session was inside the one before it


@dataclass(frozen=True, slots=True)
class SessionSpec:
    zone: str  # time zone of the session (DST via zoneinfo, each city on its own rules)
    open_time: time  # local wall time of the session open (the opening range starts here)
    exit_time: time  # an open trade closes at the close of the 1m candle closing at this time

    def __post_init__(self) -> None:
        ZoneInfo(self.zone)  # raises for an unknown zone
        if self.exit_time <= self.open_time:
            raise ValueError("exit_time must be after open_time")

    @property
    def length_minutes(self) -> int:
        d = date(2000, 1, 3)
        return int(
            (
                datetime.combine(d, self.exit_time) - datetime.combine(d, self.open_time)
            ).total_seconds()
            // 60
        )


# symbol -> market class (the key into `OpeningRangeConfig.sessions`), spec › Sessions
SYMBOL_CLASS = MappingProxyType(
    {
        **dict.fromkeys(("NAS100", "US500", "US30", "US2000"), "us_index"),
        **dict.fromkeys(("GER40", "EU50"), "frankfurt_index"),
        "UK100": "london_index",
        "JP225": "tokyo_index",
        **dict.fromkeys(
            (
                "GBPUSD", "GBPJPY", "EURUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF",
                "NZDUSD", "EURJPY", "EURGBP", "XAUUSD", "XAGUSD",
            ),
            "fx_metal",
        ),
    }
)  # fmt: skip

_NY = SessionSpec("America/New_York", time(9, 30), time(15, 55))


def _default_sessions() -> Mapping[str, Mapping[str, SessionSpec]]:
    return MappingProxyType(
        {
            "us_index": MappingProxyType({"new_york": _NY}),
            "frankfurt_index": MappingProxyType(
                {"frankfurt": SessionSpec("Europe/Berlin", time(9, 0), time(17, 25))}
            ),
            "london_index": MappingProxyType(
                {"london": SessionSpec("Europe/London", time(8, 0), time(16, 25))}
            ),
            "tokyo_index": MappingProxyType(
                {"tokyo": SessionSpec("Asia/Tokyo", time(9, 0), time(14, 55))}
            ),
            "fx_metal": MappingProxyType(
                {
                    "london": SessionSpec("Europe/London", time(8, 0), time(12, 0)),
                    "new_york": _NY,
                }
            ),
        }
    )


@dataclass(frozen=True, slots=True)
class OpeningRangeConfig:
    entry_mode: EntryMode = (
        EntryMode.RANGE
    )  # range: break of the opening range; band: of open +/- ATR band
    range_minutes: int = 15  # the opening range = high / low of the first N minutes of the session
    band_atr: float = 0.5  # band mode: the band is this x daily ATR from the open close
    atr_period: int = 14  # Wilder ATR over this session's own daily ranges
    entry_window_minutes: int = 120  # signals only until this many minutes after the open
    max_reversals: int = 0  # 1: after a stop-out a close beyond the other side trades the other way
    target_r: float = (
        0.0  # take profit in R of the stop distance (0 = none, exit at the session end)
    )
    max_range_atr: float = 0.0  # range mode: skip when the range is wider than this x ATR (0 = off)
    narrow_day_filter: NarrowDay = NarrowDay.OFF  # trade only after a narrow (nr4) or inside day
    min_rel_volume: float = 0.0  # signal tick volume at least this x its usual value (0 = off)
    volume_lookback: int = 20  # sessions averaged for the usual tick volume of that minute
    # market class -> session name -> session (FX and metals trade two sessions a day)
    sessions: Mapping[str, Mapping[str, SessionSpec]] = field(default_factory=_default_sessions)

    def __post_init__(self) -> None:
        if self.range_minutes < 1:
            raise ValueError("range_minutes must be >= 1")
        if self.band_atr <= 0:
            raise ValueError("band_atr must be > 0")
        if self.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if self.entry_window_minutes < 1:
            raise ValueError("entry_window_minutes must be >= 1")
        if self.entry_mode is EntryMode.RANGE and self.entry_window_minutes <= self.range_minutes:
            raise ValueError("entry_window_minutes must be > range_minutes in range mode")
        if not 0 <= self.max_reversals <= 1:
            raise ValueError("max_reversals must be 0 or 1")
        if self.target_r < 0:
            raise ValueError("target_r must be >= 0")
        if self.max_range_atr < 0:
            raise ValueError("max_range_atr must be >= 0")
        if self.min_rel_volume < 0:
            raise ValueError("min_rel_volume must be >= 0")
        if self.volume_lookback < 1:
            raise ValueError("volume_lookback must be >= 1")
        for market in self.sessions.values():
            for spec in market.values():
                if self.entry_window_minutes >= spec.length_minutes:
                    raise ValueError("entry_window_minutes must be shorter than every session")
