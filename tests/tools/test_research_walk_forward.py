"""Test cases (spec first, before implementation):
1. Grid modes/positive train years validate and diagnostic options preserve identity.
2. Saved development trades yield yearly max-net picks, stable ties and rolling windows.
3. Chained scorecard, annual efficiency and chosen comparison are exact; no/losing training
   and empty years are handled, and post-development entries never participate.
4. CLI flag enables anchored diagnostics; resume uses saved trades without new runs.
5. Standalone study preserves session loader and CLI period guard without backtesting.
6. Replacement grids reproduce complete former sweep settings and resolve without sampling.
"""

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest
from test_research import GRID, read_csv, research_folder, run_research, write_grid
from test_research import fakes as research_fakes

from backtester.tools import research, research_grid

fakes = research_fakes


def test_grid_options_and_identity(tmp_path):
    original = research_grid.load_grid(write_grid(tmp_path, GRID))
    spec = research_grid.load_grid(
        write_grid(
            tmp_path, GRID.replace("[base]", 'walk_forward = "rolling"\ntrain_years = 2\n[base]')
        )
    )
    assert spec.walk_forward == "rolling" and spec.train_years == 2
    assert research_grid.grid_id(spec, research_grid.expand(spec)[0]) == research_grid.grid_id(
        original, research_grid.expand(original)[0]
    )


@pytest.mark.parametrize(
    "option",
    [
        "walk_forward = true",
        'walk_forward = "bad"',
        "train_years = 0",
        "train_years = true",
        "train_years = 1.5",
    ],
)
def test_invalid_options(tmp_path, option):
    with pytest.raises(research_grid.GridError):
        research_grid.load_grid(write_grid(tmp_path, GRID.replace("[base]", option + "\n[base]")))


def trade(year, r):
    entry = datetime(year, 3, 1, tzinfo=UTC)
    return SimpleNamespace(
        symbol="XAUUSD",
        planned_r=None,
        entry_time=entry,
        exit_time=entry + timedelta(hours=1),
        r_net=r,
        r_gross=r,
        swap_r=0,
    )


def test_picks_efficiency_and_development_boundary():
    from backtester.tools.research_walk_forward import summarize_walk_forward

    variants = {
        "a": [trade(2018, 4), trade(2019, -2), trade(2020, 3), trade(2022, 999)],
        "b": [trade(2018, 2), trade(2019, 4), trade(2020, -1)],
    }
    rows, info = summarize_walk_forward(
        variants, "b", date(2018, 1, 1), date(2020, 12, 31), "anchored", 3
    )
    assert [r["picked_variant"] for r in rows] == ["a", "b"]
    assert [r["net_r"] for r in rows] == [-2, -1]
    assert [r["chosen_net_r"] for r in rows] == [4, -1]
    assert info["scorecard"]["net_r"] == -3
    assert info["efficiency"] == pytest.approx((-3 / 2) / ((4 + 6 / 2) / 2))
    rolling, _ = summarize_walk_forward(
        variants, None, date(2018, 1, 1), date(2020, 12, 31), "rolling", 1
    )
    assert rolling[1]["train_net_r"] == 4
    assert rolling[0]["chosen_net_r"] is None


def test_empty_ties_and_nonpositive_training():
    from backtester.tools.research_walk_forward import summarize_walk_forward

    rows, info = summarize_walk_forward(
        {"a": [], "b": []}, None, date(2018, 1, 1), date(2020, 9, 13), "anchored", 3
    )
    assert len(rows) == 2 and all(r["picked_variant"] == "a" for r in rows)
    assert info["efficiency"] is None and info["scorecard"]["net_r"] == 0
    rows, info = summarize_walk_forward(
        {"a": [trade(2018, -1)]}, None, date(2018, 1, 1), date(2018, 9, 13), "anchored", 3
    )
    assert rows == [] and info["efficiency"] is None


def test_cli_resume_no_additional_runs(tmp_path, fakes, monkeypatch):
    assert research.parse_args(["x.toml", "--walk-forward"]).walk_forward
    from backtester.tools import research_walk_forward

    monkeypatch.setattr(
        research_walk_forward, "read_trades", lambda folder: [trade(2015, 2), trade(2018, -1)]
    )
    text = GRID.replace("[base]", 'walk_forward = "rolling"\ntrain_years = 1\n[base]')
    run_research(tmp_path, text, dev_only=True)
    folder = research_folder(tmp_path)
    assert (folder / "walk_forward.csv").exists()
    assert "Walk-forward" in (folder / "report.md").read_text(encoding="utf-8")
    calls = len(fakes.calls)
    run_research(tmp_path, text, dev_only=True)
    assert len(fakes.calls) == calls
    assert read_csv(folder / "walk_forward.csv")


def test_unclosed_training_trade_cannot_pick_the_winner():
    from backtester.tools.research_walk_forward import summarize_walk_forward

    late = trade(2018, 100)
    late.exit_time = datetime(2019, 1, 1, tzinfo=UTC)
    variants = {"a": [late, trade(2019, -8)], "b": [trade(2018, 1), trade(2019, 2)]}
    rows, info = summarize_walk_forward(
        variants, "a", date(2018, 1, 1), date(2019, 9, 13), "anchored", 3
    )
    assert rows[0]["picked_variant"] == "b"
    assert rows[0]["train_net_r"] == 1
    assert info["scorecard"]["net_r"] == 2
    assert info["efficiency"] == 2


def test_cli_flag_forwarded_to_runner(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(
        research,
        "run_research",
        lambda *a, **kw: (
            seen.append(kw) or {"message": "done", "folder": tmp_path, "status": "dev_only"}
        ),
    )
    assert research.main(["x.toml", "--dev-only", "--walk-forward"]) == 0
    assert seen[0]["walk_forward"] is True and seen[0]["dev_only"] is True


def test_test_guard_and_trials_unchanged_by_walk_forward(tmp_path, fakes, monkeypatch):
    from backtester.tools import research_walk_forward

    monkeypatch.setattr(
        research_walk_forward, "read_trades", lambda folder: [trade(2015, 2), trade(2018, -1)]
    )
    first = run_research(tmp_path)
    folder = research_folder(tmp_path)
    trials = (tmp_path / "results" / "trials.jsonl").read_text(encoding="utf-8")
    calls = len(fakes.calls)
    second = run_research(tmp_path, walk_forward=True)
    assert second["status"] == "refused"
    assert second["chosen"] == first["chosen"]
    assert len(fakes.calls) == calls
    assert (tmp_path / "results" / "trials.jsonl").read_text(encoding="utf-8") == trials
    assert read_csv(folder / "walk_forward.csv")
    run_research(tmp_path, dev_only=True)
    assert not (folder / "walk_forward.csv").exists()
    assert "Walk-forward" not in (folder / "report.md").read_text(encoding="utf-8")
