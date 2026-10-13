"""Compare liquidity sweep rule variants by what price did after each sweep.

    python -m backtester.tools.sweep_study                      # all symbols, all timeframes
    python -m backtester.tools.sweep_study NAS100 XAUUSD --timeframes H4 M30 --horizon 20

For every variant (rule combination, `variants()`) the sweep detector runs over the cached
candles; every sweep is scored by `analytics.sweep_quality.sweep_outcome` (entry at the BOS
close, stop at the sweeping wick, 1R / 2R targets, `--horizon` candles). Written to
results/sweep_study/: `summary.csv` (variant x timeframe), `vs_base.csv` (what each rule
removes / adds compared with the base variant) and `report.md`. Gross, no costs. Research
only: it never changes a rule.
Spec: confluences.md › Liquidity sweep.
"""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from backtester.analytics.sweep_quality import SweepOutcome, sweep_outcome
from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.data.adapters.cache_adapter import MissingCacheError, candles_from_frame
from backtester.data.sources import DEFAULT_SOURCES
from backtester.detectors.atr import Atr
from backtester.detectors.sweep import SweepConfig, SweepDetector
from backtester.detectors.swings import SwingConfig
from backtester.paths import RESULTS_DIR

OUT_DIR = RESULTS_DIR / "sweep_study"
BASE = "base"
# timeframe -> (start, end) UTC: shorter spans for the fast timeframes (run time)
SPANS = {
    "M5": ("2026-04-01", "2026-10-01"),
    "M30": ("2025-01-01", "2026-10-01"),
    "H1": ("2024-01-01", "2026-10-01"),
    "H4": ("2020-01-02", "2026-10-01"),
}


@dataclass(frozen=True)
class Variant:
    name: str
    sweep: SweepConfig = field(default_factory=SweepConfig)
    doji_share: float = 0.0


def variants() -> list[Variant]:
    """The base (today's rules), every rule changed alone, then a few combinations."""
    c2 = {"two_closes_cancel": True}
    c3 = {"two_closes_cancel": True, "cancel_closes": 3}
    w2 = {"two_closes_cancel": True, "cancel_wick_first": True}
    w3 = {"two_closes_cancel": True, "cancel_wick_first": True, "cancel_closes": 3}
    top = {"bos_before_top": True}

    def v(name, doji=0.0, **kw):
        return Variant(name, SweepConfig(**kw), doji)

    return [
        v(BASE),
        # how many swings
        v("N=1", lookback_swings=1),
        v("N=2", lookback_swings=2),
        v("N=4", lookback_swings=4),
        v("N=5", lookback_swings=5),
        # which level must be taken
        v("strict (max of N)", equal_tolerance_atr=0.0),
        v("tol 0.25 ATR", equal_tolerance_atr=0.25),
        v("tol 0.5 ATR", equal_tolerance_atr=0.5),
        v("tol 1 ATR", equal_tolerance_atr=1.0),
        # breakout filter
        v("2 closes", **c2),
        v("3 closes", **c3),
        v("wick+close", **w2),
        v("wick+wick+close", **w3),
        # BOS must break structure from before the top
        v("BOS before top", **top),
        # BOS time window
        v("BOS within 5", bos_within=5),
        v("BOS within 20", bos_within=20),
        # doji as a share of the candle's range
        v("doji 5%", doji=0.05),
        v("doji 10%", doji=0.10),
        # combinations
        v("strict + 2 closes", equal_tolerance_atr=0.0, **c2),
        v("tol 0.5 + 2 closes", equal_tolerance_atr=0.5, **c2),
        v("tol 0.5 + wick+close", equal_tolerance_atr=0.5, **w2),
        v("2 closes + BOS before top", **c2, **top),
        v("wick+close + BOS before top", **w2, **top),
        v("3 closes + BOS before top", **c3, **top),
        v("tol 0.5 + 2 closes + BOS before top", equal_tolerance_atr=0.5, **c2, **top),
        v("tol 0.5 + 2 closes + top + doji 10%", doji=0.10, equal_tolerance_atr=0.5, **c2, **top),
        v("2 closes + top + doji 10%", doji=0.10, **c2, **top),
        v(
            "N=5 + tol 0.5 + 2 closes + top",
            lookback_swings=5,
            equal_tolerance_atr=0.5,
            **c2,
            **top,
        ),
    ]


@dataclass(frozen=True)
class Scored:
    key: tuple  # (symbol, timeframe, direction, BOS candle) identifies a sweep across variants
    timeframe: str
    outcome: SweepOutcome
    direction: str
    risk_atr: float  # risk in ATR at the BOS candle
    mfe_atr: float
    fav_atr: float
    adv_atr: float
    drift_atr: float
    features: tuple = ()  # (name, value) pairs: what the sweep looked like (for buckets)


def load(symbol: str, timeframe: str, start: str, end: str) -> CandleSeries | None:
    tf = Timeframe[timeframe]
    try:
        frame = DEFAULT_SOURCES.adapter(symbol).fetch_frame(
            symbol, tf, datetime.fromisoformat(start), datetime.fromisoformat(end)
        )
    except MissingCacheError:
        return None
    return CandleSeries(symbol, tf, candles_from_frame(frame)) if len(frame) else None


