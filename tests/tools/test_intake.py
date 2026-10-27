"""Synthetic contract tests; canonical schemas are copied only into temporary folders."""

import builtins
import hashlib
import json
import multiprocessing
import os
import shutil
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from backtester.paths import HOME_DIR
from backtester.tools import intake

INTERFACE = HOME_DIR.parent / "Shared_Interface"
if not INTERFACE.is_dir():
    pytest.skip("Shared_Interface is unavailable", allow_module_level=True)


@pytest.fixture
def umbrella(tmp_path):
    shared = tmp_path / "Shared_Interface"
    for state in ("pending", "claimed", "completed", "rejected"):
        (shared / "queue" / state).mkdir(parents=True)
    shutil.copytree(INTERFACE / "schemas", shared / "schemas")
    (shared / "documentation").mkdir()
    shutil.copy(INTERFACE / "documentation/V2_SYMBOLS.json", shared / "documentation")
    return tmp_path


@pytest.fixture
def payload():
    return {
        "schema_version": "0.1.0",
        "strategy_id": "SYNTHETIC",
        "specification_version": "1.0.0",
        "name": "Synthetic contract fixture",
        "status": "SUBMITTED",
        "classification": "SPECULATIVE",
        "priority": 50,
        "submitted_at": "2026-10-27T12:00:00Z",
        "research": {
            "research_ids": ["SYNTHETIC"],
            "category": "Synthetic",
            "source_references": [
                {
                    "id": "fixture",
                    "citation": "Synthetic fixture",
                    "url": "https://example.invalid/fixture",
                    "source_type": "PRIMARY",
                    "supports": "Contract testing",
                }
            ],
            "evidence_summary": "Synthetic content for contract validation only.",
            "feasibility": {"rating": "GREEN", "rationale": "Synthetic fixture only"},
        },
        "market": {
            "asset_class": "index",
            "universe": ["NAS100"],
            "v2_compatibility": "SUPPORTED",
            "base_timeframe": "M1",
            "session": "cash",
            "timezone": "America/New_York",
            "directions": ["LONG"],
            "holding_period": "DAY_TRADING",
        },
        "data": {
            "required_fields": ["close"],
            "frequency": "M1",
            "minimum_history": "1 day",
            "preprocessing": [],
            "dependencies": [],
            "limitations": ["Synthetic"],
        },
        "hypothesis": {
            "behavior": "Synthetic behavior for testing",
            "mechanism": "Synthetic mechanism for testing",
            "works_when": ["fixture"],
            "fails_when": ["fixture"],
            "falsifiable_predictions": ["fixture"],
        },
        "math": {
            "definitions": [{"name": "x", "formula": "close", "timing": "close"}],
            "parameters": [
                {
                    "name": "x",
                    "type": "integer",
                    "baseline": 2,
                    "domain": {"kind": "VALUES", "values": [1, 2, 3]},
                    "tunable": True,
                }
            ],
        },
        "entries": {
            "long_condition": "fixture",
            "short_condition": None,
            "signal_time": "close",
            "execution_timing": "SIGNAL_CLOSE",
            "execution_details": "fixture",
            "order_type": "market",
            "restrictions": ["fixture"],
        },
        "exits": {
            "stop_loss": "fixture stop",
            "profit_target": None,
            "time_exit": "session",
            "signal_exit": None,
            "maximum_holding": "session",
            "end_of_session": "flat",
            "priority": ["stop_loss", "time_exit"],
        },
        "risk": {
            "accounting_type": "R_STOP_DEFINED",
            "position_sizing": "R",
            "maximum_risk_per_trade": "1R",
            "gross_exposure_limit": "fixture",
            "leverage": "fixture",
            "concurrent_positions": "1",
        },
        "experiment": {
            "baseline": "fixture",
            "stage_protocol": "V2_FIXED_DEVELOPMENT_THEN_USER_AUTHORIZED_TEST",
            "total_grid_size": 3,
            "robustness_tests": ["fixture"],
            "costs": ["V2"],
            "benchmarks": ["fixture"],
            "multiple_testing": "fixture",
            "rejection_criteria": ["fixture"],
        },
        "implementation": {
            "pseudocode": ["fixture"],
            "required_libraries": [],
            "data_structures": [],
            "edge_cases": ["fixture"],
            "computational_requirements": "tiny",
            "known_backtester_gaps": [],
        },
    }


