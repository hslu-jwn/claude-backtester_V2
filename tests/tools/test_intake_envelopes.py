"""Envelope and lifecycle cases, written before the step-3 implementation."""

# Re-exported pytest fixtures are deliberately shadowed by test arguments.
# ruff: noqa: F811

import builtins
import hashlib
import importlib
import io
import json
import os
from datetime import date
from pathlib import Path

import pytest

from backtester.tools import intake, research
from tests.tools.test_intake import payload, publish, umbrella  # noqa: F401


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def validate(root, path, kind):
    schema = read(root / f"Shared_Interface/schemas/{kind}.schema.json")
    js = pytest.importorskip("jsonschema")
    js.Draft202012Validator(schema, format_checker=js.FormatChecker()).validate(read(path))


@pytest.fixture
def claimed(umbrella, payload):
    publish(umbrella, payload)
    return intake.claim(umbrella, umbrella / "results")


@pytest.fixture
def folder(umbrella, claimed):
    folder = umbrella / "results/research/tiny"
    identity = {
        "strategy_id": "SYNTHETIC",
        "specification_version": "1.0.0",
        "submission_sha256": claimed.sha256,
        "experiment_id": claimed.path.stem + "__DEVELOPMENT__1",
    }
    dataset = {
        "dataset_id": "v2-cache",
        "version": "fixture",
        "symbols": ["NAS100"],
        "start": "2020-01-02",
        "end": "2020-01-03",
        "source_summary": ["cache"],
    }
    write(
        folder / "research.json",
        {
            "submission": identity,
            "dataset": dataset,
            "code_commit": "a" * 40,
            "chosen": {"id": "v001", "dev_run": "dev"},
            "grid_robustness": [{"stable": True}],
            "variants": 1,
        },
    )
    run = folder / "variants/v001"
    write(run / "info.json", {"submission": identity, "dataset": dataset, "code_commit": "a" * 40})
    write(
        run / "summary.json",
        {
            "combined": {
                "net_r_net": 3,
                "max_drawdown_r_net": 1,
                "expectancy_r": 0.75,
                "profit_factor": 4,
                "trades": 4,
                "win_rate": 0.75,
                "avg_win_r": 4 / 3,
                "avg_loss_r": -1,
            }
        },
    )
    write(
        run / "scorecard.json",
        {
            "id": "v001",
            "day_sharpe": 0.2,
            "scorecard": {"net_r": 3},
            "overrides": {"range_minutes": 5},
        },
    )
    write(
        run / "settings.json",
        {
            "run": {"symbols": ["NAS100"]},
            "strategy": {"range_minutes": 5},
            "engine": {"costs": {"spread_enabled": True}},
        },
    )
    write(folder / "significance.json", {"flags": ["rc_not_significant"], "psr": 0.6})
    from backtester.analytics.trial_log import TrialRecord, append

    append(
        TrialRecord(
            "tiny",
            "opening_range",
            {},
            ["NAS100"],
            "2020-01-02",
            "2020-01-03",
            "research",
            "fixed",
            series="research/tiny/variants/v001/daily.csv",
            submission=identity,
        ),
        umbrella / "results/trials.jsonl",
    )
    return folder


def emit(root, claimed, folder, **kwargs):
    return intake.emit_result(
        root,
        root / "results",
        claimed,
        experiment_id=claimed.path.stem + "__" + kwargs.get("stage", "DEVELOPMENT") + "__1",
        stage=kwargs.pop("stage", "DEVELOPMENT"),
        research_folder=folder,
        requested_costs={"request": "fixture"},
        **kwargs,
    )


