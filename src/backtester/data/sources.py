"""Which cache each symbol is read from. Spec: ARCHITECTURE.md › Data sources.

Every source keeps its own cache folder (same layout and columns, `data/cache.py`), so
sources never mix. `SymbolSources` maps each symbol to one of these folders; the chart,
`tools.check` and `tools.show` all read through it, so every symbol can be shown in one app.

Default: histdata.com (user, 2026-10-10; the Dukascopy downloader was removed, ROADMAP C.1),
with MT5 preferred day by day (rule set by the user, 2026-10-19): "We always prefer MT5 if we
have it, but it doesn't go far enough into the past." A UTC day that exists in the MT5 cache is
read from MT5, a day only in the histdata cache from histdata, for backtests, tools and the
chart alike. MT5 index prices differ slightly from histdata's, so a small jump at the seam is
expected. Binance and MT5-only symbols have no preferred folder. To read a symbol from another
folder, change `DEFAULT_SOURCES`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from pathlib import Path
from types import MappingProxyType

from backtester.data.adapters.cache_adapter import (
    CacheAdapter,
    PreferredCacheAdapter,
    cached_days,
)
from backtester.data.binance import CACHE_DIR as BINANCE_CACHE_DIR
from backtester.data.cache import DEFAULT_CACHE_DIR, LIVE_CACHE_DIR, MT5_CACHE_DIR


class UnmappedSymbolError(KeyError):
    """A symbol has no data source in `SymbolSources`. A KeyError (older callers catch that),
    printed as a plain sentence, not as a quoted repr."""

    def __str__(self) -> str:
        return str(self.args[0]) if self.args else ""


@dataclass(frozen=True)
class SymbolSources:
    cache_dirs: Mapping[str, Path]  # symbol -> cache folder it is read from
    # symbol -> folder read first, day by day (MT5); days it lacks come from `cache_dirs`
    preferred_dirs: Mapping[str, Path] = field(default_factory=dict)
    # symbol -> folder read last, for days neither of the others has (the live bot's today,
    # `LIVE_CACHE_DIR`, ROADMAP 7.8). Its files change while the app runs: `fallback_stamp`.
    fallback_dirs: Mapping[str, Path] = field(default_factory=dict)

    def __post_init__(self) -> None:
        dirs = {symbol: Path(d) for symbol, d in self.cache_dirs.items()}
        object.__setattr__(self, "cache_dirs", MappingProxyType(dirs))
        pref = {symbol: Path(d) for symbol, d in self.preferred_dirs.items()}
        object.__setattr__(self, "preferred_dirs", MappingProxyType(pref))
        last = {symbol: Path(d) for symbol, d in self.fallback_dirs.items()}
        object.__setattr__(self, "fallback_dirs", MappingProxyType(last))

    def __hash__(self) -> int:  # the chart page caches loaded ranges per sources
        return hash(
            (
                tuple(sorted(self.cache_dirs.items())),
                tuple(sorted(self.preferred_dirs.items())),
                tuple(sorted(self.fallback_dirs.items())),
            )
        )

    @classmethod
    def single(cls, cache_dir: str | Path, symbols: Iterable[str]) -> SymbolSources:
        """All `symbols` from one folder (the `--cache-dir` override of the commands)."""
        return cls({symbol: Path(cache_dir) for symbol in symbols})

    @property
    def symbols(self) -> list[str]:
        return sorted(self.cache_dirs)

    def cache_dir(self, symbol: str) -> Path:
        if symbol not in self.cache_dirs:
            raise UnmappedSymbolError(
                f"no data source for {symbol}: add it to SymbolSources "
                f"(data/sources.py, mapped: {', '.join(self.symbols)})"
            )
        return self.cache_dirs[symbol]

    def adapter(self, symbol: str) -> CacheAdapter:
        main = self.cache_dir(symbol)
        preferred = self.preferred_dirs.get(symbol)
        preferred = None if preferred == main else preferred
        last = self.fallback_dirs.get(symbol)
        if preferred is None and last is None:
            return CacheAdapter(main)
        return PreferredCacheAdapter(main, preferred, last)

    def cached_days(self, symbol: str) -> list[date]:
        """Days in the main, the preferred or the fallback folder, sorted."""
        days = set(cached_days(symbol, self.cache_dir(symbol)))
        for folders in (self.preferred_dirs, self.fallback_dirs):
            if symbol in folders:
                days |= set(cached_days(symbol, folders[symbol]))
        return sorted(days)

    def fallback_stamp(self, symbol: str) -> tuple:
        """(name, modification time) of the fallback folder's day files: part of the chart's
        cache key, so a day the bot rewrites is read again. () without a fallback folder."""
        folder = self.fallback_dirs.get(symbol)
        if folder is None:
            return ()
        stamp = []
        for year in sorted((Path(folder) / symbol).glob("[0-9]*")):
            stamp += [(f.name, f.stat().st_mtime_ns) for f in sorted(year.glob("*.parquet"))]
        return tuple(stamp)

    def feed_switch(self, symbol: str) -> date | None:
        """First day of the preferred feed (MT5) after the symbol's last main-feed-only day,
        or None when there is no such seam (the chart marks it)."""
        preferred = self.preferred_dirs.get(symbol)
        if preferred is None or preferred == self.cache_dir(symbol):
            return None
        pref = set(cached_days(symbol, preferred))
        only_main = [d for d in cached_days(symbol, self.cache_dir(symbol)) if d not in pref]
        if not only_main:
            return None
        return min((d for d in pref if d > only_main[-1]), default=None)

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
    },
    preferred_dirs={
        symbol: MT5_CACHE_DIR
        for symbol in PRICE_DIGITS
        if symbol not in MT5_ONLY and symbol not in BINANCE_SYMBOLS
    },
)

# The chart only (spec live-trading.md › Bot data and chart): today's live bars of the bot's symbols
# for days the other caches lack. Backtests and tools keep DEFAULT_SOURCES (no partial live day).
CHART_SOURCES = replace(
    DEFAULT_SOURCES,
    fallback_dirs={
        symbol: LIVE_CACHE_DIR for symbol in PRICE_DIGITS if symbol not in BINANCE_SYMBOLS
    },
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
