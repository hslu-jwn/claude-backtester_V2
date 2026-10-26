"""Critical cases before implementation, research-runner.md > Walk-forward:
1. Per-window rates, WFE, DD, stability, chosen comparison, chained scorecard.
2. Nonpositive training excluded from BOTH overall WFE means, not OOS scorecard.
3. Partial final month uses actual length; empty windows give a reason.
4. Grid validation, diagnostic identity, nine study rows and report tables.
5. Saved-only resume, study activation and stale-artifact cleanup.
"""

from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest
from test_research import GRID, read_csv, research_folder, run_research, write_grid
from test_research import fakes as research_fakes

from backtester.tools import research_grid
from backtester.tools import research_walk_forward as wf

fakes = research_fakes


def trade(year, month, r):
    entry = datetime(year, month, 2, tzinfo=UTC)
    return SimpleNamespace(
        entry_time=entry,
        exit_time=entry + timedelta(hours=1),
        r_net=r,
        r_gross=r,
        swap_r=0,
        symbol="XAUUSD",
        planned_r=None,
    )


def test_window_metrics_and_exclusion():
    trades = [trade(2018, 2, -2), trade(2019, 2, 4), trade(2020, 2, -1)]
    rows, info = wf.summarize_walk_forward(
        {"a": trades},
        "a",
        date(2018, 1, 1),
        date(2020, 12, 31),
        "rolling",
        train_months=12,
        test_months=12,
    )
    assert rows[0]["wfe"] is None
    assert rows[1]["wfe"] == pytest.approx(-1 / 4)
    assert rows[1]["test_net_r_per_month"] == pytest.approx(-1 / 12)
    assert rows[1]["max_dd_r"] == 1
    assert rows[1]["chosen_net_r"] == -1
    assert info["efficiency"] == pytest.approx(-1 / 4)
    assert info["scorecard"]["net_r"] == 3
    assert info["positive_window_share"] == 0.5
    assert info["pick_changes"] == 0 and info["pick_change_share"] == 0
    assert info["chained_net_r_per_month"] == pytest.approx(3 / 24)


def test_partial_rate_and_short_reason():
    rows, info = wf.summarize_walk_forward(
        {"a": [trade(2020, 1, 1), trade(2020, 2, 2)]},
        None,
        date(2020, 1, 1),
        date(2020, 2, 14),
        "anchored",
        train_months=1,
        test_months=1,
    )
    assert rows[0]["test_net_r_per_month"] == pytest.approx(2 / (14 / 29))
    assert info["pick_change_share"] is None
    rows, info = wf.summarize_walk_forward(
        {"a": []}, None, date(2020, 1, 1), date(2020, 2, 14), "anchored"
    )
    assert rows == [] and info["reason"]
    assert "No" in "\n".join(wf.report(info))


def test_yearly_summary_equivalence_and_pick_changes():
    variants = {
        "a": [trade(2018, 2, 4), trade(2019, 2, -2), trade(2020, 2, 3)],
        "b": [trade(2018, 2, 2), trade(2019, 2, 4), trade(2020, 2, -1)],
    }
    args = (variants, "b", date(2018, 1, 1), date(2020, 12, 31), "anchored")
    old_rows, old = wf.summarize_walk_forward(*args, 3)
    rows, info = wf.summarize_walk_forward(*args, train_months=12, test_months=12)
    for key in ("picked_variant", "train_net_r", "net_r", "chosen_net_r", "trades"):
        assert [r[key] for r in rows] == [r[key] for r in old_rows]
    assert info["efficiency"] == pytest.approx(old["efficiency"])
    assert info["scorecard"] == old["scorecard"]
    assert (info["pick_changes"], info["pick_change_share"]) == (1, 1)


def test_empty_zero_training_and_study_report_legacy():
    rows, info = wf.summarize_walk_forward(
        {"a": []}, None, date(2018, 1, 1), date(2020, 12, 31), "anchored"
    )
    assert rows[0]["wfe"] is None and info["efficiency"] is None
    assert info["positive_window_share"] == 0
    _, legacy = wf.summarize_walk_forward(
        {"a": []}, None, date(2018, 1, 1), date(2020, 12, 31), "anchored", 3
    )
    legacy["study"] = wf.window_study(
        {"a": []}, None, date(2018, 1, 1), date(2020, 12, 31), "anchored"
    )
    assert "| train_months |" in "\n".join(wf.report(legacy))


@pytest.mark.parametrize(
    "option",
    [
        "train_months = 0",
        "test_months = true",
        "step_months = 1.5",
        "test_months = 6\nstep_months = 3",
        "walk_forward_study = 1",
        "train_years = 2\ntrain_months = 12",
    ],
)
def test_grid_validation(tmp_path, option):
    with pytest.raises(research_grid.GridError):
        research_grid.load_grid(write_grid(tmp_path, GRID.replace("[base]", option + "\n[base]")))


def test_grid_defaults_and_identity(tmp_path):
    old = research_grid.load_grid(write_grid(tmp_path))
    new = research_grid.load_grid(
        write_grid(
            tmp_path,
            GRID.replace(
                "[base]",
                'walk_forward = "rolling"\ntrain_months = 12\ntest_months = 3\n'
                "step_months = 6\nwalk_forward_study = true\n[base]",
            ),
        )
    )
    assert (old.train_months, old.test_months, old.step_months) == (24, 6, 6)
    assert (new.train_months, new.test_months, new.step_months) == (12, 3, 6)
    assert research_grid.grid_id(old, research_grid.expand(old)[0]) == research_grid.grid_id(
        new, research_grid.expand(new)[0]
    )


def test_study_resume_and_cleanup(tmp_path, fakes, monkeypatch):
    monkeypatch.setattr(wf, "read_trades", lambda folder: [trade(2015, 2, 2), trade(2018, 2, -1)])
    text = GRID.replace("[base]", "walk_forward_study = true\n[base]")
    run_research(tmp_path, text, dev_only=True)
    folder = research_folder(tmp_path)
    rows = read_csv(folder / "walk_forward_study.csv")
    assert len(rows) == 9
    assert {(int(r["train_months"]), int(r["test_months"])) for r in rows} == {
        (a, b) for a in (12, 24, 36) for b in (3, 6, 12)
    }
    report = (folder / "report.md").read_text(encoding="utf-8")
    assert "| window |" in report and "| train_months |" in report
    calls = len(fakes.calls)
    run_research(tmp_path, text, dev_only=True)
    assert len(fakes.calls) == calls
    run_research(tmp_path, GRID, dev_only=True)
    assert not (folder / "walk_forward_study.csv").exists()
    assert not (folder / "walk_forward.csv").exists()
