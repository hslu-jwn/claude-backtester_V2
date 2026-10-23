"""Research diagnostics. Spec: research-runner.md > Additional diagnostics.

No variant selection or execution takes place here; all measures are descriptive.
"""

from __future__ import annotations

import csv
import json
from datetime import UTC, datetime, time, timedelta
from types import SimpleNamespace

from backtester.analytics.market_classes import MARKET_CLASSES, market_class
from backtester.analytics.metrics import by_period, by_symbol, split
from backtester.analytics.robustness import (
    grid_stats,
    plateau_cell,
    plateau_index,
    shock_dates,
    shock_report,
    smooth_grid,
    smooth_series,
)
from backtester.core.models import Timeframe
from backtester.tools.research_grid import families, family_variants, resolved_values

__all__ = ["MARKET_CLASSES", "market_class"]

GRID_COLUMNS = (
    "family",
    "n",
    "mean",
    "std",
    "adjusted",
    "profitable_share",
    "robust",
    "plateau_variant",
    "plateau_net_r",
    "plateau_note",
)


def load_shocks(symbols, end, sources):
    """UTC daily OHLC from the cached M1 candles, one read per run of consecutive cached days
    (the cache has gaps), keeping ATR history across gaps. UTC days, not D1's New York
    boundary, because `shock_report` dates a trade by its UTC exit day."""
    out = {}
    for symbol in symbols:
        adapter = sources.adapter(symbol)
        daily = []
        for first, last in _blocks(d for d in sources.cached_days(symbol) if d <= end):
            start = datetime.combine(first, time(), UTC)
            stop = datetime.combine(last + timedelta(days=1), time(), UTC)
            frame = adapter.fetch_frame(symbol, Timeframe.M1, start, stop)
            if frame.empty:
                continue
            bars = frame.groupby(frame["ts"].dt.date, sort=True).agg(
                high=("high", "max"), low=("low", "min"), close=("close", "last")
            )
            daily += zip(bars.index, bars["high"], bars["low"], bars["close"], strict=True)
        out[symbol] = shock_dates(daily)
    return out


def _blocks(days):
    """(first, last) of each run of consecutive days."""
    blocks = []
    for day in sorted(set(days)):
        if blocks and day == blocks[-1][1] + timedelta(days=1):
            blocks[-1][1] = day
        else:
            blocks.append([day, day])
    return [tuple(b) for b in blocks]


def grid_rows(spec, variants, rows):
    """Owned-variant statistics, with plateaus along each family's original axes."""
    nets = {r["variant_id"]: r["net_r"] for r in rows}
    result = [
        {
            "family": "all",
            **grid_stats(list(nets.values())),
            "plateau_variant": None,
            "plateau_net_r": None,
            "plateau_note": "overall statistics only",
        }
    ]
    aliases = {d["id"]: d["retained"] for d in spec.duplicates}
    products = list(family_variants(spec)) if spec.grids else variants
    for family in families(spec):
        owned = [nets[v.id] for v in variants if v.family == family.name and v.id in nets]
        row = {
            "family": family.name,
            **grid_stats(owned),
            "plateau_variant": None,
            "plateau_net_r": None,
            "plateau_note": "",
        }
        axes = list(family.grid)
        if len(axes) > 2:
            row["plateau_note"] = "more than two axes: statistics only"
            result.append(row)
            continue
        shape = [len(family.grid[a]) for a in axes]
        height, width = (shape[0], shape[1]) if len(shape) == 2 else (1, shape[0] if shape else 1)
        cells = [[None] * width for _ in range(height)]
        ids = {}
        for v in products:
            if v.family != family.name:
                continue
            retained = aliases.get(v.id, v.id)
            if retained not in nets:
                continue
            positions = [family.grid[a].index(v.overrides[a]) for a in axes]
            r, c = (
                tuple(positions) if len(positions) == 2 else (0, positions[0] if positions else 0)
            )
            cells[r][c] = nets[retained]
            ids[r, c] = retained
        if len(axes) == 2:
            best = plateau_cell(cells)
            smooth = smooth_grid(cells)
        else:
            index = plateau_index(cells[0])
            best = (0, index) if index is not None else None
            smooth = [smooth_series(cells[0])]
        if best is not None:
            row.update(plateau_variant=ids[best], plateau_net_r=smooth[best[0]][best[1]])
        result.append(row)
    return result


