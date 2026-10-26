"""Offline V2.6b cache repair. Spec: ARCHITECTURE.md > Data sources.

Development clocks are proved per UTC input day across reference symbols. Ambiguous
days are excluded, never assigned an inferred year-wide clock. Originals are retained
outside the active cache layout; reruns always start from originals, never shift twice.
"""

import json
import shutil
import statistics
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path
from time import monotonic

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from backtester.data.cache import cache_path, read_cached_days, write_atomic
from backtester.filelock import file_lock


@dataclass(frozen=True)
class QualityConfig:
    min_weekday_share: float = 0.5
    min_match_bars: int = 100
    min_matched_share: float = 0.5
    max_error_range_share: float = 0.5
    min_runner_margin_range_share: float = 0.25
    min_runner_error_ratio: float = 2.0
    shifts: tuple[int, ...] = (-1, 0, 1)

    def __post_init__(self):
        if not 0 <= self.min_weekday_share <= 1:
            raise ValueError("min_weekday_share must be in [0, 1]")
        if self.min_match_bars < 1 or not 0 < self.min_matched_share <= 1:
            raise ValueError("invalid minimum match coverage")


QUALITY = QualityConfig()
DEVELOPMENT_END = date(2021, 9, 13)


def original_inputs(cache_dir: Path, symbol: str) -> dict[date, Path]:
    """Retained original days take precedence, independent of repair order."""
    return {
        date.fromisoformat(p.stem): p
        for root in (cache_dir, cache_dir / "_v26b_original")
        for p in (root / symbol).glob("*/*.parquet")
    }


def build_server_clock_table(
    cache_dir: Path,
    histdata_dir: Path,
    config: QualityConfig = QUALITY,
    *,
    original_histdata: bool = False,
    timeout_seconds: float = 540,
    log=print,
) -> dict[str, dict]:
    """Read-only per-date consensus; no decisive references means no clock proof.

    Spec: ARCHITECTURE.md > Data sources. `original_histdata` is audit-only:
    compensate the old 2015-2018 cache conversion before the queued rebuild.
    No symbol can override another decisive reading. Unproven readings abstain.
    """
    started = monotonic()
    cache_dir, histdata_dir = Path(cache_dir), Path(histdata_dir)
    symbols = {
        p.name
        for root in (cache_dir, cache_dir / "_v26b_original")
        if root.exists()
        for p in root.iterdir()
        if p.is_dir() and p.name.isalnum() and p.name.isupper()
    }
    table = {}
    for symbol in sorted(symbols):
        inputs = original_inputs(cache_dir, symbol)
        counts = {d: pq.ParquetFile(p).metadata.num_rows for d, p in inputs.items()}
        sparse = bad_density_days(counts, config)
        days = {d: p for d, p in inputs.items() if d <= DEVELOPMENT_END}
        for day in days:
            table.setdefault(str(day), {"status": "no reference", "shift": None, "readings": {}})
        for year in sorted({d.year for d in days}):
            if monotonic() - started > timeout_seconds:
                raise TimeoutError("server clock proof exceeded measurement budget")
            paths = list((histdata_dir / symbol / str(year)).glob("*.parquet"))
            for neighbour in (date(year, 1, 1) - timedelta(days=1), date(year + 1, 1, 1)):
                path = cache_path(histdata_dir, symbol, neighbour)
                if path.exists():
                    paths.append(path)
            if not paths:
                continue
            reference = read_cached_days(paths)
            if original_histdata and not reference.empty:
                from zoneinfo import ZoneInfo

                ny, eu = ZoneInfo("America/New_York"), ZoneInfo("Europe/London")
                stamps = reference.ts
                # Audit cache correction only affects US/EU gap weekdays. Compute
                # zone offsets per distinct UTC day rather than per M1 row.
                dates = stamps.dt.normalize()
                offsets = {
                    t: int(
                        2015 <= t.year <= 2018
                        and bool((t + pd.Timedelta(hours=12)).tz_convert(ny).dst())
                        != bool((t + pd.Timedelta(hours=12)).tz_convert(eu).dst())
                    )
                    for t in dates.unique()
                }
                adjust = dates.map(offsets)
                reference = reference.assign(
                    ts=stamps - pd.to_timedelta(adjust.astype(int), unit="h")
                )
            ref_days = dict(tuple(reference.groupby(reference.ts.dt.date)))
            raw = read_cached_days(
                [p for d, p in days.items() if d.year == year and d not in sparse]
            )
            for day, part in raw.groupby(raw.ts.dt.date):
                if monotonic() - started > timeout_seconds:
                    raise TimeoutError("server clock proof exceeded measurement budget")
                if day not in days or day in sparse:
                    continue
                neighbours = [
                    ref_days[d]
                    for d in (day - timedelta(days=1), day, day + timedelta(days=1))
                    if d in ref_days
                ]
                if not neighbours:
                    continue
                shift = proven_shift(part, pd.concat(neighbours, ignore_index=True), config)
                if shift is not None:
                    table[str(day)]["readings"][symbol] = shift
            log(f"clock proof {symbol} {year}: {monotonic() - started:.1f}s")
    for entry in table.values():
        shifts = set(entry["readings"].values())
        if len(shifts) == 1:
            entry.update(status="proven", shift=next(iter(shifts)))
        elif len(shifts) > 1:
            entry.update(status="ambiguous")
    return dict(sorted(table.items()))


