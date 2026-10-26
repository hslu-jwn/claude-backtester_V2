"""Offline V2.6b MT5 repair; run only AFTER the corrected histdata rebuild completes.

    python -m backtester.tools.cache_repair GBPUSD

No terminal, credentials, downloads or raw file changes. Original cached days are
retained under _v26b_original; per-day exclusions are listed under _v26b_reports.
"""

import argparse
import json
import os
import tempfile
from dataclasses import asdict

from backtester.data.cache import DEFAULT_CACHE_DIR, MT5_CACHE_DIR
from backtester.data.cache_repair import (
    QUALITY,
    QualityConfig,
    build_server_clock_table,
    repair_mt5,
)


def main(argv=None):
    from pathlib import Path

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("symbol", nargs="?")
    p.add_argument("--prove-clock", action="store_true")
    p.add_argument("--clock-table", type=Path)
    p.add_argument("--cache-dir", type=Path, default=MT5_CACHE_DIR)
    p.add_argument("--histdata-dir", type=Path, default=DEFAULT_CACHE_DIR)
    p.add_argument("--min-weekday-share", type=float, default=QUALITY.min_weekday_share)
    args = p.parse_args(argv)
    if not args.prove_clock and not args.symbol:
        p.error("symbol required unless --prove-clock is used")
    if args.prove_clock and not args.clock_table:
        p.error("--prove-clock requires --clock-table")
    try:
        config = QualityConfig(min_weekday_share=args.min_weekday_share)
        table = None
        if args.prove_clock:
            table = build_server_clock_table(args.cache_dir, args.histdata_dir, config)
            args.clock_table.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=args.clock_table.parent, delete=False, suffix=".tmp"
            ) as stream:
                temp = Path(stream.name)
                json.dump({"config": asdict(config), "days": table}, stream, indent=2)
            try:
                os.replace(temp, args.clock_table)
            finally:
                temp.unlink(missing_ok=True)
            print(f"Shared server clock: {len(table)} dates; no cache changes")
            return 0
        if args.clock_table:
            payload = json.loads(args.clock_table.read_text(encoding="utf-8"))
            if payload["config"] != json.loads(json.dumps(asdict(config))):
                raise ValueError("clock table quality settings differ from repair settings")
            table = payload["days"]
        decisions = repair_mt5(
            args.symbol,
            args.cache_dir,
            args.histdata_dir,
            config,
            server_table=table,
        )
    except (ValueError, OSError) as exc:
        p.exit(1, f"cache repair: {exc}\n")
    dropped = sum(d["shift"] is None for d in decisions)
    print(f"{args.symbol}: {len(decisions)} measured days, {dropped} excluded; originals retained")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
