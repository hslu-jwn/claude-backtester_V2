"""Skill diagnostic IO. Spec: research-runner.md > Skill vs trend, and bounds."""

import csv
import json
from datetime import date

import numpy as np

from backtester.analytics.bounds import BoundsConfig, log_pf_bounds, mean_bounds
from backtester.analytics.daily import daily_net_r_mtm, weekdays
from backtester.analytics.detrend import detrend, load_drifts, position_bias
from backtester.analytics.records import read_trades


def calculate(trades, start, end, sources, folder=None, *, symbols=(), config=None):
    cfg = config or BoundsConfig()
    trades = list(trades)
    symbols = sorted(set(symbols) | {t.symbol for t in trades})
    daily = None
    path = folder / "daily.csv" if folder else None
    if path is not None and path.is_file():
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
            if [r.get("date") for r in rows] != [d.isoformat() for d in weekdays(start, end)]:
                raise ValueError("daily.csv dates must match the complete run period in order")
            if "net_r_mtm" in (reader.fieldnames or []):
                daily = np.array([float(r["net_r_mtm"]) for r in rows])
    if daily is None:
        daily, _ = daily_net_r_mtm(trades, start, end, sources)
    drifts = load_drifts(symbols, start, end, sources)
    trend = detrend(trades, drifts)
    for symbol in symbols:
        trend["symbols"].setdefault(symbol, detrend([], {})["total"])
    bias = position_bias(trades, start, end, symbols)
    for s, row in bias["symbols"].items():
        drift = drifts.get(s)
        row["no_skill_price_per_day"] = (
            (row["long"] - row["short"]) * drift * 86400
            if drift is not None and row["long"] is not None
            else None
        )
    daily_mean = mean_bounds(daily, cfg)
    log_pf = log_pf_bounds(daily, cfg)
    total = trend["total"]
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "source": "marked_to_market",
        "drifts": drifts,
        "unavailable_symbols": [s for s in symbols if drifts.get(s) is None],
        "trend": trend,
        "position_bias": bias,
        "daily_mean": daily_mean,
        "trade_mean": mean_bounds([t.r_net for t in trades], cfg),
        "log_pf": log_pf,
        "scores": {
            "detrended_net_r": total["detrended_net_r"],
            "lower95_mean_daily_r": daily_mean["lower95_bca"],
            "log_pf": log_pf["estimate"],
        },
        "flags": ["skill_is_trend"]
        if total["net_r"] > 0
        and total["detrended_net_r"] is not None
        and total["detrended_net_r"] <= 0
        else [],
    }


def write(result, folder):
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "skill_bounds.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def _number(value):
    return "n/a" if value is None else f"{value:.6g}"


def tables(result):
    """Shared report tables (headers, rows), with explicit units."""
    trend = result["trend"]
    yield (
        ["Symbol", "Raw net R", "Trend R", "Detrended net R", "Raw mean R", "Detrended mean R"],
        [
            [
                s,
                *[
                    _number(r[k])
                    for k in ("net_r", "trend_r", "detrended_net_r", "avg_r", "detrended_avg_r")
                ],
            ]
            for s, r in [*trend["symbols"].items(), ("TOTAL", trend["total"])]
        ],
    )
    yield (
        ["Symbol", "Long time share", "Short time share", "Flat time share", "No-skill price/day"],
        [
            [s, *[_number(r.get(k)) for k in ("long", "short", "flat", "no_skill_price_per_day")]]
            for s, r in [
                *result["position_bias"]["symbols"].items(),
                ("TOTAL", result["position_bias"]["total"]),
            ]
        ],
    )
    yield (
        [
            "Statistic",
            "n",
            "Estimate",
            "BCa lower 90%",
            "BCa lower 95%",
            "t lower 90%",
            "t lower 95%",
        ],
        [
            [
                label,
                str(r["n"]),
                *[
                    _number(r.get(k))
                    for k in ("estimate", "lower90_bca", "lower95_bca", "lower90_t", "lower95_t")
                ],
            ]
            for label, r in [
                ("Daily MTM mean R", result["daily_mean"]),
                ("Trade mean R", result["trade_mean"]),
                ("Daily log PF", result["log_pf"]),
            ]
        ],
    )


def notes(result):
    cfg = result["daily_mean"]["config"]
    out = [
        (
            f"IID BCa; jackknife acceleration; boots={cfg['boots']}, seed={cfg['seed']}. "
            "One-sided bounds; no correction for dependence or selection. Position from trade intervals."
        )
    ]
    for key in ("daily_mean", "trade_mean", "log_pf"):
        if result[key]["reason"]:
            out.append(f"{key}: {result[key]['reason']}.")
    if result["unavailable_symbols"]:
        out.append(
            "Drift unavailable (fewer than two cached closes): "
            + ", ".join(result["unavailable_symbols"])
        )
    out.extend(result["flags"])
    return out


def markdown(result, label=""):
    lines = ["", f"## Skill vs trend, and bounds {label}".rstrip(), "", *notes(result), ""]
    for headers, rows in tables(result):
        lines += [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        lines += ["| " + " | ".join(row) + " |" for row in rows]
        lines.append("")
    return lines


def research_results(folder, results_dir, info, rows, tests, start, end, sources, symbols):
    """Enrich selected rows only, without executing or selecting variants or logging trials."""
    info["skill_bounds"] = {}
    chosen = info.get("chosen")
    if chosen is None:
        write({}, folder)
        return
    selected = next(r for r in rows if r["variant_id"] == chosen["id"])
    records = [("development", folder / "variants" / chosen["id"], start, end, selected)]
    records += [
        (
            f"test {r['test_run']}",
            results_dir / r["run_folder"],
            date.fromisoformat(r["start"]),
            date.fromisoformat(r["end"]),
            r,
        )
        for r in tests
    ]
    for label, target, a, b, row in records:
        result = calculate(read_trades(target), a, b, sources, target, symbols=symbols)
        write(result, target)
        if label == "development":
            write(result, results_dir / chosen["dev_run"])
        info["skill_bounds"][label] = result
        row.update(result["scores"])
        old_flags = [f for f in row.get("flags", "").split(";") if f and f != "skill_is_trend"]
        row["flags"] = ";".join([*old_flags, *result["flags"]])
        card_path = target / "scorecard.json"
        if card_path.is_file():
            data = json.loads(card_path.read_text(encoding="utf-8"))
            data["scorecard"].update(result["scores"])
            card_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    write(info["skill_bounds"], folder)
