"""Compare fill-probe demo trades with the engine (ROADMAP 12.5)."""

from __future__ import annotations

import argparse
import itertools
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from backtester.cli import utf8_output
from backtester.core.models import Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.data.sources import CHART_SOURCES
from backtester.engine.backtest import run_backtest
from backtester.engine.costs import CostConfig
from backtester.paths import RESULTS_DIR
from backtester.strategy.fill_probe.config import FillProbeConfig
from backtester.strategy.fill_probe.strategy import FillProbe
from backtester.tools.fill_report import (
    DEFAULT_PREFIX,
    DEFAULT_SINCE,
    _md,
    _num,
    _parse_time,
    _read,
    _ticket,
)

# a stop is "different" beyond this share of the demo's stop distance; below it is the broker's
# price rounding (2026-10-27..31: median 0.0001 R, p90 0.018 R where the direction matched)
STOP_TOLERANCE_R = 0.01
FIELDS = ("sl", "entry_fill", "exit_time", "exit_reason", "exit_price", "r_gross", "r_net")
COLUMNS = (
    ["symbol", "signal_time", "side", "status"]
    + [f"{s}_{f}" for s in ("demo", "engine") for f in FIELDS]
    + [
        "diff_sl",
        "diff_entry",
        "diff_entry_model_units",
        "diff_exit_seconds",
        "diff_exit_price",
        "diff_r_net",
        "explanation",
    ]
)


def load_demo(live_dir, since, until, prefix, symbols):
    papers, trades = [], []
    for day in sorted(live_dir.glob("*")):
        if not day.is_dir():
            continue
        p, t = _read(day / "paper.csv"), _read(day / "trades.csv")
        if p is not None:
            papers.extend(p.to_dict("records"))
        if t is not None:
            trades.extend(t.to_dict("records"))
    # Running windows use all paper rows, regardless of prefix or symbol.
    window = [dict(p, time_utc=_parse_time(p["time_utc"])) for p in papers]
    selected = [
        p
        for p in window
        if p.get("comment", "").startswith(prefix)
        and p["time_utc"] >= since
        and (until is None or p["time_utc"] <= until)
        and (not symbols or p["symbol"] in symbols)
    ]
    by_ticket = {_ticket(t["ticket"]): t for t in trades}
    demos = []
    for p in selected:
        if p["status"] != "filled":
            continue
        t = by_ticket.get(_ticket(p.get("ticket")), {})
        row = dict(p, signal_time=p["time_utc"])
        for f in FIELDS:
            value = t.get(f, p.get("real_fill", "") if f == "entry_fill" else p.get(f, ""))
            row[f] = (
                (_parse_time(value) if value else None)
                if f == "exit_time"
                else value
                if f == "exit_reason"
                else _num(value)
            )
        demos.append(row)
    return window, demos


def _engine_row(t):
    return {
        "symbol": t.symbol,
        "signal_time": t.entry_time,
        "side": "buy" if t.direction is Direction.BULLISH else "sell",
        "sl": t.initial_stop,
        "entry_fill": t.entry_fill,
        "exit_time": t.exit_time,
        "exit_reason": t.exit_reason.value,
        "exit_price": t.exit_fill,
        "r_gross": t.r_gross,
        "r_net": t.r_net,
    }


def _running(when, paper):
    times = sorted(
        p["time_utc"] if isinstance(p["time_utc"], datetime) else _parse_time(p["time_utc"])
        for p in paper
        if _parse_time(str(p["time_utc"])).date() == when.date()
    )
    if not times or when < times[0] or when > times[-1]:
        return False
    return not any(
        a < when < b and b - a > timedelta(minutes=60) for a, b in itertools.pairwise(times)
    )


def reconcile(demos, engines, paper, candles, skipped_paper=None):
    ds = {(d["symbol"], d["signal_time"]): d for d in demos}
    es = {(e["symbol"], e["signal_time"]): e for e in engines}
    skipped = {
        (p["symbol"], _parse_time(str(p["time_utc"]))): p
        for p in (paper if skipped_paper is None else skipped_paper)
        if p["status"] == "skipped"
    }
    rows = []
    for key in sorted(ds.keys() | es.keys()):
        d, e = ds.get(key), es.get(key)
        row = dict.fromkeys(COLUMNS, "")
        row.update(
            symbol=key[0],
            signal_time=key[1],
            side=(d or e)["side"],
            status="matched" if d and e else "demo_only" if d else "engine_only",
        )
        for label, obj in (("demo", d), ("engine", e)):
            if obj:
                for f in FIELDS:
                    row[f"{label}_{f}"] = obj.get(f, "")
        if d and e:
            for f in ("sl", "exit_price", "r_net"):
                row[f"diff_{f}"] = _num(d[f]) - _num(e[f])
            entry = (_num(d["entry_fill"]) - _num(e["entry_fill"])) * (
                1 if d["side"] == "buy" else -1
            )
            row["diff_entry"] = entry
            slip = CostConfig().slippage(key[0], _num(e["entry_fill"]))
            row["diff_entry_model_units"] = entry / slip if slip else float("nan")
            if d["exit_time"] and e["exit_time"]:
                row["diff_exit_seconds"] = (d["exit_time"] - e["exit_time"]).total_seconds()
            risk = abs(_num(d["entry_fill"]) - _num(d["sl"]))
            if d["side"] != e["side"]:
                row["explanation"] = f"direction: demo {d['side']}, engine {e['side']}"
            elif d["exit_reason"] != e["exit_reason"]:
                row["explanation"] = (
                    f"exit reason: demo {d['exit_reason']}, engine {e['exit_reason']}"
                )
            elif abs(_num(d["sl"]) - _num(e["sl"])) > STOP_TOLERANCE_R * risk:
                row["explanation"] = "different stop (ATR / bars differ)"
        elif d:
            row["explanation"] = "unexplained" if key in candles else "bar missing in cache"
        else:
            row["explanation"] = (
                skipped[key].get("reason", "")
                if key in skipped
                else "bot not running"
                if not _running(key[1], paper)
                else "unexplained"
            )
        rows.append(row)
    return rows


