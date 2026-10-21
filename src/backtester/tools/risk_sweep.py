"""Variant sweep of the adaptive prop-firm risk on the R trades of every strategy.

    python -m backtester.tools.risk_sweep                      # everything, resumable
    python -m backtester.tools.risk_sweep --strategies opening_range --runs 200
    python -m backtester.tools.risk_sweep --phase dev          # backtests + dev grid only

Per strategy (its own symbols) the R trade list of (a) the development period (histdata, from
2018 up to 2021-09-13) and (b) the test period (FTMO MT5, 2021-09-14 up to `test_end`) is
backtested (in pieces at the days histdata.com has no file for, `grid_common.run_variant`; indicator
history restarts there) with the spec defaults (strategy 6: the forward-test candidate) and cached under
`<out>/trades/`; a rerun reads the cache. Grid (`SweepConfig`): base risk x floor x daily
budget (+ the fixed-risk baseline per base risk), each cell played through
`risk.monte_carlo.ftmo_by_risk` on the same reshuffled day orders (same seed) for every
variant of a strategy and period.

Selection never sees the test period: the grid runs on the development period, the best
variant per strategy (highest pass probability; within `near_tie` of the best the fewest
average days to pass) and the universal variant (best mean rank of the pass probability over
all strategies) are fixed and only then played once on the test period, next to the
fixed-risk baseline of the same base risk. Writes `<out>/<date>/` summary.json, variants.csv
and report.md. Research only: it changes no default.

Spec: risk-management.md > Prop-firm field > Adaptive risk (ROADMAP 5.7 part 2).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time as clock
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path

from backtester.analytics.trial_log import settings_dict
from backtester.data.cache import DEFAULT_CACHE_DIR, MT5_CACHE_DIR
from backtester.data.sources import SymbolSources
from backtester.paths import RESULTS_DIR
from backtester.risk.adaptive import AdaptiveRisk
from backtester.risk.monte_carlo import (
    MonteCarloConfig,
    build_days,
    ftmo_by_risk,
    reshuffle_orders,
)
from backtester.runner import RunSettings
from backtester.strategy.opening_range.config import EntryMode, OpeningRangeConfig
from backtester.strategy.registry import REGISTRY, default_config
from backtester.tools.grid_common import run_variant

SWEEP_DIR = "risk_sweep"
TRADES_DIR = "trades"
PERCENT = 100.0
NO_BUDGET = 100.0  # daily budget (x initial balance) that never binds
FIVE = ("XAUUSD", "GBPUSD", "GBPJPY", "NAS100", "US500")


@dataclass(frozen=True, slots=True)
class SweepConfig:
    base_risks: tuple[float, ...] = (0.0025, 0.005, 0.0075, 0.01, 0.015)
    floors: tuple[float | None, ...] = (0.1, 0.25, 0.5, None)  # None = no scaling
    budgets: tuple[float | None, ...] = (None, 0.02, 0.025, 0.03, 0.04)  # None = no budget
    runs: int = 1000
    seed: int = 42
    near_tie: float = 0.01  # pass probabilities this close to the best count as tied
    flat_bands: tuple[float, ...] = (0.01, 0.02)  # "within x of the best" for the flat-top count
    min_meaningful_pass: float = 0.05  # best dev pass probability below this: no real optimum
    no_budget: float = NO_BUDGET
    dev_start: date = date(2018, 1, 1)
    cutoff: date = date(2021, 9, 14)  # first day of the test period (data split, CLAUDE.md)
    test_end: date = date(2026, 10, 16)  # last complete Friday in the MT5 cache
    workers: int = 4

    def __post_init__(self) -> None:
        if self.runs < 1 or self.workers < 1:
            raise ValueError("runs and workers must be >= 1")
        if not self.base_risks or not self.floors or not self.budgets:
            raise ValueError("base_risks, floors and budgets must not be empty")
        if not self.dev_start < self.cutoff <= self.test_end:
            raise ValueError("need dev_start < cutoff <= test_end")

    @property
    def dev_end(self) -> date:
        return date.fromordinal(self.cutoff.toordinal() - 1)


@dataclass(frozen=True, slots=True)
class Variant:
    base: float  # base risk, fraction of the balance
    floor: float | None  # least share of the base risk; None = no scaling
    budget: float | None  # daily risk budget, fraction of the initial balance; None = none

    @property
    def is_fixed(self) -> bool:
        return self.floor is None and self.budget is None

    @property
    def label(self) -> str:
        if self.is_fixed:
            return f"fixed {self.base:.2%}"
        floor = "off" if self.floor is None else f"{self.floor:g}"
        budget = "off" if self.budget is None else f"{self.budget:.1%}"
        return f"adaptive {self.base:.2%} floor {floor} budget {budget}"

    def adaptive(self, no_budget: float = NO_BUDGET) -> AdaptiveRisk | None:
        """None = fixed risk. A cell with one part off keeps the other: floor 1.0 never
        scales, a budget of `no_budget` x the account never binds."""
        if self.is_fixed:
            return None
        return AdaptiveRisk(
            floor=1.0 if self.floor is None else self.floor,
            daily_budget=no_budget if self.budget is None else self.budget,
        )


def variants(cfg: SweepConfig) -> list[Variant]:
    out = [Variant(b, None, None) for b in cfg.base_risks]
    out += [
        Variant(b, f, d)
        for f in cfg.floors
        for d in cfg.budgets
        if not (f is None and d is None)
        for b in cfg.base_risks
    ]
    return out


# ----- evaluation -----------------------------------------------------------------------


_STATE: dict = {}


def _init(days, orders, mc) -> None:
    _STATE.update(days=days, orders=orders, mc=mc)


def _play(group: tuple) -> list[dict]:
    """One (floor, budget) cell for all base risks in `group[2]`."""
    floor, budget, bases, no_budget = group
    mc = replace(
        _STATE["mc"],
        risk_levels=tuple(bases),
        adaptive=Variant(bases[0], floor, budget).adaptive(no_budget),
    )
    res = ftmo_by_risk(_STATE["days"], _STATE["orders"], mc)
    rows = []
    for base in bases:
        s = res[base]
        v = Variant(base, floor, budget)
        rows.append({
            "label": v.label, "fixed": v.is_fixed, "base": base, "floor": floor, "budget": budget,
            "pass_probability": s["pass_probability"], "attempts": s["attempts"],
            "fail_daily": s["fail_daily"], "fail_max": s["fail_max"],
            "average_days_to_pass": s["average_days_to_pass"],
            "median_days_to_pass": s["median_days_to_pass"],
            "skipped_trades": s["skipped_trades"], "trades_seen": s["trades_seen"],
            "funded_lost_probability": s["funded_lost_probability"],
        })  # fmt: skip
    return rows


def evaluate(
    trades, start: date, end: date, cfg: SweepConfig, wanted: list[Variant], workers: int = 1
) -> list[dict]:
    """The FTMO 2-Step numbers of each variant on the same reshuffled day orders."""
    mc = MonteCarloConfig(runs=cfg.runs, seed=cfg.seed)
    days = build_days(trades, start, end)
    orders = reshuffle_orders(len(days), mc)
    cells: dict = defaultdict(list)
    for v in wanted:
        cells[(v.floor, v.budget)].append(v.base)
    groups = [(f, d, tuple(sorted(b)), cfg.no_budget) for (f, d), b in cells.items()]
    if workers <= 1 or len(groups) == 1:
        _init(days, orders, mc)
        parts = [_play(g) for g in groups]
    else:
        with ProcessPoolExecutor(
            max_workers=min(workers, len(groups)), initializer=_init, initargs=(days, orders, mc)
        ) as pool:
            parts = list(pool.map(_play, groups))
    by_label = {r["label"]: r for part in parts for r in part}
    return [by_label[v.label] for v in wanted]


# ----- selection ------------------------------------------------------------------------


def _days_key(r: dict) -> float:
    d = r["average_days_to_pass"]
    return float("inf") if d is None else d


def pick_best(rows: list[dict], near_tie: float) -> dict:
    """Highest pass probability; among rows within `near_tie` of it the fewest average days
    to pass (never passing = worst), then the label for a stable result."""
    best = max(r["pass_probability"] for r in rows)
    tied = [r for r in rows if r["pass_probability"] >= best - near_tie - 1e-12]
    return min(tied, key=lambda r: (_days_key(r), -r["pass_probability"], r["label"]))


def rank_scores(rows: list[dict]) -> dict[str, float]:
    """Rank by pass probability (1 = best), tied rows share the average rank."""
    ordered = sorted(rows, key=lambda r: -r["pass_probability"])
    ranks: dict[str, float] = {}
    i = 0
    while i < len(ordered):
        j = i
        while (
            j + 1 < len(ordered)
            and ordered[j + 1]["pass_probability"] == ordered[i]["pass_probability"]
        ):
            j += 1
        for k in range(i, j + 1):
            ranks[ordered[k]["label"]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def mean_ranks(per_strategy: dict[str, list[dict]]) -> dict[str, float]:
    ranks = [rank_scores(rows) for rows in per_strategy.values()]
    return {label: sum(r[label] for r in ranks) / len(ranks) for label in ranks[0]}


def universal_pick(per_strategy: dict[str, list[dict]]) -> dict:
    """The variant with the best mean rank over the strategies; ties: higher mean pass
    probability, then the label."""
    ranks = mean_ranks(per_strategy)
    mean_pass: dict[str, float] = defaultdict(float)
    for rows in per_strategy.values():
        for r in rows:
            mean_pass[r["label"]] += r["pass_probability"] / len(per_strategy)
    label = min(ranks, key=lambda x: (ranks[x], -mean_pass[x], x))
    first = next(iter(per_strategy.values()))
    return next(r for r in first if r["label"] == label)


def flat_top(rows: list[dict], bands: tuple[float, ...]) -> dict[float, int]:
    """Variants within each band (pass probability) of the best: many = flat top."""
    best = max(r["pass_probability"] for r in rows)
    return {b: sum(r["pass_probability"] >= best - b - 1e-12 for r in rows) for b in bands}


# ----- the trades per strategy and period -------------------------------------------------


@dataclass(frozen=True, slots=True)
class Plan:
    """What is backtested for one strategy: the config and, per period, symbols and source."""

    strategy: str
    config: object
    dev_symbols: tuple[str, ...]
    test_symbols: tuple[str, ...]
    dev_source: str = "histdata"
    note: str = ""


def forward_config() -> OpeningRangeConfig:
    """Strategy 6 as the demo bot runs it (live/bot.py `forward_strategy_config`)."""
    return OpeningRangeConfig(
        entry_mode=EntryMode.BAND, band_atr=0.25, target_r=0.0, min_rel_volume=1.5
    )


def plans() -> dict[str, Plan]:
    out = {
        "session_zone_sweep": Plan(
            "session_zone_sweep",
            default_config("session_zone_sweep"),
            ("XAUUSD", "GBPUSD", "GBPJPY"),
            ("XAUUSD", "GBPUSD", "GBPJPY"),
        ),
        "ny_index_sweep": Plan(
            "ny_index_sweep",
            default_config("ny_index_sweep"),
            ("NAS100", "US500"),
            ("NAS100", "US500"),
        ),
        "no_wick": Plan("no_wick", default_config("no_wick"), FIVE, FIVE),
        "trend_following": Plan("trend_following", default_config("trend_following"), FIVE, FIVE),
        "gap_fade": Plan(
            "gap_fade", default_config("gap_fade"), ("NAS100", "US500"), ("NAS100", "US500")
        ),
        "gap_momentum": Plan(
            "gap_momentum", default_config("gap_momentum"), ("NAS100", "US500"), ("NAS100", "US500")
        ),
        "opening_range": Plan(
            "opening_range",
            forward_config(),
            ("US30", "US2000"),
            ("US30", "US500", "NAS100", "US2000"),
            dev_source="mt5",
            note="tick-volume filter: dev only on US30 / US2000 (FTMO MT5 before the cut-off, "
            "the only indices with tick volume then); test on the 4 forward symbols",
        ),
    }
    assert set(out) == set(REGISTRY)
    return out


def sources_for(kind: str, symbols) -> SymbolSources:
    """Dev = histdata only (no MT5 day preferred, so the development years stay histdata);
    test = MT5 only."""
    folder = DEFAULT_CACHE_DIR if kind == "histdata" else MT5_CACHE_DIR
    return SymbolSources.single(folder, symbols)


def cache_name(strategy, symbols, start: date, end: date, source: str, settings) -> str:
    key = json.dumps(
        [strategy, sorted(symbols), start.isoformat(), end.isoformat(), source, settings],
        sort_keys=True,
        default=str,
    )
    digest = hashlib.sha1(key.encode()).hexdigest()[:12]
    return f"{strategy}_{start:%Y%m%d}_{end:%Y%m%d}_{source}_{digest}.csv"


@dataclass(frozen=True, slots=True)
class SweepTrade:
    symbol: str
    entry_time: datetime
    exit_time: datetime
    r_gross: float
    r_net: float


def _write_trades(path: Path, trades) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "entry_time", "exit_time", "r_gross", "r_net"])
        for t in trades:
            w.writerow([t.symbol, t.entry_time.isoformat(), t.exit_time.isoformat(),
                        repr(t.r_gross), repr(t.r_net)])  # fmt: skip
    tmp.replace(path)


def _read_trades(path: Path) -> list[SweepTrade]:
    with path.open(newline="", encoding="utf8") as f:
        return [
            SweepTrade(
                r["symbol"], datetime.fromisoformat(r["entry_time"]),
                datetime.fromisoformat(r["exit_time"]), float(r["r_gross"]), float(r["r_net"]),
            )
            for r in csv.DictReader(f)
        ]  # fmt: skip


def trades_for(
    plan: Plan, period: str, cfg: SweepConfig, out: Path, backtest=None, log=print
) -> list[SweepTrade]:
    """The strategy's R trades of `period` ("dev" / "test"), from the cache when present."""
    dev = period == "dev"
    symbols = plan.dev_symbols if dev else plan.test_symbols
    start, end = (cfg.dev_start, cfg.dev_end) if dev else (cfg.cutoff, cfg.test_end)
    source = plan.dev_source if dev else "mt5"
    settings = replace(RunSettings(), strategy=plan.config)
    path = (
        out
        / TRADES_DIR
        / cache_name(plan.strategy, symbols, start, end, source, settings_dict(settings))
    )
    if path.exists():
        trades = _read_trades(path)
        log(f"  {plan.strategy} {period}: {len(trades)} trades from cache")
        return trades
    log(f"  {plan.strategy} {period}: backtest {list(symbols)} {start}..{end} ({source})")
    t0 = clock.time()
    result = (backtest or run_variant)(
        list(symbols), start, end, settings, sources=sources_for(source, symbols),
        workers=cfg.workers,
    )  # fmt: skip
    trades = [SweepTrade(t.symbol, t.entry_time, t.exit_time, t.r_gross, t.r_net)
              for t in result.trades]  # fmt: skip
    _write_trades(path, trades)
    log(f"    {len(trades)} trades in {clock.time() - t0:.0f} s")
    return trades


