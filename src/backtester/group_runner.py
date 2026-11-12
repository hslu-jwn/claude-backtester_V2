"""Group loading and artifacts. Spec: design/multi-symbol.md > B; Runner, research,
artifacts and UI. This is an opt-in app-level path; legacy runners are unchanged.

Assumptions for increment 2a-3:
* Dates are inclusive UTC days, matching runner.py. UTC datetimes are exact bounds:
  entries in [start, end], and only candles closed by end reach the engine. Adapters
  may physically read whole cache files to resample; returned histories are bounded.
* Warm-up uses each input's contiguous cached history, with the legacy 14-day default
  and declared warmup_days/full_history overrides. Callbacks update indicators during
  warm-up, but their intents and exit requests are discarded. No pre-period position
  is carried in. Results are additionally filtered by first leg entry time.
* trades.csv is a statistical compatibility projection, ONE observation per closed
  group. Its price units are synthetic: entry=1, risk=1, stop=0 long / 2 short;
  exit=1+sign*gross R. These are never executable prices or an MTM path. The first
  leg supplies direction; entry is the first ordered fill and exit the last exit.
  Mixed exit reasons are labeled 'group'; the leg artifact retains actual reasons.
* Engine attributions store negative commission and spread cashflows. Legacy rows
  store spread_r and commission_r as positive charges, so negate those sums; swap
  and funding retain their signed cashflows. conversion_r=0: 2a-1 already values
  cashflows and applies no extra conversion surcharge. Slippage remains the fill
  loss beyond diagnostic spread, as reconstructed by alternating_path_gates.
* group_legs.csv contains fully closed groups' reconciled attribution only. Open
  exposure and stale marks live in unresolved.json; no hypothetical liquidation or
  realized attribution is invented for unresolved groups. Intermediate closed peers
  of residual groups need a richer engine journal in 2b.
* Values remain the engine's constant valuation mapping (not causal FX conversion).
  settings is caller metadata, nested separately from authoritative run provenance.
  These artifacts do not claim group price-integrity, MTM, risk, or UI support.
"""

from __future__ import annotations

import csv
import json
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from types import MappingProxyType

from backtester.core.market import ReferenceInput, require_utc
from backtester.core.models import Direction, Timeframe
from backtester.core.series import CandleSeries
from backtester.data.adapters.cache_adapter import candles_from_frame
from backtester.data.resample import DayBoundary, H4Alignment
from backtester.data.sources import DEFAULT_SOURCES, SymbolSources, cached_block, warmup_start
from backtester.engine.costs import CostConfig
from backtester.engine.group_backtest import GroupRunResult as EngineGroupRunResult
from backtester.engine.group_backtest import run_group_backtest
from backtester.runner import (
    TRADE_COLUMNS,
    NoDataError,
    RunSettings,
    _midnight,
    allocate_run_folder,
    jsonable,
)
from backtester.strategy.group import GroupStrategy

DEFAULT_WARMUP_DAYS = RunSettings().warmup_days
DEFAULT_COSTS = CostConfig()
NORMALIZATION = "D = sum(abs(q_i) * v_i(0) * d_i); fixed entry D and stop-risk weights."


@dataclass(frozen=True, slots=True)
class GroupRunResult(EngineGroupRunResult):
    """Engine results plus immutable provenance for reproducible group artifacts."""

    strategy_name: str
    legs: tuple[str, ...]
    references: tuple[ReferenceInput, ...]
    start: date | datetime
    end: date | datetime
    sources: SymbolSources
    cfg: CostConfig
    values: Mapping[str, float]
    warmup_days: int


def _bounds(start, end):
    begin = start if isinstance(start, datetime) else _midnight(start)
    until = end if isinstance(end, datetime) else _midnight(end + timedelta(days=1))
    require_utc(begin)
    require_utc(until)
    if until <= begin:
        raise ValueError("end must be after start (dates include their entire UTC day)")
    return begin, until


def _in_period(entry, start, end):
    begin, until = _bounds(start, end)
    return begin <= entry and (entry <= until if isinstance(end, datetime) else entry < until)


def _declarations(strategy):
    legs = strategy.legs
    if (not isinstance(legs, tuple) or len(legs) < 2 or len(set(legs)) != len(legs)
            or any(not isinstance(s, str) or not s for s in legs)):
        raise ValueError("legs must be a tuple of at least two distinct symbols")
    declarations = {r.symbol: r for r in strategy.references}
    if len(declarations) != len(strategy.references):
        raise ValueError("duplicate reference symbol declaration")
    for symbol in legs:
        declarations.setdefault(symbol, ReferenceInput(
            symbol, "leg", (Timeframe.M1,), timedelta(0)))
    return tuple(declarations[s] for s in dict.fromkeys((*legs, *declarations)))


