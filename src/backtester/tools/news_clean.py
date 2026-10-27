"""Write a cleaned copy of the economic calendar CSV (ROADMAP V2.6d step 3). Spec: docs/news.md.

    python -m backtester.tools.news_clean SOURCE.csv [--out data/news/economic_events.csv]

Rule 1 only: rows labelled exact (second/minute) at 00:00:00 or 23:59:59 lost their real
release time in the source; they become day-only rows on the local date. Everything else is
copied unchanged (same columns, order, values, BOM and line ending). The source is never modified.
"""

import argparse
import csv
import io
import sys
import warnings
from collections import Counter
from pathlib import Path

from backtester.data.news import CSV_COLUMNS, NewsConfig, load_calendar

NOTE = (
    "; cleaned 2026-10-27: release time lost in the source (00:00 / 23:59:59 Asia/Tehran), "
    "day-only on the local date"
)
SUSPICIOUS_LABELS = ("00:00:00", "23:59:59")


def is_suspicious(row: dict[str, str]) -> bool:
    return row["time_precision"] in ("second", "minute") and row["time_label"] in SUSPICIOUS_LABELS


def clean_bytes(content: bytes) -> tuple[bytes, int, Counter]:
    """Return (cleaned bytes, rows in, changed rows by impact)."""
    bom = content.startswith(b"\xef\xbb\xbf")
    text = content.decode("utf-8-sig")
    terminator = "\r\n" if "\r\n" in text else "\n"
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    header = next(reader, None)
    if header != CSV_COLUMNS:
        raise ValueError("news CSV header must match the explicit ordered 29-column schema")
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator=terminator)
    writer.writerow(header)
    total, changed = 0, Counter()
    for values in reader:
        if not values:
            continue
        if len(values) != len(CSV_COLUMNS):
            raise ValueError(f"expected {len(CSV_COLUMNS)} columns, got {len(values)}")
        total += 1
        row = dict(zip(CSV_COLUMNS, values, strict=True))
        if is_suspicious(row):
            row["time_precision"] = "date"
            row["scheduled_timestamp_utc"] = ""
            row["scheduled_date_utc"] = row["scheduled_date_local"]
            row["time_label"] = ""
            row["point_in_time_note"] += NOTE
            changed[row["impact"]] += 1
            values = [row[c] for c in CSV_COLUMNS]
        writer.writerow(values)
    data = out.getvalue().encode("utf-8")
    return (b"\xef\xbb\xbf" + data if bom else data), total, changed


def clean_file(source: Path, out: Path) -> tuple[int, Counter]:
    if source.resolve() == out.resolve():
        raise ValueError("output must differ from the source file")
    data, total, changed = clean_bytes(source.read_bytes())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return total, changed


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("--out", type=Path, default=Path("data/news/economic_events.csv"))
    args = p.parse_args(argv)
    try:
        total, changed = clean_file(args.source, args.out)
    except (OSError, ValueError) as exc:
        print(f"news_clean: {exc}", file=sys.stderr)
        return 1
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        calendar = load_calendar(NewsConfig(path=str(args.out.resolve())))
    print(f"rows in: {total}\nrows out: {len(calendar.events) if calendar else 0}")
    print(f"rule 1 changed: {sum(changed.values())} " + str(dict(sorted(changed.items()))))
    quality = dict(calendar.quality_counts) if calendar else {}
    print(f"loader quality counters: {quality or 'none'}")
    for w in caught:
        print(f"  warning: {w.message}")
    print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
