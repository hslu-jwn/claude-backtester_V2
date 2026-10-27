import warnings
from datetime import date

import pytest

from backtester.data.news import CSV_COLUMNS, ImpactWindow, NewsConfig, load_calendar
from backtester.tools import news_clean


def _row(n, utc, local, precision, label, impact="High", **extra):
    row = dict.fromkeys(CSV_COLUMNS, "")
    row.update(
        event_id=f"e{n}",
        scheduled_timestamp_utc=utc,
        scheduled_date_utc=utc[:10] if utc else local,
        scheduled_date_local=local,
        time_precision=precision,
        time_label=label,
        currency="USD",
        country="US",
        impact=impact,
        impact_rank="3" if impact == "High" else "2",
        event_name=f"Event, {n}",
        status="historical_record",
        point_in_time_verified="false",
        point_in_time_note="note",
        dedupe_key=f"k{n}",
    )
    row.update(extra)
    return row


def _write(path, rows):
    import csv

    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, lineterminator="\r\n")
        w.writerow(CSV_COLUMNS)
        for r in rows:
            w.writerow([r[c] for c in CSV_COLUMNS])


def _read(path):
    import csv

    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _make(tmp_path):
    src = tmp_path / "src.csv"
    rows = [
        _row(1, "2024-03-07T20:30:00Z", "2024-03-08", "second", "00:00:00"),
        _row(2, "2024-03-06T20:29:59Z", "2024-03-07", "minute", "23:59:59", impact="Medium"),
        _row(3, "2024-03-08T13:30:00Z", "2024-03-08", "second", "17:00:00"),
        _row(4, "2024-03-09T01:30:00Z", "2024-03-09", "second", "05:00:00"),  # Saturday
    ]
    _write(src, rows)
    return src, rows


def test_clean_rules(tmp_path):
    src, rows = _make(tmp_path)
    before = src.read_bytes()
    out = tmp_path / "out" / "clean.csv"
    total, changed, imputed, left = news_clean.clean_file(src, out)
    assert (total, dict(changed)) == (4, {"High": 1, "Medium": 1})
    assert not imputed
    assert dict(left) == {"High": 1, "Medium": 1}
    assert src.read_bytes() == before
    got = _read(out)
    for i, local in ((0, "2024-03-08"), (1, "2024-03-07")):
        assert got[i]["time_precision"] == "date"
        assert got[i]["scheduled_timestamp_utc"] == ""
        assert got[i]["scheduled_date_utc"] == local
        assert got[i]["time_label"] == ""
        assert got[i]["point_in_time_note"].endswith(news_clean.NOTE)
    assert got[2] == rows[2]  # normal exact row unchanged
    assert got[3] == rows[3]  # weekend row kept
    assert len(got) == 4
    assert out.read_bytes().startswith(b"\xef\xbb\xbf")


def test_output_loads_without_suspicious(tmp_path):
    src, _ = _make(tmp_path)
    out = tmp_path / "clean.csv"
    news_clean.clean_file(src, out)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cal = load_calendar(NewsConfig(path=str(out)))
    counts = dict(cal.quality_counts)
    assert counts.get("suspicious_exact", 0) == 0
    assert counts["weekend"] == 1
    day_only = [e for e in cal.events if e.time_precision == "date"]
    assert [e.day for e in day_only] == [date(2024, 3, 8), date(2024, 3, 7)]
    assert all(e.scheduled_at is None for e in day_only)
    assert any("weekend" in str(w.message) for w in caught)


def test_untouched_rows_are_byte_identical(tmp_path):
    src = tmp_path / "src.csv"
    _write(src, [_row(1, "2024-03-08T13:30:00Z", "2024-03-08", "second", "17:00:00")])
    out = tmp_path / "clean.csv"
    news_clean.clean_file(src, out)
    assert out.read_bytes() == src.read_bytes()


def test_news_config_defaults():
    config = NewsConfig()
    assert config.high == ImpactWindow(2.0, 2.0)
    assert config.medium == ImpactWindow(0.0, 0.0)
    assert config.enabled is False


# Imputation (rule set by the user, 2026-10-27): NFP-style 08:30 New York.
def _sib(n, local_date, utc, **extra):
    return _row(n, utc, local_date, "minute", utc[11:19], event_name="NFP", **extra)


def _lost(n, local_date, **extra):
    return _row(n, "", local_date, "date", "", event_name="NFP", **extra)


def _lost_exact(n, local_date, prev_utc_day, **extra):
    # a source row that rule 1 turns into day-only (23:59:59 label)
    return _row(
        n, f"{prev_utc_day}T20:29:59Z", local_date, "minute", "23:59:59", event_name="NFP", **extra
    )


def _run(tmp_path, rows):
    src = tmp_path / "s.csv"
    _write(src, rows)
    out = tmp_path / "o.csv"
    result = news_clean.clean_file(src, out)
    return result, _read(out), rows


# 2024-03-01 and 2024-03-08 are EST (13:30Z); 2024-03-15 is EDT (12:30Z, DST began 03-10).
SIBS = [
    _sib(1, "2024-03-01", "2024-03-01T13:30:00Z"),
    _sib(2, "2024-03-08", "2024-03-08T13:30:00Z"),
    _sib(3, "2024-03-15", "2024-03-15T12:30:00Z"),
]


