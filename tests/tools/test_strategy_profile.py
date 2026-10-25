"""Cases: CLI refuses test period before execution; all seven sequential defaults;
overrides/workers forwarded; JSON/Markdown and single trial line; research artifact wiring.
"""

import json
from types import SimpleNamespace

import pytest

from backtester.tools import strategy_profile as tool


def test_period_guard(monkeypatch):
    monkeypatch.setattr(tool, "run_backtests", lambda *a, **k: pytest.fail("must not run"))
    with pytest.raises(SystemExit, match="test period"):
        tool.main(["--strategy", "trend_following", "--end", "2022-01-01"])


def test_all_defaults_outputs_and_trials(tmp_path, monkeypatch):
    calls, records = [], []

    def run(symbols, start, end, settings, **kw):
        calls.append((symbols, settings, kw))
        return SimpleNamespace(trades=[])

    monkeypatch.setattr(tool, "run_backtests", run)
    monkeypatch.setattr(
        tool,
        "calculate",
        lambda *a, **k: {"dimensions": {}, "total_trades": 0, "strongest_skill_cells": []},
    )
    monkeypatch.setattr(tool, "append", records.append)
    assert tool.main(["--all", "--workers", "1", "--out", str(tmp_path)]) == 0
    assert len(calls) == len(records) == 7
    assert {r.family for r in records} == {s + "-profile" for s in tool.REGISTRY}
    assert all(c[2]["workers"] == 1 for c in calls)
    assert len(list(tmp_path.glob("*/profile.md"))) == 7
    for path in tmp_path.glob("*/profile.json"):
        assert json.loads(path.read_text())["total_trades"] == 0


def test_research_saved_runs_only(tmp_path, monkeypatch):
    from datetime import date

    calls = []
    folder = tmp_path / "research"
    folder.mkdir()
    info = {"chosen": {"id": "v1", "dev_run": "dev"}}
    monkeypatch.setattr(tool, "read_trades", lambda path: [str(path)])

    def calc(trades, a, b, sources):
        calls.append((trades, a, b))
        return {"total_trades": 1, "dimensions": {}, "strongest_skill_cells": []}

    monkeypatch.setattr(tool, "calculate", calc)
    monkeypatch.setattr(tool, "append", lambda *a: pytest.fail("no profile trial in research"))
    tool.research_results(
        folder,
        tmp_path,
        info,
        [{"test_run": 1, "run_folder": "test", "start": "2021-09-14", "end": "2021-10-01"}],
        date(2020, 1, 1),
        date(2021, 9, 13),
        None,
    )
    assert len(calls) == 2
    assert set(info["profiles"]) == {"development", "test 1"}
    for target in (folder, folder / "variants/v1", tmp_path / "dev", tmp_path / "test"):
        assert (target / "profile.json").is_file()


def test_overrides_and_explicit_test_period(tmp_path, monkeypatch):
    calls = []

    def run(*args, **kw):
        calls.append(args)
        return SimpleNamespace(trades=[])

    monkeypatch.setattr(tool, "run_backtests", run)
    monkeypatch.setattr(
        tool,
        "calculate",
        lambda *a, **k: {"dimensions": {}, "total_trades": 0, "strongest_skill_cells": []},
    )
    monkeypatch.setattr(tool, "append", lambda *a: None)
    tool.main(
        [
            "--strategy",
            "trend_following",
            "--symbols",
            "xauusd",
            "--set",
            "atr_period=7",
            "--end",
            "2022-01-01",
            "--allow-test-period",
            "--out",
            str(tmp_path),
        ]
    )
    assert calls[0][0] == ["XAUUSD"]
    assert calls[0][3].strategy.atr_period == 7
