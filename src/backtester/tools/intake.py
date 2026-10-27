"""Validate and claim immutable submissions. Spec: docs/research-intake.md, Intake."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import stat
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Literal

from backtester.data.sources import SymbolSources
from backtester.filelock import atomic_json, file_lock
from backtester.paths import HOME_DIR, RESULTS_DIR

DEFAULT_UMBRELLA = HOME_DIR.parent
MAX_BYTES = 1024 * 1024
TEST_DERIVED = frozenset({"test.csv", "report.md", "bayes.json"})  # research-folder test output
FILENAME = re.compile(r"[A-Z][A-Z0-9_]{2,63}__v[0-9]+\.[0-9]+\.[0-9]+\.json")


def dataset_version(symbols, start: date, end: date, sources: SymbolSources) -> dict:
    """Fingerprint resolved day files by path and size, without reading candle contents.

    Spec: research-runner.md > Submission identity. Dates are inclusive; preferred/main/
    fallback resolution is delegated to the same cache adapter that reads the candles.
    """

    def relative(path):
        try:
            return Path(os.path.relpath(path, HOME_DIR)).as_posix()
        except ValueError:
            # Windows cannot express a relative path across volumes. Retain the volume
            # as a relative manifest label (C/cache/...), without changing file access.
            return Path(path).as_posix().replace(":", "", 1).lstrip("/")

    lines, directories = [], set()
    names = sorted(set(symbols))
    for symbol in names:
        adapter = sources.adapter(symbol)
        for day in sources.cached_days(symbol):
            if start <= day <= end:
                path = adapter._path(symbol, day)
                lines.append(f"{symbol}\t{relative(path)}\t{path.stat().st_size}")
                directories.add(relative(path.parents[2]))
    return {
        "dataset_id": "v2-cache",
        "version": hashlib.sha256("\n".join(sorted(lines)).encode("utf-8")).hexdigest(),
        "symbols": names,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "source_summary": sorted(directories),
    }


@dataclass(frozen=True)
class Issue:
    code: str
    severity: Literal["ERROR", "WARNING", "INFO"]
    message: str
    field: str | None
    kind: Literal["invalid", "unsupported", "note"]


@dataclass(frozen=True)
class Claim:
    path: Path
    sha256: str
    payload: dict
    issues: list[Issue]


def _error(code: str, message: str, field: str | None = None) -> Issue:
    return Issue(code, "ERROR", message, field, "invalid")


def _invalid(issues: list[Issue]) -> bool:
    return any(issue.kind == "invalid" and issue.severity == "ERROR" for issue in issues)


def _pointer(parts) -> str:
    return "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts)


def _queue(umbrella: Path) -> Path:
    return Path(umbrella).absolute() / "Shared_Interface" / "queue"


def _safe(path: Path, umbrella: Path) -> bool:
    """Reject traversal and symlinks in any component before touching submitted bytes."""
    try:
        if ".." in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
            return False
        return path.resolve().is_relative_to(_queue(umbrella).resolve())
    except (OSError, RuntimeError, ValueError):
        return False


def _domain_size(parameter: dict) -> int:
    """Mirror the producer's domains with a 1e-9 grid tolerance; raise on invalid input."""
    domain = parameter["domain"]
    kind, tunable, baseline = domain["kind"], parameter["tunable"], parameter["baseline"]
    if not isinstance(tunable, bool):
        raise TypeError
    if kind == "FIXED":
        if tunable or set(domain) != {"kind"}:
            raise ValueError
        return 1
    if not tunable:
        raise ValueError
    if kind == "VALUES":
        values = domain["values"]
        if (
            set(domain) != {"kind", "values"}
            or not isinstance(values, list)
            or not values
            or baseline not in values
        ):
            raise ValueError
        return len(values)
    if kind != "RANGE" or set(domain) != {"kind", "min", "max", "step"}:
        raise ValueError
    low, high, step = (domain[key] for key in ("min", "max", "step"))
    if not all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
        for v in (low, high, step, baseline)
    ):
        raise ValueError
    if step <= 0 or high < low:
        raise ValueError
    intervals, position = (high - low) / step, (baseline - low) / step
    if (
        not math.isfinite(intervals)
        or not math.isfinite(position)
        or abs(intervals - round(intervals)) > 1e-9
        or baseline < low
        or baseline > high
        or abs(position - round(position)) > 1e-9
    ):
        raise ValueError
    return round(intervals) + 1