def snapshot(trades):
    """JSON-safe summaries and minimal shock inputs, reusable without backtest replay."""
    return {
        "symbols": split(trades, by_symbol),
        "classes": split(trades, market_class),
        "years": by_period(trades),
        "shock_trades": [[t.symbol, t.exit_time.isoformat(), t.r_net] for t in trades],
    }


def write_csv(path, rows, columns=()):
    # Lazy import: grid_common's execution helpers import research.
    from backtester.tools.grid_common import write_csv as shared_write_csv

    if rows:
        shared_write_csv(path, rows)
    else:
        with path.open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerow(columns)


def write_diagnostics(folder, spec, variants, rows, info, results_dir, sources):
    """Refresh additive outputs from persisted snapshots, including historical retests."""
    grids = grid_rows(spec, variants, rows)
    write_csv(folder / "grid.csv", grids, GRID_COLUMNS)
    info["grid_robustness"] = grids
    info["duplicates"] = spec.duplicates
    chosen = info.get("chosen")
    records = []
    if chosen:
        records.append(("development", 0, chosen["id"], folder / "variants" / chosen["id"]))
    test_path = folder / "test.csv"
    if test_path.exists():
        with test_path.open(encoding="utf-8", newline="") as stream:
            records.extend(
                ("test", int(t["test_run"]), t["variant_id"], results_dir / t["run_folder"])
                for t in csv.DictReader(stream)
            )
    symbols, classes, years, shock_rows = [], [], [], []
    shocks = None
    last_period = "test" if any(period == "test" for period, *_ in records) else "development"
    for period, test_run, variant_id, run_folder in records:
        path = run_folder / "diagnostics.json"
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            # Older completed runs are upgraded from their stored trades, never rerun.
            from backtester.analytics.records import read_trades

            data = snapshot(read_trades(run_folder))
            path.write_text(json.dumps(data), encoding="utf-8")
        prefix = {"period": period, "test_run": test_run, "variant_id": variant_id}
        symbols.extend({**prefix, "symbol": k, **v} for k, v in data["symbols"].items())
        classes.extend({**prefix, "market_class": k, **v} for k, v in data["classes"].items())
        years.extend(
            {**prefix, "year": year, "symbol": symbol, **summary}
            for year, groups in data["years"].items()
            for symbol, summary in groups.items()
        )
        if spec.shocks:
            if shocks is None:
                shocks = load_shocks(
                    spec.symbols,
                    datetime.fromisoformat(info["periods"][last_period]["end"]).date(),
                    sources,
                )
            trades = [
                SimpleNamespace(symbol=s, exit_time=datetime.fromisoformat(t), r_net=r)
                for s, t, r in data["shock_trades"]
            ]
            shock_rows.append({**prefix, **shock_report(trades, shocks)})
    for name, output, key in (
        ("breakdown_symbols", symbols, "symbol"),
        ("breakdown_classes", classes, "market_class"),
        ("by_year", years, "year"),
    ):
        write_csv(folder / f"{name}.csv", output, ("period", "test_run", "variant_id", key))
    if spec.shocks:
        write_csv(folder / "shocks.csv", shock_rows, ("period", "test_run", "variant_id"))
    else:
        (folder / "shocks.csv").unlink(missing_ok=True)
    info["shocks"] = shock_rows if spec.shocks else None


def setting_cells(spec, overrides):
    """Union axis columns for combined grids, leaving single-grid exports unchanged."""
    axes = dict.fromkeys(a for f in families(spec) for a in f.grid)
    if spec.grids:
        from backtester.tools.research_grid import Variant

        values = resolved_values(spec, Variant("", "", overrides))
    else:
        values = overrides
    return {f"set.{name}": values[name] for name in axes}
