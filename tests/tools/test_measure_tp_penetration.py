"""Measurement cases: five settings x seven setups, exact baseline, counts and deltas.

Use a fake runner so the report contract is checked without historical data; the actual
script runs every setup sequentially, with spec defaults and the golden date range.
"""

import csv
import importlib.util
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from backtester.tools.golden import GoldenConfig


def module():
    spec = importlib.util.spec_from_file_location(
        "measure_tp_penetration", Path("scripts/measure_tp_penetration.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_measurement_settings_counts_and_deltas(tmp_path, monkeypatch):
    mod = module()
    calls = []
    from backtester.engine.trade import ExitReason

    def fake(symbols, start, end, settings, sources, *, workers):
        calls.append((symbols, start, end, settings, workers))
        cfg = settings.engine.costs
        trade = SimpleNamespace(
            r_net=2 - cfg.tp_penetration,
            exit_reason=ExitReason.TAKE_PROFIT,
            tp_levels_touched=2,
            tp_levels_touched_not_filled=int(cfg.tp_penetration > 0),
            parts=[SimpleNamespace(reason=ExitReason.TAKE_PROFIT)],
        )
        return SimpleNamespace(trades=[trade], notes=(), runs={})

    monkeypatch.setattr(mod, "run_backtests", fake)
    out = tmp_path / "measurement"
    assert mod.main(["--output", str(out)]) == 0
    assert len(calls) == 35
    cfg = GoldenConfig()
    for symbols, start, end, settings, workers in calls:
        assert start == cfg.start and end == cfg.end and workers == 1
        assert symbols in dict(cfg.strategies).values()
    with out.with_suffix(".csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 35
    assert {float(r["tp_penetration"]) for r in rows} == {0, 0.5, 1, 2}
    for row in rows:
        distance = float(row["tp_penetration"])
        assert float(row["delta_net_r"]) == -distance
        assert float(row["delta_avg_r"]) == -distance
        assert float(row["touched_not_filled_share"]) == (0.5 if distance else 0)
        assert int(row["tp_exits"]) == 1
    report = out.with_suffix(".md").read_text(encoding="utf-8")
    assert "2023-01-01" in report and "2023-12-31" in report
    assert all(name in report for name, _ in cfg.strategies)


def test_measurement_propagates_failure_instead_of_writing_partial_success(tmp_path, monkeypatch):
    mod = module()

    def fail(*args, **kwargs):
        raise RuntimeError("missing candle data")

    monkeypatch.setattr(mod, "run_backtests", fail)
    with pytest.raises(RuntimeError, match="missing candle"):
        mod.main(
            ["--output", str(tmp_path / "failed")],
            config=replace(GoldenConfig(), strategies=GoldenConfig().strategies[:1]),
        )
    assert not (tmp_path / "failed.csv").exists()
