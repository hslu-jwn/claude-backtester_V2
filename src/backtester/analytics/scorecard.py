"""Scorecard of a trade list and its warning flags. Pure functions, no plotting.

Spec: research-runner.md > Scorecard, Warning flags (ROADMAP 6.1 + 6.2; rules set by the user,
2026-10-21). One row per variant and period in the research runner, and for any plain backtest
run (the Research page). Works on anything with the trade attributes `analytics/metrics.py` and
`analytics/robustness.py` read (`TradeResult`, `TradeRecord`).

`scorecard(trades, cfg, start, end)` gives (net R includes the swap):
- `trades`, `win_rate` (net result above 0), `avg_r` (net R per trade), `net_r`;
- `profit_factor`: gross win R / gross loss R, None without a losing trade (or without trades);
- `max_dd_r`: deepest fall of the cumulative net R (`metrics.max_drawdown`);
- `half_first_net_r` / `half_second_net_r`: the trades entered up to / after the period's middle
  year, (first year + last year) // 2; the period is `start`..`end`, else the first and last
  entry year of the trades; a half without trades is 0;
- `net_r_stressed`: net R with every trade's cost times `cost_stress` (`robustness.stressed_net`);
- `net_r_without_best`: net R without the single best trade.

`flags(row, cfg)` names the warnings of a scorecard row (the test row also carries `period` ==
"test" and its `verdict`, "green" / "yellow" / "red").
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from math import sqrt
from statistics import stdev

from backtester.analytics.metrics import summarize
from backtester.analytics.robustness import RobustnessConfig, stressed_net, without_best

SCORE_KEYS = (
    "trades", "win_rate", "avg_r", "net_r", "profit_factor", "max_dd_r",
    "half_first_net_r", "half_second_net_r", "net_r_stressed", "net_r_without_best",
    "se_avg_r", "time_in_market", "avg_hold_hours",
    "detrended_net_r", "lower95_mean_daily_r", "log_pf",
)  # fmt: skip

FLAG_TOO_FEW = "too_few_trades"
FLAG_HIGH_WIN_SMALL_EDGE = "high_win_rate_small_edge"
FLAG_HALF = "half_not_profitable"
FLAG_STRESSED = "not_profitable_costs_x"
FLAG_WITHOUT_BEST = "not_profitable_without_best"
FLAG_TEST_FAILED = "test_failed"
FLAG_LABELS = {
    "too_many_parameters": "more than 4 swept settings",
    "entry_screen_failed": "entries not better than chance",
    "declining_returns": "returns falling over time",
    "skill_is_trend": "positive result explained by market trend",
    FLAG_TOO_FEW: "too few trades",
    FLAG_HIGH_WIN_SMALL_EDGE: "high win rate, small edge",
    FLAG_HALF: "one half not profitable",
    FLAG_STRESSED: "not profitable with higher costs",
    FLAG_WITHOUT_BEST: "not profitable without the best trade",
    FLAG_TEST_FAILED: "test failed",
    "rc_not_significant": "best variant not significant (Reality Check)",
    "pbo_high": "high probability of backtest overfitting",
    "bayes_weak": "weak Bayesian evidence for positive mean R",
}


@dataclass(frozen=True, slots=True)
class ScorecardConfig:
    min_trades: int = 100  # spec: fewer trades = flag (the grid file's min_trades)
    high_win_rate: float = 0.70  # spec: win rate at or above this ...
    small_edge_avg_r: float = 0.10  # ... with an average net R below this = flag
    cost_stress: float = RobustnessConfig().cost_stress  # spec: costs x 1.5

    def __post_init__(self) -> None:
        if self.min_trades < 0:
            raise ValueError("min_trades must be >= 0")
        if not 0 <= self.high_win_rate <= 1:
            raise ValueError("high_win_rate must be in [0, 1]")
        if self.cost_stress < 1:
            raise ValueError("cost_stress must be >= 1")


def _weekday_seconds(start: datetime, end: datetime) -> float:
    """Elapsed UTC weekday seconds in [start, end)."""
    total = 0.0
    while start < end:
        boundary = min(datetime.combine(start.date() + timedelta(days=1), time(), UTC), end)
        if start.weekday() < 5:
            total += (boundary - start).total_seconds()
        start = boundary
    return total


def _holding_metrics(trades: Sequence, start: date | None, end: date | None) -> tuple:
    """Spec: research-runner.md > Scorecard additions: UTC weekday interval union."""
    intervals = sorted((t.entry_time.astimezone(UTC), t.exit_time.astimezone(UTC)) for t in trades)
    if any(b < a for a, b in intervals):
        raise ValueError("exit_time must not precede entry_time")
    average = (
        sum((b - a).total_seconds() for a, b in intervals) / len(intervals) / 3600
        if intervals
        else None
    )
    first = start or (intervals[0][0].date() if intervals else None)
    last = end or (max(b for _, b in intervals).date() if intervals else None)
    if first is None or last is None:
        return None, average
    left = datetime.combine(first, time(), UTC)
    right = datetime.combine(last + timedelta(days=1), time(), UTC)
    denominator = _weekday_seconds(left, right)
    merged = []
    for a, b in intervals:
        a, b = max(a, left), min(b, right)
        if b <= a:
            continue
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    occupied = sum(_weekday_seconds(a, b) for a, b in merged)
    return (occupied / denominator if denominator else None), average


def scorecard(
    trades: Sequence,
    config: ScorecardConfig | None = None,
    start: date | None = None,
    end: date | None = None,
) -> dict:
    cfg = config or ScorecardConfig()
    s = summarize(trades)
    years = (
        (start.year, end.year)
        if start is not None and end is not None
        else (min(t.entry_time.year for t in trades), max(t.entry_time.year for t in trades))
        if trades
        else (0, 0)
    )
    middle = (years[0] + years[1]) // 2
    occupancy, hold = _holding_metrics(trades, start, end)
    return {
        "trades": s["trades"],
        "win_rate": s["win_rate"],
        "avg_r": s["avg_r_net"],
        "net_r": s["net_r_net"],
        "profit_factor": s["profit_factor"],
        "max_dd_r": s["max_drawdown_r_net"],
        "half_first_net_r": sum(t.r_net for t in trades if t.entry_time.year <= middle),
        "half_second_net_r": sum(t.r_net for t in trades if t.entry_time.year > middle),
        "net_r_stressed": stressed_net(trades, cfg.cost_stress),
        "net_r_without_best": without_best(trades)["net_without_best"],
        "se_avg_r": stdev(t.r_net for t in trades) / sqrt(len(trades)) if len(trades) > 1 else None,
        "time_in_market": occupancy,
        "avg_hold_hours": hold,
        "detrended_net_r": None,
        "lower95_mean_daily_r": None,
        "log_pf": None,
    }


def flags(row: dict, config: ScorecardConfig | None = None) -> list[str]:
    """The warning flags of a scorecard row, in the spec's order."""
    cfg = config or ScorecardConfig()
    out = []
    detrended = row.get("detrended_net_r")
    if row.get("net_r", 0) > 0 and detrended is not None and detrended <= 0:
        out.append("skill_is_trend")
    if row["trades"] < cfg.min_trades:
        out.append(FLAG_TOO_FEW)
    win, avg = row.get("win_rate"), row.get("avg_r")
    if (
        win is not None
        and avg is not None
        and win >= cfg.high_win_rate
        and avg < cfg.small_edge_avg_r
    ):
        out.append(FLAG_HIGH_WIN_SMALL_EDGE)
    if min(row["half_first_net_r"], row["half_second_net_r"]) <= 0:
        out.append(FLAG_HALF)
    if row["net_r_stressed"] <= 0:
        out.append(FLAG_STRESSED)
    if row["net_r_without_best"] <= 0:
        out.append(FLAG_WITHOUT_BEST)
    if row.get("period") == "test" and (row["net_r"] <= 0 or row.get("verdict") == "red"):
        out.append(FLAG_TEST_FAILED)
    return out
