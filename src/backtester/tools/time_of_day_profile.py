"""Screen weekday local-hour returns against modeled round-trip costs.

Development data only. Candle timestamps denote opens; returns use candle closes.
Spec: research-runner.md > data split; strategy-timed-hold.md > Run 1 follow-ups.
"""
from __future__ import annotations

import argparse
import csv
import math
from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import numpy as np

from backtester.analytics.entry_screen import M1Data
from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.costs import CostConfig
from backtester.tools.entry_screen import DEV_END, START, load_m1

FIELDS = ("hour", "n", "mean_bp", "t", "mean_bp_first", "t_first", "mean_bp_second", "t_second")


def _stats(values: list[float]) -> tuple[int, float, float]:
    n = len(values)
    if not n:
        return 0, math.nan, math.nan
    mean = float(np.mean(values))
    sd = float(np.std(values, ddof=1)) if n > 1 else 0.0
    return n, mean, mean / (sd / math.sqrt(n)) if sd > 0 else math.nan


def profile(data: M1Data, zone: ZoneInfo, start: date, end: date, split: date) -> list[dict]:
    """Return hourly statistics from actual M1 closes; missing endpoints are skipped."""
    # Only hour-boundary closes can contribute; use UTC timestamps to join exact instants.
    closes = data.close_s
    indices = np.flatnonzero(closes % 900 == 0)
    prices = {int(closes[i]): float(data.close[i]) for i in indices}
    samples: list[list[tuple[date, float, float]]] = [[] for _ in range(24)]
    for stamp, p0 in sorted(prices.items()):
        local = datetime.fromtimestamp(stamp, UTC).astimezone(zone)
        day = local.date()
        if not start <= day <= end or day.weekday() >= 5 or local.minute != 0:
            continue
        # Join the next local clock hour, not an arbitrary later available candle.
        p1 = prices.get(stamp + 3600)
        if p1 is None or not (math.isfinite(p0) and math.isfinite(p1) and p0 > 0 and p1 > 0):
            continue
        samples[local.hour].append((day, p1 - p0, 10000 * math.log(p1 / p0)))
    rows = []
    for hour, values in enumerate(samples):
        n, mean, t = _stats([v[2] for v in values])
        nf, mf, tf = _stats([v[2] for v in values if v[0] < split])
        ns, ms, ts = _stats([v[2] for v in values if v[0] >= split])
        _, mean_price, _ = _stats([v[1] for v in values])
        rows.append({"hour": hour, "n": n, "mean_bp": mean, "t": t, "n_first": nf, "mean_bp_first": mf,
                         "t_first": tf, "n_second": ns, "mean_bp_second": ms, "t_second": ts,
                         "mean_price": mean_price})
    return rows


def cost_bp(symbol: str, price: float) -> float:
    """Stop-out round trip at median price, using the default fixed-spread fallback."""
    config = CostConfig()
    cost = (config.spread(symbol, price=price) + 2 * config.slippage(symbol, price)
            + config.commission_price(symbol, price))
    return 10000 * cost / price


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("symbols", nargs="+")
    parser.add_argument("--zone", required=True)
    parser.add_argument("--start", type=date.fromisoformat, default=START)
    parser.add_argument("--end", type=date.fromisoformat, default=DEV_END)
    parser.add_argument("--split", type=date.fromisoformat)
    parser.add_argument("--out", type=Path, default=Path("results/tod_profile"))
    args = parser.parse_args(argv)
    if args.end > DEV_END:
        raise SystemExit(f"--end must be on or before {DEV_END} (development period only)")
    if args.start > args.end:
        parser.error("--start must be on or before --end")
    try:
        zone = ZoneInfo(args.zone)
    except ZoneInfoNotFoundError:
        parser.error(f"unknown time zone: {args.zone}")
    split = args.split or (args.start + (args.end - args.start) / 2)
    report = ["# Time-of-day profile", "", (f"Period: {args.start} to {args.end}; "
              f"split: {split}; zone: {args.zone}."), "",
              ("Cost uses the default fixed spread (no time supplied), twice slippage, "
              "and round-trip commission at the median M1 close."), ""]
    args.out.mkdir(parents=True, exist_ok=True)
    for symbol in args.symbols:
        data = load_m1(symbol, DEFAULT_SOURCES, args.start, args.end)
        rows = profile(data, zone, args.start, args.end, split)
        valid = data.close[np.isfinite(data.close) & (data.close > 0)]
        if not len(valid):
            raise SystemExit(f"{symbol}: no positive finite close prices")
        cost = cost_bp(symbol, float(np.median(valid)))
        with (args.out / f"{symbol}.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        exceeds = ", ".join(str(r["hour"]) for r in rows if abs(r["mean_bp"]) > cost) or "none"
        report += [f"## {symbol}", "", f"Cost: {cost:.4f} bp. Hours exceeding cost: {exceeds}.",
                   "", "| Hour | n | Mean bp | t | First mean bp | First t | Second mean bp | Second t |",
                   "|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for r in rows:
            report.append(f"| {r['hour']} | {r['n']} | {r['mean_bp']:.4f} | {r['t']:.3f} | "
                          f"{r['mean_bp_first']:.4f} | {r['t_first']:.3f} | "
                          f"{r['mean_bp_second']:.4f} | {r['t_second']:.3f} |")
        report.append("")
    path = args.out / "report.md"
    path.write_text("\n".join(report), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
