"""Pure weekly book calculations. Spec: strategy-crypto_carry.md › Rule (frozen)."""

from __future__ import annotations

import math
from bisect import bisect_right
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from statistics import mean
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # strategy/ must not import engine/ at runtime (tests/test_layers.py)
    from backtester.engine.costs import FundingSeries

R_BP = 1000.0
COST_BP = (
    20.0  # 2 legs x round trip x taker 0.05 % (engine/costs.BINANCE_TAKER_FEE; pinned by a test)
)


@dataclass(frozen=True)
class CryptoCarryConfig:
    """Frozen defaults. Spec: strategy-crypto_carry.md › Rule (frozen), Universe, Risk unit."""

    n_leg: int = 4
    lookback_days: int = 7
    min_history_days: int = 30
    min_rates: int = 21
    r_bp: float = R_BP
    cost_bp: float = COST_BP
    symbols: tuple[str, ...] = (
        "BTCUSDT",
        "ETHUSDT",
        "BCHUSDT",
        "XRPUSDT",
        "EOSUSDT",
        "LTCUSDT",
        "TRXUSDT",
        "ETCUSDT",
        "LINKUSDT",
        "XLMUSDT",
        "ADAUSDT",
        "BNBUSDT",
        "XTZUSDT",
        "XMRUSDT",
        "NEOUSDT",
        "DASHUSDT",
        "ATOMUSDT",
    )


DEFAULT = CryptoCarryConfig()


def _monday(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Monday must be timezone-aware")
    value = value.astimezone(UTC)
    if value.weekday() or value.time().isoformat() != "00:00:00":
        raise ValueError("expected Monday 00:00 UTC")
    return value


def signal(
    funding: FundingSeries,
    monday: datetime,
    config: CryptoCarryConfig = DEFAULT,
) -> float | None:
    """Eligible trailing settled funding. Spec: strategy-crypto_carry.md › Rule (frozen)."""
    monday = _monday(monday)
    if not funding.times or funding.times[0] > monday - timedelta(days=config.min_history_days):
        return None
    if bisect_right(funding.times, monday) < config.min_rates:
        return None
    result = funding.rate_sum(monday - timedelta(days=config.lookback_days), monday)
    if not math.isfinite(result):
        raise ValueError("non-finite funding signal")
    return result


def pick_legs(signals: Mapping[str, float], n_leg: int = 4) -> tuple[list[str], list[str]] | None:
    """Stable ascending sort by signal; ties keep the caller's order (the universe order of
    `CryptoCarryConfig.symbols`), as in the tested screen. Longs = first n_leg, shorts = last n_leg.
    Spec: strategy-crypto_carry.md › Rule (frozen), A5."""
    if n_leg < 1:
        raise ValueError("n_leg must be positive")
    if any(not math.isfinite(value) for value in signals.values()):
        raise ValueError("non-finite funding signal")
    if len(signals) < 2 * n_leg:
        return None
    ranked = sorted(signals, key=lambda sym: signals[sym])
    return ranked[:n_leg], ranked[-n_leg:]


@dataclass(frozen=True)
class WeekResult:
    """A weekly observation plus all selected members, including dropped ones."""

    trade: dict | None
    legs: list[dict]
    skipped: str | None = None


def week_result(
    monday: datetime,
    signals: Mapping[str, float],
    prices: Mapping[str, Mapping[datetime, float]],
    funding: Mapping[str, FundingSeries],
    config: CryptoCarryConfig = DEFAULT,
) -> WeekResult:
    """Evaluate a fixed book at exit; prices map M1 open times to closes.

    Per-member price_bp is the underlying return; funding_bp is signed cash flow
    (positive means received). Missing bars drop members before equal weighting.
    Spec: strategy-crypto_carry.md › Rule (frozen), Risk unit.
    """
    monday = _monday(monday)
    picked = pick_legs(signals, config.n_leg)
    if picked is None:
        return WeekResult(None, [], "fewer than required eligible symbols")
    entry = monday + timedelta(minutes=1)
    exit_ = monday + timedelta(days=7, minutes=-1)
    legs = []
    kept = {}
    for side, members in zip(("long", "short"), picked, strict=True):
        kept[side] = []
        for sym in members:
            closes = prices.get(sym, {})
            a, b = closes.get(monday), closes.get(exit_ - timedelta(minutes=1))
            dropped = a is None or b is None
            if not dropped and any(not math.isfinite(p) or p <= 0 for p in (a, b)):
                raise ValueError(f"{sym}: prices must be finite and positive")
            price = None if dropped else (b / a - 1) * 1e4
            fund = funding[sym].rate_sum(entry, exit_) * 1e4
            if not math.isfinite(fund):
                raise ValueError(f"{sym}: non-finite held funding")
            row = {
                "week": monday,
                "symbol": sym,
                "side": side,
                "signal": signals[sym],
                "price_bp": price,
                "funding_bp": fund * (-1 if side == "long" else 1),
                "dropped": dropped,
            }
            legs.append(row)
            if not dropped:
                kept[side].append(row)
    if not kept["long"] or not kept["short"]:
        return WeekResult(None, legs, "empty leg after dropping missing entry/exit bars")
    price = mean(r["price_bp"] for r in kept["long"]) - mean(r["price_bp"] for r in kept["short"])
    fund = sum(mean(r["funding_bp"] for r in kept[side]) for side in ("long", "short"))
    cost = config.cost_bp
    net = price + fund - cost
    trade = {
        "entry_time": entry,
        "exit_time": exit_,
        "r_gross": (price + fund) / config.r_bp,
        "r_net": net / config.r_bp,
        "price_bp": price,
        "funding_bp": fund,
        "cost_bp": cost,
        "net_bp": net,
        "longs": " ".join(r["symbol"] for r in kept["long"]),
        "shorts": " ".join(r["symbol"] for r in kept["short"]),
        "n_long": len(kept["long"]),
        "n_short": len(kept["short"]),
    }
    return WeekResult(trade, legs)
