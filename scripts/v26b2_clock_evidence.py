"""Bounded read-only addendum audit of ORIGINAL caches; no rebuild or terminal."""

import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from time import monotonic

import pyarrow.parquet as pq

from backtester.data.cache import DEFAULT_CACHE_DIR, MT5_CACHE_DIR, cache_path, read_cached_days
from backtester.data.cache_repair import (
    DEVELOPMENT_END,
    bad_density_days,
    build_server_clock_table,
    original_inputs,
    proven_shift,
)


def main():
    started = monotonic()
    messages = []

    def log(message):
        messages.append(message)
        print(message, flush=True)

    table = build_server_clock_table(
        MT5_CACHE_DIR,
        DEFAULT_CACHE_DIR,
        original_histdata=True,
        log=log,
    )
    Path("results/v26b2_server_clock.json").write_text(
        json.dumps(table, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# MT5 shared server clock evidence (addendum A-C, 2026-10-26)",
        "",
        "Read-only measurement of original cached M1 prices, through 2021-09-13 inclusive.",
        "The old histdata 2015-2018 US/EU gap timestamps are corrected in memory using",
        "the independent FX weekly-edge evidence in clock_check_histdata.md. No cache writes.",
        "Every decisive reference has equal standing: disagreement drops the server date for ALL symbols.",
        "No reference means no decisive price match (including absent, sparse, flat or inconclusive references).",
        "Full dated readings: results/v26b2_server_clock.json. QualityConfig thresholds unchanged.",
        "",
        "|Year|Dates proven|Ambiguous|No reference|",
        "|---|---:|---:|---:|",
    ]
    for year in sorted({d[:4] for d in table}):
        counts = Counter(e["status"] for d, e in table.items() if d.startswith(year))
        lines.append(f"|{year}|{counts['proven']}|{counts['ambiguous']}|{counts['no reference']}|")
    lines += [
        "",
        "Per-symbol input days: density filtering first, then shared clock status.",
        "Test-period dates are outside this table; density filtering remains unchanged.",
        "",
        "|Symbol|Year|Kept|Dropped sparse|Dropped ambiguous|Dropped no reference|",
        "|---|---|---:|---:|---:|---:|",
    ]
    for folder in sorted(MT5_CACHE_DIR.iterdir()):
        if not folder.is_dir() or not folder.name.isalnum() or not folder.name.isupper():
            continue
        inputs = original_inputs(MT5_CACHE_DIR, folder.name)
        counts = {d: pq.ParquetFile(p).metadata.num_rows for d, p in inputs.items()}
        sparse = bad_density_days(counts)
        for year in sorted({d.year for d in inputs if d <= DEVELOPMENT_END}):
            totals = Counter(
                "sparse" if d in sparse else table[str(d)]["status"]
                for d in inputs
                if d.year == year and d <= DEVELOPMENT_END
            )
            lines.append(
                f"|{folder.name}|{year}|{totals['proven']}|{totals['sparse']}|{totals['ambiguous']}|{totals['no reference']}|"
            )
    lines += [
        "",
        "## Ambiguous dates (both/all readings retained)",
        "",
        "Residual hours to ADD to the original NY+7-converted UTC cache timestamp.",
        "",
    ]
    for day, entry in table.items():
        if entry["status"] == "ambiguous":
            lines.append(f"- {day}: {entry['readings']}")
    lines += [
        "",
        "## Test-period sample (plain NY+7 unchanged)",
        "",
        "|Date|Symbol|Residual hours|Outcome|",
        "|---|---|---:|---|",
    ]
    for day in [
        date(2021, 9, 14),
        date(2021, 11, 3),
        date(2022, 3, 16),
        date(2023, 3, 15),
        date(2023, 7, 12),
    ]:
        for symbol in ["GBPUSD", "XAUUSD", "NAS100", "US500"]:
            if monotonic() - started > 540:
                raise TimeoutError("audit exceeded 540 seconds")
            paths = [
                cache_path(DEFAULT_CACHE_DIR, symbol, day + timedelta(days=i)) for i in [-1, 0, 1]
            ]
            refs = read_cached_days([p for p in paths if p.exists()])
            inputs = original_inputs(MT5_CACHE_DIR, symbol)
            if day not in inputs:
                continue
            shift = proven_shift(read_cached_days([inputs[day]]), refs)
            outcome = (
                "supports NY+7"
                if shift == 0
                else "UNPROVEN"
                if shift is None
                else "CONTRADICTS NY+7; report only"
            )
            lines.append(f"|{day}|{symbol}|{shift}|{outcome}|")
    lines += [
        "",
        "No repair, downloads, terminal, golden check or raw-file changes performed.",
        f"Elapsed: {monotonic() - started:.2f} seconds (540-second bound).",
        "",
    ]
    Path("results/clock_check_mt5.md").write_text("\n".join(lines), encoding="utf-8")
    log(f"Complete: {len(table)} server dates; {monotonic() - started:.2f}s; no cache writes")
    Path("results/v26b2_clock_measurement.log").write_text(
        "\n".join(messages) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
