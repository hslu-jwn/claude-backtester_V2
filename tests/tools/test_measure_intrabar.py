"""T-03 measurement: all golden setups, unchanged costs, two modes and exact deltas.

Test first: fake runner verifies report contract; real historical run is separate.
"""

import csv
import importlib.util
from pathlib import Path
from types import SimpleNamespace

from backtester.engine.costs import CostConfig
from backtester.tools.golden import GoldenConfig


def test_measurement_contract(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "measure_intrabar", Path("scripts/measure_intrabar.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    calls = []

    def fake(symbols, start, end, settings, sources, *, workers):
        calls.append((symbols, start, end, settings, workers))
        m1 = settings.engine.intrabar == "m1"
        return SimpleNamespace(
            trades=[SimpleNamespace(r_net=2 if m1 else -1)],
            notes=(),
            runs={},
            summary=lambda: {
                "combined": {
                    "intrabar_ambiguous": 2,
                    "intrabar_tp_first": int(m1),
                    "intrabar_sl_first": int(m1),
                    "intrabar_fallbacks": 0,
                }
            },
        )

    monkeypatch.setattr(mod, "run_backtests", fake)
    out = tmp_path / "measurement"
    assert mod.main(["--output", str(out)]) == 0
    assert len(calls) == 14
    cfg = GoldenConfig()
    for symbols, start, end, settings, workers in calls:
        assert (start, end, workers) == (cfg.start, cfg.end, 1)
        assert symbols in dict(cfg.strategies).values()
        assert settings.engine.costs == CostConfig()
    with out.with_suffix(".csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 14
    for row in rows:
        m1 = row["intrabar"] == "m1"
        assert float(row["delta_net_r"]) == (3 if m1 else 0)
        assert float(row["delta_avg_r"]) == (3 if m1 else 0)
        assert float(row["tp_first_share"]) == (0.5 if m1 else 0)
        assert int(row["ambiguous"]) == 2
    report = out.with_suffix(".md").read_text(encoding="utf-8")
    assert "2023-01-01" in report and "2023-12-31" in report
    assert all(name in report for name, _ in cfg.strategies)
