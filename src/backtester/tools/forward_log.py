"""Append-only forward paper logs for the shelf rows (research-runner.md › Verdicts and shelf, M3).

Each row is one period (`period` key, ISO date, ascending). A rerun recomputes all periods: a period already in the
file must come out identical (numbers within 1e-9), otherwise nothing is written; only later periods are appended.
"""

from __future__ import annotations

import csv
import math
from collections.abc import Sequence
from pathlib import Path


def _same(a: str, b) -> bool:
    try:
        x, y = float(a), float(b)
    except (TypeError, ValueError):
        return str(a) == str(b)
    return (math.isnan(x) and math.isnan(y)) or abs(x - y) <= 1e-9


def append(path: Path, rows: list[dict], columns: Sequence[str]) -> int:
    """Validate, then append the periods after the last logged one; returns the number appended."""
    periods = [str(r["period"]) for r in rows]
    if len(set(periods)) != len(periods):
        raise ValueError("duplicate period in the computed rows")
    if periods != sorted(periods):
        raise ValueError("computed periods are not ascending")
    old: dict[str, dict] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if tuple(reader.fieldnames or ()) != tuple(columns):
                raise ValueError(f"{path.name}: unexpected columns {reader.fieldnames}")
            old = {r["period"]: r for r in reader}
    last = max(old) if old else ""
    new = []
    for r in rows:
        p = str(r["period"])
        if p in old:
            bad = [c for c in columns if not _same(old[p][c], r[c])]
            if bad:
                raise ValueError(f"{path.name}: logged period {p} changed in {bad}")
        elif p < last:
            raise ValueError(f"{path.name}: period {p} is before the last logged {last}")
        else:
            new.append(r)
    if new:
        path.parent.mkdir(parents=True, exist_ok=True)
        fresh = not path.exists()
        with path.open("a", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(columns), extrasaction="ignore")
            if fresh:
                w.writeheader()
            w.writerows(new)
    return len(new)
