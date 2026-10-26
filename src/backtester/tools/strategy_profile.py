"""Profile default strategies on development data. Spec: strategy-profile.md."""

import argparse
import json
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

from backtester.analytics.profile import calculate, markdown
from backtester.analytics.records import read_trades
from backtester.analytics.trial_log import append, make_record
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings
from backtester.strategy.registry import REGISTRY
from backtester.tools.entry_screen import DEV_END, START, STRATEGY_SYMBOLS, parse_sets
from backtester.tools.research import run_period


def write(result, folder):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "profile.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    (folder / "profile.md").write_text("\n".join(markdown(result)) + "\n", encoding="utf-8")


def research_results(folder, results_dir, info, tests, start, end, sources):
    """Profile saved selected runs only; no strategy execution or trial-log mutation."""
    chosen = info.get("chosen")
    info["profiles"] = {}
    if chosen is not None:
        records = [("development", folder / "variants" / chosen["id"], start, end)]
        records += [
            (
                f"test {r['test_run']}",
                results_dir / r["run_folder"],
                date.fromisoformat(r["start"]),
                date.fromisoformat(r["end"]),
            )
            for r in tests
        ]
        for label, target, a, b in records:
            result = calculate(read_trades(target), a, b, sources)
            write(result, target)
            if label == "development":
                write(result, results_dir / chosen["dev_run"])
            info["profiles"][label] = result
    (folder / "profile.json").write_text(
        json.dumps(info["profiles"], indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    modes = p.add_mutually_exclusive_group(required=True)
    modes.add_argument("--strategy", choices=tuple(REGISTRY))
    modes.add_argument("--all", action="store_true")
    p.add_argument("--symbols", nargs="+")
    p.add_argument("--start", type=date.fromisoformat, default=START)
    p.add_argument("--end", type=date.fromisoformat, default=DEV_END)
    p.add_argument("--allow-test-period", action="store_true")
    p.add_argument("--set", dest="sets", action="append", default=[])
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--cache-dir", type=Path)
    p.add_argument("--out", type=Path, default=RESULTS_DIR / "profiles")
    args = p.parse_args(argv)
    if args.end < args.start:
        p.error("end must be >= start")
    if args.workers < 1:
        p.error("workers must be positive")
    if args.end > DEV_END and not args.allow_test_period:
        raise SystemExit(
            f"end after {DEV_END}: untouched test period; requires --allow-test-period"
        )
    return args


def main(argv=None):
    args = parse_args(argv)
    names = list(REGISTRY) if args.all else [args.strategy]
    # Validate every config before starting --all, avoiding partially executed invalid jobs.
    jobs = []
    for name in names:
        cls = REGISTRY[name].config_cls
        overrides = parse_sets(args.sets, cls)
        if len(overrides) != 1:
            raise SystemExit("profile --set takes one value per field, not a sweep")
        jobs.append((name, replace(cls(), **overrides[0])))
    for name, config in jobs:
        symbols = [s.upper() for s in (args.symbols or STRATEGY_SYMBOLS[name])]
        sources = (
            DEFAULT_SOURCES
            if args.cache_dir is None
            else SymbolSources.single(args.cache_dir, symbols)
        )
        print(f"Profiling {name}: {symbols}, {args.start}..{args.end}", flush=True)
        # run_period splits the range at cache gaps (e.g. a closed 1 January), like research
        run = run_period(
            symbols,
            args.start,
            args.end,
            replace(RunSettings(), strategy=config),
            sources=sources,
            workers=args.workers,
        )
        result = calculate(run.trades, args.start, args.end, sources)
        result.update(strategy=name, symbols=symbols)
        out = args.out / f"{name}_{datetime.now(UTC):%Y%m%dT%H%M%S%fZ}"
        write(result, out)
        append(
            make_record(
                name + "-profile",
                name,
                config,
                symbols,
                args.start,
                args.end,
                "development" if args.end <= DEV_END else "test",
                run.trades,
                "strategy condition profile",
            )
        )
        print("\n".join(markdown(result)), flush=True)
        print(f"Written to {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
