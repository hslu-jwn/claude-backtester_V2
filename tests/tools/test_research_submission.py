"""Submission identity and explicit holdout authorization (research-intake.md)."""

import hashlib
import json
import os
from dataclasses import asdict, replace
from datetime import date

import pytest

from backtester.analytics import trial_log
from backtester.data.cache import cache_path
from backtester.data.sources import SymbolSources
from backtester.tools import intake, research
from backtester.tools.research_grid import GridError, expand, grid_id, load_grid
from tests.tools import test_research as helpers
from tests.tools.test_research import GRID, run_research, write_grid

fakes = helpers.fakes


@pytest.fixture(autouse=True)
def temporary_sources(tmp_path, monkeypatch):
    # Metadata must never inspect the real cache in runner tests.
    real = research.dataset_version
    sources = SymbolSources.single(tmp_path / "cache", ["US500", "NAS100"])
    monkeypatch.setattr(
        research, "dataset_version", lambda symbols, a, b, _: real(symbols, a, b, sources)
    )


IDENTITY = {
    "strategy_id": "US500_FINAL30_CONT",
    "specification_version": "0.2.0",
    "submission_sha256": "a" * 64,
    "experiment_id": "US500_FINAL30_CONT__v0.2.0__DEVELOPMENT__1",
}
STEM = "US500_FINAL30_CONT__v0.2.0"


def submission_grid(identity=None):
    table = IDENTITY if identity is None else identity
    return (
        GRID
        + "\n[submission]\n"
        + "\n".join(f"{key} = {json.dumps(value)}" for key, value in table.items())
    )


def authorize(tmp_path, **overrides):
    path = tmp_path / "results" / "intake" / STEM / "test_authorization.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "authorized_by": "user",
                "quote": "Run the one-time test.",
                "authorized_at": "2026-10-28T12:00:00+00:00",
                "experiment_id": IDENTITY["experiment_id"],
                **overrides,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_grid_submission_optional_and_valid(tmp_path):
    assert load_grid(write_grid(tmp_path)).submission is None
    assert load_grid(write_grid(tmp_path, submission_grid())).submission == IDENTITY


def test_submission_writes_criteria_inputs(tmp_path, fakes):
    out = run_research(tmp_path, submission_grid(), dev_only=True)
    data = json.loads((out["folder"] / "criteria_inputs.json").read_text())
    assert {
        "variants_positive_net",
        "variants",
        "net_r",
        "gross_r",
        "gross_by_symbol",
        "symbols_positive_gross",
        "net_r_costs_x2",
        "costs_x2_factor",
        "net_r_costs_stress",
        "costs_stress_factor",
        "half_first_net_r",
        "half_second_net_r",
        "net_r_without_best_days",
        "stop_share",
        "trade_tags",
    } <= data.keys()


@pytest.mark.parametrize(
    "key,value",
    [
        ("strategy_id", "ab"),
        ("strategy_id", "aBC"),
        ("strategy_id", "A" * 65),
        ("strategy_id", 123),
        ("specification_version", "0.2"),
        ("specification_version", "v0.2.0"),
        ("specification_version", 2),
        ("submission_sha256", "A" * 64),
        ("submission_sha256", "a" * 63),
        ("submission_sha256", 123),
        ("experiment_id", "other"),
        ("experiment_id", STEM + "__DEVELOPMENT__0"),
        ("experiment_id", STEM + "__FINAL_HOLDOUT__1"),
        ("experiment_id", STEM + "__DEVELOPMENT__1\n"),
        ("experiment_id", 1),
        ("extra", "unexpected"),
    ],
)
def test_bad_submission_names_key(tmp_path, key, value):
    with pytest.raises(GridError, match=key):
        load_grid(write_grid(tmp_path, submission_grid(IDENTITY | {key: value})))


@pytest.mark.parametrize("key", list(IDENTITY))
def test_missing_submission_key(tmp_path, key):
    with pytest.raises(GridError, match=key):
        load_grid(
            write_grid(tmp_path, submission_grid({k: v for k, v in IDENTITY.items() if k != key}))
        )


def test_submission_must_be_table(tmp_path):
    with pytest.raises(GridError, match="submission"):
        load_grid(write_grid(tmp_path, 'submission = "wrong"\n' + GRID))


def test_submission_identity_separates_resume_and_test_state(tmp_path):
    legacy = load_grid(write_grid(tmp_path))
    submitted = load_grid(write_grid(tmp_path, submission_grid()))
    revised = load_grid(
        write_grid(
            tmp_path,
            submission_grid(
                IDENTITY
                | {
                    "submission_sha256": "b" * 64,
                }
            ),
        )
    )
    assert len({grid_id(spec, expand(spec)[0]) for spec in (legacy, submitted, revised)}) == 3


