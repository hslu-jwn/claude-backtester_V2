"""Research runner: many variants of one strategy idea, one test run for the best.

    python -m backtester.tools.research research/grids/orb_example.toml
    python -m backtester.tools.research research/grids/orb_example.toml --workers 4
    python -m backtester.tools.research research/grids/orb_example.toml --dev-only
    python -m backtester.tools.research research/grids/orb_example.toml --retest

Spec: research-runner.md (ROADMAP 6.1 + 6.2; rules set by the user, 2026-10-21). The grid file
(`tools/research_grid.py`) names the strategy, the symbols and the settings to sweep.

1. Development: every variant runs on the development period (first cached day up to
   2021-09-13). Resumable: a finished variant (`variants/<id>/scorecard.json`) is not run again.
2. Selection: ranked by net R of the development period; only variants with at least
   `min_trades` development trades are ranked. The top one is the chosen variant.
3. Test: the chosen variant runs once on 2021-09-14 up to the last cached day. A second test of
   the same grid (same strategy, symbols, base and variants) is refused without `--retest`;
   `--dev-only` stops after the selection and keeps the test unspent.

Written to `results/research/<id>/` (id = grid file name + a hash of what is tested):
- `research.json`  grid, periods, symbols, variant count, seed, chosen variant, test status;
- `variants.csv`   the development scorecards, ranked first (`set.<setting>` columns: the grid);
- `test.csv`       the test scorecards (row per test run: 1 = the test, 2.. = retests);
- `report.md`      short summary;
- `monkeys.json`   chosen development variant's matched-null diagnostics (unless disabled);
- `variants/<id>/` the development run of each variant (a normal run folder + scorecard.json).
The chosen variant's development run and test run are also written as normal run folders
`results/<run-id>/` (results page, chart) and its settings as a preset. Every variant and every
test run is appended to the trial log (family = grid file name); the deflated Sharpe of the test
uses the number of variants run as N and the variants' development Sharpes for V.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time as clock
from collections.abc import Callable, Iterator, Sequence
from datetime import date, datetime, timedelta
from pathlib import Path

from backtester.analytics.daily import daily_net_r
from backtester.analytics.deflated_sharpe import deflated_sharpe, trade_stats
from backtester.analytics.records import read_trades
from backtester.analytics.scorecard import SCORE_KEYS, ScorecardConfig, flags, scorecard
from backtester.analytics.trial_log import TRIALS_FILE, read_all, submission_identity
from backtester.analytics.trial_log import now_iso as _now
from backtester.analytics.verdict import (
    EDGE,
    NO_EDGE,
    WEAK,
    VerdictInputs,
    evaluate,
    period_halves,
    t_statistic,
)
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources, UnmappedSymbolError
from backtester.engine.ticks import TickRoundingStats
from backtester.filelock import file_lock
from backtester.paths import RESULTS_DIR
from backtester.presets import save_preset
from backtester.runner import (
    RunResult,
    RunSettings,
    SymbolRun,
    allocate_run_folder,
    combine_runs,
    iter_symbol_runs,
    merge_trades,
    run_backtests,
    write_results,
)
from backtester.tools import (
    news_diagnostics,
    research_bayes,
    research_diagnostics,
    research_monkeys,
    research_series,
    research_significance,
    research_stability,
    research_walk_forward,
)
from backtester.tools.intake import dataset_version
from backtester.tools.research_grid import (
    GridError,
    GridSpec,
    ResearchConfig,
    Variant,
    expand,
    families,
    grid_id,
    load_grid,
    variant_settings,
)

VERDICT_COLOUR = {EDGE: "green", WEAK: "yellow", NO_EDGE: "red"}
VARIANT_COLUMNS = ("variant_id", "variant", "rank", *SCORE_KEYS, "flags")
TEST_COLUMNS = (
    "test_run", "variant_id", "variant", "start", "end", *SCORE_KEYS, "t_stat",
    "deflated_sharpe", "verdict", "verdict_label", "n_variants", "flags", "run_folder",
)  # fmt: skip
SCORECARD_FILE = "scorecard.json"
SOURCE_DEV, SOURCE_TEST, SOURCE_RETEST = "research", "research-test", "research-retest"
PRESET_NAME_MAX = 60  # presets.py: a name is 1-60 characters
REPORT_TOP = 10  # variants listed in report.md


class ResearchError(ValueError):
    """The run cannot go on (no data, unmapped symbol); the message says why."""


Log = Callable[..., None]


# --- data ---------------------------------------------------------------------------------------


def cached_span(symbols: Sequence[str], sources: SymbolSources) -> tuple[date, date]:
    """(first, last) cached day over all symbols."""
    firsts, lasts = [], []
    for symbol in symbols:
        try:
            days = sources.cached_days(symbol)
        except UnmappedSymbolError as e:
            raise ResearchError(str(e)) from e
        if days:
            firsts.append(days[0])
            lasts.append(days[-1])
    if not firsts:
        raise ResearchError(f"no cached data for {', '.join(symbols)}")
    return min(firsts), max(lasts)


def segments(
    symbol: str, start: date, end: date, sources: SymbolSources = DEFAULT_SOURCES
) -> list[tuple[date, date]]:
    """The runs of consecutive cached days of `symbol` inside [start, end]. The runner needs
    every day of a range in the cache; histdata.com has no file for a closed 1 January, so a
    long range is run in pieces at such days (the daily ATR restarts after the gap)."""
    cached = sorted(d for d in set(sources.cached_days(symbol)) if start <= d <= end)
    out: list[list[date]] = []
    for d in cached:
        if out and d - out[-1][1] == timedelta(days=1):
            out[-1][1] = d
        else:
            out.append([d, d])
    return [(a, b) for a, b in out]


def _join(symbol: str, runs: list) -> SymbolRun:
    notes = [n for r in runs for n in r.notes]
    if len(runs) > 1:
        notes.append(f"{symbol}: run in {len(runs)} pieces (days missing in the cache between)")
    return SymbolRun(
        symbol,
        min(r.first_day for r in runs),
        max(r.last_day for r in runs),
        min(r.warmup_from for r in runs),
        tuple(t for r in runs for t in r.trades),
        tuple(s for r in runs for s in r.sessions),
        tuple(notes),
        TickRoundingStats.combined(r.tick_rounding for r in runs),
    )


def _pieces(
    symbols: Sequence[str], start: date, end: date, sources: SymbolSources
) -> dict[tuple[date, date], list[str]]:
    groups: dict[tuple[date, date], list[str]] = {}
    for symbol in symbols:
        for piece in segments(symbol, start, end, sources):
            groups.setdefault(piece, []).append(symbol)
    if not groups:
        raise ResearchError(f"no cached day between {start} and {end} for {', '.join(symbols)}")
    return groups


def _assemble(
    symbols: Sequence[str],
    start: date,
    end: date,
    settings: RunSettings,
    sources: SymbolSources,
    results: Sequence[RunResult],
) -> RunResult:
    """The pieces' results (`run_backtests` of each piece), trades merged per symbol."""
    per_symbol: dict[str, list] = {}
    notes: list[str] = []
    for result in results:
        notes += result.notes
        for name, run in result.runs.items():
            per_symbol.setdefault(name, []).append(run)
    runs = {s: _join(s, per_symbol[s]) for s in symbols if s in per_symbol}
    return RunResult(
        tuple(runs), start, end, settings, sources, runs, merge_trades(list(runs.values())),
        tuple(notes),
    )  # fmt: skip


