"""Synthetic CSV runner persistence; no real calendar or market cache reads."""

# ruff: noqa: F811

import json

import pytest

from backtester.analytics.trial_log import read_all
from backtester.data import news
from tests.data.news.test_loader import row, write_csv
from tests.tools.test_research import GRID, fakes, read_csv, run_research  # noqa: F401


def news_grid(path):
    return GRID.replace("[base]", '[base]\n"engine.news.path" = ' + json.dumps(path.as_posix()))


def test_runner_every_variant_hash_split_resume_and_retest(tmp_path, fakes, monkeypatch):
    path = write_csv(
        tmp_path,
        [
            row(scheduled_timestamp_utc="2020-03-02T14:30:00Z", scheduled_date_utc="2020-03-02"),
            row(
                event_id="two",
                dedupe_key="two",
                scheduled_timestamp_utc="2026-03-04T14:30:00Z",
                scheduled_date_utc="2026-03-04",
            ),
        ],
    )
    reads = []
    original = news.load_calendar

    def load(config):
        reads.append(config.path)
        return original(config)

    monkeypatch.setattr(news, "load_calendar", load)
    text = news_grid(path)
    out = run_research(tmp_path, text)
    assert len(reads) == 1  # one immutable snapshot shared by all variants and test
    folder = out["folder"]
    info = json.loads((folder / "research.json").read_text())
    split = read_csv(folder / "news.csv")
    assert len({r["variant_id"] for r in split if r["period"] == "development"}) == 6
    assert any(r["bucket"] == "no_calendar" for r in split)
    assert any(r["bucket"] == "news" for r in split)
    assert any(r["bucket"] == "news_free" for r in split)
    assert len({r["source_period"] for r in split if r["bucket"] != "no_calendar"}) == 2
    hashes = {r["calendar_sha256"] for r in split}
    assert len(hashes) == 1
    digest = hashes.pop()
    assert all(
        r.settings["calendar_sha256"] == digest for r in read_all(tmp_path / "results/trials.jsonl")
    )
    for variant in (folder / "variants").iterdir():
        assert json.loads((variant / "settings.json").read_text())["calendar_sha256"] == digest
        assert (variant / "news.json").is_file()
        card = json.loads((variant / "scorecard.json").read_text())["scorecard"]
        for dimension in ("day", "minute"):
            group = [
                r
                for r in split
                if r["variant_id"] == variant.name
                and r["period"] == "development"
                and r["dimension"] == dimension
            ]
            assert sum(int(r["trades"]) for r in group) == card["trades"]
            assert sum(float(r["net_r"]) for r in group) == pytest.approx(card["net_r"])
    for name in (info["chosen"]["dev_run"], info["test"]["run_folder"]):
        assert (
            json.loads((tmp_path / "results" / name / "settings.json").read_text())[
                "calendar_sha256"
            ]
            == digest
        )
    assert all(n["sha256"] == digest for n in info["news_calendars"])
    count = len(fakes.calls)
    run_research(tmp_path, text, dev_only=True)
    assert len(fakes.calls) == count
    run_research(tmp_path, text, retest=True)
    assert len(fakes.calls) == count + 1
    assert {r["test_run"] for r in read_csv(folder / "news.csv") if r["period"] == "test"} == {
        "1",
        "2",
    }
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="calendar.*changed"):
        run_research(tmp_path, text, dev_only=True)
    assert len(fakes.calls) == count + 1


def test_missing_calendar_disabled_and_recorded(tmp_path, fakes):
    out = run_research(tmp_path, news_grid(tmp_path / "missing.csv"), dev_only=True)
    folder = out["folder"]
    assert not (folder / "news.csv").exists()
    info = json.loads((folder / "research.json").read_text())
    assert info["news_calendars"][0]["status"] == "no calendar"
    records = read_all(tmp_path / "results/trials.jsonl")
    # Preserve the pre-feature trial identity when no calendar exists: no new trial count.
    assert all("calendar_sha256" not in r.settings for r in records)
