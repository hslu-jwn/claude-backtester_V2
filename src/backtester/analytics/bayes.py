"""Diagnostic posteriors. Spec: research-runner.md > Bayesian view.

Normal-normal mean update uses sample variance as known, adjusted for overlap.
Win-rate BF integrates a one-sided prior, never the fitted posterior twice.
"""

from dataclasses import asdict, dataclass
from math import ceil, exp, isfinite, lgamma, log, log1p, sqrt
from statistics import NormalDist

import numpy as np

from backtester.analytics.effective_n import trade_uniqueness
from backtester.analytics.stationarity import _betacf, _betainc


@dataclass(frozen=True)
class BayesConfig:
    weak_strength: float = 20
    strong_strength: float = 100
    mean_prior_sd: float = 0.075
    prior_odds: float = 1 / 50
    target_odds: float = 10
    interval_mass: float = 0.95
    weak_threshold: float = 0.9
    draws: int = 20_000
    seed: int = 42

    def __post_init__(self):
        for name in (
            "weak_strength",
            "strong_strength",
            "mean_prior_sd",
            "prior_odds",
            "target_odds",
        ):
            value = getattr(self, name)
            if not isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if not 0 < self.interval_mass < 1 or not 0 <= self.weak_threshold <= 1:
            raise ValueError("invalid interval mass or probability threshold")
        if isinstance(self.draws, bool) or not isinstance(self.draws, int) or self.draws < 1:
            raise ValueError("draws must be a positive integer")
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError("seed must be a nonnegative integer")


def _log_beta(a, b):
    return lgamma(a) + lgamma(b) - lgamma(a + b)


def _log_cdf(x, a, b):
    """Log regularized incomplete beta, preserving tiny upper-tail evidence."""
    if x < (a + 1) / (a + b + 2):
        return a * log(x) + b * log1p(-x) - _log_beta(a, b) + log(_betacf(a, b, x) / a)
    return log1p(-_betainc(b, a, 1 - x))


def _quantile(q, a, b):
    lo, hi = 0.0, 1.0
    for _ in range(70):
        mid = (lo + hi) / 2
        if _betainc(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _safe_exp(value):
    try:
        result = exp(value)
    except OverflowError:
        return None
    return result if isfinite(result) else None


def trades_needed(p, p_star, config=None):
    """Total expected count, fixed-alternative KL planning (not integrated BF)."""
    cfg = config or BayesConfig()
    if not (0 < p_star < p <= 1):
        return None
    kl = p * log(p / p_star)
    if p < 1:
        kl += (1 - p) * log((1 - p) / (1 - p_star))
    return ceil(max(0, log(cfg.target_odds / cfg.prior_odds)) / kl) if kl > 0 else None


def report(trades, config=None):
    """Posteriors from closed trades, including unavailable reasons and raw/effective n."""
    cfg = config or BayesConfig()
    trades = list(trades)
    values = np.asarray([t.r_net for t in trades], dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("trade R must be finite")
    n = len(values)
    effective = trade_uniqueness(trades)["effective_trades"]
    wins = int((values > 0).sum())
    result = {
        "n": n,
        "effective_n": effective,
        "wins": wins,
        "p_star": None,
        "config": asdict(cfg),
        "win_rate": {},
        "mean_r": {
            "mean": None,
            "sd": None,
            "interval": None,
            "p_positive": None,
            "reason": "requires at least two trades and positive sample variance",
        },
        "evidence": {
            "bayes_factor": None,
            "posterior_odds": None,
            "reason": "requires both positive and negative payoffs",
        },
    }
    tail = (1 - cfg.interval_mass) / 2
    if n >= 2:
        sd = float(values.std(ddof=1))
        if sd > 0:
            se = sd / sqrt(effective)
            # Precision update expressed through sd to avoid squaring large sample variance.
            post_sd = 1 / np.hypot(1 / cfg.mean_prior_sd, 1 / se)
            shrinkage = float((post_sd / se) ** 2)
            mean = float(values.mean()) * shrinkage
            normal = NormalDist(mean, float(post_sd))
            result["mean_r"] = {
                "mean": mean,
                "sd": float(post_sd),
                "sample_sd": sd,
                "shrinkage": shrinkage,
                "interval": [normal.inv_cdf(tail), normal.inv_cdf(1 - tail)],
                "p_positive": NormalDist().cdf(mean / post_sd),
                "reason": None,
            }
    losses = values[values < 0]
    if wins and len(losses):
        w, loss = float(values[values > 0].mean()), -float(losses.mean())
        p = loss / (w + loss)
        result["p_star"] = p
        for name, a, b in (
            ("flat", 1, 1),
            ("weak", cfg.weak_strength * p, cfg.weak_strength * (1 - p)),
            ("strong", cfg.strong_strength * p, cfg.strong_strength * (1 - p)),
        ):
            alpha, beta = a + wins, b + n - wins
            result["win_rate"][name] = {
                "prior_alpha": a,
                "prior_beta": b,
                "alpha": alpha,
                "beta": beta,
                "mean": alpha / (alpha + beta),
                "interval": [_quantile(tail, alpha, beta), _quantile(1 - tail, alpha, beta)],
                "p_above": _betainc(beta, alpha, 1 - p),
            }
        strong = result["win_rate"]["strong"]
        a, b = strong["prior_alpha"], strong["prior_beta"]
        log_bf = (
            _log_beta(a + wins, b + n - wins)
            - _log_beta(a, b)
            - wins * log(p)
            - (n - wins) * log1p(-p)
            + _log_cdf(1 - p, b + n - wins, a + wins)
            - _log_cdf(1 - p, b, a)
        )
        needed = trades_needed(wins / n, p, cfg)
        result["evidence"] = {
            "bayes_factor": _safe_exp(log_bf),
            "log_bayes_factor": log_bf,
            "posterior_odds": _safe_exp(log_bf + log(cfg.prior_odds)),
            "log_posterior_odds": log_bf + log(cfg.prior_odds),
            "trades_needed": needed,
            "additional_trades": max(0, needed - n) if needed is not None else None,
            "reason": None,
        }
    return result


def compare(a, b, config=None):
    """Independent posterior approximation; A=reference, B=comparing family."""
    cfg = config or BayesConfig()
    return compare_posteriors(report(a, cfg), report(b, cfg), cfg)


def compare_posteriors(a, b, config=None):
    cfg = config or BayesConfig()
    rng = np.random.default_rng(cfg.seed)
    result = {
        "p_mean_b_gt_a": None,
        "p_win_b_gt_a": None,
        "draws": cfg.draws,
        "seed": cfg.seed,
        "reasons": {},
    }
    for kind, key in (("mean_r", "p_mean_b_gt_a"), ("win_rate", "p_win_b_gt_a")):
        if kind == "mean_r":
            left, right = a[kind], b[kind]
            available = left["p_positive"] is not None and right["p_positive"] is not None
            if available:
                x = rng.normal(left["mean"], left["sd"], cfg.draws)
                y = rng.normal(right["mean"], right["sd"], cfg.draws)
        else:
            left, right = a[kind].get("strong"), b[kind].get("strong")
            available = left is not None and right is not None
            if available:
                x = rng.beta(left["alpha"], left["beta"], cfg.draws)
                y = rng.beta(right["alpha"], right["beta"], cfg.draws)
        if available:
            result[key] = float((y > x).mean())
        else:
            result["reasons"][key] = "one or both posteriors unavailable"
    return result


def warning_flags(result, config=None):
    probability = result["mean_r"]["p_positive"]
    return (
        ["bayes_weak"]
        if probability is not None and probability < (config or BayesConfig()).weak_threshold
        else []
    )
