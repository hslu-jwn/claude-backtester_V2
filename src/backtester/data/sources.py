"""Which cache each symbol is read from. Spec: ARCHITECTURE.md › Data sources.

Every source keeps its own cache folder (same layout and columns, `data/dukascopy.py`), so
sources never mix. `SymbolSources` maps each symbol to one of these folders; the chart,
`data.check` and `data.show` all read through it, so every symbol can be shown in one app.

Default: all three symbols from histdata.com while Dukascopy downloads are paused
(ROADMAP.md › 0.3). The XAUUSD days already in the Dukascopy cache stay there, unused;
histdata matched them exactly (2026-09-02..07, every M1 candle). To switch a symbol back,
change `DEFAULT_SOURCES`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from types import MappingProxyType

from backtester.data.adapters.cache_adapter import CacheAdapter, cached_days
from backtester.data.histdata import DEFAULT_HISTDATA_CACHE_DIR


@dataclass(frozen=True)
class SymbolSources:
    cache_dirs: Mapping[str, Path]  # symbol -> cache folder it is read from

    def __post_init__(self) -> None:
        dirs = {symbol: Path(d) for symbol, d in self.cache_dirs.items()}
        object.__setattr__(self, "cache_dirs", MappingProxyType(dirs))

    def __hash__(self) -> int:  # the chart page caches loaded ranges per sources
        return hash(tuple(sorted(self.cache_dirs.items())))

    @classmethod
    def single(cls, cache_dir: str | Path, symbols: Iterable[str]) -> SymbolSources:
        """All `symbols` from one folder (the `--cache-dir` override of the commands)."""
        return cls({symbol: Path(cache_dir) for symbol in symbols})

    @property
    def symbols(self) -> list[str]:
        return sorted(self.cache_dirs)

    def cache_dir(self, symbol: str) -> Path:
        if symbol not in self.cache_dirs:
            raise KeyError(
                f"no data source for {symbol}: add it to SymbolSources "
                f"(data/sources.py, mapped: {', '.join(self.symbols)})"
            )
        return self.cache_dirs[symbol]

    def adapter(self, symbol: str) -> CacheAdapter:
        return CacheAdapter(self.cache_dir(symbol))

    def cached_days(self, symbol: str) -> list[date]:
        return cached_days(symbol, self.cache_dir(symbol))

    def available_symbols(self) -> list[str]:
        """Mapped symbols with at least one cached day in their own folder, sorted."""
        return [s for s in self.symbols if self.cached_days(s)]


DEFAULT_SOURCES = SymbolSources(
    {
        "XAUUSD": DEFAULT_HISTDATA_CACHE_DIR,
        "GBPUSD": DEFAULT_HISTDATA_CACHE_DIR,
        "GBPJPY": DEFAULT_HISTDATA_CACHE_DIR,
    }
)


def warmup_start(cached: set[date], start: date, max_days: int) -> date:
    """Earliest day, at most `max_days` before `start`, with every day from it up to
    `start` in the cache (warm-up history for trends, zones, backtests on a chart range)."""
    first = start
    while (start - first).days < max_days and first - timedelta(days=1) in cached:
        first -= timedelta(days=1)
    return first


def cached_block(cached: set[date], day: date) -> tuple[date, date]:
    """(first, last) day of the run of consecutive cached days that contains `day`."""
    if day not in cached:
        raise KeyError(f"{day} is not cached")
    first, last = day, day
    while first - timedelta(days=1) in cached:
        first -= timedelta(days=1)
    while last + timedelta(days=1) in cached:
        last += timedelta(days=1)
    return first, last
