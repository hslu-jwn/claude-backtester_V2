"""Efficiency ratio (price noise) and the small statistics of the noise study.
Spec: ROADMAP.md › 11.1; knowledge base I-01 (Kaufman, *Trading Systems and Methods*,
p.10-14, 781, 868-871).

`efficiency_ratio(closes, n)`: |close_i - close_(i-n)| / sum of |close_k - close_(k-1)| over
the n bars up to i. 0 = pure noise, 1 = a straight line. The value at bar i uses closes up to
i only (no lookahead); the first n bars and flat windows have no value (None).
"""

from __future__ import annotations

import math
import random
from collections.abc import Hashable, Sequence

MIN_POINTS = 3  # a correlation needs at least this many pairs
PATH_EPSILON = 1e-12  # a window moving less than this (flat prices) has no ratio


def efficiency_ratio(closes: Sequence[float], n: int) -> list[float | None]:
    if n < 1:
        raise ValueError("n must be >= 1")
    out: list[float | None] = [None] * len(closes)
    cum = [0.0]  # cum[i] = sum of |close_k - close_(k-1)| for k <= i
    for i in range(1, len(closes)):
        cum.append(cum[-1] + abs(closes[i] - closes[i - 1]))
    for i in range(n, len(closes)):
        path = cum[i] - cum[i - n]
        if path > PATH_EPSILON:
            out[i] = min(1.0, abs(closes[i] - closes[i - n]) / path)
    return out


def values_by(keys: Sequence[Hashable], values: Sequence[float | None]) -> dict:
    """{key: [values]} in first-seen key order; missing values (None) are left out and a key
    without any value is not listed."""
    groups: dict[Hashable, list[float]] = {}
    for k, v in zip(keys, values, strict=True):
        if v is not None:
            groups.setdefault(k, []).append(v)
    return groups


def mean_by(keys: Sequence[Hashable], values: Sequence[float | None]) -> dict:
    """{key: (mean, count)} of the values that exist."""
    return {k: (sum(v) / len(v), len(v)) for k, v in values_by(keys, values).items()}


def median(values: Sequence[float]) -> float | None:
    if not values:
        return None
    s = sorted(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2


def _ranks(values: Sequence[float]) -> list[float]:
    """1-based ranks, ties get the mean of their positions."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        mean_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = mean_rank
        i = j + 1
    return ranks


def rank_correlation(xs: Sequence[float], ys: Sequence[float]) -> dict | None:
    """Spearman's rho of two samples: {rho, n, t}; t = rho x sqrt((n - 2) / (1 - rho^2))
    (|t| >= 2 is a rough "not chance"; cells that share trades are not independent, so treat
    it as a hint). None for fewer than 3 pairs or no variation in a sample."""
    if len(xs) != len(ys):
        raise ValueError("samples must have the same length")
    n = len(xs)
    if n < MIN_POINTS:
        return None
    rx, ry = _ranks(xs), _ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    sy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if sx == 0 or sy == 0:
        return None
    rho = sum((a - mx) * (b - my) for a, b in zip(rx, ry, strict=True)) / (sx * sy)
    rho = max(-1.0, min(1.0, rho))
    t = math.copysign(math.inf, rho) if abs(rho) >= 1 else rho * math.sqrt((n - 2) / (1 - rho**2))
    return {"rho": rho, "n": n, "t": t}


def random_walk_er(n: int, bars: int = 100_000, seed: int = 1) -> float:
    """Mean ER(n) of a seeded Gaussian random walk: the level of "no information" to read
    a market's ER against (about 0.32 at n = 10, 0.22 at n = 20, 0.13 at n = 60)."""
    rng = random.Random(seed)
    price, closes = 0.0, []
    for _ in range(bars):
        price += rng.gauss(0.0, 1.0)
        closes.append(price)
    values = [v for v in efficiency_ratio(closes, n) if v is not None]
    return sum(values) / len(values)
