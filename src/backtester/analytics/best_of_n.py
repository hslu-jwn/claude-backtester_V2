"""Spec: research-runner.md > Significance of the best variant. Pure MTM diagnostics."""

from dataclasses import dataclass

import numpy as np

from backtester.analytics.bootstrap import stationary_orders, validate_block_days


def daily_matrix(values) -> np.ndarray:
    """Validate a finite days x variants matrix without modifying the input."""
    matrix = np.asarray(values, dtype=float)
    if matrix.ndim != 2 or not np.isfinite(matrix).all():
        raise ValueError("daily matrix must be finite and two-dimensional (days x variants)")
    return matrix


@dataclass(frozen=True)
class RealityCheckConfig:
    boots: int = 2000
    block_days: float = 5
    seed: int = 42
    batch_size: int = 64

    def __post_init__(self):
        for name in ("boots", "batch_size"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        validate_block_days(self.block_days)


def reality_check(values, config: RealityCheckConfig | None = None) -> dict:
    """White's centred max-mean stationary bootstrap with synchronous day indices.

    Spec: research-runner.md > Significance of the best variant.
    Batch index counts keep memory bounded without materialising boots x days x variants.
    """
    cfg = config or RealityCheckConfig()
    matrix = daily_matrix(values)
    days, variants = matrix.shape
    if days < 2 or variants < 1:
        return {"p_value": None, "reason": "requires at least two days and one variant"}
    means = matrix.mean(axis=0)
    observed = float(means.max())
    centred = matrix - means
    rng = np.random.default_rng(cfg.seed)
    exceed = 0
    for start in range(0, cfg.boots, cfg.batch_size):
        count = min(cfg.batch_size, cfg.boots - start)
        orders = stationary_orders(days, count, days, rng, cfg.block_days)
        weights = np.array([np.bincount(order, minlength=days) for order in orders])
        maxima = (weights @ centred / days).max(axis=1)
        exceed += int(np.count_nonzero(maxima >= observed))
    return {
        "p_value": (1 + exceed) / (cfg.boots + 1),
        "observed_max_mean": observed,
        "boots": cfg.boots,
        "block_days": cfg.block_days,
        "seed": cfg.seed,
        "reason": None,
    }
