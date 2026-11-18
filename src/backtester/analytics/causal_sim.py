"""T-22 causal simulation tests for our estimators. Spec: research-runner.md > Causal simulation tests (T-22).

Generators after López de Prado, Causal Factor Investing ch.7 / appendix B (n 5,000, normal draws): a fork, a
collider and a chain with a confounded mediator, where the right specification shows no effect and a wrong control
shows a "significant" one; plus a true effect that must be recovered. `ols` is the plain estimator the checks use.
"""

import numpy as np


def ols(y, xs):
    """OLS with an intercept: {"beta", "se", "t"} per regressor in `xs` order, and "intercept"."""
    y = np.asarray(y, float)
    X = np.column_stack([np.ones(len(y))] + [np.asarray(x, float) for x in xs])
    n, k = X.shape
    if X.shape[0] != len(y) or any(len(np.asarray(x)) != n for x in xs) or n <= k + 1:
        raise ValueError("need equal lengths and n > regressors + 2")
    if not (np.isfinite(y).all() and np.isfinite(X).all()):
        raise ValueError("inputs must be finite")
    if np.linalg.matrix_rank(X) < k:
        raise ValueError("regressors are collinear")
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ b
    cov = resid @ resid / (n - k) * np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    with np.errstate(
        divide="ignore", invalid="ignore"
    ):  # perfect fit: se 0 -> t +-inf (or nan for beta 0)
        t = b[1:] / se[1:]
    return {"intercept": float(b[0]), "beta": b[1:], "se": se[1:], "t": t}


def _rng(seed, n):
    return np.random.default_rng(seed), n


def fork(seed=0, n=5000):
    """Z -> X, Z -> Y; X has no effect on Y."""
    rng, n = _rng(seed, n)
    z = rng.standard_normal(n)
    return {"z": z, "x": z + rng.standard_normal(n), "y": z + rng.standard_normal(n)}


def collider(seed=0, n=5000):
    """X -> Z <- Y; X and Y independent."""
    rng, n = _rng(seed, n)
    x, y = rng.standard_normal(n), rng.standard_normal(n)
    return {"x": x, "y": y, "z": x + y + rng.standard_normal(n)}


def confounded_mediator(seed=0, n=5000, effect=0.0):
    """X -> Z -> Y (Z's effect on Y = `effect`), W -> Z, W -> Y; W unobserved."""
    rng, n = _rng(seed, n)
    x, w = rng.standard_normal(n), rng.standard_normal(n)
    z = x + w + rng.standard_normal(n)
    return {"x": x, "z": z, "y": effect * z + w + rng.standard_normal(n)}


def true_effect(seed=0, n=5000, beta=0.1):
    """X -> Y with slope `beta`; nothing else."""
    rng, n = _rng(seed, n)
    x = rng.standard_normal(n)
    return {"x": x, "y": beta * x + rng.standard_normal(n)}