def load_group_inputs(
    strategy: GroupStrategy, start: date | datetime, end: date | datetime,
    sources: SymbolSources = DEFAULT_SOURCES, warmup_days: int = DEFAULT_WARMUP_DAYS,
) -> Mapping[str, tuple[CandleSeries, ...]]:
    """Load one bounded bundle via source adapters, preserving gaps and input policies.

    Spec: design/multi-symbol.md > Runner, research, artifacts and UI. Like
    runner._load_references, fetch contiguous covered blocks separately, never filling
    missing days. Keep M1 and declared higher frames; no candle closes after end.
    A leg must have actual M1 data in the requested period, not just warm-up data.
    """
    begin, until = _bounds(start, end)
    if not isinstance(warmup_days, int) or warmup_days < 0:
        raise ValueError("warmup_days must be a nonnegative integer")
    bundle = {}
    for item in _declarations(strategy):
        adapter = sources.adapter(item.symbol)
        covered = sources.covered_days(item.symbol)
        warm = warmup_start(covered, begin.date(), max(warmup_days, item.warmup_days))
        history = cached_block(covered, begin.date())[0] if begin.date() in covered else warm
        series = []
        for tf in item.timeframes:
            lower = _midnight(history if tf in item.full_history else warm)
            # Zero warm-up with an intraday start still allows same-day indicator history.
            blocks = []
            for day in sorted(d for d in covered if lower.date() <= d <= until.date()):
                if blocks and blocks[-1][1] + timedelta(days=1) == day:
                    blocks[-1] = (blocks[-1][0], day)
                else:
                    blocks.append((day, day))
            candles = []
            for lo, hi in blocks:
                left, right = max(lower, _midnight(lo)), min(until, _midnight(hi + timedelta(1)))
                if left >= right:
                    continue
                frame = adapter.fetch_frame(
                    item.symbol, tf, left, right,
                    boundary=DayBoundary[item.boundary], h4=H4Alignment[item.h4_alignment],
                )
                candles.extend(c for c in candles_from_frame(frame)
                               if lower <= c.ts and c.ts + tf.duration <= until)
            series.append(CandleSeries(item.symbol, tf, candles))
        m1 = next(s for s in series if s.timeframe is Timeframe.M1)
        if item.symbol in strategy.legs and not any(
            begin <= c.ts and c.ts + Timeframe.M1.duration <= until for c in m1._candles
        ):
            raise NoDataError(f"{item.symbol}: no M1 data between {start} and {end}")
        bundle[item.symbol] = tuple(series)
    return MappingProxyType(bundle)


class _PeriodStrategy(GroupStrategy):
    """Keep indicator callbacks during warm-up without carrying their orders in."""

    def __init__(self, strategy, start, end):
        self.strategy, self.start, self.end = strategy, start, end
        self.legs, self.references = strategy.legs, strategy.references

    def on_group_candle(self, now, market):
        orders = self.strategy.on_group_candle(now, market)
        return orders if _in_period(now, self.start, self.end) else []

    def group_exits(self, now, market, open_groups):
        if not _in_period(now, self.start, self.end):
            return []
        return self.strategy.group_exits(now, market, open_groups)

    def on_group_closed(self, result):
        self.strategy.on_group_closed(result)


def run_group(
    strategy: GroupStrategy, start: date | datetime, end: date | datetime,
    sources: SymbolSources = DEFAULT_SOURCES, cfg: CostConfig = DEFAULT_COSTS,
    values: Mapping[str, float] | Sequence[float] | None = None,
) -> GroupRunResult:
    """Run the bundle once, never as separate symbol jobs.

    Warm-up decisions update the strategy, but order intents are discarded before
    start. Only first-leg entries in [start, end] enter closed/unresolved results;
    dates include their full day. No end-of-data liquidation is synthesized.
    """
    inputs = load_group_inputs(strategy, start, end, sources)
    if values is None:
        used = {s: cfg.for_symbol(s).value_per_price_unit for s in strategy.legs}
    elif isinstance(values, Mapping):
        used = {s: values[s] for s in strategy.legs}
    else:
        used = dict(zip(strategy.legs, values, strict=True))
    outcome = run_group_backtest(_PeriodStrategy(strategy, start, end), inputs, cfg, used)
    closed = tuple(g for g in outcome.closed
                   if _in_period(outcome.fills[g.group_id][0].entry_time, start, end))
    unresolved = tuple(g for g in outcome.unresolved
                       if _in_period(g.open_legs[0].entry_time, start, end))
    ids = {g.group_id for g in (*closed, *unresolved)}
    return GroupRunResult(
        closed, unresolved, outcome.rejected, outcome.notes,
        MappingProxyType({k: v for k, v in outcome.fills.items() if k in ids}),
        type(strategy).__name__, strategy.legs, tuple(strategy.references), start, end,
        sources, cfg, MappingProxyType(used), DEFAULT_WARMUP_DAYS,
    )