def run_period(
    symbols: Sequence[str],
    start: date,
    end: date,
    settings: RunSettings,
    sources: SymbolSources,
    workers: int | None,
) -> RunResult:
    """`run_backtests` over each cached piece of each symbol, trades merged per symbol."""
    groups = _pieces(symbols, start, end, sources)
    results = [
        run_backtests(names, a, b, settings, sources=sources, workers=workers)
        for (a, b), names in sorted(groups.items())
    ]
    return _assemble(symbols, start, end, settings, sources, results)


def run_period_many(
    symbols: Sequence[str],
    start: date,
    end: date,
    settings_list: Sequence[RunSettings],
    sources: SymbolSources,
    workers: int | None,
) -> Iterator[tuple[int, RunResult]]:
    """`run_period` for every settings, as `(index, result)` in completion order: the candles of
    each symbol piece are loaded once for all variants and the (piece x variant chunk) runs are
    spread over `workers` processes (`runner.iter_symbol_runs`). Same trades as `run_period`."""
    groups = sorted(_pieces(symbols, start, end, sources).items())
    tasks = [(name, a, b) for (a, b), names in groups for name in names]
    slots = {task: i for i, task in enumerate(tasks)}
    got: dict[int, dict[int, object]] = {}
    for v, t, outcome in iter_symbol_runs(tasks, settings_list, sources, workers):
        got.setdefault(v, {})[t] = outcome
        if len(got[v]) < len(tasks):
            continue
        outcomes = got.pop(v)
        results = [
            combine_runs(
                names, a, b, settings_list[v], sources,
                {name: outcomes[slots[(name, a, b)]] for name in names},
            )
            for (a, b), names in groups
        ]  # fmt: skip
        yield v, _assemble(symbols, start, end, settings_list[v], sources, results)


# --- small helpers -------------------------------------------------------------------------------


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _code_version() -> dict:
    """Git provenance of this checkout; unavailable git metadata never blocks a run."""
    root = Path(__file__).resolve().parents[3]

    def git(*args):
        return subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()

    try:
        commit = git("rev-parse", "HEAD")
        dirty = git("status", "--porcelain")
    except (OSError, subprocess.SubprocessError):
        return {"code_commit": None, "code_dirty": None}
    return {"code_commit": commit, "code_dirty": bool(dirty)}


def _submission_stem(identity: dict) -> str:
    return f"{identity['strategy_id']}__v{identity['specification_version']}"


def _test_authorized(identity: dict | None, results_dir: Path) -> bool:
    if isinstance(identity, GridSpec):  # Compatibility for existing callers.
        identity = identity.submission
    if identity is None:
        return True
    path = results_dir / "intake" / _submission_stem(identity) / "test_authorization.json"
    authorization = _read_json(path)
    if not isinstance(authorization, dict):
        return False
    quote = authorization.get("quote")
    try:
        datetime.fromisoformat(authorization["authorized_at"])
    except (KeyError, TypeError, ValueError):
        return False
    return (
        authorization.get("authorized_by") == "user"
        and isinstance(quote, str)
        and bool(quote.strip())
        and authorization.get("experiment_id") == identity["experiment_id"]
    )


def _trial_submission(spec: GridSpec, source: str) -> dict | None:
    if spec.submission is None:
        return None
    identity = dict(spec.submission)
    number = None
    if source == SOURCE_TEST:
        number = 1
    elif source.startswith(SOURCE_RETEST + "-"):
        number = int(source.removeprefix(SOURCE_RETEST + "-")) + 1
    if number is not None:
        identity["experiment_id"] = f"{_submission_stem(identity)}__FINAL_HOLDOUT__{number}"
    return identity


def _holdout_number(spec: GridSpec, test_info: dict, trials: Path) -> int:
    latest = int(test_info.get("run", 0))
    if spec.submission is not None:
        prefix = _submission_stem(spec.submission) + "__FINAL_HOLDOUT__"
        for record in read_all(trials):
            experiment = (record.submission or {}).get("experiment_id", "")
            if experiment.startswith(prefix) and experiment[len(prefix) :].isdigit():
                latest = max(latest, int(experiment[len(prefix) :]))
    return latest + 1