def bad_density_days(counts: dict[date, int], config: QualityConfig = QUALITY) -> set[date]:
    """Weekday counts strictly below the median * configured share, per symbol/year.

    Empty weekdays are missing even if the whole year's median is zero. Empty
    weekend days carry no price/time information and remain valid closed days.
    """
    medians = {}
    for year in {d.year for d in counts}:
        values = [n for d, n in counts.items() if d.year == year and d.weekday() < 5]
        medians[year] = statistics.median(values) if values else 0
    return {
        d
        for d, n in counts.items()
        if d.weekday() < 5 and (n == 0 or n < config.min_weekday_share * medians[d.year])
    }


def histdata_fill_days(
    histdata_dir: Path, symbol: str, config: QualityConfig = QUALITY
) -> set[date]:
    """UTC days where histdata is a real fill: not itself sparse for its symbol/year."""
    counts = {
        date.fromisoformat(p.stem): pq.ParquetFile(p).metadata.num_rows
        for p in (Path(histdata_dir) / symbol).glob("*/*.parquet")
    }
    return {d for d, n in counts.items() if n > 0} - bad_density_days(counts, config)


def proven_shift(
    frame: pd.DataFrame,
    reference: pd.DataFrame,
    config: QualityConfig = QUALITY,
) -> int | None:
    """Hours to ADD to an old cached timestamp, or None when evidence is insufficient.

    Match M1 closes; require enough coverage, small absolute price error relative to
    the reference candle range, and a clearly worse runner-up. No detrending or price
    adjustment that could hide the wrong instrument. Flat/short references cannot prove a clock.
    """
    if frame.empty or reference.empty:
        return None
    ref = reference.drop_duplicates("ts").set_index("ts")
    closes = ref["bid_close"]
    scores = []
    minimum = max(config.min_match_bars, config.min_matched_share * len(frame))
    for shift in config.shifts:
        wanted = pd.DatetimeIndex(frame["ts"]) + pd.Timedelta(hours=shift)
        matched = closes.reindex(wanted).to_numpy()
        ok = np.isfinite(matched) & np.isfinite(frame["bid_close"].to_numpy())
        if ok.sum() < minimum:
            continue
        error = float(np.median(np.abs(frame["bid_close"].to_numpy()[ok] - matched[ok])))
        ranges = (ref["bid_high"] - ref["bid_low"]).reindex(wanted).to_numpy()[ok]
        scale = float(np.median(ranges))
        scores.append((error, shift, scale))
    if len(scores) < 2:
        return None
    scores.sort()
    error, shift, scale = scores[0]
    runner = scores[1][0]
    if not np.isfinite(scale) or scale <= 0:
        return None
    if error > config.max_error_range_share * scale:
        return None
    if runner < (
        config.min_runner_error_ratio * error + config.min_runner_margin_range_share * scale
    ):
        return None
    return shift


