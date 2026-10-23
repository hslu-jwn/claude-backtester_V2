"""Backtest runs: strategy 1 + engine over one or several symbols, results to a folder.

Spec: ROADMAP.md › 3.4. Per symbol:
1. Days: the requested UTC days [start, end]. Uncached days at the start or the end of the
   range are left out (noted in the summary); a missing day in between is an error
   (`MissingCacheError`, with the import command).
2. Warm-up: up to `RunSettings.warmup_days` cached days right before the first day are
   loaded too (fewer if the cache has a gap), so detectors, zones, ATR and the 1h / 4H
   levels have history. Trades entered in the warm-up are dropped, as are sessions that
   end before the range starts.
3. Every timeframe strategy 1 declares is loaded from the cache (`SymbolSources`) and run
   through `engine/backtest.py`. Trades still open at the end of the range close at the
   last close (`END_OF_DATA`, engine rule).
Symbols run in parallel processes (one per symbol, up to `workers`); one symbol or
`workers=1` runs in this process. The trades of all symbols are merged in entry time
order. Progress: `progress(done, total)` in base candles (5m for strategy 1, 1m for strategy 2) over all symbols;
before it `load_progress(done, total)` reports the loading phase (every symbol an equal share, in it every
timeframe an equal share: the day files read, then the candles built) and can be cancelled like the run.

`write_results` writes `results/<run-id>/` (git-ignored):
- `trades.csv`  one row per trade, all symbols, entry time order (`id` links sessions.json)
- `settings.json` the exact settings: run (symbols, range, warm-up, cache folders),
  strategy and engine (incl. costs) config dataclasses, and the settings preset's name
  (`preset`, ROADMAP 4.2; "<name> (modified)" when the run's settings differ from it)
- `summary.json` per symbol and combined (analytics/metrics.py `summarize`), the days
  used per symbol, notes and when the run was made (`created`, UTC)
- `sessions.json` per symbol and session: the session zones, the setup confluences
  (strategy/session_zone_sweep/journal.py) and the ids of the trades entered in it

`start_run` does the same in a background thread for the app (progress bar, ROADMAP 4.0).
"""

from __future__ import annotations

import copyreg
import csv
import json
import multiprocessing
import os
import shutil
import threading
import time as clock_time
from collections.abc import Callable, Iterator, Mapping, Sequence
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, as_completed, wait
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import Enum
from itertools import pairwise
from pathlib import Path
from types import MappingProxyType

from backtester.analytics.metrics import summarize
from backtester.core.models import Direction
from backtester.core.series import CandleSeries
from backtester.data.adapters.cache_adapter import candles_from_frame
from backtester.data.sources import (
    DEFAULT_SOURCES,
    SymbolSources,
    UnmappedSymbolError,
    cached_block,
    warmup_start,
)
from backtester.detectors.settings import DetectorSettings
from backtester.engine.backtest import DEFAULT_ENGINE, EngineConfig, Progress, run_backtest
from backtester.engine.spread_table import SpreadTable
from backtester.engine.trade import TradeResult
from backtester.paths import RESULTS_DIR
from backtester.strategy.base import UnsupportedSymbolError
from backtester.strategy.gap_fade.config import GapFadeConfig
from backtester.strategy.gap_momentum.config import GapMomentumConfig
from backtester.strategy.no_wick.config import NoWickConfig
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
from backtester.strategy.opening_range.config import OpeningRangeConfig
from backtester.strategy.registry import make_strategy, strategy_name
from backtester.strategy.session_zone_sweep.config import SessionZoneSweepConfig
from backtester.strategy.trend_following.config import TrendFollowingConfig


class RunCancelled(Exception):
    """The run was cancelled (`cancel` event of `run_backtests` / `BackgroundRun.cancel`).
    Nothing is written for a cancelled run."""


def _read_only(mapping: dict) -> MappingProxyType:
    return MappingProxyType(mapping)


# config dataclasses keep their mappings read-only; worker processes need them pickled
copyreg.pickle(MappingProxyType, lambda m: (_read_only, (dict(m),)))


