"""Noise study tool: per symbol x timeframe x year / half the efficiency ratio, and its
comparison with strategy 4's halves. Spec: ROADMAP.md › 11.1."""

from __future__ import annotations

import csv
from datetime import UTC, datetime, timedelta

import pytest

from backtester.tools import noise_study
from backtester.tools.noise_study import compare_with_strategy4, noise_rows


def day(year, month=6, d=1):
    return datetime(year, month, d, tzinfo=UTC)


def times(*years, per_year=30):
    out = []
    for y in years:
        out += [day(y) + timedelta(days=i) for i in range(per_year)]
    return out


def straight(n):
    return [100.0 + i for i in range(n)]


def zigzag(n):
    return [100.0 + (i % 2) for i in range(n)]


# --- noise_rows ----------------------------------------------------------------------------------


def test_noise_rows_per_year_and_half_with_the_right_means():
    ts = times(2021, 2024)
    closes = straight(30) + zigzag(30)  # 2021: trending (ER 1), 2024: back and forth (ER 0)
    rows = noise_rows("XAUUSD", "H4", ts, closes, ns=(4,))
    by = {(r["kind"], r["period"]): r for r in rows}
    assert by[("year", "2021")]["mean_er"] == pytest.approx(1.0)
    assert by[("year", "2024")]["mean_er"] < 0.2  # a few windows still span the jump
    assert by[("half", "2020-22")]["mean_er"] == pytest.approx(1.0)
    assert by[("half", "2023-26")]["mean_er"] < 0.2
    assert all(r["symbol"] == "XAUUSD" and r["timeframe"] == "H4" and r["n"] == 4 for r in rows)
    assert by[("year", "2021")]["bars"] == 30 - 4  # the first n bars have no ratio


def test_noise_rows_one_set_per_period_n():
    ts = times(2021)
    rows = noise_rows("US500", "D1", ts, straight(30), ns=(3, 7))
    assert {r["n"] for r in rows} == {3, 7}
    assert {r["kind"] for r in rows} == {"year", "half", "all"}


def test_noise_rows_period_without_values_is_left_out():
    ts = times(2021, per_year=4)  # 4 bars, n = 10: no value anywhere
    assert noise_rows("US500", "D1", ts, straight(4), ns=(10,)) == []


def test_noise_rows_median_and_overall_row():
    ts = times(2021)
    rows = noise_rows("XAUUSD", "H4", ts, straight(30), ns=(5,))
    allrow = next(r for r in rows if r["kind"] == "all")
    assert allrow["period"] == "all"
    assert allrow["median_er"] == pytest.approx(1.0)


# --- compare_with_strategy4 -------------------------------------------------------------------------


def half_noise(symbol, tf, half, er, n=20):
    return {"kind": "half", "symbol": symbol, "timeframe": tf, "n": n, "period": half,
            "bars": 1000, "mean_er": er, "median_er": er}  # fmt: skip


def split_row(variant, symbol, half, trades, gross):
    return {"variant": variant, "symbol": symbol, "half": half, "trades": str(trades),
            "sum_r_gross": str(gross), "sum_r_net": str(gross - 1)}  # fmt: skip


def test_compare_aggregates_variants_of_a_timeframe_per_symbol_and_half():
    noise = [
        half_noise("XAUUSD", "H4", "2020-22", 0.30),
        half_noise("XAUUSD", "H4", "2023-26", 0.20),
    ]
    split = [
        split_row("H4 breakout 20", "XAUUSD", "2020-22", 100, 10.0),
        split_row("H4 sma 50", "XAUUSD", "2020-22", 100, 30.0),
        split_row("H4 sma 50", "XAUUSD", "2023-26", 200, -20.0),
        split_row("H4 sma 50", "ALL", "2020-22", 999, 999.0),  # the ALL group is skipped
    ]
    cells, stats = compare_with_strategy4(noise, split, n=20, min_trades=50)
    first = next(c for c in cells if c["half"] == "2020-22")
    assert first["trades"] == 200
    assert first["avg_gross_r"] == pytest.approx(40.0 / 200)
    assert first["mean_er"] == pytest.approx(0.30)
    assert stats == []  # two cells are not enough for a correlation