# ----- the whole sweep ----------------------------------------------------------------------


def sweep(cfg: SweepConfig, names: list[str], out: Path, phase: str = "all", log=print) -> dict:
    all_plans = plans()
    todo = {n: all_plans[n] for n in names}
    grid = variants(cfg)
    result: dict = {
        "config": asdict(cfg), "strategies": {}, "universal": None, "phase": phase,
        "notes": {n: p.note for n, p in todo.items() if p.note},
    }  # fmt: skip
    dev_rows: dict[str, list[dict]] = {}
    dev_trades: dict[str, list] = {}
    for name, plan in todo.items():
        trades = trades_for(plan, "dev", cfg, out, log=log)
        dev_trades[name] = trades
        t0 = clock.time()
        rows = evaluate(trades, cfg.dev_start, cfg.dev_end, cfg, grid, cfg.workers)
        log(f"  {name} dev grid: {len(rows)} variants in {clock.time() - t0:.0f} s")
        dev_rows[name] = rows
        s = {
            "dev_trades": len(trades), "dev_net_r": sum(t.r_net for t in trades),
            "dev_gross_r": sum(t.r_gross for t in trades),
            "dev_variants": rows, "dev_best": pick_best(rows, cfg.near_tie),
            "dev_flat_top": {str(k): v for k, v in flat_top(rows, cfg.flat_bands).items()},
            "dev_meaningful": max(r["pass_probability"] for r in rows) >= cfg.min_meaningful_pass,
        }  # fmt: skip
        result["strategies"][name] = s
    result["universal"] = universal_pick(dev_rows)
    meaningful = {n: r for n, r in dev_rows.items() if result["strategies"][n]["dev_meaningful"]}
    result["universal_meaningful"] = universal_pick(meaningful) if meaningful else None
    result["meaningful_strategies"] = sorted(meaningful)
    if phase == "all":
        for name, plan in todo.items():
            s = result["strategies"][name]
            picks = {"best": s["dev_best"], "universal": result["universal"]}
            if result["universal_meaningful"] is not None:
                picks["universal_meaningful"] = result["universal_meaningful"]
            wanted: list[Variant] = []
            for p in picks.values():
                for v in (
                    Variant(p["base"], p["floor"], p["budget"]),
                    Variant(p["base"], None, None),
                ):
                    if v not in wanted:
                        wanted.append(v)
            trades = trades_for(plan, "test", cfg, out, log=log)
            rows = {
                r["label"]: r
                for r in evaluate(trades, cfg.cutoff, cfg.test_end, cfg, wanted, cfg.workers)
            }
            s["test_trades"] = len(trades)
            s["test_net_r"] = sum(t.r_net for t in trades)
            s["test_gross_r"] = sum(t.r_gross for t in trades)
            s["picks"] = {}
            dev_by = {r["label"]: r for r in dev_rows[name]}
            for kind, p in picks.items():
                base = Variant(p["base"], None, None).label
                s["picks"][kind] = {
                    "label": p["label"], "dev": dev_by[p["label"]], "test": rows[p["label"]],
                    "dev_fixed": dev_by[base], "test_fixed": rows[base],
                }  # fmt: skip
    return result


