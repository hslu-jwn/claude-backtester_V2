"""Cases: saved MTM preferred over exit-booked, complete dates required, cached MTM
fallback, raw/trend report text and JSON, score key order/old cards, trend flag,
research chosen development and executed test wiring, Monte Carlo HTML.
Spec: research-runner.md > Skill vs trend, and bounds.
"""

import json
from datetime import date
from types import SimpleNamespace as NS

import pytest

from backtester.analytics.bounds import BoundsConfig
from backtester.analytics.scorecard import SCORE_KEYS, flags, scorecard
from backtester.tools import monte_carlo, skill_bounds


def test_saved_mtm_and_outputs(tmp_path, monkeypatch):
    (tmp_path / "daily.csv").write_text(
        "date,net_r_exit_booked,net_r_mtm,position\n2020-01-06,100,1,0\n2020-01-07,100,-1,0\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(skill_bounds, "load_drifts", lambda *a: {})
    a = skill_bounds.calculate(
        [], date(2020, 1, 6), date(2020, 1, 7), NS(), tmp_path, config=BoundsConfig(boots=50)
    )
    assert a["daily_mean"]["estimate"] == 0
    assert a["log_pf"]["estimate"] == 0
    assert a["source"] == "marked_to_market"
    skill_bounds.write(a, tmp_path)
    assert json.loads((tmp_path / "skill_bounds.json").read_text()) == a
    assert "Skill vs trend, and bounds" in "\n".join(skill_bounds.markdown(a))
    assert "Skill vs trend, and bounds" in monte_carlo.skill_bounds_html({"skill_bounds": a})


def test_wrong_dates_rejected(tmp_path):
    (tmp_path / "daily.csv").write_text("date,net_r_mtm\n2020-01-07,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="dates"):
        skill_bounds.calculate([], date(2020, 1, 6), date(2020, 1, 7), NS(), tmp_path)


def test_compute_mtm_fallback(monkeypatch):
    monkeypatch.setattr(skill_bounds, "daily_net_r_mtm", lambda *a: ([1, -1], [0, 0]))
    monkeypatch.setattr(skill_bounds, "load_drifts", lambda *a: {})
    a = skill_bounds.calculate(
        [], date(2020, 1, 6), date(2020, 1, 7), NS(), config=BoundsConfig(boots=50)
    )
    assert a["daily_mean"]["estimate"] == 0


def test_legacy_daily_uses_computed_mtm(tmp_path, monkeypatch):
    (tmp_path / "daily.csv").write_text(
        "date,net_r_exit_booked\n2020-01-06,100\n2020-01-07,100\n", encoding="utf-8"
    )
    monkeypatch.setattr(skill_bounds, "daily_net_r_mtm", lambda *a: ([1, -1], [0, 0]))
    monkeypatch.setattr(skill_bounds, "load_drifts", lambda *a: {})
    a = skill_bounds.calculate(
        [], date(2020, 1, 6), date(2020, 1, 7), NS(), tmp_path, config=BoundsConfig(boots=50)
    )
    assert a["daily_mean"]["estimate"] == 0


def test_saved_nonfinite_rejected(tmp_path, monkeypatch):
    (tmp_path / "daily.csv").write_text("date,net_r_mtm\n2020-01-06,nan\n", encoding="utf-8")
    monkeypatch.setattr(skill_bounds, "load_drifts", lambda *a: {})
    with pytest.raises(ValueError, match="finite"):
        skill_bounds.calculate([], date(2020, 1, 6), date(2020, 1, 6), NS(), tmp_path)


def test_symbol_without_trades_reported(monkeypatch):
    monkeypatch.setattr(skill_bounds, "daily_net_r_mtm", lambda *a: ([0], [0]))
    monkeypatch.setattr(skill_bounds, "load_drifts", lambda *a: {"X": 0.0})
    a = skill_bounds.calculate([], date(2020, 1, 6), date(2020, 1, 6), NS(), symbols=["X"])
    assert a["trend"]["symbols"]["X"]["net_r"] == 0
    assert a["position_bias"]["symbols"]["X"]["flat"] == 1


def test_score_keys_and_old_flags():
    assert SCORE_KEYS[-3:] == ("detrended_net_r", "lower95_mean_daily_r", "log_pf")
    row = scorecard([])
    old = flags(row)
    assert "skill_is_trend" not in old
    row.update(net_r=1, detrended_net_r=0)
    assert "skill_is_trend" in flags(row)


def test_research_saved_runs_only(tmp_path, monkeypatch):
    chosen = tmp_path / "variants" / "v1"
    chosen.mkdir(parents=True)
    test = tmp_path / "test_run"
    test.mkdir()
    calls = []
    a = {
        "scores": {"detrended_net_r": -1, "lower95_mean_daily_r": -0.5, "log_pf": 0},
        "flags": ["skill_is_trend"],
    }

    def calculate(trades, start, end, sources, folder, **kw):
        calls.append(folder)
        return a

    monkeypatch.setattr(skill_bounds, "calculate", calculate)
    monkeypatch.setattr(skill_bounds, "read_trades", lambda p: [])
    info = {"chosen": {"id": "v1", "dev_run": "published"}}
    rows = [{"variant_id": "v1", "net_r": 1, "flags": ""}]
    tests = [
        {
            "test_run": "1",
            "run_folder": "test_run",
            "start": "2021-09-14",
            "end": "2021-09-15",
            "net_r": 1,
            "flags": "",
        }
    ]
    skill_bounds.research_results(
        tmp_path, tmp_path, info, rows, tests, date(2020, 1, 6), date(2020, 1, 7), NS(), ["X"]
    )
    assert calls == [chosen, test]
    assert rows[0]["detrended_net_r"] == -1
    assert tests[0]["flags"] == "skill_is_trend"
    assert set(info["skill_bounds"]) == {"development", "test 1"}
