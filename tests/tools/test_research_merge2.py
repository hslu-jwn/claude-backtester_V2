"""Spec: research-runner.md, grid merge 2.

Test-case list (before implementation):
1. Sample SE, empty/singleton results, UTC union across symbols, weekend clipping,
   inclusive period dates, zero weekday denominator, mean holds, invalid durations.
2. Sensitivity defaults on; false and compare_to validation; diagnostic options keep ID.
3. Integer minimum steps/rounding, floats/zero, booleans excluded, config rejection.
4. Default-on development neighbours, unique trial logging, partial/full resume,
   disabled mode, sharp/gentle reports and unchanged selection/DSR/test-once guard.
5. Twins match resolved defaults excluding family base only; deduplicated and sampled
   occurrences, unmatched rows, matched-pair averages and strict lift comparison.
6. Haircut development/test lines, configurable/invalid bounds, legacy empty CSV cells.
"""

import json
import math
from datetime import UTC, date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from test_research import GRID as LEGACY_GRID
from test_research import fakes as research_fakes
from test_research import read_csv, research_folder, write_grid
from test_research import run_research as run_legacy

from backtester.analytics.scorecard import SCORE_KEYS, scorecard
from backtester.tools import research_grid

# the legacy fixture switches sensitivity off; these tests need the default (on)
GRID = "".join(line for line in LEGACY_GRID.splitlines(True) if "sensitivity" not in line)


def run_research(tmp_path, text=GRID, **kw):
    return run_legacy(tmp_path, text, **kw)


fakes = research_fakes


def trade(a, b, r=1):
    return SimpleNamespace(
        symbol="US500", entry_time=a, exit_time=b, r_net=r, r_gross=r, planned_r=None
    )


def test_scorecard_union_weekdays_and_se():
    friday = datetime(2020, 1, 3, tzinfo=UTC)
    monday = friday + timedelta(days=3)
    trades = [
        trade(friday + timedelta(hours=12), monday + timedelta(hours=12), -1),
        trade(monday, monday + timedelta(hours=18), 3),
    ]
    card = scorecard(trades, start=friday.date(), end=monday.date())
    assert card["se_avg_r"] == pytest.approx(2)
    assert card["avg_hold_hours"] == 45  # (72 + 18) / 2
    assert card["time_in_market"] == pytest.approx(30 / 48)
    assert SCORE_KEYS[-3:] == ("se_avg_r", "time_in_market", "avg_hold_hours")


def test_scorecard_clipping_empty_singleton_and_utc():
    d = datetime(2020, 1, 6, tzinfo=UTC)
    t = trade(d - timedelta(hours=2), d + timedelta(hours=26))
    t.entry_time = t.entry_time.astimezone(timezone(timedelta(hours=3)))
    card = scorecard([t], start=d.date(), end=d.date())
    assert card["time_in_market"] == 1
    assert card["avg_hold_hours"] == 28
    assert card["se_avg_r"] is None
    assert scorecard([trade(d, d + timedelta(hours=6))])["time_in_market"] == 0.25
    empty = scorecard([], start=d.date(), end=d.date())
    assert empty["time_in_market"] == 0
    assert empty["se_avg_r"] is empty["avg_hold_hours"] is None
    assert scorecard([], start=date(2020, 1, 4), end=date(2020, 1, 5))["time_in_market"] is None
    assert scorecard([])["time_in_market"] is None
    with pytest.raises(ValueError, match="exit"):
        scorecard([trade(d, d - timedelta(seconds=1))])


def test_options_and_identity(tmp_path):
    a = research_grid.load_grid(write_grid(tmp_path, GRID))
    b = research_grid.load_grid(
        write_grid(tmp_path, GRID.replace("min_trades = 4", "min_trades = 4\nsensitivity = false"))
    )
    assert a.sensitivity is True and b.sensitivity is False
    assert research_grid.grid_id(a, research_grid.expand(a)[0]) == research_grid.grid_id(
        b, research_grid.expand(b)[0]
    )
    with pytest.raises(research_grid.GridError, match="sensitivity"):
        research_grid.load_grid(
            write_grid(tmp_path, GRID.replace("min_trades = 4", "min_trades = 4\nsensitivity = 1"))
        )


