"""Calendar day filters of strategy 10 (FOMC, turn of month, pre-holiday) from CSV files.

Spec: docs/strategy-timed-hold.md › Qualifying day. The calendars are published in advance,
so asking them about today's date at the entry time is not lookahead.
"""

from __future__ import annotations

import csv
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
        folder = Path(config.calendar_dir) if config.calendar_dir else DEFAULT_DIR
        self._fomc: set[date] = set()
        self._closed: set[date] = set()
        if self.kind == "fomc":
            rows = _read(folder / "fomc_statements.csv")
            self._fomc = {
                date.fromisoformat(r["date"])
                for r in rows
                if r["scheduled"].strip().lower() == "true"
            }
        elif self.kind in ("turn_of_month", "pre_holiday"):
            rows = _read(folder / "nyse_holidays.csv")
            self._closed = {
                date.fromisoformat(r["date"]) for r in rows if r["type"].strip() == "closed"
            }

    def _trading(self, d: date) -> bool:
        return d.weekday() < 5 and d not in self._closed

    def _next_trading(self, d: date) -> date:
        d += timedelta(days=1)
        while not self._trading(d):
            d += timedelta(days=1)
        return d

    def qualifies(self, d: date) -> bool:
        if self.kind == "all":
            return True
        if self.kind == "fomc":
            return d in self._fomc
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
