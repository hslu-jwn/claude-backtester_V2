"""Test cases: all variant lanes keep daily.csv; resume and historical retests backfill
from trades without execution; links do not change trial identity or daily statistics.
"""

# Re-exported pytest fixture is intentionally shadowed by test arguments.
# ruff: noqa: F811

import json

import pytest

from backtester.analytics import trial_log
from backtester.tools import research
from tests.tools.test_research import (  # noqa: F401
    fakes,
    read_csv,
    research_folder,
    run_research,
)


def test_every_variant_test_and_resume(tmp_path, fakes, monkeypatch):
    from dataclasses import replace

    run_research(tmp_path)
    run_research(tmp_path, retest=True)
    folder = research_folder(tmp_path)
    records = trial_log.read_all(tmp_path / "results" / "trials.jsonl")
    assert len(records) == 8
    assert all(r.series for r in records)
    for r in records:
        dates, values = trial_log.read_series(r, tmp_path / "results", "net_r_mtm")
        assert len(dates) > 0
        assert abs(values.sum() - r.net_r) < 1e-9
    assert len(list((folder / "variants").glob("*/daily.csv"))) == 6
    # Fake trade CSV writer has only IDs; supply the original deterministic trades on read.
    saved = fakes.run(
        fakes.calls[0].symbols, fakes.span[0], fakes.span[1], fakes.calls[0].settings
    ).trades
    monkeypatch.setattr(research, "read_trades", lambda p: saved)
    old_count = len(fakes.calls)
    for r in records:
        (tmp_path / "results" / r.series).unlink()
        # Upgrade a legacy log line, preserving every pre-existing statistic and timestamp.
        trial_log.append(replace(r, series=None), tmp_path / "results" / "trials.jsonl")
    run_research(tmp_path)
    assert len(fakes.calls) == old_count
    assert all((tmp_path / "results" / r.series).exists() for r in records)
    assert trial_log.read_all(tmp_path / "results" / "trials.jsonl") == records


def test_sensitivity_keeps_series(tmp_path, fakes):
    from tests.tools.test_research import GRID

    run_research(tmp_path, GRID.replace("sensitivity = false", "sensitivity = true"), dev_only=True)
    folder = research_folder(tmp_path)
    rows = read_csv(folder / "sensitivity.csv")
    for row in rows:
        if row["status"] == "done":
            assert (folder / "sensitivity" / row["id"] / "daily.csv").is_file()
    records = trial_log.read_all(tmp_path / "results" / "trials.jsonl")
    assert all(r.series for r in records)


def test_reporting_failure_does_not_replay_development(tmp_path, fakes, monkeypatch):
    import pytest

    from backtester.tools import research_series
    from tests.tools.test_research import make_trade

    original = research_series.daily_net_r_mtm
    monkeypatch.setattr(
        research_series,
        "daily_net_r_mtm",
        lambda *a: (_ for _ in ()).throw(RuntimeError("report failed")),
    )
    with pytest.raises(RuntimeError, match="report failed"):
        run_research(tmp_path, dev_only=True)
    assert len(list((research_folder(tmp_path) / "variants").glob("*/scorecard.json"))) == 1
    monkeypatch.setattr(research_series, "daily_net_r_mtm", original)
    monkeypatch.setattr(research, "read_trades", lambda p: [make_trade("US500", 2015, 0.2, 0)])
    run_research(tmp_path, dev_only=True)
    assert len(fakes.calls) == 6


def test_test_reporting_failure_keeps_once_only_guard(tmp_path, fakes, monkeypatch):
    import pytest

    from backtester.tools import research_series
    from tests.tools.test_research import make_trade

    original = research_series.daily_net_r_mtm

    def fail_test(trades, start, end, sources):
        if start.year == 2021:
            raise RuntimeError("test report failed")
        return original(trades, start, end, sources)

    monkeypatch.setattr(research_series, "daily_net_r_mtm", fail_test)
    with pytest.raises(RuntimeError, match="test report failed"):
        run_research(tmp_path)
    assert len(fakes.calls) == 7
    monkeypatch.setattr(research_series, "daily_net_r_mtm", original)
    monkeypatch.setattr(research, "read_trades", lambda p: [make_trade("US500", 2022, 0.2, 0)])
    assert run_research(tmp_path)["status"] == "refused"
    assert len(fakes.calls) == 7


def test_legacy_rerun_refreshes_the_trial_log_and_the_published_dev_run(
    tmp_path, fakes, monkeypatch
):
    trials = tmp_path / "results" / "trials.jsonl"
    first = run_research(tmp_path, dev_only=True)
    folder = research_folder(tmp_path)
    old_total = sum(r.net_r for r in trial_log.read_all(trials))
    old_run = first["chosen"]["dev_run"]
    for card in (folder / "variants").glob("*/scorecard.json"):  # a legacy per-trade scorecard
        data = json.loads(card.read_text(encoding="utf-8"))
        data.pop("day_sharpe")
        card.write_text(json.dumps(data), encoding="utf-8")
    original = fakes.run

    def doubled(*args, **kw):
        result = original(*args, **kw)
        trades = tuple(replace_r(t) for t in result.trades)
        return type(result)(**{**vars(result), "trades": trades, "runs": {
            s: type(r)(**{**vars(r), "trades": tuple(replace_r(t) for t in r.trades)})
            for s, r in result.runs.items()}})  # fmt: skip

    def replace_r(t):
        return type(t)(**{**vars(t), "r_net": 2 * t.r_net, "r_gross": 2 * t.r_gross})

    monkeypatch.setattr(fakes, "run", doubled)
    second = run_research(tmp_path, dev_only=True)
    assert sum(r.net_r for r in trial_log.read_all(trials)) == pytest.approx(2 * old_total)
    assert second["chosen"]["id"] == first["chosen"]["id"]
    run = tmp_path / "results" / second["chosen"]["dev_run"]
    published = read_csv(run / "trades.csv")
    stored = read_csv(folder / "variants" / second["chosen"]["id"] / "trades.csv")
    assert [r["r_net"] for r in published] == [r["r_net"] for r in stored]
    assert old_run and run.is_dir()