# ----- output ---------------------------------------------------------------------------------


def _pct(x) -> str:
    return "-" if x is None else f"{x * PERCENT:.1f}%"


def _num(x, digits: int = 1) -> str:
    return "-" if x is None else f"{x:.{digits}f}"


def _row_cells(r: dict) -> str:
    return (
        f"{_pct(r['pass_probability'])} | {r['fail_daily']} / {r['fail_max']} | "
        f"{_num(r['average_days_to_pass'])} / {_num(r['median_days_to_pass'])} | "
        f"{r['skipped_trades']} | {_pct(r['funded_lost_probability'])}"
    )


HEAD = "pass | fails daily / max | days to pass avg / median | skipped | funded lost"


def _strategy_section(name: str, s: dict, cfg: dict) -> list[str]:
    text = (
        f"Development: {s['dev_trades']} trades, {s['dev_gross_r']:+.1f} R gross, "
        f"{s['dev_net_r']:+.1f} R net."
    )
    if "test_trades" in s:
        text += (
            f" Test: {s['test_trades']} trades, {s['test_gross_r']:+.1f} R gross, "
            f"{s['test_net_r']:+.1f} R net."
        )
    lines = [f"## {name}", "", text, ""]
    if not s["dev_meaningful"]:
        limit = _pct(cfg["min_meaningful_pass"])
        lines += [
            (
                f"_No variant passes more than {limit} on the development period: the optimum "
                "below is noise, not a result._"
            ),
            "",
        ]
    top = sorted(s["dev_variants"], key=lambda r: (-r["pass_probability"], _days_key(r)))[:5]
    bands = " / ".join(_pct(float(k)) for k in s["dev_flat_top"])
    counts = " / ".join(str(v) for v in s["dev_flat_top"].values())
    lines += [
        (
            f"Top 5 on the development period. Variants within {bands} of the best: {counts} "
            f"(of {len(s['dev_variants'])})."
        ),
        "",
        f"| variant | {HEAD} |",
        "|---|---|---|---|---|---|",
    ]
    lines += [f"| {r['label']} | {_row_cells(r)} |" for r in top]
    if "picks" in s:
        lines += [
            "",
            "Picks, development vs test (never tuned on the test period):",
            "",
            f"| pick | period | variant | {HEAD} |",
            "|---|---|---|---|---|---|---|",
        ]
        for kind, p in s["picks"].items():
            for period in ("dev", "test"):
                base = p[f"{period}_fixed"]
                lines.append(f"| {kind} | {period} | {p['label']} | {_row_cells(p[period])} |")
                lines.append(
                    f"| {kind} | {period} | baseline {base['label']} | {_row_cells(base)} |"
                )
    return [*lines, ""]