def test_trial_bytes_unchanged_and_identity_not_in_key(tmp_path):
    record = trial_log.TrialRecord(
        "idea", "opening_range", {}, ["US500"], "2015-01-01", "2021-09-13", "research", "fixed"
    )
    legacy = asdict(record)
    legacy.pop("submission", None)
    path = tmp_path / "trials.jsonl"
    trial_log.append(record, path)
    assert path.read_text() == json.dumps(legacy, sort_keys=True) + "\n"
    tagged = replace(record, submission=IDENTITY)
    assert tagged.key == record.key
    trial_log.append(tagged, path)
    assert json.loads(path.read_text().splitlines()[-1])["submission"] == IDENTITY
    assert trial_log.read_all(path)[0].submission == IDENTITY


def test_dataset_fingerprint_resolves_preferred_files_and_filters_symbols(tmp_path, monkeypatch):
    monkeypatch.setattr(intake, "HOME_DIR", tmp_path)
    main, preferred = tmp_path / "data/cache/histdata", tmp_path / "data/cache/mt5"
    day = date(2020, 1, 2)
    for folder, symbol, content in [
        (main, "US500", b"shadowed"),
        (preferred, "US500", b"selected"),
        (main, "NAS100", b"irrelevant"),
    ]:
        path = cache_path(folder, symbol, day)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    sources = SymbolSources({"US500": main, "NAS100": main}, {"US500": preferred})
    version = intake.dataset_version(["US500"], day, day, sources)
    line = "US500\tdata/cache/mt5/US500/2020/2020-01-02.parquet\t8"
    assert version == {
        "dataset_id": "v2-cache",
        "version": hashlib.sha256(line.encode()).hexdigest(),
        "symbols": ["US500"],
        "start": str(day),
        "end": str(day),
        "source_summary": ["data/cache/mt5"],
    }
    assert version == intake.dataset_version(["US500", "US500"], day, day, sources)
    cache_path(main, "US500", day).write_bytes(b"ignored size change")
    assert version == intake.dataset_version(["US500"], day, day, sources)
    cache_path(preferred, "US500", day).write_bytes(b"changed size")
    assert version["version"] != intake.dataset_version(["US500"], day, day, sources)["version"]
    assert (
        intake.dataset_version(["US500"], date(2020, 1, 3), date(2020, 1, 3), sources)["version"]
        == hashlib.sha256(b"").hexdigest()
    )


@pytest.mark.parametrize(
    "authorization",
    [
        None,
        {"authorized_by": "opus"},
        {"quote": ""},
        {"quote": "   "},
        {"experiment_id": "other"},
        {"authorized_at": "bad"},
        {"authorized_at": None},
    ],
)
@pytest.mark.parametrize("retest", [False, True])
def test_unauthorized_submission_develops_only(tmp_path, fakes, authorization, retest):
    if authorization is not None:
        authorize(tmp_path, **authorization)
    messages = []
    out = run_research(tmp_path, submission_grid(), retest=retest, log=messages.append)
    assert len(fakes.calls) == 6
    assert out["test"]["status"] == "not_run"
    assert out["test"]["run"] == 0
    expected = f"test skipped: no user authorization for {STEM}"
    assert messages.count(expected) == 1
    assert expected in (out["folder"] / "report.md").read_text()
    lines = trial_log.read_all(tmp_path / "results/trials.jsonl")
    assert len(lines) == 6
    assert all(row.source == "research" and row.submission == IDENTITY for row in lines)
    info = json.loads((out["folder"] / "research.json").read_text())
    assert info["submission"] == IDENTITY
    assert info["dataset"]["symbols"] == ["NAS100", "US500"]
    assert "code_commit" in info and "code_dirty" in info


def test_authorized_test_and_retest_identity(tmp_path, fakes):
    authorization = authorize(tmp_path)
    before = authorization.read_bytes()
    out = run_research(tmp_path, submission_grid())
    assert len(fakes.calls) == 7 and out["test"]["status"] == "done"
    first = trial_log.read_all(tmp_path / "results/trials.jsonl")
    assert next(r for r in first if r.source == "research-test").submission == IDENTITY | {
        "experiment_id": STEM + "__FINAL_HOLDOUT__1"
    }
    test_folder = tmp_path / "results" / out["test"]["run_folder"]
    assert (
        json.loads((test_folder / "info.json").read_text())["submission"]["experiment_id"]
        == STEM + "__FINAL_HOLDOUT__1"
    )
    out = run_research(tmp_path, submission_grid(), retest=True)
    assert len(fakes.calls) == 8 and out["test"]["run"] == 2
    records = trial_log.read_all(tmp_path / "results/trials.jsonl")
    assert (
        next(r for r in records if r.source == "research-retest-1").submission["experiment_id"]
        == STEM + "__FINAL_HOLDOUT__2"
    )
    assert authorization.read_bytes() == before
    authorization.unlink()
    out = run_research(tmp_path, submission_grid(), retest=True)
    assert len(fakes.calls) == 8 and out["test"]["run"] == 2


