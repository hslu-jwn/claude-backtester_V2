"""Score existing research cells from a grid's [gates] table.

python -m backtester.tools.gates <research folder> [--breadth-folder <folder>]
    [--skip-integrity] [--controls N]

Spec: research-runner.md › Gates table (one gates tool).

Assumptions following us_close_de_open_gates: control exclusion and fake-cell date
sampling use Europe/Berlin entry dates. A unique long and short control are required,
including when the signal has only one direction. Midpoint halves split UTC entry
times at the midpoint of [start, end + one day), with equality in the second half.
Folder breadth uses the main run's reporting period. In-run breadth counts all
symbols in the unfiltered cell, even when symbol selects only one for scoring.
Fake cells draw n distinct dates from the controls' intersection without replacement;
the first n_long draws select long trades, the rest short trades. Duplicate trades
on a control date are ambiguous and leave controls null. Too few shared dates also
leave controls null. Rates have denominator N; positive shifts change only r_net.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import tomllib
from dataclasses import is_dataclass, replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np

from backtester.data.sources import SymbolSources
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
from backtester.tools.us_close_de_open_gates import BERLIN, control_difference, load_variants

CONTROL_SEED = 20261112
DETECTABLE_EDGE_Z = 2.8


def same_value(a, b):
    """Compare numeric settings numerically, all other settings as strings."""
    try:
        x, y = Decimal(str(a)), Decimal(str(b))
        if x.is_finite() and y.is_finite():
            return x == y
    except InvalidOperation:
        pass
    return str(a) == str(b)


def matches(settings, wanted):
    return all(k in settings and same_value(settings[k], v) for k, v in wanted.items())


def selected(trades, symbol):
    return [t for t in trades if symbol is None or t.symbol == symbol]


def report(trades, start, end, failures, halves):
    r = variant_report(trades, start, end, failures)
    if halves is not None:
        if halves == "midpoint":
            begin = datetime.combine(start, time(), UTC)
            split = begin + (datetime.combine(end + timedelta(days=1), time(), UTC) - begin) / 2
        else:
            split = datetime.combine(date.fromisoformat(halves), time(), UTC)

        def parts(items):
            return [net([t for t in items if t.entry_time.astimezone(UTC) < split]),
                    net([t for t in items if t.entry_time.astimezone(UTC) >= split])]

        r["halves_net_r"] = parts(trades)
        for direction, detail in r["by_direction"].items():
            detail["halves_net_r"] = parts([t for t in trades if t.direction == direction])
    return r


def matched_controls(variants, settings, config, symbol):
    controls = []
    for direction in ("long", "short"):
        wanted = {"family": config["family"], "direction": direction}
        for name in config.get("match", []):
            if name not in settings:
                return None
            wanted[name] = settings[name]
        cells = [v for v in variants.values() if matches(v["settings"], wanted)]
        if len(cells) != 1:
            return None
        controls.append(selected(cells[0]["trades"], symbol))
    return controls


def breadth_report(variants, trades, config, start, end, halves, control_family):
    if "min_positive" in config:
        symbols = sorted({t.symbol for t in trades})
        values = {s: net(selected(trades, s)) for s in symbols}
        count = sum(v > 0 for v in values.values())
        return {"passes": count >= config["min_positive"], "symbols_positive": count,
                "symbols_net_r": values, "note": None}
    signals = {k: v for k, v in variants.items()
               if control_family is None or not matches(v["settings"], {"family": control_family})}
    cells = [v for v in signals.values() if matches(v["settings"], config["primary"])]
    primary = report(selected(cells[0]["trades"], config.get("symbol")),
                     start, end, None, halves) if len(cells) == 1 else None
    # Preserve the strategy-14 breadth report's descriptive metadata.
    if primary is not None:
        primary["family_wise_level"] = .01
    return {"passes": primary is not None and primary["net_r"]["normal"] > 0,
            "primary": primary,
            "cells_net_r": {k: net(selected(v["trades"], config.get("symbol")))
                            for k, v in signals.items()},
            "note": None if primary is not None else "missing or ambiguous breadth primary cell"}


def _shift(trade, edge):
    if is_dataclass(trade):
        return replace(trade, r_net=trade.r_net + edge)
    out = copy.copy(trade)
    out.r_net += edge
    return out


def pipeline_controls(signal, longs, shorts, count, start, end):
    """Negative then positive fake signals, scored using the production reports."""
    if count < 1 or not signal:
        raise ValueError("pipeline controls require positive count and nonempty primary")
    pool = np.array([t.r_net for t in (*longs, *shorts)], dtype=float)
    if len(pool) < 2:
        raise ValueError("pipeline controls require at least two control trades")
    sd = float(pool.std(ddof=1))
    edge = DETECTABLE_EDGE_Z * sd / math.sqrt(len(signal))
    maps = []
    for part in (longs, shorts):
        by_date = {t.entry_time.astimezone(BERLIN).date(): t for t in part}
        if len(by_date) != len(part):
            raise ValueError("ambiguous duplicate control entry dates")
        maps.append(by_date)
    days = sorted(maps[0].keys() & maps[1].keys())
    if len(days) < len(signal):
        raise ValueError("insufficient shared control entry dates")
    n_long = sum(t.direction == "long" for t in signal)
    rng = np.random.default_rng(CONTROL_SEED)
    result = {"count": count, "seed": CONTROL_SEED, "sd": sd, "n": len(signal), "edge": edge}
    for label, shift in (("negative", 0.), ("positive", edge)):
        passed = dict.fromkeys(("mean_positive", "bootstrap_lower_positive", "effect_not_drift", "all_three"), 0)
        for _ in range(count):
            draws = rng.choice(len(days), size=len(signal), replace=False)
            fake = [_shift(maps[int(i >= n_long)][days[int(index)]], shift)
                    for i, index in enumerate(draws)]
            r = variant_report(fake, start, end)
            diff = control_difference(fake, longs, shorts)
            gates = [r["mean_net_r"] > 0, r["bootstrap"]["lower_2_5"] > 0,
                     diff is not None and diff["lower_2_5"] > 0]
            for name, value in zip(passed, (*gates, all(gates)), strict=True):
                passed[name] += int(value)
        result[label] = {k: v / count for k, v in passed.items()}
    return result


def evaluate(variants, breadth_variants, start, end, failures, config, *, controls=0):
    """Report signal gates; absent optional gates are null and do not affect verdicts."""
    if "min_trades" not in config:
        raise ValueError("[gates] requires min_trades")
    if controls < 0:
        raise ValueError("controls must be nonnegative")
    control = config.get("control")
    control_family = control["family"] if control is not None else None
    out = {}
    for key, variant in variants.items():
        settings = variant["settings"]
        trades = selected(variant["trades"], config.get("symbol"))
        r = report(trades, start, end, None if failures is None else failures[key], config.get("halves"))
        row = {"settings": settings, "report": r, "advances": False, "notes": []}
        out[key] = row
        if control_family is not None and matches(settings, {"family": control_family}):
            row["verdict"] = "control"
            continue
        matched = matched_controls(variants, settings, control, config.get("symbol")) if control else None
        diff = control_difference(trades, *matched) if matched is not None else None
        if control is not None and diff is None:
            row["notes"].append("missing or ambiguous control cells or insufficient control trades")
        breadth = breadth_report(breadth_variants, variant["trades"], config["breadth"],
                                 start, end, config.get("halves"), control_family) if "breadth" in config else None
        if breadth and breadth["note"]:
            row["notes"].append(breadth["note"])
        gates = {
            "positive_normal_and_doubled": all(r["net_r"][s or "normal"] > 0 for s in STRESSES),
            "positive_both_halves": all(x > 0 for x in r["halves_net_r"]) if "halves" in config else None,
            "effect_not_drift": diff is not None and diff["lower_2_5"] > 0 if control is not None else None,
            "breadth": breadth["passes"] if breadth is not None else None,
            "best_date_removal_positive": all(x > 0 for x in r["net_r_without_best_dates"].values()),
            "min_trades": len(trades) >= config["min_trades"],
            "no_data_integrity_failure": (failures is not None and not failures[key])
            if "integrity_max_gap" in config else None,
        }
        primary = "primary" in config and matches(settings, config["primary"])
        row.update(gates=gates, control_difference=diff, breadth=breadth, primary=primary,
                   skipped_integrity="integrity_max_gap" in config and failures is None)
        if not gates["min_trades"]:
            verdict = "not_enough_evidence"
        elif not trades or r["mean_net_r"] <= 0 or r["bootstrap"]["lower_2_5"] <= 0 or gates["effect_not_drift"] is False:
            verdict = "falsified"
        elif primary and all(v for v in gates.values() if v is not None):
            verdict = "advances"
        else:
            verdict = "rejected"
        row["verdict"], row["advances"] = verdict, verdict == "advances"
        if controls and primary:
            row["controls"] = None
            if matched is None:
                row["notes"].append("pipeline controls unavailable: no matched controls")
            else:
                try:
                    row["controls"] = pipeline_controls(trades, *matched, controls, start, end)
                except ValueError as exc:
                    row["notes"].append(f"pipeline controls unavailable: {exc}")
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder", type=Path)
    parser.add_argument("--breadth-folder", type=Path)
    parser.add_argument("--skip-integrity", action="store_true")
    parser.add_argument("--controls", type=int, default=0)
    args = parser.parse_args(argv)
    if args.controls < 0:
        parser.error("--controls must be nonnegative")
    research = json.loads((args.folder / "research.json").read_text(encoding="utf-8"))
    grid = Path(research["grid_file"])
    if not grid.is_file() and not grid.is_absolute():
        grid = args.folder / grid
    config = tomllib.loads(grid.read_text(encoding="utf-8")).get("gates")
    if config is None:
        raise ValueError(f"{grid}: missing [gates] table")
    if not isinstance(config, dict):
        raise TypeError(f"{grid}: [gates] must be a table")
    if "min_trades" not in config:
        raise ValueError("[gates] requires min_trades")
    variants = load_variants(args.folder)
    # _name is shared with the legacy loader and defines cell labels.
    variants = {_name(v["settings"]): v for v in variants.values()}
    breadth = load_variants(args.breadth_folder) if args.breadth_folder and (args.breadth_folder / "variants.csv").is_file() else {}
    settings_file = next(args.folder.glob("variants/*/settings.json"))
    run = json.loads(settings_file.read_text(encoding="utf-8"))["run"]
    start, end = date.fromisoformat(run["start"]), date.fromisoformat(run["end"])
    failures = None
    if "integrity_max_gap" in config and not args.skip_integrity:
        failures = {k: [] for k in variants}
        sources = SymbolSources({s: Path(d) for s, d in run["cache_dirs"].items()})
        symbols = [config["symbol"]] if "symbol" in config else run["symbols"]
        for symbol in symbols:
            data = load_m1(symbol, sources, start, end + timedelta(days=1))
            for key, variant in variants.items():
                failures[key] += integrity_failures(selected(variant["trades"], symbol), data,
                                                    max_gap_minutes=config["integrity_max_gap"])
    rows = evaluate(variants, breadth, start, end, failures, config, controls=args.controls)
    primary = [r for r in rows.values() if r.get("primary")]
    result = {
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "settings": {"gates": config, "best_dates_removed": BEST_DATES,
                     "bootstrap": {"block_trades": BLOCK, "resamples": RESAMPLES, "seed": SEED}},
        "skipped_integrity": args.skip_integrity, "variants": rows,
        "controls": primary[0].get("controls") if len(primary) == 1 else None,
        "controls_note": None if len(primary) == 1 and primary[0].get("controls") is not None
        else "pipeline controls not requested or no unique primary with matched controls",
    }
    (args.folder / "gates.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    for key, row in rows.items():
        print(key, row["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