def _semantics(payload: dict, path: Path, umbrella: Path) -> list[Issue]:
    issues = []
    identity = f"{payload.get('strategy_id')}__v{payload.get('specification_version')}.json"
    if path.name != identity:
        issues.append(_error("FILENAME_MISMATCH", "Filename must match submission identity."))
    if payload.get("status") != "SUBMITTED":
        issues.append(_error("NOT_SUBMITTED", "Queue status must be SUBMITTED.", "/status"))
    try:
        submitted = datetime.fromisoformat(payload["submitted_at"])
        if submitted.utcoffset() != timedelta(0):
            raise ValueError
    except (KeyError, AttributeError, TypeError, ValueError):
        issues.append(
            _error("NOT_SUBMITTED", "Submission requires a UTC timestamp.", "/submitted_at")
        )
    parameters = payload.get("math", {})
    parameters = parameters.get("parameters") if isinstance(parameters, dict) else None
    product = 1
    if not isinstance(parameters, list) or not parameters:
        issues.append(
            _error("PARAMETER_DOMAIN_INVALID", "Parameter list is required.", "/math/parameters")
        )
    else:
        for index, parameter in enumerate(parameters):
            try:
                product *= _domain_size(parameter)
            except (KeyError, TypeError, ValueError, OverflowError):
                issues.append(
                    _error(
                        "PARAMETER_DOMAIN_INVALID",
                        "Invalid parameter domain or baseline.",
                        f"/math/parameters/{index}",
                    )
                )
    experiment = payload.get("experiment")
    if not isinstance(experiment, dict) or experiment.get("total_grid_size") != product:
        issues.append(
            _error(
                "GRID_SIZE_MISMATCH",
                "Grid size must equal the domain product.",
                "/experiment/total_grid_size",
            )
        )

    # Missing optional schema validation must never turn malformed structures into crashes.
    def section(name):
        value = payload.get(name)
        return value if isinstance(value, dict) else {}

    market = section("market")
    symbols = json.loads(
        (Path(umbrella) / "Shared_Interface/documentation/V2_SYMBOLS.json").read_text(
            encoding="utf-8-sig"
        )
    )["symbols"]
    unsupported = []
    if market.get("v2_compatibility") != "SUPPORTED":
        unsupported.append(("UNSUPPORTED_DATA", "/market/v2_compatibility"))
    universe = market.get("universe")
    if not isinstance(universe, list) or any(symbol not in symbols for symbol in universe):
        unsupported.append(("UNSUPPORTED_DATA", "/market/universe"))
    if section("risk").get("accounting_type") != "R_STOP_DEFINED":
        unsupported.append(("UNSUPPORTED_STRATEGY_TYPE", "/risk/accounting_type"))
    if section("exits").get("stop_loss") is None:
        unsupported.append(("UNSUPPORTED_STRATEGY_TYPE", "/exits/stop_loss"))
    if section("entries").get("execution_timing") == "NEXT_BAR_OPEN":
        unsupported.append(("UNSUPPORTED_STRATEGY_TYPE", "/entries/execution_timing"))
    for code, field in unsupported:
        issues.append(
            Issue(code, "ERROR", "Requirement is unsupported by V2.", field, "unsupported")
        )
    if market.get("holding_period") == "OVERNIGHT":
        issues.append(
            Issue(
                "OVERNIGHT_LOW_PRIORITY",
                "WARNING",
                "Overnight submissions have low priority.",
                "/market/holding_period",
                "note",
            )
        )
    return issues


