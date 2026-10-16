"""trials CLI: add / list. Spec: risk-management.md > Trial log and deflated Sharpe."""

from __future__ import annotations

import pytest

from backtester.analytics.trial_log import family_summary, family_trials
from backtester.tools.trials import main


def test_add_count_only_backfill(tmp_path):
    p = tmp_path / "t.jsonl"
    assert main(["--log", str(p), "add", "gap", "gap_fade", "--count", "12", "--note", "old"]) == 0
    n, sharpes = family_summary(family_trials("gap", p))
    assert n == 12 and sharpes == []


def test_add_with_stats(tmp_path):
    p = tmp_path / "t.jsonl"
    main([
        "--log", str(p), "add", "gap", "gap_fade", "--trades", "100", "--mean", "0.1",
        "--sd", "1.0", "--note", "run 3",
    ])  # fmt: skip
    (line,) = family_trials("gap", p)
    assert line.trades == 100 and line.sharpe == pytest.approx(0.1)
    assert line.count == 1 and line.note == "run 3"


def test_list_shows_n_sharpe_count_and_variance(tmp_path, capsys):
    p = tmp_path / "t.jsonl"
    for mean in ("0.1", "0.3"):
        main(["--log", str(p), "add", "gap", "gap_fade", "--trades", "50", "--mean", mean,
              "--sd", "1.0", "--note", f"m{mean}"])  # fmt: skip
    main(["--log", str(p), "add", "gap", "gap_fade", "--count", "8", "--note", "old"])
    capsys.readouterr()
    assert main(["--log", str(p), "list"]) == 0
    out = capsys.readouterr().out
    assert "gap" in out and "N=10" in out and "with Sharpe=2" in out and "V=0.02" in out


def test_list_empty_log(tmp_path, capsys):
    assert main(["--log", str(tmp_path / "none.jsonl"), "list"]) == 0
    assert "no trials" in capsys.readouterr().out.lower()


def test_add_needs_count_or_stats(tmp_path):
    with pytest.raises(SystemExit):
        main(["--log", str(tmp_path / "t.jsonl"), "add", "gap", "gap_fade"])
