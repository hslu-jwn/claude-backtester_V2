"""Run strategy 6 (opening-range breakout) over its sweep and compare the results.

    python -m backtester.tools.archive.orb_grid --start 2015-01-01 --end 2021-09-13 --first-half-end-year 2018
    python -m backtester.tools.archive.orb_grid --source mt5 --volume --no-filters --symbols EURUSD US30
    python -m backtester.tools.archive.orb_grid --no-sweep --spread-table

Variants (spec: strategy-opening-range.md > Entry, Filters): the base grid is entry_mode `range`
with range_minutes 5 / 15 / 30 and `band` with band_atr 0.25 / 0.5 / 1.0, each x target_r 0 / 1 / 2
(18); the filter variants (unless `--no-filters`) change one setting of the spec default entry
(range 15, target 0): max_range_atr 0.15 / 0.3, narrow_day_filter nr4 / inside, max_reversals 1
(5); with `--volume` the 18 base variants are also run with min_rel_volume 1.5 (needs the volume
of FTMO's MT5 cache, `--source mt5`) and `<out>/ab_volume.csv` compares each with its twin.
`--no-sweep` runs only the spec default.

Written to `<out>/summary.csv` (variant x symbol group, ALL and by symbol), `split.csv` (the two
halves, split after `--first-half-end-year`), `robustness.csv` (net without the best trade,
costs x 1.5, halves, shock days), `grid.csv` (share of profitable variants per family) and
`classes.csv` (the same per market class: US indices, EU/UK/JP indices, FX London, FX New York,
Metals London, Metals NY). Default `<out>` is results/orb/fixed, or results/orb/table with
`--spread-table` (`orb_mt5/` with `--source mt5`). Net R includes the swap. Research only: it
changes no setting. ROADMAP 11.10.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Sequence
from dataclasses import replace
from datetime import date
from pathlib import Path

from backtester.analytics.metrics import summarize
from backtester.analytics.robustness import RobustnessConfig, trade_robustness
from backtester.data.cache import MT5_CACHE_DIR
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.engine.spread_table import SpreadTable
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings
from backtester.strategy.opening_range.config import EntryMode, NarrowDay, OpeningRangeConfig
from backtester.tools.archive.trend_grid import (
    grid_rows,
    load_shocks,
    print_grid,
    robustness_row,
    sum_ex_swap,
    summary_net,
    summary_row,
    swap_rates_note,
    write_csv,
)
from backtester.tools.grid_common import run_variant
from backtester.tools.research import segments  # noqa: F401  (kept importable from here)

SYMBOLS = (
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURJPY", "GBPJPY",
    "EURGBP", "XAUUSD", "XAGUSD", "NAS100", "US500", "GER40", "UK100", "JP225", "EU50",
)  # fmt: skip
START = date(2015, 1, 1)
RANGE_MINUTES = (5, 15, 30)
BAND_ATRS = (0.25, 0.5, 1.0)
TARGETS = (0.0, 1.0, 2.0)
MAX_RANGE_ATRS = (0.15, 0.3)
NARROW_DAYS = (NarrowDay.NR4, NarrowDay.INSIDE)
REVERSALS = 1
MIN_REL_VOLUME = 1.5
DEFAULT_SPREAD_TABLE = Path("data") / "spreads" / "ftmo_spread_median.json"
WORKERS = 1  # the process pool stalled on the long 1-minute runs; in-process is reliable

INDEX_CLASSES = {
    **dict.fromkeys(("NAS100", "US500", "US30", "US2000"), "US indices"),
    **dict.fromkeys(("GER40", "EU50", "UK100", "JP225"), "EU/UK/JP indices"),
}
METALS = ("XAUUSD", "XAGUSD")
SESSION_LABEL = {"london": "London", "new_york": "NY"}
FX_LABEL = {"london": "FX London", "new_york": "FX New York"}
CLASSES = (
    "US indices", "EU/UK/JP indices", "FX London", "FX New York", "Metals London", "Metals NY",
)  # fmt: skip


def variants(
    sweep: bool = True, volume: bool = False, filters: bool = True
) -> list[OpeningRangeConfig]:
    """Base grid, then the filter variants, then (with `volume`) the base grid with volume."""
    if not sweep:
        return [OpeningRangeConfig()]
    base = [
        OpeningRangeConfig(entry_mode=EntryMode.RANGE, range_minutes=m, target_r=t)
        for t in TARGETS
        for m in RANGE_MINUTES
    ] + [
        OpeningRangeConfig(entry_mode=EntryMode.BAND, band_atr=b, target_r=t)
        for t in TARGETS
        for b in BAND_ATRS
    ]
    out = list(base)
    if filters:
        out += [OpeningRangeConfig(max_range_atr=x) for x in MAX_RANGE_ATRS]
        out += [OpeningRangeConfig(narrow_day_filter=n) for n in NARROW_DAYS]
        out += [OpeningRangeConfig(max_reversals=REVERSALS)]
    if volume:
        out += [replace(c, min_rel_volume=MIN_REL_VOLUME) for c in base]
    return out


def variant_name(config: OpeningRangeConfig) -> str:
    if config.entry_mode is EntryMode.RANGE:
        name = f"range {config.range_minutes}m T{config.target_r:g}"
    else:
        name = f"band {config.band_atr:g}atr T{config.target_r:g}"
    if config.max_range_atr:
        name += f" maxrange{config.max_range_atr:g}"
    if config.narrow_day_filter is not NarrowDay.OFF:
        name += f" {config.narrow_day_filter.value}"
    if config.max_reversals:
        name += f" reversal{config.max_reversals}"
    if config.min_rel_volume:
        name += f" vol{config.min_rel_volume:g}"
    return name


def family_key(config: OpeningRangeConfig) -> tuple[str, float]:
    """(family, order): the variants that differ only in range_minutes / band_atr share a
    family (mode, target, volume) and are ordered by it; filter variants form one family."""
    base = OpeningRangeConfig()
    if (
        config.max_range_atr != base.max_range_atr
        or config.narrow_day_filter is not base.narrow_day_filter
        or config.max_reversals != base.max_reversals
    ):
        return "filters", 0
    suffix = f" vol{config.min_rel_volume:g}" if config.min_rel_volume else ""
    if config.entry_mode is EntryMode.RANGE:
        return f"range T{config.target_r:g}{suffix}", config.range_minutes
    return f"band T{config.target_r:g}{suffix}", config.band_atr


def trade_session(trade) -> str | None:
    """The session name (london, new_york, ...) the strategy put at the end of `reason`."""
    reason = getattr(trade, "reason", "") or ""
    return reason.rsplit(" ", 1)[-1] if reason.startswith("opening range") else None


def market_class(symbol: str, session: str | None) -> str | None:
    if symbol in INDEX_CLASSES:
        return INDEX_CLASSES[symbol]
    if session not in SESSION_LABEL:
        return None
    if symbol in METALS:
        return f"Metals {SESSION_LABEL[session]}"
    return FX_LABEL[session] if symbol in SYMBOLS else None


def half_labels(start: date, end: date, first_half_end_year: int) -> tuple[str, str]:
    return f"{start.year}-{first_half_end_year}", f"{first_half_end_year + 1}-{end.year}"


def split_trades(trades: Sequence, first_half_end_year: int) -> tuple[list, list]:
    return (
        [t for t in trades if t.entry_time.year <= first_half_end_year],
        [t for t in trades if t.entry_time.year > first_half_end_year],
    )


def half_rows(
    variant: str, group: str, trades: Sequence, labels, first_half_end_year
) -> list[dict]:
    rows = []
    for half, part in zip(labels, split_trades(trades, first_half_end_year), strict=True):
        s = summarize(part)
        rows.append(
            {
                "variant": variant, "symbol": group, "half": half, "trades": s["trades"],
                "sum_r_gross": s["net_r_gross"], "sum_r_net": s["net_r_net"],
                "sum_r_ex_swap": sum_ex_swap(part),
            }
        )  # fmt: skip
    return rows


def class_row(variant: str, market: str, trades: Sequence, rcfg: RobustnessConfig) -> dict:
    s = summary_row(variant, market, trades)
    rob = trade_robustness(trades, rcfg)
    return {
        "variant": variant,
        "market_class": market,
        "trades": s["trades"],
        "sum_r_gross": s["sum_r_gross"],
        "sum_r_net": s["sum_r_net"],
        "net_r_per_trade": s["avg_r_net"],
        "half_first_net_r": rob["half_first_net_r"],
        "half_second_net_r": rob["half_second_net_r"],
        "net_r_without_best": rob["net_r_without_best"],
        "net_r_stressed": rob["net_r_stressed"],
    }


def volume_pairs(summary: Sequence[dict]) -> list[dict]:
    """Each base variant with its `... vol<x>` twin (ALL rows): net R per trade of both."""
    all_rows = {r["variant"]: r for r in summary if r["symbol"] == "ALL"}
    pairs = []
    for name, row in all_rows.items():
        twin = next(
            (r for n, r in all_rows.items() if n.startswith(name + " vol") and n.count(" ") ==
             name.count(" ") + 1),
            None,
        )  # fmt: skip
        if twin is None or not row["trades"] or not twin["trades"]:
            continue
        a = row["sum_r_net"] / row["trades"]
        b = twin["sum_r_net"] / twin["trades"]
        pairs.append(
            {
                "variant": name, "trades": row["trades"], "trades_vol": twin["trades"],
                "net_r": row["sum_r_net"], "net_r_vol": twin["sum_r_net"],
                "net_per_trade": a, "net_per_trade_vol": b,
                "delta_net_per_trade": b - a, "improved": b > a,
            }
        )  # fmt: skip
    return pairs


def _part(text: str) -> tuple[int, int]:
    k, n = (int(x) for x in text.split("/"))
    if not 1 <= k <= n:
        raise argparse.ArgumentTypeError("--part must be K/N with 1 <= K <= N")
    return k, n


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, default=START)
    p.add_argument("--end", type=date.fromisoformat, default=None,
                   help="default: the last cached day")  # fmt: skip
    p.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    p.add_argument("--no-sweep", action="store_true", help="only the spec's default parameters")
    p.add_argument("--no-filters", action="store_true", help="skip the 5 filter variants")
    p.add_argument("--volume", action="store_true",
                   help="also the 18 base variants with min_rel_volume 1.5 (MT5 data)")  # fmt: skip
    p.add_argument("--variants", nargs="+", default=None, metavar="NAME",
                   help="run only these variants, named as the grid prints them (quote each, "
                   "e.g. \"band 0.25atr T0 vol1.5\"); replaces the sweep flags")  # fmt: skip
    p.add_argument("--first-half-end-year", type=int,
                   default=RobustnessConfig().first_half_end_year,
                   help="last entry year of the first half (halves are split after it)")  # fmt: skip
    p.add_argument("--spread-table", nargs="?", type=Path, const=DEFAULT_SPREAD_TABLE, default=None,
                   help=f"spread by year and hour JSON (default file {DEFAULT_SPREAD_TABLE}); "
                   "without the flag: fixed spread")  # fmt: skip
    p.add_argument("--no-shocks", action="store_true",
                   help="do not read the daily bars for the shock days")  # fmt: skip
    p.add_argument("--source", choices=("histdata", "mt5"), default="histdata",
                   help="candle cache: histdata (default) or FTMO's data/cache/mt5")  # fmt: skip
    p.add_argument("--workers", type=int, default=WORKERS,
                   help="processes per backtest (1 = in this process)")  # fmt: skip
    p.add_argument("--part", type=_part, default=None, metavar="K/N",
                   help="run only the variants K, K+N, ... (1-based) so N processes can split "
                   "the sweep; combine them with --merge")  # fmt: skip
    p.add_argument("--merge", nargs="+", type=Path, default=None, metavar="DIR",
                   help="no backtest: join the CSVs of these --part output folders into --out "
                   "and rebuild grid.csv and ab_volume.csv")  # fmt: skip
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args(argv)
    if args.variants:
        valid = [variant_name(c) for c in variants(True, True, True)]
        unknown = [v for v in args.variants if v not in valid]
        if unknown:
            p.error(f"unknown variant(s) {unknown}; valid names: {valid}")
    return args


def last_cached_day(symbols: list[str], sources: SymbolSources = DEFAULT_SOURCES) -> date:
    return max(max(sources.cached_days(s)) for s in symbols)


def finish(out: Path, summary: list[dict], entries: list, volume: bool, rcfg) -> None:
    """grid.csv, ab_volume.csv and the printed tables from the summary rows."""
    grid = grid_rows(entries, rcfg)
    write_csv(out / "grid.csv", grid)
    pairs = volume_pairs(summary) if volume else []
    if volume:
        write_csv(out / "ab_volume.csv", pairs)
    print(f"\n{'variant':34}{'trades':>7}{'gross':>9}{'net':>9}{'net/tr':>8}")
    for r in summary:
        if r["symbol"] == "ALL":
            per = "-" if r["net_r_per_trade"] is None else f"{r['net_r_per_trade']:+.3f}"
            print(
                f"{r['variant']:34}{r['trades']:>7}{r['sum_r_gross']:>+9.1f}"
                f"{r['sum_r_net']:>+9.1f}{per:>8}"
            )
    print_grid(grid)
    if pairs:
        better = sum(p["improved"] for p in pairs)
        mean = sum(p["delta_net_per_trade"] for p in pairs) / len(pairs)
        print(f"volume filter: {better}/{len(pairs)} pairs improve, mean {mean:+.4f} R per trade")


def _number(text: str):
    if text == "":
        return None
    for kind in (int, float):
        try:
            return kind(text)
        except ValueError:
            pass
    return {"True": True, "False": False}.get(text, text)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return [{k: _number(v) for k, v in row.items()} for row in csv.DictReader(f)]


def merge(dirs: Sequence[Path], out: Path, rcfg: RobustnessConfig) -> int:
    """Join the per-variant CSVs of `--part` runs and rebuild the cross-variant files."""
    out.mkdir(parents=True, exist_ok=True)
    rows = {
        name: [r for d in dirs for r in read_csv(d / name)]
        for name in ("summary.csv", "split.csv", "robustness.csv", "classes.csv")
    }
    for name, items in rows.items():
        write_csv(out / name, items)
    by_name = {variant_name(c): c for c in variants(True, True, True)}
    entries = [
        (*family_key(by_name[r["variant"]]), r["variant"], r["sum_r_net"])
        for r in rows["summary.csv"]
        if r["symbol"] == "ALL"
    ]
    volume = any(by_name[r["variant"]].min_rel_volume for r in rows["summary.csv"])
    finish(out, rows["summary.csv"], entries, volume, rcfg)
    print(f"merged {len(dirs)} folders into {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.merge:
        folder = "orb" if args.source == "histdata" else f"orb_{args.source}"
        return merge(
            args.merge,
            args.out or RESULTS_DIR / folder / "merged",
            RobustnessConfig(first_half_end_year=args.first_half_end_year),
        )
    if args.variants:
        by_name = {variant_name(c): c for c in variants(True, True, True)}
        configs = [by_name[v] for v in args.variants]
    else:
        configs = variants(not args.no_sweep, args.volume, not args.no_filters)
    if args.part:
        k, n = args.part
        configs = configs[k - 1 :: n]
    symbols = [s.upper() for s in args.symbols]
    sources = (
        DEFAULT_SOURCES
        if args.source == "histdata"
        else SymbolSources.single(MT5_CACHE_DIR, symbols)
    )
    end = args.end or last_cached_day(symbols, sources)
    engine = RunSettings().engine
    if args.spread_table is not None:
        table = SpreadTable.from_dict(json.loads(args.spread_table.read_text(encoding="utf-8")))
        engine = replace(engine, costs=replace(engine.costs, spread_table=table))
        print(f"spread table: {table.stat} by year and New York hour, {table.note}")
    mode = "fixed" if args.spread_table is None else "table"
    folder = "orb" if args.source == "histdata" else f"orb_{args.source}"
    out = args.out or RESULTS_DIR / folder / mode
    out.mkdir(parents=True, exist_ok=True)
    year = args.first_half_end_year
    rcfg = RobustnessConfig(first_half_end_year=year)
    labels = half_labels(args.start, end, year)
    shocks, shock_note = (
        ({}, "") if args.no_shocks else load_shocks(symbols, args.start, end, rcfg, sources)
    )
    summary, split, robust, classes, entries = [], [], [], [], []
    for config in configs:
        name = variant_name(config)
        result = run_variant(
            symbols,
            args.start,
            end,
            replace(RunSettings(), strategy=config, engine=engine),
            sources,
            args.workers,
        )
        print(f"{name}: {len(result.trades)} trades", flush=True)
        sets = {"ALL": result.trades, **{s: r.trades for s, r in result.runs.items()}}
        for group, trades in sets.items():
            row = summary_row(name, group, trades)
            summary.append(
                {
                    "variant": name,
                    "symbol": group,
                    "trades": row["trades"],
                    "win_rate": row["win_rate"],
                    "sum_r_gross": row["sum_r_gross"],
                    "sum_r_net": row["sum_r_net"],
                    "net_r_per_trade": row["avg_r_net"],
                    "swap_r": sum(t.swap_r for t in trades),
                }
            )
            split += half_rows(name, group, trades, labels, year)
            robust.append(robustness_row(name, group, trades, shocks, rcfg))
        by_class: dict[str, list] = {}
        for t in result.trades:
            m = market_class(t.symbol, trade_session(t))
            if m is not None:
                by_class.setdefault(m, []).append(t)
        classes += [class_row(name, m, by_class[m], rcfg) for m in CLASSES if m in by_class]
        family, order = family_key(config)
        entries.append((family, order, name, summary_net(summary, name)))
        write_csv(out / "summary.csv", summary)
        write_csv(out / "split.csv", split)
        write_csv(out / "robustness.csv", robust)
        write_csv(out / "classes.csv", classes)
    finish(out, summary, entries, args.volume, rcfg)
    print(f"halves: {labels[0]} / {labels[1]} in split.csv, per market class in classes.csv")
    print(swap_rates_note(engine.costs, symbols))
    if shock_note:
        print(shock_note)
    print(f"written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
