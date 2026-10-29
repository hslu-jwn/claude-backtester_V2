"""Write or check exact default-strategy trades. Spec: ROADMAP V2.4, step 1.

    python -m backtester.tools.golden --write
    python -m backtester.tools.golden --check --strategy no_wick --workers 1

Trade indices in differences are zero-based. The runner supplies UTC timestamps and
trade order; JSON's float encoder uses repr precision (no rounding or tolerances).
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from time import perf_counter

from backtester.analytics.trial_log import now_iso
from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.trade import TradeResult
from backtester.runner import RunSettings, jsonable, run_backtests
from backtester.strategy.registry import REGISTRY, default_config


@dataclass(frozen=True, slots=True)
class GoldenConfig:
    start: date = date(2023, 1, 1)
    end: date = date(2023, 12, 31)
    folder: Path = Path("tests/golden")
    # Specs 3 and 4 name no symbols: use the brief's fallback basket.
    strategies: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("session_zone_sweep", ("XAUUSD", "GBPUSD", "GBPJPY")),
        ("ny_index_sweep", ("NAS100", "US500")),
        ("no_wick", ("XAUUSD", "GBPUSD", "NAS100", "US500")),
        ("trend_following", ("XAUUSD", "GBPUSD", "NAS100", "US500")),
        ("gap_fade", ("NAS100", "US500")),
        ("opening_range", ("US30", "US2000", "NAS100", "US500")),
        ("gap_momentum", ("XAUUSD",)),
        ("london_fix", ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCHF", "USDCAD")),
    )


def serialize_trade(trade: TradeResult) -> str:
    """Every TradeResult field, including full partial exits; stable sets, exact floats."""
    return json.dumps(jsonable(trade), ensure_ascii=False, allow_nan=False)


def _first_difference(old, new, path: str = ""):
    if isinstance(old, dict) and isinstance(new, dict):
        for key in dict.fromkeys((*old, *new)):
            field = f"{path}.{key}" if path else key
            if key not in old or key not in new:
                return field, old.get(key, "<missing>"), new.get(key, "<missing>")
            if diff := _first_difference(old[key], new[key], field):
                return diff
        return None
    if isinstance(old, list) and isinstance(new, list):
        for i, (a, b) in enumerate(zip(old, new)):
            if diff := _first_difference(a, b, f"{path}[{i}]"):
                return diff
        if len(old) != len(new):
            return f"{path}.length", len(old), len(new)
        return None
    # repr also distinguishes -0.0 from 0.0 and integers from floats.
    if type(old) is not type(new) or repr(old) != repr(new):
        return path, old, new
    return None


def compare_trades(old: list[dict], new: list[dict]) -> str | None:
    """First changed field or missing/extra trade, always with the count difference."""
    counts = f"count old={len(old)}, new={len(new)}, difference={len(new) - len(old):+d}"
    for i, (a, b) in enumerate(zip(old, new)):
        # T-03 adds diagnostic-only ambiguity counts in legacy mode. For references
        # predating them, require neutral execution metadata and compare every old
        # field normally. Never rewrite the golden lists.
        if "intrabar_ambiguous" not in a:
            b = {k: v for k, v in b.items() if k != "intrabar_ambiguous"}
        for key, neutral in (
            ("intrabar", ""),
            ("intrabar_tp_first", 0),
            ("intrabar_sl_first", 0),
            ("intrabar_fallbacks", 0),
        ):
            if key not in a and key in b:
                a = {**a, key: neutral}
        # Pre-V2.4d references have no touch diagnostics. Preserve every historic
        # field exactly, require zero new missed fills, and compare both counters
        # normally as soon as the reference contains them. Never rewrite references.
        if "tp_levels_touched" not in a and "tp_levels_touched" in b:
            b = {k: v for k, v in b.items() if k != "tp_levels_touched"}
        if "tp_levels_touched_not_filled" not in a and "tp_levels_touched_not_filled" in b:
            a = {**a, "tp_levels_touched_not_filled": 0}
        if diff := _first_difference(a, b):
            field, previous, current = diff
            return f"trade {i}, field {field}: old={previous!r}, new={current!r}; {counts}"
    if len(old) != len(new):
        kind = "missing" if len(new) < len(old) else "extra"
        return f"trade {min(len(old), len(new))}: {kind} trade; {counts}"
    return None


def git_commit() -> str:
    """Read only the current revision; no git mutations."""
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def main(argv: list[str] | None = None, *, config: GoldenConfig | None = None) -> int:
    config = config or GoldenConfig()
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--strategy", nargs="+", choices=tuple(REGISTRY), action="extend")
    parser.add_argument("--workers", type=int, default=None, help="runner's default if omitted")
    args = parser.parse_args(argv)
    if args.workers is not None and args.workers < 1:
        parser.error("--workers must be >= 1")
    names = tuple(dict.fromkeys(args.strategy or dict(config.strategies)))
    symbols_by_name = dict(config.strategies)
    manifest_path = config.folder / "manifest.json"
    manifest = {}
    if args.write:
        config.folder.mkdir(parents=True, exist_ok=True)
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if (manifest["start"], manifest["end"]) != (
                config.start.isoformat(),
                config.end.isoformat(),
            ):
                parser.error("existing manifest has a different reference period")
        manifest.update(start=config.start.isoformat(), end=config.end.isoformat())
        manifest.setdefault("strategies", {})
        commit, written = git_commit(), now_iso()
        manifest.update(git_commit=commit, date=written)
    failed = False
    for name in names:
        started = perf_counter()
        print(f"{name}: running {config.start}..{config.end}", flush=True)
        result = run_backtests(
            symbols_by_name[name],
            config.start,
            config.end,
            RunSettings(strategy=default_config(name)),
            DEFAULT_SOURCES,
            workers=args.workers,
        )
        elapsed = perf_counter() - started
        lines = [serialize_trade(t) for t in result.trades]
        path = config.folder / f"{name}.jsonl"
        for note in (*result.notes, *(n for run in result.runs.values() for n in run.notes)):
            print(f"{name}: note: {note}", flush=True)
        if args.write:
            path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
            manifest["strategies"][name] = {
                "symbols": list(symbols_by_name[name]),
                "trade_count": len(lines),
                "runtime_seconds": elapsed,
                "git_commit": commit,
                "date": written,
            }
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            report = "written"
        else:
            try:
                old = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
                report = compare_trades(old, [json.loads(line) for line in lines]) or "identical"
            except FileNotFoundError:
                report = f"missing reference {path}; new count={len(lines)}"
            except (ValueError, TypeError) as exc:
                report = f"invalid reference {path}: {exc}"
            failed |= report != "identical"
        print(f"{name}: {report} ({len(lines)} trades, {elapsed:.2f}s)", flush=True)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
