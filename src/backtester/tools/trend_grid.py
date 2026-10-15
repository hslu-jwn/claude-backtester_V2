"""Run strategy 4 (trend following) over its variants and compare the results.

    python -m backtester.tools.trend_grid
    python -m backtester.tools.trend_grid --signals breakout --timeframes H4 D1 --symbols XAUUSD
    python -m backtester.tools.trend_grid --no-sweep --start 2026-08-01 --end 2026-08-31

Variants = signal x timeframe, each with the spec's parameter sweep (breakout 20 / 55 /
100, SMA 20 / 50 / 100 / 200, SMA 50 and 200 with band 0.5 / 1.0 ATR, momentum 5 / 20 / 63 /
252, Dunnigan without parameters, KAMA filter 0.0 / 0.1 / 0.5; the spec default is one of the
values, so the plain signal x timeframe variants are inside the sweep). `--no-sweep` runs
only the spec defaults. Everything else is the spec default. Every variant is a full
backtest with the same data and costs. Written to `<out>/summary.csv` (variant x symbol
group), `<out>/by_year.csv` and `<out>/split.csv` (2020-22 against 2023-26: a variant counts
only when neighbouring parameters and both periods agree), and printed as a table.
`<out>/robustness.csv` (variant x symbol group: net R without the best trade, with costs x 1.5,
the two halves with Welch's t, kurtosis of the daily R, shock days) and `<out>/grid.csv` (per
signal x timeframe family and over all variants: share of profitable variants, mean, st.dev,
mean - 1 sd, robust at >= 70 %, and the plateau variant of the neighbour-smoothed net R) come
from `analytics/robustness.py` (ROADMAP 6.4; knowledge/topics/testing-and-robustness.md).
`--no-shocks` skips reading the daily bars for the shock days.
Research only: it changes no setting.

The indicators' history comes from the strategy (`Strategy.min_warmup_days`), so a run that
starts at the first cached day has fewer warm-up candles than that (D1 with SMA 200 trades
from about October of the first year). Net R includes the swap
(engine/costs.py: 17:00 New York rollovers); `sumR ex-swap` = net without it, computed per
trade as r_net - swap_r (no second run). The default swap rates are FTMO's of 2026-10-14
(engine/costs.py); give other ones with `--swap-file rates.json`:

    {"XAUUSD": {"long": -12.5, "short": 4.0, "triple_weekday": 2}, ...}

(USD per 1.0 lot per night, negative = cost; weekday 0 = Monday; missing keys keep their
value). Spec: strategy-trend-following.md.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from backtester.analytics.metrics import by_period, by_year, summarize
from backtester.analytics.robustness import (
    RobustnessConfig,
    grid_stats,
    plateau_index,
    shock_dates,
    trade_robustness,
)
from backtester.core.models import Timeframe
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.engine.costs import CostConfig
from backtester.engine.spread_table import SpreadTable
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.trend_following.config import TIMEFRAMES, Signal, TrendFollowingConfig

SYMBOLS = ("XAUUSD", "GBPUSD", "GBPJPY", "NAS100", "US500")
FIRST_HALF_END_YEAR = RobustnessConfig().first_half_end_year  # in sample: up to this year
HALVES = ("2020-22", "2023-26")
# the spec's parameter sweep (strategy-trend-following.md › Evaluation)
SWEEP_BREAKOUT = (20, 55, 100)
SWEEP_SMA = (20, 50, 100, 200)
SWEEP_KAMA_FILTER = (0.0, 0.1, 0.5)
SWEEP_MOMENTUM = (5, 20, 63, 252)
SWEEP_SMA_BAND_PERIODS = (50, 200)
SWEEP_SMA_BANDS = (0.5, 1.0)
SWEPT_FIELD = {  # None: the signal has no parameter
    Signal.BREAKOUT: "breakout_period",
    Signal.SMA: "sma_period",
    Signal.MOMENTUM: "momentum_period",
    Signal.DUNNIGAN: None,
    Signal.KAMA: "kama_filter",
}
SWAP_FILE_KEYS = {  # JSON key -> SymbolCosts field
    "long": "swap_long_per_lot",
    "short": "swap_short_per_lot",
    "triple_weekday": "swap_triple_weekday",
}
LAST_WEEKDAY = 6  # Sunday; datetime.weekday()


def load_swap_file(path: Path, base: CostConfig) -> CostConfig:
    """`base` with the swap rates of the JSON file {symbol: {long, short, triple_weekday}}."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("swap file: expected an object {symbol: {long, short, triple_weekday}}")  # noqa: TRY004
    symbols = dict(base.symbols)
    for symbol, rates in data.items():
        if symbol not in symbols:
            raise ValueError(f"swap file: no cost settings for {symbol}")
        if not isinstance(rates, dict) or not set(rates) <= set(SWAP_FILE_KEYS):
            raise ValueError(f"swap file {symbol}: keys must be {sorted(SWAP_FILE_KEYS)}")
        changes = {}
        for key, value in rates.items():
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ValueError(f"swap file {symbol}.{key}: not a number")  # noqa: TRY004
            if key == "triple_weekday":
                if value != int(value) or not 0 <= value <= LAST_WEEKDAY:
                    raise ValueError(f"swap file {symbol}.{key}: weekday must be 0-6")
                value = int(value)
            changes[SWAP_FILE_KEYS[key]] = value
        symbols[symbol] = replace(symbols[symbol], **changes)
    return replace(base, symbols=symbols)


