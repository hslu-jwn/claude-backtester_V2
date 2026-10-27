"""Write a cleaned copy of the economic calendar CSV (ROADMAP V2.6d step 3). Spec: docs/news.md.

    python -m backtester.tools.news_clean SOURCE.csv [--out data/news/economic_events.csv]

Rule 1: rows labelled exact (second/minute) at 00:00:00 or 23:59:59 lost their real release
time in the source; they become day-only rows on the local date.
Rule 2 (rule set by the user, 2026-10-27): such a row gets the usual release time of the same
event (same name, currency, country; exact non-suspicious rows only) as wall-clock time in the
event's home zone, if at least 3 siblings exist and the most common local time covers >= 60 %.
Everything else is copied unchanged (same columns, order, values, BOM and line ending). The
source is never modified.
"""

import argparse
import csv
import io
import sys
import warnings
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from backtester.data.news import CSV_COLUMNS, NewsConfig, load_calendar

NOTE = (
    "; cleaned 2026-10-27: release time lost in the source (00:00 / 23:59:59 Asia/Tehran), "
    "day-only on the local date"
)
SUSPICIOUS_LABELS = ("00:00:00", "23:59:59")

COUNTRY_ZONES = {
    "US": "America/New_York",
    "EU": "Europe/Berlin",
    "DE": "Europe/Berlin",
    "GB": "Europe/London",
    "JP": "Asia/Tokyo",
    "AU": "Australia/Sydney",
    "NZ": "Pacific/Auckland",
    "CA": "America/Toronto",
    "CH": "Europe/Zurich",
    "CN": "Asia/Shanghai",
    "KR": "Asia/Seoul",
    "MY": "Asia/Kuala_Lumpur",
    "IN": "Asia/Kolkata",
    "SE": "Europe/Stockholm",
    "NO": "Europe/Oslo",
}


@dataclass(frozen=True, slots=True)
class ImputeConfig:
    min_siblings: int = 3
    min_share: float = 0.6
    zones: dict[str, str] = field(default_factory=lambda: dict(COUNTRY_ZONES))


def is_suspicious(row: dict[str, str]) -> bool:
    return row["time_precision"] in ("second", "minute") and row["time_label"] in SUSPICIOUS_LABELS


def _event_key(row: dict[str, str]) -> tuple[str, str, str]:
    return row["event_name"], row["currency"], row["country"]


def _usual_times(rows: list[dict[str, str]], cfg: ImputeConfig) -> dict:
    """Event key -> (local time, siblings agreeing, siblings, zone); unusable events absent."""
    local_times: dict[tuple[str, str, str], list[time]] = {}
    for row in rows:
        if row["time_precision"] not in ("second", "minute") or is_suspicious(row):
            continue
        zone = cfg.zones.get(row["country"])
        if zone is None or not row["scheduled_timestamp_utc"]:
            continue
        at = datetime.fromisoformat(row["scheduled_timestamp_utc"]).astimezone(ZoneInfo(zone))
        local_times.setdefault(_event_key(row), []).append(at.time().replace(second=0))
    out = {}
    for key, times in local_times.items():
        mode, agree = Counter(times).most_common(1)[0]
        if len(times) >= cfg.min_siblings and agree >= cfg.min_share * len(times):
            out[key] = mode, agree, len(times), cfg.zones[key[2]]
    return out


def _impute(row: dict[str, str], usual: dict) -> bool:
    found = usual.get(_event_key(row))
    if found is None:
        return False
    local_time, agree, total, zone = found
    local = datetime.combine(
        date.fromisoformat(row["scheduled_date_local"]), local_time, tzinfo=ZoneInfo(zone)
    )
    at = local.astimezone(UTC)
    row["scheduled_timestamp_utc"] = at.strftime("%Y-%m-%dT%H:%M:%SZ")
    row["scheduled_date_utc"] = at.date().isoformat()
    row["time_precision"] = "minute"
    row["time_label"] = local_time.strftime("%H:%M")
    row["point_in_time_note"] += (
        f"; release time imputed 2026-10-27 from {agree} of {total} occurrences "
        f"({local_time:%H:%M} {zone})"
    )
    return True


def clean_bytes(
    content: bytes, cfg: ImputeConfig | None = None
) -> tuple[bytes, int, Counter, Counter, Counter]:
    """Return (cleaned bytes, rows in, rule 1 rows, imputed, left day-only), counts by impact."""
    cfg = cfg or ImputeConfig()
    bom = content.startswith(b"\xef\xbb\xbf")
    text = content.decode("utf-8-sig")
    terminator = "\r\n" if "\r\n" in text else "\n"
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    header = next(reader, None)
    if header != CSV_COLUMNS:
        raise ValueError("news CSV header must match the explicit ordered 29-column schema")
    rows = []
    for values in reader:
        if not values:
            continue
        if len(values) != len(CSV_COLUMNS):
            raise ValueError(f"expected {len(CSV_COLUMNS)} columns, got {len(values)}")
        rows.append(dict(zip(CSV_COLUMNS, values, strict=True)))
    usual = _usual_times(rows, cfg)  # siblings = the untouched exact rows of the whole file
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator=terminator)
    writer.writerow(header)
    changed, imputed, left = Counter(), Counter(), Counter()
    for row in rows:
        if is_suspicious(row):
            row["time_precision"] = "date"
            row["scheduled_timestamp_utc"] = ""
            row["scheduled_date_utc"] = row["scheduled_date_local"]
            row["time_label"] = ""
            row["point_in_time_note"] += NOTE
            changed[row["impact"]] += 1
            if _impute(row, usual):
                imputed[row["impact"]] += 1
            else:
                left[row["impact"]] += 1
        writer.writerow([row[c] for c in CSV_COLUMNS])
    data = out.getvalue().encode("utf-8")
    return (b"\xef\xbb\xbf" + data if bom else data), len(rows), changed, imputed, left


def clean_file(source: Path, out: Path) -> tuple[int, Counter, Counter, Counter]:
    """Return (rows in, rule 1 rows, imputed, left day-only), counts by impact."""
    if source.resolve() == out.resolve():
        raise ValueError("output must differ from the source file")
    data, total, changed, imputed, left = clean_bytes(source.read_bytes())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return total, changed, imputed, left


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("--out", type=Path, default=Path("data/news/economic_events.csv"))
    args = p.parse_args(argv)
    try:
        total, changed, imputed, left = clean_file(args.source, args.out)
    except (OSError, ValueError) as exc:
        print(f"news_clean: {exc}", file=sys.stderr)
        return 1
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        calendar = load_calendar(NewsConfig(path=str(args.out.resolve())))
    print(f"rows in: {total}\nrows out: {len(calendar.events) if calendar else 0}")
    print(f"rule 1 changed: {sum(changed.values())} " + str(dict(sorted(changed.items()))))
    print(f"imputed: {sum(imputed.values())} " + str(dict(sorted(imputed.items()))))
    print(f"left day-only: {sum(left.values())} " + str(dict(sorted(left.items()))))
    quality = dict(calendar.quality_counts) if calendar else {}
    print(f"loader quality counters: {quality or 'none'}")
    for w in caught:
        print(f"  warning: {w.message}")
    print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
