"""Additive, resumable daily-series output. Spec: research-runner.md > Daily series."""

import csv
import os
import tempfile
from dataclasses import replace
from pathlib import Path

from backtester.analytics.daily import daily_net_r, daily_net_r_mtm, weekdays
from backtester.analytics.trial_log import append, make_record, read_all
from backtester.filelock import file_lock


def ensure(folder, start, end, sources, trials, record_args, *, trades=None, reader=None, note=""):
    """Save missing series and attach its link, preserving existing trial statistics."""
    lock_dir = trials.parent / ".locks" / "series" / folder.relative_to(trials.parent)
    with file_lock(lock_dir / "daily.csv.lock"):
        _ensure(
            folder,
            start,
            end,
            sources,
            trials,
            record_args,
            trades=trades,
            reader=reader,
            note=note,
        )


def _ensure(folder, start, end, sources, trials, record_args, *, trades, reader, note):
    path = folder / "daily.csv"
    series = path.relative_to(trials.parent).as_posix()
    # Identity has no dependence on statistics; empty trades suffice for the lookup.
    args = (*record_args[:4], start, end, record_args[4])
    candidate = make_record(*args, [], note=note)
    existing = next((r for r in read_all(trials) if r.key == candidate.key), None)
    if not path.exists():
        if trades is None:
            trades = reader(folder)
        mtm, position = daily_net_r_mtm(trades, start, end, sources)
        booked = daily_net_r(trades, start, end)
        # Replace only after a complete write; interrupted reporting must be resumable.
        temp_dir = trials.parent / ".locks" / "series" / folder.relative_to(trials.parent)
        temp_dir.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix="daily.csv.", suffix=".tmp", dir=temp_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(("date", "net_r_exit_booked", "net_r_mtm", "position"))
                writer.writerows(zip(weekdays(start, end), booked, mtm, position, strict=True))
            os.replace(name, path)
        finally:
            Path(name).unlink(missing_ok=True)
    if existing is not None:
        if existing.series != series:
            append(replace(existing, series=series), trials)
    else:
        if trades is None:
            trades = reader(folder)
        append(replace(make_record(*args, trades, note=note), series=series), trials)
