"""Deterministic account attempts on real trade order.

Spec: risk-management.md > Challenge path simulator and FTMO rule sets.
Uses Monte Carlo's exit-day buckets and worst-point approximation without changing it.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from math import isfinite

import numpy as np

from backtester.analytics.daily import PRAGUE, weekdays
from backtester.risk.monte_carlo import EPS, Day, build_days


@dataclass(frozen=True, slots=True)
class RuleSet:
    name: str
    targets: tuple[float, ...]
    daily_loss: float
    max_loss: float
    max_loss_mode: str
    min_trading_days: int
    consistency: float | None
    risk_base: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be non-empty")
        if not isinstance(self.targets, tuple) or any(
            not isfinite(t) or t <= 0 for t in self.targets
        ):
            raise ValueError("targets must be a tuple of finite positive fractions")
        for value in (self.daily_loss, self.max_loss):
            if not isfinite(value) or not 0 < value < 1:
                raise ValueError("loss limits must be finite fractions in (0, 1)")
        if self.max_loss_mode not in ("static", "eod_trailing", "intraday_trailing"):
            raise ValueError("unknown max_loss_mode")
        if self.risk_base not in ("balance", "initial"):
            raise ValueError("risk_base must be balance or initial")
        if type(self.min_trading_days) is not int or self.min_trading_days < 0:
            raise ValueError("min_trading_days must be a non-negative integer")
        if self.consistency is not None and (
            not isfinite(self.consistency) or not 0 < self.consistency <= 1
        ):
            raise ValueError("consistency must be None or a finite fraction in (0, 1]")


RULE_SETS = {
    "ftmo_2step": RuleSet("ftmo_2step", (0.10, 0.05), 0.05, 0.10, "static", 4, None, "balance"),
    "ftmo_1step": RuleSet("ftmo_1step", (0.10,), 0.03, 0.10, "eod_trailing", 0, 0.50, "balance"),
    "ftmo_instant": RuleSet(
        "ftmo_instant", (), 0.03, 0.10, "intraday_trailing", 0, 0.30, "initial"
    ),
}


@dataclass(frozen=True, slots=True)
class Attempt:
    status: str
    start_index: int
    end_index: int | None
    weekdays_to_end: int
    phase_results: list[dict]
    payout_day: int | None
    path: list[dict]

    def to_dict(self) -> dict:
        return asdict(self)


def _validate(risk: float, initial: float, watch_days: int) -> None:
    if not isfinite(risk) or not 0 < risk < 1:
        raise ValueError("risk must be a finite fraction in (0, 1)")
    if not isfinite(initial) or initial <= 0:
        raise ValueError("initial must be finite and positive")
    if type(watch_days) is not int or watch_days < 1:
        raise ValueError("watch_days must be a positive integer")


def _consistent(rules: RuleSet, best: float, profit: float) -> bool:
    return rules.consistency is None or best <= rules.consistency * profit + EPS


def _day(
    day: Day, balance: float, peak: float, rules: RuleSet, risk: float, initial: float
) -> tuple[str | None, float, float, float, float]:
    """Monte Carlo `_play_day` events, extended with trailing floors and path values.

    Returns breach, closed balance, worst equity, peak, and floor in force. On a
    breach the balance is the last closed balance; worst records the triggering equity.
    An EOD peak is advanced by the caller only after this day's checks.
    """
    day_start = worst = balance
    open_units = 0.0
    floor = peak - rules.max_loss * initial
    weights = day.weights or (1.0,) * len(day.events)
    for (entry, r), weight in zip(day.events, weights, strict=True):
        if not isfinite(r) or not isfinite(weight) or weight < 0:
            raise ValueError("trade R and weights must be finite, weights non-negative")
        if entry:
            open_units += max(weight, -r)
        else:
            open_units -= max(weight, -r)
            balance = (
                balance + r * risk * initial
                if rules.risk_base == "initial"
                else balance * max(0.0, 1.0 + r * risk)
            )
            if rules.max_loss_mode == "intraday_trailing":
                peak = max(peak, balance)
                floor = peak - rules.max_loss * initial
        equity = balance - open_units * risk * (
            initial if rules.risk_base == "initial" else balance
        )
        worst = min(worst, equity)
        if day_start - equity >= rules.daily_loss * initial - EPS:
            return "daily", balance, worst, peak, floor
        if equity <= floor + EPS:
            return "max", balance, worst, peak, floor
    return None, balance, worst, peak, floor


def play_attempt(
    days: Sequence[Day],
    start_index: int,
    rules: RuleSet,
    risk: float,
    initial: float = 100_000.0,
    watch_days: int = 126,
) -> Attempt:
    """Play one independent attempt; Spec: risk-management.md > Rules of the simulator.

    Path day and payout_day are zero-based indices into `days`. Phase days count
    trading days; weekdays_to_end also includes idle weekdays.
    """
    _validate(risk, initial, watch_days)
    if type(start_index) is not int or not 0 <= start_index <= len(days):
        raise ValueError("start_index must index days or its end")
    balance = peak = initial
    phase = trading_days = 0
    best = 0.0
    phases, path = [], []
    payout = None
    instant = not rules.targets
    stop = min(len(days), start_index + watch_days) if instant else len(days)

    def result(status: str) -> Attempt:
        return Attempt(
            status, start_index, path[-1]["day"] if path else None, len(path), phases, payout, path
        )

    for index in range(start_index, stop):
        day = days[index]
        day_start = balance
        breach, balance, worst, peak, floor = _day(day, balance, peak, rules, risk, initial)
        path.append(
            {
                "day": index,
                "balance": balance,
                "worst": worst,
                "daily_floor": day_start - rules.daily_loss * initial,
                "max_floor": floor,
            }
        )
        trading_days += bool(len(day.r))
        if breach:
            phases.append({"status": breach, "days": trading_days})
            return result(breach)
        best = max(best, balance - day_start)
        profit = balance - initial
        consistent = _consistent(rules, best, profit)
        if instant:
            if payout is None and profit > 0 and consistent:
                payout = index
            if len(path) == watch_days:
                phases.append({"status": "survived", "days": trading_days})
                return result("survived")
        elif (
            balance >= initial * (1 + rules.targets[phase]) - EPS
            and trading_days >= rules.min_trading_days
            and consistent
        ):
            phases.append({"status": "pass", "days": trading_days})
            phase += 1
            if phase == len(rules.targets):
                return result("pass")
            balance = peak = initial
            best = 0.0
            trading_days = 0
            continue
        if rules.max_loss_mode == "eod_trailing":
            peak = max(peak, balance)
    phases.append({"status": "open", "days": trading_days})
    return result("open")


def _summary(attempts: list[dict], rules: RuleSet, fee: float | None) -> dict:
    counts = {
        s: sum(a["status"] == s for a in attempts)
        for s in ("pass", "daily", "max", "open", "survived")
    }
    finished = len(attempts) - counts["open"]
    instant = not rules.targets
    pass_rate = counts["pass"] / finished if finished and not instant else None
    funding_days = [a["weekdays_to_end"] for a in attempts if a["status"] == "pass"]
    result = {
        "attempts": len(attempts),
        "passed": counts["pass"],
        "pass_pct": pass_rate * 100 if pass_rate is not None else None,
        "daily_pct": 100 * counts["daily"] / finished if finished else None,
        "max_pct": 100 * counts["max"] / finished if finished else None,
        "open": counts["open"],
        "survived": counts["survived"],
        "median_weekdays_to_funding": float(np.median(funding_days)) if funding_days else None,
        "p90_weekdays_to_funding": float(np.percentile(funding_days, 90)) if funding_days else None,
    }
    if fee is not None:
        cost = fee / pass_rate if pass_rate else None
        result["fee"] = fee
        if rules.name == "ftmo_2step":
            result["cost_per_funded_before_refund"] = cost
            result["cost_per_funded_after_refund"] = 0.0 if pass_rate else None
        else:
            result["cost_per_funded"] = cost
    return result


def simulate(
    trades: Sequence,
    start: date,
    end: date,
    rules_names: Sequence[str],
    risk: float,
    fees: dict[str, float] | None = None,
    watch_days: int = 126,
) -> dict:
    """Monthly starts in real order, with open attempts excluded from outcome rates.

    Spec: risk-management.md > Challenge path simulator and FTMO rule sets.
    Percentages use 0..100. Undefined rates, costs and funding times are None.
    """
    _validate(risk, 100_000.0, watch_days)
    if start > end:
        raise ValueError("start must be on or before end")
    if not rules_names or isinstance(rules_names, str):
        raise ValueError("rules_names must be a non-empty sequence of rule names")
    if any(name not in RULE_SETS for name in rules_names):
        raise ValueError("unknown rule name")
    fees = fees or {}
    if any(name not in RULE_SETS or not isfinite(fee) or fee < 0 for name, fee in fees.items()):
        raise ValueError("fees must name known rules and have finite non-negative prices")
    selected = []
    for t in trades:
        for attr in ("entry_time", "exit_time"):
            stamp = getattr(t, attr)
            if stamp.tzinfo is None or stamp.utcoffset() is None:
                raise ValueError(f"{attr} must be timezone-aware")
        if t.exit_time < t.entry_time:
            raise ValueError("trade exit precedes entry")
        if (
            not isfinite(t.r_net)
            or not isfinite(getattr(t, "risk_weight", 1.0))
            or (getattr(t, "risk_weight", 1.0) < 0)
        ):
            raise ValueError("trade R and weights must be finite, weights non-negative")
        if start <= t.exit_time.astimezone(PRAGUE).date() <= end:
            selected.append(t)
    dates = weekdays(start, end)
    days = build_days(selected, start, end)
    starts = []
    for index, d in enumerate(dates):
        first = d.replace(day=1)
        while first.weekday() >= 5:
            first += timedelta(days=1)
        if d == first:
            starts.append(index)
    report = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "risk": risk,
        "watch_days": watch_days,
        "dates": [d.isoformat() for d in dates],
        "rules": {},
    }
    for name in rules_names:
        rules = RULE_SETS[name]
        attempts = []
        for index in starts:
            # A fresh account holds no position opened before its start (Opus review); this
            # also drops every exit before the start, incl. weekend exits build_days moves forward.
            eligible = [
                t for t in selected if t.entry_time.astimezone(PRAGUE).date() >= dates[index]
            ]
            attempt_days = (
                days if len(eligible) == len(selected) else (build_days(eligible, start, end))
            )
            attempt = play_attempt(
                attempt_days, index, rules, risk, watch_days=watch_days
            ).to_dict()
            attempt["start_date"] = dates[index].isoformat()
            attempt["end_date"] = (
                dates[attempt["end_index"]].isoformat()
                if attempt["end_index"] is not None
                else None
            )
            attempts.append(attempt)
        report["rules"][name] = {
            "rule_set": asdict(rules),
            "summary": _summary(attempts, rules, fees.get(name)),
            "attempts": attempts,
        }
    return report