def _write_csv(path: Path, columns: Sequence[str], rows: Sequence[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: "" if row.get(c) is None else row[c] for c in columns})


def _set_columns(spec: GridSpec) -> list[str]:
    return (["family"] if spec.grids else []) + list(
        dict.fromkeys(f"set.{name}" for family in families(spec) for name in family.grid)
    )


def _setting_cells(spec: GridSpec, overrides: dict) -> dict:
    return research_diagnostics.setting_cells(spec, overrides)


def _log_settings(spec: GridSpec, overrides: dict) -> dict:
    settings = {"strategy": spec.strategy, "base": spec.base, "set": overrides}
    calendars = news_diagnostics.active_calendars()
    if calendars is not None:
        config = variant_settings(spec, Variant("", "", overrides)).engine.news
        digest = calendars.digest(config)
        if digest is not None:
            settings["calendar_sha256"] = digest
    return settings


# --- development ---------------------------------------------------------------------------------


def _finished_variant(vdir: Path) -> dict | None:
    """The stored development result of a finished variant (a scorecard file); the folder of
    one without (an interrupted write) is removed, it runs again."""
    done = _read_json(vdir / SCORECARD_FILE)
    if done is None and vdir.exists():
        shutil.rmtree(vdir)
    return done


def _day_stats(trades, start: date, end: date):
    """One DSR definition (the user, 2026-10-27): moments and Sharpe of the daily net R over the
    weekdays start..end, as the trial log (`trial_log.make_record`) and the Monte Carlo check 7."""
    return trade_stats(daily_net_r(trades, start, end))


def _store_variant(
    spec: GridSpec,
    variant: Variant,
    result: RunResult,
    periods: dict,
    folder: Path,
    sc_cfg: ScorecardConfig,
    trials: Path,
    sources: SymbolSources,
) -> dict:
    """Write a variant's development run, trial log line and scorecard; returns the result."""
    vdir = folder / "variants" / variant.id
    start, end = periods["dev_start"], periods["dev_end"]
    write_results(result, folder / "variants", variant.id)
    _dump(vdir / "diagnostics.json", research_diagnostics.snapshot(result.trades))
    data = {
        "id": variant.id,
        "name": variant.name,
        "overrides": variant.overrides,
        "scorecard": scorecard(result.trades, sc_cfg, start, end),
        "day_sharpe": _day_stats(result.trades, start, end).sharpe,
    }
    _dump(vdir / SCORECARD_FILE, data)
    _daily_series(
        spec, variant.overrides, vdir, start, end, sources, trials, SOURCE_DEV, trades=result.trades
    )
    return data


def _daily_series(
    spec,
    overrides,
    folder,
    start,
    end,
    sources,
    trials,
    source,
    *,
    trades=None,
    family=None,
    note="",
):
    calendars = news_diagnostics.active_calendars()
    if calendars is not None:
        config = variant_settings(spec, Variant("", "", overrides)).engine.news
        calendars.write_run(folder, config, read_trades(folder) if trades is None else trades)
    identity = _trial_submission(spec, source)
    if identity is not None:
        _dump(
            folder / "info.json",
            {
                "submission": identity,
                "dataset": dataset_version(spec.symbols, start, end, sources),
                **_code_version(),
            },
        )
    with submission_identity(identity):
        research_series.ensure(
            folder,
            start,
            end,
            sources,
            trials,
            (
                family or spec.name,
                spec.strategy,
                _log_settings(spec, overrides),
                spec.symbols,
                source,
            ),
            trades=trades,
            reader=read_trades,
            note=note,
        )


def _sensitivity(
    spec: GridSpec,
    chosen: Variant,
    best: dict,
    periods: dict,
    folder: Path,
    sc_cfg: ScorecardConfig,
    trials: Path,
    sources: SymbolSources,
    workers: int | None,
    log: Log,
) -> dict | None:
    """Spec: research-runner.md > Parameter sensitivity. No selection or test-period inputs."""
    if not spec.sensitivity:
        return None
    rows = research_stability.neighbours(spec, chosen)
    completed = {}
    pending = {}
    for row in rows:
        if row["status"] == "skipped":
            log(f"sensitivity skipped {row['setting']}={row['value']}: {row['reason']}")
            continue
        sid = row["id"]
        if sid in pending or sid in completed:
            continue
        data = _finished_variant(folder / "sensitivity" / sid)
        if data is not None:
            _daily_series(
                spec,
                row["overrides"],
                folder / "sensitivity" / sid,
                periods["dev_start"],
                periods["dev_end"],
                sources,
                trials,
                "research-sensitivity",
                family=f"{spec.name}-sensitivity",
            )
            completed[sid] = data
        else:
            pending[sid] = row
    todo = list(pending.values())
    for index, result in run_period_many(
        spec.symbols, periods["dev_start"], periods["dev_end"],
        [variant_settings(spec, Variant(r["id"], r["id"], r["overrides"])) for r in todo],
        sources, workers,
    ) if todo else ():  # fmt: skip
        row = todo[index]
        sid = row["id"]
        write_results(result, folder / "sensitivity", sid)
        card = scorecard(result.trades, sc_cfg, periods["dev_start"], periods["dev_end"])
        completed[sid] = {"scorecard": card}
        _dump(folder / "sensitivity" / sid / SCORECARD_FILE, completed[sid])
        _daily_series(
            spec,
            row["overrides"],
            folder / "sensitivity" / sid,
            periods["dev_start"],
            periods["dev_end"],
            sources,
            trials,
            "research-sensitivity",
            trades=result.trades,
            family=f"{spec.name}-sensitivity",
        )
        log(f"sensitivity {row['setting']}={row['value']}: net {card['net_r']:+.3f} R")
    for row in rows:
        if row["status"] == "skipped":
            continue
        card = completed[row["id"]]["scorecard"]
        row.update(
            card,
            status="done",
            net_r_share=card["net_r"] / best["net_r"] if best["net_r"] else None,
        )
    _write_csv(
        folder / "sensitivity.csv",
        ["id", "setting", "change", "value", "status", "reason", *SCORE_KEYS, "net_r_share"],
        rows,
    )
    return research_stability.sensitivity_summary(rows, best["net_r"])


