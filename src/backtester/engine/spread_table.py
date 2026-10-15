"""Spread by year and hour of day. Spec: ROADMAP.md › 6.7; risk-management.md › Costs.

The fixed spread of `SymbolCosts` is one number per symbol. FTMO's real spread changes over
the years and over the day (wide at the 17:00 New York rollover, tighter in London / New
York hours), so a table can give the spread of the entry time instead:

    values[symbol][year][hour] = spread in price units

`year` and `hour` are the New York date and clock hour of the time asked for (the rollover
at 17:00 and the sessions follow that clock, DST included). A year outside the table takes the
nearest year that has the hour (a tie takes the later year), an hour no year has gives None
and the cost model uses the fixed spread. The table is built from MT5's per-bar spread by
`tools/spread_table.py` (median or 90th percentile of the minute bars); this module only
looks values up.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

STATS = ("median", "p90")
HOURS_PER_DAY = 24


@dataclass(frozen=True)
class SpreadTable:
    values: Mapping[str, Mapping[int, Mapping[int, float]]]
    zone: str = "America/New_York"
    stat: str = "median"  # which statistic of the bar spreads the values are
    note: str = ""  # where it comes from (symbol names, period)
    _years: dict[str, list[int]] = field(init=False, repr=False, compare=False, hash=False)

    def __post_init__(self) -> None:
        if self.stat not in STATS:
            raise ValueError(f"stat must be one of {STATS}")
        years = {}
        for symbol, by_year in self.values.items():
            for year, by_hour in by_year.items():
                for hour, value in by_hour.items():
                    if not 0 <= hour < HOURS_PER_DAY:
                        raise ValueError(f"{symbol} {year}: hour {hour} is not in 0..23")
                    if not math.isfinite(value) or value < 0:
                        raise ValueError(f"{symbol} {year} {hour}: bad spread {value}")
            years[symbol] = sorted(by_year)
        object.__setattr__(self, "_years", years)

    def spread_at(self, symbol: str, at: datetime) -> float | None:
        """The spread in price units at the aware time `at`, or None if the table has no
        value for that symbol and hour in any year."""
        if at.tzinfo is None:
            raise ValueError("spread_at needs an aware datetime")
        by_year = self.values.get(symbol)
        if not by_year:
            return None
        local = at.astimezone(ZoneInfo(self.zone))
        # nearest year first, the later one on a tie
        order = sorted(self._years[symbol], key=lambda y: (abs(y - local.year), -y))
        for year in order:
            value = by_year[year].get(local.hour)
            if value is not None:
                return float(value)
        return None

    def to_dict(self) -> dict:
        return {
            "zone": self.zone,
            "stat": self.stat,
            "note": self.note,
            "values": {
                symbol: {
                    str(year): {str(h): v for h, v in sorted(by_hour.items())}
                    for year, by_hour in sorted(by_year.items())
                }
                for symbol, by_year in self.values.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping) -> SpreadTable:
        values = {
            symbol: {
                int(year): {int(h): float(v) for h, v in by_hour.items()}
                for year, by_hour in by_year.items()
            }
            for symbol, by_year in data["values"].items()
        }
        return cls(
            values=values,
            zone=data.get("zone", "America/New_York"),
            stat=data.get("stat", "median"),
            note=data.get("note", ""),
        )
