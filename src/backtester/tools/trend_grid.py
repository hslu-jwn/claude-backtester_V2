"""Run strategy 4 (trend following) over its variants and compare the results.

    python -m backtester.tools.trend_grid
    python -m backtester.tools.trend_grid --signals breakout --timeframes H4 D1 --symbols XAUUSD
    python -m backtester.tools.trend_grid --no-sweep --start 2026-08-01 --end 2026-08-31

Variants = signal x timeframe, each with the spec's parameter sweep (breakout 20 / 55 /
100, SMA 20 / 50 / 100 / 200, KAMA filter 0.0 / 0.1 / 0.5; the spec default is one of the
values, so the plain signal x timeframe variants are inside the sweep). `--no-sweep` runs
only the spec defaults. Everything else is the spec default. Every variant is a full
backtest with the same data and costs. Written to `<out>/summary.csv` (variant x symbol
group), `<out>/by_year.csv` and `<out>/split.csv` (2020-22 against 2023-26: a variant counts
only when neighbouring parameters and both periods agree), and printed as a table.
Research only: it changes no setting.

The indicators' history comes from the strategy (`Strategy.min_warmup_days`), so a run that
starts at the first cached day has fewer warm-up candles than that (D1 with SMA 200 trades
from about October of the first year). Swap is not modelled: net results of trades held
for days are optimistic by the swap. Spec: strategy-trend-following.md.
"""

from __future__ import annotations

import argparse
import csv
from collections.abc import Sequence
from dataclasses import replace
from datetime import date
from pathlib import Path

from backtester.analytics.metrics import by_period, by_year, summarize
from backtester.core.models import Timeframe
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.trend_following.config import TIMEFRAMES, Signal, TrendFollowingConfig

SYMBOLS = ("XAUUSD", "GBPUSD", "GBPJPY", "NAS100", "US500")
FIRST_HALF_END_YEAR = 2022  # in sample: up to and including this year
HALVES = ("2020-22", "2023-26")
# the spec's parameter sweep (strategy-trend-following.md › Evaluation)
SWEEP_BREAKOUT = (20, 55, 100)
SWEEP_SMA = (20, 50, 100, 200)
SWEEP_KAMA_FILTER = (0.0, 0.1, 0.5)
SWEPT_FIELD = {
    Signal.BREAKOUT: "breakout_period",
    Signal.SMA: "sma_period",
    Signal.KAMA: "kama_filter",
}
SWAP_NOTE = (
    "note: swap is not modelled (swap_*_per_lot = 0); net results of trades held for days "
    "are optimistic by the swap"
)


def write_csv(path: Path, rows: list[dict]) -> None:
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def variants(
    signals: Sequence[Signal],
    timeframes: Sequence[Timeframe],
    sweep: bool = True,
    breakout: Sequence[int] = SWEEP_BREAKOUT,
    sma: Sequence[int] = SWEEP_SMA,
    kama_filters: Sequence[float] = SWEEP_KAMA_FILTER,
) -> list[TrendFollowingConfig]:
    """One config per timeframe x signal x swept parameter value (the spec default only
    without `sweep`)."""
    values = {Signal.BREAKOUT: breakout, Signal.SMA: sma, Signal.KAMA: kama_filters}
    out = []
    for tf in timeframes:
        for signal in signals:
            base = TrendFollowingConfig(timeframe=tf, signal=signal)
            field = SWEPT_FIELD[signal]
            for value in values[signal] if sweep else (getattr(base, field),):
                out.append(replace(base, **{field: value}))
    return out


def variant_name(config: TrendFollowingConfig) -> str:
    param = getattr(config, SWEPT_FIELD[config.signal])
    return f"{config.timeframe.name} {config.signal.value} {param:g}"


def avg_holding_hours(trades: Sequence) -> float | None:
    if not trades:
        return None
    return sum((t.exit_time - t.entry_time).total_seconds() for t in trades) / len(trades) / 3600


def summary_row(variant: str, group: str, trades: Sequence) -> dict:
    s = summarize(trades)
    return {
        "variant": variant,
        "symbol": group,
        "trades": s["trades"],
        "win_rate": s["win_rate"],
        "avg_r_gross": s["avg_r_gross"],
        "avg_r_net": s["avg_r_net"],
        "sum_r_gross": s["net_r_gross"],
        "sum_r_net": s["net_r_net"],
        "profit_factor": s["profit_factor"],
        "max_dd_r_net": s["max_drawdown_r_net"],
        "avg_hold_hours": avg_holding_hours(trades),
    }


