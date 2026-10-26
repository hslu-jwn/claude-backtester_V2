"""Condition partitions and skill diagnostics. Spec: strategy-profile.md."""

from dataclasses import asdict
from datetime import UTC

from backtester.analytics.bounds import BoundsConfig, mean_bounds
from backtester.analytics.detrend import detrend, load_drifts
from backtester.analytics.effective_n import trade_uniqueness
from backtester.analytics.market_classes import market_class
from backtester.analytics.regime import RegimeConfig, label_trades
from backtester.core.models import Direction
from backtester.sessions import Session, session_of

TRENDS = ("trend_up", "trend_down", "sideways")
VOLS = ("high", "low")
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
SESSION_NAMES = {Session.TOKYO: "Tokyo", Session.LONDON: "London", Session.NEW_YORK: "New York"}


def entry_session(at):
    session = session_of(at.astimezone(UTC))
    return SESSION_NAMES[session.session] if session else "other"


def _cell(name, indices, trades, detrended, bounds_config):
    subset = [trades[i] for i in indices]
    raw = [t.r_net for t in subset]
    values = [detrended[i]["detrended_r"] for i in indices]
    n = len(subset)
    net = sum(values) if None not in values else None
    bound = (
        mean_bounds(values, bounds_config)["lower90_bca"] if n >= 10 and net is not None else None
    )
    balance = peak = dd = 0.0
    for t in sorted(subset, key=lambda t: t.exit_time):
        balance += t.r_net
        peak = max(peak, balance)
        dd = max(dd, peak - balance)
    return {
        "condition": name,
        "trades": n,
        "effective_trades": trade_uniqueness(subset)["effective_trades"],
        "win_rate": sum(r > 0 for r in raw) / n if n else None,
        "net_r": sum(raw),
        "avg_r": sum(raw) / n if n else None,
        "detrended_net_r": net,
        "detrended_avg_r": net / n if n and net is not None else None,
        "lower90_bca": bound,
        "max_dd_r": dd,
    }


def build_profile(trades, labels, drifts, config=None, bounds_config=None):
    """Pure partitions; labels and whole-period drift align with original trade order."""
    trades, labels = list(trades), list(labels)
    if len(trades) != len(labels):
        raise ValueError("one regime label required per trade")
    cfg = config or RegimeConfig()
    bc = bounds_config or BoundsConfig()
    adjusted = detrend(trades, drifts)["trades"]
    groups = {
        "regime": {**{f"{t} / {v}": [] for t in TRENDS for v in VOLS}, "unknown": []},
        "regime_trend": {k: [] for k in (*TRENDS, "unknown")},
        "regime_vol": {k: [] for k in (*VOLS, "unknown")},
        "symbol": {},
        "market_class": {},
        "entry_session": {k: [] for k in ("Tokyo", "London", "New York", "other")},
        "direction": {k: [] for k in ("long", "short")},
        "weekday": {k: [] for k in WEEKDAYS},
    }
    for i, (t, label) in enumerate(zip(trades, labels, strict=True)):
        trend, vol = label.regime_trend, label.regime_vol
        combined = f"{trend} / {vol}" if trend in TRENDS and vol in VOLS else "unknown"
        values = (
            combined,
            trend,
            vol,
            t.symbol,
            market_class(t),
            entry_session(t.entry_time),
            "long" if t.direction in (Direction.BULLISH, "long") else "short",
            WEEKDAYS[t.entry_time.astimezone(UTC).weekday()],
        )
        for dimension, value in zip(groups.values(), values, strict=True):
            dimension.setdefault(value, []).append(i)
    dimensions, strongest = {}, []
    for name, cells in groups.items():
        rows = [_cell(k, indices, trades, adjusted, bc) for k, indices in cells.items()]
        eligible = [
            r
            for r in rows
            if r["trades"] >= cfg.min_trades_best
            and r["lower90_bca"] is not None
            and r["lower90_bca"] > 0
        ]
        best = max(eligible, key=lambda r: r["detrended_avg_r"]) if eligible else None
        dimensions[name] = {
            "cells": rows,
            "best": best["condition"] if best else None,
            "reason": None
            if best
            else (
                f"none: requires >= {cfg.min_trades_best} trades and a positive detrended "
                "90% BCa lower bound (missing drift or <10 trades makes bounds unavailable)"
            ),
        }
        strongest.extend(
            {"dimension": name, **r}
            for r in rows
            if r["lower90_bca"] is not None and r["lower90_bca"] > 0
        )
    return {
        "total_trades": len(trades),
        "config": {**asdict(cfg), "timeframe": cfg.timeframe.name},
        "bounds_config": asdict(bc),
        "day_boundary": "17:00 America/New_York (adapter default)",
        "dimensions": dimensions,
        "strongest_skill_cells": sorted(strongest, key=lambda r: r["lower90_bca"], reverse=True)[
            :5
        ],
        "trade_labels": [asdict(label) for label in labels],
    }


def calculate(trades, start, end, sources, config=None):
    trades = list(trades)
    drifts = load_drifts(sorted({t.symbol for t in trades}), start, end, sources)
    result = build_profile(trades, label_trades(trades, sources, config), drifts, config)
    result.update(start=start.isoformat(), end=end.isoformat(), drifts=drifts)
    return result


def markdown(result, label=""):
    lines = [
        "",
        f"## Strategy condition profile {label}".rstrip(),
        "",
        f"{result['total_trades']} trades. D1: {result.get('day_boundary', 'adapter default')}.",
        (
            "Bounds: one-sided IID BCa on detrended R; descriptive overlapping cells, "
            "without dependence or multiple-comparison correction."
        ),
    ]
    columns = (
        "trades",
        "effective_trades",
        "win_rate",
        "net_r",
        "avg_r",
        "detrended_net_r",
        "detrended_avg_r",
        "lower90_bca",
        "max_dd_r",
    )
    for name, dim in result["dimensions"].items():
        best = f"**{dim['best']}**" if dim["best"] else dim["reason"]
        lines += [
            "",
            f"### {name}",
            "",
            f"Best condition: {best}",
            "",
            (
                "| Condition | Trades | Effective trades | Win rate | Net R | R/trade | "
                "Detrended net R | Detrended R/trade | BCa lower 90% | Max DD R |"
            ),
            "|" + "---|" * 10,
        ]
        for row in dim["cells"]:
            condition = row["condition"]
            if condition == dim["best"]:
                condition = f"**{condition}**"
            cells = ["n/a" if row[k] is None else f"{row[k]:.6g}" for k in columns]
            lines.append("| " + " | ".join([condition, *cells]) + " |")
    lines += ["", "### Strongest skill cells", ""]
    for row in result["strongest_skill_cells"]:
        lines.append(
            f"- {row['dimension']}: {row['condition']}; lower90="
            f"{row['lower90_bca']:.6g} R/trade; {row['trades']} trades"
        )
    if not result["strongest_skill_cells"]:
        lines.append("none: no cell has a positive available 90% lower bound.")
    return lines
