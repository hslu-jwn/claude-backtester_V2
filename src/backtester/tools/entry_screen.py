"""Entry screening battery on a strategy's default backtest (ROADMAP 12.12, idea T-13).

    python -m backtester.tools.entry_screen --strategy gap_momentum --cache-dir <histdata cache>
    python -m backtester.tools.entry_screen --strategy opening_range --set stop_atr=0.5,1 ...

Runs the registry strategy's backtest (spec defaults, `--set key=value` overrides one config
field; a comma list sweeps it, several `--set` make the product) on its own symbols over the
development period (2015-01-01 to 2021-09-13; an end after the data split cut-off is refused
unless `--allow-test-period`), then the battery of `analytics/entry_screen.py` on the M1 candles
of the same cache. Written to `<out>/<strategy>/` (default results/entry_screen): `cells.csv`
(one row per N x variant), `tests.csv` (1R/1R, random exits, per variant), `hit_scan.csv`,
`summary.json` and `summary.txt` (PASS / FAIL with the reasons). One trial-log line per variant
(family screen_<strategy>). Reads data only; `--cache-dir` reads every symbol from that folder.
Spec: risk-management.md > Entry screening.
"""

from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import fields, replace
from datetime import UTC, date, datetime, time, timedelta
from enum import Enum
from pathlib import Path
from typing import get_args, get_type_hints

import numpy as np

from backtester.analytics.entry_screen import (
    EntryScreenConfig,
    M1Data,
    ScreenTrade,
    VariantScreen,
    judge,
    screen_variant,
)
from backtester.analytics.trial_log import append, make_record
from backtester.core.models import Timeframe
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.engine.spread_table import SpreadTable
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.registry import REGISTRY, make_strategy
from backtester.tools.research_helpers import write_csv

START = date(2015, 1, 1)
DEV_END = date(2021, 9, 13)  # the day before the data split cut-off 2021-09-14
_FIVE = ("XAUUSD", "GBPUSD", "GBPJPY", "NAS100", "US500")
STRATEGY_SYMBOLS = {  # each strategy's own symbols (its spec / grid tool)
    "session_zone_sweep": ("XAUUSD", "GBPUSD", "GBPJPY"),
    "ny_index_sweep": ("NAS100", "US500"),
    "no_wick": _FIVE,
    "trend_following": _FIVE,
    "gap_fade": ("NAS100", "US500"),
    "opening_range": ("NAS100", "US500"),
    "gap_momentum": ("NAS100", "US500"),
    "london_fix": ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD"),
}
FAMILY_PREFIX = "screen_"
SOURCE = "histdata"
NOTE = "entry screen (T-13)"


# --- --set key=value ---------------------------------------------------------------------------------


def _parse_value(text: str, kind: type):
    if kind is bool:
        if text.lower() not in ("true", "false", "1", "0"):
            raise SystemExit(f"{text!r} is not a boolean")
        return text.lower() in ("true", "1")
    if kind is int:
        return int(text)
    if kind is float:
        return float(text)
    if kind is time:
        return time.fromisoformat(text)
    if isinstance(kind, type) and issubclass(kind, Enum):
        for member in kind:
            if text in (member.name, str(member.value), member.name.lower()):
                return member
        raise SystemExit(f"{text!r} is not a {kind.__name__}")
    if kind is str:
        return text
    raise SystemExit(f"--set cannot set a field of type {kind}")


def _field_type(config_cls: type, name: str) -> type:
    """The field's type, without `| None`."""
    hint = get_type_hints(config_cls)[name]
    args = [a for a in get_args(hint) if a is not type(None)]
    return args[0] if args else hint


def parse_sets(items: list[str], config_cls: type) -> list[dict]:
    """`key=value` (or `key=v1,v2`) items as override dicts, one per combination."""
    names = {f.name for f in fields(config_cls)}
    choices: list[tuple[str, list]] = []
    for item in items:
        if "=" not in item:
            raise SystemExit(f"--set {item!r}: expected key=value")
        key, _, raw = item.partition("=")
        if key not in names:
            raise SystemExit(f"--set {key}: {config_cls.__name__} has no such field")
        kind = _field_type(config_cls, key)
        choices.append((key, [_parse_value(v, kind) for v in raw.split(",")]))
    if not choices:
        return [{}]
    keys = [k for k, _ in choices]
    combos = itertools.product(*(v for _, v in choices))
    return [dict(zip(keys, combo, strict=True)) for combo in combos]


def variant_label(overrides: dict) -> str:
    if not overrides:
        return "default"
    return " ".join(
        f"{k}={v:%H:%M}" if isinstance(v, time) else f"{k}={v}" for k, v in overrides.items()
    )


# --- data -----------------------------------------------------------------------------------------------


