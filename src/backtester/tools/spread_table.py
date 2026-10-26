"""Spread by year and hour of day from FTMO's M1 history. Research / setup tool, it changes no
setting: it only writes the table a `CostConfig(spread_table=...)` can use (ROADMAP 6.7).

    python -m backtester.tools.spread_table
    python -m backtester.tools.spread_table --symbols XAUUSD US500 --min-bars 200

Reads the M1 bars of the terminal that is running and logged in (no login is read or
printed; the terminal's "Max bars in chart" must be Unlimited), takes MT5's per-bar spread
in price units, drops the bars without a spread (0 = not recorded) and writes, per symbol,
New York year and New York hour of day, the median and the 90th percentile:

- `data/spreads/ftmo_spread_median.json`: the typical spread (what a fill usually pays);
- `data/spreads/ftmo_spread_p90.json`: a stress level;
- `data/spreads/coverage.csv`: bars and share of unrecorded spreads per symbol and year.

Server time to UTC uses `America/New_York + 7 h` (measured on 2020-2026 H1 bars against the
histdata cache: 920 of 948 weeks; the misses are weeks of 2020-03..2021-03, when the server
followed Europe's summer time, so a few weeks of those years are an hour off).
Our symbol NAS100 is `US100.cash` on FTMO.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.core.models import Timeframe
from backtester.data.adapters.mt5_adapter import Mt5Adapter
from backtester.data.mt5_download import DEFAULT_CLOCK, DEFAULT_NAMES, DEFAULT_SYMBOLS
from backtester.engine.costs import DEFAULT_SYMBOL_COSTS
from backtester.engine.spread_table import STATS, SpreadTable
from backtester.paths import DATA_DIR

DEFAULT_OUT = DATA_DIR / "spreads"
FIRST_YEAR = 2015
MIN_BARS = 100  # valid bars a (symbol, year, hour) cell needs


class SpreadCollector:
    """Collects bar spreads by (symbol, New York year, New York hour) in chunks."""

    def __init__(self, min_bars: int = MIN_BARS, zone: str = "America/New_York"):
        self.min_bars = min_bars
        self.zone = zone
        self._cells: dict[tuple[str, int, int], list[np.ndarray]] = defaultdict(list)
        self._bars: dict[tuple[str, int], list[int]] = defaultdict(lambda: [0, 0])

    def add(self, symbol: str, frame: pd.DataFrame) -> None:
        """`frame`: column `ts` (UTC) and `spread` (price units; 0 = not recorded)."""
        if frame.empty:
            return
        local = pd.DatetimeIndex(frame["ts"]).tz_convert(self.zone)
        spread = frame["spread"].to_numpy(dtype=float)
        years, hours = local.year.to_numpy(), local.hour.to_numpy()
        for year in np.unique(years):
            in_year = years == year
            counts = self._bars[symbol, int(year)]
            counts[0] += int(in_year.sum())
            counts[1] += int((spread[in_year] <= 0).sum())
            for hour in np.unique(hours[in_year]):
                values = spread[in_year & (hours == hour)]
                values = values[values > 0]
                if len(values):
                    self._cells[symbol, int(year), int(hour)].append(values)

    def build(self, stat: str, note: str = "") -> tuple[SpreadTable, list[dict]]:
        if stat not in STATS:
            raise ValueError(f"stat must be one of {STATS}")
        values: dict[str, dict[int, dict[int, float]]] = {}
        for (symbol, year, hour), chunks in sorted(self._cells.items()):
            data = np.concatenate(chunks)
            if len(data) < self.min_bars:
                continue
            value = float(np.median(data) if stat == "median" else np.percentile(data, 90))
            values.setdefault(symbol, {}).setdefault(year, {})[hour] = value
        coverage = [
            {"symbol": s, "year": y, "bars": n, "zero_share": z / n}
            for (s, y), (n, z) in sorted(self._bars.items())
        ]
        return SpreadTable(values=values, zone=self.zone, stat=stat, note=note), coverage


def _fixed(symbol: str) -> float | None:
    costs = DEFAULT_SYMBOL_COSTS.get(symbol)
    return costs.spread if costs else None


def _print_symbol(symbol: str, table: SpreadTable, coverage: list[dict]) -> None:
    fixed = _fixed(symbol)
    print(f"\n{symbol}: median spread by year, price units (fixed model {fixed})")
    print(f"{'year':6}{'bars':>10}{'unrecorded':>12}{'all hours':>11}{'NY 9-15':>10}{'NY 17':>9}")
    for row in (r for r in coverage if r["symbol"] == symbol):
        hours = table.values.get(symbol, {}).get(row["year"], {})
        day = [v for h, v in hours.items() if 9 <= h <= 15]
        allv = list(hours.values())
        med = lambda xs: f"{float(np.median(xs)):.5g}" if xs else "-"
        print(
            f"{row['year']:<6}{row['bars']:>10}{row['zero_share']:>12.0%}{med(allv):>11}"
            f"{med(day):>10}{(f'{hours[17]:.5g}' if 17 in hours else '-'):>9}"
        )


def run(
    symbols: Sequence[str],
    names: Mapping[str, str],
    frames_for: Callable[[str, str], Iterable[pd.DataFrame]],
    out: Path,
    min_bars: int = MIN_BARS,
) -> int:
    """Collect every symbol's frames, write both tables and the coverage file."""
    collector = SpreadCollector(min_bars)
    used: list[str] = []
    for symbol in symbols:
        name = names.get(symbol, symbol)
        try:
            n = 0
            for frame in frames_for(symbol, name):
                collector.add(symbol, frame)
                n += len(frame)
        except Exception as e:  # noqa: BLE001 - research tool: say what is missing, go on
            print(f"{symbol} ({name}): skipped ({type(e).__name__}: {e})", flush=True)
            continue
        print(f"{symbol} ({name}): {n:,} bars", flush=True)
        used.append(f"{symbol}={name}")
    note = f"FTMO demo MT5 M1 bars, NY hour; {', '.join(used)}"
    out.mkdir(parents=True, exist_ok=True)
    coverage: list[dict] = []
    for stat in STATS:
        table, coverage = collector.build(stat, note)
        (out / f"ftmo_spread_{stat}.json").write_text(
            json.dumps(table.to_dict(), indent=1), encoding="utf-8"
        )
        if stat == "median":
            for symbol in symbols:
                if any(r["symbol"] == symbol for r in coverage):
                    _print_symbol(symbol, table, coverage)
    with (out / "coverage.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["symbol", "year", "bars", "zero_share"])
        w.writeheader()
        w.writerows(coverage)
    print(f"\nwritten to {out}")
    return 0


def mt5_frames(
    mt5, adapter: Mt5Adapter, first_year: int, last_year: int
) -> Callable[[str, str], Iterator[pd.DataFrame]]:
    """Per symbol, one frame (`ts` UTC, `spread` price units) per server year of M1 bars."""

    def frames(symbol: str, name: str) -> Iterator[pd.DataFrame]:
        for year in range(first_year, last_year + 1):
            start = datetime(year, 1, 1, tzinfo=UTC)
            raw = adapter.raw_frame(symbol, Timeframe.M1, start, start.replace(year=year + 1))
            if raw.empty:
                continue
            ts = adapter.clock.to_utc(raw["time"].to_numpy())
            yield pd.DataFrame({"ts": ts, "spread": raw["spread"].to_numpy()})

    return frames


def main(argv: Sequence[str] | None = None) -> int:
    from backtester.live.connection import session
    from backtester.live.trading_settings import load_trading_settings

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--symbols", nargs="+", default=list(DEFAULT_SYMBOLS))
    p.add_argument("--first-year", type=int, default=FIRST_YEAR)
    p.add_argument("--last-year", type=int, default=datetime.now(UTC).year)
    p.add_argument("--min-bars", type=int, default=MIN_BARS)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = p.parse_args(argv)
    settings = load_trading_settings()
    names = {**DEFAULT_NAMES, **{s: n for s, n in settings.symbols.items() if n != s}}
    clock = settings.server_clock or DEFAULT_CLOCK
    symbols = [s.upper() for s in args.symbols]
    with session(settings, None) as mt5:
        adapter = Mt5Adapter(mt5, clock, names)
        frames = mt5_frames(mt5, adapter, args.first_year, args.last_year)
        return run(symbols, names, frames, args.out, args.min_bars)


if __name__ == "__main__":
    raise SystemExit(main())
