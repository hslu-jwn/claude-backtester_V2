"""Spec: research-runner.md > Significance of the best variant; risk-management.md >
Trial log and deflated Sharpe. Diagnostics only, never substituted into DSR.
"""

from datetime import timedelta
from zoneinfo import ZoneInfo

import numpy as np

from backtester.analytics.best_of_n import daily_matrix


def effective_trials(values) -> dict:
    """Independent-trial approximation from average pairwise MTM correlation."""
    matrix = daily_matrix(values)
    days, n = matrix.shape
    result = {"n": n, "n_eff": None, "mean_correlation": None, "reason": None}
    if days < 2 or n < 1:
        return {**result, "reason": "requires at least two days and one variant"}
    if n == 1:
        return {**result, "n_eff": 1.0}
    shifted = matrix - matrix[0]
    centred = shifted - shifted.mean(0)
    norms = np.linalg.norm(centred, axis=0)
    unit = np.divide(centred, norms, out=np.zeros_like(centred), where=norms > 0)
    correlation = np.clip(unit.T @ unit, -1, 1)
    for i in range(n):
        for j in range(i):
            if np.array_equal(matrix[:, i], matrix[:, j]):
                correlation[i, j] = correlation[j, i] = 1
    mean = float(correlation[np.tril_indices(n, -1)].mean())
    denominator = 1 + (n - 1) * mean
    result["mean_correlation"] = mean
    if denominator <= np.finfo(float).eps:
        return {**result, "reason": "nonpositive correlation denominator"}
    return {**result, "n_eff": max(1.0, n / denominator)}


def trade_uniqueness(trades) -> dict:
    """Mean inverse daily concurrency per trade, using unnetted holding intervals.

    Spec: research-runner.md > Significance of the best variant. Day boundaries use
    Europe/Prague, including DST; exits at midnight exclude the new day.
    """
    spans = []
    zone = ZoneInfo("Europe/Prague")
    for trade in trades:
        a, b = trade.entry_time, trade.exit_time
        if a.utcoffset() is None or b.utcoffset() is None or b < a:
            raise ValueError("trade intervals must be timezone-aware with exit >= entry")
        start = a.astimezone(zone).date().toordinal()
        last = (b - timedelta(microseconds=1) if b > a else b).astimezone(zone)
        spans.append((start, last.date().toordinal() + 1))
    if not spans:
        return {
            "trades": 0,
            "weights": [],
            "average_uniqueness": None,
            "effective_trades": 0.0,
            "reason": None,
        }
    origin = min(a for a, _ in spans)
    delta = np.zeros(max(b for _, b in spans) - origin + 1)
    for a, b in spans:
        delta[a - origin] += 1
        delta[b - origin] -= 1
    concurrent = delta.cumsum()[:-1]
    inverse = np.divide(1.0, concurrent, out=np.zeros_like(concurrent), where=concurrent > 0)
    prefix = np.r_[0.0, inverse.cumsum()]
    weights = [float((prefix[b - origin] - prefix[a - origin]) / (b - a)) for a, b in spans]
    return {
        "trades": len(spans),
        "weights": weights,
        "average_uniqueness": float(np.mean(weights)),
        "effective_trades": float(sum(weights)),
        "reason": None,
    }
