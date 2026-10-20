"""Daily net R of a trade list: the one shared helper of the trial log, the Monte Carlo report and
the portfolio tool.

Spec: risk-management.md > Trial log and deflated Sharpe > Daily Sharpe (ROADMAP 12.13). A day is a
weekday of the period, cut at midnight `Europe/Prague`; a trade belongs to its exit day; a trade
exiting on a weekend moves to the next weekday, one outside the period to the first / last day;
days without trades are 0. `risk.monte_carlo.build_days` (kind A) follows the same rule (a test keeps
the two equal).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta
from zoneinfo import ZoneInfo

import numpy as np

PRAGUE = ZoneInfo("Europe/Prague")


def weekdays(start: date, end: date) -> list[date]:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def daily_net_r(trades: Sequence, start: date, end: date) -> np.ndarray:
    """Net R per weekday of start..end (trades need `exit_time` tz-aware and `r_net`)."""
    days = weekdays(start, end)
    out = np.zeros(len(days))
    if not days:
        return out
    for t in trades:
        day = t.exit_time.astimezone(PRAGUE).date()
        i = next((k for k, w in enumerate(days) if w >= day), len(days) - 1)
        out[i] += t.r_net
    return out
