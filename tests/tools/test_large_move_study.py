"""Large-move study tool: per-symbol analysis, CSV files, summary, shuffled sanity run.
Spec: ROADMAP.md > 11.13; ideas.md I-61."""

from __future__ import annotations

import csv
from datetime import date

import numpy as np

from backtester.tools import large_move_study as tool

EPOCH = date(1970, 1, 1)


def fake_loader(seed=1):
    def load(symbol, cache_dir, timeframe, start, end):
        step = timeframe.value * 60
        n = int((end - start).days + 1) * 86400 // step
        secs = (start - EPOCH).days * 86400 + np.arange(n) * step
        rng = np.random.default_rng(seed + sum(map(ord, symbol)))
        r = rng.normal(0, 0.001, n)
        r[200::30] = 0.01 * np.where(np.arange(len(r[200::30])) % 2 == 0, 1, -1)
        r[201::30] = np.sign(r[200::30]) * 0.004  # continuation after the big bar
        return secs, 100 * np.exp(np.cumsum(r))

    return load


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run(tmp_path, monkeypatch, symbols=("NAS100", "US500"), extra=()):
    monkeypatch.setattr(tool, "load_series", fake_loader())
    out = tmp_path / "out"
    argv = ["--cache-dir", str(tmp_path), "--symbols", *symbols, "--timeframes", "H1",
            "--start", "2016-01-04", "--end", "2016-09-30", "--n-null", "200",
            "--out", str(out), *extra]  # fmt: skip
    assert tool.main(argv) == 0
    return out


def test_main_writes_files_with_one_row_per_cell(tmp_path, monkeypatch):
    out = run(tmp_path, monkeypatch)
    for name in ("events", "findings", "findings_shuffled"):
        assert (out / f"{name}.csv").is_file(), name
    assert (out / "summary.txt").is_file()
    ev = read(out / "events.csv")
    assert len(ev) == 2 * 3 * 5  # symbols x k x h
    assert {r["symbol"] for r in ev} == {"NAS100", "US500"}
    assert {r["timeframe"] for r in ev} == {"H1"}
    c = next(r for r in ev if r["symbol"] == "NAS100" and r["k"] == "4.0" and r["h"] == "1")
    assert float(c["mean_sd"]) > 1.0 and float(c["mean_spreads"]) > 0


def test_injected_continuation_is_a_finding_and_shuffled_data_is_not(tmp_path, monkeypatch):
    out = run(tmp_path, monkeypatch)
    found = read(out / "findings.csv")
    assert {r["symbol"] for r in found} >= {"NAS100", "US500"}
    assert read(out / "findings_shuffled.csv") == []
    text = (out / "summary.txt").read_text(encoding="utf-8")
    assert "CORE SYMBOLS FIRST" in text
    assert text.index("NAS100") < text.index("FINDINGS")


def test_unknown_symbol_is_skipped_with_a_message(tmp_path, monkeypatch, capsys):
    run(tmp_path, monkeypatch, symbols=("NAS100", "FOOBAR"))
    assert "FOOBAR: skipped" in capsys.readouterr().out
