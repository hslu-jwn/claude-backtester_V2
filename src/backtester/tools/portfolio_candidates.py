"""Saved development members and portfolio jobs. Spec: portfolio.md."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from bisect import bisect_left
from dataclasses import asdict
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path
from types import SimpleNamespace

from backtester.analytics.daily import PRAGUE, weekdays
from backtester.analytics.portfolio_search import (
    CUTOFF,
    Member,
    SearchConfig,
    search,
    set_id,
    validate,
)
from backtester.analytics.records import read_trades
from backtester.filelock import file_lock
from backtester.jobs.storage import atomic_json
from backtester.paths import RESULTS_DIR

VERSION = 1
SORT_KEYS = (
    "net_dd",
    "net_r",
    "max_dd_r",
    "sharpe",
    "worst_month",
    "longest_dd_days",
    "avg_correlation",
    "idm",
)
ASCENDING = {"max_dd_r", "longest_dd_days", "avg_correlation"}


def _json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _inside(root, relative):
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("member folder must be inside results")
    return path


def _load_member(folder, root):
    info = _json(folder / "research.json")
    chosen = info.get("chosen") or {}
    vid = chosen.get("id")
    if not vid:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_-]+", str(vid)):
        raise ValueError("invalid chosen variant ID")
    run = _inside(root, (folder / "variants" / vid).relative_to(root))
    period = info["periods"]["development"]
    start, end = (date.fromisoformat(period[k]) for k in ("start", "end"))
    summary = _json(run / "summary.json")
    saved_settings = _json(run / "settings.json")
    saved_period = saved_settings.get("run", {})
    if any(saved_period.get(k, period[k]) != period[k] for k in ("start", "end")):
        raise ValueError("saved settings period differs from development period")
    if start > end or end >= CUTOFF or any(summary[k] != period[k] for k in ("start", "end")):
        raise ValueError("saved run must match its development period before 2021-09-14")
    if summary.get("source") in ("test", "mt5_test"):
        raise ValueError("test result cannot be a member")
    if not (run / "trades.csv").is_file():
        raise ValueError("Run this grid's pipeline first: Research › Queue a grid")
    trades = read_trades(run)
    check_trades(trades, start, end)
    if not (run / "daily.csv").is_file():
        from backtester.data.sources import DEFAULT_SOURCES
        from backtester.tools import research_series

        research_series.ensure(
            run,
            start,
            end,
            DEFAULT_SOURCES,
            root / "trials.jsonl",
            (
                info.get("name", folder.name),
                info["strategy"],
                {
                    "strategy": info["strategy"],
                    "base": info.get("base", {}),
                    "set": chosen.get("overrides", {}),
                },
                info["symbols"],
                "research",
            ),
            trades=trades,
        )
    with (run / "daily.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    days = tuple(date.fromisoformat(r["date"]) for r in rows)
    if list(days) != weekdays(start, end):
        raise ValueError("daily dates must cover the complete development run")
    flags = ()
    with (folder / "variants.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("variant_id") == vid:
                flags = tuple(f for f in row.get("flags", "").split(";") if f)
    member = Member(
        f"{folder.name}~{vid}",
        days,
        tuple(float(r["net_r_exit_booked"]) for r in rows),
        strategy=info["strategy"],
        symbols=tuple(info["symbols"]),
        folder=run.relative_to(root).as_posix(),
        flags=flags,
        settings=saved_settings,
        artifact_hash=hashlib.sha256(
            b"".join(
                (run / name).read_bytes()
                for name in ("summary.json", "settings.json", "trades.csv", "daily.csv")
            )
        ).hexdigest(),
    )
    validate(member)
    return member


def check_trades(trades, start, end):
    for trade in trades:
        if (
            trade.entry_time.utcoffset() is None
            or trade.exit_time.utcoffset() is None
            or trade.exit_time < trade.entry_time
        ):
            raise ValueError("invalid saved trade times")
        for timestamp in (trade.entry_time, trade.exit_time):
            utc_day = timestamp.astimezone(UTC).date()
            if not start <= utc_day <= end or utc_day >= CUTOFF:
                raise ValueError("saved trade is outside the development period")
        if trade.exit_time.astimezone(PRAGUE).date() >= CUTOFF:
            raise ValueError("saved trade reaches a test-period Prague day")
        if not math.isfinite(trade.r_net):
            raise ValueError("nonfinite saved trade R")


def load_members(results_dir=RESULTS_DIR):
    """Only chosen development variants. Never reads test.csv or test diagnostics."""
    root = Path(results_dir).resolve()
    members, errors = [], []
    for path in sorted((root / "research").glob("*/research.json")):
        try:
            member = _load_member(path.parent, root)
            if member is not None:
                members.append(member)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{path.parent.name}: {exc}")
    return members, errors


def pool_hash(pool):
    data = [asdict(m) for m in sorted(pool, key=lambda m: m.id)]
    return hashlib.sha256(
        json.dumps([VERSION, data], sort_keys=True, default=str).encode()
    ).hexdigest()[:20]


def search_hash(pool, sources=None):
    """Include classifier defaults/implementation and days feeding development D1 bars.

    D1 is resampled from cached day files; their available development days stamp its data.
    Keep this separate from the saved-trade fingerprint used by Monte Carlo manifests.
    Spec: portfolio.md > Saved searches and Monte Carlo.
    """
    from backtester.analytics import regime
    from backtester.data.sources import DEFAULT_SOURCES

    sources = sources or DEFAULT_SOURCES
    last = max(d for m in pool for d in m.days)
    stamp = {
        symbol: sorted(d for d in sources.cached_days(symbol) if d < CUTOFF and d <= last)
        for symbol in sorted({s for m in pool for s in m.symbols})
    }
    classifier = hashlib.sha256(Path(regime.__file__).read_bytes()).hexdigest()
    return hashlib.sha256(
        json.dumps(
            [pool_hash(pool), classifier, asdict(regime.RegimeConfig()), stamp],
            sort_keys=True,
            default=str,
        ).encode()
    ).hexdigest()[:20]


def daily_regimes(pool, sources):
    """Classify each symbol at Prague midnight using only D1 closes <= that instant."""
    from backtester.analytics.regime import RegimeHistory, _blocks
    from backtester.core.models import Timeframe
    from backtester.core.series import CandleSeries

    days = sorted({d for m in pool for d in m.days})
    output = {}
    stop = datetime.combine(days[-1], time(), PRAGUE).astimezone(UTC)
    for symbol in sorted({s for m in pool for s in m.symbols}):
        candles = {}
        cached = [d for d in sources.cached_days(symbol) if d < CUTOFF and d <= days[-1]]
        for first, last in _blocks(cached):
            start = datetime.combine(first, time(), UTC)
            end = min(datetime.combine(last + timedelta(days=1), time(), UTC), stop)
            if start < end:
                for candle in sources.adapter(symbol).fetch(symbol, Timeframe.D1, start, end):
                    candles[candle.ts] = candle
        history = RegimeHistory(
            CandleSeries(symbol, Timeframe.D1, [candles[t] for t in sorted(candles)])
        )
        output[symbol] = {}
        for day in days:
            label = history.at(datetime.combine(day, time(), PRAGUE))
            output[symbol][day] = f"{label.regime_trend} / {label.regime_vol}"
    return output


def cached_search(pool, results_dir=RESULTS_DIR, sources=None):
    from backtester.data.sources import DEFAULT_SOURCES

    for member in pool:
        validate(member)
    if not 2 <= len(pool) <= SearchConfig().max_pool or len({m.id for m in pool}) != len(pool):
        raise ValueError("choose 2..12 distinct development members")
    path = Path(results_dir) / "portfolio" / f"search_{search_hash(pool, sources)}.json"
    if path.is_file():
        return _json(path)["sets"]
    regimes = daily_regimes(pool, sources or DEFAULT_SOURCES)
    rows = search(pool, regimes=regimes)
    atomic_json(path, {"version": VERSION, "pool": [m.id for m in pool], "sets": rows})
    return rows


def ranked(rows, sort_key="net_dd", descending=None):
    if sort_key not in SORT_KEYS:
        raise ValueError("unknown portfolio sort metric")
    descending = sort_key not in ASCENDING if descending is None else descending
    return sorted(
        rows,
        key=lambda r: (
            r.get(sort_key) is None,
            (-1 if descending else 1) * (r.get(sort_key) or 0),
            r["id"],
        ),
    )


def queue_top(rows, pool, sort_key, queue, results_dir=RESULTS_DIR, descending=None):
    """Persist manifests, enqueue at most ten; never starts a runner or a backtest."""
    base = Path(results_dir).resolve() / "portfolio"
    lookup = {m.id: m for m in pool}
    jobs = []
    with file_lock(base / ".queue.lock"):
        for row in ranked(rows, sort_key, descending)[: SearchConfig().top_mc]:
            parts = [lookup[i] for i in row["members"]]
            sid = set_id(row["members"])
            fingerprint = pool_hash(parts)
            folder = base / sid
            manifest = {
                "id": sid,
                "members": row["members"],
                "fingerprint": fingerprint,
                "folders": {m.id: m.folder for m in parts},
                "period": "development",
            }
            path = folder / "members.json"
            # A queued worker checks this fingerprint against the current saved members.
            if (
                path.exists()
                and _json(path) != manifest
                and any(
                    j.state in ("pending", "running") and str(path) in j.argv for j in queue.jobs()
                )
            ):
                raise ValueError("member data changed while a portfolio job is active")
            atomic_json(path, manifest)
            summary_path = folder / "summary.json"
            if summary_path.exists() and _json(summary_path).get("fingerprint") == fingerprint:
                continue
            argv = [
                "backtester.tools.portfolio",
                "--existing",
                str(path),
                "--results-dir",
                str(Path(results_dir).resolve()),
            ]
            if any(j.argv == argv and j.state in ("pending", "running") for j in queue.jobs()):
                continue
            jobs.append(queue.add(argv, name=f"Portfolio {sid}").id)
    return jobs


def manifest_members(path, results_dir):
    manifest = _json(Path(path))
    if manifest.get("period") != "development" or manifest.get("id") != set_id(manifest["members"]):
        raise ValueError("invalid development portfolio manifest")
    pool, errors = load_members(results_dir)
    by_id = {m.id: m for m in pool}
    if not 2 <= len(manifest["members"]) <= 4 or len(set(manifest["members"])) != len(
        manifest["members"]
    ):
        raise ValueError("portfolio needs 2..4 distinct members")
    try:
        parts = [by_id[i] for i in manifest["members"]]
    except KeyError as exc:
        raise ValueError(f"member unavailable: {exc}; {'; '.join(errors)}") from exc
    if pool_hash(parts) != manifest["fingerprint"]:
        raise ValueError("development members changed; search and queue again")
    return manifest, parts


def resolve_set(sid, results_dir):
    """Allow CLI selection of any cached set, including one outside the MC top ten."""
    base = Path(results_dir) / "portfolio"
    path = base / sid / "members.json"
    if path.is_file():
        return path
    pool, _ = load_members(results_dir)
    by_id = {m.id: m for m in pool}
    for cached in sorted(base.glob("search_*.json")):
        saved = _json(cached)
        row = next((r for r in saved["sets"] if r["id"] == sid), None)
        if row is None:
            continue
        parts = [by_id[i] for i in row["members"]]
        if set_id(m.id for m in parts) != sid:
            raise ValueError("invalid cached set identity")
        if cached.stem != f"search_{search_hash([by_id[i] for i in saved['pool']])}":
            raise ValueError("development members changed; search again before choosing the test")
        atomic_json(
            path,
            {
                "id": sid,
                "members": row["members"],
                "fingerprint": pool_hash(parts),
                "folders": {m.id: m.folder for m in parts},
                "period": "development",
            },
        )
        return path
    raise ValueError("unknown portfolio set; find combinations first")


def reserve_test(ids, results_dir=RESULTS_DIR):
    """Exclusive, permanent reservation before any MT5 work, including failed attempts."""
    sid = set_id(ids)
    path = Path(results_dir) / "portfolio" / "tests" / sid / "attempt.json"
    with file_lock(Path(results_dir) / "portfolio" / ".test.lock"):
        if path.exists():
            raise ValueError(f"portfolio {sid}: test already attempted for this member set")
        atomic_json(
            path, {"members": sorted(ids), "start": CUTOFF.isoformat(), "status": "reserved"}
        )
    return path


def existing_summary(parts, results_dir, config, log=print):
    """Reuse saved trade lists and the existing portfolio / Monte Carlo calculations."""
    from backtester.analytics import portfolio as pf
    from backtester.analytics.daily import daily_net_r
    from backtester.analytics.deflated_sharpe import (
        DeflatedSharpeConfig,
        deflated_sharpe,
        trade_stats,
    )
    from backtester.analytics.trial_log import read_all
    from backtester.runner import RunSettings
    from backtester.settings import from_dict
    from backtester.tools import monte_carlo as mc
    from backtester.tools.portfolio import Component, combined_fills, portfolio_block

    for member in parts:
        validate(member)
    common = sorted(set(parts[0].days).intersection(*(m.days for m in parts[1:])))
    if not common:
        raise ValueError("no common development days")
    start, end = common[0], common[-1]
    allowed = set(common)
    lists = []
    for member in parts:
        trades = read_trades(_inside(results_dir, member.folder))
        period = member.settings.get("run", {})
        check_trades(
            trades,
            date.fromisoformat(period.get("start", member.days[0].isoformat())),
            date.fromisoformat(period.get("end", member.days[-1].isoformat())),
        )
        # Match daily_net_r exactly: weekend exits move to the next observed weekday,
        # boundary exits clamp to the run's last day. Never discard their booked R.
        lists.append(
            [
                t
                for t in trades
                if member.days[
                    min(
                        bisect_left(member.days, t.exit_time.astimezone(PRAGUE).date()),
                        len(member.days) - 1,
                    )
                ]
                in allowed
            ]
        )
    settings = [from_dict(m.settings) for m in parts]
    result = pf.combine(dict(zip([m.id for m in parts], lists, strict=True)), start, end)
    fills = combined_fills(
        lists,
        result.weights,
        settings[0].engine.costs.symbols,
        config.runs,
        config.seed,
        component_costs=[s.engine.costs.symbols for s in settings],
    )
    trial_path = Path(results_dir) / "trials.jsonl"
    records = read_all(trial_path)
    families = [[r.family for r in records if r.series == f"{m.folder}/daily.csv"] for m in parts]
    n_trials, sharpes = pf.component_trials(families, [trial_path])
    counts = pf.family_counts(families, [trial_path])
    deflated = deflated_sharpe(
        trade_stats(daily_net_r(result.trades, start, end)),
        n_trials,
        sharpes,
        DeflatedSharpeConfig(),
    )
    meta = {
        "strategy": "portfolio",
        "symbols": sorted({s for m in parts for s in m.symbols}),
        "start": start,
        "end": end,
        "source": "development",
    }
    summary = mc.build_summary(
        result.trades,
        None,
        meta,
        RunSettings(),
        config,
        log=log,
        family=set_id(m.id for m in parts),
        fills=fills,
        deflated=deflated,
    )
    comps = [
        Component(m.id, m.strategy, list(m.symbols), s.strategy, [m.strategy])
        for m, s in zip(parts, settings, strict=True)
    ]
    runs = [(s, ts, None) for s, ts in zip(settings, lists, strict=True)]
    summary["portfolio"] = portfolio_block(
        comps, runs, result, pf.PortfolioConfig(), counts, SimpleNamespace(start=start, end=end)
    )
    summary["fingerprint"] = pool_hash(parts)
    return summary


def run_existing(path, results_dir, config):
    from backtester.tools import monte_carlo as mc
    from backtester.tools.portfolio import render_report

    manifest, parts = manifest_members(path, results_dir)
    out = Path(results_dir) / "portfolio" / manifest["id"]
    summary = existing_summary(parts, results_dir, config)
    atomic_json(out / "summary.json", mc.jsonable(summary))
    (out / "report.html").write_text(
        render_report(summary, include_verdict=False), encoding="utf-8"
    )
    return summary


def run_test(sid, results_dir, config, end=None):
    from backtester.analytics.portfolio import equal_weights, weighted_trades
    from backtester.analytics.trial_log import append, make_record, read_all
    from backtester.data.cache import MT5_CACHE_DIR
    from backtester.data.sources import SymbolSources
    from backtester.runner import run_backtests
    from backtester.settings import from_dict
    from backtester.tools import monte_carlo as mc

    if not re.fullmatch(r"[a-f0-9]{20}", sid):
        raise ValueError("invalid portfolio set ID")
    manifest, parts = manifest_members(resolve_set(sid, results_dir), results_dir)
    symbols = sorted({s for m in parts for s in m.symbols})
    sources = SymbolSources.single(MT5_CACHE_DIR, symbols)
    last_days = [
        max((d for d in sources.cached_days(s) if d >= CUTOFF), default=None) for s in symbols
    ]
    if any(d is None for d in last_days):
        raise ValueError("no MT5 test data for every symbol")
    end = end or min(last_days)
    if end < CUTOFF:
        raise ValueError("test end precedes fixed cutoff")
    if end > min(last_days):
        raise ValueError("test end exceeds available MT5 data")
    trials = Path(RESULTS_DIR) / "trials.jsonl"
    identity = {"member_ids": sorted(manifest["members"])}
    with file_lock(Path(RESULTS_DIR) / "portfolio" / ".trial-test.lock"):
        if any(
            r.strategy == "portfolio"
            and r.source == "mt5"
            and r.settings == identity
            and r.start == CUTOFF.isoformat()
            for r in read_all(trials)
        ):
            raise ValueError("portfolio test already attempted for this member set")
        reservation = reserve_test(manifest["members"], RESULTS_DIR)
        append(
            make_record(
                "portfolio_test",
                "portfolio",
                identity,
                symbols,
                CUTOFF,
                end,
                "mt5",
                [],
                note="Reserved before execution; failed attempts count",
            ),
            trials,
        )
    lists = [
        list(
            run_backtests(
                m.symbols, CUTOFF, end, from_dict(m.settings), sources=sources, workers=1
            ).trades
        )
        for m in parts
    ]
    trades = weighted_trades(lists, equal_weights(len(parts)), 1.0)
    append(
        make_record(
            "portfolio_test",
            "portfolio",
            identity,
            symbols,
            CUTOFF,
            end,
            "mt5",
            trades,
            note="One-time portfolio test completed",
        ),
        trials,
    )
    summary = mc.build_summary(
        trades,
        None,
        {"strategy": "portfolio", "symbols": symbols, "start": CUTOFF, "end": end, "source": "mt5"},
        from_dict(parts[0].settings),
        config,
    )
    out = Path(results_dir) / "portfolio" / "tests" / sid
    atomic_json(out / "summary.json", mc.jsonable(summary))
    (out / "report.html").write_text(mc.render_report(summary), encoding="utf-8")
    atomic_json(reservation, {"members": sorted(manifest["members"]), "status": "done"})
    return summary
