"""Swept settings and persisted decay/extreme reports; synthetic development trades only."""

import json
from dataclasses import replace

import pytest

from backtester.tools import research_grid as grid
from tests.tools.test_research import fakes as research_fakes
from tests.tools.test_research import read_csv, run_research

fakes = research_fakes


def spec(**kw):
    return grid.GridSpec("checks", "opening_range", ("US500",), {}, {}, 0, 200, 1, **kw)


def test_swept_settings_are_distinct_within_families():
    assert grid.swept_params(replace(spec(), grid={"a": [1], "b": [[1], [1]]})) == []
    assert grid.swept_params(replace(spec(), grid={"b": [1, 2], "a": [1, 2]})) == ["a", "b"]
    families = (
        grid.Family("a", {}, {"same": [1], "x": [1, 2]}),
        grid.Family("b", {}, {"same": [1], "y": [1, 2]}),
    )
    assert grid.swept_params(spec(grids=families)) == ["x", "y"]


def test_parameter_limit_validation():
    with pytest.raises(ValueError, match="max_free_params"):
        grid.ResearchConfig(max_free_params=0)
    assert grid.ResearchConfig().decay_t == -2


def test_equal_numeric_values_are_not_free():
    assert grid.swept_params(replace(spec(), grid={"a": [1, 1.0]})) == []


@pytest.mark.parametrize("count", [4, 5])
def test_parameter_warning_on_every_row(tmp_path, fakes, count):
    axes = {
        "range_minutes": "[5, 15]",
        "target_r": "[0, 1]",
        "warmup_days": "[7, 14]",
        "band_atr": "[0.5, 1]",
        "atr_period": "[10, 14]",
    }
    text = (
        'strategy="opening_range"\nsymbols=["US500"]\nmin_trades=1\n'
        "sensitivity=false\nmonkeys=false\nentry_screen=false\n[grid]\n"
    )
    text += "\n".join(f'"{k}"={v}' for k, v in list(axes.items())[:count])
    out = run_research(tmp_path, text, dev_only=True)
    info = json.loads((out["folder"] / "research.json").read_text())
    assert info["free_params"] == count
    assert info["swept_params"] == sorted(list(axes)[:count])
    assert ("too_many_parameters" in info.get("flags", [])) == (count > 4)
    assert all(
        ("too_many_parameters" in r["flags"]) == (count > 4)
        for r in read_csv(out["folder"] / "variants.csv")
    )
    assert f"Free parameters: {count} (limit 4):" in (out["folder"] / "report.md").read_text()


def test_decline_flag_and_diagnostic_files(tmp_path, fakes):
    from tests.tools.test_research import GRID, make_trade

    original = fakes.run

    def declining(*args, **kwargs):
        result = original(*args, **kwargs)
        values = [12, 10, 11, 8, 9, 6, 7, 4, 5, 2, 3, 0]
        trades = []
        for month, value in enumerate(values, 1):
            t = make_trade("US500", 2020, value, 0)
            t.entry_time = t.entry_time.replace(month=month)
            t.exit_time = t.entry_time.replace(hour=16)
            trades.append(t)
        result.trades = tuple(trades)
        return result

    fakes.run = declining
    out = run_research(tmp_path, GRID, dev_only=True)
    folder = out["folder"]
    slopes = read_csv(folder / "returns_slope.csv")
    assert len(slopes) == 1 and slopes[0]["period"] == "development"
    assert slopes[0]["variant_id"] == out["chosen"]["id"] and slopes[0]["test_run"] == "0"
    assert float(slopes[0]["t_stat"]) <= -2
    rows = read_csv(folder / "variants.csv")
    assert [r["variant_id"] for r in rows if "declining_returns" in r["flags"]] == [
        out["chosen"]["id"]
    ]
    assert len(read_csv(folder / "top_trades.csv")) == 20
    assert "Decay and extreme trades" in (folder / "report.md").read_text()


def test_saved_retest_identity_and_snapshot_upgrade(tmp_path, fakes):
    """Use only saved synthetic development trades to exercise historical test identities."""
    import csv

    from backtester.tools import research_diagnostics

    out = run_research(tmp_path, dev_only=True)
    folder = out["folder"]
    variant_id = out["chosen"]["id"]
    run_folder = folder / "variants" / variant_id
    path = run_folder / "diagnostics.json"
    old = json.loads(path.read_text())
    for name in ("returns_slope", "top_trades", "extreme_summary"):
        del old[name]
    path.write_text(json.dumps(old))
    with (folder / "test.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, ["test_run", "variant_id", "run_folder"])
        writer.writeheader()
        for number in (1, 2):
            writer.writerow({"test_run": number, "variant_id": variant_id, "run_folder": "saved"})
    config = grid.load_grid(tmp_path / "idea.toml")
    variants = grid.expand(config)[0]
    rows = read_csv(folder / "variants.csv")
    for row in rows:
        row["net_r"] = float(row["net_r"])
    info = json.loads((folder / "research.json").read_text())
    # Both fake historical records reuse development trades; no price source is accessed.
    import shutil

    saved = tmp_path / "results" / "saved"
    shutil.copytree(run_folder, saved)
    calls = len(fakes.calls)
    research_diagnostics.write_diagnostics(
        folder, replace(config, shocks=False), variants, rows, info, tmp_path / "results", None
    )
    identities = {
        (r["period"], r["test_run"], r["variant_id"])
        for r in read_csv(folder / "returns_slope.csv")
    }
    assert identities == {
        ("development", "0", variant_id),
        ("test", "1", variant_id),
        ("test", "2", variant_id),
    }
    assert {r["test_run"] for r in read_csv(folder / "top_trades.csv")} == {"0", "1", "2"}
    assert "returns_slope" in json.loads(path.read_text())
    assert len(fakes.calls) == calls