def test_legacy_grid_is_not_gated(tmp_path, fakes):
    out = run_research(tmp_path)
    assert len(fakes.calls) == 7 and out["test"]["status"] == "done"
    info = json.loads((out["folder"] / "research.json").read_text())
    assert "submission" not in info and "dataset" not in info
    assert "code_commit" in info and "code_dirty" in info
    assert all(
        "submission" not in json.loads(line)
        for line in (tmp_path / "results/trials.jsonl").read_text().splitlines()
    )


def test_git_errors_are_optional_metadata(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("git unavailable")

    monkeypatch.setattr(research.subprocess, "run", fail)
    assert research._code_version() == {"code_commit": None, "code_dirty": None}


@pytest.mark.parametrize("status,dirty", [("", False), (" M modified.py\n", True)])
def test_code_provenance(monkeypatch, status, dirty):
    from types import SimpleNamespace

    calls = []

    def git(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(stdout="abc123\n" if command[1] == "rev-parse" else status)

    monkeypatch.setattr(research.subprocess, "run", git)
    assert research._code_version() == {"code_commit": "abc123", "code_dirty": dirty}
    assert [call[0][1:] for call in calls] == [["rev-parse", "HEAD"], ["status", "--porcelain"]]
    assert all(
        call[1]["cwd"] == research.Path(research.__file__).resolve().parents[3] for call in calls
    )


def test_dataset_sorted_symbols_sources_and_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(intake, "HOME_DIR", tmp_path)
    main, preferred, fallback = (tmp_path / name for name in ("main", "preferred", "fallback"))
    a, b = date(2020, 1, 1), date(2020, 1, 2)
    entries = [(main, "US500", a), (fallback, "US500", b), (main, "NAS100", a)]
    for root, symbol, day in entries:
        path = cache_path(root, symbol, day)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x")
    sources = SymbolSources(
        {"US500": main, "NAS100": main}, {"US500": preferred}, {"US500": fallback}
    )
    version = intake.dataset_version(["US500", "NAS100"], a, b, sources)
    assert version == intake.dataset_version(["NAS100", "US500"], a, b, sources)
    lines = sorted(
        f"{symbol}\t{cache_path(root, symbol, day).relative_to(tmp_path).as_posix()}\t1"
        for root, symbol, day in entries
    )
    assert version["version"] == hashlib.sha256("\n".join(lines).encode()).hexdigest()
    assert version["source_summary"] == ["fallback", "main"]


@pytest.mark.skipif(os.name != "nt", reason="Windows drive-relative paths")
def test_dataset_cache_on_another_drive(tmp_path, monkeypatch):
    from pathlib import Path

    other_drive = "Z:/repo" if tmp_path.drive.upper() != "Z:" else "Y:/repo"
    monkeypatch.setattr(intake, "HOME_DIR", Path(other_drive))
    sources = SymbolSources.single(tmp_path / "cache", ["US500"])
    day = date(2020, 1, 1)
    path = cache_path(tmp_path / "cache", "US500", day)
    path.parent.mkdir(parents=True)
    path.write_bytes(b"cache")
    version = intake.dataset_version(["US500"], day, day, sources)
    assert version == intake.dataset_version(["US500"], day, day, sources)
    assert version["source_summary"]
    assert all(not Path(label).is_absolute() for label in version["source_summary"])


def test_holdout_number_uses_trial_log_across_grids(tmp_path):
    spec = load_grid(write_grid(tmp_path, submission_grid()))
    trials = tmp_path / "trials.jsonl"
    record = trial_log.TrialRecord(
        "other_grid",
        "opening_range",
        {},
        ["US500"],
        "2021-09-14",
        "2022-01-01",
        "research-test",
        "fixed",
        submission=IDENTITY | {"experiment_id": STEM + "__FINAL_HOLDOUT__3"},
    )
    trial_log.append(record, trials)
    assert research._holdout_number(spec, {"run": 1}, trials) == 4
    assert research._holdout_number(spec, {"run": 5}, trials) == 6


def test_submission_context_is_reset_on_failure(tmp_path):
    with pytest.raises(RuntimeError), trial_log.submission_identity(IDENTITY):
        raise RuntimeError("interrupted")
    record = trial_log.make_record(
        "legacy", "opening_range", {}, ["US500"], date(2020, 1, 1), date(2020, 1, 2), "research", []
    )
    assert record.submission is None


@pytest.mark.parametrize("text", ["{", "[]", "null", "3"])
def test_malformed_authorization_is_denied(tmp_path, text):
    spec = load_grid(write_grid(tmp_path, submission_grid()))
    path = authorize(tmp_path)
    path.write_text(text, encoding="utf-8")
    assert not research._test_authorized(spec, tmp_path / "results")