def _validate(path: Path, umbrella: Path, results: Path) -> tuple[dict | None, list[Issue], bytes]:
    path = Path(path)

    def fail(code, message):
        return None, [_error(code, message)], b""

    if not _safe(path, umbrella):
        return fail("UNSAFE_PATH", "Submission must be a regular queue file without symlinks.")
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode):
            return fail("UNSAFE_PATH", "Submission must be a regular queue file.")
        if info.st_size > MAX_BYTES:
            return fail("FILE_TOO_LARGE", "Submission exceeds 1 MiB.")
        if not FILENAME.fullmatch(path.name):
            return fail("BAD_FILENAME", "Filename does not follow the submission convention.")
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return fail("FILE_TOO_LARGE", "Submission exceeds 1 MiB.")
    except OSError:
        return fail("UNSAFE_PATH", "Submission is not an accessible regular queue file.")
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
        if not isinstance(payload, dict):
            raise TypeError
    except (UnicodeError, ValueError, TypeError, RecursionError):
        return fail("INVALID_JSON", "Submission must be a UTF-8 JSON object.")
    version = payload.get("schema_version")
    if not isinstance(version, str) or not re.fullmatch(r"0\.1\.[0-9]+", version):
        return (
            payload,
            [
                _error(
                    "UNSUPPORTED_SCHEMA_VERSION", "Schema version must be 0.1.x.", "/schema_version"
                )
            ],
            raw,
        )
    issues = []
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        issues.append(
            Issue(
                "SCHEMA_NOT_CHECKED",
                "INFO",
                "Install the intake extra for schema checks.",
                None,
                "note",
            )
        )
    else:
        schema = json.loads(
            (Path(umbrella) / "Shared_Interface/schemas/strategy.schema.json").read_text(
                encoding="utf-8-sig"
            )
        )
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for error in validator.iter_errors(payload):
            parts = list(error.absolute_path)
            if error.validator == "required":
                # Attribute missing fields to their JSON Pointer rather than their parent object.
                missing = [key for key in error.validator_value if key not in error.instance]
                key = next((k for k in missing if error.message.startswith(repr(k))), None)
                if key is not None:
                    parts.append(key)
            issues.append(
                _error(
                    "SCHEMA_INVALID",
                    "Submission does not conform to the strategy schema.",
                    _pointer(parts),
                )
            )
        if issues:
            return payload, issues, raw
    issues.extend(_semantics(payload, path, umbrella))
    queue = _queue(umbrella)
    if (
        any((queue / state / path.name).exists() for state in ("claimed", "completed", "rejected"))
        or (Path(results) / "intake" / path.stem / "claim.json").exists()
    ):
        issues.append(_error("DUPLICATE_IDENTITY", "Submission identity already exists."))
    return payload, issues, raw


def validate_file(
    path: Path, umbrella: Path = DEFAULT_UMBRELLA, *, results: Path = RESULTS_DIR
) -> tuple[dict | None, list[Issue]]:
    """Read-only validation in contract order; capability errors remain distinguishable."""
    payload, issues, _ = _validate(path, umbrella, results)
    return payload, issues


def pending(umbrella: Path = DEFAULT_UMBRELLA, *, results: Path = RESULTS_DIR) -> list[Path]:
    """List valid submissions by priority, UTC submission time, then filename."""
    folder = _queue(umbrella) / "pending"
    if not folder.is_dir() or not _safe(folder, umbrella):
        return []

    def order(path):
        payload, issues, _ = _validate(path, umbrella, results)
        if payload is None or _invalid(issues):
            return (1, 0, 0, path.name)
        priority = payload.get("priority")
        if not isinstance(priority, int) or isinstance(priority, bool):
            return (1, 0, 0, path.name)
        stamp = datetime.fromisoformat(payload["submitted_at"])
        return (0, -priority, stamp.timestamp(), path.name)

    return sorted(
        (p for p in folder.iterdir() if not p.name.startswith(".") and p.name != "README.md"),
        key=order,
    )


def _check_mutation_paths(umbrella: Path) -> Path:
    queue = _queue(umbrella)
    if not all(
        _safe(queue / part, umbrella)
        for part in (".claim.lock", "pending", "claimed", "completed", "rejected")
    ):
        raise ValueError("Unsafe queue path.")
    return queue


