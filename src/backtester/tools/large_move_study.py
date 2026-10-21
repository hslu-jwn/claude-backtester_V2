"""Large-move momentum study (ROADMAP 11.13, idea I-61). Research only: it changes no setting
and runs no strategy.

    python -m backtester.tools.large_move_study --cache-dir data/cache/histdata
    python -m backtester.tools.large_move_study --cache-dir <path> --symbols XAUUSD NAS100 \\
        --timeframes H1 --start 2015-01-01 --end 2021-09-13 --out results/large_move

Per symbol x timeframe (M15 H1 H4, resampled from the M1 cache; the loader and the bridging of
the New-Year holes are the 11.11 tool's) and per k (2, 3, 4 robust sd) x h (1, 2, 4, 8, 24
bars): the bars whose return exceeds k x the trailing robust sd, their forward return signed
by the move (continuation > 0) in sd units and in spreads, against a shuffled-time null, per
half, and without the top 1 % events (statistics and choices: `analytics/large_move`). The same
pipeline also runs on the real returns in random order (the sanity check: about 0 findings).

Written to `<out>/`: events.csv (one row per symbol, timeframe, k, h), findings.csv,
findings_shuffled.csv, summary.txt. The cache folder is only read.

Spec: ROADMAP.md > 11.13; knowledge/ideas.md I-61.
"""

from __future__ import annotations

import argparse
import math
import time
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import numpy as np

from backtester.analytics import large_move as lm
from backtester.analytics.large_move import LargeMoveConfig
from backtester.analytics.stationarity import (
    EPOCH,
    SECONDS_PER_DAY,
    StationarityConfig,
    shuffle_returns,
    symbol_end,
)
from backtester.analytics.verdict import middle_date
from backtester.core.models import Timeframe
from backtester.paths import RESULTS_DIR
from backtester.tools.stationarity_study import (
    ALL_SYMBOLS,
    CORE,
    END,
    START,
    load_series,
    missing_days,
    write_rows,
)

TIMEFRAMES = ("M15", "H1", "H4")
MAX_LISTED = 40
EVENT_COLUMNS = [
    "symbol", "timeframe", "k", "h", "n", "mean_sd", "mean_spreads", "mean_ret", "t", "p",
    "pct", "null_mean", "null_sd", "up_share", "first_n", "first_mean_sd", "second_n",
    "second_mean_sd", "trim_mean", "trim_t", "above_cost", "finding", "tradeable", "reason",
]  # fmt: skip
FINDING_COLUMNS = ["symbol", "timeframe", "cell", "value", "p_value", "first_half",
                   "second_half", "siblings", "reason"]  # fmt: skip


