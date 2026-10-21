"""Portfolio maths: several components' R trade lists as one weighted account list.

Spec: risk-management.md > Portfolio tool (ROADMAP 12.9; rules set by the user, 2026-10-20);
background: knowledge/topics/combining-edges.md (Carver's IDM = 1 / sqrt(w' H w), cap 2.5).
Pure functions, no plotting. Works on anything with `entry_time`, `exit_time` and `r_net`.

- Daily R: a component's net R per weekday, cut at midnight `Europe/Prague`, trades by exit day
  (the Monte Carlo kind A days, `risk.monte_carlo.build_days`).
- Correlation: Pearson over the whole period and over rolling `window_days` windows (min / median /
  max per pair); a series without variance has correlation 0 (not NaN) to every other series.
- Weights: equal (1 / number of components, never optimised). Each trade's R fields are multiplied by
  its component's weight, times the IDM only when `apply_idm`.
- N and V for the deflated Sharpe: the trials of all component families (`component_trials`).
"""

from __future__ import annotations

import copy
import fnmatch
import statistics
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np

from backtester.analytics.daily import daily_net_r
from backtester.analytics.trial_log import family_summary, read_all

# the R-valued fields of a trade that are scaled by the weight (when the trade has them)
R_FIELDS = ("r_gross", "r_net", "spread_r", "commission_r", "swap_r", "funding_r", "mae_r", "mfe_r")


@dataclass(frozen=True, slots=True)
class PortfolioConfig:
    window_days: int = 126  # rolling correlation window, trading days (about 6 months)
    idm_cap: float = 2.5  # spec: IDM capped at 2.5
    apply_idm: bool = False  # spec: off by default (it raises the risk)

    def __post_init__(self) -> None:
        if self.window_days < 3:
            raise ValueError("window_days must be >= 3")
        if self.idm_cap < 1:
            raise ValueError("idm_cap must be >= 1")


@dataclass(slots=True)
class PortfolioResult:
    names: list[str]
    weights: list[float]
    daily: list[np.ndarray]  # per component, net R per weekday (unweighted)
    corr: list[list[float]]  # whole period
    rolling: dict[tuple[int, int], dict]  # (i, j) -> windows / min / median / max
    idm: float  # shown: from the whole-period correlation, negatives floored at 0, capped
    idm_applied: float  # the factor in the merged list (1.0 unless apply_idm)
    trades: list = field(default_factory=list)  # weighted, merged, by exit time
    component_stats: list[dict] = field(default_factory=list)


def daily_r(trades: Sequence, start: date, end: date) -> np.ndarray:
    """Net R per weekday (the shared helper `analytics.daily.daily_net_r`, equal to the Monte Carlo
    kind A days; a test keeps them equal)."""
    return daily_net_r(trades, start, end)


def _corr(a: np.ndarray, b: np.ndarray) -> float | None:
    if a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def correlation_matrix(series: Sequence[np.ndarray]) -> np.ndarray:
    n = len(series)
    h = np.eye(n)
    for i in range(n):
        for j in range(i + 1, n):
            c = _corr(np.asarray(series[i], float), np.asarray(series[j], float))
            h[i, j] = h[j, i] = 0.0 if c is None else c
    return h


def rolling_correlation(series: Sequence[np.ndarray], config: PortfolioConfig) -> dict:
    """(i, j) -> {windows, min, median, max} of the correlation in every window of
    `window_days` consecutive days (step 1); windows where a series is flat are skipped."""
    out: dict[tuple[int, int], dict] = {}
    w = config.window_days
    for i in range(len(series)):
        for j in range(i + 1, len(series)):
            a, b = np.asarray(series[i], float), np.asarray(series[j], float)
            vals = [
                c
                for k in range(len(a) - w + 1)
                if (c := _corr(a[k : k + w], b[k : k + w])) is not None
            ]
            out[(i, j)] = (
                {"windows": len(vals), "min": min(vals), "median": float(np.median(vals)),
                 "max": max(vals)}
                if vals
                else {"windows": 0, "min": None, "median": None, "max": None}
            )  # fmt: skip
    return out


