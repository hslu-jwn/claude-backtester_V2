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
from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from itertools import pairwise
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from backtester.analytics.bootstrap import block_bootstrap as block_bootstrap  # noqa: PLC0414 -- legacy re-export
from backtester.analytics.bootstrap import block_indices as block_indices  # noqa: PLC0414 -- legacy re-export
from backtester.analytics.bootstrap import interleaved_block_means
from backtester.analytics.records import read_trades
from backtester.data.sources import SymbolSources
from backtester.tools.alternating_path_gates import (
    STRESSES,
    _valid,
    halves,
    integrity_failures,
    net,
)
from backtester.tools.entry_screen import load_m1

BEST_DATES = 5
BLOCK, RESAMPLES, SEED = 5, 10_000, 2026110
NEW_YORK = ZoneInfo("America/New_York")
ROLLOVER_GAP_START = time(16, 55)  # FTMO daily break 16:55-17:05 New York


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
            # first and last missing minute inside 16:55-18:00 New York (the user, 2026-11-13)
            start = datetime.fromtimestamp(int(left + 60), UTC).astimezone(NEW_YORK)
            end = datetime.fromtimestamp(int(right - 60), UTC).astimezone(NEW_YORK)
            if start.date() != end.date() or start.time() < ROLLOVER_GAP_START or end.hour >= 18:
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
                "halves_net_r": [net(h) for h in halves(part, start, end)],
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
    means = interleaved_block_means([a, b], BLOCK, RESAMPLES, np.random.default_rng(SEED))
    diffs = means[:, 0] - means[:, 1]
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



def evaluate_energy(variants, start, end, failures, records, strict_failures=None) -> dict:
    """Score report cells against matching disjoint controls; unknown integrity fails."""
    padded = None if failures is None else {vid: failures.get(vid, {}) for vid in variants}
    out = evaluate(variants, start, end, padded, "USOIL", 150, 1, strict_failures)
    for vid, variant in variants.items():
        row = out[vid]
        settings = variant["settings"]
        if settings.get("days") != "report":
            row["advances"] = False
            row["notes"].append("control cell is not an event hypothesis")
            continue
        rest = {k: v for k, v in settings.items() if k != "days"}
        matches = [(key, v) for key, v in variants.items() if v["settings"].get("days") == "control"
                   and {k: x for k, x in v["settings"].items() if k != "days"} == rest]
        mine = [t for t in variant["trades"] if t.symbol == "USOIL"]
        control = [t for t in matches[0][1]["trades"] if t.symbol == "USOIL"] if len(matches) == 1 else []
        dates = lambda ts: {t.entry_time.astimezone(NEW_YORK).date() for t in ts}
        diff = difference_bootstrap(mine, control) if not dates(mine) & dates(control) else None
        row["baseline_difference"] = diff
        row["gates"]["effect_not_drift"] = diff is not None and diff["lower_2_5"] > 0
        row["gates"]["breadth"] = row["symbols"].get("UKOIL", {}).get("net_r", {}).get("normal", 0) > 0
        control_id = matches[0][0] if len(matches) == 1 else None
        known = (failures is not None and records is not None and control_id is not None
                 and all(key in failures and key in records for key in (vid, control_id)))
        row["gates"]["no_data_integrity_failure"] = bool(
            known and all(not any(failures[key].values())
            and not any(r.get("integrity_failed") or r.get("defects") for r in records[key])
            for key in (vid, control_id))
        )
        row["anchor"] = (settings.get("family") in ("F", "V")
                         and float(settings.get("k", 0)) == 0.15
                         and float(settings.get("stop_atr", 0)) == 1.0)
        row["advances"] = row["anchor"] and all(row["gates"].values())
    return out



DAILY_SYMBOLS = ("US500", "NAS100", "GER40", "UK100", "JP225", "AUS200")
TS_SYMBOLS = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "US500", "NAS100")


def date_cluster_bootstrap(trades) -> dict | None:
    """Bootstrap pooled UTC entry-date clusters. Spec: strategy-daily_reversal.md > Gates."""
    clusters = defaultdict(list)
    for trade in trades:
        clusters[trade.entry_time.astimezone(UTC).date()].append(trade.r_net)
    if not clusters:
        return None
    groups = [clusters[d] for d in sorted(clusters)]
    sums = np.array([sum(group) for group in groups])
    counts = np.array([len(group) for group in groups])
    rng = np.random.default_rng(13)
    samples = rng.integers(0, len(groups), size=(RESAMPLES, len(groups)))
    means = sums[samples].sum(axis=1) / counts[samples].sum(axis=1)
    return {"lower_2_5": float(np.quantile(means, 0.025)),
            "trades": len(trades), "clusters": len(groups), "seed": 13,
            "resamples": RESAMPLES}



