"""CSV-format addendum: only generated, synthetic CSV bytes are read."""

import csv
import hashlib
import io
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from backtester.data.news import EventResults, NewsConfig, load_calendar, relevant

HEADER = [
    "event_id",
    "scheduled_timestamp_utc",
    "scheduled_date_utc",
    "scheduled_date_local",
    "source_timezone",
    "time_precision",
    "time_label",
    "time_window_start_utc",
    "time_window_end_utc",
    "currency",
    "country",
    "impact",
    "impact_rank",
    "event_name",
    "actual",
    "forecast",
    "previous",
    "status",
    "source_provider",
    "source_name",
    "source_url",
    "source_record_id",
    "source_retrieved_at_utc",
    "source_updated_at_utc",
    "known_at_utc",
    "point_in_time_verified",
    "point_in_time_note",
    "provenance_quality",
    "dedupe_key",
]


def row(**changes):
    return (
        dict.fromkeys(HEADER, "")
        | {
            "event_id": "one",
            "dedupe_key": "synthetic-one",
            "scheduled_timestamp_utc": "2020-01-02T13:30:00Z",
            "scheduled_date_utc": "2020-01-02",
            "scheduled_date_local": "2020-01-02",
            "source_timezone": "America/New_York",
            "time_precision": "minute",
            "time_label": "08:30:00",
            "currency": "USD",
            "country": "US",
            "impact": "High",
            "impact_rank": "3",
            "event_name": 'Synthetic, "release"',
            "actual": "2.5%",
            "forecast": "2%",
            "previous": "1%",
            "point_in_time_verified": "false",
            "source_provider": "synthetic-A",
        }
        | changes
    )


def write_csv(tmp_path, rows=None, header=HEADER):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(header)
    for item in rows if rows is not None else [row()]:
        writer.writerow([item.get(c, "") for c in header])
    path = tmp_path / "synthetic.csv"
    path.write_bytes(stream.getvalue().encode("utf-8-sig"))
    return path


def test_bom_quoting_hash_and_results_separate(tmp_path):
    path = write_csv(tmp_path)
    calendar = load_calendar(NewsConfig(path=str(path)))
    assert calendar.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    event = calendar.events[0]
    assert event.name == 'Synthetic, "release"'
    assert event.scheduled_at == datetime(2020, 1, 2, 13, 30, tzinfo=UTC)
    assert not any(hasattr(event, c) for c in ("actual", "forecast", "previous"))
    assert not hasattr(calendar, "results")
    results = EventResults.from_csv(path)
    delay = timedelta(seconds=15)
    assert (
        results.actual("one", event.scheduled_at + delay - timedelta(microseconds=1), delay) is None
    )
    assert results.actual("one", event.scheduled_at + delay, delay) == "2.5%"


@pytest.mark.parametrize(
    "header", [HEADER[:-1], HEADER + ["extra"], HEADER[::-1], HEADER[:-1] + ["event_id"]]
)
def test_strict_header(tmp_path, header):
    with pytest.raises(ValueError, match="header"):
        load_calendar(NewsConfig(path=str(write_csv(tmp_path, header=header))))


@pytest.mark.parametrize(
    "changes",
    [
        {"event_id": ""},
        {"dedupe_key": ""},
        {"impact": "Low"},
        {"impact_rank": "2"},
        {"time_precision": "hour"},
        {"scheduled_timestamp_utc": ""},
        {"scheduled_timestamp_utc": "bad"},
        {"scheduled_timestamp_utc": "2020-01-02T13:30:00"},
        {"scheduled_date_utc": "bad"},
        {"scheduled_date_utc": "2020-01-03"},
        {"point_in_time_verified": "maybe"},
        {"known_at_utc": "bad"},
        {
            "time_precision": "range",
            "scheduled_timestamp_utc": "",
            "time_window_start_utc": "2020-01-02T13:00:00Z",
        },
        {
            "time_precision": "range",
            "scheduled_timestamp_utc": "",
            "time_window_start_utc": "2020-01-02T14:00:00Z",
            "time_window_end_utc": "2020-01-02T13:00:00Z",
        },
    ],
)
def test_invalid_rows_fail(tmp_path, changes):
    with pytest.raises(ValueError):
        load_calendar(NewsConfig(path=str(write_csv(tmp_path, [row(**changes)]))))


@pytest.mark.parametrize("column", ["event_id", "dedupe_key"])
def test_duplicate_identity(tmp_path, column):
    second = row(event_id="two", dedupe_key="two")
    second[column] = row()[column]
    with pytest.raises(ValueError, match=column):
        load_calendar(NewsConfig(path=str(write_csv(tmp_path, [row(), second]))))


