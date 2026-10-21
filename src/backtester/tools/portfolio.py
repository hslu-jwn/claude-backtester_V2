"""Portfolio tool: several components as one weighted account, reported like a Monte Carlo run.

    python -m backtester.tools.portfolio components.json --start 2021-09-14 --end 2026-10-19 \\
        --cache-dir data/cache/mt5 --spread-table data/spreads/ftmo_spread_median.json \\
        --family portfolio_first

Components file (JSON):

    {"components": [
      {"name": "orb", "strategy": "opening_range", "symbols": ["US30", "NAS100"],
       "set": {"entry_mode": "band", "band_atr": 0.25, "min_rel_volume": 1.5},
       "families": ["opening_range", "screen_opening_range"]},
      {"name": "gold", "strategy": "gap_momentum", "symbols": ["XAUUSD"],
       "set": {"mode": "fx", "exit_time": "11:00"}, "families": ["gap_momentum*"]}
    ]}

`strategy` is a registry name; `set` overrides its spec defaults (same rules as `--set` of
`tools.monte_carlo`: numbers, booleans, HH:MM times, enum values); `families` are the trial-log
families (a `*` is a wildcard) whose trials count in N of the deflated Sharpe (default: the
strategy name). All components share one period and one candle cache.

Each component is backtested once (plus the kind B alternative where the strategy has one:
gap_fade, gap_momentum); the trade lists are weighted equally (never optimised) and merged; the
Monte Carlo report machinery runs on the merged list. Kind B and C are drawn per component and
added with the same weights; a component without a kind B variant stays at its actual result in
every kind B run (only the others are randomised); kind B is n/a when none has one. Kind D is not
part of the portfolio report. N and V of the deflated Sharpe come from the trial-log lines of all
component families (this run's own line, family `--family`, is written after and not counted).
The components' own backtests are not logged again.

Writes `<out>/report.html` and `<out>/summary.json`; default `<out>` is `results/portfolio/<family>/`.

Spec: risk-management.md > Portfolio tool (ROADMAP 12.9). Research only: changes no setting.
"""

from __future__ import annotations

import argparse
import json
import time as clock
from dataclasses import dataclass, field, replace
from datetime import date
from pathlib import Path

import numpy as np

from backtester.analytics import portfolio as pf
from backtester.analytics.daily import daily_net_r
from backtester.analytics.deflated_sharpe import (
    DeflatedSharpeConfig,
    deflated_sharpe,
    trade_stats,
)
from backtester.analytics.portfolio import PortfolioConfig
from backtester.analytics.random_baseline import (
    HIGH_PCT,
    LOW_PCT,
    PERCENT,
    RandomBaselineConfig,
    RandomBaselineResult,
    random_entry_baseline,
)
from backtester.analytics.random_fills import RandomFillsConfig, RandomFillsResult, random_fills
from backtester.analytics.trial_log import append, default_path, make_record, settings_dict
from backtester.analytics.verdict import period_halves, t_statistic
from backtester.data.cache import MT5_CACHE_DIR
from backtester.data.sources import SymbolSources
from backtester.engine.spread_table import SpreadTable
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.registry import REGISTRY, default_config
from backtester.tools import monte_carlo as mc
from backtester.tools.monte_carlo import ALTERNATIVES, ToolConfig, apply_overrides, esc, fmt, table

PORTFOLIO_DIR = "portfolio"


@dataclass(frozen=True, slots=True)
class Component:
    name: str
    strategy: str
    symbols: list[str]
    config: object  # the strategy's config dataclass with the overrides applied
    families: list[str]
    overrides: dict = field(default_factory=dict)


