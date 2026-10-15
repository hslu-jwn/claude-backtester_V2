"""Download Binance USD-M futures aggTrades into 1m bars + order flow (ROADMAP 11.9).
Logic and format: `data/binance.py`.

    python -m backtester.tools.binance_download                       # BTCUSDT ETHUSDT, 2020-01 .. latest
    python -m backtester.tools.binance_download BTCUSDT --start 2024-01 --end 2024-01
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path

from backtester.data.binance import (
    DEFAULT_SYMBOLS,
    FIRST_MONTH,
    TMP_DIR,
    BinanceConfig,
    download_symbol,
)


def _month(text: str) -> date:
    y, m = text.split("-")[:2]
    return date(int(y), int(m), 1)


def _log(text: str) -> None:
    print(f"{datetime.now(UTC):%H:%M:%S} {text}", flush=True)


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("symbols", nargs="*", default=list(DEFAULT_SYMBOLS))
    p.add_argument("--start", type=_month, default=FIRST_MONTH, help="YYYY-MM (default 2020-01)")
    p.add_argument("--end", type=_month, default=None, help="YYYY-MM (default: this month)")
    p.add_argument("--tmp", type=Path, default=TMP_DIR)
    args = p.parse_args(argv)
    end = args.end or datetime.now(UTC).date()
    cfg = BinanceConfig(tmp_dir=args.tmp)
    for symbol in (s.upper() for s in args.symbols):
        results = download_symbol(symbol, args.start, end, cfg, log=_log)
        _log(
            f"{symbol} done: {sum(r.bars for r in results):,} bars, "
            f"{sum(not r.skipped for r in results)} months written, "
            f"{sum(r.missing_days for r in results)} daily files not published"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
