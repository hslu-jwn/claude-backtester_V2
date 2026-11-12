"""Score strategy 14 development cells. Spec: strategy-us_close_de_open.md › Gates.

python -m backtester.tools.us_close_de_open_gates <GER40 folder> --breadth-folder <UK100 folder> [--skip-integrity]
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from backtester.analytics.bootstrap import block_indices as block_indices  # noqa: PLC0414 -- legacy re-export
from backtester.analytics.bootstrap import interleaved_block_means
from backtester.analytics.records import read_trades
from backtester.data.sources import SymbolSources
from backtester.strategy.timed_hold.day_filter import DEFAULT_DIR
from backtester.tools.alternating_path_gates import STRESSES, integrity_failures, net
from backtester.tools.entry_screen import load_m1
from backtester.tools.timed_hold_gates import (
    BEST_DATES,
    BLOCK,
    RESAMPLES,
    SEED,
    _name,
    variant_report,
)

BERLIN = ZoneInfo("Europe/Berlin")
NEW_YORK = ZoneInfo("America/New_York")
SPLIT = date(2017, 10, 8)


def is_primary(settings, *, uk=False):
    try:
        return (settings.get("family") == "S" and float(settings["min_ref_return_pct"]) == 0.1
                and float(settings["stop_atr"]) == 0.5
                and settings["exit_time"] == ("08:30" if uk else "09:30"))
    except (KeyError, ValueError, TypeError):
        return False


def report(trades, start, end, failures=None):
    result = variant_report(trades, start, end, failures)
    def halves(items):
        return [net([t for t in items if t.entry_time.astimezone(UTC).date() < SPLIT]),
                net([t for t in items if t.entry_time.astimezone(UTC).date() >= SPLIT])]
    result["halves_net_r"] = halves(trades)
    for direction, detail in result["by_direction"].items():
        detail["halves_net_r"] = halves([t for t in trades if t.direction == direction])
    result["family_wise_level"] = 0.01
    return result


def control_difference(signal, longs, shorts):
    dates = {t.entry_time.astimezone(BERLIN).date() for t in signal}
    controls = [[t for t in part if t.entry_time.astimezone(BERLIN).date() not in dates]
                for part in (longs, shorts)]
    counts = [sum(t.direction == d for t in signal) for d in ("long", "short")]
    arrays = [np.array([t.r_net for t in sorted(part, key=lambda t: t.entry_time)], dtype=float)
              for part in (signal, *controls)]
    if not len(arrays[0]) or any(count and not len(x) for count, x in zip(counts, arrays[1:])):
        return None
    weights = np.array(counts) / len(signal)
    def difference(means):
        return float(means[0] - sum(w * m for w, m in zip(weights, means[1:])))
    means = interleaved_block_means(arrays, BLOCK, RESAMPLES, np.random.default_rng(SEED))
    samples = np.array([difference(row) for row in means])
    return {"difference": difference([x.mean() if len(x) else 0. for x in arrays]),
            "lower_2_5": float(np.quantile(samples, .025)),
            "lower_5": float(np.quantile(samples, .05)),
            "n_long": counts[0], "n_short": counts[1],
            "control_long_trades": len(controls[0]), "control_short_trades": len(controls[1])}


def dst_split(trades):
    mismatch = lambda t: bool(t.entry_time.astimezone(NEW_YORK).dst()) != bool(t.entry_time.astimezone(BERLIN).dst())
    parts = {"mismatch": [t for t in trades if mismatch(t)],
             "rest": [t for t in trades if not mismatch(t)]}
    return {name: {"trades": len(part), "net_r": net(part)} for name, part in parts.items()}


def breadth_report(variants, start, end):
    signals = {key: v for key, v in variants.items() if v["settings"].get("family") == "S"}
    matches = [v for v in signals.values() if is_primary(v["settings"], uk=True)]
    primary = report([t for t in matches[0]["trades"] if t.symbol == "UK100"], start, end) if len(matches) == 1 else None
    return {"passes": primary is not None and primary["net_r"]["normal"] > 0,
            "primary": primary,
            "cells_net_r": {k: net([t for t in v["trades"] if t.symbol == "UK100"]) for k, v in signals.items()},
            "note": None if primary is not None else "missing or ambiguous UK100 primary cell"}


def evaluate(variants, uk_variants, start, end, failures):
    breadth = breadth_report(uk_variants, start, end)
    out = {}
    for key, variant in variants.items():
        settings = variant["settings"]
        trades = [t for t in variant["trades"] if t.symbol == "GER40"]
        r = report(trades, start, end, None if failures is None else failures[key])
        row = {"settings": settings, "report": r, "advances": False, "notes": []}
        out[key] = row
        if settings.get("family") == "C":
            row["verdict"] = "control"
            continue
        controls = []
        for direction in ("long", "short"):
            matches = [v for v in variants.values() if v["settings"].get("family") == "C"
                       and v["settings"].get("direction") == direction
                       and v["settings"].get("stop_atr") == settings.get("stop_atr")
                       and v["settings"].get("exit_time") == settings.get("exit_time")]
            controls.append(matches)
        diff = None
        if all(len(m) == 1 for m in controls):
            diff = control_difference(trades, *[[t for t in m[0]["trades"] if t.symbol == "GER40"] for m in controls])
        if diff is None:
            row["notes"].append("missing or ambiguous control cells or insufficient control trades")
        if breadth["note"]:
            row["notes"].append(breadth["note"])
        gates = {"positive_normal_and_doubled": all(r["net_r"][s or "normal"] > 0 for s in STRESSES),
                 "positive_both_halves": all(x > 0 for x in r["halves_net_r"]),
                 "effect_not_drift": diff is not None and diff["lower_2_5"] > 0,
                 "breadth": breadth["passes"],
                 "best_date_removal_positive": all(x > 0 for x in r["net_r_without_best_dates"].values()),
                 "min_trades": len(trades) >= 200,
                 "no_data_integrity_failure": failures is not None and not failures[key]}
        row.update({"gates": gates, "control_difference": diff, "breadth": breadth,
                    "dst_split": dst_split(trades), "skipped_integrity": failures is None,
                    "primary": is_primary(settings)})
        if not gates["min_trades"]:
            verdict = "not_enough_evidence"
        elif r["mean_net_r"] <= 0 or r["bootstrap"]["lower_2_5"] <= 0 or not gates["effect_not_drift"]:
            verdict = "falsified"
        elif row["primary"] and all(gates.values()):
            verdict = "advances"
        else:
            verdict = "rejected"
        row["verdict"] = verdict
        row["advances"] = verdict == "advances"
    return out


def load_variants(folder):
    with (folder / "variants.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    variants = {}
    for row in rows:
        settings = {k[4:]: v for k, v in row.items() if k.startswith("set.")}
        if row.get("family"):
            settings = {"family": row["family"], **settings}
        key = _name(settings)
        if key in variants:
            raise ValueError(f"duplicate cell {key}")
        variants[key] = {"settings": settings, "trades": read_trades(folder / "variants" / row["variant_id"])}
    return variants


def missing_signal_days(data, start, end):
    with (DEFAULT_DIR / "nyse_holidays.csv").open(encoding="utf-8", newline="") as stream:
        excluded = {date.fromisoformat(r["date"]) for r in csv.DictReader(stream)
                    if r["type"].strip() in ("closed", "early_close_13:00")}
    available = set(data.open_s)
    missing = 0
    for i in range((end - start).days + 1):
        day = start + timedelta(days=i)
        if day.weekday() >= 5 or day in excluded:
            continue
        stamps = [int((datetime.combine(day, time(h, m), NEW_YORK) - timedelta(minutes=1)).timestamp())
                  for h, m in ((15, 30), (16, 0))]
        missing += any(stamp not in available for stamp in stamps)
    return missing


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder", type=Path)
    parser.add_argument("--breadth-folder", type=Path, required=True)
    parser.add_argument("--skip-integrity", action="store_true")
    args = parser.parse_args(argv)
    variants = load_variants(args.folder)
    uk = load_variants(args.breadth_folder) if (args.breadth_folder / "variants.csv").is_file() else {}
    settings_file = next(args.folder.glob("variants/*/settings.json"))
    run = json.loads(settings_file.read_text(encoding="utf-8"))["run"]
    start, end = date.fromisoformat(run["start"]), date.fromisoformat(run["end"])
    failures, missing = None, None
    if not args.skip_integrity:
        sources = SymbolSources({s: Path(d) for s, d in run["cache_dirs"].items()})
        data = load_m1("GER40", sources, start, end + timedelta(days=1))
        failures = {key: integrity_failures([t for t in v["trades"] if t.symbol == "GER40"], data, max_gap_minutes=5) for key, v in variants.items()}
        us = load_m1("US500", sources, start, end + timedelta(days=1))
        missing = missing_signal_days(us, start, end)
    result = {"period": {"start": start.isoformat(), "end": end.isoformat()},
              "settings": {"max_gap_minutes": 5, "best_dates_removed": BEST_DATES,
                           "bootstrap": {"block_trades": BLOCK, "resamples": RESAMPLES, "seed": SEED}},
              "missing_us500_signal_days": missing, "skipped_integrity": args.skip_integrity,
              "variants": evaluate(variants, uk, start, end, failures)}
    (args.folder / "gates.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    for key, row in result["variants"].items():
        print(key, row["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