def test_compare_skips_cells_with_too_few_trades_or_no_noise():
    noise = [half_noise("XAUUSD", "H4", "2020-22", 0.3)]
    split = [
        split_row("H4 sma 50", "XAUUSD", "2020-22", 10, 5.0),  # < min_trades
        split_row("D1 sma 50", "XAUUSD", "2020-22", 500, 5.0),  # no noise row for D1
    ]
    cells, _ = compare_with_strategy4(noise, split, n=20, min_trades=50)
    assert cells == []


def test_compare_uses_only_the_requested_n():
    noise = [
        half_noise("XAUUSD", "H4", "2020-22", 0.9, n=60),
        half_noise("XAUUSD", "H4", "2020-22", 0.3, n=20),
    ]
    split = [split_row("H4 sma 50", "XAUUSD", "2020-22", 100, 10.0)]
    cells, _ = compare_with_strategy4(noise, split, n=20, min_trades=50)
    assert cells[0]["mean_er"] == pytest.approx(0.3)


def test_compare_correlates_levels_and_changes():
    # more noise (lower ER) goes with a worse gross R per trade in every cell
    noise, split = [], []
    for i, (sym, tf) in enumerate(
        [("A", "H1"), ("A", "H4"), ("B", "H1"), ("B", "H4"), ("C", "D1")]
    ):
        er1, er2 = 0.10 + 0.05 * i, 0.20 + 0.06 * i
        noise += [half_noise(sym, tf, "2020-22", er1), half_noise(sym, tf, "2023-26", er2)]
        split += [
            split_row(f"{tf} sma 50", sym, "2020-22", 100, 100 * (er1 - 0.15)),
            split_row(f"{tf} sma 50", sym, "2023-26", 100, 100 * (er2 - 0.15)),
        ]
    cells, stats = compare_with_strategy4(noise, split, n=20, min_trades=50)
    assert len(cells) == 10
    by = {s["measure"]: s for s in stats}
    assert by["level: mean ER vs avg gross R per trade"]["rho"] == pytest.approx(1.0)
    assert by["change: ER 2023-26 minus 2020-22 vs change in avg gross R"]["n"] == 5
    assert by["change: ER 2023-26 minus 2020-22 vs change in avg gross R"]["rho"] == pytest.approx(
        1.0
    )


# --- the command ---------------------------------------------------------------------------------------


def test_main_writes_the_csv_files_and_prints_a_table(tmp_path, monkeypatch, capsys):
    ts = times(2021, 2024)
    closes = straight(30) + zigzag(30)
    monkeypatch.setattr(noise_study, "load_closes", lambda symbol, tf, start, end: (ts, closes))
    split = tmp_path / "split.csv"
    with split.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["variant", "symbol", "half", "trades", "sum_r_gross", "sum_r_net"])
        w.writeheader()
        w.writerow(split_row("H4 sma 50", "XAUUSD", "2020-22", 100, 10.0))
        w.writerow(split_row("H4 sma 50", "XAUUSD", "2023-26", 100, -10.0))
    out = tmp_path / "noise"
    code = noise_study.main(
        ["--symbols", "XAUUSD", "--timeframes", "H4", "--ns", "5", "--join-n", "5",
         "--split-csv", str(split), "--out", str(out)]
    )  # fmt: skip
    assert code == 0
    for name in ("noise.csv", "vs_strategy4.csv"):
        with (out / name).open(encoding="utf-8") as f:
            assert list(csv.DictReader(f)), name
    text = capsys.readouterr().out
    assert "XAUUSD" in text and "H4" in text


def test_main_without_a_split_file_still_writes_the_noise(tmp_path, monkeypatch):
    ts = times(2021)
    monkeypatch.setattr(noise_study, "load_closes", lambda *a: (ts, straight(30)))
    out = tmp_path / "n"
    argv = [
        "--symbols",
        "US500",
        "--timeframes",
        "D1",
        "--ns",
        "5",
        "--no-compare",
        "--out",
        str(out),
    ]
    assert noise_study.main(argv) == 0
    assert (out / "noise.csv").is_file()
    assert not (out / "vs_strategy4.csv").exists()