def test_malformed_feedback_and_issue_mapping(umbrella):
    path = umbrella / "Shared_Interface/queue/pending/BAD__v1.0.0.json"
    path.write_text("{")
    _, issues = intake.validate_file(path, umbrella, results=umbrella / "results")
    out = intake.emit_feedback(
        umbrella,
        status="REJECTED",
        issues=issues,
        subject_file=path,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    validate(umbrella, out, "feedback")
    data = read(out)
    assert data["strategy_id"] is data["specification_version"] is None
    assert data["scope"] == "SUBMISSION"
    assert data["subject_file"] == path.relative_to(umbrella).as_posix()
    assert data["issues"][0] == {
        "code": "INVALID_JSON",
        "severity": "ERROR",
        "message": issues[0].message,
        "field": None,
        "requires_revision": True,
    }


def test_reject_invalid_preserves_bytes_and_collision(umbrella, payload):
    path = publish(umbrella, payload)
    path.write_bytes(b"{")
    terminal = umbrella / "Shared_Interface/queue/rejected" / path.name
    terminal.write_bytes(b"existing")
    outputs = intake.reject_invalid(umbrella, umbrella / "results")
    assert len(outputs) == 1 and not path.exists()
    assert terminal.read_bytes() == b"existing"
    assert terminal.with_name(path.stem + ".dup-1.json").read_bytes() == b"{"
    assert read(outputs[0])["submission_sha256"] == hashlib.sha256(b"{").hexdigest()
    validate(umbrella, outputs[0], "feedback")
    assert intake.reject_invalid(umbrella, umbrella / "results") == []


@pytest.mark.parametrize("data", [False, True])
def test_unsupported_rejected(umbrella, payload, data):
    payload["entries"]["execution_timing"] = "NEXT_BAR_OPEN"
    if data:
        payload["market"]["universe"] = ["UNKNOWN"]
    publish(umbrella, payload)
    claim = intake.claim(umbrella, umbrella / "results")
    out = intake.reject_unsupported(umbrella, umbrella / "results", claim)
    validate(umbrella, out, "feedback")
    assert read(out)["status"] == ("UNSUPPORTED_DATA" if data else "UNSUPPORTED_STRATEGY_TYPE")
    assert not claim.path.exists()
    assert (claim.path.parent.parent / "rejected" / claim.path.name).exists()


@pytest.mark.parametrize("status", ["CLAIMED", "IMPLEMENTING", "TESTING"])
def test_progress(umbrella, claimed, status):
    path = intake.progress(umbrella, claimed, status)
    validate(umbrella, path, "feedback")
    assert read(path)["issues"][0]["requires_revision"] is False


def test_ids_survive_restart(umbrella, claimed):
    stem = claimed.path.stem
    results = umbrella / "results"
    assert intake.next_experiment_id(results, stem, "DEVELOPMENT") == stem + "__DEVELOPMENT__1"
    write(results / "intake" / stem / "experiments" / (stem + "__DEVELOPMENT__7.json"), {})
    importlib.reload(intake)
    assert intake.next_experiment_id(results, stem, "DEVELOPMENT") == stem + "__DEVELOPMENT__8"
    assert intake.next_experiment_id(results, stem, "FINAL_HOLDOUT") == stem + "__FINAL_HOLDOUT__1"


def test_result_metrics_artifacts_and_immutable_record(umbrella, claimed, folder):
    out = emit(umbrella, claimed, folder)
    validate(umbrella, out, "result")
    data = read(out)
    assert data["submission_sha256"] == claimed.sha256
    assert data["metrics"] == {
        "net_r": 3,
        "max_drawdown_r": 1,
        "expectancy_r": 0.75,
        "sharpe_daily_r": 0.2,
        "profit_factor": 4,
        "trades": 4,
        "win_rate": 0.75,
        "average_win_r": 4 / 3,
        "average_loss_r": -1,
        "sortino_daily_r": None,
        "net_return_pct": None,
        "max_drawdown_pct": None,
        "expectancy_pct": None,
        "exposure_pct": None,
        "turnover_pct": None,
    }
    assert data["holdout_disclosure"] == "NONE" and data["variants_tried"] == 1
    assert data["resolved_cost_model"] == {"spread_enabled": True}
    assert data["statistical_diagnostics"]["psr"] == 0.6
    assert data["robustness"]["grid_robustness"] == [{"stable": True}]
    assert data["artifacts"]
    for artifact in data["artifacts"]:
        assert "\\" not in artifact["path"] and not Path(artifact["path"]).is_absolute()
        assert (
            artifact["sha256"]
            == hashlib.sha256((umbrella / artifact["path"]).read_bytes()).hexdigest()
        )
    record = (
        umbrella
        / "results/intake"
        / claimed.path.stem
        / "experiments"
        / (data["experiment_id"] + ".json")
    )
    assert read(record)["envelope"] == data
    with pytest.raises(FileExistsError):
        emit(umbrella, claimed, folder)


@pytest.mark.parametrize("disclosure", ["REDACTED", "FULL"])
def test_holdout_authorization_and_redaction(umbrella, claimed, folder, disclosure):
    with pytest.raises(ValueError, match="authoriz"):
        emit(umbrella, claimed, folder, stage="FINAL_HOLDOUT")
    info = read(folder / "research.json")
    run = umbrella / "results/holdout"
    for name in ("info.json", "summary.json", "settings.json", "scorecard.json"):
        write(run / name, read(folder / "variants/v001" / name))
    meta = read(run / "info.json")
    meta["submission"]["experiment_id"] = claimed.path.stem + "__FINAL_HOLDOUT__1"
    write(run / "info.json", meta)
    info["test"] = {"run_folder": "holdout", "status": "done"}
    write(folder / "research.json", info)
    write(
        umbrella / "results/intake" / claimed.path.stem / "test_authorization.json",
        {
            "authorized_by": "user",
            "quote": "Run the one-time test.",
            "authorized_at": "2026-10-28T12:00:00Z",
            "experiment_id": info["submission"]["experiment_id"],
        },
    )
    out = emit(umbrella, claimed, folder, stage="FINAL_HOLDOUT", holdout_disclosure=disclosure)
    validate(umbrella, out, "result")
    assert read(out)["holdout_disclosure"] == disclosure
    if disclosure == "REDACTED":
        assert all(v is None for v in read(out)["metrics"].values())
        assert read(out)["artifacts"] == []
    else:
        assert read(out)["metrics"]["net_r"] == 3
        assert read(out)["artifacts"]


def test_outside_paths_and_invalid_envelopes_refused(umbrella, claimed, folder):
    info = read(folder / "research.json")
    info["chosen"]["dev_run"] = "../../outside"
    write(folder / "research.json", info)
    with pytest.raises(ValueError, match="path|umbrella"):
        emit(umbrella, claimed, folder)
    with pytest.raises(ValueError):
        intake.emit_feedback(
            umbrella,
            status="REJECTED",
            issues=claimed.issues,
            claim=claimed,
            subject_file=umbrella.parent / "outside",
        )
    js = pytest.importorskip("jsonschema")
    with pytest.raises(js.ValidationError):
        intake.emit_feedback(
            umbrella, status="INVALID", issues=[], claim=claimed, subject_file=claimed.path
        )
    assert not list((umbrella / "Shared_Interface/feedback").rglob("*.json"))


def test_feedback_collision_refused(umbrella, claimed, monkeypatch):
    monkeypatch.setattr(intake, "_feedback_id", lambda _: "FB_SYNTHETIC_fixed_aaaa")
    first = intake.progress(umbrella, claimed, "CLAIMED")
    raw = first.read_bytes()
    with pytest.raises(FileExistsError):
        intake.progress(umbrella, claimed, "TESTING")
    assert first.read_bytes() == raw


def test_finish_metadata_and_collision(umbrella, claimed):
    terminal = claimed.path.parent.parent / "completed" / claimed.path.name
    terminal.write_bytes(b"existing")
    intake.finish(umbrella, umbrella / "results", claimed, "completed")
    assert terminal.read_bytes() == b"existing"
    assert terminal.with_name(terminal.stem + ".dup-1.json").exists()
    record = read(umbrella / "results/intake" / claimed.path.stem / "claim.json")
    assert record["outcome"] == "completed" and record["finished_at"].endswith("+00:00")


def test_i7_real_development_run_and_negative_paths(umbrella, payload, monkeypatch):
    from backtester.analytics.trial_log import read_all
    from backtester.data.sources import SymbolSources
    from tests.test_runner import FULL, write_day

    opened = []
    real_io_open, real_os_open = io.open, os.open

    def check_write(path):
        if not isinstance(path, int):
            resolved = Path(path).resolve()
            assert resolved.is_relative_to(umbrella.resolve()), resolved
            opened.append(resolved)

    def guarded_io(path, mode="r", *args, **kwargs):
        if any(flag in mode for flag in "wax+"):
            check_write(path)
        return real_io_open(path, mode, *args, **kwargs)

    def guarded_os(path, flags, *args, **kwargs):
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT):
            check_write(path)
        return real_os_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(io, "open", guarded_io)
    monkeypatch.setattr(builtins, "open", guarded_io)
    monkeypatch.setattr(os, "open", guarded_os)

    payload["market"]["universe"] = ["XAUUSD"]
    payload["math"]["parameters"][0].update(
        name="warmup_days", baseline=0, domain={"kind": "FIXED"}, tunable=False
    )
    payload["experiment"]["total_grid_size"] = 1
    path = umbrella / "Shared_Interface/queue/pending/SYNTHETIC__v1.0.0.json"
    temp = path.with_name(".tmp-x")
    temp.write_bytes(json.dumps(payload).encode())
    temp.replace(path)
    raw = path.read_bytes()
    results = umbrella / "results"
    assert not intake._invalid(intake.validate_file(path, umbrella, results=results)[1])
    claim = intake.claim(umbrella, results)
    intake.progress(umbrella, claim, "CLAIMED")
    cache = umbrella / "cache"
    write_day(cache, "XAUUSD", date(2020, 1, 6), FULL)
    identity = {
        "strategy_id": "SYNTHETIC",
        "specification_version": "1.0.0",
        "submission_sha256": claim.sha256,
        "experiment_id": intake.next_experiment_id(results, path.stem, "DEVELOPMENT"),
    }
    grid = umbrella / "tiny.toml"
    grid.write_text(
        'strategy = "session_zone_sweep"\nsymbols = ["XAUUSD"]\n'
        "min_trades = 1\nsensitivity = false\nmonkeys = false\n"
        "[base]\nwarmup_days = 0\n[submission]\n"
        + "\n".join(f"{k} = {json.dumps(v)}" for k, v in identity.items())
    )
    # All output, including provenance and cache lookups, stays in this umbrella.
    monkeypatch.setattr(intake, "HOME_DIR", umbrella)
    out = research.run_research(
        grid,
        results_dir=results,
        dev_only=True,
        workers=1,
        sources=SymbolSources.single(cache, ["XAUUSD"]),
        log=lambda *a: None,
    )
    envelope = emit(umbrella, claim, out["folder"])
    intake.finish(umbrella, results, claim, "completed")
    terminal = path.parent.parent / "completed" / path.name
    assert terminal.read_bytes() == raw
    assert read(envelope)["submission_sha256"] == hashlib.sha256(raw).hexdigest()
    validate(umbrella, envelope, "result")
    assert read_all(results / "trials.jsonl")
    assert all(t.submission == identity for t in read_all(results / "trials.jsonl"))
    before = (results / "trials.jsonl").read_bytes()
    bad = path.with_name("BAD__v1.0.0.json")
    bad.write_text("{")
    payload["strategy_id"] = "UNSUPPORTED"
    payload["entries"]["execution_timing"] = "NEXT_BAR_OPEN"
    publish(umbrella, payload)
    assert len(intake.reject_invalid(umbrella, results)) == 1
    unsupported = intake.claim(umbrella, results)
    intake.reject_unsupported(umbrella, results, unsupported)
    assert intake.claim(umbrella, results) is None
    assert (results / "trials.jsonl").read_bytes() == before
    assert len(list((path.parent.parent / "rejected").glob("*.json"))) == 2
    assert opened