def half_rows(variant: str, group: str, trades: Sequence) -> list[dict]:
    parts = (
        [t for t in trades if t.entry_time.year <= FIRST_HALF_END_YEAR],
        [t for t in trades if t.entry_time.year > FIRST_HALF_END_YEAR],
    )
    rows = []
    for half, part in zip(HALVES, parts, strict=True):
        s = summarize(part)
        rows.append(
            {
                "variant": variant,
                "symbol": group,
                "half": half,
                "trades": s["trades"],
                "sum_r_gross": s["net_r_gross"],
                "sum_r_net": s["net_r_net"],
            }
        )
    return rows


def year_rows(variant: str, trades: Sequence) -> list[dict]:
    rows = []
    for year, groups in by_period(trades, by_year).items():
        for group, s in groups.items():
            rows.append(
                {
                    "variant": variant,
                    "year": year,
                    "symbol": "ALL" if group == "all" else group,
                    "trades": s["trades"],
                    "sum_r_gross": s["net_r_gross"],
                    "sum_r_net": s["net_r_net"],
                }
            )
    return rows


def _fmt(value: float | None, spec: str) -> str:
    return "-" if value is None else format(value, spec)


def print_table(summary: list[dict], split: list[dict]) -> None:
    print(
        f"{'variant':20}{'trades':>7}{'win%':>6}{'avgR gr':>9}{'avgR net':>9}{'sumR gr':>9}"
        f"{'sumR net':>9}{'PF':>6}{'maxDD':>7}{'hold h':>8}{'20-22':>8}{'23-26':>8}"
    )
    halves = {(r["variant"], r["half"]): r["sum_r_net"] for r in split if r["symbol"] == "ALL"}
    for r in (r for r in summary if r["symbol"] == "ALL"):
        win = None if r["win_rate"] is None else r["win_rate"] * 100
        print(
            f"{r['variant']:20}{r['trades']:>7}{_fmt(win, '.1f'):>6}"
            f"{_fmt(r['avg_r_gross'], '+.3f'):>9}{_fmt(r['avg_r_net'], '+.3f'):>9}"
            f"{r['sum_r_gross']:>+9.1f}{r['sum_r_net']:>+9.1f}"
            f"{_fmt(r['profit_factor'], '.2f'):>6}{r['max_dd_r_net']:>7.1f}"
            f"{_fmt(r['avg_hold_hours'], '.0f'):>8}"
            f"{halves[(r['variant'], HALVES[0])]:>+8.1f}{halves[(r['variant'], HALVES[1])]:>+8.1f}"
        )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, default=date(2020, 1, 1))
    p.add_argument("--end", type=date.fromisoformat, default=date(2026, 9, 30))
    p.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    p.add_argument("--signals", nargs="+", choices=[s.value for s in Signal],
                   default=[s.value for s in Signal])  # fmt: skip
    p.add_argument("--timeframes", nargs="+", choices=[t.name for t in TIMEFRAMES],
                   default=[t.name for t in TIMEFRAMES])  # fmt: skip
    p.add_argument("--no-sweep", action="store_true", help="only the spec's default parameters")
    p.add_argument("--breakout-periods", nargs="+", type=int, default=list(SWEEP_BREAKOUT))
    p.add_argument("--sma-periods", nargs="+", type=int, default=list(SWEEP_SMA))
    p.add_argument("--kama-filters", nargs="+", type=float, default=list(SWEEP_KAMA_FILTER))
    p.add_argument("--out", type=Path, default=RESULTS_DIR / "trend_grid")
    args = p.parse_args(argv)

    configs = variants(
        [Signal(s) for s in args.signals],
        [Timeframe[t] for t in args.timeframes],
        sweep=not args.no_sweep,
        breakout=args.breakout_periods,
        sma=args.sma_periods,
        kama_filters=args.kama_filters,
    )
    symbols = [s.upper() for s in args.symbols]
    args.out.mkdir(parents=True, exist_ok=True)
    summary, years, split = [], [], []
    for config in configs:
        name = variant_name(config)
        result = run_backtests(
            symbols, args.start, args.end, replace(RunSettings(), strategy=config)
        )
        print(f"{name}: {len(result.trades)} trades", flush=True)
        sets = {"ALL": result.trades, **{s: r.trades for s, r in result.runs.items()}}
        for group, trades in sets.items():
            summary.append(summary_row(name, group, trades))
            split += half_rows(name, group, trades)
        years += year_rows(name, result.trades)
        write_csv(args.out / "summary.csv", summary)
        write_csv(args.out / "by_year.csv", years)
        write_csv(args.out / "split.csv", split)
    print_table(summary, split)
    print(SWAP_NOTE)
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