# every registered strategy's config (tests/strategy/test_registry.py keeps this in step)
StrategyConfig = (
    SessionZoneSweepConfig
    | NyIndexSweepConfig
    | NoWickConfig
    | TrendFollowingConfig
    | GapFadeConfig
    | OpeningRangeConfig
    | GapMomentumConfig
)


@dataclass(frozen=True, slots=True)
class RunSettings:
    # the config of the strategy to run (`strategy/registry.py` maps it to the strategy);
    # the settings panel is built from it. Default: strategy 1
    strategy: StrategyConfig = field(default_factory=SessionZoneSweepConfig)
    # swings, FVG, order block, equilibrium: one group for every strategy
    detectors: DetectorSettings = field(default_factory=DetectorSettings)
    engine: EngineConfig = DEFAULT_ENGINE
    warmup_days: int = 14  # cached days loaded before the range (1h / 4H levels, ATR)

    def __post_init__(self) -> None:
        if self.warmup_days < 0:
            raise ValueError("warmup_days must be >= 0")


@dataclass(frozen=True)
class SymbolRun:
    symbol: str
    first_day: date  # first and last day of the range actually run
    last_day: date
    warmup_from: date  # first day loaded
    trades: tuple[TradeResult, ...]  # entered in the range, entry order
    sessions: tuple[dict, ...]  # strategy.session_records(), sessions overlapping the range
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class RunResult:
    symbols: tuple[str, ...]
    start: date
    end: date
    settings: RunSettings
    sources: SymbolSources
    runs: Mapping[str, SymbolRun]
    trades: tuple[TradeResult, ...]  # all symbols merged, entry time order
    # symbols asked for but left out (no rules for them in the strategy, no data in the range),
    # one line each; `symbols` holds only the ones that ran
    notes: tuple[str, ...] = ()

    def summary(self) -> dict:
        return {
            "per_symbol": {s: summarize(r.trades) for s, r in self.runs.items()},
            "combined": summarize(self.trades),
        }


def merge_trades(runs: Sequence[SymbolRun]) -> tuple[TradeResult, ...]:
    """All symbols' trades in entry time order (same time: by symbol)."""
    trades = [t for r in runs for t in r.trades]
    return tuple(sorted(trades, key=lambda t: (t.entry_time, t.symbol)))


# --- loading ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Job:
    symbol: str
    first_day: date
    last_day: date
    warmup_from: date
    series: tuple[CandleSeries, ...]
    settings: RunSettings
    notes: tuple[str, ...]

    @property
    def base_candles(self) -> int:
        base = make_strategy(
            self.symbol, self.settings.strategy, self.settings.detectors
        ).base_timeframe
        return len(next(s for s in self.series if s.timeframe is base))


@dataclass(frozen=True)
class LoadConfig:
    read_share: float = 0.2  # share of a timeframe's loading taken by reading the day files
    chunk_rows: int = 50_000  # candles built per step (progress and cancel in between)


LOAD = LoadConfig()
LOAD_UNITS = 10_000  # loading progress is reported in these units per symbol

StepProgress = Callable[[float], None]  # share (0-1) of one symbol's loading done


class NoDataError(ValueError):
    """A symbol has no cached day in the requested range."""


def _midnight(d: date) -> datetime:
    return datetime.combine(d, time(), UTC)


def _load(
    sources: SymbolSources,
    symbol: str,
    start: date,
    end: date,
    settings: RunSettings,
    step: StepProgress | None = None,
    cache: SeriesCache | None = None,
) -> _Job:
    cached = set(sources.cached_days(symbol))
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    in_range = [d for d in days if d in cached]
    if not in_range:
        raise NoDataError(f"{symbol}: no cached day between {start} and {end}")
    first, last = in_range[0], in_range[-1]
    notes = []
    if first > start:
        notes.append(f"{symbol}: {start}..{first - timedelta(days=1)} not cached, left out")
    if last < end:
        notes.append(f"{symbol}: {last + timedelta(days=1)}..{end} not cached, left out")
    adapter = sources.adapter(symbol)
    strategy = make_strategy(symbol, settings.strategy, settings.detectors)
    # the strategy's indicators may need more history than the setting (strategy 4)
    warm = warmup_start(cached, first, max(settings.warmup_days, strategy.min_warmup_days))
    h4 = strategy.h4_alignment
    history = cached_block(cached, first)[0]  # first day of the cached run around `first`
    full = strategy.full_history
    end = _midnight(last + timedelta(1))
    timeframes = tuple(dict.fromkeys(strategy.timeframes))
    series = tuple(
        _timeframe_series(
            cache, sources, adapter, symbol, tf, _midnight(history if tf in full else warm), end,
            h4, lambda share, k=k: step((k + share) / len(timeframes)) if step else None,
        )
        for k, tf in enumerate(timeframes)
    )  # fmt: skip
    return _Job(symbol, first, last, warm, series, settings, tuple(notes))


