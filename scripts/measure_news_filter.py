"""Measure the news blackout filter (V2.4e) on the seven 2023 golden setups.

    .venv/Scripts/python.exe scripts/measure_news_filter.py > results/measure_news_filter.log 2>&1

Filter off (the default) against on (block_entries, High 2 / 2 min, Medium none, the user's
windows of 2026-10-27) with the cleaned calendar `data/news/economic_events.csv`. Current
defaults otherwise; no default change, no trial-log line. Writes results/news_filter.md / .csv.
A script file, not stdin: the multiprocessing workers crash on stdin scripts.
"""

from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path
from time import perf_counter

from backtester.analytics.metrics import BREAK_EVEN_TOL
from backtester.data.sources import DEFAULT_SOURCES
from backtester.runner import RunSettings, run_backtests
from backtester.strategy.registry import default_config
from backtester.tools.golden import GoldenConfig

OUTPUT = Path("results/news_filter")


def main() -> int:
    config = GoldenConfig()
    rows = []
    for name, symbols in config.strategies:
        base = None
        for label, enabled in (("off", False), ("on", True)):
            started = perf_counter()
            settings = RunSettings(strategy=default_config(name))
            news = replace(settings.engine.news, enabled=enabled)
            settings = replace(settings, engine=replace(settings.engine, news=news))
            result = run_backtests(
                symbols, config.start, config.end, settings, DEFAULT_SOURCES, workers=1
            )
            n = len(result.trades)
            net = sum(t.r_net for t in result.trades)
            base = (n, net) if base is None else base
            rows.append(
                {
                    "strategy": name, "news": label, "trades": n,
                    "wins": sum(t.r_net > BREAK_EVEN_TOL for t in result.trades),
                    "net_r": net, "avg_r": net / n if n else 0.0,
                    "delta_trades": n - base[0], "delta_net_r": net - base[1],
                }
            )  # fmt: skip
            print(f"{name} {label}: {n} trades, net {net:.2f} R ({perf_counter() - started:.0f}s)",
                  flush=True)  # fmt: skip
            write(rows)
    return 0


def write(rows: list[dict]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.with_suffix(".csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# News filter measurement (V2.4e)",
        "",
        "Golden setups 2023, current defaults; news filter off (default) vs on (block entries,",
        "High 2 / 2 min, Medium none). Changes are against the filter off.",
        "",
        "| Strategy | News | Trades | Wins | Net R | Avg R | Change trades | Change R |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
        *(
            f"| {r['strategy']} | {r['news']} | {r['trades']} | {r['wins']} | {r['net_r']:.2f} "
            f"| {r['avg_r']:.4f} | {r['delta_trades']:+d} | {r['delta_net_r']:+.2f} |"
            for r in rows
        ),
    ]
    OUTPUT.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