def test_neighbour_values_and_rejections(tmp_path):
    from backtester.tools.research_stability import neighbours

    text = GRID[: GRID.index("[grid]")] + "[grid]\nrange_minutes = [1]\ntarget_r = [0]\n"
    spec = research_grid.load_grid(write_grid(tmp_path, text))
    chosen = research_grid.expand(spec)[0][0]
    rows = neighbours(spec, chosen)
    ints = [r for r in rows if r["setting"] == "range_minutes"]
    assert [r["value"] for r in ints] == [0, 0, 2, 2]
    assert [r["status"] for r in ints] == ["skipped", "skipped", "pending", "pending"]
    assert all(r["reason"] for r in ints[:2])
    assert ints[2]["id"] == ints[3]["id"]
    assert [r["value"] for r in rows if r["setting"] == "target_r"] == [0, 0, 0, 0]
    text = text.replace("target_r = [0]", 'target_r = [1.5]\n"engine.costs.swap_enabled" = [true]')
    spec = research_grid.load_grid(write_grid(tmp_path, text))
    rows = neighbours(spec, research_grid.expand(spec)[0][0])
    assert {r["setting"] for r in rows} == {"range_minutes", "target_r"}
    assert [r["value"] for r in rows if r["setting"] == "target_r"] == pytest.approx(
        [1.2, 1.35, 1.65, 1.8]
    )


def test_sensitivity_runner_resume_guard_and_dsr(tmp_path, fakes):
    out = run_research(tmp_path, dev_only=True)
    folder = research_folder(tmp_path)
    rows = read_csv(folder / "sensitivity.csv")
    assert len(rows) == 8 and all(r["status"] == "done" for r in rows)
    assert len(fakes.calls) == 14
    assert all(c.end == date(2021, 9, 13) for c in fakes.calls)
    assert out["chosen"]["id"] == "v0005"
    assert all(float(r["net_r_share"]) > 0.5 for r in rows)
    assert "gentle" in (folder / "report.md").read_text()
    trials = [json.loads(s) for s in (tmp_path / "results/trials.jsonl").read_text().splitlines()]
    assert sum(t["family"] == "idea-sensitivity" for t in trials) == 8
    run_research(tmp_path, dev_only=True)
    assert len(fakes.calls) == 14
    out = run_research(tmp_path)
    assert len(fakes.calls) == 15
    assert out["test"]["n_variants"] == 6
    assert run_research(tmp_path)["status"] == "refused"
    assert len(fakes.calls) == 15
    report = (folder / "report.md").read_text()
    assert report.count("Live expectation: 50-75 %") == 2
    assert "0.113 to 0.169 R per trade" in report


def test_partial_sensitivity_resume(tmp_path, fakes):
    fakes.fail_after = 8  # six grid runs, two neighbours
    with pytest.raises(RuntimeError, match="interrupted"):
        run_research(tmp_path, dev_only=True)
    folder = research_folder(tmp_path)
    assert len(list((folder / "sensitivity").glob("*/scorecard.json"))) == 2
    fakes.fail_after = None
    run_research(tmp_path, dev_only=True)
    assert len(fakes.calls) == 14
    assert len((tmp_path / "results/trials.jsonl").read_text().splitlines()) == 14


def test_sensitivity_batches_pending_neighbours(tmp_path, fakes, monkeypatch):
    from backtester.tools import research

    batches = []

    def run_many(symbols, start, end, settings_list, sources, workers):
        batches.append(len(settings_list))
        yield from fakes.run_many(symbols, start, end, settings_list, sources, workers)

    monkeypatch.setattr(research, "run_period_many", run_many)
    run_research(tmp_path, dev_only=True)
    assert batches == [6, 8]  # shared candle loading for all pending neighbours


def test_sensitivity_threshold_zero_baseline_and_no_numeric_settings():
    from backtester.tools.research_stability import haircut, sensitivity_summary

    row = {"setting": "target_r", "status": "done", "net_r": 5, "net_r_share": 0.5}
    assert sensitivity_summary([row], 10)["status"] == "gentle"
    assert sensitivity_summary([{**row, "net_r_share": 0.499}], 10)["failed_settings"] == [
        "target_r"
    ]
    assert sensitivity_summary([{**row, "net_r": 0}], 10)["status"] == "sharp"
    assert sensitivity_summary([{**row, "net_r_share": None}], 0)["status"] == "sharp"
    assert sensitivity_summary([], 10)["status"] == "sharp"
    assert haircut(None, (0.5, 0.75)).endswith("= n/a")
    assert haircut(-1, (0.5, 0.75)).endswith("= no positive edge to discount")
    assert haircut(0.2, (0.5, 0.75)).endswith("= 0.100 to 0.150 R per trade")


