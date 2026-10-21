"""A/B test of strategy 2's tick-volume filter: spec defaults against `min_rel_volume`.

    python -m backtester.tools.archive.s2_volume_ab --source mt5 --symbols US30 US2000 --end 2021-09-13
    python -m backtester.tools.archive.s2_volume_ab --source mt5 --symbols NAS100 US500 --start 2021-09-14

Two variants on the same data and costs (real spread scaled by price, FTMO swap): the spec
defaults and the entry candle's tick volume >= `--min-rel-volume` (1.5) x its usual value over
`--volume-lookback` (20) sessions. Needs candles with volume, so `--source mt5` (histdata candles
carry 0 and the filter would skip everything). Default symbols NAS100 and US500, from 2020-01-01
to the last cached day. Written to `<out>/summary.csv`, `split.csv` (2020-22 against 2023-26),
`robustness.csv` and `ab.csv` (one row per variant over all symbols: trades, gross, net, net per
trade, halves, net without the best trade, costs x 1.5). Default `<out>` is results/s2_volume_ab
(`s2_volume_ab_mt5` with `--source mt5`). Symbols other than NAS100 / US500 are a backtest-only
extension of strategy 2. Research only: it changes no setting. Spec: strategy-ny-indices.md >
Volume filter (ROADMAP 11.15).
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import UTC, date, datetime
from pathlib import Path

from backtester.analytics.robustness import RobustnessConfig
from backtester.core.models import Timeframe
from backtester.data.cache import MT5_CACHE_DIR
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.detectors.settings import DetectorSettings
from backtester.detectors.swings import SwingConfig, equivalent_doji_body
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
from backtester.tools.archive.trend_grid import (
    HALVES,
    half_rows,
    load_shocks,
    robustness_row,
    summary_row,
    swap_rates_note,
    write_csv,
)

SYMBOLS = ("NAS100", "US500")
SPEC_SYMBOLS = frozenset(SYMBOLS)
START = date(2020, 1, 1)
DOJI_FROM = date(2020, 1, 2)  # the median 5m range the spec took for the indices starts here
MIN_REL_VOLUME = 1.5
VOLUME_LOOKBACK = 20
WORKERS = 1  # in-process: the process pool stalled on long 1-minute runs
BASE = "spec defaults"


def variants(min_rel_volume: float, volume_lookback: int) -> list[tuple[str, NyIndexSweepConfig]]:
    return [
        (BASE, NyIndexSweepConfig()),
        (
            f"volume >= {min_rel_volume:g} x usual",
            NyIndexSweepConfig(min_rel_volume=min_rel_volume, volume_lookback=volume_lookback),
        ),
    ]


def swing_config_for(
    symbols: list[str],
    start: date,
    end: date,
    sources: SymbolSources,
    base: SwingConfig | None = None,
) -> SwingConfig:
    """`base` plus a doji threshold for each symbol that has none (the backtest-only
    extension symbols): the gold rule (swings.py `equivalent_doji_body`) on the symbol's
    median 5m candle range over start..end, as the spec derived NAS100's and US500's."""
    base = base or SwingConfig()
    missing = [s for s in symbols if s not in base.doji_max_body]
    if not missing:
        return base
    extra = {}
    for symbol in missing:
        frame = sources.adapter(symbol).fetch_frame(
            symbol,
            Timeframe.M5,
            datetime.combine(start, datetime.min.time(), UTC),
            datetime.combine(end, datetime.min.time(), UTC),
        )
        extra[symbol] = equivalent_doji_body(float((frame["high"] - frame["low"]).median()))
    return replace(base, doji_max_body={**base.doji_max_body, **extra})


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, default=START)
    p.add_argument("--end", type=date.fromisoformat, default=None,
                   help="default: the last cached day")  # fmt: skip
    p.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    p.add_argument("--min-rel-volume", type=float, default=MIN_REL_VOLUME)
    p.add_argument("--volume-lookback", type=int, default=VOLUME_LOOKBACK)
    p.add_argument("--no-shocks", action="store_true",
                   help="do not read the daily bars for the shock days")  # fmt: skip
    p.add_argument("--source", choices=("histdata", "mt5"), default="histdata",
                   help="candle cache: histdata (default, no volume) or FTMO's data/cache/mt5")  # fmt: skip
    p.add_argument("--workers", type=int, default=WORKERS)
    p.add_argument("--out", type=Path, default=None)
    return p.parse_args(argv)


def last_cached_day(symbols: list[str], sources: SymbolSources = DEFAULT_SOURCES) -> date:
    return max(max(sources.cached_days(s)) for s in symbols)


def ab_row(name: str, summary: dict, robust: dict, halves: list[dict]) -> dict:
    row = {
        "variant": name,
        "trades": summary["trades"],
        "sum_r_gross": summary["sum_r_gross"],
        "sum_r_net": summary["sum_r_net"],
        "net_r_per_trade": summary["net_r_per_trade"],
    }
    for h in halves:
        row[f"half_{h['half']}_trades"] = h["trades"]
        row[f"half_{h['half']}_net"] = h["sum_r_net"]
    row["net_without_best"] = robust["net_r_without_best"]
    row["net_costs_x1.5"] = robust["net_r_stressed"]
    return row


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    symbols = [s.upper() for s in args.symbols]
    sources = (
        DEFAULT_SOURCES
        if args.source == "histdata"
        else SymbolSources.single(MT5_CACHE_DIR, symbols)
    )
    end = args.end or last_cached_day(symbols, sources)
    folder = "s2_volume_ab" if args.source == "histdata" else f"s2_volume_ab_{args.source}"
    out = args.out or RESULTS_DIR / folder
    out.mkdir(parents=True, exist_ok=True)
    extra = sorted(set(symbols) - SPEC_SYMBOLS)
    if extra:
        print(
            f"note: {', '.join(extra)}: strategy 2 is specced for NAS100 / US500; running it "
            "there is a backtest-only extension"
        )
    rcfg = RobustnessConfig()
    shocks, shock_note = (
        ({}, "") if args.no_shocks else load_shocks(symbols, args.start, end, rcfg, sources)
    )
    engine = RunSettings().engine
    swings = swing_config_for(symbols, max(args.start, DOJI_FROM), end, sources)
    detectors = DetectorSettings(swings=swings)
    summary, split, robust, ab = [], [], [], []
    for name, config in variants(args.min_rel_volume, args.volume_lookback):
        result = run_backtests(
            symbols,
            args.start,
            end,
            replace(RunSettings(), strategy=config, engine=engine, detectors=detectors),
            sources=sources,
            workers=args.workers,
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
            halves = half_rows(name, group, trades)
            split += halves
            rob = robustness_row(name, group, trades, shocks, rcfg)
            robust.append(rob)
            if group == "ALL":
                ab.append(ab_row(name, summary[-1], rob, halves))
        write_csv(out / "summary.csv", summary)
        write_csv(out / "split.csv", split)
        write_csv(out / "robustness.csv", robust)
        write_csv(out / "ab.csv", ab)
    h1, h2 = HALVES
    print(f"\n{'variant':26}{'trades':>7}{'gross':>9}{'net':>9}{'net/tr':>8}{h1:>9}{h2:>9}")
    for r in ab:
        per = "-" if r["net_r_per_trade"] is None else f"{r['net_r_per_trade']:+.3f}"
        print(
            f"{r['variant']:26}{r['trades']:>7}{r['sum_r_gross']:>+9.1f}{r['sum_r_net']:>+9.1f}"
            f"{per:>8}{r[f'half_{h1}_net']:>+9.1f}{r[f'half_{h2}_net']:>+9.1f}"
        )
    print(swap_rates_note(engine.costs, symbols))
    if shock_note:
        print(shock_note)
    print(f"written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