class SeriesCache:
    """Loaded candle series of ONE symbol and range, shared by the variants run on it.
    Series are immutable (`CandleSeries` holds a tuple, views only read), so every variant
    gets a new strategy and engine on the same series. Holds the last scope only (memory):
    a request for another (symbol, range end) drops the old series."""

    def __init__(self) -> None:
        self._scope: tuple | None = None
        self._items: dict[tuple, CandleSeries] = {}

    def get(self, scope: tuple, key: tuple, load: Callable[[], CandleSeries]) -> CandleSeries:
        if scope != self._scope:
            self._items.clear()
            self._scope = scope
        if key not in self._items:
            self._items[key] = load()
        return self._items[key]

    def clear(self) -> None:
        self._items.clear()
        self._scope = None


def _timeframe_series(
    cache, sources, adapter, symbol, tf, start, end, h4, step: StepProgress
) -> CandleSeries:
    if cache is None:
        return _load_timeframe(adapter, symbol, tf, start, end, h4, step)
    return cache.get(
        (symbol, end, sources),
        (tf, start, h4),
        lambda: _load_timeframe(adapter, symbol, tf, start, end, h4, step),
    )


def _load_timeframe(adapter, symbol, tf, start, end, h4, step: StepProgress) -> CandleSeries:
    """One timeframe's candles; `step(share)` after every chunk of day files and of candles."""
    share = LOAD.read_share
    frame = adapter.fetch_frame(
        symbol, tf, start, end, h4=h4, on_read=lambda done, total: step(share * done / total)
    )
    candles = []
    for i in range(0, len(frame), LOAD.chunk_rows):
        candles += candles_from_frame(frame.iloc[i : i + LOAD.chunk_rows])
        step(share + (1 - share) * min(i + LOAD.chunk_rows, len(frame)) / len(frame))
    step(1.0)
    return CandleSeries(symbol, tf, candles)


# --- running ---------------------------------------------------------------------------


def _run_job(job: _Job, progress: Progress | None = None) -> SymbolRun:
    strategy = make_strategy(job.symbol, job.settings.strategy, job.settings.detectors)
    trades = run_backtest(strategy, job.series, job.settings.engine, progress)
    start, end = _midnight(job.first_day), _midnight(job.last_day + timedelta(days=1))
    sessions = [
        s
        for s in strategy.session_records(run_end=end)
        if datetime.fromisoformat(s["end"]) > start and datetime.fromisoformat(s["start"]) < end
    ]
    return SymbolRun(
        job.symbol,
        job.first_day,
        job.last_day,
        job.warmup_from,
        tuple(t for t in trades if t.entry_candle >= start),
        tuple(sessions),
        job.notes,
    )


_worker_queue = None  # set in each worker process


def _init_worker(queue) -> None:
    global _worker_queue
    _worker_queue = queue
    # Progress items are informational: never wait at exit until they are read, or a finished
    # worker and the exiting main process wait for each other (hang found 2026-10-23).
    queue.cancel_join_thread()


def _run_in_worker(job: _Job) -> SymbolRun:
    return _run_job(job, lambda done, _total: _worker_queue.put((job.symbol, done)))