def swap_rates_note(costs: CostConfig, symbols: Sequence[str]) -> str:
    """Which swap rates the run used."""
    used = {s: costs.symbols[s] for s in symbols if s in costs.symbols}
    if not any(c.swap_long_per_lot or c.swap_short_per_lot for c in used.values()):
        return "swap rates are 0 (--swap-file to set them); net = net ex-swap"
    parts = [
        f"{s} long {c.swap_long_per_lot:g} short {c.swap_short_per_lot:g} "
        f"triple weekday {c.swap_triple_weekday}"
        for s, c in used.items()
    ]
    return "swap rates (USD per lot per night): " + "; ".join(parts)


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
    momentum: Sequence[int] = SWEEP_MOMENTUM,
    sma_bands: Sequence[float] = SWEEP_SMA_BANDS,
    sma_band_periods: Sequence[int] = SWEEP_SMA_BAND_PERIODS,
) -> list[TrendFollowingConfig]:
    """One config per timeframe x signal x swept parameter value (the spec default only
    without `sweep`). With the sweep the SMA also runs banded: each band period x band."""
    values = {
        Signal.BREAKOUT: breakout,
        Signal.SMA: sma,
        Signal.MOMENTUM: momentum,
        Signal.DUNNIGAN: (None,),
        Signal.KAMA: kama_filters,
    }
    out = []
    for tf in timeframes:
        for signal in signals:
            base = TrendFollowingConfig(timeframe=tf, signal=signal)
            field = SWEPT_FIELD[signal]
            if not sweep:
                out.append(base)
                continue
            for value in values[signal]:
                out.append(base if field is None else replace(base, **{field: value}))
            if signal is Signal.SMA:
                out += [
                    replace(base, sma_period=period, sma_band_atr=band)
                    for period in sma_band_periods
                    for band in sma_bands
                ]
    return out


def variant_name(config: TrendFollowingConfig) -> str:
    field = SWEPT_FIELD[config.signal]
    name = f"{config.timeframe.name} {config.signal.value}"
    if field is not None:
        name += f" {getattr(config, field):g}"
    if config.signal is Signal.SMA and config.sma_band_atr > 0:
        name += f" b{config.sma_band_atr:g}"
    return name


def avg_holding_hours(trades: Sequence) -> float | None:
    if not trades:
        return None
    return sum((t.exit_time - t.entry_time).total_seconds() for t in trades) / len(trades) / 3600


def sum_ex_swap(trades: Sequence) -> float:
    """Net R without the swap: r_net already includes swap_r, so take it out per trade."""
    return sum(t.r_net - t.swap_r for t in trades)


def summary_row(variant: str, group: str, trades: Sequence) -> dict:
    s = summarize(trades)
    ex_swap = sum_ex_swap(trades)
    return {
        "variant": variant,
        "symbol": group,
        "trades": s["trades"],
        "win_rate": s["win_rate"],
        "avg_r_gross": s["avg_r_gross"],
        "avg_r_net": s["avg_r_net"],
        "sum_r_gross": s["net_r_gross"],
        "sum_r_net": s["net_r_net"],  # with swap
        "avg_r_ex_swap": ex_swap / len(trades) if trades else None,
        "sum_r_ex_swap": ex_swap,
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
                "sum_r_ex_swap": sum_ex_swap(part),
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
                    "sum_r_ex_swap": sum_ex_swap(
                        [t for t in trades if by_year(t) == year and group in ("all", t.symbol)]
                    ),
                }
            )
    return rows


ALL_VARIANTS = "ALL VARIANTS"
SHOCK_WARMUP_DAYS = 30  # calendar days before the run for the mean true range


def family_key(config: TrendFollowingConfig) -> tuple[str, float]:
    """(family, order): the variants that differ only in the swept parameter share a family
    and are ordered by it; the banded SMA is a family per band, ordered by period."""
    prefix = f"{config.timeframe.name} {config.signal.value}"
    if config.signal is Signal.SMA and config.sma_band_atr > 0:
        return f"{prefix} band {config.sma_band_atr:g}", config.sma_period
    field = SWEPT_FIELD[config.signal]
    return prefix, 0 if field is None else getattr(config, field)


