"""Read-only observation contracts. Spec: design/multi-symbol.md > Data contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from backtester.core.models import Timeframe
from backtester.core.series import SeriesView

if TYPE_CHECKING:
    from backtester.data.resample import DayBoundary, H4Alignment


def require_utc(now: datetime) -> None:
    if now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ValueError("market timestamps must be UTC")


@dataclass(frozen=True, slots=True)
class MarketCalendar:
    """Explicit local session; equal endpoints mean all day, never guessed holidays.

    Overnight sessions belong to their opening weekday/date. Breaks are local civil
    time intervals. This calendar reports observation availability, not execution rights.
    Spec: design/multi-symbol.md > Missing candles, sessions and freshness.
    """

    identifier: str = "always"
    timezone: str = "UTC"
    opens: time = time()
    closes: time = time()
    weekdays: tuple[int, ...] = (0, 1, 2, 3, 4)
    holidays: tuple[date, ...] = ()
    breaks: tuple[tuple[time, time], ...] = ()

    def __post_init__(self) -> None:
        ZoneInfo(self.timezone)
        if not self.identifier or not self.weekdays or any(d not in range(7) for d in self.weekdays):
            raise ValueError("calendar requires identifier and valid weekdays")
        if any(t.tzinfo is not None for t in (self.opens, self.closes, *sum(self.breaks, ()))):
            raise ValueError("calendar times must be local civil times")

    def is_open(self, now: datetime) -> bool:
        require_utc(now)
        local = now.astimezone(ZoneInfo(self.timezone))
        clock = local.time()
        day = local.date()
        if self.opens < self.closes:
            active = self.opens <= clock < self.closes
        elif self.opens > self.closes:
            active = clock >= self.opens or clock < self.closes
            if clock < self.closes:
                day -= timedelta(days=1)
        else:
            active = True
        for start, end in self.breaks:
            if (start <= clock < end) if start < end else (clock >= start or clock < end):
                return False
        return active and day.weekday() in self.weekdays and day not in self.holidays


@dataclass(frozen=True, slots=True)
class ReferenceInput:
    """Resolved, explicit input policy; no implicit age threshold or history length.

    `max_age` applies to every declared timeframe. Split policies into a future richer
    contract if a strategy needs different per-timeframe limits; do not infer them.
    Spec: design/multi-symbol.md > Declared dependencies.
    """

    symbol: str
    role: str
    timeframes: tuple[Timeframe, ...]
    max_age: timedelta
    boundary: DayBoundary | str = "UTC"
    h4_alignment: H4Alignment | str = "UTC"
    warmup_days: int = 0
    full_history: tuple[Timeframe, ...] = ()
    calendar: MarketCalendar = field(default_factory=lambda: MarketCalendar(weekdays=tuple(range(7))))
    min_candles: int = 1
    require_contiguous: bool = True
    required: bool = True

    def __post_init__(self) -> None:
        # Keep core independent of data/resample; the runner resolves these names.
        for name, allowed in (("boundary", {"UTC", "NEW_YORK_17"}),
                              ("h4_alignment", {"UTC", "NEW_YORK"})):
            value = getattr(self, name)
            value = value.name if isinstance(value, Enum) else value
            if value not in allowed:
                raise ValueError(f"invalid {name}: {value}")
            object.__setattr__(self, name, value)
        if not self.symbol or not self.role or not self.timeframes:
            raise ValueError("reference requires symbol, role and timeframes")
        if len(set(self.timeframes)) != len(self.timeframes):
            raise ValueError("duplicate reference timeframes")
        if Timeframe.M1 not in self.timeframes:
            raise ValueError("reference must declare M1 for coverage")
        if self.max_age < timedelta(0) or self.min_candles < 1 or self.warmup_days < 0:
            raise ValueError("invalid freshness or warm-up policy")
        if not set(self.full_history) <= set(self.timeframes):
            raise ValueError("full history timeframe not declared")


@dataclass(frozen=True, slots=True)
class Availability:
    status: str  # ready, closed, missing, not_ready
    ready: bool
    last_close_time: datetime | None
    age: timedelta | None
    cursor: int | None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class MarketView:
    """Fixed snapshot; only bounded SeriesViews cross the strategy boundary.

    `newly_closed` contains absolute index ranges since the previous snapshot. Process
    each with `views[symbol][tf].at(i)` to feed incremental detectors exactly once.
    Spec: design/multi-symbol.md > One logical clock, separate cursors.
    """

    now: datetime
    views: Mapping[str, Mapping[Timeframe, SeriesView | None]]
    availability: Mapping[str, Mapping[Timeframe, Availability]]
    newly_closed: Mapping[str, Mapping[Timeframe, range]]
    ready: bool
    reasons: tuple[str, ...]