def run_backtests(
    symbols: Sequence[str],
    start: date,
    end: date,
    settings: RunSettings | None = None,
    sources: SymbolSources = DEFAULT_SOURCES,
    progress: Progress | None = None,
    workers: int | None = None,
    cancel: threading.Event | None = None,
    load_progress: Progress | None = None,
) -> RunResult:
    """The settings' strategy over `symbols` and the UTC days [start, end].

    A symbol the strategy has no rules for (`UnsupportedSymbolError`) or without a cached day
    in the range is left out with a note while others can run; when none can, the error is
    raised (the symbol's own error for a single symbol). Setting `cancel` stops the run at the
    next progress step, loading chunk (about a second at most) or symbol: `RunCancelled`.
    `load_progress(done, total)` reports the loading phase before the run's `progress`."""
    settings = settings or RunSettings()
    requested = tuple(dict.fromkeys(symbols))
    if not requested:
        raise ValueError("no symbols")
    if end < start:
        raise ValueError(f"end {end} is before start {start}")
    jobs: list[_Job] = []
    skipped: list[tuple[str, Exception]] = []
    load_total = LOAD_UNITS * len(requested)

    def loaded(index: int, share: float) -> None:
        _check_cancel(cancel)
        if load_progress is not None:
            load_progress(round((index + share) * LOAD_UNITS), load_total)

    for i, s in enumerate(requested):
        loaded(i, 0.0)
        try:
            jobs.append(
                _load(sources, s, start, end, settings, lambda share, i=i: loaded(i, share))
            )
        except (UnsupportedSymbolError, NoDataError, UnmappedSymbolError) as e:
            skipped.append((s, e))
        loaded(i, 1.0)
    if not jobs:
        raise _nothing_to_run(skipped)
    symbols = tuple(j.symbol for j in jobs)
    total = sum(j.base_candles for j in jobs)
    done = dict.fromkeys(symbols, 0)

    def report(symbol: str, n: int) -> None:
        _check_cancel(cancel)
        done[symbol] = max(done[symbol], n)
        if progress is not None:
            progress(sum(done.values()), total)

    workers = min(len(jobs), workers or os.cpu_count() or 1)
    if workers <= 1:
        runs = [_run_job(j, lambda n, _t, s=j.symbol: report(s, n)) for j in jobs]
    else:
        runs = _run_parallel(jobs, workers, report, cancel)
    outcomes = {**dict(skipped), **{r.symbol: r for r in runs}}
    return combine_runs(requested, start, end, settings, sources, outcomes)


def _nothing_to_run(skipped: Sequence[tuple[str, Exception]]) -> Exception:
    """The error of a run where no symbol could run: the symbol's own for a single one."""
    if len(skipped) == 1:
        return skipped[0][1]
    text = "; ".join(str(e) for _, e in skipped)
    if all(isinstance(e, UnsupportedSymbolError) for _, e in skipped):
        return UnsupportedSymbolError(text)
    return ValueError(text)


def combine_runs(
    requested: Sequence[str],
    start: date,
    end: date,
    settings: RunSettings,
    sources: SymbolSources,
    outcomes: Mapping[str, SymbolRun | Exception],
) -> RunResult:
    """The `RunResult` of `requested` symbols from their outcomes: a `SymbolRun`, or the
    error that left the symbol out (a note; raised when no symbol could run)."""
    runs = {s: o for s in requested if isinstance(o := outcomes[s], SymbolRun)}
    skipped = [(s, o) for s in requested if isinstance(o := outcomes[s], Exception)]
    if not runs:
        raise _nothing_to_run(skipped)
    left_out = tuple(f"{s} left out: {e}" for s, e in skipped)
    return RunResult(
        tuple(runs), start, end, settings, sources, runs, merge_trades(list(runs.values())),
        left_out,
    )  # fmt: skip


def _check_cancel(cancel: threading.Event | None) -> None:
    if cancel is not None and cancel.is_set():
        raise RunCancelled


def _run_parallel(
    jobs: list[_Job],
    workers: int,
    report: Callable[[str, int], None],
    cancel: threading.Event | None = None,
) -> list[SymbolRun]:
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()

    def drain() -> None:
        while not queue.empty():
            report(*queue.get())

    pool = ProcessPoolExecutor(workers, ctx, _init_worker, (queue,))
    try:
        futures = {pool.submit(_run_in_worker, j): j for j in jobs}
        pending = set(futures)
        while pending:
            _check_cancel(cancel)
            finished, pending = wait(pending, timeout=0.2, return_when=FIRST_COMPLETED)
            drain()
            for f in finished:
                f.result()  # raise a worker's error here
                report(futures[f].symbol, futures[f].base_candles)
        return [f.result() for f in futures]
    except BaseException:  # cancelled or failed: stop the workers, don't wait for them
        _kill_workers(pool)
        raise
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def _kill_workers(pool: ProcessPoolExecutor) -> None:
    for process in list(getattr(pool, "_processes", {}).values()):
        process.terminate()