def claim(
    umbrella: Path = DEFAULT_UMBRELLA,
    results: Path = RESULTS_DIR,
    worker: str = "intake",
    now: datetime | None = None,
) -> Claim | None:
    """Claim once under the shared OS lock, retaining the exact validated bytes."""
    queue = _check_mutation_paths(umbrella)
    with file_lock(queue / ".claim.lock"):
        for path in pending(umbrella, results=results):
            payload, issues, raw = _validate(path, umbrella, results)
            if payload is None or _invalid(issues):
                continue
            target = queue / "claimed" / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(path, target)
            digest = hashlib.sha256(raw).hexdigest()
            record = {
                "file": target.relative_to(Path(umbrella).absolute()).as_posix(),
                "strategy_id": payload["strategy_id"],
                "specification_version": payload["specification_version"],
                "sha256": digest,
                "worker": worker,
                "claimed_at": (now or datetime.now(UTC)).astimezone(UTC).isoformat(),
                "issues": [asdict(issue) for issue in issues],
            }
            atomic_json(Path(results) / "intake" / path.stem / "claim.json", record)
            return Claim(target, digest, payload, issues)
    return None


def recover(
    umbrella: Path = DEFAULT_UMBRELLA,
    results: Path = RESULTS_DIR,
    now: datetime | None = None,
    max_age: timedelta = timedelta(hours=1),
) -> list[Path]:
    """Return stale orphaned claims to pending under the same shared lock."""
    queue = _check_mutation_paths(umbrella)
    recovered = []
    cutoff = ((now or datetime.now(UTC)) - max_age).timestamp()
    with file_lock(queue / ".claim.lock"):
        folder = queue / "claimed"
        if not folder.is_dir():
            return []
        for path in sorted(folder.iterdir()):
            if path.name.startswith(".") or not FILENAME.fullmatch(path.name):
                continue
            if not _safe(path, umbrella) or not path.is_file():
                continue
            target = queue / "pending" / path.name
            record = Path(results) / "intake" / path.stem / "claim.json"
            if not record.exists() and path.stat().st_mtime < cutoff and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(path, target)
                recovered.append(target)
    return recovered


def _contained(path: Path, umbrella: Path) -> Path:
    """Resolve envelope/artifact paths within the umbrella, including symlink targets."""
    root = Path(umbrella).resolve()
    path = Path(path)
    path = path if path.is_absolute() else root / path
    if ".." in path.parts or not path.resolve().is_relative_to(root):
        raise ValueError("Path must resolve inside the umbrella.")
    return path.resolve()


def _relative(path: Path, umbrella: Path) -> str:
    return _contained(path, umbrella).relative_to(Path(umbrella).resolve()).as_posix()


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _validate_envelope(umbrella: Path, kind: str, envelope: dict) -> None:
    # JSON itself must also be portable: Python's NaN/Infinity extensions are forbidden.
    json.dumps(envelope, allow_nan=False)
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        return
    schema = _contained(Path("Shared_Interface/schemas") / f"{kind}.schema.json", umbrella)
    Draft202012Validator(_read(schema), format_checker=FormatChecker()).validate(envelope)


def _publish(path: Path, envelope: dict, umbrella: Path) -> Path:
    path = _contained(path, umbrella)
    with file_lock(_contained(path.parent / ".envelope.lock", umbrella)):
        if path.exists():
            raise FileExistsError("Envelope already exists.")
        atomic_json(path, envelope)
    return path


def _feedback_id(strategy_id: str | None) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"FB_{strategy_id or 'UNKNOWN'}_{stamp}_{uuid.uuid4().hex[:4]}"


