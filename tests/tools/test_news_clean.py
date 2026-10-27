import warnings
from datetime import date

from backtester.data.news import CSV_COLUMNS, NewsConfig, load_calendar
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
    total, changed = news_clean.clean_file(src, out)
    assert (total, dict(changed)) == (4, {"High": 1, "Medium": 1})
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