def publish(root, payload, name=None):
    name = name or f"{payload['strategy_id']}__v{payload['specification_version']}.json"
    path = root / "Shared_Interface/queue/pending" / name
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps(payload, indent=2).encode())
    return path


def codes(path, root):
    return {issue.code for issue in intake.validate_file(path, root)[1]}


def test_claim_bytes_and_record(umbrella, payload):
    path = publish(umbrella, payload)
    raw = path.read_bytes()
    now = datetime(2026, 10, 27, 14, tzinfo=UTC)
    result = intake.claim(umbrella, umbrella / "results", "test-worker", now=now)
    assert result.path.parent.name == "claimed"
    assert result.path.read_bytes() == raw
    assert result.sha256 == hashlib.sha256(raw).hexdigest()
    assert result.payload == payload
    record = json.loads((umbrella / "results/intake" / path.stem / "claim.json").read_text())
    assert record == {
        "file": result.path.relative_to(umbrella).as_posix(),
        "strategy_id": "SYNTHETIC",
        "specification_version": "1.0.0",
        "sha256": result.sha256,
        "worker": "test-worker",
        "claimed_at": now.isoformat(),
        "issues": [asdict(issue) for issue in result.issues],
    }
    assert intake.claim(umbrella, umbrella / "results", "test-worker") is None


def test_pending_time_and_name_ties(umbrella, payload):
    paths = []
    for identity, submitted in [
        ("CCC", "2026-10-27T12:00:00Z"),
        ("BBB", "2026-10-27T11:00:00Z"),
        ("AAA", "2026-10-27T12:00:00+00:00"),
    ]:
        payload.update(strategy_id=identity, submitted_at=submitted)
        paths.append(publish(umbrella, payload))
    assert intake.pending(umbrella) == [paths[1], paths[2], paths[0]]


def test_pending_ignores_temps_and_orders(umbrella, payload):
    first = publish(umbrella, payload)
    for name in (".tmp-x.json", ".claim.lock", ".hidden", "README.md"):
        first.with_name(name).write_text("partial")
    payload.update(strategy_id="HIGH_PRIORITY", priority=90)
    high = publish(umbrella, payload)
    bad = first.with_name("BROKEN__v1.0.0.json")
    bad.write_text("{")
    assert intake.pending(umbrella) == [high, first, bad]
    assert intake.claim(umbrella, umbrella / "results", "worker").path.name == high.name


@pytest.mark.parametrize("raw", [b"{", b"[]", b"\xff"])
def test_invalid_json_not_claimed(umbrella, payload, raw):
    path = publish(umbrella, payload)
    path.write_bytes(raw)
    assert codes(path, umbrella) == {"INVALID_JSON"}
    assert intake.claim(umbrella, umbrella / "results", "worker") is None
    assert path.exists()


def test_schema_errors_have_pointers(umbrella, payload):
    pytest.importorskip("jsonschema")
    del payload["risk"]
    payload["priority"] = "bad"
    issues = intake.validate_file(publish(umbrella, payload), umbrella)[1]
    assert {issue.code for issue in issues} == {"SCHEMA_INVALID"}
    assert {issue.field for issue in issues} >= {"/risk", "/priority"}


@pytest.mark.parametrize(
    "field,value,expected",
    [
        ("strategy_id", "OTHER", "FILENAME_MISMATCH"),
        ("schema_version", "1.0.0", "UNSUPPORTED_SCHEMA_VERSION"),
        ("schema_version", "0.2.0", "UNSUPPORTED_SCHEMA_VERSION"),
        ("status", "DRAFT", "NOT_SUBMITTED"),
        ("submitted_at", None, "NOT_SUBMITTED"),
        ("submitted_at", "2026-10-27T12:00:00+01:00", "NOT_SUBMITTED"),
    ],
)
def test_identity_version_submission(umbrella, payload, field, value, expected):
    path = publish(umbrella, payload)
    payload[field] = value
    publish(umbrella, payload, path.name)
    assert expected in codes(path, umbrella)


