"""Check the FTMO server clock rule for the years of the downloaded history (ROADMAP 11.5).

    python -m backtester.tools.mt5_clock_check NAS100 US500 --first-year 2018

Per week of MT5's H1 history it finds the whole-hour offset that lines the bars up with the
histdata cache (`mt5_compare.weekly_offsets`, only where both exist), then counts per year
how many weeks the rule `America/New_York + 7 h` (or `--zone` / `--shift`) predicts and lists
the misses. Research tool: it changes no setting and reads no login.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, date, datetime

import pandas as pd

from backtester.core.models import Timeframe
from backtester.data.adapters.mt5_adapter import Mt5Adapter, ServerClock
from backtester.data.sources import DEFAULT_SOURCES
from backtester.tools.mt5_compare import cached_frame, predicted_offset, weekly_offsets


def clock_report(weeks: pd.DataFrame, clock: ServerClock) -> pd.DataFrame:
    """Per calendar year: weeks, weeks the rule predicts, and the misses as `date (Nh)`."""
    rows = []
    for year, part in weeks.groupby(pd.to_datetime(weeks["week"]).dt.year):
        misses = [
            f"{r.week} ({r.offset_h}h)"
            for r in part.itertuples()
            if predicted_offset(clock, r.week) != r.offset_h
        ]
        rows.append(
            {
                "year": int(year),
                "weeks": len(part),
                "hits": len(part) - len(misses),
                "misses": ", ".join(misses),
                "offsets": dict(Counter(part["offset_h"])),
            }
        )
    return pd.DataFrame(rows, columns=["year", "weeks", "hits", "misses", "offsets"])


def main(argv: Sequence[str] | None = None) -> int:
    from backtester.data.mt5_download import DEFAULT_NAMES
    from backtester.live.connection import session
    from backtester.live.trading_settings import load_trading_settings

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("symbols", nargs="+")
    p.add_argument("--first-year", type=int, default=2018)
    p.add_argument("--zone", default="America/New_York")
    p.add_argument("--shift", type=int, default=7)
    args = p.parse_args(argv)
    clock = ServerClock(args.zone, args.shift)
    settings = load_trading_settings()
    names = {**DEFAULT_NAMES, **{s: n for s, n in settings.symbols.items() if n != s}}
    with session(settings, None) as mt5:
        adapter = Mt5Adapter(mt5, clock, names)
        for symbol in (s.upper() for s in args.symbols):
            raw = adapter.raw_frame(
                symbol,
                Timeframe.H1,
                datetime(args.first_year, 1, 1, tzinfo=UTC),
                datetime.now(UTC),
            )
            days = DEFAULT_SOURCES.cached_days(symbol)
            ref = cached_frame(
                DEFAULT_SOURCES,
                symbol,
                Timeframe.H1,
                max(days[0], date(args.first_year, 1, 1)),
                days[-1],
            )
            weeks = weekly_offsets(raw, ref)
            print(f"\n{symbol}: {len(weeks)} weeks matched, rule {clock.label}")
            report = clock_report(weeks, clock)
            for r in report.itertuples():
                print(f"{r.year}: {r.hits}/{r.weeks} weeks fit  offsets {r.offsets}")
                if r.misses:
                    print(f"   misses: {r.misses}")
            print(f"total {int(report['hits'].sum())}/{int(report['weeks'].sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
