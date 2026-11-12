"""The rejection gates of submission M15_ALTERNATING_PATH_BATCH v0.2.0 from its four
development cells; V2 reports them, the user decides. Spec: strategy-alternating-path.md > Gates.

    python -m backtester.tools.alternating_path_gates results/research/<alternating_path_...>

Writes `gates.json` into the research folder.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from backtester.analytics.bootstrap import block_bootstrap as block_bootstrap  # noqa: PLC0414 -- legacy re-export
from backtester.analytics.bootstrap import block_indices as block_indices  # noqa: PLC0414 -- legacy re-export
from backtester.analytics.daily import weekdays
from backtester.analytics.entry_screen import M1Data
from backtester.analytics.records import read_trades
from backtester.data.sources import SymbolSources
from backtester.tools.entry_screen import load_m1

LONDON = ZoneInfo("Europe/London")
COMPONENTS = ("spread", "commission", "slippage")
STRESSES = (None, *COMPONENTS, "all")  # None = normal costs
CENTER, NEIGHBOR = 60, 30  # holding minutes
MODES = ("FOLLOW_LAST", "FADE_LAST")
BEST_DATES = 5
MIN_TRADES = 300
MIN_SYMBOLS = 3
BLOCK, RESAMPLES, SEED = 5, 10_000, 2026014


def components(t) -> tuple[float, float, float]:
    """(spread, commission, slippage) in R. Slippage is the rest of the fill cost; conversion,
    swap and funding are inside r_net but are not trading costs."""
    fills = t.r_net + t.commission_r - t.swap_r - t.funding_r - t.conversion_r
    return t.spread_r, t.commission_r, max(0.0, t.r_gross - fills - t.spread_r)


def trade_net(t, stress: str | None = None) -> float:
    """Net R with one cost component (or "all") paid twice."""
    if stress is None:
        return t.r_net
    parts = dict(zip(COMPONENTS, components(t), strict=True))
    return t.r_net - (sum(parts.values()) if stress == "all" else parts[stress])


def net(trades, stress: str | None = None) -> float:
    return sum(trade_net(t, stress) for t in trades)


def london_date(t) -> date:
    return t.entry_time.astimezone(LONDON).date()


def halves(trades, start: date, end: date) -> tuple[list, list]:
    """Split at the UTC midpoint of [start, end + 1 day); a close on the midpoint is first."""
    begin = datetime.combine(start, datetime.min.time(), UTC)
    mid = begin + (datetime.combine(end + timedelta(days=1), datetime.min.time(), UTC) - begin) / 2
    first = [t for t in trades if t.exit_time <= mid]
    return first, [t for t in trades if t.exit_time > mid]


def best_dates(trades, n: int) -> set[date]:
    days: dict[date, float] = defaultdict(float)
    for t in trades:
        days[london_date(t)] += t.r_net
    return set(sorted(days, key=lambda d: days[d], reverse=True)[:n])


def without_dates(trades, dates: set[date]) -> list:
    return [t for t in trades if london_date(t) not in dates]


def daily_series(trades, start: date, end: date) -> np.ndarray:
    """Normal-cost net R per eligible London weekday in [start, end], zeros included."""
    days = weekdays(start, end)
    index = {d: i for i, d in enumerate(days)}
    out = np.zeros(len(days))
    for t in trades:
        if (i := index.get(london_date(t))) is not None:
            out[i] += t.r_net
    return out


def _valid(data: M1Data, i: np.ndarray) -> np.ndarray:
    o, h, lo, c = data.open[i], data.high[i], data.low[i], data.close[i]
    prices = np.stack([o, h, lo, c])
    return (
        np.isfinite(prices).all(axis=0)
        & (prices > 0).all(axis=0)
        & (h >= np.maximum(o, c))
        & (lo <= np.minimum(o, c))
        & (h >= lo)
    )


def integrity_failures(trades, data: M1Data, *, max_gap_minutes: int = 5) -> list:
    """Trades failing the M1 integrity gate. Spec: strategy-alternating-path.md > Gates."""
    bad = []
    for t in trades:
        first, last = int(t.entry_time.timestamp()), int(t.exit_time.timestamp()) - 60
        lo = np.searchsorted(data.open_s, first, side="left")
        hi = np.searchsorted(data.open_s, last, side="right")
        i = np.arange(lo, hi)
        times = data.open_s[lo:hi]
        gaps = np.diff(np.concatenate(([first - 60], times, [last + 60]))) // 60 - 1
        if (
            len(times) == 0
            or times[-1] != last
            or np.any(gaps > max_gap_minutes)
            or not _valid(data, i).all()
        ):
            bad.append(t)
    return bad


def _cell_report(trades, start: date, end: date) -> dict:
    first, second = halves(trades, start, end)
    by_half = []
    for part in (first, second):
        symbols: dict[str, float] = defaultdict(float)
        for t in part:
            symbols[t.symbol] += t.r_net
        by_half.append(
            {"net_r": net(part), "symbols_positive": sum(v > 0 for v in symbols.values())}
        )
    return {
        "trades": len(trades),
        "net_r": {s or "normal": net(trades, s) for s in STRESSES},
        "halves": by_half,
    }


def evaluate(cells: dict[tuple[str, int], list], start: date, end: date, failures: dict) -> dict:
    """Every gate per response mode (centre hold 60, neighbour hold 30)."""
    out = {"cells": {}, "modes": {}}
    for (mode, hold), trades in sorted(cells.items()):
        report = _cell_report(trades, start, end)
        report["bootstrap"] = block_bootstrap(
            daily_series(trades, start, end), BLOCK, RESAMPLES, SEED
        )
        report["data_integrity_failures"] = len(failures[mode, hold])
        report["data_integrity_examples"] = [
            t.entry_time.isoformat() + " " + t.symbol for t in failures[mode, hold][:20]
        ]
        out["cells"][f"{mode}/{hold}"] = report
    for mode in MODES:
        centre = cells[mode, CENTER]
        dates = best_dates(centre, BEST_DATES)
        cr = out["cells"][f"{mode}/{CENTER}"]
        both = [out["cells"][f"{mode}/{h}"] for h in (CENTER, NEIGHBOR)]
        removal = {
            str(h): {
                s or "normal": net(without_dates(cells[mode, h], dates), s) for s in (None, "all")
            }
            for h in (CENTER, NEIGHBOR)
        }
        gates = {
            "both_cells_positive_normal_and_doubled": all(
                v > 0 for c in both for v in c["net_r"].values()
            ),
            "centre_positive_both_halves": all(h["net_r"] > 0 for h in cr["halves"]),
            "centre_3_symbols_positive_each_half": all(
                h["symbols_positive"] >= MIN_SYMBOLS for h in cr["halves"]
            ),
            "centre_at_least_300_trades": cr["trades"] >= MIN_TRADES,
            "five_date_removal_positive": all(v > 0 for r in removal.values() for v in r.values()),
            "bootstrap_lower_above_zero": all(c["bootstrap"]["lower_2_5"] > 0 for c in both),
            "no_data_integrity_failure": all(c["data_integrity_failures"] == 0 for c in both),
        }
        out["modes"][mode] = {
            "gates": gates,
            "advances": all(gates.values()),
            "removed_dates": sorted(d.isoformat() for d in dates),
            "five_date_removal_net_r": removal,
            "opposite_mode_net_r": {
                str(h): net(cells[MODES[1 - MODES.index(mode)], h]) for h in (CENTER, NEIGHBOR)
            },
        }
    return out


def _cells(folder: Path) -> dict[tuple[str, int], list]:
    with (folder / "variants.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    cells = {}
    for row in rows:
        key = (row["set.response_mode"], int(float(row["set.holding_minutes"])))
        cells[key] = read_trades(folder / "variants" / row["variant_id"])
    if set(cells) != {(m, h) for m in MODES for h in (CENTER, NEIGHBOR)}:
        raise SystemExit(f"expected the four declared cells, found {sorted(cells)}")
    return cells


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("folder", type=Path)
    args = p.parse_args(argv)
    cells = _cells(args.folder)
    some = next(iter(args.folder.glob("variants/*/settings.json")))
    run = json.loads(some.read_text(encoding="utf-8"))["run"]
    start, end = date.fromisoformat(run["start"]), date.fromisoformat(run["end"])
    sources = SymbolSources({s: Path(d) for s, d in run["cache_dirs"].items()})
    failures = {key: [] for key in cells}
    for symbol in run["symbols"]:
        data = load_m1(symbol, sources, start, end + timedelta(days=1))
        for key, trades in cells.items():
            failures[key] += integrity_failures([t for t in trades if t.symbol == symbol], data)
    result = evaluate(cells, start, end, failures)
    result["period"] = {"start": start.isoformat(), "end": end.isoformat()}
    result["settings"] = {
        "bootstrap": {
            "block_dates": BLOCK,
            "resamples": RESAMPLES,
            "seed": SEED,
            "gate": "lower_2_5",
        },
        "best_dates_removed": BEST_DATES,
    }
    (args.folder / "gates.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    for mode, row in result["modes"].items():
        print(mode, "advances" if row["advances"] else "rejected", row["gates"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
