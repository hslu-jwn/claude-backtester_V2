"""R10 effect columns of research/ledger.csv (docs/research-runner.md › Ledger): est / se per row for pooling."""

import csv
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "ledger_effects", "research/screens/ledger_effects.py"
)
le = importlib.util.module_from_spec(spec)
spec.loader.exec_module(le)


def write(tmp_path, rows, header=None):
    header = header or ["id", "stage", "family", *le.EFFECT_COLUMNS]
    p = tmp_path / "ledger.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return p


def row(**kw):
    base = {"id": "X1", "stage": "screened", "family": "f"}
    return base | kw


def test_blank_effect_columns_are_valid(tmp_path):
    assert le.check(write(tmp_path, [row()])) == []


def test_complete_effect_row_is_valid(tmp_path):
    r = row(
        est="12.5",
        se="4.1",
        est_unit="bp/week",
        est_basis="gross",
        est_sample="dev",
        type="c",
        dup_group="S20",
    )
    assert le.check(write(tmp_path, [r])) == []


@pytest.mark.parametrize(
    ("bad", "word"),
    [
        ({"est": "1.2"}, "se"),  # est without se
        ({"est": "1.2", "se": "0"}, "se"),  # se must be > 0
        ({"est": "1.2", "se": "-1"}, "se"),
        ({"est": "abc", "se": "1"}, "est"),  # not a number
        ({"est": "1", "se": "1", "est_basis": "after"}, "est_basis"),
        ({"est": "1", "se": "1", "est_basis": "gross", "est_sample": "later"}, "est_sample"),
        ({"type": "z"}, "type"),
        (
            {"est": "1", "se": "1", "est_basis": "gross", "est_sample": "dev"},
            "est_unit",
        ),  # unit required
    ],
)
def test_bad_effect_values_are_flagged(tmp_path, bad, word):
    errors = le.check(write(tmp_path, [row(**bad)]))
    assert errors and word in errors[0]


def test_missing_effect_column_is_flagged(tmp_path):
    p = write(tmp_path, [row()], header=["id", "stage", "family"])
    assert any("column" in e for e in le.check(p))


def test_t_is_est_over_se_and_blank_rows_skipped(tmp_path):
    rows = [
        row(id="A", est="6", se="2", est_unit="bp", est_basis="gross", est_sample="dev", type="a"),
        row(id="B"),
    ]
    t = le.t_values(write(tmp_path, rows))
    assert t == {"A": 3.0}


def test_real_ledger_passes():
    assert le.check(Path("research/ledger.csv")) == []
