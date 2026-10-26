"""Development-only equal-weight combinations. Spec: portfolio.md > Search metrics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from itertools import combinations

import numpy as np

from backtester.analytics.portfolio import PortfolioConfig, correlation_matrix, equal_weights, idm

CUTOFF = date(2021, 9, 14)


@dataclass(frozen=True)
class SearchConfig:
    max_pool: int = 12
    min_days: int = 250
    annual_days: int = 252
    top_mc: int = 10


@dataclass(frozen=True)
class Member:
    id: str
    days: tuple[date, ...]
    values: tuple[float, ...]
    period: str = "development"
    strategy: str = ""
    symbols: tuple[str, ...] = ()
    folder: str = ""
    flags: tuple[str, ...] = ()
    settings: dict = field(default_factory=dict)
    artifact_hash: str = ""


def validate(member: Member):
    if member.period != "development":
        raise ValueError(f"{member.id}: development-only member required")
    if not member.id or len(member.days) != len(member.values) or not member.days:
        raise ValueError("member needs an ID and matching nonempty days/R")
    if list(member.days) != sorted(set(member.days)) or any(d >= CUTOFF for d in member.days):
        raise ValueError(f"{member.id}: invalid or test-period daily dates")
    if not np.isfinite(member.values).all():
        raise ValueError(f"{member.id}: nonfinite daily R")


def set_id(ids) -> str:
    return hashlib.sha256(json.dumps(sorted(ids), separators=(",", ":")).encode()).hexdigest()[:20]


def metrics(days, values, config=None):
    """Initial equity is zero; undefined ratios are None, never infinity."""
    config = config or SearchConfig()
    r = np.asarray(values, float)
    if not len(r):
        return dict.fromkeys(
            ("net_r", "max_dd_r", "net_dd", "sharpe", "worst_month", "longest_dd_days")
        )
    equity = np.cumsum(r)
    peak = np.maximum.accumulate(np.r_[0.0, equity])[1:]
    drawdown = peak - equity
    high_indices = np.maximum.accumulate(np.where(drawdown <= 0, np.arange(len(r)), -1))
    duration = np.arange(len(r)) - high_indices
    dd, net = float(drawdown.max()), float(r.sum())
    months = np.array([d.year * 12 + d.month for d in days])
    starts = np.r_[0, np.flatnonzero(months[1:] != months[:-1]) + 1]
    sd = float(r.std(ddof=1)) if len(r) > 1 else 0
    return {
        "net_r": net,
        "max_dd_r": dd,
        "net_dd": net / dd if dd else None,
        "sharpe": float(r.mean() / sd * np.sqrt(config.annual_days)) if sd else None,
        "worst_month": float(np.add.reduceat(r, starts).min()),
        "longest_dd_days": int(duration.max()),
    }


def search(pool, *, regimes=None, config=None):
    """All 2..4 sets. LOO uses the remaining members' own common days.

    Regimes map symbol -> day -> label: the whole combined R is conditioned on each
    symbol separately; symbols are never voted/averaged into one market regime.
    """
    config = config or SearchConfig()
    pool = sorted(pool, key=lambda m: m.id)
    if not 2 <= len(pool) <= config.max_pool or len({m.id for m in pool}) != len(pool):
        raise ValueError(f"choose 2..{config.max_pool} distinct members")
    for member in pool:
        validate(member)
    maps = {m.id: dict(zip(m.days, m.values, strict=True)) for m in pool}
    cache = {}
    regime_cache = {}

    def breakdown(symbol, days, values):
        key = (symbol, tuple(days))
        if key not in regime_cache:
            labels = (regimes or {}).get(symbol, {})
            names, indices = np.unique(
                [labels.get(d, "unknown") for d in days], return_inverse=True
            )
            regime_cache[key] = names, indices
        names, indices = regime_cache[key]
        counts = np.bincount(indices, minlength=len(names))
        sums = np.bincount(indices, weights=values, minlength=len(names))
        return {
            str(label): {"days": int(count), "net_r": float(net), "r_per_day": float(net / count)}
            for label, count, net in zip(names, counts, sums, strict=True)
        }

    def calculate(parts):
        key = tuple(m.id for m in parts)
        if key in cache:
            return cache[key]
        common = set(parts[0].days).intersection(*(m.days for m in parts[1:]))
        days = sorted(common)
        union = set().union(*(m.days for m in parts))
        matrix = np.array([[maps[m.id][d] for d in days] for m in parts])
        combined = matrix.mean(axis=0)
        corr = correlation_matrix(matrix)
        pairs = corr[np.triu_indices(len(parts), 1)]
        result = {
            "id": set_id(key),
            "members": list(key),
            **metrics(days, combined, config),
            "common_days": len(days),
            "dropped_days": len(union) - len(days),
            "dropped_by_member": {m.id: len(m.days) - len(days) for m in parts},
            "flags": ["fewer_than_250_common_days"] if len(days) < config.min_days else [],
            "avg_correlation": float(pairs.mean()) if len(pairs) else None,
            "idm": idm(corr, equal_weights(len(parts)), PortfolioConfig()),
            "days": [d.isoformat() for d in days],
            "daily_r": combined.tolist(),
            "equity": np.cumsum(combined).tolist(),
            "correlation": corr.tolist(),
        }
        cache[key] = result
        return result

    rows = []
    for size in range(2, min(4, len(pool)) + 1):
        for parts in combinations(pool, size):
            row = dict(calculate(parts))
            row["leave_one_out"] = {
                m.id: {
                    k: v
                    for k, v in calculate(tuple(p for p in parts if p.id != m.id)).items()
                    if k not in ("days", "daily_r", "equity", "correlation")
                }
                for m in parts
            }
            symbols = sorted({s for m in parts for s in m.symbols}) or sorted(regimes or {})
            row["regimes"] = {}
            days = [date.fromisoformat(d) for d in row["days"]]
            for symbol in symbols:
                row["regimes"][symbol] = breakdown(symbol, days, row["daily_r"])
            rows.append(row)
    return rows
