"""Server clock check per year against the histdata cache (ROADMAP 11.5)."""

from __future__ import annotations

from datetime import date

import pandas as pd

from backtester.data.adapters.mt5_adapter import ServerClock
from backtester.tools.mt5_clock_check import clock_report

NY7 = ServerClock("America/New_York", 7)


def weeks(rows):
    return pd.DataFrame(rows, columns=["week", "offset_h"])


def test_report_counts_hits_and_misses_per_year():
    frame = weeks(
        [
            (date(2018, 1, 8), 2),  # winter: UTC+2 fits
            (date(2018, 7, 9), 3),  # summer: UTC+3 fits
            (date(2018, 7, 16), 2),  # miss: observed 2 in summer
            (date(2019, 1, 7), 2),
        ]
    )
    report = clock_report(frame, NY7)
    y18 = report[report["year"] == 2018].iloc[0]
    assert (y18["weeks"], y18["hits"]) == (3, 2)
    assert y18["misses"] == "2018-07-16 (2h)"
    y19 = report[report["year"] == 2019].iloc[0]
    assert (y19["weeks"], y19["hits"], y19["misses"]) == (1, 1, "")


def test_report_of_no_weeks_is_empty():
    assert clock_report(weeks([]), NY7).empty