def build_report(rows):
    counts = Counter(r["status"] for r in rows)
    out = [
        "# Demo reconciliation\n",
        "Counts: "
        + ", ".join(f"{s}: {counts[s]}" for s in ("matched", "demo_only", "engine_only"))
        + "\n",
    ]
    matched = pd.DataFrame([r for r in rows if r["status"] == "matched"])
    for title, column in (("By symbol", "symbol"), ("By exit reason (demo)", "demo_exit_reason")):
        stats = {}
        if not matched.empty:
            for key, group in matched.groupby(column, dropna=False):
                data = {
                    "matched n": len(group),
                    "exit agreement": (group.demo_exit_reason == group.engine_exit_reason).mean(),
                }
                for name in ("entry", "exit_seconds", "exit_price", "r_net"):
                    values = pd.to_numeric(group["diff_" + name], errors="coerce")
                    data[name + " median"] = values.median()
                    data[name + " p90"] = values.quantile(0.9)
                data["demo r_net sum"] = pd.to_numeric(group.demo_r_net, errors="coerce").sum(
                    min_count=1
                )
                data["engine r_net sum"] = pd.to_numeric(group.engine_r_net, errors="coerce").sum(
                    min_count=1
                )
                stats[key] = data
        out.append(f"## {title}\n" + _md(pd.DataFrame.from_dict(stats, orient="index")))
    unexplained = [r for r in rows if r["explanation"] == "unexplained"]
    out.append(f"## Unexplained\n\n{len(unexplained)} unexplained\n")
    out.append(
        "| symbol | signal time | status | explanation |\n|---|---|---|---|\n"
        + "\n".join(
            f"| {r['symbol']} | {r['signal_time']} | {r['status']} | unexplained |"
            for r in unexplained[:50]
        )
    )
    if len(unexplained) > 50:
        out.append(f"\n{len(unexplained) - 50} more\n")
    return "\n".join(out) + "\n"


def main(argv=None):
    utf8_output()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live-dir", type=Path, default=RESULTS_DIR / "live")
    ap.add_argument("--since", default=DEFAULT_SINCE)
    ap.add_argument("--until")
    ap.add_argument("--comment-prefix", default=DEFAULT_PREFIX)
    ap.add_argument("--symbols", nargs="+")
    ap.add_argument("--out", type=Path, default=RESULTS_DIR / "reconcile")
    args = ap.parse_args(argv)
    if args.out.resolve().is_relative_to(args.live_dir.resolve()):
        print("Output must be outside the live folder.")
        return 1
    since = _parse_time(args.since)
    until = _parse_time(args.until) if args.until else None
    paper, demos = load_demo(args.live_dir, since, until, args.comment_prefix, args.symbols)
    selected = [
        p
        for p in paper
        if p.get("comment", "").startswith(args.comment_prefix)
        and p["time_utc"] >= since
        and (until is None or p["time_utc"] <= until)
        and (not args.symbols or p["symbol"] in args.symbols)
    ]
    if not selected:
        print("No matching paper rows in live folder.")
        return 1
    end = datetime.combine(
        max(p["time_utc"].date() for p in selected) + timedelta(days=1), datetime.min.time(), UTC
    )
    start = datetime.combine(
        since.date() - timedelta(days=FillProbe.min_warmup_days), datetime.min.time(), UTC
    )
    engines, candle_keys = [], set()
    for symbol in sorted({p["symbol"] for p in selected}):
        adapter = CHART_SOURCES.adapter(symbol)
        cached = set(CHART_SOURCES.cached_days(symbol))
        candles = []
        day = start
        while day < end:
            if day.date() in cached:
                candles.extend(adapter.fetch(symbol, Timeframe.M1, day, day + timedelta(days=1)))
            day += timedelta(days=1)
        candle_keys.update((symbol, c.ts + Timeframe.M1.duration) for c in candles)
        if candles:
            results = run_backtest(
                FillProbe(symbol, FillProbeConfig()), [CandleSeries(symbol, Timeframe.M1, candles)]
            )
            engines.extend(
                _engine_row(t)
                for t in results
                if t.entry_time >= since and (until is None or t.entry_time <= until)
            )
    # Skipped rows must obey the same prefix and date selection as demo trades.
    rows = reconcile(demos, engines, paper, candle_keys, selected)
    args.out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=COLUMNS).to_csv(args.out / "trades.csv", index=False)
    (args.out / "report.md").write_text(build_report(rows), encoding="utf-8")
    counts = Counter(r["status"] for r in rows)
    print(
        ", ".join(f"{s}: {counts[s]}" for s in ("matched", "demo_only", "engine_only"))
        + f" -> {args.out / 'report.md'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
