"""The gates of the timed-hold families from their development cells; V2 reports, the user
decides. Spec: strategy-timed-hold.md > Gates.

    python -m backtester.tools.timed_hold_gates results/research/<folder> \
        --primary-symbol EURUSD --min-trades 300 --min-breadth 1 [--skip-integrity]

Writes `gates.json` into the research folder.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import UTC, date, datetime, time, timedelta
from itertools import pairwise
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from backtester.analytics.records import read_trades
from backtester.data.sources import SymbolSources
from backtester.tools.alternating_path_gates import (
    STRESSES,
    block_bootstrap,
    block_indices,
    halves,
    integrity_failures,
    net,
)
from backtester.tools.entry_screen import load_m1

BEST_DATES = 5
BLOCK, RESAMPLES, SEED = 5, 10_000, 2026110
NEW_YORK = ZoneInfo("America/New_York")


def rollover_integrity_failures(trades, data, *, max_gap_minutes: int = 5) -> list:
    """Apply Gate 7 tolerance. Spec: strategy-timed-hold.md > Hypothesis 11 > Gate 7 decision."""
    bad = []
    for t in integrity_failures(trades, data, max_gap_minutes=max_gap_minutes):
        day = t.entry_time.astimezone(NEW_YORK).date()
        last_day = t.exit_time.astimezone(NEW_YORK).date()
        crosses = False
        while day <= last_day:
            rollover = datetime.combine(day, time(17), NEW_YORK)
            if t.entry_time < rollover <= t.exit_time:
                crosses = True
                break
            day += timedelta(days=1)
        if not crosses or integrity_failures([t], data, max_gap_minutes=10**9):
            bad.append(t)
            continue
        first, last = int(t.entry_time.timestamp()), int(t.exit_time.timestamp()) - 60
        lo = np.searchsorted(data.open_s, first, side="left")
        hi = np.searchsorted(data.open_s, last, side="right")
        edges = np.concatenate(([first - 60], data.open_s[lo:hi], [last + 60]))
        for left, right in pairwise(edges):
            missing = (right - left) // 60 - 1
            if missing <= 6:
                continue
            start = datetime.fromtimestamp(int(left + 60), UTC)
            end = datetime.fromtimestamp(int(right - 60), UTC)
            if start.date() != end.date() or start.hour < 21 or end.hour >= 23:
                bad.append(t)
                break
    return bad


def _ordered(trades) -> list:
    return sorted(trades, key=lambda t: t.entry_time)


def _nets(trades) -> np.ndarray:
    return np.array([t.r_net for t in _ordered(trades)])


def variant_report(
    trades,
    start: date,
    end: date,
    failures: list | None = None,
    strict_failures: list | None = None,
) -> dict:
    """All numbers of one trade set (one symbol or the pool)."""
    trades = _ordered(trades)
    n = len(trades)
    days: dict[date, float] = defaultdict(float)
    for t in trades:
        days[t.entry_time.date()] += t.r_net
    dropped = set(sorted(days, key=lambda d: days[d], reverse=True)[:BEST_DATES])
    kept = [t for t in trades if t.entry_time.date() not in dropped]
    report = {
        "trades": n,
        "net_r": {s or "normal": net(trades, s) for s in STRESSES},
        "gross_r": sum(t.r_gross for t in trades),
        "mean_net_r": net(trades) / n if n else None,
        "halves_net_r": [net(h) for h in halves(trades, start, end)],
        "best_dates_removed": sorted(d.isoformat() for d in dropped),
        "net_r_without_best_dates": {"normal": net(kept), "all": net(kept, "all")},
        "bootstrap": block_bootstrap(_nets(trades), BLOCK, RESAMPLES, SEED) if n else None,
        # one-sided p of mean net R per trade > 0 (normal approximation; raw, uncorrected)
        "p_value": _p_value(_nets(trades)),
        "by_direction": {
            d: {
                "trades": len(part),
                "net_r": net(part),
                "gross_r": sum(t.r_gross for t in part),
            }
            for d in ("long", "short")
            if (part := [t for t in trades if getattr(t, "direction", None) == d])
        },
        "trades_with_swap": sum(1 for t in trades if getattr(t, "swap_r", 0.0) != 0),
    }
    if failures is not None:
        report["data_integrity_failures"] = len(failures)
        if strict_failures is not None:
            report["data_integrity_failures_strict"] = len(strict_failures)
        report["data_integrity_examples"] = [
            t.entry_time.isoformat() + " " + t.symbol for t in failures[:20]
        ]
    return report


def _p_value(x: np.ndarray) -> float | None:
    if len(x) < 2 or x.std(ddof=1) == 0:
        return None
    z = x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))
    return 0.5 * math.erfc(z / math.sqrt(2))


def difference_bootstrap(filtered, baseline) -> dict | None:
    """Mean net R per trade, filter minus baseline; both series block-resampled independently."""
    a, b = _nets(filtered), _nets(baseline)
    if not len(a) or not len(b):
        return None
    rng = np.random.default_rng(SEED)
    diffs = np.empty(RESAMPLES)
    for i in range(RESAMPLES):
        means = []
        for x in (a, b):
            starts = rng.integers(0, len(x), size=math.ceil(len(x) / BLOCK))
            means.append(x[block_indices(len(x), BLOCK, starts)].mean())
        diffs[i] = means[0] - means[1]
    return {
        "difference": float(a.mean() - b.mean()),
        "lower_2_5": float(np.quantile(diffs, 0.025)),
        "lower_5": float(np.quantile(diffs, 0.05)),
    }


def _name(settings: dict) -> str:
    return "|".join(f"{k}={v}" for k, v in settings.items())


def _baseline(settings: dict, variants: dict) -> dict | None:
    rest = {k: x for k, x in settings.items() if k != "day_filter"}
    for o in variants.values():
        s = o["settings"]
        if (
            s.get("day_filter") == "all"
            and {k: x for k, x in s.items() if k != "day_filter"} == rest
        ):
            return o
    return None


def evaluate(
    variants, start, end, failures, primary, min_trades, min_breadth, strict_failures=None
) -> dict:
    """variants: key -> {"settings": {name: value}, "trades": [...]}; failures: key -> symbol ->
    failing trades, or None when integrity is skipped."""
    out = {}
    for vid, v in variants.items():
        settings, trades = v["settings"], v["trades"]
        mine = {} if failures is None else failures[vid]
        reports = {
            s: variant_report(
                [t for t in trades if t.symbol == s],
                start,
                end,
                None if failures is None else mine.get(s, []),
                None if strict_failures is None else strict_failures[vid].get(s, []),
            )
            for s in sorted({t.symbol for t in trades} | {primary})
        }
        pooled_fails = None if failures is None else [t for f in mine.values() for t in f]
        row = {
            "settings": settings,
            "symbols": reports,
            "pooled": variant_report(
                trades,
                start,
                end,
                pooled_fails,
                None
                if strict_failures is None
                else [t for f in strict_failures[vid].values() for t in f],
            ),
            "skipped_integrity": failures is None,
            "notes": [],
        }
        p = reports[primary]
        if settings.get("day_filter", "all") != "all":
            base = _baseline(settings, variants)
            diff = None
            if base is None:
                row["notes"].append("no baseline variant with day_filter all")
            else:
                # disjoint samples: the baseline without the filter's entry dates
                mine_p = [t for t in trades if t.symbol == primary]
                dates = {t.entry_time.date() for t in mine_p}
                diff = difference_bootstrap(
                    mine_p,
                    [
                        t
                        for t in base["trades"]
                        if t.symbol == primary and t.entry_time.date() not in dates
                    ],
                )
            row["baseline_difference"] = diff
            effect = diff is not None and diff["lower_2_5"] > 0
        else:
            effect = p["bootstrap"] is not None and p["bootstrap"]["lower_2_5"] > 0
        gates = {
            "positive_normal_and_doubled": all(x > 0 for x in p["net_r"].values()),
            "positive_both_halves": all(x > 0 for x in p["halves_net_r"]),
            "effect_not_drift": effect,
            "breadth": sum(r["net_r"]["normal"] > 0 for s, r in reports.items() if s != primary)
            >= min_breadth,
            "best_date_removal_positive": all(
                x > 0 for x in p["net_r_without_best_dates"].values()
            ),
            "min_trades": p["trades"] >= min_trades,
            "no_data_integrity_failure": failures is None or p["data_integrity_failures"] == 0,
        }
        row["gates"] = gates
        row["advances"] = all(gates.values())
        out[vid] = row
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("folder", type=Path)
    p.add_argument("--primary-symbol", required=True)
    p.add_argument("--min-trades", type=int, required=True)
    p.add_argument("--min-breadth", type=int, required=True)
    p.add_argument("--skip-integrity", action="store_true")
    args = p.parse_args(argv)
    with (args.folder / "variants.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    variants = {}
    for row in rows:
        settings = {k[4:]: v for k, v in row.items() if k.startswith("set.")}
        if row.get("family"):  # [[grids]] families differ by their base, not by set.* columns
            settings = {"family": row["family"], **settings}
        key = _name(settings)
        if key in variants:
            raise SystemExit(f"two variants share the key {key!r}; gates need distinct cells")
        variants[key] = {
            "settings": settings,
            "trades": read_trades(args.folder / "variants" / row["variant_id"]),
        }
    some = next(iter(args.folder.glob("variants/*/settings.json")))
    run = json.loads(some.read_text(encoding="utf-8"))["run"]
    start, end = date.fromisoformat(run["start"]), date.fromisoformat(run["end"])
    max_gap_minutes = 5
    failures = None
    strict_failures = None
    if not args.skip_integrity:
        sources = SymbolSources({s: Path(d) for s, d in run["cache_dirs"].items()})
        failures = {vid: {} for vid in variants}
        strict_failures = {vid: {} for vid in variants}
        for symbol in run["symbols"]:
            data = load_m1(symbol, sources, start, end + timedelta(days=1))
            for vid, v in variants.items():
                mine = [t for t in v["trades"] if t.symbol == symbol]
                strict_failures[vid][symbol] = integrity_failures(
                    mine, data, max_gap_minutes=max_gap_minutes
                )
                failures[vid][symbol] = rollover_integrity_failures(
                    mine, data, max_gap_minutes=max_gap_minutes
                )
    result = {
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "settings": {
            "max_gap_minutes": max_gap_minutes,
            "rollover_tolerance": True,
            "primary_symbol": args.primary_symbol,
            "min_trades": args.min_trades,
            "min_breadth": args.min_breadth,
            "bootstrap": {"block_trades": BLOCK, "resamples": RESAMPLES, "seed": SEED},
            "best_dates_removed": BEST_DATES,
        },
        "variants": evaluate(
            variants,
            start,
            end,
            failures,
            args.primary_symbol,
            args.min_trades,
            args.min_breadth,
            strict_failures=strict_failures,
        ),
    }
    (args.folder / "gates.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    for vid, row in result["variants"].items():
        print(vid, "advances" if row["advances"] else "rejected", row["gates"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
