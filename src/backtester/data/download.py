"""Download Dukascopy M1 bid/ask candles into the local Parquet cache.

    python -m backtester.data.download XAUUSD 2020-01-01 2026-10-01

END is exclusive (same as `DataAdapter.fetch`). Already cached days are skipped, so an
interrupted download can simply be started again. The run stops early on HTTP 429, or when
several days in a row fail with 503s / timeouts (Dukascopy throttling).
Spec: ROADMAP.md › 0.1.
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import replace
from datetime import date
from pathlib import Path

import pandas as pd

from backtester.data.dukascopy import (
    DEFAULT_CACHE_DIR,
    POINT_FACTORS,
    DayStatus,
    DownloadStoppedError,
    DukascopyConfig,
    DukascopyDownloader,
    RateLimitedError,
    read_cached_day,
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("symbol", choices=sorted(POINT_FACTORS))
    p.add_argument("start", type=date.fromisoformat, help="first day, YYYY-MM-DD (UTC)")
    p.add_argument("end", type=date.fromisoformat, help="end day, exclusive, YYYY-MM-DD (UTC)")
    p.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    p.add_argument(
        "--delay",
        type=float,
        default=DukascopyConfig().request_delay_s,
        help="seconds to wait after each request",
    )
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    config = replace(DukascopyConfig(), request_delay_s=args.delay)
    downloader = DukascopyDownloader(args.cache_dir, config)
    counts = dict.fromkeys(DayStatus, 0)
    failed: list[date] = []
    stopped = False
    try:
        for result in downloader.download(args.symbol, args.start, args.end):
            counts[result.status] += 1
            if result.status is DayStatus.FAILED:
                failed.append(result.day)
            detail = f"{result.rows} rows" if result.rows else result.error
            print(f"{args.symbol} {result.day}  {result.status.value:<10} {detail}", flush=True)
    except RateLimitedError as e:
        stopped = True
        print(f"\nSTOPPED: {e}")
        print(
            "Dukascopy is blocking this IP address for now. Wait (at least an hour), then run "
            "the same command again, ideally with a larger --delay. Cached days are kept."
        )
    except DownloadStoppedError as e:
        stopped = True
        print(f"\nSTOPPED: {e}")
        print(
            "Dukascopy is throttling this connection or cannot be reached. Wait a while, then "
            f"run the same command again with a larger --delay (now {args.delay:g} s, try "
            f"{2 * args.delay:g}), or from another network (phone hotspot). Download one pair "
            "at a time. Cached days are kept."
        )

    print("\n" + ", ".join(f"{s.value}: {n}" for s, n in counts.items()))
    if failed:
        print(f"Failed days: {', '.join(map(str, failed))}. Run the same command again to retry.")
    _print_sample(downloader, args.symbol, args.start, args.end)
    return 1 if failed or stopped else 0


def _print_sample(downloader: DukascopyDownloader, symbol: str, start: date, end: date) -> None:
    """Show the first and last cached candle so prices can be eyeballed against a chart."""
    frames = [
        read_cached_day(path)
        for path in sorted((downloader.cache_dir / symbol).glob("*/*.parquet"))
        if start <= date.fromisoformat(path.stem) < end
    ]
    frames = [f for f in frames if not f.empty]
    if not frames:
        return
    data = pd.concat(frames, ignore_index=True)
    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(f"\n{len(data)} M1 rows in range. First and last (UTC open time):")
        print(data.iloc[[0, -1]].to_string(index=False))


if __name__ == "__main__":
    raise SystemExit(main())
