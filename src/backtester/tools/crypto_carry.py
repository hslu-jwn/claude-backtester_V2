"""Weekly crypto carry research CSVs. Spec: strategy-crypto_carry.md › Rule (frozen).

python -m backtester.tools.crypto_carry [--start YYYY-MM-DD] [--end YYYY-MM-DD]
    [--out DIR] [--update] [--forward]
"""

from __future__ import annotations

import argparse
import csv
import math
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

import numpy as np

from backtester.data.binance import download_symbol
from backtester.data.sources import BINANCE_CACHE_DIR, SymbolSources
from backtester.engine.costs import FUNDING_DIR, FundingSeries, load_funding
from backtester.paths import RESULTS_DIR
from backtester.strategy.crypto_carry.book import DEFAULT, CryptoCarryConfig, signal, week_result
from backtester.tools.entry_screen import load_m1

FORWARD_START = date(2026, 11, 16)
FORWARD_PATH = Path("research/forward/crypto_carry.csv")
TRADE_COLUMNS = (
    "entry_time",
    "exit_time",
    "r_gross",
    "r_net",
    "price_bp",
    "funding_bp",
    "cost_bp",
    "net_bp",
    "longs",
    "shorts",
    "n_long",
    "n_short",
)
LEG_COLUMNS = ("week", "symbol", "side", "signal", "price_bp", "funding_bp", "dropped")
NUMERIC_COLUMNS = (
    "r_gross",
    "r_net",
    "price_bp",
    "funding_bp",
    "cost_bp",
    "net_bp",
    "n_long",
    "n_short",
)


def read_funding(symbols: Sequence[str]) -> dict[str, FundingSeries]:
    """Read fresh snapshots, including after a resumable update in this process."""
    load_funding.cache_clear()
    return {sym: load_funding(FUNDING_DIR / f"{sym}.csv") for sym in symbols}


class _DayIndexSources(SymbolSources):
    """Reuse a single directory listing while loading endpoint days through load_m1."""

    def __init__(self, sources: SymbolSources):
        super().__init__(sources.cache_dirs, sources.preferred_dirs, sources.fallback_dirs)
        object.__setattr__(self, "days", {s: sources.cached_days(s) for s in sources.symbols})

    def cached_days(self, symbol: str) -> list[date]:
        return self.days[symbol]


def compute_weeks(
    funding: Mapping[str, FundingSeries],
    sources: SymbolSources,
    start: date | None = None,
    end: date | None = None,
    config: CryptoCarryConfig = DEFAULT,
    *,
    complete_only: bool = False,
) -> tuple[list[dict], list[dict], list[tuple[datetime, str]]]:
    """Read endpoint prices and emit closed weekly books, diagnostics and skipped weeks.

    Explicit end dates include that day's Sunday exit. With no end, every eligible
    funding file must reach exit; future weeks are excluded by the current UTC date.
    Spec: strategy-crypto_carry.md › Rule (frozen), Decisions by the user 3.
    """
    starts = [f.times[0].date() for f in funding.values() if f.times]
    if not starts:
        return [], [], []
    first = start or min(starts)
    monday = datetime.combine(first, time(), UTC) + timedelta(days=(-first.weekday()) % 7)
    require_complete = complete_only or end is None
    last = end or datetime.now(UTC).date() - timedelta(days=1)
    last_time = datetime.combine(last + timedelta(days=1), time(), UTC)
    sources = _DayIndexSources(sources)
    day_sets = {s: set(sources.cached_days(s)) for s in funding}
    trades, legs, skipped = [], [], []
    newest = max(f.times[-1] for f in funding.values() if f.times)
    while monday + timedelta(days=7, minutes=-1) < last_time:
        exit_ = monday + timedelta(days=7, minutes=-1)
        signals = {
            s: value for s, f in funding.items() if (value := signal(f, monday, config)) is not None
        }
        # A symbol whose funding stopped 7+ days before the newest print of any symbol (delisted)
        # stays ranked, as frozen, but must not hold the week back. Measured against the newest print,
        # not the Monday, so a feed that lags for every symbol still holds the week back.
        live = [s for s in signals if funding[s].times[-1] > newest - timedelta(days=7)]
        if require_complete and any(funding[s].times[-1] < exit_ for s in live):
            monday += timedelta(days=7)
            continue
        prices = {}
        for sym in signals:
            closes = {}
            for bar in (monday, exit_ - timedelta(minutes=1)):
                if bar.date() not in day_sets[sym]:
                    continue
                try:
                    data = load_m1(sym, sources, bar.date(), bar.date())
                except SystemExit as exc:
                    # entry_screen reports physically empty cached days via SystemExit.
                    expected = (
                        f"{sym}: the cached days between {bar.date()} and {bar.date()} are empty"
                    )
                    if str(exc) != expected:
                        raise
                    continue
                idx = int(np.searchsorted(data.open_s, int(bar.timestamp())))
                if idx < len(data.open_s) and data.open_s[idx] == int(bar.timestamp()):
                    closes[bar] = float(data.close[idx])
            prices[sym] = closes
        result = week_result(monday, signals, prices, funding, config)
        legs.extend(result.legs)
        if result.trade is not None:
            trades.append(result.trade)
        else:
            skipped.append((monday, result.skipped))
        monday += timedelta(days=7)
    return trades, legs, skipped


def _serialized(row: dict, columns: Sequence[str]) -> dict:
    return {
        key: row[key].astimezone(UTC).isoformat() if isinstance(row[key], datetime) else row[key]
        for key in columns
    }


def write_csv(path: Path, rows: list[dict], columns: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(_serialized(row, columns) for row in rows)


def append_forward(path: Path, rows: list[dict]) -> None:
    """Validate every existing observation before appending any bytes.

    Spec: strategy-crypto_carry.md › Decisions by the user 3 (forward paper log).
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
    pending = []
    seen = set()
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
    header = not path.exists() or path.stat().st_size == 0
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
        "1 R = 1,000 bp of one side's notional; losses are not capped at 1 R."
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat)
    parser.add_argument("--end", type=date.fromisoformat)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--forward", action="store_true")
    args = parser.parse_args(argv)
    if args.forward and args.start is not None and args.start != FORWARD_START:
        parser.error("--forward starts at 2026-11-16; --start cannot override it")
    if args.start and args.end and args.end < args.start:
        parser.error("--end must be on or after --start")
    if args.update:
        # shortcut: only the last 3 months; the history is cached already (2026-11-13). After a pause of
        # more than 2 months fill the gap with `binance_download --klines --start YYYY-MM` first.
        this_month = datetime.now(UTC).date().replace(day=1)
        start_month = (this_month - timedelta(days=62)).replace(day=1)
        for sym in DEFAULT.symbols:
            download_symbol(sym, start_month, this_month, kind="klines")
    try:
        funding = read_funding(DEFAULT.symbols)
        trades, legs, skipped = compute_weeks(
            funding,
            SymbolSources.single(BINANCE_CACHE_DIR, DEFAULT.symbols),
            FORWARD_START if args.forward else args.start,
            args.end,
            complete_only=args.forward,
        )
        if args.forward:
            append_forward(FORWARD_PATH, trades)
        out = args.out or RESULTS_DIR / "crypto_carry" / datetime.now(UTC).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )
        write_csv(out / "trades.csv", trades, TRADE_COLUMNS)
        write_csv(out / "legs.csv", legs, LEG_COLUMNS)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"crypto carry: {exc}\n")
    for monday, reason in skipped:
        print(f"skipped {monday.date()}: {reason}")
    print(summary(trades))
    print(f"output: {out}")


if __name__ == "__main__":
    main()