@pytest.mark.parametrize("suffix", [",extra", ""])
def test_row_width(tmp_path, suffix):
    path = write_csv(tmp_path)
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    lines[-1] = lines[-1] + suffix if suffix else lines[-1].rsplit(",", 1)[0]
    path.write_text("\n".join(lines), encoding="utf-8-sig")
    with pytest.raises(ValueError, match="columns"):
        load_calendar(NewsConfig(path=str(path)))


@pytest.mark.parametrize("precision", ["date", "unknown", "range"])
def test_blank_timestamps_and_local_day(tmp_path, precision):
    values = {"scheduled_timestamp_utc": "", "scheduled_date_utc": "", "time_precision": precision}
    if precision == "range":
        values |= {
            "time_window_start_utc": "2020-01-02T12:00:00Z",
            "time_window_end_utc": "2020-01-02T15:00:00Z",
        }
    calendar = load_calendar(NewsConfig(path=str(write_csv(tmp_path, [row(**values)]))))
    assert calendar.events[0].scheduled_at is None
    assert calendar.events[0].day.isoformat() == "2020-01-02"


@pytest.mark.parametrize("tz", ["UTC", "America/New_York", "Europe/Zurich"])
@pytest.mark.parametrize("stamp", ["2020-03-08T13:30:00Z", "2020-11-01T14:30:00+01:00"])
def test_utc_dst_independent_of_environment(tmp_path, monkeypatch, tz, stamp):
    monkeypatch.setenv("TZ", tz)
    day = stamp[:10]
    path = write_csv(tmp_path, [row(scheduled_timestamp_utc=stamp, scheduled_date_utc=day)])
    with pytest.warns(UserWarning, match="weekend"):
        calendar = load_calendar(NewsConfig(path=str(path)))
    assert calendar.events[0].scheduled_at.hour == 13
    assert calendar.events[0].scheduled_at.tzinfo == UTC


@pytest.mark.parametrize("label", ["00:00:00", "23:59:59"])
def test_counted_quality_warning_or_error(tmp_path, label):
    path = write_csv(
        tmp_path, [row(time_label=label), row(event_id="two", dedupe_key="two", time_label=label)]
    )
    config = NewsConfig(path=str(path))
    with pytest.warns(UserWarning, match="suspicious_exact=2"):
        load_calendar(config)
    with pytest.raises(ValueError, match="suspicious_exact=2"):
        load_calendar(replace(config, quality_errors=True))


def test_composition_and_skip_counts(tmp_path):
    path = write_csv(
        tmp_path,
        [
            row(),
            row(
                event_id="two",
                dedupe_key="two",
                source_provider="synthetic-B",
                scheduled_timestamp_utc="2025-10-24T13:30:00Z",
                scheduled_date_utc="2025-10-24",
            ),
        ],
    )
    with pytest.warns(UserWarning, match="source_boundary_changes=1"):
        calendar = load_calendar(NewsConfig(path=str(path)))
    assert calendar.high_counts == (("synthetic-A", 2020, 1), ("synthetic-B", 2025, 1))
    with pytest.raises(ValueError, match="source_boundary_changes=1"):
        load_calendar(NewsConfig(path=str(path), quality_errors=True))
    path = write_csv(tmp_path, [row(time_precision="date", scheduled_timestamp_utc="")])
    with pytest.warns(UserWarning, match="uncertain_skipped=1"):
        load_calendar(NewsConfig(path=str(path), uncertain_policy="skip"))


def test_missing_calendar_and_simultaneous_global(tmp_path, caplog):
    assert load_calendar(NewsConfig(path=str(tmp_path / "missing.csv"))) is None
    assert "no calendar" in caplog.text
    path = write_csv(
        tmp_path, [row(), row(event_id="two", dedupe_key="two", currency="ALL", country="GLOBAL")]
    )
    calendar = load_calendar(NewsConfig(path=str(path)))
    assert len(calendar.events) == 2
    config = NewsConfig()
    assert not relevant(calendar.events[1], "EURUSD", config)
    mapping = dict(config.instruments)
    mapping["EURUSD"] = replace(mapping["EURUSD"], include_global=True)
    assert relevant(calendar.events[1], "EURUSD", replace(config, instruments=mapping))


def test_weekend_counts_can_be_errors_and_empty_csv_rejected(tmp_path):
    path = write_csv(
        tmp_path,
        [row(scheduled_timestamp_utc="2020-01-04T13:30:00Z", scheduled_date_utc="2020-01-04")],
    )
    with pytest.warns(UserWarning, match="weekend=1"):
        calendar = load_calendar(NewsConfig(path=str(path)))
    assert dict(calendar.quality_counts)["weekend"] == 1
    with pytest.raises(ValueError, match="weekend=1"):
        load_calendar(NewsConfig(path=str(path), quality_errors=True))
    path = write_csv(tmp_path, [])
    with pytest.raises(ValueError, match="no events"):
        load_calendar(NewsConfig(path=str(path)))