def equal_weights(n: int) -> list[float]:
    if n < 1:
        raise ValueError("no components")
    return [1.0 / n] * n


def idm(corr: np.ndarray, weights: Sequence[float], config: PortfolioConfig) -> float:
    """1 / sqrt(w' H w), H = `corr` with negative values floored at 0, capped at `idm_cap`."""
    h = np.clip(np.asarray(corr, float), 0.0, None)
    w = np.asarray(weights, float)
    return min(float(1.0 / np.sqrt(w @ h @ w)), config.idm_cap)


def weighted_trades(
    components: Sequence[Sequence], weights: Sequence[float], factor: float
) -> list:
    """Copies of all trades with their R fields x weight x `factor`, sorted by exit time."""
    out = []
    for trades, weight in zip(components, weights, strict=True):
        for t in trades:
            c = copy.copy(t)
            for name in R_FIELDS:
                if hasattr(t, name):
                    object.__setattr__(c, name, getattr(t, name) * weight * factor)
            out.append(c)
    out.sort(key=lambda t: t.exit_time)
    return out


def combine(
    components: dict[str, Sequence], start: date, end: date, config: PortfolioConfig | None = None
) -> PortfolioResult:
    """Daily R, correlations, equal weights, IDM and the merged weighted list."""
    cfg = config or PortfolioConfig()
    if not components:
        raise ValueError("no components")
    names = list(components)
    lists = [list(components[n]) for n in names]
    weights = equal_weights(len(names))
    daily = [daily_r(t, start, end) for t in lists]
    h = correlation_matrix(daily)
    factor = idm(h, weights, cfg)
    applied = factor if cfg.apply_idm else 1.0
    stats = []
    for name, trades, w in zip(names, lists, weights, strict=True):
        net = sum(t.r_net for t in trades)
        stats.append({
            "name": name, "weight": w, "trades": len(trades), "net_r": net,
            "r_per_trade": net / len(trades) if trades else None, "weighted_net_r": net * w * applied,
        })  # fmt: skip
    return PortfolioResult(
        names, weights, daily, h.tolist(), rolling_correlation(daily, cfg), factor, applied,
        weighted_trades(lists, weights, applied), stats,
    )  # fmt: skip


# ----- N and V -------------------------------------------------------------------------------


def _matches(family: str, pattern: str) -> bool:
    return fnmatch.fnmatchcase(family, pattern)


def component_trials(
    component_patterns: Sequence[Sequence[str]], paths: Sequence[Path | None]
) -> tuple[int, list[float]]:
    """(N, Sharpes) of the trial-log lines whose family matches any pattern of any component
    (`*` is a wildcard). The logs are merged, a line present twice (same key) counts once, a
    family named by two components counts once. N includes count-only lines."""
    patterns = [p for group in component_patterns for p in group]
    by_key = {}
    for path in paths:
        for r in read_all(path):
            by_key[r.key] = r
    lines = [r for r in by_key.values() if any(_matches(r.family, p) for p in patterns)]
    return family_summary(lines)


def family_counts(
    component_patterns: Sequence[Sequence[str]], paths: Sequence[Path | None]
) -> dict[str, int]:
    """Trials per matched family (for the report: which families made N)."""
    patterns = [p for group in component_patterns for p in group]
    by_key = {}
    for path in paths:
        for r in read_all(path):
            by_key[r.key] = r
    out: dict[str, int] = {}
    for r in by_key.values():
        if any(_matches(r.family, p) for p in patterns):
            out[r.family] = out.get(r.family, 0) + r.count
    return dict(sorted(out.items()))


def sharpe_variance(sharpes: Sequence[float]) -> float | None:
    return statistics.variance(sharpes) if len(sharpes) >= 2 else None
