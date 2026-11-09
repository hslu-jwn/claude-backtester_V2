"""Calendar day filters of strategy 10 (FOMC, turn of month, pre-holiday) from CSV files.

Spec: docs/strategy-timed-hold.md › Qualifying day. The calendars are published in advance,
so asking them about today's date at the entry time is not lookahead.
"""

from __future__ import annotations

import csv
from calendar import monthrange
from datetime import date, timedelta
from pathlib import Path

from backtester.strategy.timed_hold.config import TimedHoldConfig

DEFAULT_DIR = Path(__file__).parent / "calendars"


def _read(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"calendar file missing for this day_filter: {path}")
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class DayFilter:
    """`qualifies(day)` for the config's day_filter; loads only the file the filter needs."""

    def __init__(self, config: TimedHoldConfig):
        self.kind, self.tom_after = config.day_filter, config.tom_days_after
        self.month_day, self.trading_days = config.month_day, config.trading_days
        folder = Path(config.calendar_dir) if config.calendar_dir else DEFAULT_DIR
        self._fomc: set[date] = set()
        self._closed: set[date] = set()
        self._short_days: set[date] = set()
        if self.kind == "fomc":
            rows = _read(folder / "fomc_statements.csv")
            self._fomc = {
                date.fromisoformat(r["date"])
                for r in rows
                if r["scheduled"].strip().lower() == "true"
            }
        if (self.kind in ("turn_of_month", "pre_holiday") or config.skip_nyse_short_days
                or config.trading_days == "nyse"):
            rows = _read(folder / "nyse_holidays.csv")
            self._closed = {
                date.fromisoformat(r["date"]) for r in rows if r["type"].strip() == "closed"
            }
            if config.skip_nyse_short_days:
                self._short_days = {
                    date.fromisoformat(r["date"]) for r in rows
                    if r["type"].strip() in ("closed", "early_close_13:00")
                }

    def _trading(self, d: date) -> bool:
        return d.weekday() < 5 and d not in self._closed

    def _next_trading(self, d: date) -> date:
        d += timedelta(days=1)
        while not self._trading(d):
            d += timedelta(days=1)
        return d

    def is_trading_day(self, d: date) -> bool:
        """Selected calendar for multi-day holds and month_day; early closes count.

        Spec: strategy-timed-hold.md > Definitions.
        """
        return d.weekday() < 5 and (self.trading_days == "weekdays" or d not in self._closed)

    def after_trading_days(self, d: date, count: int) -> date:
        """Calendar target, independent of missing candles. Entry date is day zero."""
        while count:
            d += timedelta(days=1)
            if self.is_trading_day(d):
                count -= 1
        return d

    def qualifies(self, d: date) -> bool:
        if d in self._short_days:
            return False
        if self.kind == "all":
            return True
        if self.kind == "fomc":
            return d in self._fomc
        if self.kind == "month_day":
            if not self.is_trading_day(d):
                return False
            days = [
                x for n in range(1, monthrange(d.year, d.month)[1] + 1)
                if self.is_trading_day(x := d.replace(day=n))
            ]
            index = self.month_day - 1 if self.month_day > 0 else self.month_day
            return -len(days) <= index < len(days) and days[index] == d
        if not self._trading(d):
            return False
        if self.kind == "turn_of_month":
            if self._next_trading(d).month != d.month:
                return True  # last trading day of the month
            n, x = 0, d.replace(day=1)
            while x <= d:  # trading days of this month up to and including d
                n += self._trading(x)
                x += timedelta(days=1)
            return n <= self.tom_after
        x = d + timedelta(days=1)  # pre_holiday: the next weekday is a full closure
        while x.weekday() >= 5:
            x += timedelta(days=1)
        return x in self._closed