def test_missing_metrics_are_null_and_trial_count_is_local(umbrella, claimed, folder):
    summary = folder / "variants/v001/summary.json"
    write(summary, {"combined": {"trades": 0, "net_return_pct": 99, "exposure_pct": 50}})
    from backtester.analytics.trial_log import TrialRecord, append

    append(
        TrialRecord(
            "elsewhere",
            "opening_range",
            {},
            ["NAS100"],
            "2020-01-02",
            "2020-01-03",
            "research",
            "fixed",
            count=99,
            series="research/other/daily.csv",
        ),
        umbrella / "results/trials.jsonl",
    )
    out = emit(umbrella, claimed, folder)
    assert read(out)["variants_tried"] == 1
    assert read(out)["metrics"]["net_r"] is None
    assert read(out)["metrics"]["trades"] == 0
    assert read(out)["metrics"]["net_return_pct"] is None
    assert read(out)["metrics"]["exposure_pct"] is None


def test_artifact_symlink_outside_refused(umbrella, claimed, folder, tmp_path):
    target = tmp_path.parent / (tmp_path.name + "-external.txt")
    target.write_text("outside fixture")
    try:
        link = folder / "outside.txt"
        try:
            link.symlink_to(target)
        except OSError:
            pytest.skip("OS does not permit symlinks")
        with pytest.raises(ValueError, match="umbrella"):
            emit(umbrella, claimed, folder)
    finally:
        target.unlink()