def report(res: dict) -> str:
    cfg = res["config"]
    lines = [
        "# Adaptive risk variant sweep (ROADMAP 5.7 part 2)",
        "",
        (
            f"Development {cfg['dev_start']} to the day before {cfg['cutoff']}, test "
            f"{cfg['cutoff']} to {cfg['test_end']}; {cfg['runs']} reshuffles, seed {cfg['seed']}, "
            "the same day orders for every variant of a strategy and period. FTMO 2-Step, "
            "funded account watched 126 days."
        ),
        "",
        (
            "Selection runs on the development period only; the picks are played once on the "
            "test period."
        ),
        "",
    ]
    lines += [f"- {name}: {note}" for name, note in res.get("notes", {}).items()]
    lines.append("")
    for name, s in res["strategies"].items():
        lines += _strategy_section(name, s, cfg)
    lines += [
        f"## Universal variant (best mean rank over all strategies): {res['universal']['label']}",
        "",
    ]
    if res.get("universal_meaningful"):
        names = ", ".join(res["meaningful_strategies"])
        lines += [
            (
                f"Over the strategies with a real optimum ({names}): "
                f"{res['universal_meaningful']['label']}"
            ),
            "",
        ]
    return "\n".join(lines) + "\n"


def write_outputs(res: dict, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "summary.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf8")
    cols = ["strategy", "period", "label", "fixed", "base", "floor", "budget", "pass_probability",
            "attempts", "fail_daily", "fail_max", "average_days_to_pass", "median_days_to_pass",
            "skipped_trades", "trades_seen", "funded_lost_probability"]  # fmt: skip
    with (folder / "variants.csv").open("w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for name, s in res["strategies"].items():
            for r in s["dev_variants"]:
                w.writerow({"strategy": name, "period": "dev", **r})
            for p in s.get("picks", {}).values():
                w.writerow({"strategy": name, "period": "test", **p["test"]})
                w.writerow({"strategy": name, "period": "test", **p["test_fixed"]})
    (folder / "report.md").write_text(report(res), encoding="utf8")


def lower_priority() -> None:
    """Below-normal process priority (children inherit it): the live bot runs on this PC."""
    try:
        if sys.platform == "win32":
            import ctypes

            below_normal = 0x00004000
            kernel = ctypes.windll.kernel32
            kernel.GetCurrentProcess.restype = ctypes.c_void_p
            kernel.SetPriorityClass.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
            kernel.SetPriorityClass(kernel.GetCurrentProcess(), below_normal)
        else:
            os.nice(10)
    except OSError:
        pass


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m backtester.tools.risk_sweep", description=__doc__)
    p.add_argument("--strategies", nargs="+", choices=tuple(REGISTRY), default=list(REGISTRY))
    p.add_argument("--runs", type=int, default=SweepConfig().runs, help="reshuffles per variant")
    p.add_argument("--workers", type=int, default=SweepConfig().workers)
    p.add_argument("--phase", choices=("dev", "all"), default="all")
    p.add_argument("--out", type=Path, default=RESULTS_DIR / SWEEP_DIR)
    p.add_argument("--stamp", default=None, help="output folder name (default: today)")
    p.add_argument("--no-lower-priority", action="store_true")
    args = p.parse_args(argv)
    if not args.no_lower_priority:
        lower_priority()
    cfg = SweepConfig(runs=args.runs, workers=args.workers)
    stamp = args.stamp or datetime.now(UTC).date().isoformat()
    t0 = clock.time()
    res = sweep(cfg, args.strategies, args.out, args.phase)
    folder = args.out / stamp
    write_outputs(res, folder)
    print(f"done in {clock.time() - t0:.0f} s: {folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