def score_variant(series: CandleSeries, atr: list[float | None], v: Variant, horizon: int):
    detector = SweepDetector.for_symbol(
        series.symbol, SwingConfig(doji_range_share=v.doji_share), v.sweep
    )
    candles = list(series.view(len(series) - 1))
    out = []
    for i in range(len(series)):
        for e in detector.update(series.view(i)):
            res = sweep_outcome(candles, e.direction, e.extreme, e.confirmed_index, horizon)
            a = atr[e.confirmed_index]
            if res is None or not a:
                continue
            key = (series.symbol, series.timeframe.name, e.direction.value, e.confirmed_index)
            out.append(
                Scored(
                    key, series.timeframe.name, res, e.direction.value, res.risk / a,
                    res.mfe_r * res.risk / a, res.fav / a, res.adv / a, res.drift / a,
                    (
                        ("risk_ATR", res.risk / a),
                        ("wick_beyond_level_ATR", abs(e.extreme - e.swing.price) / a),
                        ("levels_taken", len(e.swept)),
                        ("level_age_candles", e.index - e.swing.index),
                        ("BOS_delay_candles", e.confirmed_index - e.index),
                    ),
                )
            )  # fmt: skip
    return out


def atr_values(series: CandleSeries) -> list[float | None]:
    atr = Atr(14)
    return [atr.update(series.view(i)) for i in range(len(series))]


def stats(rows: list[Scored]) -> dict:
    n = len(rows)
    if not n:
        return {"n": 0}
    r1 = [r.outcome.r1 for r in rows]
    r2 = [r.outcome.r2 for r in rows]
    se = statistics.pstdev(r1) / n**0.5 if n > 1 else 0.0
    return {
        "n": n,
        "E_1R": round(statistics.fmean(r1), 3),
        "se": round(se, 3),
        "E_2R": round(statistics.fmean(r2), 3),
        "win_1R_%": round(100 * sum(x == 1.0 for x in r1) / n, 1),
        "stopped_%": round(100 * sum(r.outcome.stopped for r in rows) / n, 1),
        "mfe_ATR_median": round(statistics.median(r.mfe_atr for r in rows), 2),
        "risk_ATR_median": round(statistics.median(r.risk_atr for r in rows), 2),
        "fav_ATR_mean": round(statistics.fmean(r.fav_atr for r in rows), 2),
        "adv_ATR_mean": round(statistics.fmean(r.adv_atr for r in rows), 2),
        "drift_ATR_mean": round(statistics.fmean(r.drift_atr for r in rows), 3),
        "drift_se": round(statistics.pstdev(r.drift_atr for r in rows) / n**0.5, 3),
        "drift_up_%": round(100 * sum(r.drift_atr > 0 for r in rows) / n, 1),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("symbols", nargs="*", default=list(DEFAULT_SOURCES.symbols))
    p.add_argument("--timeframes", nargs="+", default=list(SPANS), choices=list(SPANS))
    p.add_argument("--horizon", type=int, default=20, help="candles looked at after the sweep")
    p.add_argument("--out", type=Path, default=OUT_DIR)
    args = p.parse_args(argv)

    vs = variants()
    scored: dict[str, list[Scored]] = defaultdict(list)
    for tf in args.timeframes:
        for symbol in args.symbols:
            series = load(symbol, tf, *SPANS[tf])
            if series is None:
                print(f"{symbol} {tf}: no data, skipped")
                continue
            atr = atr_values(series)
            print(f"{symbol} {tf}: {len(series):,} candles", flush=True)
            for v in vs:
                scored[v.name] += score_variant(series, atr, v, args.horizon)

    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for v in vs:
        for tf in [*args.timeframes, "ALL", "bearish", "bullish"]:
            sel = [
                r for r in scored[v.name]
                if tf == "ALL" or tf in (r.timeframe, r.direction)
            ]  # fmt: skip
            rows.append({"variant": v.name, "timeframe": tf, **stats(sel)})
    write_csv(args.out / "summary.csv", rows)

    base = {r.key: r for r in scored[BASE]}
    diff = []
    for v in vs[1:]:
        mine = {r.key: r for r in scored[v.name]}
        kept = [mine[k] for k in mine if k in base]
        added = [mine[k] for k in mine if k not in base]
        removed = [base[k] for k in base if k not in mine]
        for label, sel in (("kept", kept), ("added", added), ("removed", removed)):
            diff.append({"variant": v.name, "set": label, **stats(sel)})
    write_csv(args.out / "vs_base.csv", diff)
    write_csv(args.out / "base_buckets.csv", buckets(scored[BASE]))
    (args.out / "report.md").write_text(report(rows, diff, args), encoding="utf-8")
    print(f"written to {args.out}")
    return 0


def buckets(rows: list[Scored], parts: int = 4) -> list[dict]:
    """The base sweeps split into `parts` equally large groups by each feature."""
    out = []
    for name in dict(rows[0].features):
        ranked = sorted(rows, key=lambda r: dict(r.features)[name])
        size = max(1, len(ranked) // parts)
        for k in range(parts):
            chunk = ranked[k * size : (k + 1) * size if k < parts - 1 else len(ranked)]
            values = [dict(r.features)[name] for r in chunk]
            out.append(
                {
                    "feature": name,
                    "group": f"{k + 1}/{parts}",
                    "range": f"{min(values):.2f} .. {max(values):.2f}",
                    **stats(chunk),
                }
            )
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    cols = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def table(rows: list[dict], cols: list[str]) -> list[str]:
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows]
    return out


def report(rows: list[dict], diff: list[dict], args) -> str:
    lines = [
        "# Liquidity sweep rule study",
        "",
        (
            f"Symbols: {', '.join(args.symbols)}. Timeframes: {', '.join(args.timeframes)}. "
            f"Horizon {args.horizon} candles after the BOS candle. Entry = BOS close, stop = "
            "sweeping wick, E_1R / E_2R = average result in R of a 1R / 2R target (gross)."
        ),
        "",
        "## All timeframes pooled",
        *table([r for r in rows if r["timeframe"] == "ALL"], list(rows[0])),
        "",
        "## What each rule removes / adds compared with the base",
        *table(diff, list(diff[0])),
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