def _rank(rows: list[dict], min_trades: int) -> list[dict]:
    """Rows with a `rank` (1 = best net R) when they have at least `min_trades` trades, else
    None; ranked rows first, then the others by id."""
    ranked = sorted(
        (r for r in rows if r["trades"] >= min_trades), key=lambda r: (-r["net_r"], r["variant_id"])
    )
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    rest = sorted((r for r in rows if r["trades"] < min_trades), key=lambda r: r["variant_id"])
    for r in rest:
        r["rank"] = None
    return ranked + rest


def _variant_row(spec: GridSpec, data: dict, sc_cfg: ScorecardConfig) -> dict:
    card = data["scorecard"]
    return {
        "variant_id": data["id"], "variant": data["name"], "rank": None, **card,
        "flags": ";".join(flags({**card, "period": "development"}, sc_cfg)),
        "day_sharpe": data["day_sharpe"], "overrides": data["overrides"],
        **_setting_cells(spec, data["overrides"]),
    }  # fmt: skip


# --- test ----------------------------------------------------------------------------------------


def _test_row(
    spec: GridSpec,
    chosen: dict,
    result: RunResult,
    test_start: date,
    test_end: date,
    run_number: int,
    run_folder: str,
    dev_rows: list[dict],
    sc_cfg: ScorecardConfig,
) -> dict:
    trades = result.trades
    card = scorecard(trades, sc_cfg, test_start, test_end)
    r_net = [t.r_net for t in trades]
    stats = trade_stats(r_net)  # per-trade: the mean R shown in the verdict only
    n_variants = len(dev_rows)
    sharpes = [r["day_sharpe"] for r in dev_rows if r["day_sharpe"] is not None]
    dsr = deflated_sharpe(_day_stats(trades, test_start, test_end), n_variants, sharpes).dsr
    first, second = period_halves(trades, test_start, test_end)
    verdict = evaluate(
        VerdictInputs(
            mean_r=stats.mean if trades else None,
            t=t_statistic(r_net),
            percentile=None,  # kind B / C need random-entry and random-fill runs: n/a here
            half_first_net=first,
            half_second_net=second,
            stressed_net=card["net_r_stressed"],
            net_without_best=card["net_r_without_best"],
            fill_median=None,
            dsr=dsr,
        )
    )
    row = {
        "test_run": run_number, "variant_id": chosen["variant_id"], "variant": chosen["variant"],
        "start": test_start.isoformat(), "end": test_end.isoformat(), **card,
        "t_stat": t_statistic(r_net), "deflated_sharpe": dsr,
        "verdict": VERDICT_COLOUR[verdict.label], "verdict_label": verdict.label,
        "n_variants": n_variants, "run_folder": run_folder, "period": "test",
        "verdict_reason": verdict.reason,
        **_setting_cells(spec, chosen["overrides"]),
    }  # fmt: skip
    row["flags"] = ";".join(flags(row, sc_cfg))
    return row


# --- the run -------------------------------------------------------------------------------------


def _preset_name(grid: str, variant_id: str) -> str:
    tail = f" {variant_id}"
    return f"research {grid}"[: PRESET_NAME_MAX - len(tail)] + tail


def _publish_dev_run(vdir: Path, spec: GridSpec, results_dir: Path, preset: str) -> str:
    """The chosen variant's development run as a normal run folder `results/<run-id>/`."""
    target = allocate_run_folder(spec.symbols, results_dir)
    run_id = target.name
    try:
        shutil.copytree(
            vdir, target, ignore=shutil.ignore_patterns(SCORECARD_FILE), dirs_exist_ok=True
        )
    except BaseException:
        shutil.rmtree(target, ignore_errors=True)
        raise
    for name, key, value in (
        ("summary.json", "run_id", run_id),
        ("settings.json", "preset", preset),
    ):
        path = target / name
        data = _read_json(path)
        if data is not None:
            data[key] = value
            _dump(path, data)
    return run_id


def run_research(
    grid_path: Path | str,
    *,
    results_dir: Path = RESULTS_DIR,
    workers: int | None = None,
    retest: bool = False,
    dev_only: bool = False,
    walk_forward: bool = False,
    sources: SymbolSources = DEFAULT_SOURCES,
    config: ResearchConfig | None = None,
    bayes_config=None,
    log: Log = print,
) -> dict:
    """Run the grid file; returns the outcome: `status` ("done", "dev_only", "no_test",
    "refused"), `message`, `id`, `folder`, `variants`, `ranked`, `chosen` and `test` (the same
    entries as research.json)."""
    cfg = config or ResearchConfig()
    results_dir = Path(results_dir)
    spec = load_grid(grid_path, cfg)
    variants, size, sampled = expand(spec)
    rid = grid_id(spec, variants)
    folder = results_dir / "research" / rid
    # Every report/variant/resume write for this grid shares one transaction lock.
    # Distinct grids can still run concurrently. Spec: research-runner.md > Job queue.
    with (
        file_lock(results_dir / ".locks" / "research" / f"{rid}.lock"),
        news_diagnostics.research_calendars([variant_settings(spec, v) for v in variants], folder),
    ):
        return _run_research_locked(
            spec,
            variants,
            size,
            sampled,
            rid,
            folder,
            cfg,
            results_dir,
            workers=workers,
            retest=retest,
            dev_only=dev_only,
            walk_forward=walk_forward,
            sources=sources,
            bayes_config=bayes_config,
            log=log,
        )