def repair_mt5(
    symbol: str,
    cache_dir: Path,
    histdata_dir: Path,
    config: QualityConfig = QUALITY,
    log=print,
    *,
    server_table: dict[str, dict] | None = None,
) -> list[dict]:
    """Repair a symbol without downloads, retaining originals in `_v26b_original/`.

    The histdata rebuild MUST finish first. Development days require shared per-date
    evidence. From 2021-09-14 the clock stays unchanged. Sparse weekdays (all years) are
    dropped only where histdata has a real fill; otherwise they are kept.
    Corrections crossing midnight are regrouped into UTC day files.
    Writes a dated per-day decision log, including every rejected period.
    """
    cache_dir, histdata_dir = Path(cache_dir), Path(histdata_dir)
    if not symbol.isalnum() or symbol != symbol.upper():
        raise ValueError("expected an uppercase alphanumeric symbol")
    if server_table is None:
        server_table = build_server_clock_table(cache_dir, histdata_dir, config, log=log)
    archive = cache_dir / "_v26b_original"
    stage = cache_dir / "_v26b_staged"
    with file_lock(cache_dir / "_v26b_locks" / f"{symbol}.lock"):
        active = {date.fromisoformat(p.stem): p for p in (cache_dir / symbol).glob("*/*.parquet")}
        originals = {date.fromisoformat(p.stem): p for p in (archive / symbol).glob("*/*.parquet")}
        inputs = {**active, **originals}
        counts = {day: pq.ParquetFile(path).metadata.num_rows for day, path in inputs.items()}
        # A sparse MT5 weekday of the development period is dropped only when histdata
        # really fills it; otherwise (exchange holidays, MT5-only symbols) the day stays,
        # even if empty. From 2021-09-14 FTMO's own data always stays (user, 2026-10-26).
        sparse = bad_density_days(counts, config)
        fill = histdata_fill_days(histdata_dir, symbol, config)
        excluded = {d for d in sparse & fill if d <= DEVELOPMENT_END}
        decisions, affected = [], set()
        staged_days = set()
        # A completed older staging run is overwritten from the retained original data.
        for path in (stage / symbol).glob("*/*.parquet"):
            path.unlink()
        for year in sorted({d.year for d in inputs}):
            work = {
                d: p
                for d, p in inputs.items()
                if d.year == year and (d <= DEVELOPMENT_END or d in sparse or d in originals)
            }
            if not work:
                continue
            # Backup the complete affected year before touching ANY active file.
            for day, path in work.items():
                backup = cache_path(archive, symbol, day)
                if not backup.exists():
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, backup)
            raw = read_cached_days(list(work.values()))
            by_day = dict(tuple(raw.groupby(raw["ts"].dt.date)))
            kept = []
            for day in sorted(work):
                affected.add(day)
                part = by_day.get(day, raw.iloc[:0])
                if day in excluded:
                    decision, shift = "drop: sparse/empty weekday, histdata fill", None
                elif day > DEVELOPMENT_END:
                    decision = (
                        "keep: sparse, test period (FTMO data)"
                        if day in sparse
                        else "keep: test-period clock unchanged"
                    )
                    shift = 0
                else:
                    entry = server_table.get(str(day), {"status": "no reference", "shift": None})
                    shift = entry["shift"] if entry["status"] == "proven" else None
                    if shift is None:
                        decision = f"drop: {entry['status']}"
                    elif day in sparse:
                        decision = "keep: sparse, no histdata fill"
                    else:
                        decision = "keep: server clock proven"
                decisions.append(
                    {"day": str(day), "bars": counts[day], "decision": decision, "shift": shift}
                )
                if shift is not None:
                    shifted = part.assign(ts=part.ts + pd.Timedelta(hours=shift))
                    if day <= DEVELOPMENT_END and (shifted.ts.dt.date > DEVELOPMENT_END).any():
                        raise ValueError(
                            f"{symbol} {day}: correction crosses test-period boundary; no active writes"
                        )
                    kept.append(shifted)
                    if part.empty:
                        write_atomic(part, cache_path(stage, symbol, day))
                        staged_days.add(day)
            if kept:
                corrected = pd.concat(kept, ignore_index=True)
                for day, part in corrected.groupby(corrected.ts.dt.date):
                    path = cache_path(stage, symbol, day)
                    if day in staged_days:
                        part = pd.concat([read_cached_days([path]), part], ignore_index=True)
                    part = part.drop_duplicates("ts").sort_values("ts", ignore_index=True)
                    write_atomic(part, path)
                    staged_days.add(day)
            log(f"{symbol} {year}: measured {len(work)} days")
        # All measurements and staged files are complete before active files change.
        for day in sorted(staged_days):
            frame = read_cached_days([cache_path(stage, symbol, day)])
            if day not in affected and day in active:
                frame = pd.concat([read_cached_days([active[day]]), frame], ignore_index=True)
                frame = frame.drop_duplicates("ts").sort_values("ts", ignore_index=True)
            write_atomic(frame, cache_path(cache_dir, symbol, day))
        for day in affected - staged_days:
            cache_path(cache_dir, symbol, day).unlink(missing_ok=True)
        report = cache_dir / "_v26b_reports" / f"{symbol}.json"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            json.dumps({"symbol": symbol, "config": asdict(config), "days": decisions}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        for path in (stage / symbol).glob("*/*.parquet"):
            path.unlink()
        return decisions
