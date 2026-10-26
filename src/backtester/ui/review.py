"""User review data and server-side decision-time limits. Spec: V2.6 build step 5.

Labels never enter strategy settings or trading logic. Outcome data stays server-side
until reveal. The browser's review state contains only the current decision time.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from math import isfinite
from pathlib import Path
from threading import Lock

from dash import dcc, html

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
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", strategy):
        raise ValueError("Invalid strategy name")
    return Path(folder) / f"{strategy}.jsonl"


def save_label(row, folder=LABEL_DIR):
    path = _path(row["strategy"], folder)
    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, allow_nan=False) + "\n")


def load_labels(strategy, folder=LABEL_DIR):
    path = _path(strategy, folder)
    if not path.exists():
        return []
    latest = {}
    with _LOCK:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                latest[key(row)] = row
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


def history(strategy, run_hash, counts, folder=LABEL_DIR):
    """Keep the latest observed agreement for each settings hash (never settings)."""
    path = _path(strategy + "-history", folder)
    latest = {}
    with _LOCK:
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                latest[row["settings_hash"]] = row
        row = dict(settings_hash=run_hash, evaluated=utc(datetime.now(UTC)), **counts)
        if latest.get(run_hash, {}).get("total") != counts["total"] or any(
            latest.get(run_hash, {}).get(k) != v for k, v in counts.items()
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row) + "\n")
        latest[run_hash] = row
    return list(latest.values())


def agreement_text(counts):
    percent = "—" if counts["percent"] is None else f"{counts['percent']:.1f}%"
    return (
        f"Agreement {percent} · {counts['agreed']}/{counts['total']} labels · "
        f"take still exists {counts['take_exists']} · skip absent {counts['skip_absent']}"
    )


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