def _daily_report(trades, start, end):
    report = variant_report(trades, start, end)
    begin = datetime.combine(start, time.min, UTC)
    midpoint = begin + (datetime.combine(end + timedelta(days=1), time.min, UTC) - begin) / 2

    def entry_halves(items):
        return [net([t for t in items if t.entry_time < midpoint]),
                net([t for t in items if t.entry_time >= midpoint])]

    report["halves_net_r"] = entry_halves(trades)
    for direction, detail in report["by_direction"].items():
        detail["halves_net_r"] = entry_halves(
            [t for t in trades if getattr(t, "direction", None) == direction]
        )
    return report


def evaluate_daily_reversal(normal, stressed, start, end, integrity, covered_symbols,
                            *, setup="E8") -> dict:
    """Score supplied independent reruns; integrity must be positively established externally."""
    pooled = _daily_report(normal, start, end)
    pool = TS_SYMBOLS if setup == "TS" else DAILY_SYMBOLS
    symbols = {symbol: _daily_report([t for t in normal if t.symbol == symbol], start, end)
               for symbol in pool}
    bootstrap = date_cluster_bootstrap(normal)
    doubled = None if stressed is None else _daily_report(stressed, start, end)
    covered = set(covered_symbols) == set(pool)
    gates = {
        "positive_normal_and_doubled": pooled["net_r"]["normal"] > 0 and doubled is not None
        and doubled["net_r"]["normal"] > 0,
        "positive_both_halves": all(x > 0 for x in pooled["halves_net_r"]),
        "breadth": covered and sum(r["net_r"]["normal"] > 0 for r in symbols.values())
        >= (5 if setup == "TS" else 4),
        "best_date_removal_positive": pooled["net_r_without_best_dates"]["normal"] > 0,
        "bootstrap_positive": bootstrap is not None and bootstrap["lower_2_5"] > 0,
        "min_trades": len(normal) >= (150 if setup == "TS" else 80),
        "integrity": integrity is True and covered,
    }
    return {"pooled": pooled, "doubled": doubled, "symbols": symbols,
            "date_cluster_bootstrap": bootstrap, "gates": gates,
            "advances": all(gates.values())}



def daily_doubled_costs(costs):
    """Double specified trading costs, including all spread-table values."""
    fields = ("spread", "slippage", "commission_per_lot", "commission_pct_per_side",
              "swap_long_per_lot", "swap_short_per_lot", "swap_long_pct_year",
              "swap_short_pct_year")
    symbols = {name: replace(value, **{f: 2 * getattr(value, f) for f in fields})
               for name, value in costs.symbols.items()}
    table = costs.spread_table
    if table is not None:
        values = {symbol: {year: {hour: 2 * value for hour, value in hours.items()}
                           for year, hours in years.items()}
                  for symbol, years in table.values.items()}
        table = replace(table, values=values)
    return replace(costs, symbols=symbols, spread_table=table)


def daily_integrity_failures(trades, data):
    """Check the exit candle and observed OHLC in (entry, exit]; gaps are not audited."""
    bad = []
    for trade in trades:
        first = int(trade.entry_time.timestamp())
        last = int(trade.exit_time.timestamp()) - 60
        lo = np.searchsorted(data.open_s, first, side="left")
        hi = np.searchsorted(data.open_s, last, side="right")
        if hi == lo or data.open_s[hi - 1] != last or not _valid(data, np.arange(lo, hi)).all():
            bad.append(trade)
    return bad