def _midnight(day: date) -> datetime:
    return datetime.combine(day, time(), UTC)


def _blocks(days: list[date]) -> list[tuple[date, date]]:
    out: list[tuple[date, date]] = []
    for d in days:
        if out and d - out[-1][1] == timedelta(days=1):
            out[-1] = (out[-1][0], d)
        else:
            out.append((d, d))
    return out


def load_m1(symbol: str, sources: SymbolSources, start: date, end: date) -> M1Data:
    """M1 candles of the cached days in [start, end] (a missing day is simply absent)."""
    days = sorted(d for d in sources.cached_days(symbol) if start <= d <= end)
    if not days:
        raise SystemExit(f"{symbol}: no cached day between {start} and {end}")
    adapter = sources.adapter(symbol)
    parts = []
    for first, last in _blocks(days):
        frame = adapter.fetch_frame(
            symbol, Timeframe.M1, _midnight(first), _midnight(last + timedelta(days=1))
        )
        if len(frame):
            parts.append(M1Data.from_frame(frame))
    if not parts:
        raise SystemExit(f"{symbol}: the cached days between {start} and {end} are empty")
    return M1Data(*(np.concatenate([getattr(p, f) for p in parts]) for f in
                    ("open_s", "open", "high", "low", "close")))  # fmt: skip


# --- output ---------------------------------------------------------------------------------------------


def summary_rows(v: VariantScreen) -> list[dict]:
    b, r = v.bracket, v.random
    rows = [{"variant": v.label, "test": "bracket_1R1R", "metric": k, "value": val}
            for k, val in b.items()]  # fmt: skip
    rows += [{"variant": v.label, "test": "random_exit", "metric": k, "value": getattr(r, k)}
             for k in r.__slots__]  # fmt: skip
    return rows


def summary_text(strategy: str, header: dict, variants: list[VariantScreen], verdict) -> str:
    lines = [
        f"entry screen {strategy}: {'PASS' if verdict.passed else 'FAIL'}",
        f"  symbols {header['symbols']}, {header['period']}, bar {header['bar_minutes']} min",
        (
            f"  cells with mean net R > 0: {verdict.cells_positive}/{verdict.cells} "
            f"({verdict.cell_share:.1%}, needs >= {header['config']['min_cell_share']:.0%})"
        ),
        (
            f"  1R/1R win rate: {verdict.bracket_win_rate:.2%} "
            f"(needs >= {header['config']['min_bracket_win_rate']:.0%})"
        ),
        (
            f"  percentile vs random-time exits: {verdict.random_percentile:.1f} "
            f"(needs > {header['config']['random_percentile']:g})"
        ),
    ]
    lines += [f"  reason: {why}" for why in verdict.reasons]
    for v in variants:
        r = v.random
        lines.append(f"  [{v.label}] {v.trades} trades ({v.skipped} skipped), mean hold "
                     f"{r.mean_hold_s / 60:.0f} min, own net {r.strategy_net:+.1f} R, random-time "
                     f"median {r.median:+.1f} R, reversed random median {r.rev_median:+.1f} R")  # fmt: skip
        for c in v.cells:
            net = "-" if c["mean_net"] is None else f"{c['mean_net']:+.3f}"
            rev = "-" if c["rev_mean_net"] is None else f"{c['rev_mean_net']:+.3f}"
            lines.append(f"    N={c['bars']:<3} net {net}  reversed net {rev}")
        b = v.bracket
        lines.append(f"    1R/1R: wins {b['wins']} losses {b['losses']} open {b['unresolved']}, "
                     f"win rate {b['win_rate']:.2%}, reversed {b['rev_win_rate']:.2%}")  # fmt: skip
        for h in v.hit_rows:
            lines.append(f"    hit N={h['bars']:<3} real {h['real_hit_rate']:.3f} vs shuffled "
                         f"{h['shuffled_mean']:.3f} +- {h['shuffled_sd']:.3f} (z {h['z']:+.1f})")  # fmt: skip
    return "\n".join(lines) + "\n"