def analyze_symbol(job: tuple) -> dict:
    """One worker job: (symbol, cache_dir, timeframes, start, end, cfg, scfg, shuffled) ->
    {"symbol", "rows", "shuffled_rows", "messages"}."""
    symbol, cache_dir, timeframes, start, end, cfg, scfg, with_shuffled = job
    out: dict = {"symbol": symbol, "rows": [], "shuffled_rows": [], "messages": []}
    try:
        spread = lm.spread_return(symbol)
    except KeyError:
        out["messages"].append(f"{symbol}: skipped (no cost settings, spread unknown)")
        return out
    end = symbol_end(symbol, end, scfg)
    mid_day = (middle_date(start, end) - EPOCH).days
    holes = missing_days(symbol, Path(cache_dir), start, end)
    if holes:
        shown = ", ".join(d.isoformat() for d in holes[:8])
        out["messages"].append(
            f"{symbol}: {len(holes)} day(s) without a cache file (bridged): {shown}"
        )
    for tf_name in timeframes:
        tf = Timeframe[tf_name]
        try:
            secs, closes = load_series(symbol, Path(cache_dir), tf, start, end)
        except Exception as e:  # noqa: BLE001 - research tool: say what is missing, go on
            out["messages"].append(f"{symbol} {tf_name}: skipped ({type(e).__name__}: {e})")
            continue
        ok = closes > 0
        secs, closes = secs[ok], closes[ok]
        split = int(np.searchsorted(secs // SECONDS_PER_DAY, mid_day, side="right"))
        y = np.log(closes)
        series = [("rows", y)]
        if with_shuffled:
            series.append(("shuffled_rows", shuffle_returns(y, scfg)))
        for key, yy in series:
            rows = lm.cell_rows(
                yy, secs, tf.value * 60, split, spread, cfg, scfg, f"{symbol}|{tf_name}|{key}"
            )
            for r in rows:
                r["symbol"], r["timeframe"] = symbol, tf_name
            out[key] += rows
        out["messages"].append(f"{symbol} {tf_name}: {len(closes)} bars, spread {spread:.2e}")
    return out


def merge_periods(rows: Sequence[dict]) -> list[dict]:
    """One row per (symbol, timeframe, k, h): the whole row plus the half columns."""
    halves = {
        (r["symbol"], r["timeframe"], r["k"], r["h"], r["period"]): r
        for r in rows
        if r["period"] != "whole"
    }
    merged = []
    for r in rows:
        if r["period"] != "whole":
            continue
        key = (r["symbol"], r["timeframe"], r["k"], r["h"])
        first, second = halves.get((*key, "first_half")), halves.get((*key, "second_half"))
        merged.append(
            {**r, "first_n": first and first["n"], "first_mean_sd": first and first["mean_sd"],
             "second_n": second and second["n"], "second_mean_sd": second and second["mean_sd"]}
        )  # fmt: skip
    return merged


def evaluate(rows: list[dict], scfg: StationarityConfig, cfg: LargeMoveConfig):
    """(annotated rows, findings, counts) with BH over all cells of `rows`."""
    findings, counts = lm.find_move_findings(lm.cells_for_findings(rows), scfg)
    return lm.annotate(rows, findings, scfg, cfg), findings, counts


def _fmt(v, f="{:+.3f}"):
    return "-" if v is None else f.format(v)


def summary_text(
    real: list[dict], shuf: list[dict], counts: dict, shuf_counts: dict | None,
    symbols: Sequence[str], timeframes: Sequence[str], cfg: LargeMoveConfig,
    scfg: StationarityConfig,
) -> str:  # fmt: skip
    ann = [r for r in real if r["period"] == "whole"]
    lines = [
        "LARGE-MOVE MOMENTUM STUDY (ROADMAP 11.13, idea I-61)",
        (
            "Reading: events = bars with |return| > k x trailing robust sd (500 past bars). "
            "'sd' = mean forward return over h bars signed by the move in per-bar sd units "
            "(continuation > 0), 'sp' = the same in spreads of the symbol (one spread = "
            "spread / reference price), p = two-sided normal p against the shuffled-time null "
            "(same count and hour of day, 1,000 runs), halves = first / second half, trim = t of "
            f"the mean without the top {cfg.top_share:.0%} events. Tradeable only above "
            f"{cfg.tradeable_spreads} spreads."
        ),
        "",
        "CORE SYMBOLS FIRST (n events, sd, sp, p, halves, trimmed t):",
    ]
    order = [s for s in CORE if s in symbols] + [s for s in symbols if s not in CORE]
    by = {(r["symbol"], r["timeframe"], r["k"], r["h"]): r for r in ann}
    for sym in order:
        if sym not in CORE:
            continue
        for tf in timeframes:
            for k in cfg.ks:
                cells = []
                for h in cfg.hs:
                    r = by.get((sym, tf, k, h))
                    if r is None:
                        continue
                    cells.append(
                        f"h{h}: n{r['n']} {_fmt(r['mean_sd'], '{:+.2f}')}sd "
                        f"{_fmt(r['mean_spreads'], '{:+.1f}')}sp p{_fmt(r['p'], '{:.2g}')} "
                        f"[{_fmt(r['first_mean_sd'], '{:+.2f}')}/{_fmt(r['second_mean_sd'], '{:+.2f}')}] "
                        f"t{_fmt(r['trim_t'], '{:+.1f}')}"
                    )
                if cells:
                    lines.append(f"{sym} {tf} k{k:g}: " + " | ".join(cells))
    lines += ["", "ALL CELLS: count, BH-significant, findings"]
    for name, c, label in (("real", counts, "real"), ("shuffled", shuf_counts, "shuffled")):
        if c is None:
            continue
        fam = c.get(lm.FAMILY, {"cells": 0, "bh_significant": 0, "findings": 0})
        n_final = sum(1 for r in (real if name == "real" else shuf) if r.get("finding"))
        lines.append(
            f"  {label}: {fam['cells']} cells, {fam['bh_significant']} BH-significant, "
            f"{fam['findings']} pass halves + sibling, {n_final} findings after the top-"
            f"{cfg.top_share:.0%} removal"
        )
    lines.append(
        "  (shuffled = the real returns in random order, same rule: the honest answer is about 0)"
    )
    findings = sorted((r for r in ann if r["finding"]), key=lambda r: r["p"])
    lines += ["", f"FINDINGS ({len(findings)}; first {MAX_LISTED} by p-value):"]
    for r in findings[:MAX_LISTED]:
        lines.append(_cell_line(r))
    if not findings:
        lines.append("  none")
    sig = sorted(
        (r for r in ann if r["p"] is not None and r["p"] < 0.001),
        key=lambda r: -abs(r["mean_spreads"] or 0),
    )
    lines += [
        "",
        f"STRONGEST BY SPREADS among cells with p < 0.001 ({len(sig)}; first {MAX_LISTED}):",
    ]
    lines += [_cell_line(r) + f"  -> {r['reason']}" for r in sig[:MAX_LISTED]] or ["  none"]
    above = [r for r in ann if r["above_cost"] and r["p"] is not None and r["p"] < 0.05]
    lines += ["", f"CELLS ABOVE {cfg.tradeable_spreads} SPREADS with p < 0.05: {len(above)}"]
    return "\n".join(lines) + "\n"


def _cell_line(r: dict) -> str:
    return (
        f"  {r['symbol']} {r['timeframe']} k{r['k']:g} h{r['h']}: n {r['n']}, "
        f"{_fmt(r['mean_sd'], '{:+.3f}')} sd, {_fmt(r['mean_spreads'], '{:+.2f}')} spreads, "
        f"p {_fmt(r['p'], '{:.2g}')}, pct {_fmt(r['pct'], '{:.3f}')}, halves "
        f"{_fmt(r['first_mean_sd'], '{:+.3f}')} / {_fmt(r['second_mean_sd'], '{:+.3f}')}, "
        f"without top: {_fmt(r['trim_mean'], '{:+.3f}')} (t {_fmt(r['trim_t'], '{:+.1f}')})"
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument(
        "--cache-dir", type=Path, required=True, help="histdata cache folder (read only)"
    )
    p.add_argument("--symbols", nargs="+", default=list(ALL_SYMBOLS))
    p.add_argument("--timeframes", nargs="+", choices=TIMEFRAMES, default=list(TIMEFRAMES))
    p.add_argument("--start", type=date.fromisoformat, default=START)
    p.add_argument("--end", type=date.fromisoformat, default=END)
    p.add_argument("--workers", type=int, default=1, help="processes, one symbol each")
    p.add_argument("--n-null", type=int, default=LargeMoveConfig.n_null)
    p.add_argument("--no-shuffled", action="store_true", help="skip the shuffled sanity run")
    p.add_argument("--out", type=Path, default=RESULTS_DIR / "large_move")
    args = p.parse_args(argv)

    cfg = LargeMoveConfig(n_null=args.n_null)
    scfg = StationarityConfig()
    symbols = [s.upper() for s in args.symbols]
    jobs = [
        (s, str(args.cache_dir), tuple(args.timeframes), args.start, args.end, cfg, scfg,
         not args.no_shuffled)
        for s in symbols
    ]  # fmt: skip
    started = time.time()
    if args.workers > 1 and len(jobs) > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(analyze_symbol, jobs))
    else:
        results = []
        for j in jobs:
            res = analyze_symbol(j)
            for line in res["messages"]:
                print(line, flush=True)
            results.append(res)
    rows, shuf = [], []
    for res in results:
        rows += res["rows"]
        shuf += res["shuffled_rows"]

    real, findings, counts = evaluate(rows, scfg, cfg)
    shuf_ann, shuf_findings, shuf_counts = evaluate(shuf, scfg, cfg) if shuf else ([], [], None)
    args.out.mkdir(parents=True, exist_ok=True)
    write_rows(args.out / "events.csv", merge_periods(real), EVENT_COLUMNS)

    def finding_rows(ann, found):
        keep = {
            (r["symbol"], r["timeframe"], lm.cell_name(r["k"], r["h"])) for r in ann if r["finding"]
        }
        return [f for f in found if (f["symbol"], f["timeframe"], f["cell"]) in keep]

    write_rows(args.out / "findings.csv", finding_rows(real, findings), FINDING_COLUMNS)
    write_rows(
        args.out / "findings_shuffled.csv", finding_rows(shuf_ann, shuf_findings), FINDING_COLUMNS
    )
    done = [s for s in symbols if any(r["symbol"] == s for r in rows)]
    text = summary_text(merge_periods(real), merge_periods(shuf_ann), counts, shuf_counts, done,
                        list(args.timeframes), cfg, scfg)  # fmt: skip
    (args.out / "summary.txt").write_text(text, encoding="utf-8")
    print(text)
    print(f"written to {args.out} ({math.ceil(time.time() - started)} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