def _run_research_locked(
    spec,
    variants,
    size,
    sampled,
    rid,
    folder,
    cfg,
    results_dir,
    *,
    workers,
    retest,
    dev_only,
    walk_forward,
    sources,
    bayes_config,
    log,
):
    first, last = cached_span(spec.symbols, sources)
    dev_end = min(cfg.cutoff - timedelta(days=1), last)
    if first > dev_end:
        raise ResearchError(
            f"no development data before {cfg.cutoff} for {', '.join(spec.symbols)}"
        )
    periods = {"dev_start": first, "dev_end": dev_end, "test_start": cfg.cutoff, "test_end": last}
    sc_cfg = ScorecardConfig(min_trades=spec.min_trades)

    previous = _read_json(folder / "research.json") or {}
    test_info = previous.get("test") or {"status": "not_run", "run": 0, "retests": 0}
    info = {
        "id": rid, "name": spec.name, "grid_file": str(spec.path), "version": 1,
        "created": previous.get("created", _now()), "updated": _now(), "status": "running",
        "strategy": spec.strategy, "idea": spec.idea,
        "symbols": list(spec.symbols), "base": spec.base,
        "grid": spec.grid, "grid_size": size, "variants": len(variants), "sampled": sampled,
        "seed": spec.seed, "min_trades": spec.min_trades, "max_variants": spec.max_variants,
        "periods": {
            "cutoff": cfg.cutoff.isoformat(),
            "development": {"start": first.isoformat(), "end": dev_end.isoformat()},
            "test": {"start": cfg.cutoff.isoformat(), "end": last.isoformat()},
        },
        "ranked": 0, "chosen": previous.get("chosen"), "test": test_info,
    }  # fmt: skip
    info.update(_code_version())
    if spec.submission is not None:
        info["submission"] = spec.submission
        info["dataset"] = dataset_version(spec.symbols, first, last, sources)
    if spec.grids:
        info["grids"] = [{"name": f.name, "base": f.base, "grid": f.grid} for f in spec.grids]
        for entry, family in zip(info["grids"], spec.grids, strict=True):
            entry["compare_to"] = family.compare_to
    info["live_expectation_range"] = cfg.live_expectation_range
    calendars = news_diagnostics.active_calendars()
    if calendars is not None:
        info["news_calendars"] = calendars.manifest()
        for item in info["news_calendars"]:
            log(f"news: {item['status']}; {item['path']}; sha256={item['sha256']}")
    _dump(folder / "research.json", info)
    log(
        f"research {rid}: {spec.strategy} {','.join(spec.symbols)}, {len(variants)} variants"
        f"{f' (sample of {size}, seed {spec.seed})' if sampled else ''}, "
        f"development {first}..{dev_end}"
    )

    trials = results_dir / TRIALS_FILE
    done: dict[str, dict] = {}
    for variant in variants:
        data = _finished_variant(folder / "variants" / variant.id)
        if data is not None and "day_sharpe" not in data:  # old per-trade Sharpe: runs again
            shutil.rmtree(folder / "variants" / variant.id)
            data = None
        if data is not None:
            _daily_series(
                spec,
                variant.overrides,
                folder / "variants" / variant.id,
                first,
                dev_end,
                sources,
                trials,
                SOURCE_DEV,
            )
            done[variant.id] = data
            log(f"[{len(done)}/{len(variants)}] {variant.id} {variant.name}: "
                f"{data['scorecard']['trades']} trades, net {data['scorecard']['net_r']:+.1f} R "
                "(done before)")  # fmt: skip
    pending = [v for v in variants if v.id not in done]
    rerun = {v.id for v in pending}  # run again now: a published dev run of it is stale
    started = clock.perf_counter()
    for index, result in run_period_many(
        spec.symbols, periods["dev_start"], periods["dev_end"],
        [variant_settings(spec, v) for v in pending], sources, workers,
    ) if pending else ():  # fmt: skip
        variant = pending[index]
        data = _store_variant(spec, variant, result, periods, folder, sc_cfg, trials, sources)
        done[variant.id] = data
        card = data["scorecard"]
        log(
            f"[{len(done)}/{len(variants)}] {variant.id} {variant.name}: {card['trades']} trades, "
            f"net {card['net_r']:+.1f} R ({clock.perf_counter() - started:.0f}s since start)"
        )
    rows = [_variant_row(spec, done[v.id], sc_cfg) for v in variants]
    if spec.grids:
        for row, variant in zip(rows, variants, strict=True):
            row["family"] = variant.family
    rows = _rank(rows, spec.min_trades)
    ranked = [r for r in rows if r["rank"] is not None]
    info["ranked"] = len(ranked)
    info["significance"] = research_significance.calculate(
        folder,
        [v.id for v in variants],
        ranked[0]["variant_id"] if ranked else None,
        reader=read_trades,
    )
    _dump(folder / "significance.json", info["significance"])
    if ranked:
        selected = ranked[0]
        selected["flags"] = ";".join(
            filter(
                None,
                [
                    selected["flags"],
                    *info["significance"]["flags"],
                ],
            )
        )
    _write_csv(folder / "variants.csv", [*VARIANT_COLUMNS, *_set_columns(spec)], rows)

    def finish(status: str, message: str, chosen: dict | None) -> dict:
        from backtester.tools import drawdown_report

        info.update(status=status, chosen=chosen, test=test_info, updated=_now())
        # Keep the once-only test guard durable even if optional reporting fails.
        _dump(folder / "research.json", info)
        info["monkeys"] = None
        if chosen is not None and spec.monkeys:
            variant = next(v for v in variants if v.id == chosen["id"])
            info["monkeys"] = research_monkeys.calculate(
                folder,
                spec,
                chosen["id"],
                first,
                dev_end,
                variant_settings(spec, variant),
                sources,
            )
            _dump(folder / "monkeys.json", info["monkeys"])
            selected = next(r for r in rows if r["variant_id"] == chosen["id"])
            selected["flags"] = ";".join(
                dict.fromkeys(
                    filter(
                        None,
                        [
                            *selected["flags"].split(";"),
                            *info["monkeys"].get("flags", []),
                        ],
                    )
                )
            )
        else:
            (folder / "monkeys.json").unlink(missing_ok=True)
        for saved in _test_rows(folder):
            number = int(saved["test_run"])
            variant = next(v for v in variants if v.id == saved["variant_id"])
            _daily_series(
                spec,
                variant.overrides,
                results_dir / saved["run_folder"],
                date.fromisoformat(saved["start"]),
                date.fromisoformat(saved["end"]),
                sources,
                trials,
                f"{SOURCE_RETEST}-{number - 1}" if number > 1 else SOURCE_TEST,
            )
        info["drawdown_bounds"] = {}
        if chosen is not None:
            vdir = folder / "variants" / chosen["id"]
            bounds = drawdown_report.calculate([], first, dev_end, vdir)
            drawdown_report.write(bounds, vdir)
            drawdown_report.write(bounds, results_dir / chosen["dev_run"])
            info["drawdown_bounds"]["development"] = bounds
            for saved in _test_rows(folder):
                target = results_dir / saved["run_folder"]
                bounds = drawdown_report.calculate(
                    [],
                    date.fromisoformat(saved["start"]),
                    date.fromisoformat(saved["end"]),
                    target,
                )
                drawdown_report.write(bounds, target)
                info["drawdown_bounds"][f"test {saved['test_run']}"] = bounds
        research_diagnostics.write_diagnostics(
            folder, spec, variants, rows, info, results_dir, sources
        )
        news_diagnostics.write_research(folder, variants, info, results_dir)
        from backtester.tools import skill_bounds

        saved_tests = _test_rows(folder)
        skill_bounds.research_results(
            folder, results_dir, info, rows, saved_tests, first, dev_end, sources, spec.symbols
        )
        from backtester.tools import strategy_profile

        strategy_profile.research_results(
            folder, results_dir, info, saved_tests, first, dev_end, sources
        )
        if saved_tests:
            _write_csv(folder / "test.csv", [*TEST_COLUMNS, *_set_columns(spec)], saved_tests)
        pairs, info["twins"] = research_stability.twin_rows(spec, variants, rows)
        info["bayes"] = research_bayes.calculate(
            folder,
            results_dir,
            spec,
            variants,
            chosen["id"] if chosen else None,
            _test_rows(folder),
            pairs,
            reader=read_trades,
            config=bayes_config,
        )
        _dump(folder / "bayes.json", info["bayes"])
        if chosen is not None:
            selected = next(r for r in rows if r["variant_id"] == chosen["id"])
            selected["flags"] = ";".join(
                filter(
                    None,
                    [
                        selected["flags"],
                        *info["bayes"]["flags"],
                    ],
                )
            )
            _write_csv(folder / "variants.csv", [*VARIANT_COLUMNS, *_set_columns(spec)], rows)
        if any(f.compare_to for f in families(spec)):
            _write_csv(
                folder / "twins.csv",
                [
                    "family",
                    "variant_id",
                    "twin_id",
                    "status",
                    "net_r",
                    "twin_net_r",
                    "difference",
                    "trades",
                    "twin_trades",
                ],
                pairs,
            )
        mode = spec.walk_forward or (
            "anchored" if walk_forward or spec.walk_forward_study else None
        )
        if mode:
            wf_rows, info["walk_forward"] = research_walk_forward.from_saved(
                folder,
                variants,
                ranked[0]["variant_id"] if ranked else None,
                first,
                dev_end,
                mode,
                spec.train_years,
                train_months=spec.train_months,
                test_months=spec.test_months,
                step_months=spec.step_months,
                study=spec.walk_forward_study,
            )
            columns = (
                research_walk_forward.LEGACY_COLUMNS
                if spec.train_years is not None
                else research_walk_forward.COLUMNS
            )
            _write_csv(folder / "walk_forward.csv", columns, wf_rows)
            if spec.walk_forward_study:
                _write_csv(
                    folder / "walk_forward_study.csv",
                    research_walk_forward.STUDY_COLUMNS,
                    info["walk_forward"]["study"],
                )
            else:
                (folder / "walk_forward_study.csv").unlink(missing_ok=True)
        else:
            info.pop("walk_forward", None)
            (folder / "walk_forward.csv").unlink(missing_ok=True)
            (folder / "walk_forward_study.csv").unlink(missing_ok=True)
        _dump(folder / "research.json", info)
        _write_report(folder, info, rows, _test_rows(folder))
        return {
            "status": status, "message": message, "id": rid, "folder": folder,
            "variants": len(variants), "ranked": len(ranked), "chosen": chosen, "test": test_info,
        }  # fmt: skip

    if not ranked:
        best = max((r["trades"] for r in rows), default=0)
        message = (
            f"no variant has at least {spec.min_trades} development trades (the most has {best}); "
            "no test run. Lower min_trades in the grid file or widen the grid."
        )
        test_info.update(status="skipped", reason=message)
        return finish("no_test", message, None)

    best = ranked[0]
    info["sensitivity"] = _sensitivity(
        spec,
        next(v for v in variants if v.id == best["variant_id"]),
        best,
        periods,
        folder,
        sc_cfg,
        trials,
        sources,
        workers,
        log,
    )
    authorization_skip = None
    if not dev_only and not _test_authorized(spec.submission, results_dir):
        authorization_skip = (
            f"test skipped: no user authorization for {_submission_stem(spec.submission)}"
        )
        log(authorization_skip)
        info["test_skip"] = authorization_skip
        dev_only = True
    if dev_only:
        info["chosen"] = previous.get("chosen") if previous.get("chosen") else None
        test_info.setdefault("status", "not_run")
    elif test_info.get("status") == "done" and not retest:
        message = (
            f"the test of this grid was run on {test_info.get('ran_at')} (variant "
            f"{test_info.get('variant')}); a second test is only allowed with --retest"
        )
        return finish("refused", message, previous.get("chosen"))

    settings = variant_settings(spec, next(v for v in variants if v.id == best["variant_id"]))
    preset = _preset_name(rid, best["variant_id"])
    save_preset(preset, settings, results_dir / "presets")
    old = previous.get("chosen") or {}
    dev_run = old.get("dev_run") if old.get("id") == best["variant_id"] else None
    if best["variant_id"] in rerun or dev_run is None or not (results_dir / dev_run).is_dir():
        dev_run = _publish_dev_run(
            folder / "variants" / best["variant_id"], spec, results_dir, preset
        )
    chosen = {
        "id": best["variant_id"], "name": best["variant"], "overrides": best["overrides"],
        "preset": preset, "dev_run": dev_run, "dev_trades": best["trades"],
        "dev_net_r": best["net_r"],
    }  # fmt: skip
    if dev_only:
        return finish(
            "dev_only",
            authorization_skip or "development done; the test run was not started (--dev-only)",
            chosen,
        )
    if cfg.cutoff > last:
        message = f"no cached data from {cfg.cutoff} on: no test run"
        test_info.update(status="skipped", reason=message)
        return finish("no_test", message, chosen)

    log(f"test: {best['variant_id']} {best['variant']} on {cfg.cutoff}..{last}")
    result = run_period(spec.symbols, cfg.cutoff, last, settings, sources, workers)
    run_folder = write_results(result, results_dir, preset=preset).name
    _dump(
        results_dir / run_folder / "diagnostics.json", research_diagnostics.snapshot(result.trades)
    )
    run_number = _holdout_number(spec, test_info, trials)
    is_retest = run_number > 1
    row = _test_row(
        spec, chosen | {"variant_id": best["variant_id"], "variant": best["variant"]}, result,
        cfg.cutoff, last, run_number, run_folder, rows, sc_cfg,
    )  # fmt: skip
    if spec.grids:
        row["family"] = next(v.family for v in variants if v.id == best["variant_id"])
    old_rows = _test_rows(folder)
    _write_csv(
        folder / "test.csv", [*TEST_COLUMNS, *_set_columns(spec)],
        [*old_rows, {**row, "flags": row["flags"]}],
    )  # fmt: skip
    test_info.clear()
    test_info.update(
        status="done", run=run_number, retests=run_number - 1, ran_at=_now(),
        variant=best["variant_id"], start=cfg.cutoff.isoformat(), end=last.isoformat(),
        run_folder=run_folder, trades=row["trades"], net_r=row["net_r"], t_stat=row["t_stat"],
        deflated_sharpe=row["deflated_sharpe"], verdict=row["verdict"],
        verdict_label=row["verdict_label"], verdict_reason=row["verdict_reason"],
        n_variants=row["n_variants"], flags=row["flags"].split(";") if row["flags"] else [],
    )  # fmt: skip
    info.update(chosen=chosen, test=test_info)
    _dump(folder / "research.json", info)
    _daily_series(
        spec,
        best["overrides"],
        results_dir / run_folder,
        cfg.cutoff,
        last,
        sources,
        trials,
        f"{SOURCE_RETEST}-{run_number - 1}" if is_retest else SOURCE_TEST,
        trades=result.trades,
        note=f"retest {run_number - 1} of grid {rid}" if is_retest else f"test of grid {rid}",
    )
    log(
        f"test result: {row['trades']} trades, net {row['net_r']:+.1f} R, "
        f"verdict {row['verdict']} ({row['verdict_label']})"
    )
    return finish("done", "development and test done", chosen)


