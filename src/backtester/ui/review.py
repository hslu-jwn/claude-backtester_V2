"""User review data and server-side decision-time limits. Spec: V2.6 build step 5.

Labels never enter strategy settings or trading logic. Outcome data stays server-side
until reveal. The browser's review state contains only the current decision time.
"""

from __future__ import annotations

import hashlib
import json
import re
from contextlib import contextmanager
from datetime import UTC, datetime
from math import isfinite
from pathlib import Path
from threading import Lock

from dash import dcc, html

from backtester.filelock import file_lock
from backtester.paths import RESULTS_DIR

LABEL_DIR = RESULTS_DIR / "review"
_LOCK = Lock()


def utc(value):
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError("Review timestamps must include a timezone")
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def settings_hash(settings_json):
    return hashlib.sha256(
        json.dumps(json.loads(settings_json), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]


def key(row):
    return (row["strategy"], row["symbol"], utc(row["entry_time"]), row["direction"])


def label(strategy, order, run_hash, choice, reason="", own_tp=None):
    if choice not in {"take", "skip"} or len(reason or "") > 200:
        raise ValueError("Choose take or skip; reason must be at most 200 characters")
    if own_tp is not None and not isfinite(float(own_tp)):
        raise ValueError("Own TP must be finite")
    return {
        "strategy": strategy,
        "symbol": order["symbol"],
        "entry_time": utc(order["entry_time"]),
        "direction": order["direction"],
        "settings_hash": run_hash,
        "choice": choice,
        "reason": reason or "",
        "own_tp": None if own_tp is None else float(own_tp),
        "label_time": utc(datetime.now(UTC)),
    }


def _path(strategy, folder):
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", strategy):
        raise ValueError("Invalid strategy name")
    return Path(folder) / f"{strategy}.jsonl"


@contextmanager
def _locked(folder):
    # One lock also covers migration from a legacy path that may belong to another
    # strategy. The thread lock handles same-process callers on all platforms.
    with _LOCK, file_lock(Path(folder).parent / ".locks" / "review.lock"):
        yield


def _append(path, row):
    """Append one complete UTF-8 line under the caller's process lock."""
    payload = (json.dumps(row, allow_nan=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        # A crashed writer may have left a fragment. Keep it on its own line so
        # the next valid record survives and readers can warn about the fragment.
        handle.seek(0, 2)
        if handle.tell():
            handle.seek(-1, 2)
            if handle.read(1) != b"\n":
                payload = b"\n" + payload
        handle.write(payload)
        handle.flush()


def _label_key(row):
    identity = key(row)
    label(row["strategy"], row, row["settings_hash"], row["choice"], row["reason"], row["own_tp"])
    utc(row["label_time"])
    return identity


def _history_key(row):
    utc(row["evaluated"])
    for field in ("total", "take_exists", "skip_absent", "agreed"):
        if not isinstance(row[field], int) or row[field] < 0:
            raise ValueError("Invalid history count")
    if row["percent"] is not None and not 0 <= row["percent"] <= 100:
        raise ValueError("Invalid history percentage")
    if not isinstance(row["settings_hash"], str):
        raise TypeError("Invalid settings hash")
    return row["settings_hash"]


def _read(path, row_key, notices):
    latest = {}
    if path.exists():
        for number, line in enumerate(path.read_bytes().splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
                latest[row_key(row)] = row
            except (ValueError, KeyError, TypeError, AttributeError, OverflowError):
                if notices is not None:
                    notices.append(f"Warning: skipped corrupt line {number} in {path.name}")
    return latest


def save_label(row, folder=LABEL_DIR):
    path = _path(row["strategy"], folder)
    _label_key(row)
    with _locked(folder):
        _append(path, row)


def load_labels(strategy, folder=LABEL_DIR, notices=None):
    path = _path(strategy, folder)
    with _locked(folder):
        latest = _read(path, _label_key, notices)
    return list(latest.values())


def agreement(labels, strategy, orders):
    exists = {key(dict(o, strategy=strategy)) for o in orders}
    take = sum(r["choice"] == "take" and key(r) in exists for r in labels)
    skip = sum(r["choice"] == "skip" and key(r) not in exists for r in labels)
    total = len(labels)
    return {
        "total": total,
        "take_exists": take,
        "skip_absent": skip,
        "agreed": take + skip,
        "percent": 100 * (take + skip) / total if total else None,
    }


def navigate(index, action, count, labelled):
    if not count:
        return None
    if action == "unlabelled":
        return next((i for i in range(count) if i not in labelled), index)
    return max(0, min(count - 1, index + {"previous": -1, "next": 1}.get(action, 0)))


def decision_order(order, revealed):
    return dict(order) if revealed else dict(order, exit_time=None, exit=None)


def ceiling(state):
    return (
        datetime.fromisoformat(state["entry_time"])
        if state and state.get("entry_time") and not state.get("revealed")
        else None
    )


def limit_cursor(replay, cursor, state):
    at = ceiling(state)
    if at is None:
        return cursor
    limit = replay.cursor_at(at)
    return -1 if limit is None else min(cursor, limit)


def layout():
    return html.Details(
        [
            html.Summary("Review setups"),
            html.P(
                "Uses the selected chart strategy, symbol and current settings. Labels are personal review data."
            ),
            dcc.DatePickerRange(id="review-period", end_date="2021-09-13"),
            html.Button("Run review", id="review-run"),
            html.Button("Leave review", id="review-leave"),
            html.Button("Previous", id="review-previous"),
            html.Button("Next", id="review-next"),
            html.Button("First unlabelled", id="review-unlabelled"),
            html.Button("Reveal outcome", id="review-reveal"),
            html.Div(id="review-current"),
            dcc.Input(
                id="review-reason", maxLength=200, placeholder="Optional reason", type="text"
            ),
            dcc.Input(id="review-tp", placeholder="Optional own TP price", type="number"),
            html.Button("Take", id="review-take"),
            html.Button("Skip", id="review-skip"),
            html.Div(id="review-status"),
            html.Div(id="review-agreement"),
            html.Div(id="review-history"),
            dcc.Store(id="chart-review"),
        ],
        className="ui-details",
    )


def _migrate_history(strategy, folder, path):
    legacy = _path(strategy + "-history", folder)
    if not legacy.exists():
        return
    history_lines, other_lines = [], []
    for line in legacy.read_bytes().splitlines(keepends=True):
        try:
            row = json.loads(line)
        except ValueError:
            row = None
        # A strategy named '<strategy>-history' owns its labels at this path.
        if isinstance(row, dict) and "strategy" in row:
            other_lines.append(line)
        else:
            history_lines.append(line)
    if not history_lines:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if not other_lines and not path.exists():
        legacy.replace(path)
        return
    # Merge old records before newer observations; replacement is atomic. On a
    # crash before removal, a retry only duplicates old lines (last row wins).
    old = b"".join(history_lines).rstrip(b"\r\n") + b"\n"
    new = path.read_bytes() if path.exists() else b""
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes(old + new)
    temporary.replace(path)
    if other_lines:
        temporary = legacy.with_suffix(".tmp")
        temporary.write_bytes(b"".join(other_lines))
        temporary.replace(legacy)
    else:
        legacy.unlink()


def history(strategy, run_hash, counts, folder=LABEL_DIR, notices=None):
    """Latest agreement per hash; legacy history moves into its reserved folder."""
    path = _path(strategy, Path(folder) / "_history")
    with _locked(folder):
        _migrate_history(strategy, folder, path)
        latest = _read(path, _history_key, notices)
        row = dict(settings_hash=run_hash, evaluated=utc(datetime.now(UTC)), **counts)
        if any(latest.get(run_hash, {}).get(k) != v for k, v in counts.items()):
            _append(path, row)
        latest[run_hash] = row
    return list(latest.values())


def agreement_text(counts):
    percent = "\u2014" if counts["percent"] is None else f"{counts['percent']:.1f}%"
    text = (
        f"Agreement {percent} \u00b7 {counts['agreed']}/{counts['total']} labels \u00b7 "
        f"take still exists {counts['take_exists']} \u00b7 skip absent {counts['skip_absent']}"
    )
    if "labels_all" in counts:
        text += f" \u00b7 {counts['total']} of {counts['labels_all']} labels in this view"
    return text


def history_table(rows):
    return html.Table(
        [
            html.Thead(
                html.Tr([html.Th(t) for t in ["Settings hash", "Agreement at evaluation", "UTC"]])
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(r["settings_hash"]),
                            html.Td(agreement_text(r)),
                            html.Td(r["evaluated"]),
                        ]
                    )
                    for r in rows
                ]
            ),
        ]
    )