def test_cli_lifecycle(umbrella, claimed, folder, monkeypatch):
    monkeypatch.setattr(intake, "HOME_DIR", umbrella / "V2")
    # The CLI derives its result directory from the umbrella and the V2 directory name.
    (umbrella / "V2").mkdir()
    (umbrella / "results").rename(umbrella / "V2/results")
    root = ["--root", str(umbrella)]
    assert (
        intake.main(
            [
                "result",
                claimed.path.stem,
                "--research-folder",
                str(umbrella / "V2/results/research/tiny"),
                "--stage",
                "DEVELOPMENT",
                *root,
            ]
        )
        == 0
    )
    assert intake.main(["progress", claimed.path.stem, "TESTING", *root]) == 0
    assert intake.main(["finish", claimed.path.stem, "completed", *root]) == 0
    assert (claimed.path.parent.parent / "completed" / claimed.path.name).exists()


def test_development_envelope_carries_nothing_from_the_test_period(umbrella, claimed, folder):
    info = read(folder / "research.json")
    info["drawdown_bounds"] = {"development": {"p95": 5}, "test 1": {"p95": 9}}
    info["bayes"] = {"development": {"p": 0.6}, "tests": [{"test_run": 1, "p": 0.1}], "twins": []}
    write(folder / "research.json", info)
    for name in ("test.csv", "report.md", "bayes.json"):
        (folder / name).write_text("test-period content", encoding="utf-8")
    envelope = read(emit(umbrella, claimed, folder))
    assert envelope["robustness"]["drawdown_bounds"] == {"development": {"p95": 5}}
    assert envelope["robustness"]["bayes"]["tests"] == []
    assert envelope["robustness"]["bayes"]["development"] == {"p": 0.6}
    names = {Path(a["path"]).name for a in envelope["artifacts"]}
    assert not names & {"test.csv", "report.md", "bayes.json"}
