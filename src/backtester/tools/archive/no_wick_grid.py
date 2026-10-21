"""Run strategy 3 (no-wick candle in the trend) over its variants and compare the results.

    python -m backtester.tools.archive.no_wick_grid
    python -m backtester.tools.archive.no_wick_grid --timeframes M15 H1 --entries close --symbols XAUUSD

Variants = entry timeframe x trend source x entry mode (spec defaults for everything else).
Every variant is a full backtest with the same data and costs. Written to
`<out>/summary.csv` (variant x symbol group), `<out>/by_year.csv` and
`<out>/split.csv` (2020-22 against 2023-26: a result is only believed when both halves
agree), and printed as a table. Research only: it changes no setting.
Spec: strategy-no-wick.md.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from datetime import date
from pathlib import Path

from backtester.analytics.metrics import by_period, by_year, summarize
from backtester.core.models import Timeframe
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.no_wick.config import (
    HIGHER_TIMEFRAME,
    EntryMode,
    NoWickConfig,
    TrendSource,
)

SYMBOLS = ("XAUUSD", "GBPUSD", "GBPJPY", "NAS100", "US500")
FIRST_HALF_END_YEAR = 2022  # in sample: up to and including this year


def write_csv(path: Path, rows: list[dict]) -> None:
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def variant_name(config: NoWickConfig) -> str:
    return f"{config.timeframe.name} {config.trend_source.value} {config.entry_mode.value}"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, default=date(2020, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date(2026, 9, 30))
    p.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    p.add_argument(
        "--timeframes", nargs="+", choices=[t.name for t in HIGHER_TIMEFRAME],
        default=[t.name for t in HIGHER_TIMEFRAME],
    )  # fmt: skip
    p.add_argument("--trends", nargs="+", choices=[t.value for t in TrendSource],
                   default=[t.value for t in TrendSource])  # fmt: skip
    p.add_argument("--entries", nargs="+", choices=[e.value for e in EntryMode],
                   default=[e.value for e in EntryMode])  # fmt: skip
    p.add_argument("--out", type=Path, default=RESULTS_DIR / "no_wick_grid")
    args = p.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    summary, years, split = [], [], []
    for tf in args.timeframes:
        for trend in args.trends:
            for entry in args.entries:
                config = NoWickConfig(
                    timeframe=Timeframe[tf],
                    trend_source=TrendSource(trend),
                    entry_mode=EntryMode(entry),
                )
                name = variant_name(config)
                result = run_backtests(
                    [s.upper() for s in args.symbols],
                    args.start,
                    args.end,
                    replace(RunSettings(), strategy=config),
                )
                print(f"{name}: {len(result.trades)} trades", flush=True)
                sets = {"ALL": result.trades, **{s: r.trades for s, r in result.runs.items()}}
                for group, trades in sets.items():
                    s = summarize(trades)
                    summary.append(
                        {
                            "variant": name,
                            "symbol": group,
                            "trades": s["trades"],
                            "win_rate": s["win_rate"],
                            "net_r_gross": s["net_r_gross"],
                            "net_r_net": s["net_r_net"],
                            "avg_rr": s["avg_rr"],
                            "max_dd_r_net": s["max_drawdown_r_net"],
                        }
                    )
                    for label, part in (
                        (f"<= {FIRST_HALF_END_YEAR}",
                         [t for t in trades if t.entry_time.year <= FIRST_HALF_END_YEAR]),
                        (f"> {FIRST_HALF_END_YEAR}",
                         [t for t in trades if t.entry_time.year > FIRST_HALF_END_YEAR]),
                    ):  # fmt: skip
                        h = summarize(part)
                        split.append(
                            {
                                "variant": name,
                                "symbol": group,
                                "half": label,
                                "trades": h["trades"],
                                "net_r_gross": h["net_r_gross"],
                                "net_r_net": h["net_r_net"],
                            }
                        )
                for year, row in by_period(result.trades, by_year).items():
                    for group, s in row.items():
                        years.append(
                            {
                                "variant": name,
                                "year": year,
                                "symbol": group,
                                "trades": s["trades"],
                                "net_r_net": s["net_r_net"],
                            }
                        )
                write_csv(args.out / "summary.csv", summary)
                write_csv(args.out / "by_year.csv", years)
                write_csv(args.out / "split.csv", split)
    print(
        f"{'variant':28}{'trades':>8}{'win%':>7}{'gross R':>10}{'net R':>10}{'<=22':>9}{'>22':>9}"
    )
    halves = {(r["variant"], r["half"]): r["net_r_net"] for r in split if r["symbol"] == "ALL"}
    for r in (r for r in summary if r["symbol"] == "ALL"):
        a = halves[(r["variant"], f"<= {FIRST_HALF_END_YEAR}")]
        b = halves[(r["variant"], f"> {FIRST_HALF_END_YEAR}")]
        print(
            f"{r['variant']:28}{r['trades']:>8}{(r['win_rate'] or 0) * 100:>7.1f}"
            f"{r['net_r_gross']:>10.1f}{r['net_r_net']:>10.1f}{a:>9.1f}{b:>9.1f}"
        )
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
