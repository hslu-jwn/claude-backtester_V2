"""Print resampled candles from the cache, to compare them with another chart.

    python -m backtester.data.show XAUUSD M5 2026-09-02T13:00 2026-09-02T14:00
    python -m backtester.data.show XAUUSD H1 2026-09-02 2026-09-03 --tz Etc/GMT-3

START/END are UTC (END exclusive). `--tz` adds a column with the open time in another time
zone, e.g. MT5 server time (`Etc/GMT-3` = UTC+3; note the inverted sign in Etc/ names).
Spec: ROADMAP.md › 0.2.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from backtester.core.models import Timeframe
from backtester.data.adapters.cache_adapter import CacheAdapter, MissingCacheError
from backtester.data.dukascopy import DEFAULT_CACHE_DIR, POINT_FACTORS
from backtester.data.resample import supported


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("symbol", choices=sorted(POINT_FACTORS))
    p.add_argument("timeframe", choices=[tf.name for tf in Timeframe if supported(tf)])
    p.add_argument("start", type=datetime.fromisoformat, help="UTC, e.g. 2026-09-02T13:00")
    p.add_argument("end", type=datetime.fromisoformat, help="UTC, exclusive")
    p.add_argument("--tz", type=ZoneInfo, help="also show open time in this time zone")
    p.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    args = p.parse_args(argv)

    try:
        frame = CacheAdapter(args.cache_dir).fetch_frame(
            args.symbol, Timeframe[args.timeframe], args.start, args.end
        )
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


if __name__ == "__main__":
    raise SystemExit(main())