def test_disabled_and_legacy_scorecard_cells(tmp_path, fakes):
    text = GRID.replace("min_trades = 4", "min_trades = 4\nsensitivity = false")
    run_research(tmp_path, text, dev_only=True)
    folder = research_folder(tmp_path)
    assert len(fakes.calls) == 6
    assert not (folder / "sensitivity.csv").exists()
    for path in (folder / "variants").glob("*/scorecard.json"):
        data = json.loads(path.read_text())
        for key in SCORE_KEYS[-3:]:
            data["scorecard"].pop(key)
        path.write_text(json.dumps(data))
    run_research(tmp_path, text, dev_only=True)
    assert all(
        r["se_avg_r"] == r["time_in_market"] == r["avg_hold_hours"] == ""
        for r in read_csv(folder / "variants.csv")
    )


TWINS = """strategy = "opening_range"
symbols = ["US500"]
min_trades = 4
sensitivity = false
[[grids]]
name = "plain"
[grids.grid]
range_minutes = [5, 15]
[[grids]]
name = "filtered"
compare_to = "plain"
[grids.base]
target_r = 1
[grids.grid]
range_minutes = [5, 15, 30]
"""


@pytest.mark.parametrize("target", ["missing", "filtered", 1])
def test_invalid_twin_target(tmp_path, target):
    text = TWINS.replace('compare_to = "plain"', f"compare_to = {json.dumps(target)}")
    with pytest.raises(research_grid.GridError, match="compare_to"):
        research_grid.load_grid(write_grid(tmp_path, text))


def test_twins_runner_and_unmatched(tmp_path, fakes):
    run_research(tmp_path, TWINS, dev_only=True)
    folder = research_folder(tmp_path)
    rows = read_csv(folder / "twins.csv")
    assert len(rows) == 3
    assert [r["status"] for r in rows] == ["matched", "matched", "unmatched"]
    assert [r["twin_id"] for r in rows] == ["v0000", "v0001", ""]
    assert all(float(r["difference"]) == pytest.approx(0.003) for r in rows[:2])
    info = json.loads((folder / "research.json").read_text())
    summary = info["twins"][0]
    assert summary["mean_net_r"] == pytest.approx(0.303)
    assert summary["mean_twin_net_r"] == pytest.approx(0.3)
    assert summary["lifts_average"] == "yes"


def test_deduplicated_twins_and_sampled_out(tmp_path):
    from backtester.tools.research_stability import twin_rows

    spec = research_grid.load_grid(
        write_grid(tmp_path, TWINS.replace("target_r = 1", "target_r = 0"))
    )
    variants = research_grid.expand(spec)[0]
    rows = [{"variant_id": v.id, "net_r": 2, "trades": 4} for v in variants]
    pairs, summaries = twin_rows(spec, variants, rows)
    assert [p["status"] for p in pairs] == ["matched", "matched", "unmatched"]
    assert summaries[0]["lifts_average"] == "no"
    pairs, summaries = twin_rows(spec, variants[:1], rows[:1])
    assert pairs[0]["status"] == "matched"
    assert pairs[1]["status"] == "unmatched"
    assert summaries[0]["matched"] == 1


def test_sharp_rejected_and_zero_baseline(tmp_path, fakes):
    text = GRID[: GRID.index("[grid]")] + "[grid]\nrange_minutes = [1]\n"
    run_research(tmp_path, text, dev_only=True)
    folder = research_folder(tmp_path)
    report = (folder / "report.md").read_text()
    assert "sharp" in report and "range_minutes" in report
    assert len(fakes.calls) == 2  # repeated integer neighbours share a trial


@pytest.mark.parametrize("bounds", [(-0.1, 0.7), (0.8, 0.5), (0.5, 1.1), (math.nan, 0.7)])
def test_invalid_haircut_bounds(bounds):
    with pytest.raises(ValueError, match="live_expectation_range"):
        research_grid.ResearchConfig(live_expectation_range=bounds)


def test_configured_haircut(tmp_path, fakes):
    run_research(
        tmp_path,
        GRID,
        dev_only=True,
        config=research_grid.ResearchConfig(live_expectation_range=(0.25, 0.5)),
    )
    report = (research_folder(tmp_path) / "report.md").read_text()
    assert "Live expectation: 25-50 %" in report
    assert "0.056 to 0.113 R per trade" in report