def _test_rows(folder: Path) -> list[dict]:
    path = folder / "test.csv"
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _cell(value) -> str:
    """A report table cell: floats to 2 decimals, None empty."""
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _write_report(folder: Path, info: dict, rows: list[dict], tests: list[dict]) -> None:
    dev = info["periods"]["development"]
    sampled = f", sampled with seed {info['seed']}" if info["sampled"] else ""
    lines = [
        f"# Research {info['id']}",
        "",
        (
            f"- Strategy {info['strategy']}, symbols {', '.join(info['symbols'])}, "
            f"grid file {info['grid_file']}"
        ),
        (
            f"- {info['variants']} variants (full grid {info['grid_size']}{sampled}), "
            f"{info['ranked']} with at least {info['min_trades']} development trades"
        ),
        f"- Development {dev['start']} to {dev['end']}; test from {info['periods']['cutoff']}",
        f"- Status: {info['status']}",
        "",
        f"## Development, top {REPORT_TOP} by net R",
        "",
        "| rank | variant | trades | net R | avg R | flags |",
        "|---|---|---|---|---|---|",
    ]
    for r in [r for r in rows if r["rank"] is not None][:REPORT_TOP]:
        avg = "" if r["avg_r"] is None else f"{r['avg_r']:+.3f}"
        lines.append(
            f"| {r['rank']} | {r['variant']} | {r['trades']} | {r['net_r']:+.1f} | {avg} | "
            f"{r['flags']} |"
        )
    chosen = info.get("chosen")
    lines += ["", "## Chosen variant", ""]
    if chosen is None:
        lines.append("None (no variant has enough development trades).")
    else:
        lines.append(
            f"{chosen['id']} {chosen['name']}: {chosen['dev_trades']} development trades, "
            f"net {chosen['dev_net_r']:+.1f} R; preset `{chosen['preset']}`, "
            f"development run `{chosen['dev_run']}`."
        )
        selected = next((r for r in rows if r["variant_id"] == chosen["id"]), {})
        lines += [
            "",
            research_stability.haircut(selected.get("avg_r"), info["live_expectation_range"]),
        ]
    lines += research_significance.markdown(info.get("significance"))
    lines += research_bayes.markdown(info.get("bayes"))
    from backtester.analytics.monkeys import markdown as monkey_markdown

    lines += monkey_markdown(info.get("monkeys"))
    sensitivity = info.get("sensitivity")
    if sensitivity is not None:
        lines += [
            "",
            f"Sensitivity: **{sensitivity['status']}**. Failed settings: "
            + (
                ", ".join(sensitivity["failed_settings"])
                or ("no numeric settings" if not sensitivity["rows"] else "none")
            )
            + ".",
        ]
    else:
        lines += ["", "Sensitivity: disabled or no chosen variant."]
    for twin in info.get("twins", []):
        lines += [
            "",
            (
                f"Filter twins {twin['family']} vs {twin['compare_to']}: "
                f"{twin['matched']} matched; mean net R {_cell(twin['mean_net_r'])} vs "
                f"{_cell(twin['mean_twin_net_r'])}; lifts the average: "
                f"{twin['lifts_average'] or 'n/a'}."
            ),
        ]
    test = info["test"]
    lines += ["", "## Test", ""]
    if info.get("test_skip"):
        lines.append(info["test_skip"])
    if test.get("status") == "done":
        lines.append(
            f"Test {test['run']} ({test['start']} to {test['end']}): {test['trades']} trades, "
            f"net {test['net_r']:+.1f} R, verdict **{test['verdict']}** ({test['verdict_label']}), "
            f"deflated Sharpe {test['deflated_sharpe']} with N = {test['n_variants']}. "
            f"{test['verdict_reason']} Run `{test['run_folder']}`. Test runs so far: {len(tests)}."
        )
        average = float(tests[-1]["avg_r"]) if tests and tests[-1].get("avg_r") else None
        lines += ["", research_stability.haircut(average, info["live_expectation_range"])]
    else:
        lines.append(f"Not run ({test.get('status')}). {test.get('reason', '')}".strip())
    lines += [
        "",
        "## Development grid robustness",
        "",
        "| family | n | profitable share | mean | sd | mean - sd | robust | plateau | smoothed net R |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    notes = []
    for row in info.get("grid_robustness", []):
        lines.append(
            "| "
            + " | ".join(
                _cell(row.get(k))
                for k in (
                    "family",
                    "n",
                    "profitable_share",
                    "mean",
                    "std",
                    "adjusted",
                    "robust",
                    "plateau_variant",
                    "plateau_net_r",
                )
            )
            + " |"
        )
        if row.get("plateau_note"):
            notes.append(f"{row['family']}: {row['plateau_note']}.")
    lines += ["", *notes]
    lines += ["", "## Duplicate settings", ""]
    for duplicate in info.get("duplicates", []):
        lines.append(f"- {duplicate['id']} ({duplicate['family']}) reuses {duplicate['retained']}.")
    if not info.get("duplicates"):
        lines.append("None.")
    lines += ["", "## Shock days", ""]
    if info.get("shocks") is None:
        lines.append("Disabled (shocks = false).")
    for row in info.get("shocks") or []:
        lines.append(
            f"- {row['period']} (test run {row['test_run']}): "
            f"net {row['net_r_total']:+.3f} R, without shocks "
            f"{row['net_r_without_shocks']:+.3f} R."
        )
    lines += research_walk_forward.report(info.get("walk_forward"))
    lines += news_diagnostics.markdown(info)
    from backtester.tools import drawdown_report

    for label, bounds in info.get("drawdown_bounds", {}).items():
        lines += drawdown_report.markdown(bounds, label)
    from backtester.tools import skill_bounds

    for label, result in info.get("skill_bounds", {}).items():
        lines += skill_bounds.markdown(result, label)
    from backtester.analytics.profile import markdown as profile_markdown

    for label, result in info.get("profiles", {}).items():
        lines += profile_markdown(result, label)
    (folder / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


# --- command line ----------------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="python -m backtester.tools.research",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("grid", type=Path, help="research/grids/<name>.toml")
    p.add_argument("--workers", type=int, default=None,
                   help="worker processes (default: all CPUs but one)")  # fmt: skip
    p.add_argument("--retest", action="store_true",
                   help="allow a second test run of this grid (recorded in the trial log)")  # fmt: skip
    p.add_argument("--dev-only", action="store_true",
                   help="development and selection only; the test stays unspent")  # fmt: skip
    p.add_argument(
        "--walk-forward",
        action="store_true",
        help="calendar-month walk-forward diagnostics from saved development trades",
    )
    p.add_argument("--results-dir", type=Path, default=RESULTS_DIR, help=argparse.SUPPRESS)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        out = run_research(
            args.grid, results_dir=args.results_dir, workers=args.workers, retest=args.retest,
            dev_only=args.dev_only, walk_forward=args.walk_forward,
        )  # fmt: skip
    except (GridError, ResearchError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    print(f"\n{out['message']}")
    print(f"results: {out['folder']}")
    if out["status"] == "refused":
        print(f"error: {out['message']}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
