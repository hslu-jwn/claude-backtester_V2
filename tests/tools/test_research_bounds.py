"""Chosen-only bounds; dev-only and resume must never spend the test period."""

# ruff: noqa: F811
import json

from backtester.risk.drawdown_bounds import DrawdownBoundsConfig
from backtester.tools import drawdown_report
from tests.tools.test_research import (  # noqa: F401
    fakes,
    research_folder,
    run_research,
)


def test_chosen_dev_and_test_bounds_and_resume(tmp_path, fakes, monkeypatch):
    original = drawdown_report.calculate
    fast = DrawdownBoundsConfig(outer=3, inner=8, horizon_days=4)
    monkeypatch.setattr(
        drawdown_report, "calculate", lambda *a, **kw: original(*a, **kw, config=fast)
    )
    out = run_research(tmp_path, dev_only=True)
    folder = research_folder(tmp_path)
    variant = folder / "variants" / out["chosen"]["id"]
    dev = tmp_path / "results" / out["chosen"]["dev_run"]
    for target in (variant, dev):
        bounds = json.loads((target / "drawdown_bounds.json").read_text())
        assert bounds["source"] == "marked_to_market"
        assert len(bounds["rows"]) == 4
    assert "Double-bootstrap development" in (folder / "report.md").read_text()
    assert len(list((folder / "variants").glob("*/drawdown_bounds.json"))) == 1
    out = run_research(tmp_path)
    test = tmp_path / "results" / out["test"]["run_folder"]
    assert (test / "drawdown_bounds.json").is_file()
    assert "Double-bootstrap test" in (folder / "report.md").read_text()
    calls = len(fakes.calls)
    assert run_research(tmp_path)["status"] == "refused"
    assert len(fakes.calls) == calls
