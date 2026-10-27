"""Export the demo account's deals for the fill report (V2.4b), read-only.

    .venv/Scripts/python.exe scripts/export_deals.py 2026-10-27T16:00 [--offset-hours 3]

Attaches to the running MT5 terminal's logged-in account (no login from the credential store,
so the demo bot's connection is not switched), reads `history_deals_get(since, now)` and
writes `results/fill_report/deals.csv` through `fill_report.deals_to_csv`. The epoch of MT5 deal
times is server time: pass the server's UTC offset (+3 h until 2026-11-01, then +2 h). Places no
order and changes no setting. Then: `python -m backtester.tools.fill_report --since ... --deals
results/fill_report/deals.csv`.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta

from backtester.live.connection import session
from backtester.live.trading_settings import load_trading_settings
from backtester.paths import RESULTS_DIR
from backtester.tools.fill_report import deals_to_csv


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("since", help="UTC, ISO")
    p.add_argument("--offset-hours", type=float, default=3.0, help="server UTC offset")
    p.add_argument("--out", default=str(RESULTS_DIR / "fill_report" / "deals.csv"))
    args = p.parse_args(argv)
    since = datetime.fromisoformat(args.since).replace(tzinfo=UTC)
    offset = timedelta(hours=args.offset_hours)
    with session(load_trading_settings(), None) as mt5:
        # history_deals_get takes server-time datetimes; ask a margin wider than the offset
        deals = mt5.history_deals_get(since + offset - timedelta(hours=1), datetime.now(UTC) + offset
                                      + timedelta(hours=1)) or ()  # fmt: skip
    text = deals_to_csv(deals, args.out, int(offset.total_seconds()))
    print(f"{text.count(chr(10)) - 1} deals -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
