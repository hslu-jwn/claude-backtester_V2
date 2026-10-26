"""Print resampled candles from the cache, to compare them with another chart.

    python -m backtester.tools.show XAUUSD M5 2026-09-02T13:00 2026-09-02T14:00
    python -m backtester.tools.show XAUUSD H1 2026-09-02 2026-09-03 --tz Etc/GMT-3

START/END are UTC (END exclusive). `--tz` adds a column with the open time in another time
zone, e.g. MT5 server time (`Etc/GMT-3` = UTC+3; note the inverted sign in Etc/ names).
`--atr N` adds the ATR(N) at each candle's close (compare with TradingView's ATR indicator),
the range a candle needed to be a strong move (k x ATR of the candles before it) and a
`strong` flag. Earlier candles are loaded for the warm-up but not printed.
Spec: ROADMAP.md › 0.2, 2.1; confluences.md › Strong-move filter.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.data.adapters.cache_adapter import (
    CacheAdapter,
    MissingCacheError,
    candles_from_frame,
)
from backtester.data.resample import supported
from backtester.data.sources import DEFAULT_SOURCES
from backtester.detectors.atr import StrongMoveConfig, StrongMoveFilter

# ATR warm-up loaded before START: this many ATR periods (Wilder's seed has faded by then)
# plus a few days so weekends and holidays don't eat the warm-up.
ATR_WARMUP_PERIODS = 20
ATR_WARMUP_EXTRA = timedelta(days=4)


def _zone(value: str) -> ZoneInfo:
    try:
        return ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise argparse.ArgumentTypeError(f"unknown time zone: {value}") from exc


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("symbol", choices=DEFAULT_SOURCES.symbols)
    p.add_argument("timeframe", choices=[tf.name for tf in Timeframe if supported(tf)])
    p.add_argument("start", type=datetime.fromisoformat, help="UTC, e.g. 2026-09-02T13:00")
    p.add_argument("end", type=datetime.fromisoformat, help="UTC, exclusive")
    p.add_argument("--tz", type=_zone, help="also show open time in this time zone")
    p.add_argument("--atr", type=int, metavar="N", help="add ATR(N) and the strong-move flag")
    p.add_argument("--atr-mult", type=float, default=StrongMoveConfig().atr_mult, metavar="K")
    p.add_argument("--cache-dir", type=Path, help="default: the symbol's source (data/sources.py)")
    args = p.parse_args(argv)
    args.start = (
        args.start.replace(tzinfo=UTC) if args.start.tzinfo is None else args.start.astimezone(UTC)
    )
    args.end = args.end.replace(tzinfo=UTC) if args.end.tzinfo is None else args.end.astimezone(UTC)
    if args.end <= args.start:
        p.error("end must be after start")

    adapter = (
        CacheAdapter(args.cache_dir) if args.cache_dir else DEFAULT_SOURCES.adapter(args.symbol)
    )
    timeframe = Timeframe[args.timeframe]
    try:
        frame = adapter.fetch_frame(args.symbol, timeframe, args.start, args.end)
        if args.atr and not frame.empty:
            frame = add_atr(adapter, args, timeframe, frame)
    except MissingCacheError as e:
        print(e)
        return 1
    if frame.empty:
        print("No candles in range.")
        return 0
    table = frame.assign(ts=frame["ts"].dt.strftime("%Y-%m-%d %H:%M"))
    table = table.rename(columns={"ts": "open time UTC"})
    if args.tz:
        local = frame["ts"].dt.tz_convert(args.tz).dt.strftime("%Y-%m-%d %H:%M")
        table.insert(1, f"open time {args.tz.key}", local)
    with pd.option_context("display.width", 200, "display.max_rows", 500):
        print(
            table.to_string(index=False, float_format=lambda x: f"{x:.5f}".rstrip("0").rstrip("."))
        )
    print(f"\n{len(frame)} {args.timeframe} candles (bid prices; spread = mean ask - bid)")
    return 0


def add_atr(
    adapter: CacheAdapter, args: argparse.Namespace, timeframe: Timeframe, frame: pd.DataFrame
) -> pd.DataFrame:
    """Columns atr, needed (k x previous ATR) and strong, computed with a warm-up."""
    config = StrongMoveConfig(atr_period=args.atr, atr_mult=args.atr_mult)
    warmup = ATR_WARMUP_PERIODS * args.atr * timeframe.duration + ATR_WARMUP_EXTRA
    from_ = args.start - warmup
    while True:  # shorten the warm-up day by day until all its days are cached
        try:
            full = adapter.fetch_frame(args.symbol, timeframe, from_, args.end)
            break
        except MissingCacheError:
            from_ = datetime.combine(from_.date() + timedelta(days=1), datetime.min.time(), UTC)
            if from_ >= args.start:
                full, from_ = frame, args.start
                break
    warmup_candles = len(full) - len(frame)
    if warmup_candles < ATR_WARMUP_PERIODS * args.atr:
        print(
            f"Note: only {warmup_candles} warm-up candles in the cache "
            f"(want {ATR_WARMUP_PERIODS * args.atr}); early ATR values may differ from TradingView."
        )
    series = CandleSeries(args.symbol, timeframe, candles_from_frame(full))
    f = StrongMoveFilter(config)
    for i in range(len(series)):
        f.update(series.view(i))
    first = len(full) - len(frame)
    idx = range(first, len(full))
    return frame.assign(
        atr=[f.atr.at(i) for i in idx],
        needed=[f.threshold_at(i) for i in idx],
        range=(frame["high"] - frame["low"]).to_list(),
        strong=["yes" if f.is_strong(i) else "" for i in idx],
    )


if __name__ == "__main__":
    raise SystemExit(main())
