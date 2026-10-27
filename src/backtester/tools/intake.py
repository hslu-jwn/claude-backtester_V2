"""Validate and claim immutable submissions. Spec: docs/research-intake.md, Intake."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import stat
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Literal

from backtester.data.sources import SymbolSources
from backtester.filelock import atomic_json, file_lock
from backtester.paths import HOME_DIR, RESULTS_DIR

DEFAULT_UMBRELLA = HOME_DIR.parent
MAX_BYTES = 1024 * 1024
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "claim", "recover"))
    parser.add_argument("--root", type=Path, default=DEFAULT_UMBRELLA)
    parser.add_argument("--worker", default="intake")
    args = parser.parse_args(argv)
    if args.command == "validate":
        invalid = False
        for path in pending(args.root):
            _, issues = validate_file(path, args.root)
            invalid |= _invalid(issues)
            print(f"{path.name}: {', '.join(issue.code for issue in issues) or 'ok'}")
        return int(invalid)
    if args.command == "claim":
        result = claim(args.root, worker=args.worker)
        print(f"{result.path.name} {result.sha256}" if result else "nothing to claim")
    else:
        for path in recover(args.root):
            print(path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
