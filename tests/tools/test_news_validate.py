import csv

from backtester.data.news import CSV_COLUMNS
from backtester.tools.news_validate import main


def row(n, timestamp, name="Event", country="US", provider="Provider", note="", precision="minute"):
    data = dict.fromkeys(CSV_COLUMNS, "")
    data.update(
        event_id=str(n),
        dedupe_key=str(n),
        scheduled_date_utc=timestamp[:10],
        scheduled_date_local=timestamp[:10],
        scheduled_timestamp_utc=timestamp if precision == "minute" else "",
        time_precision=precision,
        impact="High",
        impact_rank="3",
        event_name=name,
        country=country,
        source_provider=provider,
        point_in_time_verified="false",
        point_in_time_note=note,
    )
    return data


def run(tmp_path, rows):
    path = tmp_path / "calendar.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        writer.writerows([r[c] for c in CSV_COLUMNS] for r in rows)
    out = tmp_path / "out"
    assert main(["--calendar", str(path), "--out", str(out)]) == 0
    with (out / "deviations.csv").open(encoding="utf-8", newline="") as f:
        deviations = list(csv.DictReader(f))
    return (out / "report.md").read_text(encoding="utf-8"), deviations


def test_anchors_dst_and_imputed(tmp_path):
    rows = [
        row(1, "2024-01-05T13:30:00+00:00", "Non-Farm Employment Change"),
        row(2, "2024-07-05T12:30:00+00:00", "Non-Farm Employment Change"),
        row(3, "2024-02-02T12:30:00+00:00", "Non-Farm Employment Change"),
        row(
            4,
            "2024-03-01T13:30:00+00:00",
            "Non-Farm Employment Change",
            note="release time imputed",
        ),
        row(5, "2024-01-31T19:00:00+00:00", "FOMC Statement"),
        row(6, "2024-08-01T11:00:00+00:00", "Official Bank Rate", "GB"),
    ]
    report, deviations = run(tmp_path, rows)
    assert "Non-Farm Employment Change | US | 4 | 3 | 1 | 1" in report
    assert "FOMC Statement | US | 1 | 1 | 0 | 0" in report
    assert "Official Bank Rate | GB | 1 | 1 | 0 | 0" in report
    assert "2024-02-02" in report and "07:30" in report
    assert any(d["check"] == "anchor" and d["event_id"] == "3" for d in deviations)


def test_consistency_and_coverage(tmp_path):
    rows = [
        row(i, f"2024-01-{i:02}T15:{'30' if i == 6 else '00'}:00+00:00", "Regular")
        for i in range(1, 7)
    ]
    rows += [row(10 + i, f"2024-02-{i:02}T15:00:00+00:00", "Too few") for i in range(1, 5)]
    rows += [
        row(20 + i, f"2025-10-{24 + i:02}T10:00:00+00:00", "Unknown", "XX", "Finance Calendar")
        for i in range(5)
    ]
    rows += [row(30, "2025-11-01", "Day", provider="Finance Calendar", precision="date")]
    report, deviations = run(tmp_path, rows)
    found = [d for d in deviations if d["check"] == "consistency"]
    assert len(found) == 1 and found[0]["event_id"] == "6"
    assert found[0]["mode"] == "10:00:00" and found[0]["mode_share"] == "5/6"
    assert "below 5: 4 rows" in report and "no zone: 5 rows" in report
    assert "2024 | Provider | 10" in report
    assert "2025 | Finance Calendar | 6" in report
    assert "2025 | 1" in report
    assert "Finance-Calendar from 2025-10-24: 6" in report


def test_missing_file(tmp_path, capsys):
    assert main(["--calendar", str(tmp_path / "missing.csv")]) == 2
    assert "cannot load calendar" in capsys.readouterr().err.lower()
