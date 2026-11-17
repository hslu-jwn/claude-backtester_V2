"""Alpaca US share minute bars downloader (data/alpaca.py): paging, month cache, resume, missing key."""

from datetime import date

import pandas as pd
import pytest

from backtester.data import alpaca


def bar(t, c):
    return {"t": t, "o": c, "h": c + 1, "l": c - 1, "c": c, "v": 100, "n": 3, "vw": c}


def fake_fetch(pages):
    """Returns the pages in order and records each request's params."""
    calls = []

    def fetch(params):
        calls.append(dict(params))
        return pages[len(calls) - 1]

    return fetch, calls


def test_month_pages_are_joined_and_written(tmp_path):
    fetch, calls = fake_fetch(
        [
            {"bars": {"SPY": [bar("2020-01-02T14:30:00Z", 300)]}, "next_page_token": "abc"},
            {"bars": {"SPY": [bar("2020-01-02T14:31:00Z", 301)]}, "next_page_token": None},
        ]
    )
    n = alpaca.download_month("SPY", date(2020, 1, 1), fetch, tmp_path)
    assert n == 2
    assert calls[0]["start"] == "2020-01-01T00:00:00Z" and calls[0]["end"] == "2020-02-01T00:00:00Z"
    assert (
        calls[0]["timeframe"] == "1Min"
        and calls[0]["feed"] == "sip"
        and calls[0]["adjustment"] == "split"
    )
    assert "page_token" not in calls[0] and calls[1]["page_token"] == "abc"
    d = pd.read_csv(tmp_path / "SPY" / "2020-01.csv")
    assert list(d.columns) == alpaca.COLUMNS
    assert d.close.tolist() == [300, 301] and d.ts.iloc[0] == "2020-01-02T14:30:00Z"


def test_empty_month_writes_empty_file(tmp_path):
    fetch, _ = fake_fetch([{"bars": {}, "next_page_token": None}])
    assert alpaca.download_month("SPY", date(2015, 1, 1), fetch, tmp_path) == 0
    assert pd.read_csv(tmp_path / "SPY" / "2015-01.csv").empty


def test_done_month_is_skipped_but_current_month_refetched(tmp_path):
    fetch, calls = fake_fetch([{"bars": {}, "next_page_token": None}] * 3)
    months = [date(2020, 1, 1), date(2020, 2, 1)]
    alpaca.download("SPY", months, fetch, tmp_path, today=date(2020, 2, 10))
    alpaca.download("SPY", months, fetch, tmp_path, today=date(2020, 2, 10))
    assert [c["start"][:7] for c in calls] == ["2020-01", "2020-02", "2020-02"]


def test_months_range():
    assert alpaca.months(date(2019, 11, 1), date(2020, 2, 1)) == [
        date(2019, 11, 1),
        date(2019, 12, 1),
        date(2020, 1, 1),
        date(2020, 2, 1),
    ]


def test_missing_key_raises_with_how_to(monkeypatch):
    monkeypatch.setattr(alpaca, "_secret", lambda name: None)
    with pytest.raises(RuntimeError, match="python -m keyring set backtester-alpaca key_id"):
        alpaca.keys()


def test_current_month_ends_16_minutes_before_now(tmp_path):
    from datetime import UTC, datetime

    fetch, calls = fake_fetch([{"bars": {}, "next_page_token": None}])
    now = datetime(2026, 11, 16, 22, 30, tzinfo=UTC)
    alpaca.download_month("SPY", date(2026, 11, 1), fetch, tmp_path, now=now)
    assert (
        calls[0]["end"] == "2026-11-16T22:14:00Z"
    )  # free plan: the latest 15 minutes are refused (HTTP 403)


def test_batch_splits_symbols_and_pages_into_one_file_each(tmp_path):
    fetch, calls = fake_fetch(
        [
            {"bars": {"AAA": [bar("2020-01-02T05:00:00Z", 10)]}, "next_page_token": "p2"},
            {
                "bars": {
                    "AAA": [bar("2020-01-03T05:00:00Z", 11)],
                    "BBB": [bar("2020-01-02T05:00:00Z", 20)],
                },
                "next_page_token": None,
            },
        ]
    )
    alpaca.download_batch(["AAA", "BBB", "CCC"], "1Day", "2020-01-01", fetch, tmp_path, batch=10)
    assert calls[0]["symbols"] == "AAA,BBB,CCC" and calls[0]["timeframe"] == "1Day"
    assert calls[0]["start"] == "2020-01-01T00:00:00Z" and calls[1]["page_token"] == "p2"
    assert pd.read_csv(tmp_path / "AAA.csv").close.tolist() == [10, 11]
    assert pd.read_csv(tmp_path / "BBB.csv").close.tolist() == [20]
    assert pd.read_csv(
        tmp_path / "CCC.csv"
    ).empty  # no bars: empty file, so a resume does not ask again


def test_batch_skips_done_symbols_and_respects_batch_size(tmp_path):
    (tmp_path / "AAA.csv").write_text(",".join(alpaca.COLUMNS) + "\n")
    fetch, calls = fake_fetch([{"bars": {}, "next_page_token": None}] * 2)
    alpaca.download_batch(
        ["AAA", "BBB", "CCC", "DDD"], "1Day", "2020-01-01", fetch, tmp_path, batch=2
    )
    assert [c["symbols"] for c in calls] == ["BBB,CCC", "DDD"]


def test_batch_end_is_16_minutes_before_now(tmp_path):
    from datetime import UTC, datetime

    fetch, calls = fake_fetch([{"bars": {}, "next_page_token": None}])
    now = datetime(2026, 11, 17, 15, 0, tzinfo=UTC)
    alpaca.download_batch(["AAA"], "30Min", "2016-01-01", fetch, tmp_path, now=now)
    assert calls[0]["end"] == "2026-11-17T14:44:00Z" and calls[0]["timeframe"] == "30Min"


def test_batch_end_date_caps_the_request(tmp_path):
    fetch, calls = fake_fetch([{"bars": {}, "next_page_token": None}])
    alpaca.download_batch(["AAA"], "1Hour", "2015-12-01", fetch, tmp_path, end="2021-09-14")
    assert calls[0]["end"] == "2021-09-14T00:00:00Z" and calls[0]["timeframe"] == "1Hour"
