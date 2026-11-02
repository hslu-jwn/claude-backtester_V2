"""Read-only calendar validation report. Spec: docs/news.md > Real-calendar validation."""

import argparse
import csv
import hashlib
import io
import sys
import warnings
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

from backtester.data.news import NewsConfig, load_calendar
from backtester.paths import HOME_DIR
from backtester.tools.news_clean import COUNTRY_ZONES

# Only fixed published schedules belong here; variable schedules use consistency checks.
ANCHORS = (
    ("Non-Farm Employment Change", "US", "America/New_York", "08:30:00"),
    ("CPI m/m", "US", "America/New_York", "08:30:00"),
    ("CPI y/y", "US", "America/New_York", "08:30:00"),
    ("Core CPI m/m", "US", "America/New_York", "08:30:00"),
    ("FOMC Statement", "US", "America/New_York", "14:00:00"),
    ("Official Bank Rate", "GB", "Europe/London", "12:00:00"),
)
FIELDS = (
    "check",
    "event_id",
    "event_name",
    "country",
    "date",
    "utc_time",
    "local_time",
    "source_provider",
    "time_precision",
    "precision_note",
    "expected",
    "mode",
    "mode_share",
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calendar", default="data/news/economic_events.csv")
    parser.add_argument("--out", default="results/news_validation")
    args = parser.parse_args(argv)
    path = Path(args.calendar)
    if not path.is_absolute():
        path = HOME_DIR / path
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            calendar = load_calendar(NewsConfig(path=str(path)))
        if calendar is None:
            raise FileNotFoundError(path)
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != calendar.sha256:
            raise ValueError("calendar changed during loading")
        notes = {
            r["event_id"]: r["point_in_time_note"]
            for r in csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""))
        }
    except (OSError, ValueError, UnicodeError, csv.Error) as exc:
        print(f"Cannot load calendar: {exc}", file=sys.stderr)
        return 2

    events = calendar.events
    exact = [e for e in events if e.time_precision in ("minute", "second")]
    deviations = []
    lines = [
        "# Real-calendar validation",
        "",
        f"SHA256: {calendar.sha256}",
        f"Loaded rows: {len(events)}",
        "",
        "## Loader counts",
        "",
    ]
    for label, counts in (
        ("Impact", Counter(e.impact for e in events)),
        ("Precision", Counter(e.time_precision for e in events)),
    ):
        lines.append(f"{label}: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    lines.append(f"Loader warning counters: {dict(calendar.quality_counts) or 'none'}")
    lines.extend(f"- {w.message}" for w in caught)
    lines.extend(
        [
            "",
            "## Fixed schedule anchors",
            "",
            "Event | Country | Checked | Matching | Deviating | Imputed",
            "--- | --- | ---: | ---: | ---: | ---:",
        ]
    )
    passed = failed = 0

    def record(kind, event, local, expected="", mode="", share=""):
        return {
            "check": kind,
            "event_id": event.event_id,
            "event_name": event.name,
            "country": event.country,
            "date": local.date().isoformat(),
            "utc_time": event.scheduled_at.isoformat(),
            "local_time": local.strftime("%H:%M:%S"),
            "source_provider": event.source_provider,
            "time_precision": event.time_precision,
            "precision_note": notes[event.event_id],
            "expected": expected,
            "mode": mode,
            "mode_share": share,
        }

    anchor_details = []
    for name, country, zone, expected in ANCHORS:
        rows = [e for e in exact if e.impact == "High" and e.name == name and e.country == country]
        bad = []
        for e in rows:
            local = e.scheduled_at.astimezone(ZoneInfo(zone))
            if local.strftime("%H:%M:%S") != expected:
                bad.append(record("anchor", e, local, expected=expected))
        deviations.extend(bad)
        imputed = sum("release time imputed" in notes[e.event_id].lower() for e in rows)
        lines.append(
            f"{name} | {country} | {len(rows)} | {len(rows) - len(bad)} | {len(bad)} | {imputed}"
        )
        if rows:
            if bad:
                failed += 1
            else:
                passed += 1
        for d in bad:
            anchor_details.append(
                f"- {name} ({country}): {d['date']}, UTC {d['utc_time']}, local "
                f"{d['local_time']}, provider {d['source_provider']}, "
                f"precision {d['time_precision']}; note: {d['precision_note']}"
            )
    lines.extend(
        [
            "",
            "Anchor deviations:",
            *(anchor_details or ["- None"]),
            "",
            "Imputed is a subset of checked rows; unchecked anchors are excluded from pass/fail.",
        ]
    )
    groups = defaultdict(list)
    for e in exact:
        groups[e.name, e.country].append(e)
    no_zone = below = 0
    ranking = []
    for (name, country), rows in sorted(groups.items()):
        if country not in COUNTRY_ZONES:
            no_zone += len(rows)
            continue
        if len(rows) < 5:
            below += len(rows)
            continue
        zone = ZoneInfo(COUNTRY_ZONES[country])
        local_rows = [(e, e.scheduled_at.astimezone(zone)) for e in rows]
        times = Counter(t.strftime("%H:%M:%S") for _, t in local_rows)
        mode, count = min(times.items(), key=lambda pair: (-pair[1], pair[0]))

        def seconds(value):
            h, m, s = map(int, value.split(":"))
            return h * 3600 + m * 60 + s

        mode_seconds = seconds(mode)
        bad = []
        for e, local in local_rows:
            delta = abs(seconds(local.strftime("%H:%M:%S")) - mode_seconds)
            if min(delta, 86400 - delta) > 300:
                bad.append(record("consistency", e, local, mode=mode, share=f"{count}/{len(rows)}"))
        deviations.extend(bad)
        if bad:
            ranking.append((len(bad), name, country, mode, count, len(rows)))
    consistency_count = sum(d["check"] == "consistency" for d in deviations)
    lines.extend(
        [
            "",
            "## Consistency",
            "",
            f"Not checked: no zone: {no_zone} rows; below 5: {below} rows.",
            "Tied modes use the earliest local time. Differences wrap across midnight.",
            "",
            "Event | Country | Deviations | Mode | Mode share",
            "--- | --- | ---: | --- | ---:",
        ]
    )
    for n, name, country, mode, count, total in sorted(ranking, key=lambda x: (-x[0], x[1], x[2]))[
        :20
    ]:
        lines.append(f"{name} | {country} | {n} | {mode} | {count}/{total}")

    def represented_day(event):
        return event.day or event.window_start.date()

    high = [e for e in events if e.impact == "High"]
    day_only = [e for e in events if e.time_precision in ("date", "unknown")]
    high_day = sum(e.time_precision in ("date", "unknown") for e in high)
    share = high_day / len(high) if high else 0
    lines.extend(
        [
            "",
            "## Coverage",
            "",
            "High rows by year and provider:",
            "",
            "Year | Provider | Rows",
            "--- | --- | ---:",
        ]
    )
    for (year, provider), n in sorted(
        Counter((represented_day(e).year, e.source_provider) for e in high).items()
    ):
        lines.append(f"{year} | {provider} | {n}")
    finance = sum(
        e.source_provider.casefold().replace("-", " ") == "finance calendar"
        and represented_day(e) >= date(2025, 10, 24)
        for e in high
    )
    weekdays = sum(represented_day(e).weekday() < 5 for e in events)
    lines.extend(
        [
            "",
            f"Finance-Calendar from 2025-10-24: {finance} High rows",
            f"Weekday share (all rows, UTC represented date): {weekdays}/{len(events)} ({weekdays / len(events):.2%})",
            "",
            "Day-only rows by year (all impacts):",
            "",
            "Year | Rows",
            "--- | ---:",
        ]
    )
    for year, n in sorted(Counter(represented_day(e).year for e in day_only).items()):
        lines.append(f"{year} | {n}")
    summary = (
        f"Anchors passed: {passed}, failed: {failed}; consistency deviations: {consistency_count}; "
        f"High day-only: {high_day}/{len(high)} ({share:.2%})"
    )
    lines.extend(["", "## Summary", "", summary, ""])
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    with (out / "deviations.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(deviations)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
