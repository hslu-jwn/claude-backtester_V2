"""Matched monkeys for any registry strategy. Spec: risk-management.md > Matched monkeys.

python -m backtester.tools.monkeys --strategy trend_following --symbols XAUUSD --runs 200
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

from backtester.analytics.monkeys import MonkeyConfig, markdown, matched_monkeys
from backtester.analytics.trial_log import append, make_record
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.engine.spread_table import SpreadTable
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings
from backtester.strategy.registry import REGISTRY
from backtester.tools.entry_screen import DEV_END, START, STRATEGY_SYMBOLS, load_m1, parse_sets
from backtester.tools.research import run_period


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--strategy", required=True, choices=tuple(REGISTRY))
    p.add_argument("--symbols", nargs="+")
    p.add_argument("--start", type=date.fromisoformat, default=START)
    p.add_argument("--end", type=date.fromisoformat, default=DEV_END)
    p.add_argument("--allow-test-period", action="store_true")
    p.add_argument("--runs", type=int, default=MonkeyConfig().runs)
    p.add_argument("--seed", type=int, default=MonkeyConfig().seed)
    p.add_argument("--set", dest="sets", action="append", default=[])
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--cache-dir", type=Path)
    p.add_argument("--spread-table", type=Path)
    p.add_argument("--out", type=Path, default=RESULTS_DIR / "monkeys")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.end > DEV_END and not args.allow_test_period:
        raise SystemExit(f"end after {DEV_END}: untouched test period; use --allow-test-period")
    if args.start > args.end:
        raise SystemExit("start must be <= end")
    cfg = MonkeyConfig(runs=args.runs, seed=args.seed)
    spec = REGISTRY[args.strategy]
    overrides = parse_sets(args.sets, spec.config_cls)
    symbols = [s.upper() for s in (args.symbols or STRATEGY_SYMBOLS[args.strategy])]
    sources = (
        DEFAULT_SOURCES if args.cache_dir is None else SymbolSources.single(args.cache_dir, symbols)
    )
    engine = RunSettings().engine
    if args.spread_table:
        table = SpreadTable.from_dict(json.loads(args.spread_table.read_text(encoding="utf-8")))
        engine = replace(engine, costs=replace(engine.costs, spread_table=table))
    out = args.out / f"{args.strategy}_{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}"
    out.mkdir(parents=True, exist_ok=True)
    print(f"{args.strategy} {symbols} {args.start}..{args.end}, {cfg.runs} runs", flush=True)
    m1s = {s: load_m1(s, sources, args.start, args.end) for s in symbols}
    summary = {
        "strategy": args.strategy,
        "symbols": symbols,
        "start": str(args.start),
        "end": str(args.end),
        "variants": [],
    }
    lines = [f"# Matched monkeys: {args.strategy}", "", f"{args.start}..{args.end}; {symbols}"]
    for ov in overrides:
        settings = replace(RunSettings(), strategy=replace(spec.config_cls(), **ov), engine=engine)
        result = run_period(symbols, args.start, args.end, settings, sources, args.workers)
        append(
            make_record(
                "monkeys_" + args.strategy,
                args.strategy,
                settings.strategy,
                symbols,
                args.start,
                args.end,
                "histdata",
                result.trades,
                "matched monkeys (T-14)",
            )
        )
        print(f"{ov or 'default'}: {len(result.trades)} source trades", flush=True)
        tested = matched_monkeys(result.trades, m1s, engine.costs, cfg)
        summary["variants"].append(dict(overrides=ov, **tested))
        lines += ["", f"Variant: {ov or 'default'}", *markdown(tested)]
        (out / "summary.json").write_text(
            json.dumps(summary, indent=2, default=str), encoding="utf-8"
        )
        (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines), flush=True)
    print(f"written to {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
