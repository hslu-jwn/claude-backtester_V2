"""Async intake questions and immutable reply handling."""

# ruff: noqa: F811
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from backtester.tools import intake
from tests.tools.test_intake import payload, publish, umbrella  # noqa: F401
from tests.tools.test_intake_envelopes import claimed, emit, folder, read, validate, write  # noqa: F401

FIXTURES = Path(__file__).parent / "fixtures/intake"


def examples():
    return [read(FIXTURES / name) for name in ("00ab.json", "reply.json", "1abf.json")]


def test_questions_and_replies():
    messages = examples()
    opened = intake.open_questions(messages)
    assert [m["feedback_id"] for m in opened] == [messages[2]["feedback_id"]]
    now = datetime.fromisoformat(messages[2]["created_at"])
    assert intake.summary_line(opened, now) == "Open questions for Research: 1 (oldest 0 days)"
    assert intake.summary_line(opened, now + timedelta(days=3)).endswith("(oldest 3 days)")
    unknown = dict(messages[1], feedback_id="unknown", in_reply_to="missing")
    assert intake.new_replies(messages + [unknown], set())[-1]["unknown_reference"]
    assert not intake.open_questions([dict(messages[0], issues=[{"code": "PROGRESS"}])])


def test_assume_park_and_inbox(umbrella, claimed, capsys):
    results = umbrella / "results"
    points = [
        {"field": "/strategy_id", "message": "First point"},
        {"field": "/status", "message": "Second point"},
    ]
    out = intake.assume(umbrella, claimed, "IMPLEMENTING", points)
    validate(umbrella, out, "feedback")
    assert len(read(out)["issues"]) == 2
    before = set(out.parent.glob("*.json"))
    for bad in ([], [{"field": "/missing", "message": "bad"}]):
        with pytest.raises(ValueError):
            intake.assume(umbrella, claimed, "TESTING", bad)
    assert set(out.parent.glob("*.json")) == before
    parked = intake.park(umbrella, results, claimed, points)
    validate(umbrella, parked, "feedback")
    assert read(results / "intake" / claimed.path.stem / "claim.json")["parked"]
    assert (
        intake.recover(umbrella, results, now=datetime.now().astimezone() + timedelta(days=2)) == []
    )
    assert claimed.path.exists()
    for version in ("0.9.0", "1.0.0"):
        publish(umbrella, dict(claimed.payload, specification_version=version))
        intake.inbox(umbrella, results)
        assert "unpark" not in capsys.readouterr().out.lower()
    newer = dict(claimed.payload, specification_version="1.0.1")
    publish(umbrella, newer)
    intake.inbox(umbrella, results)
    assert "unpark" in capsys.readouterr().out.lower()


def test_inbox_ack_and_invalid(umbrella, capsys):
    results = umbrella / "results"
    messages = examples()
    for message in messages:
        write(
            umbrella / "Shared_Interface/feedback/messages" / (message["feedback_id"] + ".json"),
            message,
        )
    (umbrella / "Shared_Interface/feedback/messages/bad.json").write_text("{")
    intake.inbox(umbrella, results, json_output=True)
    output = capsys.readouterr()
    assert set(json.loads(output.out)) >= {"open", "replies", "summary"}
    assert "warning" in output.err.lower()
    intake.inbox(umbrella, results, ack=messages[1]["feedback_id"])
    capsys.readouterr()
    intake.inbox(umbrella, results, json_output=True)
    assert not json.loads(capsys.readouterr().out)["replies"]
    with pytest.raises(ValueError):
        intake.inbox(umbrella, results, ack="missing")


def test_result_assumption_warnings(umbrella, claimed, folder):
    points = [{"field": "/status", "message": "An assumption"}]
    first = intake.assume(umbrella, claimed, "TESTING", points)
    second = intake.assume(umbrella, claimed, "TESTING", points)
    reply = dict(
        read(first),
        feedback_id="REPLY_1",
        producer="Research department",
        in_reply_to=read(first)["feedback_id"],
        issues=[
            {
                "code": "CONFIRMED",
                "field": "/status",
                "message": "Confirmed",
                "severity": "INFO",
                "requires_revision": False,
            }
        ],
    )
    write(first.parent / "reply.json", reply)
    warnings = read(emit(umbrella, claimed, folder))["warnings"]
    assert f"Assumption {first.stem}: CONFIRMED by REPLY_1" in warnings
    assert f"Open assumption (unanswered): {second.stem}: /status" in warnings
