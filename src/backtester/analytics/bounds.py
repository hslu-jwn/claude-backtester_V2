"""Pure iid BCa diagnostics. Spec: research-runner.md > Skill vs trend, and bounds."""

from dataclasses import asdict, dataclass
from statistics import NormalDist

import numpy as np

from backtester.analytics.stationarity import t_p_value


@dataclass(frozen=True)
class BoundsConfig:
    boots: int = 5000
    seed: int = 42

    def __post_init__(self):
        if not isinstance(self.boots, int) or self.boots < 1:
            raise ValueError("boots must be a positive integer")


def _sample(values):
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError("sample must be one dimensional and finite")
    return x


def _result(x, cfg, estimate):
    return {
        "n": len(x),
        "estimate": estimate,
        "lower90_bca": None,
        "lower95_bca": None,
        "method": "iid BCa, jackknife acceleration",
        "config": asdict(cfg),
        "reason": None,
    }


def _bca(result, draws, jack):
    if not np.isfinite(draws).all() or not np.isfinite(jack).all():
        result["reason"] = "undefined bootstrap or jackknife log PF replicate"
        return result
    estimate = result["estimate"]
    if np.all(draws == estimate):
        result.update(lower90_bca=estimate, lower95_bca=estimate)
        return result
    normal = NormalDist()
    probability = (
        np.count_nonzero(draws < estimate) + 0.5 * np.count_nonzero(draws == estimate)
    ) / len(draws)
    probability = np.clip(probability, 0.5 / len(draws), 1 - 0.5 / len(draws))
    z0 = normal.inv_cdf(float(probability))
    delta = jack.mean() - jack
    scale = np.max(np.abs(delta))
    delta = delta / scale if scale else delta
    denominator = 6 * np.sum(delta**2) ** 1.5
    acceleration = float(np.sum(delta**3) / denominator) if denominator else 0.0
    for confidence in (90, 95):
        z = normal.inv_cdf(1 - confidence / 100)
        divisor = 1 - acceleration * (z0 + z)
        if divisor <= 0:
            result["reason"] = "BCa transformation is singular"
            continue
        p = normal.cdf(z0 + (z0 + z) / divisor)
        result[f"lower{confidence}_bca"] = float(np.quantile(draws, p))
    return result


def _draws(x, cfg, statistic):
    rng = np.random.default_rng(cfg.seed)
    out = []
    # Bound temporary memory for long daily histories/trade lists.
    chunk = max(1, 1_000_000 // len(x))
    for offset in range(0, cfg.boots, chunk):
        sample = x[rng.integers(len(x), size=(min(chunk, cfg.boots - offset), len(x)))]
        out.append(statistic(sample))
    return np.concatenate(out)


def _t_quantile(confidence, df):
    left, right = 0.0, 1.0
    target = 2 * (1 - confidence)
    while t_p_value(right, df) > target:
        right *= 2
    for _ in range(70):
        middle = (left + right) / 2
        if t_p_value(middle, df) > target:
            left = middle
        else:
            right = middle
    return (left + right) / 2


def mean_bounds(values, config=None):
    """One-sided mean bounds; constants are exact, n < 2 unavailable."""
    cfg = config or BoundsConfig()
    x = _sample(values)
    estimate = float(x.mean()) if len(x) else None
    result = _result(x, cfg, estimate)
    result.update(lower90_t=None, lower95_t=None)
    if len(x) < 2:
        result["reason"] = "fewer than two observations"
        return result
    se = float(x.std(ddof=1) / np.sqrt(len(x)))
    for confidence in (90, 95):
        result[f"lower{confidence}_t"] = estimate - _t_quantile(confidence / 100, len(x) - 1) * se
    jack = (x.sum() - x) / (len(x) - 1)
    return _bca(result, _draws(x, cfg, lambda a: a.mean(axis=1)), jack)


def _log_ratio(wins, losses):
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where((wins > 0) & (losses > 0), np.log(wins) - np.log(losses), np.nan)


def log_pf_bounds(values, config=None):
    """Bootstrap log PF, never PF; undefined replicates invalidate bounds."""
    cfg = config or BoundsConfig()
    x = _sample(values)
    wins, losses = np.maximum(x, 0), np.maximum(-x, 0)
    estimate = float(_log_ratio(wins.sum(), losses.sum()))
    result = _result(x, cfg, estimate if np.isfinite(estimate) else None)
    if result["estimate"] is None:
        result["reason"] = "log PF needs both a winning and a losing day"
        return result
    jack = _log_ratio(wins.sum() - wins, losses.sum() - losses)
    draws = _draws(
        x, cfg, lambda a: _log_ratio(np.maximum(a, 0).sum(axis=1), np.maximum(-a, 0).sum(axis=1))
    )
    return _bca(result, draws, jack)
