"""Monte Carlo kind A: reshuffle whole trading days, simulate the account per order, plus the
FTMO 2-Step pass simulation on each reshuffled order.
Spec: risk-management.md › Monte Carlo report (A. Day reshuffle, FTMO 2-Step, daily loss
approximation) and › Prop-firm field (FTMO rules).

Pure functions on R trade lists: anything with `entry_time`, `exit_time` (tz-aware) and
`r_net`. All randomness comes from `numpy.random.default_rng(config.seed)`.

Choices (simplifications until the account simulator, ROADMAP 5.2):
- Days: the weekdays of the period, cut at midnight `Europe/Prague`; a trade belongs to its
  exit day. A trade exiting on a weekend moves to the next weekday, one exiting outside the
  period to the first / last day. Trades keep their order (by exit time) inside a day.
- Risk is a fraction of the closed balance: P/L = r_net x risk x balance just before the
  trade closes (compounding, trades closing in order). No lots, no personal daily stop.
- Drawdown is measured on the balance after every trade closes.
- FTMO daily-loss approximation: see `_play_day`.
- Adaptive risk (`MonteCarloConfig.adaptive`, ROADMAP 5.7): see `_play_day_adaptive`. With
  `adaptive=None` the numbers are exactly those of the fixed-risk simulation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, time

import numpy as np

from backtester.analytics.daily import PRAGUE, weekdays
from backtester.analytics.metrics import longest_streak
from backtester.risk.adaptive import AdaptiveRisk, budgeted_risk, risk_factor

PERCENTILES = (5, 50, 95)
EPS = 1e-9  # float tolerance when a loss is compared with its limit
NO_TARGET = float("inf")


@dataclass(frozen=True, slots=True)
class MonteCarloConfig:
    runs: int = 1000
    seed: int = 42
    start_balance: float = 100_000.0
    risk_levels: tuple[float, ...] = (0.005, 0.01, 0.015)  # fraction of the balance per trade
    fan_paths: int = 20
    month_days: int = 21
    dd_alert: float = 0.10  # P(max drawdown > this) is reported
    funded_days: int = 126  # trading days a funded account is watched
    p1_target: float = 0.10  # FTMO 2-Step, fractions of the initial balance
    p2_target: float = 0.05
    daily_loss: float = 0.05
    max_loss: float = 0.10  # static
    min_trading_days: int = 4
    adaptive: AdaptiveRisk | None = None  # None = fixed risk per trade (ROADMAP 5.7)

    def __post_init__(self) -> None:
        if self.runs < 1 or self.fan_paths < 0 or self.month_days < 1 or self.funded_days < 1:
            raise ValueError("runs, month_days and funded_days must be >= 1, fan_paths >= 0")
        if self.start_balance <= 0 or self.min_trading_days < 0:
            raise ValueError("start_balance must be > 0 and min_trading_days >= 0")
        if not self.risk_levels or any(not 0 < r < 1 for r in self.risk_levels):
            raise ValueError("risk_levels must be a non-empty tuple of fractions in (0, 1)")
        for v in (self.p1_target, self.p2_target, self.daily_loss, self.max_loss, self.dd_alert):
            if v <= 0:
                raise ValueError("targets, loss limits and dd_alert must be > 0")


@dataclass(frozen=True, slots=True)
class Day:
    """One weekday: `r` the net R of the trades exiting on it, `events` their entry / exit
    events in time order as (is_entry, r) (a trade entered on an earlier day is entered at
    the day start). `ids` (same length as `events`) names the trade of each event so an exit
    can be matched to its entry (adaptive risk fixes the risk at the entry)."""

    r: np.ndarray
    events: tuple[tuple[bool, float], ...]
    ids: tuple[int, ...] = ()
    weights: tuple[float, ...] = ()  # event stop-risk weights; empty means all 1 (legacy days)


def _prague_day_start(d: date) -> float:
    return datetime.combine(d, time.min, tzinfo=PRAGUE).timestamp()


def build_days(trades: Sequence, start: date, end: date) -> list[Day]:
    """The weekdays of start..end with their trades (exit day in Prague time)."""
    for trade in trades:
        for name in ("entry_time", "exit_time"):
            stamp = getattr(trade, name)
            if stamp.tzinfo is None or stamp.utcoffset() is None:
                raise ValueError(f"{name} must be timezone-aware")
    wd = weekdays(start, end)
    if not wd:
        return []
    index = {d: i for i, d in enumerate(wd)}
    buckets: list[list] = [[] for _ in wd]
    for n, t in sorted(enumerate(trades), key=lambda p: (p[1].exit_time, p[0])):
        d = t.exit_time.astimezone(PRAGUE).date()
        i = index.get(d)
        if i is None:  # weekend or outside the period
            i = next((k for k, w in enumerate(wd) if w >= d), len(wd) - 1)
        buckets[i].append((n, t, d))
    days = []
    for bucket in buckets:
        ev = []
        for n, t, d in bucket:
            t_in, t_out = t.entry_time.timestamp(), t.exit_time.timestamp()
            t_in = max(t_in, _prague_day_start(d))  # open since the day start
            weight = getattr(t, "risk_weight", 1.0)
            ev.append(((t_in, -1 if t_in == t_out else 1, n), True, t.r_net, weight))
            ev.append(((t_out, 0, n), False, t.r_net, weight))
        ev.sort(key=lambda e: e[0])
        days.append(
            Day(
                np.array([t.r_net for _, t, _ in bucket], dtype=float),
                tuple((a, b) for _, a, b, _ in ev),
                tuple(k[2] for k, _, _, _ in ev),
                tuple(w for _, _, _, w in ev),
            )
        )
    return days


def reshuffle_orders(n_days: int, config: MonteCarloConfig) -> np.ndarray:
    """`runs` permutations of the day indices (rows), from the seeded generator."""
    rng = np.random.default_rng(config.seed)
    return np.array([rng.permutation(n_days) for _ in range(config.runs)], dtype=int).reshape(
        config.runs, n_days
    )


def monthly_gains(balances: Sequence[float], month_days: int) -> list[float]:
    """Gain of each full block of `month_days` days; `balances` = start + one value per day.
    A last partial block is dropped. Once ruined (start balance <= 0), post-ruin gain is 0.0."""
    b = list(balances)
    return [
        (b[k + month_days] / b[k] - 1) if b[k] > 0 else 0.0
        for k in range(0, len(b) - month_days, month_days)
    ]


def _pct(values, q=PERCENTILES) -> dict:
    if len(values) == 0:
        return {f"p{p}": 0.0 for p in q}
    return {f"p{p}": float(np.percentile(values, p)) for p in q}


# ----- A. account path statistics -------------------------------------------------------


def _path(r_seq: np.ndarray, risk: float, start: float) -> np.ndarray:
    """Closed balance before the first trade and after each trade (compounding)."""
    f = np.maximum(0.0, 1.0 + r_seq * risk)
    return start * np.concatenate(([1.0], np.cumprod(f)))


def _max_dd(bal: np.ndarray) -> float:
    peak = np.maximum.accumulate(bal)
    return float(np.max((peak - bal) / peak)) if len(bal) else 0.0


def _longest_underwater(day_bal: np.ndarray) -> int:
    idx = np.arange(len(day_bal))
    below = day_bal < np.maximum.accumulate(day_bal)
    last_ok = np.maximum.accumulate(np.where(below, -1, idx))
    return int(np.max(idx - last_ok)) if len(idx) else 0


def _trade_constants(r: np.ndarray, n_days: int, config: MonteCarloConfig) -> dict:
    wins, losses = r[r > 0].sum(), -r[r < 0].sum()
    months = n_days / config.month_days
    return {
        "trades": len(r),
        "win_rate": float((r > 0).mean()) if len(r) else 0.0,
        "expectancy_r": float(r.mean()) if len(r) else 0.0,
        "profit_factor": float(wins / losses)
        if losses > 0
        else (None if wins == 0 else float("inf")),
        "trades_per_month": float(len(r) / months) if months > 0 else 0.0,
    }


def _risk_stats(runs: list[dict], const: dict, config: MonteCarloConfig) -> dict:
    start = config.start_balance
    final = np.array([x["final"] for x in runs])
    dd = np.array([x["max_dd"] for x in runs]) * 100
    months = [g for x in runs for g in x["months"]]
    return {
        **const,
        "final_balance": _pct(final),
        "gain_pct": _pct((final / start - 1) * 100),
        "months": len(runs[0]["months"]),
        "monthly_gain_pct": {
            "mean": float(np.mean(months) * 100) if months else 0.0,
            "median": float(np.median(months) * 100) if months else 0.0,
        },
        "profitable_months": float(np.mean([m > 0 for m in months])) if months else 0.0,
        "max_dd_pct": {"median": float(np.median(dd)), "p95": float(np.percentile(dd, 95))},
        "p_dd_over_alert": float(np.mean(dd > config.dd_alert * 100)),
        "longest_dd_days": {"median": float(np.median([x["dd_days"] for x in runs]))},
        "worst_day_pct": float(np.min([x["worst_day"] for x in runs]) * 100),
        "longest_losing_streak": {
            "median": float(np.median([x["streak"] for x in runs])),
            "max": int(np.max([x["streak"] for x in runs])),
        },
    }


def _fan(day_bal: np.ndarray, actual: np.ndarray, config: MonteCarloConfig) -> dict:
    final = day_bal[:, -1]
    n = min(config.fan_paths, len(day_bal))
    return {
        "days": list(range(day_bal.shape[1])),
        "p5": np.percentile(day_bal, 5, axis=0).tolist(),
        "p50": np.percentile(day_bal, 50, axis=0).tolist(),
        "p95": np.percentile(day_bal, 95, axis=0).tolist(),
        "paths": day_bal[:n].tolist(),
        "actual": actual.tolist(),
        "best": day_bal[int(np.argmax(final))].tolist(),
        "worst": day_bal[int(np.argmin(final))].tolist(),
    }


def _day_balances(path: np.ndarray, counts: np.ndarray) -> np.ndarray:
    """Balance at each day end (first value = start): `counts` = trades per day in order."""
    return path[np.concatenate(([0], np.cumsum(counts)))]


def _one_run(days: list[Day], order, risk: float, config: MonteCarloConfig) -> dict:
    r_seq = np.concatenate([days[i].r for i in order]) if len(order) else np.zeros(0)
    counts = np.array([len(days[i].r) for i in order], dtype=int)
    path = _path(r_seq, risk, config.start_balance)
    day_bal = _day_balances(path, counts)
    if len(day_bal) > 1:
        prev, curr = day_bal[:-1], day_bal[1:]
        # Post-ruin (prev == 0): return is 0.0. When dropping to 0 from > 0: return is -1.0.
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(prev > 0, curr / prev - 1, 0.0)
    else:
        ratio = np.zeros(1)
    return {
        "day_bal": day_bal,
        "final": float(day_bal[-1]),
        "max_dd": _max_dd(path),
        "dd_days": _longest_underwater(day_bal),
        "worst_day": float(ratio.min()),
        "streak": longest_streak(r_seq, -1),
        "months": monthly_gains(day_bal, config.month_days),
    }


# ----- FTMO 2-Step ----------------------------------------------------------------------


def _play_day(
    day: Day,
    bal: float,
    risk: float,
    config: MonteCarloConfig,
    target_bal: float,
    tdays: int,
    fixed: bool = False,
    stats: dict | None = None,
) -> tuple[str | None, float]:
    """Play one day. Returns (status, closing balance): status None, "daily", "max" (the
    attempt is over) or "pass" (closed balance >= `target_bal` and `tdays` + 1 trading days).

    Daily-loss approximation (user, 2026-10-15): at every entry and exit of the day the worst
    point is the closed balance minus, for each trade still open, risk$ x max(1, -r_net), with
    risk$ = risk x the closed balance at that moment. Trades open since an earlier day count
    from the day start. Loss limits are fractions of the initial balance; reaching the limit
    counts as a breach. Daily loss is checked before max loss. `fixed` (the funded account,
    user 2026-10-20): risk$ = risk x the initial balance, so it does not grow with the profits.
    With `config.adaptive` the day is played by `_play_day_adaptive` (`stats` counts entries
    and skipped trades there).
    """
    if config.adaptive is not None and config.adaptive.enabled:
        return _play_day_adaptive(day, bal, risk, config, target_bal, tdays, fixed, stats)
    init = config.start_balance
    day_start, open_units = bal, 0.0
    daily_lim = config.daily_loss * init - EPS
    max_lim = config.max_loss * init - EPS
    weights = day.weights or (1.0,) * len(day.events)
    for (is_entry, r), weight in zip(day.events, weights, strict=True):
        if is_entry:
            open_units += max(weight, -r)
        else:
            open_units -= max(weight, -r)
            bal = bal + r * risk * init if fixed else bal * max(0.0, 1.0 + r * risk)
        worst = bal - open_units * risk * (init if fixed else bal)
        if day_start - worst >= daily_lim:
            return "daily", worst
        if init - worst >= max_lim:
            return "max", worst
        if not is_entry and bal >= target_bal - EPS and tdays + 1 >= config.min_trading_days:
            return "pass", bal
    return None, bal


def _play_day_adaptive(
    day: Day,
    bal: float,
    risk: float,
    config: MonteCarloConfig,
    target_bal: float,
    tdays: int,
    fixed: bool,
    stats: dict | None,
) -> tuple[str | None, float]:
    """`_play_day` with adaptive risk (spec: risk-management.md > Adaptive risk). Differences:
    - Each trade's risk$ is fixed at its entry: base risk (risk x the closed balance, or x the
      initial balance when `fixed`) x `risk_factor` of the equity at the entry, then cut by the
      daily budget; its exit P/L = r x that risk$. Modelling choice: the equity at the entry is
      the closed balance (the R list has no floating P/L), neutral rather than conservative.
    - Daily budget (`adaptive.daily_budget` x the initial balance): today's closed loss
      (day start - balance, not below 0) + every open trade at its stop (risk$ x max(1, -r),
      the daily-loss approximation) + the new trade's risk$ must fit; the new trade counts at
      1 x its risk$ (its own r is not used: that would skip losers by hindsight). Cut to what
      is left, skipped when not even floor x base risk fits; a skipped trade's exit is
      ignored (its R is not taken). A day with only skipped trades still counts as a trading day.
    - The worst point uses each open trade's own risk$. Loss limits and pass test as before.
    """
    ad = config.adaptive
    init = config.start_balance
    stats = stats if stats is not None else {}
    day_start, open_units = bal, 0.0
    daily_lim = config.daily_loss * init - EPS
    max_lim = config.max_loss * init - EPS
    budget = ad.daily_budget * init
    open_: dict[int, tuple[float, float]] = {}  # trade id -> (risk$, exposure at its stop)
    skipped: set[int] = set()
    weights = day.weights or (1.0,) * len(day.events)
    for (is_entry, r), tid, weight in zip(day.events, day.ids, weights, strict=True):
        if is_entry:
            stats["entries"] = stats.get("entries", 0) + 1
            base = risk * (init if fixed else bal) * weight
            desired = base * risk_factor(bal, init, config.max_loss, ad.floor)
            allowed = budget - max(0.0, day_start - bal) - open_units
            got = budgeted_risk(desired, ad.floor * base, allowed)
            if got is None:
                skipped.add(tid)
                stats["skipped"] = stats.get("skipped", 0) + 1
                continue
            exposure = got * max(1.0, -r / weight) if weight > 0 else 0.0
            open_[tid] = (got, exposure)
            open_units += exposure
        else:
            if tid in skipped:
                continue
            got, exposure = open_.pop(tid)
            open_units = open_units - exposure if open_ else 0.0
            bal = max(0.0, bal + r / weight * got) if weight > 0 else bal
        worst = bal - open_units
        if day_start - worst >= daily_lim:
            return "daily", worst
        if init - worst >= max_lim:
            return "max", worst
        if not is_entry and bal >= target_bal - EPS and tdays + 1 >= config.min_trading_days:
            return "pass", bal
    return None, bal


def _run_phase(
    seq: list, j: int, risk: float, target: float, config: MonteCarloConfig,
    stats: dict | None = None,
) -> tuple[str, int, int | None]:  # fmt: skip
    """One challenge phase from `seq[j]` (list of (day position, Day) with trades).
    Returns (status, next index, last day position): "pass", "daily", "max" or "open"."""
    bal = config.start_balance
    target_bal = config.start_balance * (1.0 + target)
    for tdays, k in enumerate(range(j, len(seq))):
        pos, day = seq[k]
        status, bal = _play_day(day, bal, risk, config, target_bal, tdays, stats=stats)
        if status is not None:
            return status, k + 1, pos
    return "open", len(seq), None


def _run_funded(
    seq: list, j: int, pos0: int, n_days: int, risk: float, config, stats: dict | None = None
) -> tuple:
    """Funded account from day position `pos0`, watched `funded_days` days. Returns
    (lost, observed fully, next index, last day position). Rule set by the user 2026-10-20:
    risk is a share of the initial balance and the profits are paid out at each day end
    (balance back to at most the initial one), so they neither raise the risk nor buffer the
    loss limits."""
    init = config.start_balance
    bal, last = init, pos0 + config.funded_days - 1
    k = j
    while k < len(seq) and seq[k][0] <= last:
        pos, day = seq[k]
        status, bal = _play_day(day, bal, risk, config, NO_TARGET, 0, fixed=True, stats=stats)
        k += 1
        if status in ("daily", "max"):
            return True, True, k, pos
        bal = min(bal, init)
    return False, last < n_days, k, last


def _ftmo_run(seq: list, n_days: int, risk: float, config: MonteCarloConfig, acc: dict) -> None:
    pos, j = 0, 0
    while True:
        j = next((k for k in range(j, len(seq)) if seq[k][0] >= pos), len(seq))
        start, status = pos, "pass"
        for target in (config.p1_target, config.p2_target):
            status, j, end = _run_phase(seq, j, risk, target, config, acc)
            if status != "pass":
                break
            pos = end + 1
        if status == "open":
            return
        acc["attempts"] += 1
        if status == "daily":
            acc["fail_daily"] += 1
            pos = end + 1
            continue
        if status == "max":
            acc["fail_max"] += 1
            pos = end + 1
            continue
        acc["passes"] += 1
        acc["days_to_pass"].append(end - start + 1)
        j = next((k for k in range(j, len(seq)) if seq[k][0] >= pos), len(seq))
        lost, observed, j, last = _run_funded(seq, j, pos, n_days, risk, config, acc)
        if observed:
            acc["funded_observed"] += 1
            acc["funded_lost"] += int(lost)
        pos = last + 1


def _ftmo_summary(acc: dict) -> dict:
    n = acc["attempts"]
    days = acc["days_to_pass"]
    return {
        "attempts": n,
        "passes": acc["passes"],
        "pass_probability": acc["passes"] / n if n else 0.0,
        "fail_daily": acc["fail_daily"],
        "fail_max": acc["fail_max"],
        "median_days_to_pass": float(np.median(days)) if days else None,
        "average_days_to_pass": float(np.mean(days)) if days else None,
        "skipped_trades": acc.get("skipped", 0),  # adaptive risk: cut out by the daily budget
        "trades_seen": acc.get("entries", 0),  # adaptive risk: trades entered or skipped
        "funded_observed": acc["funded_observed"],
        "funded_lost_probability": (
            acc["funded_lost"] / acc["funded_observed"] if acc["funded_observed"] else 0.0
        ),
    }


# ----- entry point ----------------------------------------------------------------------


def ftmo_by_risk(days: list[Day], orders, config: MonteCarloConfig) -> dict:
    """The FTMO 2-Step summary (`_ftmo_summary`) for each risk level over the reshuffled
    `orders`; no account statistics (the pass-probability card needs only this)."""
    n = len(days)
    out = {}
    for risk in config.risk_levels:
        acc = {"attempts": 0, "passes": 0, "fail_daily": 0, "fail_max": 0, "days_to_pass": [],
               "funded_observed": 0, "funded_lost": 0}  # fmt: skip
        for o in orders:
            seq = [(p, days[i]) for p, i in enumerate(o) if len(days[i].r)]
            _ftmo_run(seq, n, risk, config, acc)
        out[risk] = _ftmo_summary(acc)
    return out


def run_monte_carlo(
    trades: Sequence, start: date, end: date, config: MonteCarloConfig | None = None
) -> dict:
    """Kind A for each risk level. Returns
    {"config": MonteCarloConfig, "days": n, "risks": {risk: {"stats", "fan", "ftmo"}}}.
    Counts in "ftmo" are summed over all reshuffled runs; the real order (not part of the
    statistics) is the "actual" line of the fan."""
    config = config or MonteCarloConfig()
    days = build_days(trades, start, end)
    n = len(days)
    orders = reshuffle_orders(n, config)
    r_all = np.array([t.r_net for t in trades], dtype=float)
    const = _trade_constants(r_all, n, config)
    actual_order = np.arange(n)
    result: dict = {"config": config, "days": n, "risks": {}}
    ftmo = ftmo_by_risk(days, orders, config)
    for risk in config.risk_levels:
        runs = [_one_run(days, o, risk, config) for o in orders]
        mat = np.array([x["day_bal"] for x in runs])
        actual = _one_run(days, actual_order, risk, config)["day_bal"]
        result["risks"][risk] = {
            "stats": _risk_stats(runs, const, config),
            "fan": _fan(mat, actual, config),
            "ftmo": ftmo[risk],
        }
    return result


__all__ = [
    "Day",
    "MonteCarloConfig",
    "build_days",
    "ftmo_by_risk",
    "monthly_gains",
    "reshuffle_orders",
    "run_monte_carlo",
    "weekdays",
]  # fmt: skip
