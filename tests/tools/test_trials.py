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


def test_list_shows_n_daily_sharpe_count_and_variance(tmp_path, capsys):
    from datetime import UTC, date, datetime
    from types import SimpleNamespace

    from backtester.analytics.trial_log import append, make_record

    p = tmp_path / "t.jsonl"
    start, end = date(2021, 3, 1), date(2021, 3, 5)  # 5 weekdays
    for k, rs in enumerate(([1.0, 0.0, -1.0, 2.0, 0.5], [0.5, 0.5, -1.0, 0.0, 2.0])):
        ts = [
            SimpleNamespace(r_net=r, exit_time=datetime(2021, 3, 1 + i, 12, tzinfo=UTC))
            for i, r in enumerate(rs)
        ]
        append(make_record("gap", "gap_fade", {"k": k}, ["X"], start, end, "mt5", ts), p)
    # a manual per-trade line and a count-only line: neither has a daily Sharpe
    main(["--log", str(p), "add", "gap", "gap_fade", "--trades", "50", "--mean", "0.1",
          "--sd", "1.0", "--note", "m"])  # fmt: skip
    main(["--log", str(p), "add", "gap", "gap_fade", "--count", "8", "--note", "old"])
    capsys.readouterr()
    assert main(["--log", str(p), "list"]) == 0
    out = capsys.readouterr().out
    assert "gap" in out and "N=11" in out and "with daily Sharpe=2" in out and "V=" in out
    assert "V=-" not in out


def test_list_empty_log(tmp_path, capsys):
    assert main(["--log", str(tmp_path / "none.jsonl"), "list"]) == 0
    assert "no trials" in capsys.readouterr().out.lower()


def test_add_needs_count_or_stats(tmp_path):
    with pytest.raises(SystemExit):
        main(["--log", str(tmp_path / "t.jsonl"), "add", "gap", "gap_fade"])