def test_imputation_dst_both_sides(tmp_path):
    rows = [
        *SIBS,
        _lost_exact(4, "2024-03-05", "2024-03-04"),  # EST
        _lost_exact(5, "2024-03-12", "2024-03-11"),  # EDT
    ]
    (_, _, imputed, left), got, _ = _run(tmp_path, rows)
    assert dict(imputed) == {"High": 2} and not left
    est, edt = got[3], got[4]
    assert est["scheduled_timestamp_utc"] == "2024-03-05T13:30:00Z"
    assert edt["scheduled_timestamp_utc"] == "2024-03-12T12:30:00Z"
    for r, day in ((est, "2024-03-05"), (edt, "2024-03-12")):
        assert r["scheduled_date_local"] == day  # the row's own day is kept
        assert r["scheduled_date_utc"] == day
        assert r["time_precision"] == "minute"
        assert r["time_label"] == "08:30"
        assert r["point_in_time_note"].endswith(
            "; release time imputed 2026-10-27 from 3 of 3 occurrences (08:30 America/New_York)"
        )
    assert got[:3] == rows[:3]  # siblings untouched
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cal = load_calendar(NewsConfig(path=str(tmp_path / "o.csv")))
    assert [e.time_precision for e in cal.events[3:]] == ["minute", "minute"]


def test_utc_date_can_differ_from_local_date(tmp_path):
    sibs = [
        _row(i, f"2024-06-0{i}T01:00:00Z", f"2024-06-0{i}", "minute", "x", event_name="NFP")
        for i in (3, 4, 5)
    ]  # 01:00Z = 21:00 EDT of the previous evening; local time 21:00
    (_, _, imputed, _), got, _ = _run(tmp_path, [*sibs, _lost_exact(9, "2024-06-10", "2024-06-09")])
    assert dict(imputed) == {"High": 1}
    assert got[3]["scheduled_timestamp_utc"] == "2024-06-11T01:00:00Z"
    assert got[3]["scheduled_date_utc"] == "2024-06-11"
    assert got[3]["scheduled_date_local"] == "2024-06-10"


def test_two_siblings_not_enough(tmp_path):
    rows = [*SIBS[:2], _lost_exact(4, "2024-03-05", "2024-03-04")]
    (_, _, imputed, left), got, _ = _run(tmp_path, rows)
    assert not imputed and dict(left) == {"High": 1}
    assert got[2]["time_precision"] == "date" and got[2]["scheduled_timestamp_utc"] == ""


def test_split_mode_not_imputed(tmp_path):
    # 08:30 x2 vs 10:00 x2 vs 14:00 x1 -> mode share 2/5 = 40 % < 60 %
    sibs = [
        _sib(1, "2024-03-01", "2024-03-01T13:30:00Z"),
        _sib(2, "2024-03-08", "2024-03-08T13:30:00Z"),
        _sib(3, "2024-03-02", "2024-03-02T15:00:00Z"),
        _sib(4, "2024-03-09", "2024-03-09T15:00:00Z"),
        _sib(5, "2024-03-03", "2024-03-03T19:00:00Z"),
    ]
    (_, _, imputed, left), _, _ = _run(
        tmp_path, [*sibs, _lost_exact(9, "2024-03-05", "2024-03-04")]
    )
    assert not imputed and dict(left) == {"High": 1}


def test_threshold_exactly_60_percent_imputes(tmp_path):
    sibs = [
        _sib(1, "2024-03-01", "2024-03-01T13:30:00Z"),
        _sib(2, "2024-03-08", "2024-03-08T13:30:00Z"),
        _sib(3, "2024-03-15", "2024-03-15T12:30:00Z"),
        _sib(4, "2024-03-02", "2024-03-02T15:00:00Z"),
        _sib(5, "2024-03-09", "2024-03-09T15:00:00Z"),
    ]
    (_, _, imputed, _), got, _ = _run(tmp_path, [*sibs, _lost_exact(9, "2024-03-05", "2024-03-04")])
    assert dict(imputed) == {"High": 1}
    assert "from 3 of 5 occurrences" in got[5]["point_in_time_note"]


@pytest.mark.parametrize("other", [{"currency": "EUR"}, {"event_name": "Other"}])
def test_siblings_must_be_same_event_and_currency(tmp_path, other):
    sibs = [{**s, **other} for s in SIBS]
    (_, _, imputed, left), _, _ = _run(
        tmp_path, [*sibs, _lost_exact(9, "2024-03-05", "2024-03-04")]
    )
    assert not imputed and dict(left) == {"High": 1}


def test_unknown_country_and_medium_impact(tmp_path):
    unk = [{**s, "country": "XX"} for s in SIBS]
    (_, _, imputed, left), _, _ = _run(
        tmp_path, [*unk, _lost_exact(9, "2024-03-05", "2024-03-04", country="XX")]
    )
    assert not imputed and dict(left) == {"High": 1}
    med = [{**s, "impact": "Medium", "impact_rank": "2"} for s in SIBS]
    lost = _lost_exact(9, "2024-03-05", "2024-03-04", impact="Medium", impact_rank="2")
    (_, _, imputed, _), got, _ = _run(tmp_path, [*med, lost])
    assert dict(imputed) == {"Medium": 1}
    assert got[3]["scheduled_timestamp_utc"] == "2024-03-05T13:30:00Z"


def test_other_date_rows_untouched_and_suspicious_not_siblings(tmp_path):
    other_date = _row(7, "", "2024-03-06", "date", "", event_name="NFP")
    # suspicious exact rows never count as siblings (2 good siblings + 1 suspicious)
    rows = [
        *SIBS[:2],
        _lost_exact(3, "2024-03-15", "2024-03-14"),
        other_date,
        _lost_exact(9, "2024-03-05", "2024-03-04"),
    ]
    (_, _, imputed, left), got, _ = _run(tmp_path, rows)
    assert not imputed and dict(left) == {"High": 2}
    assert got[3] == other_date