# --- many variants on one loaded series (research runner) ------------------------------


@dataclass(frozen=True)
class ManyConfig:
    # most variants one worker task runs on a series it loaded once: a finished task is a
    # resumable unit for the research runner, so a long grid is cut into tasks of this size
    max_chunk: int = 8


MANY = ManyConfig()

Task = tuple[str, date, date]  # symbol and its range of consecutive cached days
Outcome = SymbolRun | Exception  # the run, or why the symbol is left out of it
_SERIES = SeriesCache()  # this process' loaded series (worker processes keep their own)


def default_workers() -> int:
    """All CPUs but one (the machine stays usable); at least one."""
    return max(1, (os.cpu_count() or 1) - 1)


def _chunk_symbol_run(
    task: Task, items: Sequence[tuple[int, RunSettings]], sources: SymbolSources
) -> Iterator[tuple[int, Outcome]]:
    """`items` (variant index, settings) on one symbol's range; the series is loaded once and
    shared (`SeriesCache`), strategy and engine are new for every variant."""
    symbol, start, end = task
    for index, settings in items:
        try:
            job = _load(sources, symbol, start, end, settings, cache=_SERIES)
        except (UnsupportedSymbolError, NoDataError, UnmappedSymbolError) as e:
            yield index, e
        else:
            yield index, _run_job(job)


def _run_chunk_in_worker(task, items, sources) -> list[tuple[int, Outcome]]:
    return list(_chunk_symbol_run(task, items, sources))


