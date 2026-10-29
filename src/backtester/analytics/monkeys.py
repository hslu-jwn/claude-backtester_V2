"""Matched null models. Spec: risk-management.md > Matched monkeys (T-14).

All M1 exits delegate to entry_screen; no independent fill or cost simulator lives here.
"""

from __future__ import annotations

import math
import os
from collections import defaultdict
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime

import numpy as np

from backtester.analytics import _worker_data
from backtester.analytics.entry_screen import (
    ExitResult,
    M1Data,
    ScreenTrade,
    _entry_index,
    _percentile_of,
    _window_candidates,
    exit_after_bars,
)
from backtester.core.models import Direction
from backtester.engine.costs import CostConfig

KINDS = {1: "random entry", 2: "random exit", 3: "both random"}


@dataclass(frozen=True, slots=True)
class MonkeyConfig:
    runs: int = 1000
    seed: int = 42
    window_bucket_minutes: int = 15
    pass_percentile: float = 90.0

    def __post_init__(self):
        if self.runs < 1 or self.window_bucket_minutes < 1 or self.seed < 0:
            raise ValueError("runs and bucket minutes must be positive; seed nonnegative")
        if not 0 <= self.pass_percentile <= 100:
            raise ValueError("pass_percentile must be in [0, 100]")


def screen_trades(trades: Sequence) -> list[ScreenTrade]:
    """Accept engine trades and saved CSV records without misreading string directions."""
    return [
        ScreenTrade(
            t.symbol,
            (Direction.BULLISH if t.direction == "long" else Direction.BEARISH)
            if isinstance(t.direction, str)
            else t.direction,
            t.entry_time,
            t.entry,
            t.initial_stop,
            t.exit_time,
            t.r_net,
        )
        for t in trades
    ]


def _groups(trades):
    grouped = defaultdict(list)
    for t in trades:
        grouped[t.symbol].append(t)
    return grouped


def _candidates(trades, m1s, config):
    result = {}
    for symbol, ts in _groups(trades).items():
        m1 = m1s.get(symbol)
        if m1 is None:
            raise ValueError(f"{symbol}: missing M1 data")
        for t in ts:
            if (
                not np.isfinite([t.entry, t.initial_stop, t.r_net]).all()
                or t.risk <= 0
                or t.exit_time < t.entry_time
                or t.sign * (t.entry - t.initial_stop) <= 0
                or _entry_index(m1, t) >= len(m1)
            ):
                raise ValueError(f"{symbol}: invalid trade or no candle after entry")
        candidates = _window_candidates(
            m1, [t.entry_time for t in ts], config.window_bucket_minutes
        )
        candidates = candidates[candidates < len(m1) - 1]
        if not len(candidates):
            raise ValueError(f"{symbol}: no eligible M1 closes in trading window")
        result[symbol] = candidates
    return result


def draw_run(
    trades: Sequence[ScreenTrade],
    m1s: Mapping[str, M1Data],
    kind: int,
    rng: np.random.Generator,
    config: MonkeyConfig,
    *,
    candidates=None,
) -> list[ScreenTrade]:
    """Per-symbol permutations preserve exact empirical marginals, paired only in kind 1."""
    if kind not in KINDS:
        raise ValueError("kind must be 1, 2 or 3")
    candidates = _candidates(trades, m1s, config) if candidates is None else candidates
    out = []
    for symbol, ts in _groups(trades).items():
        n, m1 = len(ts), m1s[symbol]
        stops = rng.permutation(n) if kind != 2 else np.arange(n)
        holds = stops if kind == 1 else rng.permutation(n)
        refs = rng.choice(candidates[symbol], n) if kind != 2 else None
        for i, t in enumerate(ts):
            entry_time, entry = t.entry_time, t.entry
            if refs is not None:
                idx = refs[i]
                entry_time = datetime.fromtimestamp(int(m1.close_s[idx]), UTC)
                entry = float(m1.close[idx])
            hold = ts[holds[i]].exit_time - ts[holds[i]].entry_time
            out.append(
                replace(
                    t,
                    entry_time=entry_time,
                    entry=entry,
                    initial_stop=entry - t.sign * ts[stops[i]].risk,
                    exit_time=entry_time + hold,
                )
            )
    return out


def replay(trades, m1s, costs: CostConfig) -> list[ExitResult]:
    """Use the existing M1 stop/time exit, including funding and all engine costs."""
    return [
        exit_after_bars(
            m1s[t.symbol], t, 1, (t.exit_time - t.entry_time).total_seconds() / 60, costs
        )
        for t in trades
    ]


def statistics(net, exit_times) -> tuple[float, float]:
    """Net and max additive drawdown in stable exit order, with initial zero peak."""
    ordered = np.asarray(net, dtype=float)[np.argsort(exit_times, kind="stable")]
    equity = np.concatenate(([0.0], np.cumsum(ordered)))
    return float(equity[-1]), float(np.max(np.maximum.accumulate(equity) - equity))


