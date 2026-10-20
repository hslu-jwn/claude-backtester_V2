"""Probabilistic and deflated Sharpe ratio on a net R series (since ROADMAP 12.13 the daily net R, `analytics/daily.py`). Pure math, no plotting.

Spec: risk-management.md > Trial log and deflated Sharpe (ROADMAP 12.10); López de Prado,
*Advances in Financial Machine Learning* 14.7. Sharpe = mean / sample sd of the series (not
annualised), n = its length (days), skew g3 and kurtosis g4 (not excess: normal = 3).

    PSR(SR*) = Phi((SR - SR*) sqrt(n - 1) / sqrt(1 - g3 SR + (g4 - 1) / 4 SR^2))
    DSR      = PSR(SR0), SR0 = sqrt(V) ((1 - gamma) Phi^-1(1 - 1/N) + gamma Phi^-1(1 - 1/(N e)))
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import NormalDist

_NORMAL = NormalDist()
EULER_GAMMA = 0.5772156649015329  # Euler-Mascheroni constant (spec: 0.5772)


@dataclass(frozen=True, slots=True)
class DeflatedSharpeConfig:
    dsr_min: float = 0.95  # spec: check 7 passes at DSR >= 0.95
    min_sharpes: int = 2  # spec: V from the family's Sharpes when at least this many exist
    euler_gamma: float = EULER_GAMMA


@dataclass(frozen=True, slots=True)
class TradeStats:
    n: int
    mean: float | None
    sd: float | None  # sample sd
    skew: float | None  # g3
    kurt: float | None  # g4, not excess
    sharpe: float | None  # mean / sd


@dataclass(frozen=True, slots=True)
class DeflatedResult:
    psr0: float | None
    dsr: float | None
    n_trials: int  # N, at least 1
    variance: float | None  # V
    sr0: float | None


def trade_stats(r_net: Sequence[float]) -> TradeStats:
    """Mean, sample sd, skewness, kurtosis and Sharpe of the values; skew, kurtosis and Sharpe
    are None for fewer than 2 values or zero spread."""
    n = len(r_net)
    if n == 0:
        return TradeStats(0, None, None, None, None, None)
    mean = sum(r_net) / n
    if n < 2:
        return TradeStats(n, mean, None, None, None, None)
    m2 = sum((v - mean) ** 2 for v in r_net) / n
    if m2 <= 0:
        return TradeStats(n, mean, 0.0, None, None, None)
    sd = math.sqrt(m2 * n / (n - 1))
    skew = sum((v - mean) ** 3 for v in r_net) / n / m2**1.5
    kurt = sum((v - mean) ** 4 for v in r_net) / n / m2**2
    return TradeStats(n, mean, sd, skew, kurt, mean / sd)


def psr(sharpe: float, sr_star: float, n: int, skew: float, kurt: float) -> float | None:
    """Probabilistic Sharpe ratio; None for n < 2 or a non-positive denominator."""
    if n < 2:
        return None
    denominator = 1 - skew * sharpe + (kurt - 1) / 4 * sharpe**2
    if denominator <= 0:
        return None
    return _NORMAL.cdf((sharpe - sr_star) * math.sqrt(n - 1) / math.sqrt(denominator))


def expected_max_sharpe(
    n_trials: int, variance: float, config: DeflatedSharpeConfig | None = None
) -> float:
    """SR0: expected maximum Sharpe of `n_trials` zero-skill trials with Sharpe variance V."""
    if n_trials <= 1:
        return 0.0
    g = (config or DeflatedSharpeConfig()).euler_gamma
    return math.sqrt(variance) * (
        (1 - g) * _NORMAL.inv_cdf(1 - 1 / n_trials)
        + g * _NORMAL.inv_cdf(1 - 1 / (n_trials * math.e))
    )


def deflated_sharpe(
    stats: TradeStats,
    n_trials: int,
    family_sharpes: Sequence[float],
    config: DeflatedSharpeConfig | None = None,
) -> DeflatedResult:
    """PSR(0) and DSR of the evaluated run. V = sample variance of `family_sharpes` when there
    are `min_sharpes` or more, otherwise 1 / n of the run (chosen by Claude 2026-10-16)."""
    cfg = config or DeflatedSharpeConfig()
    n_trials = max(1, n_trials)
    if stats.sharpe is None or stats.skew is None or stats.kurt is None:
        return DeflatedResult(None, None, n_trials, None, None)
    if len(family_sharpes) >= cfg.min_sharpes:
        v = statistics.variance(family_sharpes)
    else:
        v = 1 / stats.n
    sr0 = expected_max_sharpe(n_trials, v, cfg)
    psr0 = psr(stats.sharpe, 0.0, stats.n, stats.skew, stats.kurt)
    dsr = psr(stats.sharpe, sr0, stats.n, stats.skew, stats.kurt)
    return DeflatedResult(psr0, dsr, n_trials, v, sr0)