def daily_cli(folder, rows, start, end, run, skip_integrity):
    from backtester.settings import from_dict
    from backtester.tools.research import run_period

    sources = SymbolSources({s: Path(d) for s, d in run["cache_dirs"].items()})
    symbols = run["symbols"]
    data = {} if skip_integrity else {
        symbol: load_m1(symbol, sources, start, end + timedelta(days=1)) for symbol in symbols
    }
    cached = {s: set(sources.cached_days(s)) for s in symbols}
    missing_days = {s: sum(1 for i in range((end - start).days + 1)
                           if (day := start + timedelta(days=i)).weekday() < 5
                           and day not in cached[s]) for s in symbols}
    output = {}
    for row in rows:
        folder_v = folder / "variants" / row["variant_id"]
        raw = json.loads((folder_v / "settings.json").read_text(encoding="utf-8"))
        settings = from_dict(raw)
        costs = daily_doubled_costs(settings.engine.costs)
        stressed_settings = replace(settings, engine=replace(settings.engine, costs=costs))
        stressed_run = run_period(symbols, start, end, stressed_settings, sources, workers=1)
        normal = read_trades(folder_v)
        records_path = folder_v / "sessions.json"
        records = json.loads(records_path.read_text(encoding="utf-8")) if records_path.exists() else None
        failed = []
        if not skip_integrity:
            for symbol in symbols:
                failed.extend(daily_integrity_failures([t for t in normal if t.symbol == symbol], data[symbol]))
                failed.extend(daily_integrity_failures([t for t in stressed_run.trades if t.symbol == symbol], data[symbol]))
        stress_records = [r for run_ in stressed_run.runs.values() for r in run_.sessions]
        normal_records = [] if records is None else [r for group in records.values() for r in group]
        defects = [r for r in normal_records + stress_records
                   if r.get("kind") in ("missing_exit_candle", "censored_position")]
        integrity = (not skip_integrity and records is not None and set(records) == set(symbols)
                     and not failed and not defects)
        setup = settings.strategy.setup
        if setup == "TS":
            # No exchange-calendar/interior-coverage audit exists in this CLI yet.
            # Unknown integrity must never award a TS pass from exit-only checks.
            integrity = False
        report = evaluate_daily_reversal(normal, stressed_run.trades, start, end, integrity,
                                         symbols, setup=setup)
        report["integrity_details"] = {"trade_failures": len(failed),
            "strategy_defects": len(defects),
            "missing_weekday_cache_days": missing_days,
            "exchange_calendar_audited": False}
        key = _name({k[4:]: v for k, v in row.items() if k.startswith("set.")})
        output[key] = report
        print(key, "advances" if report["advances"] else "rejected", report["gates"], flush=True)
    return {"period": {"start": start.isoformat(), "end": end.isoformat()}, "variants": output}

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("folder", type=Path)
    p.add_argument("--mode", choices=("timed_hold", "energy_report", "daily_reversal"), default="timed_hold")
    p.add_argument("--primary-symbol")
    p.add_argument("--min-trades", type=int)
    p.add_argument("--min-breadth", type=int)
    p.add_argument("--skip-integrity", action="store_true")
    args = p.parse_args(argv)
    if args.mode == "energy_report":
        if (args.primary_symbol not in (None, "USOIL") or args.min_trades not in (None, 150)
                or args.min_breadth not in (None, 1)):
            p.error("energy_report has fixed primary USOIL, 150 trades and UKOIL breadth")
        args.primary_symbol, args.min_trades, args.min_breadth = "USOIL", 150, 1
    elif args.mode == "timed_hold" and (args.primary_symbol is None or args.min_trades is None or args.min_breadth is None):
        p.error("timed_hold requires --primary-symbol, --min-trades and --min-breadth")
    with (args.folder / "variants.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    variants = {}
    records = {}
    for row in rows:
        settings = {k[4:]: v for k, v in row.items() if k.startswith("set.")}
        if row.get("family"):  # [[grids]] families differ by their base, not by set.* columns
            settings = {"family": row["family"], **settings}
        key = _name(settings)
        if key in variants:
            raise SystemExit(f"two variants share the key {key!r}; gates need distinct cells")
        session_path = args.folder / "variants" / row["variant_id"] / "sessions.json"
        if args.mode == "energy_report" and session_path.is_file():
            session_data = json.loads(session_path.read_text(encoding="utf-8"))
            if all(symbol in session_data for symbol in ("USOIL", "UKOIL")):
                records[key] = [r for group in session_data.values() for r in group]
        variants[key] = {
            "settings": settings,
            "trades": read_trades(args.folder / "variants" / row["variant_id"]),
        }
    some = next(iter(args.folder.glob("variants/*/settings.json")))
    run = json.loads(some.read_text(encoding="utf-8"))["run"]
    start, end = date.fromisoformat(run["start"]), date.fromisoformat(run["end"])
    if args.mode == "daily_reversal":
        result = daily_cli(args.folder, rows, start, end, run, args.skip_integrity)
        (args.folder / "gates.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 0
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
            **({"family_wise_level": 0.025} if args.mode == "energy_report" else {}),
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
    if args.mode == "energy_report":
        result["variants"] = evaluate_energy(
            variants, start, end, failures, records, strict_failures=strict_failures
        )
    (args.folder / "gates.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    for vid, row in result["variants"].items():
        print(vid, "advances" if row["advances"] else "rejected", row["gates"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