def emit_feedback(
    umbrella,
    *,
    status,
    issues,
    subject_file,
    claim=None,
    payload=None,
    sha256=None,
    scope="SUBMISSION",
    in_reply_to=None,
    related_experiment_id=None,
) -> Path:
    """Publish immutable feedback. Spec: research-intake.md > Pipeline, steps 1–3."""
    payload = claim.payload if claim is not None else payload
    payload = payload if isinstance(payload, dict) else {}
    strategy_id, version = payload.get("strategy_id"), payload.get("specification_version")
    if not isinstance(strategy_id, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", strategy_id):
        strategy_id = None
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        version = None
    feedback_id = _feedback_id(strategy_id)
    envelope = {
        "schema_version": "0.1.0",
        "feedback_id": feedback_id,
        "scope": scope,
        "subject_file": _relative(subject_file, umbrella),
        "strategy_id": strategy_id,
        "specification_version": version,
        "submission_sha256": claim.sha256 if claim is not None else sha256,
        "status": status,
        "issues": [
            {
                "code": i.code,
                "severity": i.severity,
                "message": i.message,
                "field": i.field,
                "requires_revision": i.kind in ("invalid", "unsupported"),
            }
            for i in issues
        ],
        "created_at": datetime.now(UTC).isoformat(),
        "producer": "V2 backtester team",
        "in_reply_to": in_reply_to,
        "related_experiment_id": related_experiment_id,
    }
    _validate_envelope(umbrella, "feedback", envelope)
    return _publish(
        Path("Shared_Interface/feedback/messages") / f"{feedback_id}.json", envelope, umbrella
    )


def _terminal_target(queue: Path, name: str, outcome: str) -> Path:
    target = queue / outcome / name
    n = 0
    while target.exists() or target.is_symlink():
        n += 1
        target = queue / outcome / f"{Path(name).stem}.dup-{n}.json"
    return target


def reject_invalid(umbrella, results) -> list[Path]:
    """Quarantine invalid pending bytes, retaining originals and one feedback per file."""
    queue = _check_mutation_paths(umbrella)
    _contained(results, umbrella)
    outputs = []
    with file_lock(queue / ".claim.lock"):
        for path in pending(umbrella, results=results):
            payload, issues, _ = _validate(path, umbrella, results)
            if not _invalid(issues):
                continue
            if not path.is_file() or not _safe(path, umbrella):
                # Never follow unsafe paths to obtain a hash; a symlink itself can be moved.
                if not path.is_symlink():
                    raise ValueError("Unsafe pending path cannot be quarantined as a file.")
                digest = None
            else:
                digest = _digest(path)
            target = _terminal_target(queue, path.name, "rejected")
            out = emit_feedback(
                umbrella,
                status="REJECTED",
                issues=issues,
                subject_file=target,
                payload=payload,
                sha256=digest,
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(path, target)
            outputs.append(out)
    return outputs


def finish(umbrella, results, claim, outcome):
    """Move original bytes to terminal ownership under the claim lock; never delete them."""
    if outcome not in ("completed", "rejected"):
        raise ValueError("Invalid terminal outcome.")
    queue = _check_mutation_paths(umbrella)
    path = _contained(claim.path, umbrella)
    record_path = _contained(Path(results) / "intake" / path.stem / "claim.json", umbrella)
    with file_lock(queue / ".claim.lock"):
        if path.parent != (queue / "claimed").resolve() or _digest(path) != claim.sha256:
            raise ValueError("Claim path or submission hash mismatch.")
        record = _read(record_path)
        if record.get("sha256") != claim.sha256 or record.get("outcome") is not None:
            raise ValueError("Claim record mismatch or already finished.")
        target = _terminal_target(queue, path.name, outcome)
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(path, target)
        record.update(
            finished_at=datetime.now(UTC).isoformat(),
            outcome=outcome,
            file=_relative(target, umbrella),
        )
        atomic_json(record_path, record)


def reject_unsupported(umbrella, results, claim) -> Path:
    issues = [i for i in claim.issues if i.kind == "unsupported" and i.severity == "ERROR"]
    if not issues:
        raise ValueError("Claim has no unsupported error.")
    status = (
        "UNSUPPORTED_DATA"
        if any(i.code == "UNSUPPORTED_DATA" for i in issues)
        else "UNSUPPORTED_STRATEGY_TYPE"
    )
    out = emit_feedback(
        umbrella, status=status, issues=claim.issues, subject_file=claim.path, claim=claim
    )
    finish(umbrella, results, claim, "rejected")
    return out


def progress(umbrella, claim, status) -> Path:
    if status not in ("CLAIMED", "IMPLEMENTING", "TESTING"):
        raise ValueError("Invalid progress status.")
    return emit_feedback(
        umbrella,
        status=status,
        subject_file=claim.path,
        claim=claim,
        issues=[Issue("PROGRESS", "INFO", status, None, "note")],
    )


def _experiment_directory(results, stem):
    if not FILENAME.fullmatch(stem + ".json"):
        raise ValueError("Invalid submission stem.")
    return Path(results) / "intake" / stem / "experiments"


def next_experiment_id(results, stem, stage) -> str:
    if stage not in ("DEVELOPMENT", "FINAL_HOLDOUT"):
        raise ValueError("Invalid evaluation stage.")
    folder = _experiment_directory(results, stem)
    prefix = f"{stem}__{stage}__"
    numbers = [
        int(p.stem[len(prefix) :])
        for p in folder.glob(prefix + "*.json")
        if re.fullmatch(re.escape(prefix) + r"[1-9][0-9]*", p.stem)
    ]
    return prefix + str(max(numbers, default=0) + 1)


def _run_artifacts(folder, umbrella):
    """Hash individual files rather than inventing a hash for a directory."""
    _contained(folder, umbrella)
    return [
        {"kind": p.name, "path": _relative(p, umbrella), "sha256": _digest(_contained(p, umbrella))}
        for p in sorted(folder.rglob("*"))
        if p.is_file() and not p.name.startswith(".")
    ]


def emit_result(
    umbrella,
    results,
    claim,
    *,
    experiment_id,
    stage,
    research_folder,
    requested_costs,
    warnings=(),
    errors=(),
    status="COMPLETED",
    holdout_disclosure=None,
) -> Path:
    """Export recorded evidence only. Spec: research-intake.md > Result metric mapping."""
    from types import SimpleNamespace

    from backtester.analytics.trial_log import read_all
    from backtester.tools.research import _test_authorized

    results = _contained(results, umbrella)
    folder = _contained(research_folder, umbrella)
    stem = claim.path.stem
    if stage not in ("DEVELOPMENT", "FINAL_HOLDOUT") or not re.fullmatch(
        re.escape(f"{stem}__{stage}__") + r"[1-9][0-9]*", experiment_id
    ):
        raise ValueError("Invalid experiment identity or stage.")
    info = _read(_contained(folder / "info.json", umbrella))
    identity = info["submission"]
    for key, value in (
        ("strategy_id", claim.payload["strategy_id"]),
        ("specification_version", claim.payload["specification_version"]),
        ("submission_sha256", claim.sha256),
    ):
        if identity.get(key) != value:
            raise ValueError("Research submission identity mismatch.")
    if stage == "FINAL_HOLDOUT":
        _contained(results / "intake" / stem / "test_authorization.json", umbrella)
        if not _test_authorized(SimpleNamespace(submission=identity), results):
            raise ValueError("Final holdout requires user authorization.")
    disclosure = holdout_disclosure or ("NONE" if stage == "DEVELOPMENT" else "REDACTED")
    if disclosure not in (("NONE",) if stage == "DEVELOPMENT" else ("REDACTED", "FULL")):
        raise ValueError("Invalid holdout disclosure.")
    chosen = info.get("chosen")
    if chosen is None:
        with _contained(folder / "variants.csv", umbrella).open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        ranked = [r for r in rows if r.get("rank")]
        if not ranked:
            raise ValueError("Research folder has no chosen or ranked development variant.")
        chosen = {"id": min(ranked, key=lambda r: int(r["rank"]))["variant_id"]}
    variant = _contained(folder / "variants" / chosen["id"], umbrella)
    linked = []
    if chosen.get("dev_run"):
        linked.append(_contained(results / chosen["dev_run"], umbrella))
    run = variant
    if stage == "FINAL_HOLDOUT":
        run = _contained(results / info["test"]["run_folder"], umbrella)
        linked.append(run)
    run_info = _read(_contained(run / "info.json", umbrella))
    expected = identity | ({"experiment_id": experiment_id} if stage == "FINAL_HOLDOUT" else {})
    if run_info["submission"] != expected:
        raise ValueError("Run submission identity mismatch.")
    if stage == "DEVELOPMENT" and identity["experiment_id"] != experiment_id:
        raise ValueError("Development experiment identity mismatch.")
    summary = _read(_contained(run / "summary.json", umbrella))["combined"]
    settings = _read(_contained(run / "settings.json", umbrella))
    card_path = _contained(variant / "scorecard.json", umbrella)
    card = _read(card_path) if card_path.exists() else {}
    mapping = {
        "net_r": "net_r_net",
        "max_drawdown_r": "max_drawdown_r_net",
        "average_win_r": "avg_win_r",
        "average_loss_r": "avg_loss_r",
        "expectancy_r": "expectancy_r",
        "profit_factor": "profit_factor",
        "trades": "trades",
        "win_rate": "win_rate",
    }
    metric_keys = (
        "net_r",
        "max_drawdown_r",
        "expectancy_r",
        "sharpe_daily_r",
        "sortino_daily_r",
        "net_return_pct",
        "max_drawdown_pct",
        "expectancy_pct",
        "profit_factor",
        "trades",
        "win_rate",
        "average_win_r",
        "average_loss_r",
        "exposure_pct",
        "turnover_pct",
    )
    metrics = dict.fromkeys(metric_keys)
    metrics.update({key: summary.get(source) for key, source in mapping.items()})
    # day_sharpe is the stored daily R Sharpe; never substitute a per-trade statistic.
    metrics["sharpe_daily_r"] = card.get("day_sharpe") if stage == "DEVELOPMENT" else None
    diagnostics = {}
    significance = _contained(folder / "significance.json", umbrella)
    if significance.exists():
        diagnostics.update(_read(significance))
    for key in ("deflated_sharpe", "psr", "dsr", "flags"):
        if key in info.get("test", {}) and stage == "FINAL_HOLDOUT":
            diagnostics[key] = info["test"][key]
        if key in card.get("scorecard", {}):
            diagnostics[key] = card["scorecard"][key]
    robustness = {
        k: info[k]
        for k in (
            "grid_robustness",
            "sensitivity",
            "monkeys",
            "twins",
            "shocks",
            "bayes",
            "walk_forward",
            "drawdown_bounds",
        )
        if k in info
    }
    if stage == "DEVELOPMENT":  # never carry test-period evidence (contract: holdout control)
        if "drawdown_bounds" in robustness:
            bounds = robustness["drawdown_bounds"]
            robustness["drawdown_bounds"] = {k: v for k, v in bounds.items() if k == "development"}
        if isinstance(robustness.get("bayes"), dict):
            robustness["bayes"] = {**robustness["bayes"], "tests": []}
    trials = []
    for trial in read_all(results / "trials.jsonl"):
        if trial.series:
            series = _contained(results / trial.series, umbrella)
            if series.is_relative_to(folder):
                trials.append(trial)
    count = sum(t.count for t in trials)
    if count < 1:
        raise ValueError("Research folder has no recorded trials.")
    artifacts = _run_artifacts(folder, umbrella)
    if stage == "DEVELOPMENT":  # files that hold test results
        artifacts = [a for a in artifacts if a["kind"] not in TEST_DERIVED]
    for target in linked:
        artifacts.extend(_run_artifacts(target, umbrella))
    artifacts = list({a["path"]: a for a in artifacts}.values())
    configuration = dict(settings["run"])
    if "cache_dirs" in configuration:
        configuration["cache_dirs"] = {
            s: _relative(Path(p), umbrella) for s, p in configuration["cache_dirs"].items()
        }
    dataset = dict(run_info["dataset"])
    if isinstance(dataset["source_summary"], list):
        dataset["source_summary"] = "; ".join(dataset["source_summary"])
    redacted = disclosure == "REDACTED"
    envelope = {
        "schema_version": "0.1.0",
        "strategy_id": claim.payload["strategy_id"],
        "specification_version": claim.payload["specification_version"],
        "submission_sha256": claim.sha256,
        "experiment_id": experiment_id,
        "implementation_version": str(info.get("version", 1)),
        "code_commit": run_info.get("code_commit", info.get("code_commit")),
        "accounting_type": "R_STOP_DEFINED",
        "dataset": dataset,
        "evaluation_stage": stage,
        "stage_split": {
            "protocol": "V2_FIXED_DEVELOPMENT_THEN_USER_AUTHORIZED_TEST",
            "cutoff": "2021-09-14",
            "test_requires_user_authorization": True,
        },
        "status": status,
        "test_configuration": configuration,
        "parameters": settings["strategy"],
        "execution": settings["engine"],
        "requested_costs": requested_costs,
        "resolved_cost_model": settings["engine"]["costs"],
        "metrics": dict.fromkeys(metric_keys) if redacted else metrics,
        "statistical_diagnostics": {} if redacted else diagnostics,
        "robustness": {} if redacted else robustness,
        "variants_tried": count,
        "artifacts": [] if redacted else artifacts,
        "warnings": list(warnings),
        "errors": list(errors),
        "created_at": datetime.now(UTC).isoformat(),
        "holdout_disclosure": disclosure,
    }
    _validate_envelope(umbrella, "result", envelope)
    target = _contained(
        Path("Shared_Interface/feedback/results") / f"{experiment_id}.json", umbrella
    )
    record = _contained(_experiment_directory(results, stem) / f"{experiment_id}.json", umbrella)
    with file_lock(_contained(record.parent / ".experiments.lock", umbrella)):
        if record.exists() or target.exists():
            raise FileExistsError("Experiment envelope already exists.")
        # Reserve the ID durably before publication so a crash can never reuse it.
        atomic_json(record, {"envelope": envelope, "path": _relative(target, umbrella)})
        return _publish(target, envelope, umbrella)


def _load_claim(umbrella, results, stem):
    _experiment_directory(results, stem)
    record = _read(_contained(Path(results) / "intake" / stem / "claim.json", umbrella))
    path = _contained(Path(umbrella) / record["file"], umbrella)
    if path.stem != stem or _digest(path) != record["sha256"]:
        raise ValueError("Claim hash or identity mismatch.")
    return Claim(path, record["sha256"], _read(path), [Issue(**i) for i in record["issues"]])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("validate", "claim", "recover", "reject", "progress", "finish", "result"),
    )
    parser.add_argument("stem", nargs="?")
    parser.add_argument("status", nargs="?")
    parser.add_argument("--root", type=Path, default=DEFAULT_UMBRELLA)
    parser.add_argument("--worker", default="intake")
    parser.add_argument("--research-folder", type=Path)
    parser.add_argument("--stage", choices=("DEVELOPMENT", "FINAL_HOLDOUT"), default="DEVELOPMENT")
    parser.add_argument("--requested-costs", default="{}")
    args = parser.parse_args(argv)
    results = args.root / HOME_DIR.name / "results"
    if args.command in ("progress", "finish", "result"):
        if not args.stem:
            parser.error("submission stem is required")
        current = _load_claim(args.root, results, args.stem)
        if args.command == "progress":
            print(progress(args.root, current, args.status))
        elif args.command == "finish":
            finish(args.root, results, current, args.status)
        else:
            if args.research_folder is None:
                parser.error("--research-folder is required")
            print(
                emit_result(
                    args.root,
                    results,
                    current,
                    experiment_id=next_experiment_id(results, args.stem, args.stage),
                    stage=args.stage,
                    research_folder=args.research_folder,
                    requested_costs=json.loads(args.requested_costs),
                )
            )
        return 0
    if args.command == "reject":
        for path in reject_invalid(args.root, results):
            print(path)
        return 0
    if args.command == "validate":
        invalid = False
        for path in pending(args.root, results=results):
            _, issues = validate_file(path, args.root, results=results)
            invalid |= _invalid(issues)
            print(f"{path.name}: {', '.join(issue.code for issue in issues) or 'ok'}")
        return int(invalid)
    if args.command == "claim":
        result = claim(args.root, results, worker=args.worker)
        print(f"{result.path.name} {result.sha256}" if result else "nothing to claim")
    else:
        for path in recover(args.root, results):
            print(path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