def robustness_row(
    variant: str,
    group: str,
    trades: Sequence,
    shocks: Mapping[str, set[date]] | None,
    config: RobustnessConfig | None = None,
) -> dict:
    return {
        "variant": variant,
        "symbol": group,
        **trade_robustness(trades, config, shocks or None),
    }


def grid_rows(
    entries: Sequence[tuple[str, float, str, float]], config: RobustnessConfig | None = None
) -> list[dict]:
    """Per family and over all variants: `entries` are (family, order, variant, net R of the
    ALL group). The variants of a family are taken in parameter order for the smoothing."""
    families: dict[str, list[tuple[float, str, float]]] = {}
    for family, order, variant, net in entries:
        families.setdefault(family, []).append((order, variant, net))
    rows = []
    for family, items in families.items():
        items.sort(key=lambda x: x[0])
        values = [net for _, _, net in items]
        best = plateau_index(values)
        rows.append(
            {
                "family": family,
                **grid_stats(values, config),
                "plateau_variant": "" if best is None else items[best][1],
            }
        )
    rows.append(
        {
            "family": ALL_VARIANTS,
            **grid_stats([e[3] for e in entries], config),
            "plateau_variant": "",
        }
    )
    return rows


def _midnight(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=UTC)


def load_shocks(
    symbols: Sequence[str],
    start: date,
    end: date,
    config: RobustnessConfig | None = None,
    sources: SymbolSources | None = None,
) -> tuple[dict[str, set[date]], str]:
    """({symbol: shock dates}, note). Daily bars from the cache (a bar is dated the day it
    closes); a symbol that cannot be read is left out and the note says so."""
    cfg = config or RobustnessConfig()
    sources = sources or DEFAULT_SOURCES
    shocks: dict[str, set[date]] = {}
    parts, failed = [], []
    for symbol in symbols:
        try:
            cached = set(sources.cached_days(symbol))
            first = start - timedelta(days=SHOCK_WARMUP_DAYS)
            days = [d for d in cached if first <= d <= end]
            if not days:
                raise ValueError("no cached days")
            frame = sources.adapter(symbol).fetch_frame(
                symbol,
                Timeframe.D1,
                _midnight(min(days)),
                _midnight(max(days) + timedelta(days=1)),
            )
            bars = [
                ((ts + timedelta(days=1)).date(), hi, lo, cl)
                for ts, hi, lo, cl in zip(
                    frame["ts"].dt.to_pydatetime(),
                    frame["high"],
                    frame["low"],
                    frame["close"],
                    strict=True,
                )
            ]
            found = {d for d in shock_dates(bars, cfg) if d >= start}
            shocks[symbol] = found
            parts.append(f"{symbol} {len(found)}")
        except Exception as e:  # noqa: BLE001 - research tool: an unreadable cache is a note
            failed.append(f"{symbol} ({type(e).__name__})")
    note = (
        f"shock days (daily range > {cfg.shock_range_atr:g} x the mean of the "
        f"{cfg.shock_atr_period} days before): " + (", ".join(parts) or "none")
    )
    if failed:
        note += "; not available: " + ", ".join(failed)
    return shocks, note


def summary_net(summary: Sequence[dict], variant: str) -> float:
    """Net R (with swap) of the ALL group of `variant` in the summary rows."""
    return next(r["sum_r_net"] for r in summary if r["variant"] == variant and r["symbol"] == "ALL")


def _fmt(value: float | None, spec: str) -> str:
    return "-" if value is None else format(value, spec)


def print_table(summary: list[dict], split: list[dict]) -> None:
    print(
        f"{'variant':20}{'trades':>7}{'win%':>6}{'avgR gr':>9}{'avgR net':>9}{'avgR exsw':>10}"
        f"{'sumR gr':>9}{'sumR net':>9}{'sumR exsw':>10}{'PF':>6}{'maxDD':>7}{'hold h':>8}"
        f"{'20-22':>8}{'23-26':>8}"
    )
    halves = {(r["variant"], r["half"]): r["sum_r_net"] for r in split if r["symbol"] == "ALL"}
    for r in (r for r in summary if r["symbol"] == "ALL"):
        win = None if r["win_rate"] is None else r["win_rate"] * 100
        print(
            f"{r['variant']:20}{r['trades']:>7}{_fmt(win, '.1f'):>6}"
            f"{_fmt(r['avg_r_gross'], '+.3f'):>9}{_fmt(r['avg_r_net'], '+.3f'):>9}"
            f"{_fmt(r['avg_r_ex_swap'], '+.3f'):>10}"
            f"{r['sum_r_gross']:>+9.1f}{r['sum_r_net']:>+9.1f}{r['sum_r_ex_swap']:>+10.1f}"
            f"{_fmt(r['profit_factor'], '.2f'):>6}{r['max_dd_r_net']:>7.1f}"
            f"{_fmt(r['avg_hold_hours'], '.0f'):>8}"
            f"{halves[(r['variant'], HALVES[0])]:>+8.1f}{halves[(r['variant'], HALVES[1])]:>+8.1f}"
        )


