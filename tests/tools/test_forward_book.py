"""Forward book (research/screens/2026-11-27_forward_book.py): weeks, weights, missing logs, units."""

import importlib.util
import math
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def fb():
    spec = importlib.util.spec_from_file_location(
        "forward_book", ROOT / "research/screens/2026-11-27_forward_book.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def member(fb, name, **kw):
    base = {
        "file": f"{name}.csv",
        "date_col": "period",
        "col": "net_bp",
        "unit": "bp",
        "ppw": 1,
        "mean": 10.0,
        "sd": 100.0,
        "factor": 0.4,
        "source": "test",
    }
    return fb.Member(name, **{**base, **kw})


def log(tmp_path, name, rows, col="net_bp"):
    (tmp_path / f"{name}.csv").write_text(
        f"period,{col}\n" + "".join(f"{p},{v}\n" for p, v in rows)
    )


def test_week_bucketing_sunday_goes_to_monday_before(fb):
    assert fb.week_start(date(2026, 11, 29)) == date(2026, 11, 23)  # Sunday
    assert fb.week_start(date(2026, 11, 23)) == date(2026, 11, 23)  # Monday
    assert fb._day("2026-11-29T23:00:00-05:00") == date(2026, 11, 30)  # converted to UTC first
    assert fb._day("2026-11") == date(2026, 11, 30)  # month label = month-end


def test_weekly_sd_scaling_and_sum(fb, tmp_path):
    m = member(fb, "a", ppw=4, sd=50.0)  # weekly sd = 50 x sqrt(4) = 100
    log(
        tmp_path,
        "a",
        [("2026-11-23", 100), ("2026-11-27", 50), ("2026-11-29", 30), ("2026-11-30", -100)],
    )
    wk = fb.weekly(fb.load(m, tmp_path), m)
    assert wk == {date(2026, 11, 23): pytest.approx(1.8), date(2026, 11, 30): pytest.approx(-1.0)}


def test_nonpositive_shrunk_sharpe_gets_zero_and_weights_sum_one(fb):
    ms = (
        member(fb, "a", mean=10),
        member(fb, "b", mean=-5),
        member(fb, "c", mean=0),
        member(fb, "d", mean=30),
    )
    w = fb.weights(ms)
    assert w["b"] == 0 and w["c"] == 0
    assert sum(w.values()) == pytest.approx(1)
    assert w["d"] == pytest.approx(0.75)  # shrunk Sharpe 3 : 1
    assert fb.weights((member(fb, "z", mean=-1),)) == {
        "z": 0.0
    }  # nothing positive: no division by zero


def test_default_members_weights_sum_one(fb):
    assert sum(fb.weights().values()) == pytest.approx(1)


def test_missing_and_empty_logs(fb, tmp_path):
    ms = (member(fb, "a"), member(fb, "b"))
    assert fb.load(ms[0], tmp_path) is None
    txt = fb.report(tmp_path, ms)
    assert txt.count("no rows yet") == 3  # two members + the book
    log(tmp_path, "a", [])  # header only
    assert "no rows yet" in fb.report(tmp_path, ms)
    assert fb.book(ms, tmp_path)[2] == []


def test_r_and_bp_members_combine_only_in_risk_units(fb, tmp_path):
    a = member(fb, "a", unit="bp", sd=100.0, mean=10)
    b = member(fb, "b", unit="R", col="net_r", sd=0.5, mean=0.1)
    log(tmp_path, "a", [("2026-11-23", 100)])
    log(tmp_path, "b", [("2026-11-24", 0.5)], col="net_r")
    w, _, weeks, vals = fb.book((a, b), tmp_path)
    assert weeks == [date(2026, 11, 23)]
    assert vals == [
        pytest.approx(w["a"] * 1.0 + w["b"] * 1.0)
    ]  # 100 bp and 0.5 R are each one weekly sd


def test_zero_filled_weeks_between_logs(fb, tmp_path):
    m = member(fb, "a")
    log(tmp_path, "a", [("2026-11-23", 100), ("2026-12-07", 100)])
    _, _, weeks, vals = fb.book((m,), tmp_path)
    assert weeks == [date(2026, 11, 23), date(2026, 11, 30), date(2026, 12, 7)]
    assert vals == [1.0, 0.0, 1.0]


def test_forward_data_never_changes_weights(fb, tmp_path):
    ms = (member(fb, "a", mean=10), member(fb, "b", mean=20))
    before = fb.weights(ms)
    log(tmp_path, "a", [("2026-11-23", -9999)])
    log(tmp_path, "b", [("2026-11-23", 9999)])
    assert fb.book(ms, tmp_path)[0] == before
    log(tmp_path, "a", [("2026-11-23", 9999)])
    assert fb.book(ms, tmp_path)[0] == before


def test_report_numbers(fb, tmp_path):
    m = member(fb, "a", mean=10, sd=100, factor=0.4)
    log(tmp_path, "a", [("2026-11-23", 100), ("2026-11-30", 0), ("2026-12-07", 50)])
    txt = fb.report(tmp_path, (m,))
    assert "periods 3" in txt and "fwd mean +50.000" in txt
    z = 50 / (100 / math.sqrt(3))
    assert f"z {z:+.2f}" in txt
    assert "weeks 3" in txt and "cumulative +1.500" in txt
    assert f"expected z at shrunk mean {0.4 * 0.1 * math.sqrt(3):+.2f}" in txt
