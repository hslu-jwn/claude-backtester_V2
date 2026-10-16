"""Trial log by hand: back-fill earlier trials and list the families.

    python -m backtester.tools.trials add gap_fade gap_fade --count 40 --note "old grids"
    python -m backtester.tools.trials add gap_fade gap_fade --trades 900 --mean 0.03 --sd 0.9
    python -m backtester.tools.trials list

`add` writes a count-only line (`--count N`: N trials for the count, no Sharpe) or, with
`--trades`, `--mean` and `--sd`, one line with a Sharpe (mean / sd). `list` shows per family: N,
the number of lines with a Sharpe and their variance V. Spec: risk-management.md > Trial log and
deflated Sharpe (ROADMAP 12.10).
"""

from __future__ import annotations

import argparse
import statistics
from pathlib import Path

from backtester.analytics.trial_log import (
    TrialRecord,
    append,
    count_only,
    family_summary,
    now_iso,
    read_all,
)

MANUAL = "manual"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m backtester.tools.trials", description=__doc__)
    p.add_argument("--log", type=Path, default=None, help="default results/trials.jsonl")
    sub = p.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add", help="add a back-fill line")
    add.add_argument("family")
    add.add_argument("strategy")
    add.add_argument("--count", type=int, default=None, help="count-only: N trials, no stats")
    add.add_argument("--trades", type=int, default=None)
    add.add_argument("--mean", type=float, default=None, help="mean net R per trade")
    add.add_argument("--sd", type=float, default=None, help="sample sd of net R per trade")
    add.add_argument("--note", default="")
    sub.add_parser("list", help="per family: N, lines with a Sharpe, V")
    args = p.parse_args(argv)
    if args.command == "add":
        stats = (args.trades, args.mean, args.sd)
        if args.count is None and None in stats:
            p.error("add needs --count, or --trades with --mean and --sd")
        if args.count is not None and any(x is not None for x in stats):
            p.error("--count cannot be combined with --trades / --mean / --sd")
        if args.count is None and args.sd <= 0:
            p.error("--sd must be > 0")
    return args


def build_record(args: argparse.Namespace) -> TrialRecord:
    if args.count is not None:
        return count_only(args.family, args.strategy, args.count, args.note)
    return TrialRecord(
        args.family, args.strategy, {"note": args.note}, [], MANUAL, MANUAL, MANUAL, now_iso(),
        trades=args.trades, net_r=args.mean * args.trades, mean=args.mean, sd=args.sd,
        sharpe=args.mean / args.sd, note=args.note,
    )  # fmt: skip


def list_text(lines: list[TrialRecord]) -> str:
    if not lines:
        return "no trials logged yet"
    out = []
    for family in dict.fromkeys(r.family for r in lines):
        n, sharpes = family_summary([r for r in lines if r.family == family])
        v = f"{statistics.variance(sharpes):.4g}" if len(sharpes) >= 2 else "-"
        out.append(f"{family}: N={n}, with Sharpe={len(sharpes)}, V={v}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.command == "add":
        append(build_record(args), args.log)
        return 0
    print(list_text(read_all(args.log)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
