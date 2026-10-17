"""What the "Update data" job has to fetch: pure planning, no terminal, no network.
Spec: ROADMAP.md > 7.5, ARCHITECTURE.md > Data sources > Updating the caches.

Per cache and symbol: the last cached UTC day `L`, the missing range `L+1 .. yesterday`
(UTC; today's candles are still forming, so they are never stored). Execution is in
`tools/update_data.py`.

- MT5 cache (`data/cache/mt5`): every symbol that has a folder, also those whose chart and
  backtest feed is histdata. `data/mt5_download.py` caches weekend days as empty files, so a
  Monday after a fully cached Sunday has nothing to do.
- Binance cache: `BINANCE_SYMBOLS`.
- histdata cache: whole months after the month of `L`, only months that are over (their last
  day is before today), since histdata publishes finished months only. Symbols whose histdata
  cache is more than `UpdateConfig.histdata_max_stale_days` behind (a closed archive such as
  EURUSD to 2021-12) are skipped: their later history comes from the MT5 cache.
- A symbol without any cached day is skipped and reported ("use the full download tool"); an
  update never downloads a whole history from scratch.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from backtester.data.binance import CACHE_DIR as BINANCE_CACHE_DIR
from backtester.data.cache import DEFAULT_CACHE_DIR, MT5_CACHE_DIR
from backtester.data.histdata import SYMBOL_NAMES, MonthFile
from backtester.data.sources import BINANCE_SYMBOLS, MT5_ONLY

MT5 = "mt5"
BINANCE = "binance"
HISTDATA = "histdata"
FULL_DOWNLOAD_TOOL = {
    MT5: "python -m backtester.tools.mt5_download",
    BINANCE: "python -m backtester.tools.binance_download",
    HISTDATA: "python -m backtester.tools.histdata_download",
}


@dataclass(frozen=True)
class UpdateConfig:
    # MT5: the download starts this many days before the first missing day, because
    # `download_symbol` treats the first day with real bars of its range as partial and skips it;
    # a weekend or holiday at the cache edge would otherwise swallow the days after it.
    mt5_overlap_days: int = 7
    # histdata: a cache whose last day is further behind than this is not kept current.
    histdata_max_stale_days: int = 93


DEFAULT_CONFIG = UpdateConfig()


@dataclass(frozen=True)
class Task:
    source: str  # MT5 / BINANCE / HISTDATA
    symbol: str  # our name
    first: date  # missing range, inclusive
    last: date
    months: tuple[date, ...] = ()  # histdata: first day of each month to fetch


@dataclass(frozen=True)
class Skip:
    source: str
    symbol: str
    reason: str


@dataclass(frozen=True)
class Plan:
    today: date  # UTC date the plan was made for
    tasks: tuple[Task, ...] = ()
    skipped: tuple[Skip, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not self.tasks


def histdata_pair(symbol: str) -> str:
    """histdata.com's name of our symbol (NAS100 -> NSXUSD)."""
    return next((pair for pair, ours in SYMBOL_NAMES.items() if ours == symbol), symbol)


def last_cached_day(cache_dir: Path, symbol: str) -> date | None:
    """Newest day file of `symbol` (days cached as empty count), or None."""
    root = Path(cache_dir) / symbol
    if not root.is_dir():
        return None
    years = sorted((p for p in root.iterdir() if p.is_dir() and p.name.isdigit()), reverse=True)
    for year in years:
        days = [p.stem for p in year.glob("*.parquet")]
        if days:
            return date.fromisoformat(max(days))
    return None


def missing_range(last: date, yesterday: date) -> tuple[date, date] | None:
    """(last + 1, yesterday), or None when the cache is already up to yesterday."""
    first = last + timedelta(days=1)
    return (first, yesterday) if first <= yesterday else None


def _symbol_folders(cache_dir: Path) -> list[str]:
    root = Path(cache_dir)
    return sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


def _month_start(day: date) -> date:
    return day.replace(day=1)


def _next_month(month: date) -> date:
    return (month + timedelta(days=32)).replace(day=1)


def _month_last_day(month: date) -> date:
    return _next_month(month) - timedelta(days=1)


def histdata_months(last: date, today: date) -> tuple[date, ...]:
    """Months to fetch after the cached day `last`: the month of `last` itself when `last` is
    not its final day, then every following month that is over before `today`."""
    month = _month_start(last)
    if last == _month_last_day(month):
        month = _next_month(month)
    out = []
    while _month_last_day(month) < today:
        out.append(month)
        month = _next_month(month)
    return tuple(out)


def select_import_files(files: list[MonthFile], last: date) -> list[MonthFile]:
    """The histdata files to import after a download: the period holding the last cached day
    (so the first new day is complete, `data/histdata.py`) and every later one."""
    start = _month_start(last)
    return [f for f in sorted(files, key=lambda f: f.month) if f.end > start]


def plan_update(
    today: date,
    *,
    mt5_dir: Path = MT5_CACHE_DIR,
    binance_dir: Path = BINANCE_CACHE_DIR,
    histdata_dir: Path = DEFAULT_CACHE_DIR,
    config: UpdateConfig = DEFAULT_CONFIG,
) -> Plan:
    """The tasks that bring every cache up to yesterday (`today` = UTC date)."""
    yesterday = today - timedelta(days=1)
    tasks: list[Task] = []
    skipped: list[Skip] = []

    def day_task(source: str, cache_dir: Path, symbol: str) -> None:
        last = last_cached_day(cache_dir, symbol)
        if last is None:
            skipped.append(
                Skip(
                    source,
                    symbol,
                    f"no cache, use the full download tool: {FULL_DOWNLOAD_TOOL[source]}",
                )
            )
            return
        span = missing_range(last, yesterday)
        if span is not None:
            tasks.append(Task(source, symbol, *span))

    for symbol in _symbol_folders(mt5_dir):
        day_task(MT5, mt5_dir, symbol)
    for symbol in BINANCE_SYMBOLS:
        day_task(BINANCE, binance_dir, symbol)
    for symbol in _symbol_folders(histdata_dir):
        if symbol in MT5_ONLY or symbol in BINANCE_SYMBOLS:
            continue
        last = last_cached_day(histdata_dir, symbol)
        if last is None:
            skipped.append(
                Skip(
                    HISTDATA,
                    symbol,
                    f"no cache, use the full download tool: {FULL_DOWNLOAD_TOOL[HISTDATA]}",
                )
            )
        elif (yesterday - last).days > config.histdata_max_stale_days:
            skipped.append(
                Skip(HISTDATA, symbol, f"cache ends {last}, not kept current (MT5 feed after it)")
            )
        elif months := histdata_months(last, today):
            tasks.append(Task(HISTDATA, symbol, months[0], _month_last_day(months[-1]), months))
    return Plan(today, tuple(tasks), tuple(skipped))
