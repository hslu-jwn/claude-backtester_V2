"""Offline V2.6b MT5 repair; run only AFTER the corrected histdata rebuild completes.

    python -m backtester.tools.cache_repair GBPUSD

No terminal, credentials, downloads or raw file changes. Original cached days are
retained under _v26b_original; per-day exclusions are listed under _v26b_reports.
"""

import argparse

from backtester.data.cache import DEFAULT_CACHE_DIR, MT5_CACHE_DIR
from backtester.data.cache_repair import QUALITY, QualityConfig, repair_mt5


def main(argv=None):
    from pathlib import Path

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("symbol")
    p.add_argument("--cache-dir", type=Path, default=MT5_CACHE_DIR)
    p.add_argument("--histdata-dir", type=Path, default=DEFAULT_CACHE_DIR)
    p.add_argument("--min-weekday-share", type=float, default=QUALITY.min_weekday_share)
    args = p.parse_args(argv)
    try:
        decisions = repair_mt5(
            args.symbol,
            args.cache_dir,
            args.histdata_dir,
            QualityConfig(min_weekday_share=args.min_weekday_share),
        )
    except (ValueError, OSError) as exc:
        p.exit(1, f"cache repair: {exc}\n")
    dropped = sum(d["shift"] is None for d in decisions)
    print(f"{args.symbol}: {len(decisions)} measured days, {dropped} excluded; originals retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