def load_components(path: Path) -> list[Component]:
    """The components of a JSON file; anything wrong stops with a message (SystemExit)."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        raw = data["components"]
    except (OSError, ValueError, KeyError, TypeError) as e:
        raise SystemExit(f"{path}: cannot read a components file ({e})") from None
    if not isinstance(raw, list) or not raw:
        raise SystemExit(f"{path}: 'components' must be a non-empty list")
    out: list[Component] = []
    for item in raw:
        name = str(item.get("name", "")).strip()
        strategy = item.get("strategy")
        symbols = [str(s).upper() for s in item.get("symbols", [])]
        if not name or any(c.name == name for c in out):
            raise SystemExit(f"{path}: every component needs a unique name (got {name!r})")
        if strategy not in REGISTRY:
            raise SystemExit(f"{path}: component {name}: unknown strategy {strategy!r}")
        if not symbols:
            raise SystemExit(f"{path}: component {name}: no symbols")
        overrides = dict(item.get("set") or {})
        items = [
            f"{k}={str(v).lower() if isinstance(v, bool) else v}" for k, v in overrides.items()
        ]
        config = apply_overrides(default_config(strategy), items)
        out.append(Component(name, strategy, symbols, config, list(item.get("families") or [strategy]), overrides))  # fmt: skip
    return out


# ----- running -------------------------------------------------------------------------------


def run_component(comp: Component, start: date, end: date, sources, engine, log=print):
    """(settings, trades, kind B alternative trades or None) of one component."""
    settings = replace(RunSettings(), strategy=comp.config, engine=engine)
    log(f"backtest {comp.name}: {comp.strategy} {comp.symbols} {start}..{end}")
    trades = list(
        run_backtests(comp.symbols, start, end, settings, sources=sources, workers=1).trades
    )
    log(f"  {len(trades)} trades")
    follow = None
    if comp.strategy in ALTERNATIVES:
        field_, value = ALTERNATIVES[comp.strategy]
        log(f"  kind B alternative: {field_}={value}")
        alt = replace(settings, strategy=replace(comp.config, **{field_: value}))
        follow = list(
            run_backtests(comp.symbols, start, end, alt, sources=sources, workers=1).trades
        )
    return settings, trades, follow


def combined_baseline(parts, scales, runs: int, seed: int) -> RandomBaselineResult | None:
    """Kind B of the portfolio: the components with an alternative are randomised (seed + index),
    the others stay at their actual net R; every part is scaled by its weight. None when no
    component has an alternative."""
    total = np.zeros(runs)
    strategy_net, days, any_b = 0.0, 0, False
    for k, ((trades, follow), scale) in enumerate(zip(parts, scales, strict=True)):
        if follow is None:
            const = sum(t.r_net for t in trades) * scale
            total += const
            strategy_net += const
            continue
        any_b = True
        res = random_entry_baseline(trades, follow, RandomBaselineConfig(runs, seed + k))
        total += np.array(res.run_net_r) * scale
        strategy_net += res.strategy_net_r * scale
        days += res.days
    if not any_b:
        return None
    return RandomBaselineResult(
        strategy_net, tuple(float(x) for x in total),
        float((total < strategy_net).mean() * PERCENT), float(total.mean()),
        float(np.percentile(total, LOW_PCT)), float(np.percentile(total, HIGH_PCT)), days,
    )  # fmt: skip


def combined_fills(parts, scales, costs, runs: int, seed: int) -> RandomFillsResult:
    """Kind C of the portfolio: random fills per component (seed + index), added with the weights."""
    total, base = np.zeros(runs), 0.0
    for k, (trades, scale) in enumerate(zip(parts, scales, strict=True)):
        res = random_fills(trades, RandomFillsConfig(runs, seed + k), costs)
        total += np.array(res.run_net_r) * scale
        base += res.base_net_r * scale
    p5, p50, p95 = np.percentile(total, [LOW_PCT, 50.0, HIGH_PCT])
    return RandomFillsResult(
        base, tuple(float(x) for x in total), float(p5), float(p50), float(p95)
    )


def analyse(args: argparse.Namespace, config: ToolConfig, pcfg: PortfolioConfig, log=print) -> dict:
    comps = load_components(args.components)
    symbols = list(dict.fromkeys(s for c in comps for s in c.symbols))
    sources = SymbolSources.single(args.cache_dir, symbols)
    engine = RunSettings().engine
    if args.spread_table is not None:
        spread = SpreadTable.from_dict(json.loads(args.spread_table.read_text(encoding="utf-8")))
        engine = replace(engine, costs=replace(engine.costs, spread_table=spread))
        log(f"spread table: {spread.stat} by year and New York hour, {spread.note}")
    runs = [run_component(c, args.start, args.end, sources, engine, log) for c in comps]
    own = {c.name: r[1] for c, r in zip(comps, runs, strict=True)}

    log("combining")
    res = pf.combine(own, args.start, args.end, pcfg)
    merged = res.trades
    scales = [w * res.idm_applied for w in res.weights]
    paths = [args.trials, *args.trials_extra]
    patterns = [c.families for c in comps]
    n_trials, sharpes = pf.component_trials(patterns, paths)
    counts = pf.family_counts(patterns, paths)
    deflated = deflated_sharpe(
        trade_stats(daily_net_r(merged, args.start, args.end)),
        n_trials,
        sharpes,
        DeflatedSharpeConfig(),
    )
    log(f"trial log: component families {counts}, N = {n_trials}, {len(sharpes)} daily Sharpes")
    append(make_record(
        args.family, "portfolio",
        {"components": [{"name": c.name, "strategy": c.strategy, "settings": settings_dict(c.config)}
                        for c in comps],
         "weights": res.weights, "apply_idm": pcfg.apply_idm},
        symbols, args.start, args.end, args.source, merged,
    ), args.trials)  # fmt: skip

    log("kind B: random entries per component")
    baseline = combined_baseline([(r[1], r[2]) for r in runs], scales, config.runs, config.seed)
    log("kind C: random fills per component")
    costs = runs[0][0].engine.costs.symbols
    fills = combined_fills([r[1] for r in runs], scales, costs, config.runs, config.seed)
    meta = {"strategy": "portfolio", "symbols": symbols, "start": args.start, "end": args.end,
            "source": args.source}  # fmt: skip
    summary = mc.build_summary(
        merged, None, meta, runs[0][0], config, None, log, deflated, args.family,
        baseline=baseline, fills=fills,
    )  # fmt: skip
    summary["portfolio"] = portfolio_block(comps, runs, res, pcfg, counts, args)
    return summary


def portfolio_block(comps, runs, res, pcfg, counts, args) -> dict:
    rows = []
    for c, (_, trades, follow), stat in zip(comps, runs, res.component_stats, strict=True):
        rs = [t.r_net for t in trades]
        first, second = period_halves(trades, args.start, args.end)
        rows.append({
            **stat, "strategy": c.strategy, "symbols": c.symbols, "families": c.families,
            "gross_r": sum(t.r_gross for t in trades), "t_stat": t_statistic(rs),
            "half_first_net_r": first, "half_second_net_r": second,
            "has_kind_b": follow is not None,
        })  # fmt: skip
    pairs = [
        {"a": res.names[i], "b": res.names[j], "whole": res.corr[i][j], **v}
        for (i, j), v in res.rolling.items()
    ]
    return {
        "components": rows, "names": res.names, "weights": res.weights,
        "correlation": res.corr, "rolling": pairs, "window_days": pcfg.window_days,
        "idm": res.idm, "idm_cap": pcfg.idm_cap, "apply_idm": pcfg.apply_idm,
        "idm_applied": res.idm_applied, "trial_families": counts,
        "kind_b_components": [r["name"] for r in rows if r["has_kind_b"]],
    }  # fmt: skip


# ----- report.html ---------------------------------------------------------------------------


def components_html(summary: dict) -> str:
    p = summary["portfolio"]
    rob = summary["robustness"]
    n = summary["meta"]["trades"]
    rows = []
    for c in p["components"]:
        rows.append([
            c["name"], c["strategy"], ", ".join(c["symbols"]), f"{c['weight']:.3f}",
            str(c["trades"]), fmt(c["net_r"], "+.1f"), fmt(c["r_per_trade"], "+.3f"),
            fmt(c["t_stat"]), f"{c['half_first_net_r']:+.1f} / {c['half_second_net_r']:+.1f}",
            fmt(c["weighted_net_r"], "+.1f"),
        ])  # fmt: skip
    rows.append([
        "COMBINATION", "portfolio", "", "1.000", str(n), fmt(rob["net_r"], "+.1f"),
        fmt(rob["mean_net_r"], "+.3f"), fmt(rob["t_stat"]),
        f"{rob['half_first_net_r']:+.1f} / {rob['half_second_net_r']:+.1f}",
        fmt(rob["net_r"], "+.1f"),
    ])  # fmt: skip
    head = ["Component", "Strategy", "Symbols", "Weight", "Trades", "Own net R", "R / trade",
            "t", "Halves (own R)", "Net R in account"]  # fmt: skip
    return mc.section(
        "Components and the combination",
        "each component's own numbers (unweighted R) next to the combination: the account R "
        "per trade is the Monte Carlo risk x weight; 'Net R in account' is own net R x weight"
        + (" x IDM" if p["apply_idm"] else "")
        + ". The halves split at the middle of the period.",
        table(head, rows),
    )


def correlation_html(summary: dict) -> str:
    p = summary["portfolio"]
    names = p["names"]
    rows = [[names[i], *[f"{v:+.2f}" for v in row]] for i, row in enumerate(p["correlation"])]
    whole = table(["", *names], rows)
    pair_rows = [
        [f"{r['a']} / {r['b']}", f"{r['whole']:+.2f}", str(r["windows"]),
         fmt(r["min"], "+.2f"), fmt(r["median"], "+.2f"), fmt(r["max"], "+.2f")]
        for r in p["rolling"]
    ]  # fmt: skip
    rolling = table(
        ["Pair", "Whole period", "Windows", "Rolling min", "Rolling median", "Rolling max"],
        pair_rows,
    )
    idm_note = (
        f"<p>IDM = 1 / sqrt(w' H w) = <b>{p['idm']:.2f}</b> (cap {p['idm_cap']:g}, negatives "
        f"floored at 0). Applied to the account list: "
        f"<b>{'yes, x' + format(p['idm_applied'], '.2f') if p['apply_idm'] else 'no'}</b> "
        "(off by default: it raises the risk).</p>"
    )
    return mc.section(
        "Correlation of the daily R and IDM",
        f"daily net R per FTMO day (midnight Prague, trades by exit day), correlation over the "
        f"whole period and in rolling {p['window_days']}-trading-day windows; a lower value means "
        "more diversification. Days without trades count as 0 R.",
        whole + rolling + idm_note,
    )


def trials_html(summary: dict) -> str:
    p = summary["portfolio"]
    rows = [[fam, str(n)] for fam, n in p["trial_families"].items()]
    rows.append(["N (sum)", str(sum(p["trial_families"].values()))])
    return mc.section(
        "Trial families behind N",
        "N of the deflated Sharpe is the sum of the trials logged in all component families; V "
        "comes from all their daily Sharpes. This portfolio's own line (family "
        f"{summary['meta']['family']}) is written after and not counted.",
        table(["Family", "Trials"], rows),
    )


def render_report(summary: dict) -> str:
    p = summary["portfolio"]
    note = (
        f"<p class='how'>Kind B randomises {esc(', '.join(p['kind_b_components']))}; the other "
        "components stay at their actual result.</p>"
        if p["kind_b_components"]
        else ""
    )
    body = "".join((
        mc.verdict_html(summary), mc.deflated_html(summary), trials_html(summary),
        components_html(summary), correlation_html(summary), mc.fan_html(summary),
        mc.numbers_html(summary), mc.ftmo_html(summary), mc.random_entries_html(summary), note,
        mc.random_fills_html(summary), mc.robustness_html(summary),
    ))  # fmt: skip
    m = summary["meta"]
    title = f"Portfolio {m['family']}: {' + '.join(p['names'])}"
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{esc(title)}</title><style>{mc.CSS}</style></head><body><main>"
        f"<h1>{esc(title)}</h1>{body}</main></body></html>"
    )


# ----- command line --------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    d, pd = ToolConfig(), PortfolioConfig()
    p = argparse.ArgumentParser(prog="python -m backtester.tools.portfolio", description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)  # fmt: skip
    p.add_argument("components", type=Path, help="components JSON file (format above)")
    p.add_argument("--start", type=date.fromisoformat, required=True, help="first UTC day")
    p.add_argument("--end", type=date.fromisoformat, required=True, help="last UTC day")
    p.add_argument("--cache-dir", type=Path, default=MT5_CACHE_DIR,
                   help="candle cache for every symbol (read only; default: FTMO MT5 cache)")  # fmt: skip
    p.add_argument("--source", default="mt5", help="source label for the trial log (default mt5)")
    p.add_argument("--spread-table", type=Path, default=None,
                   help="spread by year and New York hour (JSON); without it: fixed spread")  # fmt: skip
    p.add_argument("--family", default="portfolio", help="trial-log family of this run's own line")
    p.add_argument("--trials", type=Path, default=None,
                   help="trial log to read and append to (default results/trials.jsonl)")  # fmt: skip
    p.add_argument("--trials-extra", type=Path, nargs="*", default=[],
                   help="more trial logs, read only (another checkout's log)")  # fmt: skip
    p.add_argument("--runs", type=int, default=d.runs, help="runs for kinds A, B and C")
    p.add_argument("--seed", type=int, default=d.seed)
    p.add_argument("--window-days", type=int, default=pd.window_days,
                   help="rolling correlation window in trading days")  # fmt: skip
    p.add_argument("--apply-idm", action="store_true",
                   help="multiply the account list by the IDM (off by default)")  # fmt: skip
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args(argv)
    args.trials = args.trials or default_path()
    return args


def default_out(args: argparse.Namespace) -> Path:
    return RESULTS_DIR / PORTFOLIO_DIR / args.family


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = ToolConfig(runs=args.runs, seed=args.seed, paths=0)
    pcfg = PortfolioConfig(window_days=args.window_days, apply_idm=args.apply_idm)
    out = args.out or default_out(args)
    t0 = clock.time()
    summary = analyse(args, config, pcfg)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.html").write_text(render_report(summary), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(mc.jsonable(summary), indent=1), encoding="utf-8")
    v = summary["verdict"]
    print(f"\nVERDICT: {v.label}. {v.reason}")
    print(f"written to {out} ({clock.time() - t0:.0f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
