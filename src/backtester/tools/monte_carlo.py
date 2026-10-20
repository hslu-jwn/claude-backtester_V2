"""Monte Carlo report: one backtest run through all four kinds of Monte Carlo and a verdict.

    python -m backtester.tools.monte_carlo NAS100 US500 --start 2020-01-01 --end 2021-09-13 \\
        --strategy gap_fade
    python -m backtester.tools.monte_carlo NAS100 --start 2021-09-15 --end 2026-09-30 \\
        --strategy gap_fade --source mt5 --paths 0
    python -m backtester.tools.monte_carlo NAS100 US500 --start 2015-01-01 --end 2021-09-13 \\
        --strategy gap_momentum --family gap_momentum_index --set entry_z=0.1 exit_time=12:00

Runs the strategy (spec defaults, shared costs), then: kind A day reshuffle + FTMO 2-Step at
0.5 / 1 / 1.5 % risk, kind B random entries (only the gap fade, "follow" variant, and the gap
momentum, "fade" side, have one; other strategies show "not available for this strategy yet" and
the verdict check is n/a), kind C random fills, kind D seeded random-walk paths (`--paths`, 0
skips; the volatility profile is measured on the same days as the run), and the robustness
measures. Writes `<out>/report.html` (Plotly from the CDN) and `<out>/summary.json`; default
`<out>` is `results/monte_carlo/<strategy>_<symbols>_<start>_<end>/`.

Spec: risk-management.md > Monte Carlo report (ROADMAP 12.7). Research only: changes no setting.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import tempfile
import time as clock
from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from datetime import date, time
from pathlib import Path

from backtester.analytics.deflated_sharpe import (
    DeflatedResult,
    DeflatedSharpeConfig,
    deflated_sharpe,
    trade_stats,
)
from backtester.analytics.random_baseline import RandomBaselineConfig, random_entry_baseline
from backtester.analytics.random_fills import RandomFillsConfig, random_fills
from backtester.analytics.robustness import RobustnessConfig, trade_robustness
from backtester.analytics.trial_log import (
    append,
    family_summary,
    family_trials,
    make_record,
)
from backtester.analytics.verdict import (
    VerdictConfig,
    VerdictInputs,
    evaluate,
    middle_date,
    period_halves,
    t_statistic,
)
from backtester.data.cache import MT5_CACHE_DIR
from backtester.data.random_walk import RandomWalkConfig, load_profile, write_path
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.paths import RESULTS_DIR
from backtester.risk.monte_carlo import MonteCarloConfig, run_monte_carlo
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.registry import REGISTRY, default_config

# strategies with a kind B alternative on the same days: (setting, value) of the other choice
ALTERNATIVES = {"gap_fade": ("mode", "follow"), "gap_momentum": ("side", "fade")}
PERCENT = 100.0
MONTE_CARLO_DIR = "monte_carlo"
NOT_AVAILABLE = "not available for this strategy yet"


@dataclass(frozen=True, slots=True)
class ToolConfig:
    runs: int = 1000  # kinds A, B and C (spec: 1,000)
    seed: int = 42  # spec: every random draw seeded with 42
    paths: int = 20  # kind D paths per symbol (spec: 20); 0 = skip
    # kind D warning: mean net R per trade on random paths above this is a bug warning. The
    # spec says "clearly more than minus the mean cost"; clearly = above 0 net (Claude, 2026-10-15)
    warn_net_r: float = 0.0


# ----- kind D ------------------------------------------------------------------------------


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def path_row(symbol: str, trades, paths: int, config: ToolConfig) -> dict:
    """Kind D numbers of one symbol (trades of all its paths): net R per trade against the
    mean cost per trade (`r_gross - r_net`, spread + commission + swap); warning above
    `config.warn_net_r`."""
    net = _mean([t.r_net for t in trades])
    cost = _mean([t.r_gross - t.r_net for t in trades])
    return {
        "symbol": symbol,
        "paths": paths,
        "trades": len(trades),
        "trades_per_path": len(trades) / paths if paths else 0.0,
        "mean_net_r": net,
        "mean_cost_r": cost,
        "expected_net_r": None if cost is None else -cost,
        "warning": net is not None and net > config.warn_net_r,
    }


def random_paths(
    symbols, settings: RunSettings, sources: SymbolSources, start: date, end: date,
    config: ToolConfig, log=print,
) -> dict:  # fmt: skip
    """Run the strategy on `config.paths` random-walk paths per symbol (profile measured on
    the run's own days) and report each symbol's net R per trade."""
    walk = RandomWalkConfig(paths=config.paths, seed=config.seed)
    rows = []
    for symbol in symbols:
        profile = load_profile(symbol, sources.cache_dir(symbol), start, end)
        trades: list = []
        for k in range(config.paths):
            with tempfile.TemporaryDirectory(prefix=f"mc_path_{symbol}_") as tmp:
                path_sources = write_path(profile, symbol, k, Path(tmp), walk)
                result = run_backtests(
                    [symbol], walk.start, walk.end, settings, sources=path_sources, workers=1
                )
            trades += list(result.trades)
            log(f"  {symbol} path {k + 1}/{config.paths}: {len(result.trades)} trades")
        rows.append(path_row(symbol, trades, config.paths, config))
    return {
        "rows": rows, "warning": any(r["warning"] for r in rows),
        "years": walk.years, "start": walk.start, "end": walk.end,
    }  # fmt: skip


# ----- analysis ----------------------------------------------------------------------------


def verdict_inputs(
    trades, baseline, fills, rcfg: RobustnessConfig, start: date, end: date,
    dsr: float | None = None,
) -> VerdictInputs:  # fmt: skip
    rob = trade_robustness(trades, rcfg)
    rs = [t.r_net for t in trades]
    first, second = period_halves(trades, start, end)
    return VerdictInputs(
        mean_r=_mean(rs),
        t=t_statistic(rs),
        percentile=None if baseline is None else baseline.percentile,
        half_first_net=first,
        half_second_net=second,
        stressed_net=rob["net_r_stressed"],
        net_without_best=rob["net_r_without_best"],
        fill_median=fills.p50,
        dsr=dsr,
    )


def build_summary(
    trades, follow_trades, meta: dict, settings: RunSettings, config: ToolConfig,
    paths: dict | None = None, log=print, deflated: DeflatedResult | None = None,
    family: str | None = None,
) -> dict:  # fmt: skip
    """The report numbers of a ready trade list. `meta` needs strategy, symbols, start, end and
    source. `follow_trades` (kind B alternative, same days) None = kind B not available; `paths`
    (kind D result) None = skipped; `deflated` (ROADMAP 12.10) None = check 7 is n/a."""
    start, end = meta["start"], meta["end"]
    rcfg = RobustnessConfig()
    trades = list(trades)
    baseline = None
    if follow_trades is not None:
        baseline = random_entry_baseline(
            trades, list(follow_trades), RandomBaselineConfig(config.runs, config.seed)
        )
    log("kind C: random fills")
    fills = random_fills(
        trades, RandomFillsConfig(config.runs, config.seed), settings.engine.costs.symbols
    )
    log("kind A: day reshuffle + FTMO")
    mc = run_monte_carlo(trades, start, end, MonteCarloConfig(config.runs, config.seed))
    inputs = verdict_inputs(
        trades, baseline, fills, rcfg, start, end, None if deflated is None else deflated.dsr
    )
    verdict = evaluate(inputs, VerdictConfig())
    rob = trade_robustness(trades, rcfg)
    first, second = period_halves(trades, start, end)
    mid = middle_date(start, end)
    rs = [t.r_net for t in trades]
    return {
        "meta": {
            **meta,
            "runs": config.runs,
            "seed": config.seed,
            "paths": config.paths if paths is not None else 0,
            "trades": len(trades),
            "family": family,
        },
        "verdict": verdict,
        "deflated": None if deflated is None else {**asdict(deflated), "family": family},
        "robustness": {
            **rob,
            "half_first_net_r": first,
            "half_second_net_r": second,
            "half_first_trades": sum(t.entry_time.date() <= mid for t in trades),
            "half_second_trades": sum(t.entry_time.date() > mid for t in trades),
            "half_split_date": mid,
            "mean_net_r": _mean(rs),
            "t_stat": inputs.t,
            "cost_stress": rcfg.cost_stress,
        },
        "random_entries": (
            {"available": False, "note": NOT_AVAILABLE}
            if baseline is None
            else {"available": True, **asdict(baseline)}
        ),
        "random_fills": asdict(fills),
        "monte_carlo": mc,
        "random_paths": paths,
    }


def apply_overrides(config, items: list[str]):
    """`config` with `key=value` items applied (types from the setting's current value; a time
    setting is HH:MM). Research use: run one variant of a sweep. Unknown key: SystemExit."""
    known = {f.name for f in fields(config)}
    changes = {}
    for item in items:
        key, sep, text = item.partition("=")
        if not sep or key not in known:
            raise SystemExit(f"--set {item!r}: expected key=value with a setting of the strategy: "
                             f"{', '.join(sorted(known))}")  # fmt: skip
        current = getattr(config, key)
        if key.endswith("_time") or isinstance(current, time):
            changes[key] = time.fromisoformat(text)
        elif isinstance(current, bool):
            changes[key] = text.lower() in ("1", "true", "yes")
        elif isinstance(current, int):
            changes[key] = int(text)
        elif isinstance(current, float):
            changes[key] = float(text)
        else:
            changes[key] = text
    return replace(config, **changes)


def analyse(args: argparse.Namespace, config: ToolConfig, log=print) -> dict:
    symbols = [s.upper() for s in args.symbols]
    if args.cache_dir is not None:
        sources = SymbolSources.single(args.cache_dir, symbols)
    elif args.source == "histdata":
        sources = DEFAULT_SOURCES
    else:
        sources = SymbolSources.single(MT5_CACHE_DIR, symbols)
    strategy_cfg = apply_overrides(default_config(args.strategy), args.set or [])
    settings = replace(RunSettings(), strategy=strategy_cfg)

    log(f"backtest {args.strategy} {symbols} {args.start}..{args.end}")
    base = run_backtests(symbols, args.start, args.end, settings, sources=sources)
    trades = list(base.trades)
    log(f"  {len(trades)} trades")

    family = args.family or args.strategy
    append(make_record(
        family, args.strategy, strategy_cfg, symbols, args.start, args.end, args.source,
        [t.r_net for t in trades],
    ))  # fmt: skip
    n_trials, sharpes = family_summary(family_trials(family))
    deflated = deflated_sharpe(
        trade_stats([t.r_net for t in trades]), n_trials, sharpes, DeflatedSharpeConfig()
    )
    log(f"trial log: family {family}, N = {n_trials}")

    follow = None
    if args.strategy in ALTERNATIVES:
        field, value = ALTERNATIVES[args.strategy]
        log(f"kind B: {field}={value} run")
        follow = list(run_backtests(
            symbols, args.start, args.end,
            replace(settings, strategy=replace(strategy_cfg, **{field: value})), sources=sources,
        ).trades)  # fmt: skip
    paths = None
    if config.paths > 0:
        log("kind D: random price paths")
        paths = random_paths(symbols, settings, sources, args.start, args.end, config, log)
    meta = {
        "strategy": args.strategy, "symbols": symbols, "start": args.start, "end": args.end,
        "source": args.source,
    }  # fmt: skip
    summary = build_summary(trades, follow, meta, settings, config, paths, log, deflated, family)
    summary["meta"]["paths"] = config.paths
    return summary


# ----- summary.json ------------------------------------------------------------------------


def jsonable(value):
    """Plain JSON types: dataclasses as dicts, dates as ISO text, inf / nan as null."""
    if is_dataclass(value) and not isinstance(value, type):
        return jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [jsonable(v) for v in value]
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


# ----- report.html -------------------------------------------------------------------------

LABEL_COLOURS = {"EDGE": "#1a7f37", "WEAK": "#b7791f", "NO EDGE": "#c0392b"}
CSS = """
:root{--bg:#fff;--fg:#1c2330;--muted:#5b6575;--line:#d8dde5;--card:#f6f8fa}
@media (prefers-color-scheme:dark){:root{--bg:#10151c;--fg:#e6e9ee;--muted:#9aa4b2;
--line:#2c3542;--card:#171e28}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:16px}
h1{font-size:20px;margin:8px 0}h2{font-size:17px;margin:28px 0 4px}
.banner{color:#fff;border-radius:8px;padding:16px 20px;margin:12px 0}
.banner .big{font-size:34px;font-weight:700;letter-spacing:.02em}
.banner .why{font-size:15px;margin-top:4px}
.warn{background:#fff3cd;color:#664d03;border-radius:6px;padding:8px 12px;margin:8px 0}
table{border-collapse:collapse;width:100%;margin:8px 0;background:var(--card)}
th,td{border:1px solid var(--line);padding:5px 9px;text-align:right}
th:first-child,td:first-child{text-align:left}th{font-weight:600}
td.pass{color:#1a7f37;font-weight:600}td.fail{color:#c0392b;font-weight:600}
td.na{color:var(--muted)}
.how{color:var(--muted);font-size:13px;margin:2px 0 8px}
.meta{color:var(--muted);font-size:13px}
@media (max-width:640px){main{padding:12px}th,td{padding:4px 6px;font-size:13px}}
"""


def esc(x) -> str:
    return html.escape(str(x))


def fmt(v, spec: str = ".2f", suffix: str = "") -> str:
    return "-" if v is None else format(v, spec) + suffix


def table(head: list[str], rows: list[list[str]], classes: dict | None = None) -> str:
    """HTML table; `classes[(row, col)]` is a CSS class for one cell."""
    classes = classes or {}
    out = ["<table><tr>" + "".join(f"<th>{esc(h)}</th>" for h in head) + "</tr>"]
    for r, row in enumerate(rows):
        cells = []
        for c, cell in enumerate(row):
            cls = classes.get((r, c))
            attr = f" class='{cls}'" if cls else ""
            cells.append(f"<td{attr}>{esc(cell)}</td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    return "".join(out) + "</table>"


def section(title: str, how: str, body: str) -> str:
    return f"<h2>{esc(title)}</h2><div class='how'>How to read this: {esc(how)}</div>{body}"


def verdict_html(summary: dict) -> str:
    v = summary["verdict"]
    rows, classes = [], {}
    for i, c in enumerate(v.checks):
        state = "n/a" if not c.available else "PASS" if c.passed else "FAIL"
        classes[(i, 3)] = {"n/a": "na", "PASS": "pass", "FAIL": "fail"}[state]
        rows.append([c.label, fmt(c.value, ".3f"), fmt(c.threshold, "g"), state])
    warn = ""
    paths = summary["random_paths"]
    if paths and paths["warning"]:
        bad = ", ".join(r["symbol"] for r in paths["rows"] if r["warning"])
        warn = (
            f"<div class='warn'>Warning: net R per trade on random price paths is above zero "
            f"for {esc(bad)}. A strategy without an edge must lose about its cost there; this "
            f"points to a bug or lookahead, not to an edge.</div>"
        )
    m = summary["meta"]
    return (
        f"<div class='banner' style='background:{LABEL_COLOURS[v.label]}'>"
        f"<div class='big'>{esc(v.label)}</div><div class='why'>{esc(v.reason)}</div></div>"
        f"<div class='meta'>{esc(m['strategy'])} on {esc(', '.join(m['symbols']))}, "
        f"{esc(m['start'])} to {esc(m['end'])}, {m['trades']} trades, {m['runs']} runs, "
        f"seed {m['seed']}, source {esc(m['source'])}</div>{warn}"
        + table(["Check", "Value", "Threshold", "Result"], rows, classes)
        + "<div class='how'>How to read this: EDGE = all checks pass, WEAK = one or two fail, "
        "NO EDGE = three or more fail; an n/a check is listed but not counted.</div>"
    )


def deflated_html(summary: dict) -> str:
    d = summary["deflated"]
    if d is None:
        return section("Deflated Sharpe", "not computed for this summary.", "")
    rows = [[
        fmt(d["psr0"], ".3f"), fmt(d["dsr"], ".3f"), str(d["n_trials"]),
        fmt(d["variance"], ".5f"), fmt(d["sr0"], ".4f"), str(d["family"]),
    ]]  # fmt: skip
    return section(
        "Deflated Sharpe",
        "PSR(0) is the chance the true Sharpe per trade is above 0. DSR is the same after "
        "allowing for the best of N tried variants (family): SR0 is the Sharpe the best of N "
        "zero-skill variants would show, V the variance of the family's Sharpes. DSR >= 0.95 "
        "passes check 7.",
        table(["PSR(0)", "DSR", "N", "V", "SR0", "Family"], rows),
    )


def fan_html(summary: dict) -> str:
    import plotly.graph_objects as go

    risks = summary["monte_carlo"]["risks"]
    start_balance = summary["monte_carlo"]["config"].start_balance
    fig = go.Figure()
    groups: list[int] = []
    for data in risks.values():
        fan = data["fan"]
        x = fan["days"]
        before = len(fig.data)
        for name, y in (("5 %", fan["p5"]), ("95 %", fan["p95"])):
            fig.add_scatter(
                x=x, y=y, mode="lines", line={"width": 0}, name=name, showlegend=False,
                fill="tonexty" if name == "95 %" else None, fillcolor="rgba(120,130,150,0.22)",
                hoverinfo="skip",
            )  # fmt: skip
        fig.add_scatter(
            x=x, y=fan["p50"], mode="lines", name="median (5 / 50 / 95 % band)",
            line={"color": "rgba(90,100,120,0.9)", "dash": "dash", "width": 1.5},
        )  # fmt: skip
        for p in fan["paths"]:
            fig.add_scatter(x=x, y=p, mode="lines", line={"width": 1}, opacity=0.6,
                            showlegend=False, hoverinfo="skip")  # fmt: skip
        fig.add_scatter(x=x, y=fan["actual"], mode="lines", name="actual order",
                        line={"color": "black", "width": 3})  # fmt: skip
        fig.add_scatter(x=[x[0], x[-1]], y=[start_balance] * 2, mode="lines",
                        line={"color": "gray", "dash": "dot", "width": 1},
                        name="start balance")  # fmt: skip
        best, worst = fan["best"][-1], fan["worst"][-1]
        fig.add_scatter(
            x=[x[-1]] * 2, y=[best, worst], mode="markers+text",
            text=[f"best ${best:,.0f}", f"worst ${worst:,.0f}"],
            textposition="middle left", marker={"size": 8, "color": ["#1a7f37", "#c0392b"]},
            name="best / worst end", showlegend=False,
        )  # fmt: skip
        groups.append(len(fig.data) - before)
    default = list(risks).index(0.01) if 0.01 in risks else 0
    visible, buttons, first = [], [], 0
    for risk, count in zip(risks, groups, strict=True):
        mask = [False] * len(fig.data)
        mask[first : first + count] = [True] * count
        first += count
        visible.append(mask)
        buttons.append({"label": f"{risk * PERCENT:g} % risk", "method": "update",
                        "args": [{"visible": mask}]})  # fmt: skip
    for trace, shown in zip(fig.data, visible[default], strict=True):
        trace.visible = shown
    fig.update_layout(
        height=520, margin={"l": 60, "r": 20, "t": 30, "b": 50},
        xaxis_title="trading days", yaxis_title="balance (USD)",
        updatemenus=[{"buttons": buttons, "active": default, "x": 0.0, "y": 1.12}],
        legend={"orientation": "h", "y": -0.18}, template="plotly_white",
    )  # fmt: skip
    return section(
        "Fan chart (kind A, day reshuffle)",
        f"each thin line is one reshuffled order of the trading days from "
        f"{start_balance:,.0f} USD; the shaded band holds 90 % of all runs, the dashed line is "
        f"the median, the bold black line is the real order. Pick the risk per trade in the menu.",
        fig.to_html(full_html=False, include_plotlyjs="cdn"),
    )


def numbers_html(summary: dict) -> str:
    mc = summary["monte_carlo"]
    risks = mc["risks"]
    cfg = mc["config"]
    head = ["", *[f"{r * PERCENT:g} % risk" for r in risks]]
    st = [d["stats"] for d in risks.values()]

    def trio(get, spec=".1f", suffix=""):
        return [" / ".join(fmt(get(s)[p], spec, suffix) for p in ("p5", "p50", "p95")) for s in st]

    rows = [
        ["Gain on 100k, p5 / p50 / p95", *trio(lambda s: s["gain_pct"], "+.1f", " %")],
        ["Final balance, p5 / p50 / p95", *trio(lambda s: s["final_balance"], ",.0f")],
        ["Avg monthly gain, mean / median",
         *[f"{fmt(s['monthly_gain_pct']['mean'], '+.2f')} % / "
           f"{fmt(s['monthly_gain_pct']['median'], '+.2f')} %" for s in st]],
        ["Profitable months", *[fmt(s["profitable_months"] * PERCENT, ".0f", " %") for s in st]],
        ["Max drawdown, median / p95",
         *[f"{fmt(s['max_dd_pct']['median'])} % / {fmt(s['max_dd_pct']['p95'])} %" for s in st]],
        [f"P(max drawdown > {cfg.dd_alert * PERCENT:g} %)",
         *[fmt(s["p_dd_over_alert"] * PERCENT, ".1f", " %") for s in st]],
        ["Longest drawdown, days (median)",
         *[fmt(s["longest_dd_days"]["median"], ".0f") for s in st]],
        ["Worst day", *[fmt(s["worst_day_pct"], "+.2f", " %") for s in st]],
        ["Longest losing streak, median / max",
         *[f"{fmt(s['longest_losing_streak']['median'], '.0f')} / "
           f"{s['longest_losing_streak']['max']}" for s in st]],
        ["Profit factor", *[fmt(s["profit_factor"], ".2f") for s in st]],
        ["Win rate", *[fmt(s["win_rate"] * PERCENT, ".1f", " %") for s in st]],
        ["Expectancy (R per trade)", *[fmt(s["expectancy_r"], "+.3f") for s in st]],
        ["Trades per month", *[fmt(s["trades_per_month"], ".1f") for s in st]],
    ]  # fmt: skip
    return section(
        "Account numbers (kind A)",
        f"the trades are replayed on a {cfg.start_balance:,.0f} USD account at each risk "
        "(compounding, no lots); p5 / p50 / p95 = bad / typical / good luck in the order of "
        f"days. A month = {cfg.month_days} trading days. Max drawdown is on the closed balance.",
        table(head, rows),
    )


def ftmo_html(summary: dict) -> str:
    risks = summary["monte_carlo"]["risks"]
    cfg = summary["monte_carlo"]["config"]
    head = ["", *[f"{r * PERCENT:g} % risk" for r in risks]]
    ft = [d["ftmo"] for d in risks.values()]

    def share(f, key):
        return f"{f[key]} ({f[key] / f['attempts'] * PERCENT:.0f} %)" if f["attempts"] else "-"

    rows = [
        ["Attempts simulated", *[str(f["attempts"]) for f in ft]],
        ["Pass probability (both phases)",
         *[fmt(f["pass_probability"] * PERCENT, ".1f", " %") for f in ft]],
        ["Failed: daily loss", *[share(f, "fail_daily") for f in ft]],
        ["Failed: max loss", *[share(f, "fail_max") for f in ft]],
        ["Median days to pass", *[fmt(f["median_days_to_pass"], ".0f") for f in ft]],
        [f"Funded account lost within {cfg.funded_days} days",
         *[fmt(f["funded_lost_probability"] * PERCENT, ".1f", " %") for f in ft]],
    ]  # fmt: skip
    return section(
        "FTMO 2-Step (kind A orders)",
        f"each reshuffled order is played as FTMO challenge attempts (Phase 1 +"
        f"{cfg.p1_target * PERCENT:g} %, Phase 2 +{cfg.p2_target * PERCENT:g} %, daily loss "
        f"{cfg.daily_loss * PERCENT:g} %, max loss {cfg.max_loss * PERCENT:g} %). Open trades "
        "count as if at their stop, so the pass rate is a little too low.",
        table(head, rows),
    )


def random_entries_html(summary: dict) -> str:
    re_ = summary["random_entries"]
    how = (
        "the same days with a coin flip between the strategy's direction and the other one; "
        "if the strategy's net R sits far right of the histogram, the direction choice matters."
    )
    if not re_["available"]:
        return section("Random entries (kind B)", how, f"<p>{esc(NOT_AVAILABLE)}.</p>")
    import plotly.graph_objects as go

    fig = go.Figure(go.Histogram(x=re_["run_net_r"], nbinsx=40, name="random runs"))
    fig.add_vline(x=re_["strategy_net_r"], line_color="#c0392b", line_width=3,
                  annotation_text=f"strategy {re_['strategy_net_r']:+.1f} R")  # fmt: skip
    fig.update_layout(height=320, margin={"l": 50, "r": 20, "t": 30, "b": 40},
                      xaxis_title="net R of a random run", yaxis_title="runs",
                      template="plotly_white", showlegend=False)  # fmt: skip
    line = (
        f"<p>Strategy {re_['strategy_net_r']:+.1f} R is above {re_['percentile']:.1f} % of "
        f"{len(re_['run_net_r'])} random runs (mean {re_['mean']:+.1f} R, 5 % "
        f"{re_['p5']:+.1f}, 95 % {re_['p95']:+.1f}), {re_['days']} days.</p>"
    )
    chart = fig.to_html(full_html=False, include_plotlyjs=False)
    return section("Random entries (kind B)", how, line + chart)


def random_fills_html(summary: dict) -> str:
    f = summary["random_fills"]
    rows = [[f"{f['base_net_r']:+.1f}", f"{f['p5']:+.1f}", f"{f['p50']:+.1f}", f"{f['p95']:+.1f}"]]
    return section(
        "Random fills (kind C)",
        "every market fill gets an extra random slippage; the median is what a typical worse "
        "execution leaves of the result (net R, all trades).",
        table(["As backtested", "p5", "p50", "p95"], rows),
    )


def random_paths_html(summary: dict) -> str:
    how = (
        "the strategy on seeded random-walk prices with the symbol's real volatility has no "
        "edge by construction, so net R per trade should be about minus the mean cost; clearly "
        "above zero is a bug warning, not an edge."
    )
    p = summary["random_paths"]
    if p is None:
        return section(
            "Random paths (kind D)", how, "<p>Skipped (--paths 0 or not applicable).</p>"
        )
    rows, classes = [], {}
    for i, r in enumerate(p["rows"]):
        rows.append([
            r["symbol"], str(r["paths"]), str(r["trades"]), fmt(r["mean_net_r"], "+.3f"),
            fmt(r["mean_cost_r"], ".3f"), fmt(r["expected_net_r"], "+.3f"),
            "WARNING" if r["warning"] else "ok",
        ])  # fmt: skip
        classes[(i, 6)] = "fail" if r["warning"] else "pass"
    head = ["Symbol", "Paths", "Trades", "Net R / trade", "Mean cost R / trade",
            "Expected net", "Flag"]  # fmt: skip
    return section("Random paths (kind D)", how, table(head, rows, classes))


def robustness_html(summary: dict) -> str:
    r = summary["robustness"]
    split = r["half_split_date"]
    rows = [
        ["Mean net R per trade / t-statistic",
         f"{fmt(r['mean_net_r'], '+.3f')} / {fmt(r['t_stat'])}"],
        [f"Halves (to {split} / after), net R",
         f"{r['half_first_net_r']:+.1f} / {r['half_second_net_r']:+.1f}"],
        [f"Costs x {r['cost_stress']:g}, net R", f"{r['net_r_stressed']:+.1f}"],
        ["Without the best trade, net R", f"{r['net_r_without_best']:+.1f}"],
        ["Net R", f"{r['net_r']:+.1f}"],
        ["Welch t between the halves", fmt(r["welch_t"])],
    ]  # fmt: skip
    return section(
        "Robustness",
        "a real edge survives higher costs, losing its best trade and a split in time; "
        "t of 2 or more means the mean is unlikely to be luck.",
        table(["Measure", "Value"], rows),
    )


def render_report(summary: dict) -> str:
    body = "".join((
        verdict_html(summary), deflated_html(summary), fan_html(summary), numbers_html(summary), ftmo_html(summary),
        random_entries_html(summary), random_fills_html(summary), random_paths_html(summary),
        robustness_html(summary),
    ))  # fmt: skip
    m = summary["meta"]
    title = f"Monte Carlo {m['strategy']} {'-'.join(m['symbols'])}"
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{esc(title)}</title><style>{CSS}</style></head><body><main>"
        f"<h1>{esc(title)}</h1>{body}</main></body></html>"
    )


# ----- command line ------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    d = ToolConfig()
    p = argparse.ArgumentParser(prog="python -m backtester.tools.monte_carlo", description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)  # fmt: skip
    p.add_argument("symbols", nargs="+", help="e.g. NAS100 US500")
    p.add_argument("--start", type=date.fromisoformat, required=True, help="first UTC day")
    p.add_argument("--end", type=date.fromisoformat, required=True, help="last UTC day")
    p.add_argument("--strategy", choices=tuple(REGISTRY), default="session_zone_sweep",
                   help="registry name, spec defaults (default session_zone_sweep)")  # fmt: skip
    p.add_argument("--source", choices=("histdata", "mt5"), default="histdata",
                   help="candle cache: histdata (default) or FTMO's data/cache/mt5")  # fmt: skip
    p.add_argument("--cache-dir", type=Path, default=None,
                   help="read every symbol from this cache folder (read only; overrides --source)")  # fmt: skip
    p.add_argument("--set", nargs="+", default=None, metavar="KEY=VALUE",
                   help="override settings of the strategy, e.g. entry_z=0.25 stop_atr=2 "
                   "exit_time=11:00 (one variant of a sweep; the rest stay at the spec default)")  # fmt: skip
    p.add_argument("--runs", type=int, default=d.runs, help="runs for kinds A, B and C")
    p.add_argument("--seed", type=int, default=d.seed)
    p.add_argument("--paths", type=int, default=d.paths,
                   help="random price paths per symbol (kind D), 0 = skip")  # fmt: skip
    p.add_argument("--family", default=None,
                   help="trial-log family: the variants this run was picked from "
                   "(default: the strategy)")  # fmt: skip
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args(argv)
    args.symbols = [s.upper() for s in args.symbols]
    return args


def default_out(args: argparse.Namespace) -> Path:
    name = f"{args.strategy}_{'-'.join(args.symbols)}_{args.start}_{args.end}"
    return RESULTS_DIR / MONTE_CARLO_DIR / name


def write_outputs(summary: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.html").write_text(render_report(summary), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(jsonable(summary), indent=1), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = ToolConfig(runs=args.runs, seed=args.seed, paths=args.paths)
    out = args.out or default_out(args)
    t0 = clock.time()
    summary = analyse(args, config)
    write_outputs(summary, out)
    v = summary["verdict"]
    print(f"\nVERDICT: {v.label}. {v.reason}")
    print(f"written to {out} ({clock.time() - t0:.0f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
