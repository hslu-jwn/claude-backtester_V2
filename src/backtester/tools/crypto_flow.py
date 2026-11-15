"""Weekly crypto taker-flow research CSVs. Spec: strategy-crypto_flow.md › Build.

python -m backtester.tools.crypto_flow [--start YYYY-MM-DD] [--end YYYY-MM-DD]
    [--out DIR] [--update] [--forward] [--liquid]

--liquid: the frozen FB-017 variant (top 100 by median quote volume), own forward log.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.data import binance_wide
from backtester.paths import RESULTS_DIR
from backtester.strategy.crypto_flow.book import (
    DEFAULT,
    CryptoFlowConfig,
    eligible_signals,
    pick_legs,
    week_result,
)
from backtester.tools.crypto_carry import _serialized, write_csv

FORWARD_START = date(2026, 11, 16)
FORWARD_PATH = Path("research/forward/crypto_flow.csv")
LIQUID_FORWARD_PATH = Path("research/forward/crypto_flow_top100.csv")
LIQUID = CryptoFlowConfig(top_volume=100)  # ideas.md › FB-017, frozen 2026-11-15
TRADE_COLUMNS = (
    "entry_time",
    "exit_time",
    "r_gross",
    "r_net",
    "price_bp",
    "funding_bp",
    "cost_bp",
    "net_bp",
    "n_long",
    "n_short",
    "n_eligible",
)
LEG_COLUMNS = ("week", "symbol", "side", "signal", "price_bp", "funding_bp", "exit_day")
NUMERIC_COLUMNS = TRADE_COLUMNS[2:]


def load(roots=binance_wide.ROOTS) -> tuple[dict[str, pd.DataFrame], dict[str, pd.Series]]:
    """Fresh snapshots after any update; file layout belongs to the data layer."""
    symbols = binance_wide.symbols(roots)
    klines = {s: binance_wide.read_klines(s, roots) for s in symbols}
    return (
        {s: d for s, d in klines.items() if len(d)},
        {s: binance_wide.read_funding(s, roots) for s in symbols},
    )


def compute_weeks(
    klines: Mapping[str, pd.DataFrame],
    funding: Mapping[str, pd.Series],
    start: date | None = None,
    end: date | None = None,
    config: CryptoFlowConfig = DEFAULT,
    *,
    complete_only: bool = False,
) -> tuple[list[dict], list[dict]]:
    """Emit whole Monday–Sunday books, never future weeks.

    Default end (and forward mode) requires both the newest daily day and newest
    settlement anywhere in the universe to reach the Sunday exit. A Sunday daily
    bar covers its day's close. Explicit historical ends reproduce the screen.
    Spec: strategy-crypto_flow.md › Rule (frozen), Build.
    """
    dates = [d.index[0] for d in klines.values() if len(d)]
    if not dates:
        return [], []
    first = pd.Timestamp(start, tz="UTC") if start else min(dates)
    monday = first + pd.Timedelta(days=(-first.weekday()) % 7)
    # Only exits already in the past may be emitted, even with explicit --end.
    now = pd.Timestamp.now(tz="UTC")
    last = min(pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1), now) if end else now
    if end is None or complete_only:
        rates = [f.index.max() for f in funding.values() if len(f)]
        if not rates:
            return [], []
        daily_close = max(d.index[-1] for d in klines.values() if len(d)) + pd.Timedelta(days=1)
        last = min(last, daily_close, max(rates))
    trades, legs = [], []
    while monday + pd.Timedelta(days=7, minutes=-1) <= last:
        signals = eligible_signals(klines, monday, config)
        selected = pick_legs(signals, config)
        if selected is not None:
            result = week_result(monday, *selected, klines, funding, config)
            result.trade["n_eligible"] = len(signals)
            trades.append(result.trade)
            legs.extend(result.legs)
        monday += pd.Timedelta(days=7)
    return trades, legs


def append_forward(path: Path, rows: list[dict]) -> None:
    """Validate all observations before appending; never rewrite existing bytes.

    Same checks as crypto_carry.append_forward, with Strategy 20's columns.
    Spec: strategy-crypto_flow.md › Build (append-only forward paper log).
    """
    existing = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if tuple(reader.fieldnames or ()) != TRADE_COLUMNS:
                raise ValueError("forward log has unexpected columns")
            for row in reader:
                key = row["entry_time"]
                if key in existing:
                    raise ValueError(f"duplicate forward week {key}")
                existing[key] = row
    pending, seen = [], set()
    for row in rows:
        new = _serialized(row, TRADE_COLUMNS)
        key = str(new["entry_time"])
        if key in seen:
            raise ValueError(f"duplicate computed week {key}")
        seen.add(key)
        if key in existing:
            old = existing[key]
            for col in TRADE_COLUMNS:
                if col in NUMERIC_COLUMNS:
                    a, b = float(old[col]), float(new[col])
                    equal = math.isfinite(a) and math.isfinite(b) and abs(a - b) <= 1e-9
                else:
                    equal = old[col] == str(new[col])
                if not equal:
                    raise ValueError(f"data changed under forward log: week {key}, {col}")
        else:
            if existing and key <= max(existing):
                raise ValueError(f"cannot append out-of-order forward week {key}")
            pending.append(new)
    if not pending:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=TRADE_COLUMNS)
        if header:
            writer.writeheader()
        writer.writerows(sorted(pending, key=lambda row: row["entry_time"]))


def summary(trades: list[dict]) -> str:
    net = np.array([r["net_bp"] for r in trades], dtype=float)
    if not len(net):
        return "weeks 0; no completed book"
    sd = float(net.std(ddof=1)) if len(net) > 1 else float("nan")
    t = float(net.mean() / sd * np.sqrt(len(net))) if sd > 0 else float("nan")
    equity = np.r_[0.0, np.cumsum([r["r_net"] for r in trades])]
    drawdown = float((equity - np.maximum.accumulate(equity)).min())
    return (
        f"weeks {len(net)}, mean net {net.mean():.4f} bp, t {t:.4f}, sd {sd:.4f} bp, "
        f"worst week {net.min():.4f} bp, max drawdown {drawdown:.4f} R\n"
        "1 R = 600 bp of one side's notional; losses are not capped at 1 R."
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat)
    parser.add_argument("--end", type=date.fromisoformat)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--forward", action="store_true")
    parser.add_argument("--liquid", action="store_true")
    args = parser.parse_args(argv)
    if args.forward and args.start is not None and args.start != FORWARD_START:
        parser.error("--forward starts at 2026-11-16; --start cannot override it")
    start = FORWARD_START if args.forward else args.start
    if start and args.end and args.end < start:
        parser.error("--end must be on or after --start")
    try:
        if args.update:
            last_month = datetime.now(UTC).date().replace(day=1) - timedelta(days=1)
            binance_wide.update(binance_wide.ROOTS[-1], last_month.strftime("%Y-%m"))
        config = LIQUID if args.liquid else DEFAULT
        trades, legs = compute_weeks(*load(), start, args.end, config, complete_only=args.forward)
        if args.forward:
            append_forward(LIQUID_FORWARD_PATH if args.liquid else FORWARD_PATH, trades)
        out = args.out or RESULTS_DIR / "crypto_flow" / datetime.now(UTC).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        write_csv(out / "trades.csv", trades, TRADE_COLUMNS)
        write_csv(out / "legs.csv", legs, LEG_COLUMNS)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"crypto flow: {exc}\n")
    print(summary(trades))
    print(f"output: {out}")


if __name__ == "__main__":
    main()