def iter_symbol_runs(
    tasks: Sequence[Task],
    settings_list: Sequence[RunSettings],
    sources: SymbolSources = DEFAULT_SOURCES,
    workers: int | None = None,
) -> Iterator[tuple[int, int, Outcome]]:
    """Every task (symbol, first day, last day) with every settings, as `(variant index, task
    index, outcome)` in completion order. Tasks run in parallel processes (`workers`, default
    `default_workers()`); the variants of a task run in chunks (`ManyConfig`) on one loading of
    its candles. A symbol the strategy has no rules for, or without a cached day, is an
    `Outcome` error like in `run_backtests`; any other error is raised (the workers stop)."""
    n = len(settings_list)
    if n == 0:
        return
    workers = workers or default_workers()
    chunks = max(-(-n // MANY.max_chunk), min(n, workers // max(1, len(tasks))))
    bounds = [round(i * n / chunks) for i in range(chunks + 1)]
    units = [  # chunk by chunk, so early variants finish first
        (t, [(v, settings_list[v]) for v in range(lo, hi)])
        for lo, hi in pairwise(bounds)
        if hi > lo
        for t in range(len(tasks))
    ]
    if workers <= 1 or len(units) == 1:
        try:
            for t, items in units:
                for v, outcome in _chunk_symbol_run(tasks[t], items, sources):
                    yield v, t, outcome
        finally:
            _SERIES.clear()
        return
    ctx = multiprocessing.get_context("spawn")
    pool = ProcessPoolExecutor(min(workers, len(units)), ctx)
    try:
        futures = {pool.submit(_run_chunk_in_worker, tasks[t], i, sources): t for t, i in units}
        for future in as_completed(futures):
            for v, outcome in future.result():  # a worker's error is raised here
                yield v, futures[future], outcome
    except BaseException:  # failed or the consumer stopped: stop the workers
        _kill_workers(pool)
        raise
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def run_backtests_many(
    symbols: Sequence[str],
    start: date,
    end: date,
    settings_list: Sequence[RunSettings],
    sources: SymbolSources = DEFAULT_SOURCES,
    workers: int | None = None,
) -> Iterator[tuple[int, RunResult]]:
    """`run_backtests(symbols, start, end, settings, sources)` for every settings, as `(index,
    result)` in completion order, with the candles of a symbol loaded once for all of them and
    the (symbol, variant) runs spread over `workers` processes."""
    requested = tuple(dict.fromkeys(symbols))
    if not requested:
        raise ValueError("no symbols")
    if end < start:
        raise ValueError(f"end {end} is before start {start}")
    tasks = [(s, start, end) for s in requested]
    got: dict[int, dict[str, Outcome]] = {}
    for v, t, outcome in iter_symbol_runs(tasks, settings_list, sources, workers):
        got.setdefault(v, {})[requested[t]] = outcome
        if len(got[v]) == len(requested):
            yield v, combine_runs(requested, start, end, settings_list[v], sources, got.pop(v))


# --- results folder --------------------------------------------------------------------


def jsonable(value):
    """Settings and records as JSON values: dataclasses -> dicts of their fields, enums ->
    their name, sets -> sorted lists, times -> ISO strings."""
    if isinstance(value, SpreadTable):
        return value.to_dict()  # integer year / hour keys written as text, read back as int
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: jsonable(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, Mapping):
        return {str(jsonable(k)): jsonable(v) for k, v in value.items()}
    if isinstance(value, set | frozenset):
        return sorted((jsonable(v) for v in value), key=str)
    if isinstance(value, list | tuple):
        return [jsonable(v) for v in value]
    if isinstance(value, datetime | date | time):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    return value


TRADE_COLUMNS = (
    "id", "symbol", "direction", "session", "entry_time", "entry_candle", "entry",
    "entry_fill", "initial_stop", "take_profit", "take_profit_2", "take_profit_3",
    "tp1_share", "tp2_share", "planned_rr",
    "exit_time", "exit_candle", "exit_price", "exit_fill", "exit_reason", "r_gross", "r_net",
    "spread_r", "commission_r", "swap_r", "funding_r", "break_even_time", "break_even_stop", "mae_r", "mfe_r",
    "tags", "confluence", "reason", "parts", "limit_fill",
)  # fmt: skip


def session_label(session: dict) -> str:
    return f"{session['session']} {session['trading_date']}"


def _session_of(trade: TradeResult, sessions: Sequence[dict]) -> str:
    """The session record the trade was entered in (start < entry close time <= end)."""
    for s in sessions:
        start, end = datetime.fromisoformat(s["start"]), datetime.fromisoformat(s["end"])
        if start < trade.entry_time <= end:
            return session_label(s)
    return ""


def trade_rows(result: RunResult) -> list[dict]:
    """One dict per trade (TRADE_COLUMNS), merged order; `id` counts from 1."""
    rows = []
    for i, t in enumerate(result.trades, 1):
        row = {
            "id": i,
            "direction": "long" if t.direction is Direction.BULLISH else "short",
            "session": _session_of(t, result.runs[t.symbol].sessions),
            "planned_rr": t.planned_r,
            "exit_reason": t.exit_reason.value,
            "tags": ";".join(sorted(t.tags)),
            "parts": json.dumps(
                [
                    {
                        "share": p.share,
                        "time": p.time.isoformat(),
                        "price": p.price,
                        "reason": p.reason.value,
                        "r_gross": p.r_gross,
                        "fill": p.fill,
                        "r_fills": p.r_fills,
                    }
                    for p in t.parts
                ]
            ),
        }
        for name in TRADE_COLUMNS:
            if name not in row:
                value = getattr(t, name)
                row[name] = value.isoformat() if isinstance(value, datetime) else value
        rows.append({name: row[name] for name in TRADE_COLUMNS})
    return rows


def _session_file(result: RunResult, rows: list[dict]) -> dict:
    out = {}
    for symbol, run in result.runs.items():
        ids: dict[str, list[int]] = {}
        for row in rows:
            if row["symbol"] == symbol and row["session"]:
                ids.setdefault(row["session"], []).append(row["id"])
        out[symbol] = [{**s, "trades": ids.get(session_label(s), [])} for s in run.sessions]
    return out


def new_run_id(symbols: Sequence[str], out_dir: Path, now: datetime | None = None) -> str:
    base = f"{(now or datetime.now(UTC)):%Y%m%d-%H%M%S}_{'-'.join(symbols)}"
    run_id, n = base, 1
    while (Path(out_dir) / run_id).exists():
        n += 1
        run_id = f"{base}_{n}"
    return run_id


def write_results(
    result: RunResult,
    out_dir: Path = RESULTS_DIR,
    run_id: str | None = None,
    preset: str | None = None,
) -> Path:
    """Write the run to `out_dir/<run_id>/`; returns that folder."""
    out_dir = Path(out_dir)
    run_id = run_id or new_run_id(result.symbols, out_dir)
    folder = out_dir / run_id
    folder.mkdir(parents=True, exist_ok=False)
    try:
        _write_files(result, folder, run_id, preset)
    except BaseException:  # no half-written run folder is left behind
        shutil.rmtree(folder, ignore_errors=True)
        raise
    return folder


def _write_files(result: RunResult, folder: Path, run_id: str, preset: str | None) -> None:
    rows = trade_rows(result)
    with open(folder / "trades.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, TRADE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    settings = {
        "preset": preset,
        "run": {
            "symbols": result.symbols,
            "start": result.start,
            "end": result.end,
            "warmup_days": result.settings.warmup_days,
            "cache_dirs": {s: result.sources.cache_dir(s) for s in result.symbols},
        },
        "strategy": {
            "name": strategy_name(result.settings.strategy),
            **jsonable(result.settings.strategy),
        },
        "detectors": result.settings.detectors,
        "engine": result.settings.engine,
    }
    summary = {
        "run_id": run_id,
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "symbols": result.symbols,
        "start": result.start,
        "end": result.end,
        "days": {
            s: {"first": r.first_day, "last": r.last_day, "warmup_from": r.warmup_from}
            for s, r in result.runs.items()
        },
        **result.summary(),
        "notes": [*result.notes, *(n for r in result.runs.values() for n in r.notes)],
    }
    _dump(folder / "settings.json", settings)
    _dump(folder / "summary.json", summary)
    _dump(folder / "sessions.json", _session_file(result, rows))


def _dump(path: Path, data) -> None:
    path.write_text(json.dumps(jsonable(data), indent=2), encoding="utf-8")


# --- background ------------------------------------------------------------------------


class BackgroundRun:
    """A run in a background thread (`start_run`). Poll `done` / `total` and `finished`;
    afterwards `folder` (results written), `error` or `cancelled` (`cancel()` was called:
    nothing was written) is set."""

    def __init__(self, target: Callable[[Progress, threading.Event, Progress], Path]):
        self.done = 0
        self.total = 0
        self.load_done = 0  # the loading phase (before `done` / `total` start)
        self.load_total = 0
        self.load_finished_at: float | None = None  # clock_time.monotonic() when loading ended
        self.folder: Path | None = None
        self.error: Exception | None = None
        self.cancelled = False
        self._cancel = threading.Event()
        self._thread = threading.Thread(target=self._main, args=(target,), daemon=True)
        self._thread.start()

    def _progress(self, done: int, total: int) -> None:
        self.done, self.total = done, total

    def _load_progress(self, done: int, total: int) -> None:
        self.load_done, self.load_total = done, total
        if done >= total:
            self.load_finished_at = clock_time.monotonic()

    def _main(self, target: Callable[[Progress, threading.Event, Progress], Path]) -> None:
        try:
            self.folder = target(self._progress, self._cancel, self._load_progress)
        except RunCancelled:
            self.cancelled = True
        except Exception as e:  # noqa: BLE001  (handed to the caller through `error`)
            self.error = e

    def cancel(self) -> None:
        """Stop the run at its next step; no results folder is written."""
        self._cancel.set()

    @property
    def finished(self) -> bool:
        return not self._thread.is_alive()

    def join(self, timeout: float | None = None) -> None:
        self._thread.join(timeout)


def start_run(
    symbols: Sequence[str],
    start: date,
    end: date,
    settings: RunSettings | None = None,
    sources: SymbolSources = DEFAULT_SOURCES,
    out_dir: Path = RESULTS_DIR,
    workers: int | None = None,
    preset: str | None = None,
) -> BackgroundRun:
    """`run_backtests` + `write_results` in a background thread."""

    def target(progress: Progress, cancel: threading.Event, load_progress: Progress) -> Path:
        result = run_backtests(
            symbols, start, end, settings, sources, progress, workers, cancel, load_progress
        )
        _check_cancel(cancel)
        return write_results(result, out_dir, preset=preset)

    return BackgroundRun(target)
