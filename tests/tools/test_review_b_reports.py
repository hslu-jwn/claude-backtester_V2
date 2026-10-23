"""B2 report regressions. Spec: risk-management.md (user decision, 2026-10-22)."""

import csv
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest

from backtester.risk.monte_carlo import MonteCarloConfig
from backtester.tools import monte_carlo as tool
from backtester.tools import risk_sweep as sweep


def test_full_monte_carlo_report_shows_unfinished_count_and_share_next_to_pass_rate():
    summary = {
        "monte_carlo": {
            "config": MonteCarloConfig(),
            "risks": {
                0.01: {
                    "ftmo": {
                        "attempts": 2,
                        "passes": 1,
                        "fail_daily": 1,
                        "fail_max": 0,
                        "pass_probability": 0.5,
                        "unfinished_attempts": 1,
                        "total_attempts": 3,
                        "unfinished_share": 1 / 3,
                        "median_days_to_pass": 8,
                        "funded_lost_probability": 0,
                    }
                }
            },
        }
    }
    html = tool.ftmo_html(summary)
    assert "Unfinished attempts" in html
    assert "1 (33.3 %)" in html
    assert "50.0 %" in html
    assert "finished attempts" in html


def test_adaptive_sweep_exports_unfinished_count_and_share(tmp_path):
    start = date(2025, 1, 6)
    stamp = datetime(2025, 1, 6, 10, tzinfo=UTC)
    trade = SimpleNamespace(entry_time=stamp, exit_time=stamp + timedelta(hours=1), r_net=0)
    config = sweep.SweepConfig(runs=2, workers=1)
    variants = [sweep.Variant(0.01, None, None), sweep.Variant(0.01, 0.25, 0.03)]
    rows = sweep.evaluate([trade], start, start, config, variants, workers=1)
    for row in rows:
        assert row["attempts"] == 0
        assert row["unfinished_attempts"] == row["total_attempts"] == 2
        assert row["unfinished_share"] == 1
    strategy = {
        "dev_variants": rows,
        "dev_trades": 1,
        "dev_gross_r": 0,
        "dev_net_r": 0,
        "dev_meaningful": False,
        "dev_flat_top": {},
    }
    result = {
        "config": asdict(config),
        "strategies": {"fixture": strategy},
        "universal": {"label": rows[0]["label"]},
    }
    sweep.write_outputs(result, tmp_path)
    with (tmp_path / "variants.csv").open(encoding="utf8", newline="") as stream:
        exported = list(csv.DictReader(stream))
    assert len(exported) == 2
    assert all(int(row["unfinished_attempts"]) == 2 for row in exported)
    assert all(float(row["unfinished_share"]) == pytest.approx(1) for row in exported)
    report = (tmp_path / "report.md").read_text(encoding="utf8")
    assert "unfinished" in report.lower()
    assert "2 (100.0%)" in report