# --- main -----------------------------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--strategy", required=True, choices=tuple(REGISTRY))
    p.add_argument("--symbols", nargs="+", default=None, help="default: the strategy's own")
    p.add_argument("--start", type=date.fromisoformat, default=START)
    p.add_argument("--end", type=date.fromisoformat, default=DEV_END,
                   help=f"default {DEV_END} (development period)")  # fmt: skip
    p.add_argument("--allow-test-period", action="store_true",
                   help=f"allow an end after {DEV_END} (the untouched test period)")  # fmt: skip
    p.add_argument("--set", dest="sets", action="append", default=[], metavar="KEY=VALUE",
                   help="override a strategy config field; v1,v2 sweeps it")  # fmt: skip
    p.add_argument("--cache-dir", type=Path, default=None,
                   help="read every symbol from this cache folder (default: the app's sources)")  # fmt: skip
    p.add_argument("--spread-table", type=Path, default=None,
                   help="spread by year and hour JSON; without the flag: fixed spread")  # fmt: skip
    p.add_argument("--random-runs", type=int, default=EntryScreenConfig().random_runs)
    p.add_argument("--shuffle-runs", type=int, default=EntryScreenConfig().shuffle_runs)
    p.add_argument("--workers", type=int, default=None,
                   help="processes of the backtest (default: one per symbol)")  # fmt: skip
    p.add_argument("--out", type=Path, default=None,
                   help="default results/entry_screen (files go to <out>/<strategy>/)")  # fmt: skip
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.end > DEV_END and not args.allow_test_period:
        raise SystemExit(
            f"end {args.end} is after {DEV_END}: that is the untouched test period "
            "(use --allow-test-period for the one test run with the variants fixed in advance)"
        )
    spec = REGISTRY[args.strategy]
    symbols = [s.upper() for s in (args.symbols or STRATEGY_SYMBOLS[args.strategy])]
    overrides = parse_sets(args.sets, spec.config_cls)
    sources = (
        DEFAULT_SOURCES if args.cache_dir is None else SymbolSources.single(args.cache_dir, symbols)
    )
    engine = RunSettings().engine
    if args.spread_table is not None:
        table = SpreadTable.from_dict(json.loads(args.spread_table.read_text(encoding="utf-8")))
        engine = replace(engine, costs=replace(engine.costs, spread_table=table))
    config = replace(EntryScreenConfig(), random_runs=args.random_runs,
                     shuffle_runs=args.shuffle_runs)  # fmt: skip
    out = (args.out or RESULTS_DIR / "entry_screen") / args.strategy
    out.mkdir(parents=True, exist_ok=True)
    print(f"{args.strategy} {symbols} {args.start}..{args.end}, {len(overrides)} variant(s)",
          flush=True)  # fmt: skip
    m1s = {s: load_m1(s, sources, args.start, args.end) for s in symbols}
    screens, cells, tests, hits = [], [], [], []
    bar_minutes = 0
    for ov in overrides:
        label = variant_label(ov)
        strategy_config = replace(spec.config_cls(), **ov)
        result = run_backtests(
            symbols, args.start, args.end,
            replace(RunSettings(), strategy=strategy_config, engine=engine),
            sources=sources, workers=args.workers,
        )  # fmt: skip
        bar_minutes = make_strategy(symbols[0], strategy_config).base_timeframe.value
        print(f"[{label}] {len(result.trades)} trades, bar {bar_minutes} min", flush=True)
        append(make_record(
            FAMILY_PREFIX + args.strategy, args.strategy, strategy_config, symbols, args.start,
            args.end, SOURCE, result.trades, NOTE,
        ))  # fmt: skip
        trades = [ScreenTrade.from_trade(t) for t in result.trades]
        screen = screen_variant(
            trades,
            m1s,
            bar_minutes,
            engine.costs,
            config,
            label,
            (args.start, args.end),
            workers=args.workers,
        )
        screens.append(screen)
        cells += [{"variant": label, **c} for c in screen.cells]
        tests += summary_rows(screen)
        hits += [{"variant": label, **h} for h in screen.hit_rows]
        write_csv(out / "cells.csv", cells)
        write_csv(out / "tests.csv", tests)
        write_csv(out / "hit_scan.csv", hits)
    verdict = judge(screens, config)
    header = {
        "symbols": symbols, "period": f"{args.start}..{args.end}", "bar_minutes": bar_minutes,
        "config": {f.name: getattr(config, f.name) for f in fields(config)},
    }  # fmt: skip
    summary = {
        "strategy": args.strategy, **header, "cache_dir": str(args.cache_dir),
        "verdict": {"passed": verdict.passed, "reasons": list(verdict.reasons),
                    "cells": verdict.cells, "cells_positive": verdict.cells_positive,
                    "cell_share": verdict.cell_share,
                    "bracket_win_rate": verdict.bracket_win_rate,
                    "random_percentile": verdict.random_percentile},
        "variants": [
            {"label": v.label, "trades": v.trades, "skipped": v.skipped,
             "by_symbol": v.n_trades_by_symbol, "bracket": v.bracket,
             "random": {k: getattr(v.random, k) for k in v.random.__slots__},
             "cells": v.cells, "hit_rows": v.hit_rows}
            for v in screens
        ],
    }  # fmt: skip
    (out / "summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    text = summary_text(args.strategy, header, screens, verdict)
    (out / "summary.txt").write_text(text, encoding="utf-8")
    print(text)
    print(f"written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
