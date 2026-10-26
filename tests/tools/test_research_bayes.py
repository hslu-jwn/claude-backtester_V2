"""Cases before code: chosen-only flag; saved dev/test Bayes; no extra backtests,
test guard, unchanged trials/selection on resume; twin family orientation and
dedup resolution; unmatched families; readable report with priors and limitations.
"""

# ruff: noqa: F811
import json

import pytest

from backtester.analytics.scorecard import FLAG_LABELS
from backtester.tools import research, research_bayes, research_grid, research_stability
from tests.tools.test_research import (  # noqa: F401
    GRID,
    fakes,
    make_trade,
    read_csv,
    research_folder,
    run_research,
)


def test_runner_resume(tmp_path, fakes, monkeypatch):
    monkeypatch.setattr(
        research,
        "read_trades",
        lambda p: [
            make_trade("US500", 2015, 1, 0),
            make_trade("US500", 2015, -1, 1),
        ],
    )
    out = run_research(tmp_path)
    folder = research_folder(tmp_path)
    saved = json.loads((folder / "bayes.json").read_text())
    assert saved["development"]["n"] == 2
    assert len(saved["tests"]) == 1
    rows = read_csv(folder / "variants.csv")
    assert all(
        ("bayes_weak" in r["flags"]) == (r["variant_id"] == out["chosen"]["id"]) for r in rows
    )
    assert "bayes_weak" in FLAG_LABELS
    calls = len(fakes.calls)
    log = (tmp_path / "results" / "trials.jsonl").read_bytes()
    (folder / "bayes.json").unlink()
    again = run_research(tmp_path)
    assert again["status"] == "refused" and again["chosen"] == out["chosen"]
    assert len(fakes.calls) == calls
    assert (tmp_path / "results" / "trials.jsonl").read_bytes() == log
    assert json.loads((folder / "bayes.json").read_text()) == saved
    text = (folder / "report.md").read_text()
    for term in ("Bayesian view", "1:50", "strong", "development", "test 1"):
        assert term in text


def test_twin_family_saved_occurrences(tmp_path, fakes, monkeypatch):
    monkeypatch.setattr(
        research,
        "read_trades",
        lambda p: [
            make_trade("US500", 2015, 1, 0),
            make_trade("US500", 2015, -1, 1),
        ],
    )
    grid = """strategy = "opening_range"
symbols = ["US500"]
sensitivity = false
min_trades = 1
[[grids]]
name = "plain"
[grids.grid]
range_minutes = [5, 15]
[[grids]]
name = "filter"
compare_to = "plain"
[grids.base]
target_r = 1
[grids.grid]
range_minutes = [5, 15]
"""
    run_research(tmp_path, grid, dev_only=True)
    data = json.loads((research_folder(tmp_path) / "bayes.json").read_text())
    family = data["twins"][0]
    assert family["family"] == "filter" and family["compare_to"] == "plain"
    assert family["matched"] == 2
    assert family["p_mean_b_gt_a"] == 0.5 or abs(family["p_mean_b_gt_a"] - 0.5) < 0.015
    assert len(family["pairs"]) == 2


def test_no_comparisons_does_not_expand_full_product(tmp_path, monkeypatch):
    from tests.tools.test_research import write_grid

    spec = research_grid.load_grid(write_grid(tmp_path))
    variants = research_grid.expand(spec)[0]

    def forbidden(*args):
        raise AssertionError("no compare_to: must not enumerate all family occurrences")

    monkeypatch.setattr(research_bayes, "family_variants", forbidden)
    data = research_bayes.calculate(
        tmp_path,
        tmp_path,
        spec,
        variants,
        None,
        [],
        [],
        reader=lambda p: [],
    )
    assert data == {"development": None, "tests": [], "twins": [], "flags": []}


@pytest.mark.parametrize("sample", [False, True])
def test_deduplicated_and_sampled_pairs(tmp_path, sample):
    from tests.tools.test_research import write_grid

    text = """strategy = "opening_range"
symbols = ["US500"]
[[grids]]
name = "plain"
[grids.grid]
range_minutes = [5, 15]
[[grids]]
name = "copy"
compare_to = "plain"
[grids.grid]
range_minutes = [5, 15]
"""
    if sample:
        text = text.replace('symbols = ["US500"]', 'symbols = ["US500"]\nmax_variants = 1')
    spec = research_grid.load_grid(write_grid(tmp_path, text))
    variants = research_grid.expand(spec)[0]
    rows = [{"variant_id": v.id, "net_r": 0, "trades": 2} for v in variants]
    pairs, _ = research_stability.twin_rows(spec, variants, rows)
    reads = []

    def reader(path):
        reads.append(path.name)
        assert path.name in {v.id for v in variants}
        return [make_trade("US500", 2015, 1, 0), make_trade("US500", 2015, -1, 1)]

    data = research_bayes.calculate(
        tmp_path,
        tmp_path,
        spec,
        variants,
        None,
        [],
        pairs,
        reader=reader,
    )
    twin = data["twins"][0]
    assert twin["matched"] == len(variants)
    assert twin["unmatched"] == (1 if sample else 0)
    assert len(reads) == len(variants)  # aliases reuse saved result and posterior
    assert all(p["a_saved_id"] == p["b_saved_id"] for p in twin["pairs"])
