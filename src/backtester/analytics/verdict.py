"""Monte Carlo verdict: seven checks, EDGE / WEAK / NO EDGE. Pure logic, no plotting.

Spec: risk-management.md > Monte Carlo report > Verdict (ROADMAP 12.7). The checks:

1. `t_stat`: mean net R per trade > 0 and t = mean / (sd / sqrt(n)) >= `t_min`;
2. `random_entries` (kind B): the strategy's percentile among the random-entry runs >=
   `percentile_min`;
3. `halves`: both halves' net R > 0 (the run's own period split at the middle date of start..end,
   `middle_date` / `period_halves`; rule set by the user 2026-10-15; a half without trades has net 0
   and fails);
4. `cost_stress`: net R with costs x `RobustnessConfig.cost_stress` > 0;
5. `without_best`: net R without the best trade > 0;
6. `random_fills` (kind C): median net R of the random-fill runs > 0;
7. `deflated_sharpe`: DSR >= `dsr_min` (rule set by the user 2026-10-16, ROADMAP 12.10; n/a when
   the DSR cannot be computed: fewer than 2 trades, zero sd or a non-positive denominator).

EDGE when every available check passes, WEAK when one or two fail, NO EDGE otherwise. A check
without input (None, e.g. kind B for a strategy that has no random-entry variant yet) is "n/a":
it is listed, counts neither as pass nor as fail, and the verdict then needs all available
checks (chosen by Claude 2026-10-15, to be confirmed by the user). Equality passes for the
three threshold checks (t == t_min, percentile == percentile_min, dsr == dsr_min); the net checks need > 0.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

CHECK_KEYS = (
    "t_stat", "random_entries", "halves", "cost_stress", "without_best", "random_fills",
    "deflated_sharpe",
)  # fmt: skip
EDGE, WEAK, NO_EDGE = "EDGE", "WEAK", "NO EDGE"


@dataclass(frozen=True, slots=True)
class VerdictConfig:
    t_min: float = 2.0  # spec: t >= 2
    percentile_min: float = 95.0  # spec: above 95 % of the random-entry runs
    net_min: float = 0.0  # the net checks need strictly more than this (R)
    dsr_min: float = 0.95  # spec: deflated Sharpe >= 0.95
    weak_max_fails: int = 2  # up to this many failed checks = WEAK

    def __post_init__(self) -> None:
        if not 0 <= self.percentile_min <= 100:
            raise ValueError("percentile_min must be in [0, 100]")
        if not 0 <= self.dsr_min <= 1:
            raise ValueError("dsr_min must be in [0, 1]")
        if self.weak_max_fails < 0:
            raise ValueError("weak_max_fails must be >= 0")


@dataclass(frozen=True, slots=True)
class VerdictInputs:
    mean_r: float | None  # mean net R per trade (None: no trades)
    t: float | None  # None: fewer than 2 trades or no variance
    percentile: float | None  # kind B; None = not available
    half_first_net: float
    half_second_net: float
    stressed_net: float
    net_without_best: float
    fill_median: float | None  # kind C median; None = not available
    dsr: float | None = None  # deflated Sharpe; None = not available


@dataclass(frozen=True, slots=True)
class Check:
    key: str
    label: str
    value: float | None  # the number shown (None: n/a or not computable)
    threshold: float
    passed: bool
    available: bool = True


@dataclass(frozen=True, slots=True)
class Verdict:
    label: str
    checks: tuple[Check, ...]
    failed: tuple[str, ...]  # keys of the failed checks
    not_available: tuple[str, ...]
    reason: str  # one plain-English line


def t_statistic(values: Sequence[float]) -> float | None:
    """mean / (sample sd / sqrt(n)); None for fewer than 2 values or no variance."""
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    if var <= 0:
        return None
    return mean / math.sqrt(var / n)


def middle_date(start: date, end: date) -> date:
    """Middle date of start..end (start + half the day span, rounded down)."""
    return start + timedelta(days=(end - start).days // 2)


def period_halves(trades: Sequence, start: date, end: date) -> tuple[float, float]:
    """Net R of the trades entered up to / after the middle date (the middle date is in the first
    half). A half without trades has net 0."""
    mid = middle_date(start, end)
    first = sum(t.r_net for t in trades if t.entry_time.date() <= mid)
    second = sum(t.r_net for t in trades if t.entry_time.date() > mid)
    return first, second


def _over(value: float | None, limit: float) -> bool:
    return value is not None and value > limit


def evaluate(inputs: VerdictInputs, config: VerdictConfig | None = None) -> Verdict:
    cfg = config or VerdictConfig()
    i = inputs
    weaker_half = min(i.half_first_net, i.half_second_net)
    fills_ok = _over(i.fill_median, cfg.net_min)
    checks = (
        Check(
            "t_stat", "Mean net R > 0 and t-statistic", i.t, cfg.t_min,
            _over(i.mean_r, cfg.net_min) and i.t is not None and i.t >= cfg.t_min,
        ),
        Check(
            "random_entries", "Net R above random entries (kind B, percentile)",
            i.percentile, cfg.percentile_min,
            i.percentile is not None and i.percentile >= cfg.percentile_min,
            available=i.percentile is not None,
        ),
        Check(
            "halves", "Both halves net positive (weaker half, R)", weaker_half, cfg.net_min,
            _over(weaker_half, cfg.net_min),
        ),
        Check(
            "cost_stress", "Net R positive with costs x stress", i.stressed_net, cfg.net_min,
            _over(i.stressed_net, cfg.net_min),
        ),
        Check(
            "without_best", "Net R positive without the best trade", i.net_without_best,
            cfg.net_min, _over(i.net_without_best, cfg.net_min),
        ),
        Check(
            "random_fills", "Median net R of random fills (kind C) > 0", i.fill_median,
            cfg.net_min, fills_ok, available=i.fill_median is not None,
        ),
        Check(
            "deflated_sharpe", "Deflated Sharpe ratio (DSR)", i.dsr, cfg.dsr_min,
            i.dsr is not None and i.dsr >= cfg.dsr_min, available=i.dsr is not None,
        ),
    )  # fmt: skip
    failed = tuple(c.key for c in checks if c.available and not c.passed)
    missing = tuple(c.key for c in checks if not c.available)
    label = EDGE if not failed else WEAK if len(failed) <= cfg.weak_max_fails else NO_EDGE
    return Verdict(label, checks, failed, missing, _reason(label, checks, failed, missing))


def _reason(label: str, checks: tuple[Check, ...], failed: tuple[str, ...], missing) -> str:
    names = {c.key: c.label for c in checks}
    available = sum(c.available for c in checks)
    if not failed:
        text = f"All {available} available checks pass."
    else:
        text = (
            f"{len(failed)} of {available} checks fail: "
            + "; ".join(names[k] for k in failed)
            + "."
        )
    if missing:
        text += " Not available (n/a, not counted): " + "; ".join(names[k] for k in missing) + "."
    return text
