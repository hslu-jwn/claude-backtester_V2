"""Cases: MTM-only grid matrix; excludes sensitivity/tests; flags on chosen only;
resume recomputes without backtests/trials/selection changes; unavailable series;
threshold equality; report and effective trade count from saved intervals.
"""

# ruff: noqa: F811
import json

import numpy as np

from backtester.analytics import trial_log
from backtester.analytics.scorecard import FLAG_LABELS
from backtester.tools import research, research_significance
from tests.tools.test_research import (  # noqa: F401
    GRID,
    fakes,
    make_trade,
    read_csv,
    research_folder,
    run_research,
)


def test_runner_resume_and_exclusions(tmp_path, fakes, monkeypatch):
    monkeypatch.setattr(research, "read_trades", lambda p: [make_trade("US500", 2015, 1, 0)])
    seen = []

    def rc(matrix, *args):
        seen.append(matrix.copy())
        return {"p_value": 0.8, "reason": None}

    monkeypatch.setattr(research_significance, "reality_check", rc)
    monkeypatch.setattr(
        research_significance,
        "cscv_pbo",
        lambda *a: {"pbo": 0.5, "median_oos_rank": 0.5, "reason": None},
    )
    out = run_research(
        tmp_path, GRID.replace("sensitivity = false", "sensitivity = true"), dev_only=True
    )
    folder = research_folder(tmp_path)
    saved = json.loads((folder / "significance.json").read_text())
    assert saved["effective_trials"]["n"] == 6
    assert saved["effective_trades"]["effective_trades"] == 1
    rows = read_csv(folder / "variants.csv")
    chosen = next(row for row in rows if row["variant_id"] == out["chosen"]["id"])
    assert "rc_not_significant" in chosen["flags"] and "pbo_high" in chosen["flags"]
    assert all("pbo_high" not in r["flags"] for r in rows if r is not chosen)
    records = trial_log.read_all(tmp_path / "results" / "trials.jsonl")
    grid_records = [
        next(
            r
            for r in records
            if r.series
            == (folder / "variants" / vid / "daily.csv")
            .relative_to(tmp_path / "results")
            .as_posix()
        )
        for vid in saved["variant_ids"]
    ]
    _, expected = trial_log.series_matrix(grid_records, "net_r_mtm", tmp_path / "results")
    np.testing.assert_array_equal(seen[0], expected)
    calls = len(fakes.calls)
    log = (tmp_path / "results" / "trials.jsonl").read_bytes()
    (folder / "significance.json").unlink()
    again = run_research(
        tmp_path, GRID.replace("sensitivity = false", "sensitivity = true"), dev_only=True
    )
    assert again["chosen"] == out["chosen"] and len(fakes.calls) == calls
    assert (tmp_path / "results" / "trials.jsonl").read_bytes() == log
    assert json.loads((folder / "significance.json").read_text()) == saved
    assert "Is the best variant better than luck?" in (folder / "report.md").read_text()


def test_flag_boundaries():
    assert research_significance.warning_flags({"p_value": 0.05}, {"pbo": 0.49}) == []
    assert research_significance.warning_flags({"p_value": None}, {"pbo": None}) == []
    assert research_significance.warning_flags({"p_value": 0.051}, {"pbo": 0.5}) == [
        "rc_not_significant",
        "pbo_high",
    ]
    assert "rc_not_significant" in FLAG_LABELS and "pbo_high" in FLAG_LABELS


def test_missing_series_unavailable(tmp_path):
    result = research_significance.calculate(tmp_path, ["v1", "v2"], None)
    assert result["reality_check"]["p_value"] is None
    assert result["reality_check"]["reason"]
    assert result["pbo"]["pbo"] is None
