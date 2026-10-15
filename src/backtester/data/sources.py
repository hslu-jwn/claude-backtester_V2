"""Which cache each symbol is read from. Spec: ARCHITECTURE.md › Data sources.

Every source keeps its own cache folder (same layout and columns, `data/cache.py`), so
sources never mix. `SymbolSources` maps each symbol to one of these folders; the chart,
`tools.check` and `tools.show` all read through it, so every symbol can be shown in one app.

Default: every symbol from histdata.com (user, 2026-10-10; the Dukascopy downloader was
removed, ROADMAP C.1). To read a symbol from another folder, change `DEFAULT_SOURCES`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from types import MappingProxyType

from backtester.data.adapters.cache_adapter import CacheAdapter, cached_days
from backtester.data.binance import CACHE_DIR as BINANCE_CACHE_DIR
from backtester.data.cache import DEFAULT_CACHE_DIR, MT5_CACHE_DIR


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


# Decimals of the quoted price, per symbol the app knows (chart axis, reports). histdata
# writes the indices with 3 decimals; MT5 index CFDs quote 2. The symbols of ROADMAP 11.8 /
# 11.9 use FTMO's `digits` (MT5 symbol_info, 2026-10-15); histdata's are never higher.
PRICE_DIGITS = MappingProxyType(
    {
        "XAUUSD": 3, "GBPUSD": 5, "GBPJPY": 3, "NAS100": 2, "US500": 2,
        # histdata.com and FTMO
        "EURUSD": 5, "USDJPY": 3, "AUDUSD": 5, "USDCAD": 5, "USDCHF": 5, "NZDUSD": 5,
        "EURJPY": 3, "EURGBP": 5, "XAGUSD": 3, "GER40": 2, "UK100": 2, "JP225": 2, "EU50": 2,
        "USOIL": 3, "UKOIL": 3, "DXY": 3,
        # FTMO only (data/cache/mt5)
        "US30": 2, "US2000": 2, "NATGAS": 3, "BTCUSD": 2, "ETHUSD": 2,
        # Binance futures (data/cache/binance)
        "BTCUSDT": 2, "ETHUSDT": 2,
    }
)  # fmt: skip

# Symbols that have no histdata.com file: they are read from another cache (ROADMAP 11.8 / 11.9).
MT5_ONLY = ("US30", "US2000", "NATGAS", "BTCUSD", "ETHUSD")
BINANCE_SYMBOLS = ("BTCUSDT", "ETHUSDT")

DEFAULT_SOURCES = SymbolSources(
    {
        symbol: (
            MT5_CACHE_DIR
            if symbol in MT5_ONLY
            else BINANCE_CACHE_DIR
            if symbol in BINANCE_SYMBOLS
            else DEFAULT_CACHE_DIR
        )
        for symbol in PRICE_DIGITS
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
