"""Trial log: append-only JSONL, dedupe on read, count-only lines.
Spec: risk-management.md > Trial log and deflated Sharpe (ROADMAP 12.10)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace

import pytest

from backtester.analytics import trial_log as tl
from backtester.analytics.trial_log import (
    TrialRecord,
    append,
    count_only,
    default_path,
    family_summary,
    family_trials,
    make_record,
    read_all,
)

R = [1.0, -1.0, 2.0, -0.5, 1.5]
START, END = date(2020, 1, 1), date(2021, 1, 1)


def trades_of(values, first=date(2020, 1, 6)):
    """One trade per value, exiting at noon UTC on consecutive days from `first`."""
    return [
        SimpleNamespace(
            r_net=v, exit_time=datetime.combine(first + timedelta(days=i), time(12), tzinfo=UTC)
        )
        for i, v in enumerate(values)
    ]


def rec(family="f", settings=None, r=R, strategy="s", symbols=("A",), source="histdata"):
    return make_record(
        family, strategy, settings or {"x": 1}, list(symbols),
        date(2020, 1, 1), date(2021, 1, 1), source, trades_of(r),
    )  # fmt: skip


def test_default_path_is_results_trials_jsonl():
    assert default_path().name == "trials.jsonl" and default_path().parent == tl.RESULTS_DIR


def test_record_fields_and_stats():
    r = rec()
    assert r.trades == 5 and r.net_r == pytest.approx(3.0)
    assert r.mean == pytest.approx(0.6) and r.sharpe == pytest.approx(r.mean / r.sd)
    assert r.start == "2020-01-01" and r.end == "2021-01-01" and r.written
    assert r.count == 1


def test_record_daily_fields_use_weekdays_of_the_period_with_empty_days_zero():
    import numpy as np

    from backtester.analytics.daily import daily_net_r

    ts = trades_of(R)  # Mon 6 Jan .. Fri 10 Jan 2020
    r = make_record("f", "s", {}, ["A"], date(2020, 1, 6), date(2020, 1, 17), "mt5", ts)
    assert r.days == 10  # two full weeks, five empty days are zeros
    d = np.array([1.0, -1.0, 2.0, -0.5, 1.5, 0, 0, 0, 0, 0])
    assert daily_net_r(ts, date(2020, 1, 6), date(2020, 1, 17)).tolist() == d.tolist()
    assert r.day_mean == pytest.approx(d.mean()) and r.day_sd == pytest.approx(d.std(ddof=1))
    assert r.day_sharpe == pytest.approx(d.mean() / d.std(ddof=1))
    assert r.day_skew is not None and r.day_kurt is not None
    assert r.net_r == pytest.approx(3.0) and r.trades == 5  # per-trade fields unchanged


def test_old_lines_without_daily_fields_are_read_and_excluded_from_v(tmp_path):
    import json

    p = tmp_path / "t.jsonl"
    old = {"family": "f", "strategy": "s", "settings": {"x": 0}, "symbols": ["A"],
           "start": "2020-01-01", "end": "2021-01-01", "source": "mt5", "written": "2020",
           "trades": 5, "net_r": 3.0, "mean": 0.6, "sd": 1.0, "skew": 0.0, "kurt": 3.0,
           "sharpe": 0.6, "count": 1, "note": ""}  # fmt: skip
    p.write_text(json.dumps(old) + "\n", encoding="utf-8")
    append(rec(settings={"x": 1}), p)
    lines = family_trials("f", p)
    assert len(lines) == 2 and lines[0].day_sharpe is None and lines[0].days is None
    n, sharpes = family_summary(lines)
    assert n == 2 and sharpes == [lines[1].day_sharpe]


def test_key_depends_on_all_identity_fields_and_sorts_settings():
    base = rec(settings={"a": 1, "b": 2})
    assert base.key == rec(settings={"b": 2, "a": 1}).key
    for other in (
        rec(family="g"), rec(strategy="t"), rec(settings={"a": 2, "b": 2}),
        rec(symbols=("A", "B")), rec(source="mt5"),
    ):  # fmt: skip
        assert other.key != base.key


def test_append_only_file_grows_and_is_not_rewritten(tmp_path):
    p = tmp_path / "trials.jsonl"
    append(rec(), p)
    first = p.read_text(encoding="utf-8")
    append(rec(settings={"x": 2}), p)
    both = p.read_text(encoding="utf-8")
    assert both.startswith(first) and both.count("\n") == 2


def test_read_dedupes_last_line_per_key_wins(tmp_path):
    p = tmp_path / "t.jsonl"
    append(rec(r=[1.0, 2.0, 3.0]), p)
    append(rec(settings={"x": 9}), p)
    append(rec(r=[5.0, -1.0, 2.0]), p)  # same key as the first
    lines = read_all(p)
    assert len(lines) == 2
    same = next(r for r in lines if r.settings == {"x": 1})
    assert same.net_r == pytest.approx(6.0)
    assert p.read_text(encoding="utf-8").count("\n") == 3  # file untouched


def test_missing_file_is_empty(tmp_path):
    assert read_all(tmp_path / "nope.jsonl") == []


def test_family_trials_filters_by_family(tmp_path):
    p = tmp_path / "t.jsonl"
    append(rec(family="a"), p)
    append(rec(family="b"), p)
    assert [r.family for r in family_trials("a", p)] == ["a"]


def test_count_only_lines_count_for_n_but_not_v(tmp_path):
    p = tmp_path / "t.jsonl"
    append(rec(settings={"x": 1}), p)
    append(rec(settings={"x": 2}, r=[2.0, -1.0, 1.0, 1.0]), p)
    append(count_only("f", "s", 8, note="old tests"), p)
    n, sharpes = family_summary(family_trials("f", p))
    assert n == 10 and len(sharpes) == 2  # daily Sharpes
    assert count_only("f", "s", 8, note="old tests").sharpe is None


def test_count_only_same_note_is_replaced_different_note_is_not(tmp_path):
    p = tmp_path / "t.jsonl"
    append(count_only("f", "s", 8, note="a"), p)
    append(count_only("f", "s", 5, note="a"), p)
    append(count_only("f", "s", 3, note="b"), p)
    assert family_summary(family_trials("f", p))[0] == 8  # 5 + 3


def test_count_only_rejects_nonpositive():
    with pytest.raises(ValueError):
        count_only("f", "s", 0)


def test_corrupt_and_blank_lines_are_skipped_with_a_warning(tmp_path):
    p = tmp_path / "t.jsonl"
    append(rec(), p)
    with p.open("a", encoding="utf-8") as f:
        f.write("\n{not json\n" + '{"family": "f"}\n')  # blank, corrupt, missing fields
    append(rec(settings={"x": 2}), p)
    with pytest.warns(UserWarning, match="trials"):
        lines = read_all(p)
    assert len(lines) == 2


def test_roundtrip_preserves_record(tmp_path):
    p = tmp_path / "t.jsonl"
    r = rec()
    append(r, p)
    assert read_all(p) == [r]
    assert isinstance(read_all(p)[0], TrialRecord)


def test_few_trades_have_no_sharpe():
    assert rec(r=[1.0]).sharpe is None and rec(r=[]).trades == 0
