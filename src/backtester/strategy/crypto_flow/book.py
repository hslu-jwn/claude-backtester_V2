"""Pure weekly flow books. Spec: strategy-crypto_flow.md › Rule (frozen)."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import mean

import pandas as pd


@dataclass(frozen=True)
class CryptoFlowConfig:
    """Frozen defaults. Spec: strategy-crypto_flow.md › Rule (frozen), Risk unit."""

    min_bars: int = 60
    volume_window: int = 30
    min_quote_volume: float = 5e6
    min_eligible: int = 20
    signal_days: int = 7
    quantile: int = 5
    cost_bp: float = 20.0
    r_bp: float = 600.0


DEFAULT = CryptoFlowConfig()


def _monday(value) -> pd.Timestamp:
    value = pd.Timestamp(value)
    if value.tzinfo is None:
        raise ValueError("Monday must be timezone-aware")
    value = value.tz_convert("UTC")
    if value.weekday() or value != value.normalize():
        raise ValueError("expected Monday 00:00 UTC")
    return value


def eligible_signals(
    klines: Mapping[str, pd.DataFrame],
    monday,
    config: CryptoFlowConfig = DEFAULT,
) -> dict[str, float]:
    """Use only pre-entry bars; NaN retains eligibility but cannot be ranked.

    Spec: strategy-crypto_flow.md › Rule (frozen), rules 1–2.
    """
    monday = _monday(monday)
    signals = {}
    for symbol, data in klines.items():
        if monday not in data.index:
            continue
        past = data.loc[data.index < monday]
        if len(past) < config.min_bars:
            continue
        if past.quote_volume.iloc[-config.volume_window :].median() < config.min_quote_volume:
            continue
        last = past.loc[past.index >= monday - pd.Timedelta(days=config.signal_days)]
        if len(last) < config.signal_days:
            continue
        volume = last.volume.sum()
        signals[symbol] = float(
            (2 * last.taker_buy_volume - last.volume).sum() / volume
            if volume != 0
            else float("nan")
        )
    return signals


def pick_legs(
    signals: Mapping[str, float],
    config: CryptoFlowConfig = DEFAULT,
) -> tuple[list[str], list[str]] | None:
    """Rank by (flow, symbol). Spec: strategy-crypto_flow.md › Rule (frozen), rule 3."""
    if len(signals) < config.min_eligible:
        return None
    ranked = sorted(
        (s for s in signals if not math.isnan(signals[s])), key=lambda s: (signals[s], s)
    )
    n = len(ranked) // config.quantile
    if n == 0:
        return None
    return ranked[-n:], ranked[:n]


@dataclass(frozen=True)
class WeekResult:
    """One observation and its members; leg price returns are underlying, funding signed."""

    trade: dict
    legs: list[dict]


def week_result(
    monday,
    longs: Sequence[str],
    shorts: Sequence[str],
    klines: Mapping[str, pd.DataFrame],
    funding: Mapping[str, pd.Series],
    config: CryptoFlowConfig = DEFAULT,
) -> WeekResult:
    """Evaluate a fixed book with last-bar exits and all strictly interior settlements.

    Per-member price_bp is the underlying return; funding_bp is signed cash flow.
    Spec: strategy-crypto_flow.md › Rule (frozen), rules 4–6; Assumptions A4.
    """
    monday = _monday(monday)
    next_monday = monday + pd.Timedelta(days=7)
    signals = eligible_signals({s: klines[s] for s in (*longs, *shorts)}, monday, config)
    legs = []
    for side, members in (("long", longs), ("short", shorts)):
        if not members:
            raise ValueError("empty book leg")
        direction = 1 if side == "long" else -1
        for symbol in members:
            data = klines[symbol]
            held = data.loc[(data.index >= monday) & (data.index < next_monday)]
            if monday not in held.index:
                raise ValueError(f"missing Monday entry for {symbol}")
            entry, exit_ = float(held.open.iloc[0]), float(held.close.iloc[-1])
            if not all(math.isfinite(p) and p > 0 for p in (entry, exit_)):
                raise ValueError(f"prices must be finite and positive: {symbol}")
            rates = funding.get(symbol)
            paid = (
                float(rates.loc[(rates.index > monday) & (rates.index < next_monday)].sum())
                if rates is not None
                else 0.0
            )
            legs.append(
                {
                    "week": monday,
                    "symbol": symbol,
                    "side": side,
                    "signal": signals.get(symbol, float("nan")),
                    "price_bp": (exit_ / entry - 1) * 1e4,
                    "funding_bp": -direction * paid * 1e4,
                    "exit_day": held.index[-1],
                }
            )
    price = mean(r["price_bp"] for r in legs if r["side"] == "long") - mean(
        r["price_bp"] for r in legs if r["side"] == "short"
    )
    cash = mean(r["funding_bp"] for r in legs if r["side"] == "long") + mean(
        r["funding_bp"] for r in legs if r["side"] == "short"
    )
    net = price + cash - config.cost_bp
    return WeekResult(
        {
            "entry_time": monday,
            "exit_time": next_monday - pd.Timedelta(minutes=1),
            "r_gross": (price + cash) / config.r_bp,
            "r_net": net / config.r_bp,
            "price_bp": price,
            "funding_bp": cash,
            "cost_bp": config.cost_bp,
            "net_bp": net,
            "n_long": len(longs),
            "n_short": len(shorts),
        },
        legs,
    )