def group_trade_rows(result: EngineGroupRunResult) -> list[dict]:
    """One statistical row per closed group; synthetic unit risk, never leg trades.

    Spec: design/multi-symbol.md > B. See module assumptions for legacy cost signs
    and synthetic prices. Original execution prices belong in group_legs.csv.
    """
    rows = []
    groups = sorted(result.closed, key=lambda g: (
        result.fills[g.group_id][0].entry_time, g.group_id))
    for index, group in enumerate(groups, 1):
        fills = result.fills[group.group_id]
        if any(f is None for f in fills) or len(fills) != len(group.legs):
            raise ValueError(f"{group.group_id}: closed group requires all leg fills")
        first = fills[0]
        last = max(fills, key=lambda f: f.exit_time)
        sign = 1 if group.legs[0].direction is Direction.BULLISH else -1
        reason = (last.exit_reason.value if len(set(group.exit_reasons)) == 1 else "group")
        # Blank unsupported diagnostics; no fake group excursions or intrabar path.
        row = dict.fromkeys(TRADE_COLUMNS, "")
        row.update(
            id=index, symbol="/".join(leg.symbol for leg in group.legs),
            direction="long" if sign > 0 else "short",
            entry_time=first.entry_time.isoformat(), entry_candle=first.entry_time.isoformat(),
            entry=1.0, entry_fill=1.0, initial_stop=1.0 - sign,
            tp1_share=1.0, exit_time=last.exit_time.isoformat(),
            exit_candle=last.exit_time.isoformat(), exit_price=1.0 + sign * group.r_gross,
            exit_reason=reason, r_gross=group.r_gross, r_net=group.r_net,
            spread_r=-sum(p.spread_diagnostic_r for p in group.attributions),
            commission_r=-sum(p.commission_r for p in group.attributions),
            swap_r=sum(p.swap_r for p in group.attributions),
            funding_r=sum(p.funding_r for p in group.attributions), conversion_r=0.0,
            reason=f"group_id={group.group_id}; synthetic unit-risk statistical projection",
            parts="[]", limit_fill=False,
        )
        rows.append(row)
    return rows


LEG_COLUMNS = (
    "group_id", "leg_id", "symbol", "direction", "quantity", "weight", "D",
    "entry_time", "exit_time", "chart_entry", "entry_fill", "chart_exit", "exit_fill",
    "exit_reason", "gross_r", "net_r", "spread_r", "commission_r", "swap_r",
    "funding_r", "conversion_r",
)


def _leg_rows(result):
    rows = []
    for group in result.closed:
        for index, (leg, weight, part, fill) in enumerate(zip(
            group.legs, group.weights, group.attributions, result.fills[group.group_id], strict=True,
        )):
            rows.append(dict(zip(LEG_COLUMNS, (
                group.group_id, index, leg.symbol,
                "long" if leg.direction is Direction.BULLISH else "short", leg.quantity,
                weight, group.D, fill.entry_time.isoformat(), fill.exit_time.isoformat(),
                fill.chart_entry, fill.entry_fill, fill.chart_exit, fill.exit_fill,
                fill.exit_reason.value, part.gross_r, part.net_r,
                -part.spread_diagnostic_r, -part.commission_r, part.swap_r, part.funding_r, 0.0,
            ), strict=True)))
    return rows


def _write_csv(path, columns, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, columns)
        writer.writeheader()
        writer.writerows(rows)


def write_group_results(result: GroupRunResult, out_dir: Path, run_id: str | None,
                        settings: Mapping) -> Path:
    """Write five group artifacts with legacy UTF-8/CSV and run-folder conventions.

    The settings payload records all leg/reference source directories and constant
    values used, separate from caller metadata. Existing folders are never replaced.
    """
    out_dir = Path(out_dir)
    if run_id is None:
        folder = allocate_run_folder(result.legs, out_dir)
    else:
        folder = out_dir / run_id
        folder.mkdir(parents=True, exist_ok=False)
    try:
        _write_csv(folder / "trades.csv", TRADE_COLUMNS, group_trade_rows(result))
        _write_csv(folder / "group_legs.csv", LEG_COLUMNS, _leg_rows(result))
        _write_csv(folder / "rejected.csv", ("group_id", "reason"),
                   (jsonable(r) for r in result.rejected))
        symbols = tuple(dict.fromkeys((*result.legs, *(r.symbol for r in result.references))))
        payload = {
            "artifact_version": "group-2a-3", "run_id": folder.name,
            "run": {"mode": "group", "legs": result.legs, "symbols": result.legs,
                    "references": [{**jsonable(r), "max_age": r.max_age.total_seconds(),
                                    "max_age_unit": "seconds"} for r in result.references],
                    "start": result.start, "end": result.end,
                    "warmup_days": result.warmup_days,
                    "cache_dirs": {s: result.sources.cache_dir(s) for s in symbols},
                    "preferred_dirs": {s: result.sources.preferred_dirs[s] for s in symbols
                                       if s in result.sources.preferred_dirs},
                    "fallback_dirs": {s: result.sources.fallback_dirs[s] for s in symbols
                                      if s in result.sources.fallback_dirs}},
            "strategy": {"name": result.strategy_name}, "costs": result.cfg,
            "values": result.values, "normalization": NORMALIZATION,
            "synthetic_prices": "trades.csv: entry=1, unit risk; statistical use only, no MTM.",
            "notes": result.notes, "settings": settings,
        }
        for name, data in (("settings.json", payload), ("unresolved.json", result.unresolved)):
            (folder / name).write_text(json.dumps(jsonable(data), indent=2), encoding="utf-8")
    except BaseException:
        # Only remove the freshly created folder, exactly as legacy write_results does.
        shutil.rmtree(folder)
        raise
    return folder
