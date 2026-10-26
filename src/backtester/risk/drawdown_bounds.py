"""Pure double-bootstrap daily-R bounds. Spec: risk-management.md > Monte Carlo report.

Masters ch.6: outer plausible histories, inner future-horizon drawdown quantiles.
R is additive; percentage bounds use fixed risk without compounding.
"""

from dataclasses import asdict, dataclass
from math import isfinite

import numpy as np

from backtester.risk.bootstrap import stationary_orders, validate_block_days


@dataclass(frozen=True, slots=True)
class DrawdownBoundsConfig:
    outer: int = 200
    inner: int = 1000
    horizon_days: int = 126
    block_days: float = 5.0
    seed: int = 42
    quantiles: tuple[float, ...] = (0.5, 0.9, 0.95, 0.99)
    risk_levels: tuple[float, ...] = (0.005, 0.01, 0.015)

    def __post_init__(self) -> None:
        for v in (self.outer, self.inner, self.horizon_days):
            if not isinstance(v, int) or isinstance(v, bool) or v < 1:
                raise ValueError("outer, inner and horizon_days must be positive integers")
        validate_block_days(self.block_days)
        if (
            not self.quantiles
            or any(not 0 < q < 1 for q in self.quantiles)
            or tuple(sorted(set(self.quantiles))) != self.quantiles
        ):
            raise ValueError("quantiles must be increasing unique fractions in (0, 1)")
        if not self.risk_levels or any(not isfinite(r) or not 0 < r < 1 for r in self.risk_levels):
            raise ValueError("risk_levels must be nonempty finite fractions in (0, 1)")


def max_drawdown_r(paths: np.ndarray) -> np.ndarray:
    """Additive peak-to-trough R per row, including the initial zero equity peak."""
    paths = np.asarray(paths, dtype=float)
    if paths.ndim != 2 or not np.isfinite(paths).all():
        raise ValueError("paths must be a finite two-dimensional R array")
    equity = np.cumsum(paths, axis=1)
    if not paths.shape[1]:
        return np.zeros(paths.shape[0])
    peaks = np.maximum(0, np.maximum.accumulate(equity, axis=1))
    return np.max(peaks - equity, axis=1)


def drawdown_bounds(daily_r, config: DrawdownBoundsConfig | None = None) -> dict:
    """q x outer confidence table; Spec: risk-management.md > Double-bootstrap bounds.

    Process one outer history at a time to keep memory bounded by inner x horizon.
    """
    config = config or DrawdownBoundsConfig()
    data = np.asarray(daily_r, dtype=float)
    if data.ndim != 1 or not np.isfinite(data).all():
        raise ValueError("daily_r must be a finite one-dimensional series")
    result = {
        "status": "ok" if len(data) else "unavailable",
        "days": len(data),
        "config": asdict(config),
        "rows": [],
    }
    if not len(data):
        result["reason"] = "no daily observations"
        return result
    rng = np.random.default_rng(config.seed)
    histories = stationary_orders(len(data), config.outer, len(data), rng, config.block_days)
    estimates = np.empty((config.outer, len(config.quantiles)))
    for k, indices in enumerate(histories):
        future = stationary_orders(
            len(data), config.inner, config.horizon_days, rng, config.block_days
        )
        dd = max_drawdown_r(data[indices][future])
        estimates[k] = np.quantile(dd, config.quantiles)
    bounds = np.quantile(estimates, (0.5, 0.9, 0.95), axis=0).T
    names = ("median", "upper90", "upper95")
    for q, values in zip(config.quantiles, bounds, strict=True):
        result["rows"].append(
            {
                "q": q,
                "bounds_r": dict(zip(names, values.tolist(), strict=True)),
                "bounds_pct": {
                    str(r): dict(zip(names, (values * r * 100).tolist(), strict=True))
                    for r in config.risk_levels
                },
            }
        )
    return result
