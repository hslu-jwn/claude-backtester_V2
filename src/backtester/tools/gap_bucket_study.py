"""Descriptive gap-bucket study; no strategy backtests or trial logging.

    python -m backtester.tools.gap_bucket_study --mode index
    python -m backtester.tools.gap_bucket_study --mode fx

Spec: research-runner.md > Standalone gap-bucket study; strategy-gap-momentum.md.
"""

from __future__ import annotations

import argparse
import csv
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from backtester.analytics.gap_buckets import GapDay, bucket_rows, gap_days
from backtester.analytics.verdict import middle_date
from backtester.core.models import Timeframe
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.paths import RESULTS_DIR
from backtester.strategy.gap_momentum.config import GapMomentumConfig

SYMBOLS = {"index": ("NAS100", "US500"), "fx": ("GBPUSD", "EURUSD", "XAUUSD")}
START = date(2015, 1, 1)
DEV_END = date(2021, 9, 13)
MINUTES_PER_HOUR = 60


def data_start(symbols: Sequence[str], sources: SymbolSources, start: date) -> date:
    """`start`, or the first cached day when the data begins later (halves are cut there)."""
    firsts = [min(days) for s in symbols if (days := sources.cached_days(s))]
    return max(start, min(firsts)) if firsts else start


def load_session_bars(
    symbol: str, cache_dir: Path, start: date, end: date, config: GapMomentumConfig
) -> list[tuple[datetime, float, float, float]]:
    """(close time UTC, high, low, close) of the cached 1m candles closing within the session
    [open, close] of `config` in New York time, for the cached days of [start, end]."""
    sources = SymbolSources.single(cache_dir, [symbol])
    cached = sorted(d for d in sources.cached_days(symbol) if start <= d <= end)
    if not cached:
        raise ValueError(f"{symbol}: no cached days between {start} and {end}")
    first = datetime(cached[0].year, cached[0].month, cached[0].day, tzinfo=UTC)
    last = cached[-1] + timedelta(days=1)
    frame = sources.adapter(symbol).fetch_frame(
        symbol, Timeframe.M1, first, datetime(last.year, last.month, last.day, tzinfo=UTC)
    )
    close_time = frame["ts"] + Timeframe.M1.duration
    local = close_time.dt.tz_convert(config.zone)
    minute = local.dt.hour * MINUTES_PER_HOUR + local.dt.minute
    lo = config.session_open.hour * MINUTES_PER_HOUR + config.session_open.minute
    hi = config.session_close.hour * MINUTES_PER_HOUR + config.session_close.minute
    keep = (minute >= lo) & (minute <= hi)
    return [
        (ts.to_pydatetime(), float(h), float(low), float(c))
        for ts, h, low, c in zip(
            close_time[keep], frame["high"][keep], frame["low"][keep], frame["close"][keep],
            strict=True,
        )
    ]  # fmt: skip


def study_rows(
    symbols: Sequence[str], sources: SymbolSources, start: date, end: date, mode: str,
    middle: date,
) -> list[dict]:  # fmt: skip
    """Gap-bucket rows per symbol and pooled over the symbols (`ALL`), for days from `start`."""
    config = GapMomentumConfig(mode=mode)
    warm = timedelta(days=int(config.vol_days * 1.5) + 14)  # history for the sd and the ATR
    rows: list[dict] = []
    pooled: list[GapDay] = []
    for symbol in symbols:
        bars = load_session_bars(symbol, sources.cache_dir(symbol), start - warm, end, config)
        days = [g for g in gap_days(bars, config) if g.day >= start]
        pooled += days
        rows += bucket_rows(days, symbol, middle)
    if len(symbols) > 1:
        rows += bucket_rows(pooled, "ALL", middle)
    return rows


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--mode", choices=tuple(SYMBOLS), default="index")
    p.add_argument("--symbols", nargs="+", default=None)
    p.add_argument("--start", type=date.fromisoformat, default=START)
    p.add_argument("--end", type=date.fromisoformat, default=DEV_END)
    p.add_argument("--allow-test-period", action="store_true")
    p.add_argument("--cache-dir", type=Path, default=None)
    p.add_argument("--out", type=Path, default=None)
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.end > DEV_END and not args.allow_test_period:
        raise SystemExit(
            f"end {args.end} is after {DEV_END}: untouched test period (use --allow-test-period)"
        )
    if args.start > args.end:
        raise SystemExit("start must not be after end")
    symbols = list(dict.fromkeys(s.upper() for s in (args.symbols or SYMBOLS[args.mode])))
    sources = (
        DEFAULT_SOURCES if args.cache_dir is None else SymbolSources.single(args.cache_dir, symbols)
    )
    first = data_start(symbols, sources, args.start)
    rows = study_rows(symbols, sources, first, args.end, args.mode, middle_date(first, args.end))
    out = args.out or RESULTS_DIR / "gap_bucket_study" / args.mode
    out.mkdir(parents=True, exist_ok=True)
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with (out / "gap_buckets.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"written to {out / 'gap_buckets.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
