"""Append-only forward log for shelf rows (research-runner.md › Verdicts and shelf)."""

import pandas as pd
import pytest

from backtester.tools import forward_log as fl

COLS = ("period", "n", "gross_bp", "net_bp")


def rows(*periods, net=5.0):
    return [{"period": p, "n": 10, "gross_bp": net + 20, "net_bp": net} for p in periods]


def test_new_file_then_only_new_periods_are_appended(tmp_path):
    path = tmp_path / "x.csv"
    assert fl.append(path, rows("2026-11-23", "2026-11-30"), COLS) == 2
    assert fl.append(path, rows("2026-11-23", "2026-11-30", "2026-12-07"), COLS) == 1
    d = pd.read_csv(path)
    assert d.period.tolist() == ["2026-11-23", "2026-11-30", "2026-12-07"] and list(
        d.columns
    ) == list(COLS)


def test_a_changed_logged_period_is_refused_and_nothing_written(tmp_path):
    path = tmp_path / "x.csv"
    fl.append(path, rows("2026-11-23"), COLS)
    before = path.read_bytes()
    with pytest.raises(ValueError, match="2026-11-23"):
        fl.append(path, rows("2026-11-23", "2026-11-30", net=6.0), COLS)
    assert path.read_bytes() == before


def test_out_of_order_or_duplicate_periods_are_refused(tmp_path):
    path = tmp_path / "x.csv"
    fl.append(path, rows("2026-11-30"), COLS)
    with pytest.raises(ValueError, match="before"):
        fl.append(path, rows("2026-11-23"), COLS)
    with pytest.raises(ValueError, match="duplicate"):
        fl.append(tmp_path / "y.csv", rows("2026-11-23", "2026-11-23"), COLS)


def test_wrong_columns_are_refused(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text("period,other\n2026-11-23,1\n")
    with pytest.raises(ValueError, match="columns"):
        fl.append(path, rows("2026-11-30"), COLS)
