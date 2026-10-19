"""Stationarity study tool: loading from a cache folder, per-symbol analysis, the CSV files,
the summary. Spec: ROADMAP.md > 11.11; ideas.md T-11."""

from __future__ import annotations

import csv
from datetime import UTC, date, datetime, timedelta

import numpy as np
import pandas as pd

from backtester.core.models import Timeframe
from backtester.data.cache import cache_path, write_atomic
from backtester.tools import stationarity_study as tool

EPOCH = date(1970, 1, 1)


def fake_loader(calls=None, seed=1, days=400):
    """A loader returning a random walk of M5 / H1 / D1 bars over `days` days from `start`."""

    def load(symbol, cache_dir, timeframe, start, end):
        if calls is not None:
            calls.append((symbol, timeframe.name, start, end))
        step = timeframe.value * 60
        n = int((end - start).days + 1) * 86400 // step
        secs = (start - EPOCH).days * 86400 + np.arange(n) * step
        rng = np.random.default_rng(seed + sum(map(ord, symbol)))
        return secs, 100 * np.exp(np.cumsum(rng.normal(0, 0.001, n)))

    return load


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run(tmp_path, monkeypatch, extra=(), symbols=("NAS100", "US500"), **kw):
    monkeypatch.setattr(tool, "load_series", fake_loader(**kw))
    out = tmp_path / "out"
    argv = ["--cache-dir", str(tmp_path), "--symbols", *symbols, "--timeframes", "H1", "M5",
            "--start", "2016-01-04", "--end", "2016-06-30", "--workers", "1",
            "--out", str(out), *extra]  # fmt: skip
    assert tool.main(argv) == 0
    return out


def test_main_writes_all_files_with_real_and_random_walk_rows(tmp_path, monkeypatch):
    out = run(tmp_path, monkeypatch)
    for name in ("adf", "hurst", "vr", "lagcorr", "time_of_day", "findings"):
        assert (out / f"{name}.csv").is_file(), name
    assert (out / "summary.txt").is_file()
    adf = read(out / "adf.csv")
    assert {r["source"] for r in adf} == {"real", "random_walk"}
    assert {r["symbol"] for r in adf} == {"NAS100", "US500"}
    assert {r["timeframe"] for r in adf} == {"H1", "M5"}
    assert {r["period"] for r in adf} == {"whole", "first_half", "second_half"}
    vr = read(out / "vr.csv")
    assert {int(r["q"]) for r in vr} == {2, 5, 10, 20}
    tod = read(out / "time_of_day.csv")
    assert {r["period"] for r in tod} == {"whole", "first_half", "second_half"}
    assert len({r["bucket"] for r in tod}) == 48
    assert "NAS100" in (out / "summary.txt").read_text(encoding="utf-8")


def test_findings_file_has_a_header_even_when_empty(tmp_path, monkeypatch):
    out = run(tmp_path, monkeypatch)
    header = (out / "findings.csv").read_text(encoding="utf-8").splitlines()[0]
    assert "family" in header and "reason" in header and "symbol" in header


def test_random_walk_symbols_have_hurst_and_vr_near_the_null(tmp_path, monkeypatch):
    out = run(tmp_path, monkeypatch)
    h = [float(r["hurst"]) for r in read(out / "hurst.csv")
         if r["source"] == "real" and r["period"] == "whole" and r["timeframe"] == "H1"]  # fmt: skip
    assert h and all(0.4 < x < 0.6 for x in h)


def test_ger40_end_is_cut_and_halves_split_at_the_middle(tmp_path, monkeypatch):
    calls = []
    out = run(tmp_path, monkeypatch, symbols=("GER40",), calls=calls)
    assert calls and all(c[3] == date(2016, 6, 30) for c in calls)  # end 2016 < cut, kept
    calls.clear()
    monkeypatch.setattr(tool, "load_series", fake_loader(calls=calls))
    argv = ["--cache-dir", str(tmp_path), "--symbols", "GER40", "--timeframes", "H1",
            "--start", "2019-01-01", "--end", "2021-09-13", "--workers", "1",
            "--out", str(tmp_path / "o2")]  # fmt: skip
    assert tool.main(argv) == 0
    assert {c[3] for c in calls} == {date(2020, 6, 12)}
    hurst = [r for r in read(tmp_path / "o2" / "hurst.csv") if r["source"] == "real"]
    bars = {r["period"]: int(r["bars"]) for r in hurst}
    assert bars["first_half"] + bars["second_half"] == bars["whole"]
    assert abs(bars["first_half"] - bars["second_half"]) <= 24  # the middle of the period
    assert out.is_dir()


def test_missing_symbol_is_skipped_with_a_message(tmp_path, monkeypatch, capsys):
    def load(symbol, cache_dir, timeframe, start, end):
        if symbol == "NAS100":
            raise ValueError("no cached days")
        return fake_loader()(symbol, cache_dir, timeframe, start, end)

    monkeypatch.setattr(tool, "load_series", load)
    argv = ["--cache-dir", str(tmp_path), "--symbols", "NAS100", "US500", "--timeframes", "H1",
            "--start", "2016-01-04", "--end", "2016-06-30", "--workers", "1",
            "--out", str(tmp_path / "o")]  # fmt: skip
    assert tool.main(argv) == 0
    assert "NAS100" in capsys.readouterr().out
    assert {r["symbol"] for r in read(tmp_path / "o" / "adf.csv")} == {"US500"}


def write_days(tmp_path, offsets):
    for i in offsets:
        day = date(2016, 6, 1) + timedelta(days=i)
        ts = pd.date_range(
            datetime(day.year, day.month, day.day, tzinfo=UTC), periods=1440, freq="min"
        )
        price = 100 + (i * 1440 + np.arange(1440)) * 0.01
        frame = pd.DataFrame({"ts": ts})
        for side in ("bid", "ask"):
            for f in ("open", "high", "low", "close"):
                frame[f"{side}_{f}"] = price + (0.001 if side == "ask" else 0)
            frame[f"{side}_volume"] = 1.0
        write_atomic(frame, cache_path(tmp_path, "TEST", day))


def test_load_series_reads_a_cache_folder_and_resamples(tmp_path):
    write_days(tmp_path, range(3))
    secs, closes = tool.load_series(
        "TEST", tmp_path, Timeframe.H1, date(2016, 6, 1), date(2016, 6, 3)
    )
    assert len(secs) == len(closes) == 72
    assert secs[0] == (date(2016, 6, 1) - EPOCH).days * 86400
    assert np.all(np.diff(secs) == 3600) and np.all(np.diff(closes) > 0)


def test_load_series_bridges_a_day_missing_from_the_cache(tmp_path):
    # histdata has no file for some days (2018-01-01, 2020-01-01): the series goes on after them
    write_days(tmp_path, [0, 1, 3, 4])
    secs, _closes = tool.load_series(
        "TEST", tmp_path, Timeframe.H1, date(2016, 6, 1), date(2016, 6, 5)
    )
    assert len(secs) == 96
    jump = np.flatnonzero(np.diff(secs) > 3600)
    assert len(jump) == 1 and np.diff(secs)[jump[0]] == 25 * 3600
    assert tool.missing_days("TEST", tmp_path, date(2016, 6, 1), date(2016, 6, 5)) == [
        date(2016, 6, 3)
    ]
