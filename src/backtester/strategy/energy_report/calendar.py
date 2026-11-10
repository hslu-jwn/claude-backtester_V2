"""Report proxy calendar. Spec: strategy-energy_report.md > Calendar.

Federal observed dates follow OPM's Monday-Friday calendar, Juneteenth from 2021.
NYSE full closures, including exceptional closures, reuse the repository CSV.
"""
from __future__ import annotations

import csv
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from backtester.strategy.timed_hold.day_filter import DEFAULT_DIR


def _nth(year: int, month: int, weekday: int, n: int) -> date:
    first = date(year, month, 1)
    return first + timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


def _observed(d: date) -> date:
    return d + timedelta(days={5: -1, 6: 1}.get(d.weekday(), 0))


@lru_cache(maxsize=64)
def federal_holidays(year: int) -> frozenset[date]:
    """Nationwide observed dates only; neighboring years cover observed New Year."""
    days = set()
    for y in (year - 1, year, year + 1):
        fixed = [(1, 1), (7, 4), (11, 11), (12, 25)]
        if y >= 2021:
            fixed.append((6, 19))
        days.update(_observed(date(y, m, d)) for m, d in fixed)
        days.update((_nth(y, 1, 0, 3), _nth(y, 2, 0, 3),
                     _nth(y, 9, 0, 1), _nth(y, 10, 0, 2), _nth(y, 11, 3, 4)))
        last = date(y, 5, 31)
        days.add(last - timedelta(days=last.weekday()))
    return frozenset(d for d in days if d.year == year)


class ReportCalendar:
    def __init__(self, calendar_dir: str = ""):
        folder = Path(calendar_dir) if calendar_dir else DEFAULT_DIR
        with (folder / "nyse_holidays.csv").open(newline="", encoding="utf-8") as stream:
            self.closed = frozenset(date.fromisoformat(r["date"]) for r in csv.DictReader(stream)
                                    if r["type"].strip() == "closed")

    def qualifies(self, day: date, days: str) -> bool:
        if days == "control":
            return day.weekday() in (1, 3) and day not in self.closed
        if days != "report":
            raise ValueError("days must be report or control")
        if day.weekday() != 2:
            return False
        return not any(d in self.closed or d in federal_holidays(d.year)
                       for d in (day - timedelta(days=n) for n in (2, 1, 0)))