def print_grid(rows: list[dict]) -> None:
    print(
        f"\n{'family':22}{'n':>4}{'profit%':>8}{'mean':>8}{'std':>8}{'mean-sd':>9}"
        f"{'robust':>8}  plateau variant"
    )
    for r in rows:
        share = None if r["profitable_share"] is None else r["profitable_share"] * 100
        print(
            f"{r['family']:22}{r['n']:>4}{_fmt(share, '.0f'):>8}{_fmt(r['mean'], '+.1f'):>8}"
            f"{_fmt(r['std'], '.1f'):>8}{_fmt(r['adjusted'], '+.1f'):>9}"
            f"{'yes' if r['robust'] else 'no':>8}  {r['plateau_variant']}"
        )
    print("(net R of the ALL group per variant; robust = at least 70 % of the variants profitable)")


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
    p.add_argument("--momentum-periods", nargs="+", type=int, default=list(SWEEP_MOMENTUM))
    p.add_argument("--sma-bands", nargs="+", type=float, default=list(SWEEP_SMA_BANDS),
                   help="ATR band widths of the banded SMA variants")  # fmt: skip
    p.add_argument("--sma-band-periods", nargs="+", type=int, default=list(SWEEP_SMA_BAND_PERIODS))
    p.add_argument("--swap-file", type=Path, default=None,
                   help='JSON {symbol: {"long": usd_per_lot_night, "short": ..., "triple_weekday": 0-6}}')  # fmt: skip
    p.add_argument("--spread-table", type=Path, default=None,
                   help="spread by year and hour (tools/spread_table.py JSON); default: fixed spread")  # fmt: skip
    p.add_argument("--no-shocks", action="store_true",
                   help="do not read the daily bars for the shock days")  # fmt: skip
    p.add_argument("--out", type=Path, default=RESULTS_DIR / "trend_grid")
    args = p.parse_args(argv)

    configs = variants(
        [Signal(s) for s in args.signals],
        [Timeframe[t] for t in args.timeframes],
        sweep=not args.no_sweep,
        breakout=args.breakout_periods,
        sma=args.sma_periods,
        kama_filters=args.kama_filters,
        momentum=args.momentum_periods,
        sma_bands=args.sma_bands,
        sma_band_periods=args.sma_band_periods,
    )
    symbols = [s.upper() for s in args.symbols]
    engine = RunSettings().engine
    if args.swap_file is not None:
        engine = replace(engine, costs=load_swap_file(args.swap_file, engine.costs))
    if args.spread_table is not None:
        table = SpreadTable.from_dict(json.loads(args.spread_table.read_text(encoding="utf-8")))
        engine = replace(engine, costs=replace(engine.costs, spread_table=table))
        print(f"spread table: {table.stat} by year and New York hour, {table.note}")
    args.out.mkdir(parents=True, exist_ok=True)
    rcfg = RobustnessConfig()
    shocks, shock_note = (
        ({}, "") if args.no_shocks else load_shocks(symbols, args.start, args.end, rcfg)
    )
    summary, years, split, robust, entries = [], [], [], [], []
    for config in configs:
        name = variant_name(config)
        result = run_backtests(
            symbols, args.start, args.end, replace(RunSettings(), strategy=config, engine=engine)
        )
        print(f"{name}: {len(result.trades)} trades", flush=True)
        sets = {"ALL": result.trades, **{s: r.trades for s, r in result.runs.items()}}
        for group, trades in sets.items():
            summary.append(summary_row(name, group, trades))
            split += half_rows(name, group, trades)
            robust.append(robustness_row(name, group, trades, shocks, rcfg))
        family, order = family_key(config)
        entries.append((family, order, name, summary_net(summary, name)))
        years += year_rows(name, result.trades)
        write_csv(args.out / "summary.csv", summary)
        write_csv(args.out / "by_year.csv", years)
        write_csv(args.out / "split.csv", split)
        write_csv(args.out / "robustness.csv", robust)
    grid = grid_rows(entries, rcfg)
    write_csv(args.out / "grid.csv", grid)
    print_table(summary, split)
    print_grid(grid)
    print(swap_rates_note(engine.costs, symbols))
    if shock_note:
        print(shock_note)
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
