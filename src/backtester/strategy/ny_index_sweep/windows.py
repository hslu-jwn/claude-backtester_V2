"""AM / PM trading windows of strategy 2.

Spec: strategy-ny-indices.md › General. Times are New York local times (zoneinfo
America/New_York, so they follow US DST; Europe's dates don't matter):
- AM: window 09:00-11:30, open 09:30, best time 09:50-10:10.
- PM: window 13:30-16:00, open 14:00, best time 13:50-14:10.
All are settings (`WindowConfig`). Windows exist Monday to Friday (New York date);
holidays have no candles, so nothing happens in them.

A candle belongs to the window it CLOSES in, `start < close <= end` (like sessions.py: the
1m candle closing at 09:00 is before the window, the one closing at 11:30 its last). An
entry is tagged "best time" when its time (the entry candle's close) is within the best
time, both edges included. Inputs and outputs are UTC.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from enum import Enum
from zoneinfo import ZoneInfo


class Window(Enum):
    AM = "am"
    PM = "pm"


@dataclass(frozen=True, slots=True)
class WindowTimes:
    start: time  # New York local time
    end: time
    open: time  # the index open the window is built around
    best_start: time  # best-time tag
    best_end: time

    def __post_init__(self) -> None:
        if not self.start < self.end:
            raise ValueError(f"window start {self.start} must be before its end {self.end}")
        if not self.best_start <= self.best_end:
            raise ValueError("best_start must not be after best_end")


@dataclass(frozen=True, slots=True)
class WindowConfig:
    am: WindowTimes = field(
        default_factory=lambda: WindowTimes(
            time(9), time(11, 30), time(9, 30), time(9, 50), time(10, 10)
        )
    )
    pm: WindowTimes = field(
        default_factory=lambda: WindowTimes(
            time(13, 30), time(16), time(14), time(13, 50), time(14, 10)
        )
    )
    zone: str = "America/New_York"

    def times(self, window: Window) -> WindowTimes:
        return self.am if window is Window.AM else self.pm


DEFAULT_WINDOWS = WindowConfig()


@dataclass(frozen=True, slots=True)
class TradingWindow:
    """One AM or PM window on one New York trading day; times in UTC."""

    kind: Window
    trading_date: date  # New York date
    start: datetime
    end: datetime
    open: datetime
    best_start: datetime
    best_end: datetime


def window_on(
    day: date, kind: Window, config: WindowConfig = DEFAULT_WINDOWS
) -> TradingWindow | None:
    """The `kind` window on New York date `day`; None on a weekend."""
    if day.weekday() >= 5:
        return None
    zone, t = ZoneInfo(config.zone), config.times(kind)

    def at(local: time) -> datetime:
        return datetime.combine(day, local, zone).astimezone(UTC)

    return TradingWindow(
        kind, day, at(t.start), at(t.end), at(t.open), at(t.best_start), at(t.best_end)
    )


def window_of(close: datetime, config: WindowConfig = DEFAULT_WINDOWS) -> TradingWindow | None:
    """The window a candle closing at `close` (UTC) belongs to: start < close <= end."""
    day = close.astimezone(ZoneInfo(config.zone)).date()
    for kind in Window:
        w = window_on(day, kind, config)
        if w is not None and w.start < close <= w.end:
            return w
    return None


def is_best_time(t: datetime, window: TradingWindow) -> bool:
    """`t` (an entry time, UTC) is within the window's best time, edges included."""
    return window.best_start <= t <= window.best_end


def windows_between(
    start: datetime, end: datetime, config: WindowConfig = DEFAULT_WINDOWS
) -> list[TradingWindow]:
    """Every window starting in [start, end), in time order."""
    zone = ZoneInfo(config.zone)
    day, last = start.astimezone(zone).date(), end.astimezone(zone).date()
    out = []
    while day <= last:
        for kind in Window:
            w = window_on(day, kind, config)
            if w is not None and start <= w.start < end:
                out.append(w)
        day += timedelta(days=1)
    return out