@pytest.mark.parametrize(
    "domain,baseline,tunable",
    [
        ({"kind": "FIXED"}, 2, True),
        ({"kind": "FIXED", "values": [2]}, 2, False),
        ({"kind": "VALUES", "values": [1]}, 2, True),
        ({"kind": "VALUES", "values": [2]}, 2, False),
        ({"kind": "RANGE", "min": 1, "max": 3}, 2, True),
        ({"kind": "RANGE", "min": 1, "max": 3, "step": 0}, 2, True),
        ({"kind": "RANGE", "min": 3, "max": 1, "step": 1}, 2, True),
        ({"kind": "RANGE", "min": 1, "max": 4, "step": 2}, 1, True),
        ({"kind": "RANGE", "min": 1, "max": 5, "step": 2}, 2, True),
        ({"kind": "RANGE", "min": 1, "max": 5, "step": 2}, "bad", True),
    ],
)
def test_bad_domains(umbrella, payload, domain, baseline, tunable):
    payload["math"]["parameters"][0].update(domain=domain, baseline=baseline, tunable=tunable)
    assert "PARAMETER_DOMAIN_INVALID" in codes(publish(umbrella, payload), umbrella)


def test_grid_product_and_range_tolerance(umbrella, payload):
    payload["math"]["parameters"].append(
        {
            "name": "y",
            "type": "number",
            "baseline": 0.3,
            "domain": {"kind": "RANGE", "min": 0.1, "max": 0.3, "step": 0.1},
            "tunable": True,
        }
    )
    path = publish(umbrella, payload)
    assert "GRID_SIZE_MISMATCH" in codes(path, umbrella)
    payload["experiment"]["total_grid_size"] = 9
    publish(umbrella, payload)
    assert not codes(path, umbrella) - {"SCHEMA_NOT_CHECKED"}


@pytest.mark.parametrize(
    "section,field,value,code",
    [
        ("market", "universe", ["UNKNOWN"], "UNSUPPORTED_DATA"),
        ("market", "v2_compatibility", "UNSUPPORTED_DATA", "UNSUPPORTED_DATA"),
        ("risk", "accounting_type", "UNIT_NOTIONAL", "UNSUPPORTED_STRATEGY_TYPE"),
        ("risk", "accounting_type", "TARGET_WEIGHT", "UNSUPPORTED_STRATEGY_TYPE"),
        ("exits", "stop_loss", None, "UNSUPPORTED_STRATEGY_TYPE"),
        ("entries", "execution_timing", "NEXT_BAR_OPEN", "UNSUPPORTED_STRATEGY_TYPE"),
        ("market", "holding_period", "OVERNIGHT", "OVERNIGHT_LOW_PRIORITY"),
    ],
)
def test_capabilities_still_claimable(umbrella, payload, section, field, value, code):
    payload[section][field] = value
    publish(umbrella, payload)
    result = intake.claim(umbrella, umbrella / "results", "worker")
    issue = next(issue for issue in result.issues if issue.code == code)
    assert issue.field == f"/{section}/{field}"
    assert issue.kind == ("note" if code == "OVERNIGHT_LOW_PRIORITY" else "unsupported")


def test_unsafe_paths_and_size(umbrella, payload):
    path = publish(umbrella, payload)
    assert codes(umbrella / path.name, umbrella) == {"UNSAFE_PATH"}
    assert codes(path.parent / ".." / "pending" / path.name, umbrella) == {"UNSAFE_PATH"}
    assert codes(path.parent, umbrella) == {"UNSAFE_PATH"}
    wrong = path.rename(path.with_name("bad.json"))
    assert codes(wrong, umbrella) == {"BAD_FILENAME"}
    path.write_bytes(b" " * (1024 * 1024 + 1))
    assert codes(path, umbrella) == {"FILE_TOO_LARGE"}


def test_symlink(umbrella, payload):
    path = publish(umbrella, payload)
    link = path.with_name("LINK__v1.0.0.json")
    try:
        link.symlink_to(path)
    except OSError:
        pytest.skip("OS does not permit symlinks")
    assert codes(link, umbrella) == {"UNSAFE_PATH"}


