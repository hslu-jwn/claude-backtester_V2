"""Offline V2.6b cache repair. Spec: ARCHITECTURE.md > Data sources.

Pre-2020 clocks are proved per UTC input day against corrected histdata. Ambiguous
days are excluded, never assigned an inferred year-wide clock. Originals are retained
outside the active cache layout; reruns always start from originals, never shift twice.
"""

import json
import shutil
import statistics
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

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
) -> list[dict]:
    """Repair a symbol without downloads, retaining originals in `_v26b_original/`.

    The histdata rebuild MUST finish first. All pre-2020 input days require independent
    per-day evidence. 2020+ clock conversion stays unchanged; density filtering applies
    to all years. Corrections crossing midnight are regrouped into UTC day files.
    Writes a dated per-day decision log, including every rejected period.
    """
    cache_dir, histdata_dir = Path(cache_dir), Path(histdata_dir)
    if not symbol.isalnum() or symbol != symbol.upper():
        raise ValueError("expected an uppercase alphanumeric symbol")
    archive = cache_dir / "_v26b_original"
    stage = cache_dir / "_v26b_staged"
    with file_lock(cache_dir / "_v26b_locks" / f"{symbol}.lock"):
        active = {date.fromisoformat(p.stem): p for p in (cache_dir / symbol).glob("*/*.parquet")}
        originals = {date.fromisoformat(p.stem): p for p in (archive / symbol).glob("*/*.parquet")}
        inputs = {**active, **originals}
        counts = {day: pq.ParquetFile(path).metadata.num_rows for day, path in inputs.items()}
        sparse = bad_density_days(counts, config)
        decisions, affected = [], set()
        staged_days = set()
        # A completed older staging run is overwritten from the retained original data.
        for path in (stage / symbol).glob("*/*.parquet"):
            path.unlink()
        for year in sorted({d.year for d in inputs}):
            work = {
                d: p
                for d, p in inputs.items()
                if d.year == year and (d.year < 2020 or d in sparse or d in originals)
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
            ref_paths = [p for p in (histdata_dir / symbol / str(year)).glob("*.parquet")]
            # Adjacent days permit proof and re-bucketing at year boundaries.
            for neighbour in (date(year, 1, 1) - timedelta(days=1), date(year + 1, 1, 1)):
                path = cache_path(histdata_dir, symbol, neighbour)
                if path.exists():
                    ref_paths.append(path)
            reference = read_cached_days(ref_paths) if year < 2020 else pd.DataFrame()
            kept = []
            for day in sorted(work):
                affected.add(day)
                part = by_day.get(day, raw.iloc[:0])
                if day in sparse:
                    decision, shift = "drop: sparse/empty weekday", None
                elif part.empty:
                    decision, shift = "keep: empty weekend", 0
                elif year >= 2020:
                    decision, shift = "keep: modern clock unchanged", 0
                else:
                    shift = proven_shift(part, reference, config)
                    decision = "drop: clock unproven" if shift is None else "keep: clock proven"
                decisions.append(
                    {"day": str(day), "bars": counts[day], "decision": decision, "shift": shift}
                )
                if shift is not None:
                    kept.append(part.assign(ts=part.ts + pd.Timedelta(hours=shift)))
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
