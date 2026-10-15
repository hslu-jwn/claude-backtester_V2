"""Download FTMO's M1 history into `data/cache/mt5/` (ROADMAP 11.5). Logic and format:
`data/mt5_download.py`.

    python -m backtester.tools.mt5_download                          # all five symbols, all history
    python -m backtester.tools.mt5_download NAS100 US500 --start 2021-09-15 --end 2022-12-31

Needs the MT5 terminal running and logged in; no login is read or printed.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from backtester.data.adapters.mt5_adapter import Mt5Adapter
from backtester.data.cache import MT5_CACHE_DIR
from backtester.data.mt5_download import (
    DEFAULT_CLOCK,
    DEFAULT_NAMES,
    DEFAULT_SYMBOLS,
    download_symbol,
)


def main(argv: Sequence[str] | None = None) -> int:
    from backtester.live.connection import session
    from backtester.live.trading_settings import load_trading_settings

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("symbols", nargs="*", default=list(DEFAULT_SYMBOLS))
    p.add_argument("--start", type=date.fromisoformat, default=None, help="default: all history")
    p.add_argument("--end", type=date.fromisoformat, default=None, help="default: yesterday UTC")
    p.add_argument("--out", type=Path, default=MT5_CACHE_DIR)
    args = p.parse_args(argv)
    settings = load_trading_settings()
    names = {**DEFAULT_NAMES, **{s: n for s, n in settings.symbols.items() if n != s}}
    clock = settings.server_clock or DEFAULT_CLOCK
    print(f"server clock {clock.label}; cache {args.out}", flush=True)
    with session(settings, None) as mt5:
        adapter = Mt5Adapter(mt5, clock, names)
        for symbol in (s.upper() for s in args.symbols):
            r = download_symbol(
                adapter, symbol, args.start, args.end, args.out, log=lambda t: print(t, flush=True)
            )
            print(
                f"{symbol} ({names.get(symbol, symbol)}): {r.bars:,} bars, {r.days_written} days "
                f"({r.days_empty} empty), {r.first_day} .. {r.last_day}",
                flush=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