def _summary(real, samples, lower=False):
    p5, median, p95 = np.percentile(samples, [5, 50, 95])
    percentile = _percentile_of(-real, -samples) if lower else _percentile_of(real, samples)
    return {
        "real": real,
        "median": float(median),
        "p5": float(p5),
        "p95": float(p95),
        "percentile": percentile,
    }


def _replay_chunk(chunk):
    result = []
    for drawn in chunk:
        exits = replay(drawn, _worker_data.m1s, _worker_data.costs)
        result.append(
            statistics([r.r_net for r in exits], [r.exit_time.timestamp() for r in exits])
        )
    return result


def matched_monkeys(
    trades: Sequence[ScreenTrade],
    m1s: Mapping[str, M1Data],
    costs: CostConfig,
    config: MonkeyConfig | None = None,
    workers: int | None = None,
) -> dict:
    """Run all three matched models; retain samples for audit and downstream verdicts."""
    cfg = config or MonkeyConfig()
    trades = screen_trades(trades)
    result = {
        "available": bool(trades),
        "config": asdict(cfg),
        "trades": len(trades),
        "kinds": [],
        "passed": False,
        "flags": [],
    }
    if not trades:
        result["note"] = "no trades"
        return result
    candidates = _candidates(trades, m1s, cfg)
    real = statistics([t.r_net for t in trades], [t.exit_time.timestamp() for t in trades])
    workers = max(1, (os.cpu_count() or 1) - 1) if workers is None else workers
    if workers < 1:
        raise ValueError("workers must be positive")
    pool = (
        ProcessPoolExecutor(
            max_workers=workers, initializer=_worker_data.initialize, initargs=(m1s, costs)
        )
        if workers > 1
        else None
    )
    try:
        _monkey_runs(result, trades, m1s, costs, cfg, candidates, real, workers, pool)
    finally:
        if pool is not None:
            pool.shutdown(wait=True, cancel_futures=True)
    result["passed"] = all(k["passed"] for k in result["kinds"])
    result["flags"] = [] if result["passed"] else ["monkey_beaten"]
    return result


def _monkey_runs(result, trades, m1s, costs, cfg, candidates, real, workers, pool):
    for kind, name in KINDS.items():
        rng = np.random.default_rng([cfg.seed, kind])
        samples = np.empty((cfg.runs, 2))
        if pool is None:
            for run in range(cfg.runs):
                drawn = draw_run(trades, m1s, kind, rng, cfg, candidates=candidates)
                exits = replay(drawn, m1s, costs)
                samples[run] = statistics(
                    [r.r_net for r in exits], [r.exit_time.timestamp() for r in exits]
                )
        else:
            size = max(1, math.ceil(cfg.runs / (4 * workers)))
            futures = []
            output = []
            for start in range(0, cfg.runs, size):
                chunk = [
                    draw_run(trades, m1s, kind, rng, cfg, candidates=candidates)
                    for _ in range(min(size, cfg.runs - start))
                ]
                futures.append(pool.submit(_replay_chunk, chunk))
                if len(futures) >= workers:
                    output.extend(futures.pop(0).result())
            for future in futures:
                output.extend(future.result())
            samples[:] = output
        net = _summary(real[0], samples[:, 0])
        dd = _summary(real[1], samples[:, 1], lower=True)
        passed = min(net["percentile"], dd["percentile"]) >= cfg.pass_percentile
        result["kinds"].append(
            {
                "kind": kind,
                "name": name,
                "net_r": net,
                "max_dd_r": dd,
                "passed": passed,
                "samples_net_r": samples[:, 0].tolist(),
                "samples_max_dd_r": samples[:, 1].tolist(),
            }
        )


def net_percentile(result: dict | None) -> float | None:
    return result["kinds"][0]["net_r"]["percentile"] if result and result["available"] else None


def markdown(result: dict | None) -> list[str]:
    lines = ["", "## Matched monkeys", ""]
    if result and result.get("skipped") == "gate":
        return lines + ["skipped (failed the cost gate)"]
    if not result or not result["available"]:
        return lines + ["Unavailable (disabled or no trades)."]
    lines += [
        (
            f"{result['trades']} trades, {result['config']['runs']} seeded runs per kind. "
            f"{'PASS' if result['passed'] else 'FAIL'}; lower drawdown is better."
        ),
        "",
        "| Kind | Statistic | Real R | p5 R | Median R | p95 R | Favorable percentile | Pass |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for k in result["kinds"]:
        for key in ("net_r", "max_dd_r"):
            s = k[key]
            lines.append(
                f"| {k['kind']} {k['name']} | {key} | {s['real']:.3f} | "
                f"{s['p5']:.3f} | {s['median']:.3f} | {s['p95']:.3f} | "
                f"{s['percentile']:.1f}% | {k['passed']} |"
            )
    return lines