@pytest.mark.parametrize("state", ["claimed", "completed", "rejected", "record"])
def test_duplicate_identity(umbrella, payload, state):
    path = publish(umbrella, payload)
    results = umbrella / "results"
    if state == "record":  # an earlier claim of this identity left its claim record
        (results / "intake" / path.stem).mkdir(parents=True)
        (results / "intake" / path.stem / "claim.json").write_text("{}")
    else:
        shutil.copy(path, path.parent.parent / state / path.name)
    assert "DUPLICATE_IDENTITY" in {
        issue.code for issue in intake.validate_file(path, umbrella, results=results)[1]
    }
    assert intake.claim(umbrella, results, "worker") is None


def _claim_worker(root, start, output):
    start.wait(15)
    result = intake.claim(root, root / "results", "spawn-worker")
    output.put(None if result is None else result.sha256)


def test_spawn_race(umbrella, payload):
    publish(umbrella, payload)
    context = multiprocessing.get_context("spawn")
    start, output = context.Event(), context.Queue()
    workers = [
        context.Process(target=_claim_worker, args=(umbrella, start, output)) for _ in range(2)
    ]
    try:
        for worker in workers:
            worker.start()
        start.set()
        answers = [output.get(timeout=30) for _ in workers]
        for worker in workers:
            worker.join(30)
            assert worker.exitcode == 0
        assert sum(answer is None for answer in answers) == 1
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
                worker.join()
        output.close()


@pytest.mark.parametrize(
    "age,record,expected",
    [(2, False, True), (0, False, False), (2, True, False), (1, False, False)],
)
def test_recover(umbrella, payload, age, record, expected):
    path = publish(umbrella, payload)
    claimed = path.parent.parent / "claimed" / path.name
    path.replace(claimed)
    now = datetime(2026, 10, 27, 14, tzinfo=UTC)
    stamp = (now - timedelta(hours=age)).timestamp()
    os.utime(claimed, (stamp, stamp))
    results = umbrella / "results"
    if record:
        target = results / "intake" / path.stem / "claim.json"
        target.parent.mkdir(parents=True)
        target.write_text("{}")
    assert intake.recover(umbrella, results, now=now) == ([path] if expected else [])


def test_without_jsonschema(umbrella, payload, monkeypatch):
    original = builtins.__import__

    def no_schema(name, *args, **kwargs):
        if name == "jsonschema":
            raise ImportError("not installed")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_schema)
    path = publish(umbrella, payload)
    issues = intake.validate_file(path, umbrella)[1]
    assert [(i.code, i.severity, i.kind) for i in issues] == [
        ("SCHEMA_NOT_CHECKED", "INFO", "note")
    ]
    payload["math"]["parameters"][0]["domain"] = {"kind": "RANGE", "step": 0}
    publish(umbrella, payload)
    assert "PARAMETER_DOMAIN_INVALID" in codes(path, umbrella)


@pytest.mark.parametrize("broken", [False, True])
def test_validate_cli_writes_nothing(umbrella, payload, broken):
    path = publish(umbrella, payload)
    if broken:
        path.write_text("{")
    before = {p.relative_to(umbrella): p.read_bytes() for p in umbrella.rglob("*") if p.is_file()}
    run = subprocess.run(
        [sys.executable, "-m", "backtester.tools.intake", "validate", "--root", str(umbrella)],
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert run.returncode == int(broken), run.stderr
    assert ("INVALID_JSON" if broken else "ok") in run.stdout
    after = {p.relative_to(umbrella): p.read_bytes() for p in umbrella.rglob("*") if p.is_file()}
    assert after == before


def test_a_crash_remnant_folder_without_claim_record_is_not_a_duplicate(umbrella, payload):
    path = publish(umbrella, payload)
    results = umbrella / "results"
    (results / "intake" / path.stem).mkdir(parents=True)  # crash after mkdir, before claim.json
    assert "DUPLICATE_IDENTITY" not in codes(path, umbrella)
    assert intake.claim(umbrella, results) is not None


def test_pending_order_uses_the_given_results_folder(umbrella, payload, monkeypatch):
    path = publish(umbrella, payload)
    results = umbrella / "results"
    (results / "intake" / path.stem).mkdir(parents=True)
    (results / "intake" / path.stem / "claim.json").write_text("{}")
    seen = []
    real = intake._validate

    def spy(path, root, results_dir):
        seen.append(Path(results_dir))
        return real(path, root, results_dir)

    monkeypatch.setattr(intake, "_validate", spy)
    assert intake.pending(umbrella, results=results) == [path]
    assert seen and all(r == results for r in seen)
