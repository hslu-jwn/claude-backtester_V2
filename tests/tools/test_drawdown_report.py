"""Bounds report integration and MTM preference, written before implementation."""

import json
from dataclasses import replace
from datetime import date

import pytest

from backtester.risk.drawdown_bounds import DrawdownBoundsConfig
from backtester.tools import drawdown_report

START, END = date(2025, 1, 6), date(2025, 1, 7)
FAST = DrawdownBoundsConfig(outer=3, inner=8, horizon_days=4)


def test_mtm_preferred_and_legacy_fallback(tmp_path):
    path = tmp_path / "daily.csv"
    path.write_text("date,net_r_exit_booked,net_r_mtm\n2025-01-06,-7,1\n2025-01-07,0,2\n")
    result = drawdown_report.calculate([], START, END, tmp_path, FAST)
    assert result["source"] == "marked_to_market"
    assert all(v == 0 for r in result["rows"] for v in r["bounds_r"].values())
    path.write_text("date,net_r_exit_booked\n2025-01-06,-7\n2025-01-07,0\n")
    result = drawdown_report.calculate([], START, END, tmp_path, FAST)
    assert result["source"] == "exit_booked"
    assert result["rows"][0]["bounds_r"]["median"] > 0


@pytest.mark.parametrize(
    "rows", ["2025-01-06,nan\n2025-01-07,0\n", "2025-01-06,1\n", "2025-01-07,1\n2025-01-06,2\n"]
)
def test_malformed_mtm_rejected(tmp_path, rows):
    (tmp_path / "daily.csv").write_text("date,net_r_mtm\n" + rows)
    with pytest.raises(ValueError):
        drawdown_report.calculate([], START, END, tmp_path, FAST)


@pytest.mark.parametrize(
    "content",
    [
        "",
        "date,unknown\n2025-01-06,1\n2025-01-07,2\n",
        "date,net_r_mtm\n2025-01-06\n2025-01-07,0\n",
    ],
)
def test_broken_daily_file_never_silently_falls_back(tmp_path, content):
    (tmp_path / "daily.csv").write_text(content)
    with pytest.raises(ValueError, match="daily.csv"):
        drawdown_report.calculate([], START, END, tmp_path, FAST)


def test_tool_html_json_and_sampling(tmp_path):
    from backtester.runner import RunSettings
    from backtester.tools import monte_carlo as tool

    config = tool.ToolConfig(runs=3, paths=0, bounds=FAST, sampling="permutation", block_days=2)
    summary = tool.build_summary(
        [],
        None,
        {"strategy": "x", "symbols": [], "start": START, "end": END, "source": "run"},
        RunSettings(),
        config,
        log=lambda *_: None,
    )
    tool.write_outputs(summary, tmp_path)
    data = json.loads((tmp_path / "summary.json").read_text())
    assert data["drawdown_bounds"]["source"] == "exit_booked"
    html = (tmp_path / "report.html").read_text(encoding="utf-8")
    for text in ("Double-bootstrap", "permutation", "block_days=2", "95% upper", "0.5%"):
        assert text in html
    assert replace(config, sampling="block_bootstrap").sampling == "block_bootstrap"
