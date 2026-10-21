"""Gap fade walk-forward (ROADMAP 11.7): each year trades the variant that was best before it.

    python -m backtester.tools.gap_fade_walk_forward
    python -m backtester.tools.gap_fade_walk_forward --source mt5 --start 2021-09-15

Runs the 36 variants of `tools/gap_fade_grid.py` once each over the whole period and splits their
trades by entry year (equal to per-year runs except for the daily ATR: the runner seeds it from
`min_warmup_days` cached days before every run, and the Wilder ATR forgets its seed within weeks,
so a per-year run only differs in the first days of its year; the full run is the more accurate
one). `analytics/walk_forward.py` (anchored, max net R on the train years, ties to the first
variant) picks the variant per test year, the first test year being the year after the start.
Writes `<out>/years.csv`, `<out>/summary.json` and the Monte Carlo report of the chained
out-of-sample trades (`monte_carlo/`, kind B = the follow trades of the variant chosen each year,
kind D n/a) and of the default variant over the same test years (`monte_carlo_default/`).
Net R includes the swap. Default `<out>`: results/gap_fade_walk_forward.
Research only: it changes no setting.
"""

from __future__ import annotations

import argparse
import csv
import json
import time as clock
from dataclasses import replace
from datetime import date
from pathlib import Path

from backtester.analytics.walk_forward import WalkForwardConfig, walk_forward
from backtester.data.cache import MT5_CACHE_DIR
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.gap_fade.config import GapFadeConfig
from backtester.tools.gap_fade_grid import SYMBOLS, last_cached_day, variant_name, variants
from backtester.tools.monte_carlo import ToolConfig, build_summary, jsonable, write_outputs

START = date(2018, 1, 1)
OUT_DIR = "gap_fade_walk_forward"
COLUMNS = ("year", "chosen_variant", "train_net_r", "test_net_r", "default_net_r", "trades")


def _in_years(trades, first: int, last: int) -> list:
    return [t for t in trades if first <= t.entry_time.year <= last]


def _net(trades) -> float:
    return sum(t.r_net for t in trades)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    d = ToolConfig()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, default=START)
    p.add_argument("--end", type=date.fromisoformat, default=None,
                   help="default: the last cached day")  # fmt: skip
    p.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    p.add_argument("--source", choices=("histdata", "mt5"), default="histdata")
    p.add_argument("--runs", type=int, default=d.runs, help="runs for Monte Carlo kinds A, B, C")
    p.add_argument("--seed", type=int, default=d.seed)
    p.add_argument("--out", type=Path, default=None)
    return p.parse_args(argv)


def main(argv: list[str] | None = None, log=print) -> int:
    args = parse_args(argv)
    symbols = [s.upper() for s in args.symbols]
    sources = (
        DEFAULT_SOURCES
        if args.source == "histdata"
        else SymbolSources.single(MT5_CACHE_DIR, symbols)
    )
    end = args.end or last_cached_day(symbols, sources)
    out = args.out or RESULTS_DIR / OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    settings = RunSettings()
    t0 = clock.time()

    def run(config: GapFadeConfig) -> list:
        res = run_backtests(
            symbols, args.start, end, replace(settings, strategy=config),
            sources=sources, workers=1,
        )  # fmt: skip
        return list(res.trades)

    configs = {variant_name(c): c for c in variants()}
    default_name = variant_name(GapFadeConfig())
    trades_by_variant = {}
    for name, config in configs.items():
        trades_by_variant[name] = run(config)
        log(f"{name}: {len(trades_by_variant[name])} trades")

    wf = walk_forward(
        trades_by_variant, WalkForwardConfig(), first_year=args.start.year, last_year=end.year
    )
    if not wf.picks:
        log("no test year (period too short)")
        return 1
    first_test, last_test = wf.picks[0].year, wf.picks[-1].year
    rows = []
    for pick in wf.picks:
        default_year = _in_years(trades_by_variant[default_name], pick.year, pick.year)
        rows.append({
            "year": pick.year, "chosen_variant": pick.variant,
            "train_net_r": round(pick.train_net, 4),
            "test_net_r": round(_net(pick.test_trades), 4),
            "default_net_r": round(_net(default_year), 4),
            "trades": len(pick.test_trades),
        })  # fmt: skip
    with (out / "years.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    chained = list(wf.chained)
    default_oos = _in_years(trades_by_variant[default_name], first_test, last_test)
    meta = {"symbols": symbols, "start": date(first_test, 1, 1), "end": end, "source": args.source}
    mc_config = ToolConfig(runs=args.runs, seed=args.seed, paths=0)

    # kind B: the follow trades of the variant chosen each year (one follow run per variant)
    follow_cache: dict[str, list] = {}

    def follow_trades(name: str) -> list:
        if name not in follow_cache:
            log(f"follow run: {name}")
            follow_cache[name] = run(replace(configs[name], mode="follow"))
        return follow_cache[name]

    follow_chained = [
        t for p in wf.picks for t in follow_trades(p.variant) if t.entry_time.year == p.year
    ]
    reports = {
        "monte_carlo": (
            chained,
            follow_chained,
            f"gap_fade walk-forward (anchored, from {first_test})",
        ),
        "monte_carlo_default": (
            default_oos,
            _in_years(follow_trades(default_name), first_test, last_test),
            f"gap_fade default {default_name} ({first_test}-{last_test})",
        ),
    }
    verdicts = {}
    for folder, (trades, follow, label) in reports.items():
        log(f"Monte Carlo report: {label}")
        summary = build_summary(
            trades, follow, {**meta, "strategy": label}, settings, mc_config, None, log
        )
        write_outputs(summary, out / folder)
        v = summary["verdict"]
        risks = summary["monte_carlo"]["risks"]
        verdicts[folder] = {
            "label": v.label, "reason": v.reason,
            "checks": [
                {"key": c.key, "value": c.value, "passed": c.passed, "available": c.available}
                for c in v.checks
            ],
            "ftmo_pass_probability": {str(r): d["ftmo"]["pass_probability"] for r, d in risks.items()},
            "monthly_gain_pct_mean": {
                str(r): d["stats"]["monthly_gain_pct"]["mean"] for r, d in risks.items()
            },
        }  # fmt: skip
    result = {
        "symbols": symbols, "source": args.source, "start": args.start, "end": end,
        "first_test_year": first_test, "last_test_year": last_test,
        "default_variant": default_name, "variants": len(configs),
        "chained_net_r": _net(chained), "chained_trades": len(chained),
        "default_net_r": _net(default_oos), "default_trades": len(default_oos),
        "verdicts": verdicts, "seconds": round(clock.time() - t0),
    }  # fmt: skip
    (out / "summary.json").write_text(json.dumps(jsonable(result), indent=1), encoding="utf-8")
    log(
        f"chained out-of-sample {result['chained_net_r']:+.1f} R / {len(chained)} trades, "
        f"default {result['default_net_r']:+.1f} R / {len(default_oos)} trades; written to {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
